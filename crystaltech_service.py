# crystaltech_service.py
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from typing import Any

from crystaltech_config import (
    DEFAULT_ASSETS_DIR,
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROGRESS_PATH,
    Step,
    ValidationReport,
    compute_path_avg_completion,
    compute_user_progress_pct,
    get_path_flat,
    load_and_validate_config,
    load_progress_file,
    save_progress_file,
)

logger = logging.getLogger(__name__)


# --- helper: offload blocking sync call to preferred workers (run_step / process / thread / to_thread)
async def _offload_sync_call(
    func: Callable[..., Any],
    *args,
    prefer_process: bool = True,
    name: str | None = None,
    meta: dict | None = None,
) -> Any:
    """
    Try to execute the sync callable off the event loop using the repo's helpers
    (preferred order):
      - file_utils.run_step (if available)
      - file_utils.run_maintenance_with_isolation (if available)
      - file_utils.run_blocking_in_thread (if available)
      - fallback: asyncio.to_thread

    The callable will be invoked with the provided args.
    Returns whatever the callable returns (or raises).
    """
    try:
        from file_utils import run_step  # type: ignore
    except Exception:
        run_step = None
    try:
        from file_utils import (  # type: ignore
            run_blocking_in_thread,
            run_maintenance_with_isolation,
        )
    except Exception:
        run_maintenance_with_isolation = None
        run_blocking_in_thread = None

    call_name = name or (getattr(func, "__name__", "callable") if func else "callable")
    wrapped = lambda: func(*args)

    if run_step is not None:
        try:
            return await run_step(wrapped, name=call_name, meta=meta or {})
        except Exception:
            logger.debug("[OFFLOAD] run_step failed for %s; falling back", call_name, exc_info=True)

    if run_maintenance_with_isolation is not None:
        try:
            return await run_maintenance_with_isolation(
                wrapped, name=call_name, prefer_process=prefer_process, meta=meta or {}
            )
        except Exception:
            logger.debug(
                "[OFFLOAD] run_maintenance_with_isolation failed for %s; falling back",
                call_name,
                exc_info=True,
            )

    if run_blocking_in_thread is not None:
        try:
            return await run_blocking_in_thread(wrapped, name=call_name, meta=meta or {})
        except Exception:
            logger.debug(
                "[OFFLOAD] run_blocking_in_thread failed for %s; falling back",
                call_name,
                exc_info=True,
            )

    return await asyncio.to_thread(wrapped)


# --- path id normalisation & validation helpers ---
def _canon_path_id(pid: str | None) -> str | None:
    if not pid:
        return pid
    p = pid.strip().lower().replace(" ", "_").replace("-", "_")
    p = (
        p.replace("archers", "archer")
        .replace("infantries", "infantry")
        .replace("cavalries", "cavalry")
    )
    return p


def _valid_path_ids(cfg: dict) -> list[str]:
    return [p.get("path_id") for p in cfg.get("paths", []) if p.get("path_id")]


def _validate_path_id_or_hint(cfg: dict, pid_raw: str) -> str:
    want = _canon_path_id(pid_raw)
    canon_map = {}
    for vid in _valid_path_ids(cfg):
        canon_map[_canon_path_id(vid)] = vid
    if want in canon_map:
        return canon_map[want]
    hint = ", ".join(sorted(canon_map.values()))
    raise ValueError(f"Unknown path_id '{pid_raw}'. Try one of: {hint}")


@dataclass(frozen=True)
class NextSteps:
    last_completed_order: int
    last_completed_step_uid: str | None
    next_two: list[Step]
    remaining_count: int
    user_progress_pct: float
    path_avg_pct: float


class CrystalTechService:
    def __init__(
        self,
        config_path: str = DEFAULT_CONFIG_PATH,
        assets_dir: str = DEFAULT_ASSETS_DIR,
        progress_path: str = DEFAULT_PROGRESS_PATH,
    ) -> None:
        self._config_path = config_path
        self._assets_dir = assets_dir
        self._progress_path = progress_path

        self._cfg: dict | None = None
        self._report: ValidationReport | None = None
        self._progress_cache: dict | None = None
        # single lock to protect in-memory mutations and provide serialized writes
        self._write_lock = asyncio.Lock()
        self._cfg_lock = asyncio.Lock()

    # -------- lifecycle --------
    async def load(self, fail_on_warn: bool = False) -> ValidationReport:
        async with self._cfg_lock:
            try:
                res = await _offload_sync_call(
                    load_and_validate_config,
                    self._config_path,
                    self._assets_dir,
                    fail_on_warn,
                    name="load_crystaltech_config",
                    meta={"path": self._config_path},
                )
                if isinstance(res, tuple) and len(res) == 2:
                    cfg, report = res
                else:
                    cfg, report = res
            except Exception:
                logger.exception("[CrystalTech] load_and_validate_config offload failed")
                raise

            self._cfg = cfg
            self._report = report

            try:
                prog = await _offload_sync_call(
                    load_progress_file, self._progress_path, name="load_crystaltech_progress"
                )
                prog = prog or {}
                prog.setdefault("kvk_no", None)
                prog.setdefault("updated_at_utc", None)
                prog.setdefault("entries", [])
                self._progress_cache = prog
            except Exception:
                logger.exception("[CrystalTech] preload progress failed; starting with empty cache")
                self._progress_cache = {"kvk_no": None, "updated_at_utc": None, "entries": []}

            return report

    async def reload(self, fail_on_warn: bool = False) -> ValidationReport:
        return await self.load(fail_on_warn=fail_on_warn)

    # -------- getters --------
    @property
    def is_ready(self) -> bool:
        return self._cfg is not None and self._report is not None and self._report.ok

    def report(self) -> ValidationReport | None:
        return self._report

    def cfg(self) -> dict:
        if self._cfg is None:
            raise RuntimeError("CrystalTechService not loaded. Call load() first.")
        return self._cfg

    # -------- progress I/O (cached + serialized writes) --------
    def _ensure_progress_loaded(self) -> dict:
        if self._progress_cache is None:
            self._progress_cache = {"kvk_no": None, "updated_at_utc": None, "entries": []}
        return self._progress_cache

    # Non-locking persister: performs offloaded disk write but DOES NOT acquire _write_lock.
    # Callers that already hold _write_lock should call this directly to avoid nested-lock deadlocks.
    async def _persist_progress_nolock(self) -> None:
        if self._progress_cache is not None:
            try:
                await _offload_sync_call(
                    save_progress_file,
                    self._progress_cache,
                    self._progress_path,
                    name="save_crystaltech_progress",
                    meta={"path": self._progress_path},
                )
            except Exception:
                logger.exception("[CrystalTech] Failed to persist progress to disk")

    # Public persist that acquires the lock before delegating to nolock version.
    async def persist_progress(self) -> None:
        async with self._write_lock:
            await self._persist_progress_nolock()

    # -------- typed helpers for the command handler --------
    def flatten_path(self, path_id: str, locale: str = "en-GB") -> list[Step]:
        cfg = self.cfg()
        pid = _validate_path_id_or_hint(cfg, path_id)
        logger.info("[CrystalTech] path_id raw=%s -> resolved=%s", path_id, pid)
        return get_path_flat(cfg, pid, locale=locale)

    def get_user_entry(self, governor_id: str) -> dict | None:
        prog = self._ensure_progress_loaded()
        entries: list[dict] = prog.get("entries", [])
        return next((e for e in entries if e.get("governor_id") == governor_id), None)

    # internal nolock helper to mutate cache; caller must hold _write_lock when invoking
    def _ensure_user_entry_nolock(
        self,
        governor_id: str,
        selected_path_id: str,
        selected_troop_type: str,
    ) -> dict:
        prog = self._ensure_progress_loaded()
        entries: list[dict] = prog.get("entries", [])
        entry = next((e for e in entries if e.get("governor_id") == governor_id), None)

        if entry is None:
            entry = {
                "governor_id": governor_id,
                "selected_path_id": selected_path_id,
                "selected_troop_type": selected_troop_type,
                "steps_completed": [],
                "last_update_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            entries.append(entry)
        else:
            entry["selected_path_id"] = selected_path_id
            entry["selected_troop_type"] = selected_troop_type
        return entry

    async def ensure_user_entry(
        self,
        governor_id: str,
        selected_path_id: str,
        selected_troop_type: str,
    ) -> dict:
        cfg = self.cfg()
        canon_path = _validate_path_id_or_hint(cfg, selected_path_id)
        async with self._write_lock:
            return self._ensure_user_entry_nolock(governor_id, canon_path, selected_troop_type)

    def compute_next_steps(
        self,
        path_id: str,
        governor_id: str,
        locale: str = "en-GB",
    ) -> NextSteps:
        cfg = self.cfg()
        pid = _validate_path_id_or_hint(cfg, path_id)
        steps = self.flatten_path(pid, locale=locale)
        if not steps:
            return NextSteps(
                last_completed_order=0,
                last_completed_step_uid=None,
                next_two=[],
                remaining_count=0,
                user_progress_pct=0.0,
                path_avg_pct=0.0,
            )

        entry = self.get_user_entry(governor_id) or {
            "steps_completed": [],
            "selected_path_id": pid,
        }
        completed = set(entry.get("steps_completed") or [])

        last_completed_order = 0
        last_completed_uid: str | None = None
        uid_to_order = {s.step_uid: s.order for s in steps}

        for uid in completed:
            order_val = uid_to_order.get(uid)
            if order_val is not None and order_val > last_completed_order:
                last_completed_order = order_val
                last_completed_uid = uid

        remaining = [s for s in steps if s.order > last_completed_order]
        next_two = remaining[:2]

        user_pct = compute_user_progress_pct(steps, list(completed))
        avg_pct = compute_path_avg_completion(self._ensure_progress_loaded(), pid, cfg)

        return NextSteps(
            last_completed_order=last_completed_order,
            last_completed_step_uid=last_completed_uid,
            next_two=next_two,
            remaining_count=len(remaining),
            user_progress_pct=user_pct,
            path_avg_pct=avg_pct,
        )

    async def save_progress(
        self,
        governor_id: str,
        path_id: str,
        troop_type: str,
        newly_completed_uids: list[str],
    ) -> dict:
        # Perform read-update-persist under lock using nolock helper to avoid nested acquisitions
        async with self._write_lock:
            cfg = self.cfg()
            canon_path = _validate_path_id_or_hint(cfg, path_id)
            entry = self._ensure_user_entry_nolock(governor_id, canon_path, troop_type)
            existing = set(entry.get("steps_completed") or [])
            if newly_completed_uids:
                existing.update(newly_completed_uids)
            entry["steps_completed"] = sorted(existing)
            entry["last_update_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            # call the nolock persister (we already hold the lock)
            await self._persist_progress_nolock()
            return entry

    async def reset_account_progress(self, governor_id: str) -> bool:
        async with self._write_lock:
            prog = self._ensure_progress_loaded()
            entries: list[dict] = prog.get("entries", [])
            before = len(entries)
            entries[:] = [e for e in entries if e.get("governor_id") != governor_id]
            changed = len(entries) != before
            if changed:
                await self._persist_progress_nolock()
            return changed

    async def archive_and_reset_all(self, next_kvk_no: int | None = None) -> str:
        async with self._write_lock:
            prog = self._ensure_progress_loaded()
            current_kvk = prog.get("kvk_no")
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            suffix = f"KVK_{current_kvk}" if current_kvk is not None else f"arch_{ts}"
            archive_dir = os.path.join("data", "crystaltech_archives")
            os.makedirs(archive_dir, exist_ok=True)
            archive_path = os.path.join(archive_dir, f"{suffix}.crystaltech_progress.json")

            # ensure current file flushed
            try:
                await self._persist_progress_nolock()
            except Exception:
                logger.exception(
                    "[CrystalTech] _persist_progress before archive failed (continuing)"
                )

            live_copy = None
            try:
                try:
                    from crystaltech_config import _read_json as _ct_read  # type: ignore
                except Exception:
                    _ct_read = None

                if _ct_read is not None:
                    try:
                        live_copy = await _offload_sync_call(
                            _ct_read,
                            self._progress_path,
                            name="read_crystaltech_progress_for_archive",
                        )
                    except Exception:
                        logger.exception(
                            "[CrystalTech] read_crystaltech_progress_for_archive failed"
                        )
                        live_copy = None
                else:
                    live_copy = None
            except Exception:
                logger.exception("[CrystalTech] failed to prepare live copy for archive")
                live_copy = None

            if live_copy is not None:
                try:
                    # Import the write func cleanly and offload it
                    try:
                        from crystaltech_config import _write_json as _ct_write  # type: ignore
                    except Exception:
                        _ct_write = None

                    if _ct_write is not None:
                        await _offload_sync_call(
                            _ct_write, archive_path, live_copy, name="write_crystaltech_archive"
                        )
                    else:
                        # fallback: direct write (best-effort)
                        try:
                            from crystaltech_config import (
                                _write_json as _fallback_write,  # type: ignore
                            )

                            _fallback_write(archive_path, live_copy)
                        except Exception:
                            logger.exception(
                                "[CrystalTech] failed to write archive copy (fallback)"
                            )
                except Exception:
                    try:
                        from crystaltech_config import _write_json  # type: ignore

                        _write_json(archive_path, live_copy)
                    except Exception:
                        logger.exception("[CrystalTech] failed to write archive copy")

            self._progress_cache = {
                "kvk_no": next_kvk_no,
                "updated_at_utc": None,
                "entries": [],
            }
            await self._persist_progress_nolock()
            return archive_path

    def list_incomplete_steps(
        self, path_id: str, governor_id: str, locale: str = "en-GB"
    ) -> list[Step]:
        steps = self.flatten_path(path_id, locale=locale)
        entry = self.get_user_entry(governor_id) or {"steps_completed": []}
        completed = set(entry.get("steps_completed") or [])
        last_order = 0
        uid_to_order = {s.step_uid: s.order for s in steps}
        for uid in completed:
            order_val = uid_to_order.get(uid)
            if order_val and order_val > last_order:
                last_order = order_val
        return [s for s in steps if s.order > last_order]

    def get_last_completed(
        self, path_id: str, governor_id: str, locale: str = "en-GB"
    ) -> Step | None:
        steps = self.flatten_path(path_id, locale=locale)
        entry = self.get_user_entry(governor_id) or {"steps_completed": []}
        completed = set(entry.get("steps_completed") or [])
        uid_to_step = {s.step_uid: s for s in steps}
        last: Step | None = None
        for uid in completed:
            st = uid_to_step.get(uid)
            if st and (last is None or st.order > last.order):
                last = st
        return last
