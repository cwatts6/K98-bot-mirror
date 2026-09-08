"""Durable ownership for Pre-KVK and off-season fresh production dispatch.

The CSV remains a legacy success/ping log. This versioned sidecar is the
authority for pending sends, including unresolved outcomes across UTC days.
No network operations, Discord types, lease stealing or background retries.
All participants must use the same local filesystem; mixed-version writers
and independent hosts are outside this protocol.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
import json
import logging
import math
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import psutil

from file_utils import atomic_json_write, run_blocking_in_thread
from stats_alerts import guard, state
from utils import utcnow

logger = logging.getLogger(__name__)
KINDS = frozenset({"prekvk_daily", "offseason_daily", "offseason_weekly"})
PHASES = frozenset({"reserved", "sending", "uncertain", "accepted", "committed", "released"})


class DispatchUnavailable(RuntimeError):
    """A fresh send cannot safely proceed; never retry through another backend."""


def _utc(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() != UTC.utcoffset(result):
        raise ValueError("Dispatch timestamps must be UTC")
    return result


def _owner_alive(record: dict) -> bool | None:
    try:
        return psutil.Process(record["owner_pid"]).create_time() == record["owner_created"]
    except psutil.NoSuchProcess:
        return False
    except (psutil.Error, OSError):
        return None


class ReservationStore:
    def __init__(
        self,
        log_path: str | None = None,
        *,
        clock: Callable[[], datetime] = utcnow,
        owner_alive: Callable[[dict], bool | None] = _owner_alive,
    ):
        self.log_path = str(log_path or guard.LOG_PATH)
        self.path = Path(f"{self.log_path}.dispatch.json")
        self.clock = clock
        self.owner_alive = owner_alive

    def _read(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "message_generation": 0, "attempts": {}}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            not isinstance(data, dict)
            or type(data.get("version")) is not int
            or data["version"] != 1
            or type(data.get("message_generation")) is not int
            or data["message_generation"] < 0
            or not isinstance(data.get("attempts"), dict)
        ):
            raise DispatchUnavailable("Invalid dispatch store; preserve it for operator recovery")
        for token, row in data["attempts"].items():
            if (
                not isinstance(row, dict)
                or not isinstance(token, str)
                or len(token) != 32
                or any(c not in "0123456789abcdef" for c in token)
            ):
                raise DispatchUnavailable("Invalid dispatch attempt")
            if (
                row.get("token") != token
                or row.get("kind") not in KINDS
                or row.get("phase") not in PHASES
            ):
                raise DispatchUnavailable("Invalid dispatch ownership/phase")
            for key in ("owner_pid", "channel_id", "generation"):
                if type(row.get(key)) is not int or row[key] < (0 if key == "generation" else 1):
                    raise DispatchUnavailable("Invalid dispatch identity")
            if (
                type(row.get("owner_created")) not in (float, int)
                or not math.isfinite(row["owner_created"])
                or row["owner_created"] <= 0
            ):
                raise DispatchUnavailable("Invalid dispatch process identity")
            reserved = _utc(row["reserved_at"])
            if row.get("day") != reserved.date().isoformat():
                raise DispatchUnavailable("Invalid dispatch day")
            if row["phase"] in {"sending", "uncertain", "accepted", "committed"}:
                _utc(row["started_at"])
            if row["phase"] in {"accepted", "committed"}:
                if type(row.get("message_id")) is not int or row["message_id"] <= 0:
                    raise DispatchUnavailable("Invalid delivery receipt")
                _utc(row["accepted_at"])
        return data

    def _write(self, data: dict) -> None:
        atomic_json_write(str(self.path), data, ensure_ascii=False, sort_keys=True, default=None)

    @staticmethod
    def _owned(data: dict, token: str) -> dict:
        row = data["attempts"].get(token)
        if not row or row.get("token") != token:
            raise DispatchUnavailable("Dispatch owner token mismatch")
        return row

    @staticmethod
    def _conflicts(kind: str, other: str) -> bool:
        # Daily and weekly off-season are independent. Pre-KVK conflicts with both.
        return kind == other or "prekvk_daily" in (kind, other)

    def _project(self, data: dict, row: dict) -> None:
        """Idempotent projections of a durable positive receipt. Lock already held."""
        when = _utc(row["accepted_at"])
        if (
            row["kind"] == "prekvk_daily"
            and row["generation"] == data["message_generation"]
            and when.date() == self.clock().date()
        ):
            state.update_prekvk_message(row["message_id"])
        guard._append_success_unlocked(self.log_path, row["kind"], when)
        row["phase"] = "committed"
        self._write(data)

    def _recover(self, data: dict) -> None:
        for row in data["attempts"].values():
            if row["phase"] == "accepted":
                self._project(data, row)
            elif row["phase"] == "reserved" and self.owner_alive(row) is False:
                row["phase"] = "released"
                row["reason"] = "owner_exited_before_send"
                self._write(data)
            elif row["phase"] == "sending" and self.owner_alive(row) is False:
                row["phase"] = "uncertain"
                row["reason"] = "owner_exited_after_send_started"
                self._write(data)

    def reserve(self, kind: str, channel_id: int) -> str | None:
        if kind not in KINDS or type(channel_id) is not int or channel_id <= 0:
            raise ValueError("Invalid dispatch kind/channel")
        with guard.coordination_lock(self.log_path):
            data = self._read()
            self._recover(data)
            now = self.clock()
            day = now.date().isoformat()
            for row in data["attempts"].values():
                if row["phase"] not in {"released", "committed"} and self._conflicts(
                    kind, row["kind"]
                ):
                    logger.info(
                        "[DISPATCH] Contended kind=%s phase=%s token=%s",
                        kind,
                        row["phase"],
                        row["token"],
                    )
                    return None
            _, rows = guard._read_rows_unlocked(self.log_path)
            blocked = {kind}
            if kind == "prekvk_daily":
                blocked.update({"offseason_daily", "offseason_weekly"})
            # A missing CSV never erases an already committed receipt.
            if any(guard._count_rows(rows, key, day) for key in blocked) or any(
                row["phase"] == "committed"
                and row["kind"] in blocked
                and _utc(row["accepted_at"]).date() == now.date()
                for row in data["attempts"].values()
            ):
                return None
            token = uuid4().hex
            data["attempts"][token] = {
                "token": token,
                "kind": kind,
                "day": day,
                "phase": "reserved",
                "owner_pid": os.getpid(),
                "owner_created": psutil.Process().create_time(),
                "channel_id": channel_id,
                "reserved_at": now.isoformat(),
                "generation": data["message_generation"],
            }
            self._write(data)
            logger.info("[DISPATCH] Reserved kind=%s day=%s token=%s", kind, day, token)
            return token

    def start(self, token: str) -> None:
        with guard.coordination_lock(self.log_path):
            data = self._read()
            row = self._owned(data, token)
            if row["phase"] != "reserved":
                raise DispatchUnavailable("Reservation is no longer available to start")
            now = self.clock()
            # Recheck the quota when UTC rolls over during preparation, without a new timer/retry.
            _, rows = guard._read_rows_unlocked(self.log_path)
            blocked = {row["kind"]}
            if row["kind"] == "prekvk_daily":
                blocked.update({"offseason_daily", "offseason_weekly"})
            if any(guard._count_rows(rows, key, now.date().isoformat()) for key in blocked):
                raise DispatchUnavailable("Daily eligibility changed before publication")
            if row["kind"] == "prekvk_daily" and row["generation"] != data["message_generation"]:
                raise DispatchUnavailable("Message state invalidated before publication")
            row.update(phase="sending", started_at=now.isoformat())
            self._write(data)

    def accept(self, token: str, message_id: int) -> None:
        if type(message_id) is not int or message_id <= 0:
            raise ValueError("A positive Discord message receipt is required")
        with guard.coordination_lock(self.log_path):
            data = self._read()
            row = self._owned(data, token)
            if row["phase"] == "committed":
                if row["message_id"] != message_id:
                    raise DispatchUnavailable("Receipt mismatch")
                return
            if row["phase"] == "accepted":
                if row["message_id"] != message_id:
                    raise DispatchUnavailable("Receipt mismatch")
            elif row["phase"] in {"sending", "uncertain"}:
                row.update(
                    phase="accepted", message_id=message_id, accepted_at=self.clock().isoformat()
                )
                self._write(data)  # Receipt survives failure of either legacy projection.
            else:
                raise DispatchUnavailable("Cannot commit an attempt that never started")
            self._project(data, row)
            logger.info(
                "[DISPATCH] Committed kind=%s token=%s message_id=%s",
                row["kind"],
                token,
                message_id,
            )

    def finish_failure(self, token: str, *, rejected: bool = False) -> None:
        """Release only known non-delivery; rejected is for pre-invocation proof.

        A final HTTP status is insufficient: the Discord client's earlier HTTP
        retries can have ambiguous outcomes. Normal send exceptions never set it.
        """
        with guard.coordination_lock(self.log_path):
            data = self._read()
            row = self._owned(data, token)
            if row["phase"] in {"accepted", "committed", "released"}:
                return
            if row["phase"] == "reserved" or rejected:
                row.update(phase="released", reason="known_not_delivered")
            else:
                row.update(phase="uncertain", reason="send_outcome_unknown")
            self._write(data)
            logger.warning(
                "[DISPATCH] Outcome kind=%s token=%s phase=%s", row["kind"], token, row["phase"]
            )

    def clear_message(self, *, expected_id: Any = ...) -> bool:
        """Fence in-flight receipts when fighting opens or a reference is invalidated."""
        with guard.coordination_lock(self.log_path):
            data = self._read()
            if expected_id is not ... and state.load_state().get("prekvk_msg_id") != expected_id:
                return False
            if self.path.exists():
                data["message_generation"] += 1
                self._write(data)
            return state.update_prekvk_message(None, expected_id=expected_id)

    def reconcile_receipt(
        self, token: str, *, channel_id: int, message_id: int, accepted_at: datetime
    ) -> None:
        """Operator-only recovery from positive Discord evidence, never from absence.

        Caller must verify bot author, destination, payload and publication time.
        This local API does not discover messages or send anything to Discord.
        """
        with guard.coordination_lock(self.log_path):
            data = self._read()
            row = self._owned(data, token)
            if row["phase"] not in {"sending", "uncertain"} or row["channel_id"] != channel_id:
                raise DispatchUnavailable("Reconciliation ownership/destination mismatch")
            if (
                type(message_id) is not int
                or message_id <= 0
                or _utc(accepted_at.isoformat()) < _utc(row["started_at"])
            ):
                raise ValueError("Invalid reconciliation receipt")
            row.update(phase="accepted", message_id=message_id, accepted_at=accepted_at.isoformat())
            self._write(data)
            self._project(data, row)


async def _io(func, *args, **kwargs):
    """One telemetry backend; finish a started filesystem operation on cancellation."""
    task = asyncio.create_task(
        run_blocking_in_thread(func, *args, **kwargs, name=f"dispatch_{func.__name__}")
    )
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
        except Exception:
            break
    if cancelled:
        try:
            task.result()
        except Exception:
            logger.exception("[DISPATCH] Filesystem operation failed during cancellation")
        raise asyncio.CancelledError()
    return task.result()


async def clear_prekvk_message(*, expected_id: Any = ...) -> bool:
    """Complete reference invalidation off-loop, including during cancellation."""
    return await _io(ReservationStore().clear_message, expected_id=expected_id)


class DispatchAttempt:
    """Async lifetime adapter; the repository remains Discord-independent."""

    def __init__(self, kind: str, channel_id: int):
        self.store = ReservationStore()
        self.kind = kind
        self.channel_id = channel_id
        self.token: str | None = None

    async def __aenter__(self):
        def reserve():
            self.token = self.store.reserve(self.kind, self.channel_id)
            return self.token

        try:
            await _io(reserve)
        except BaseException:
            if self.token:
                await _io(self.store.finish_failure, self.token)
            raise
        if not self.token:
            raise DispatchUnavailable("Dispatch is already owned or daily quota is satisfied")
        return self

    async def start(self) -> None:
        try:
            await _io(self.store.start, self.token)
        except asyncio.CancelledError:
            # start() has not returned to the sender; no Discord call entered.
            await _io(self.store.finish_failure, self.token, rejected=True)
            raise

    async def accept(self, message_id: int) -> None:
        try:
            await _io(self.store.accept, self.token, message_id)
        except Exception:
            logger.exception(
                "[DISPATCH] Delivery accepted; persistence requires reconciliation token=%s message_id=%s",
                self.token,
                message_id,
            )

    async def __aexit__(self, exc_type, exc, tb):
        if self.token:
            # Even a final HTTP rejection can follow an ambiguous client retry.
            try:
                await _io(self.store.finish_failure, self.token)
            except Exception:
                logger.exception(
                    "[DISPATCH] Failed finalizing token=%s; retained state requires recovery",
                    self.token,
                )
        return False
