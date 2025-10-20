# crystaltech_service.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
import os

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


# --- path id normalisation & validation helpers ---
def _canon_path_id(pid: str | None) -> str | None:
    """
    Normalise common user-facing variants to the canonical path_id form used in config.
    Examples: 'f2p low archers' -> 'f2p_low_archer', 'cavalries' -> 'cavalry'
    """
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
    """Return the list of path_id values defined in the config."""
    return [p.get("path_id") for p in cfg.get("paths", []) if p.get("path_id")]


def _validate_path_id_or_hint(cfg: dict, pid_raw: str) -> str:
    """
    Accept user/path IDs that differ only by spacing/dashes/pluralisation.
    Compare in canonical form, but return the exact path_id from the loaded config.
    """
    want = _canon_path_id(pid_raw)
    # canonical(config_id) -> original config_id
    canon_map = {}
    for vid in _valid_path_ids(cfg):
        canon_map[_canon_path_id(vid)] = vid
    if want in canon_map:
        return canon_map[want]  # use the real config id (singular *or* plural in your file)
    # Not found: show what's actually in the running config
    hint = ", ".join(sorted(canon_map.values()))
    raise ValueError(f"Unknown path_id '{pid_raw}'. Try one of: {hint}")


@dataclass(frozen=True)
class NextSteps:
    last_completed_order: int
    last_completed_step_uid: str | None
    next_two: list[Step]  # up to 2
    remaining_count: int
    user_progress_pct: float
    path_avg_pct: float


class CrystalTechService:
    """
    Small in-memory service for Crystal Tech:
      - caches config + validation report
      - exposes helpers for command handlers
      - serializes progress writes with an asyncio.Lock
    """

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
        self._progress_cache: dict | None = None  # lazy-loaded
        self._write_lock = asyncio.Lock()
        self._cfg_lock = asyncio.Lock()

    # -------- lifecycle --------
    async def load(self, fail_on_warn: bool = False) -> ValidationReport:
        """
        Loads config + validation report into memory.
        Preloads progress file lazily on first access (to keep startup faster).
        """
        # single-thread this via lock to avoid overlapping reloads at boot
        async with self._cfg_lock:
            cfg, report = load_and_validate_config(
                config_path=self._config_path,
                assets_dir=self._assets_dir,
                fail_on_warn=fail_on_warn,
            )
            self._cfg = cfg
            self._report = report
            # do not load progress here; defer to first read
            self._progress_cache = None
            return report

    async def reload(self, fail_on_warn: bool = False) -> ValidationReport:
        """Hot-reload config (e.g., /crystaltech_reload)."""
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
            self._progress_cache = load_progress_file(self._progress_path)
            # shape guard
            self._progress_cache.setdefault("kvk_no", None)
            self._progress_cache.setdefault("updated_at_utc", None)
            self._progress_cache.setdefault("entries", [])
        return self._progress_cache

    async def _persist_progress(self) -> None:
        async with self._write_lock:
            if self._progress_cache is not None:
                save_progress_file(self._progress_cache, self._progress_path)

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

    def ensure_user_entry(
        self,
        governor_id: str,
        selected_path_id: str,
        selected_troop_type: str,
    ) -> dict:
        prog = self._ensure_progress_loaded()
        entries: list[dict] = prog.get("entries", [])
        entry = next((e for e in entries if e.get("governor_id") == governor_id), None)

        # store the canonical id to prevent drift
        cfg = self.cfg()
        canon_path = _validate_path_id_or_hint(cfg, selected_path_id)

        if entry is None:
            entry = {
                "governor_id": governor_id,
                "selected_path_id": canon_path,
                "selected_troop_type": selected_troop_type,
                "steps_completed": [],
                "last_update_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            entries.append(entry)
        else:
            # keep path/troop in sync if user changes them at setup/reset
            entry["selected_path_id"] = canon_path
            entry["selected_troop_type"] = selected_troop_type
        return entry

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

        # Determine last completed order
        last_completed_order = 0
        last_completed_uid: str | None = None
        uid_to_order = {s.step_uid: s.order for s in steps}

        for uid in completed:
            order_val = uid_to_order.get(uid)
            if order_val is not None and order_val > last_completed_order:
                last_completed_order = order_val
                last_completed_uid = uid

        # Auto-complete for newly inserted steps behind last_completed_order
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
        """
        Adds completed step_uids (de-duped), updates timestamp, persists.
        Returns the updated entry.
        """
        entry = self.ensure_user_entry(governor_id, path_id, troop_type)
        existing = set(entry.get("steps_completed") or [])
        if newly_completed_uids:
            existing.update(newly_completed_uids)
        entry["steps_completed"] = sorted(existing)  # store as sorted list for stable diffs
        entry["last_update_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        await self._persist_progress()
        return entry

    async def reset_account_progress(self, governor_id: str) -> bool:
        """
        Clears an individual's progress entry.
        Returns True if an entry was removed, False if none existed.
        """
        prog = self._ensure_progress_loaded()
        entries: list[dict] = prog.get("entries", [])
        before = len(entries)
        entries[:] = [e for e in entries if e.get("governor_id") != governor_id]
        changed = len(entries) != before
        if changed:
            await self._persist_progress()
        return changed

    async def archive_and_reset_all(self, next_kvk_no: int | None = None) -> str:
        """
        Archives the current progress to /data/crystaltech_archives/KVK_<N>.json
        and resets live progress for the next KVK.
        Returns the archive file path.
        """
        prog = self._ensure_progress_loaded()
        current_kvk = prog.get("kvk_no")
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        # Decide archive name; guard None
        suffix = f"KVK_{current_kvk}" if current_kvk is not None else f"arch_{ts}"
        archive_dir = os.path.join("data", "crystaltech_archives")
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, f"{suffix}.crystaltech_progress.json")

        # Persist archive (use the public function to stamp updated_at)
        await self._persist_progress()  # ensure current file is up-to-date on disk
        # Write a fresh copy explicitly (not move) to keep live file present
        from crystaltech_config import _read_json, _write_json  # safe internal reuse

        live_copy = _read_json(self._progress_path)
        _write_json(archive_path, live_copy)

        # Reset live
        self._progress_cache = {
            "kvk_no": next_kvk_no,
            "updated_at_utc": None,
            "entries": [],
        }
        await self._persist_progress()
        return archive_path

    # -------- convenience for UI composition --------
    def list_incomplete_steps(
        self, path_id: str, governor_id: str, locale: str = "en-GB"
    ) -> list[Step]:
        steps = self.flatten_path(path_id, locale=locale)
        entry = self.get_user_entry(governor_id) or {"steps_completed": []}
        completed = set(entry.get("steps_completed") or [])
        # treat inserted steps behind completion as auto-complete for display purposes
        # compute threshold:
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
