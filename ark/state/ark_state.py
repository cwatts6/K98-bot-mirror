from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import logging
import os
from typing import Any

from constants import DATA_DIR

try:
    from file_utils import acquire_lock, atomic_write_json, read_json_safe, run_blocking_in_thread
except Exception:  # test environments
    acquire_lock = None
    atomic_write_json = None
    read_json_safe = None
    run_blocking_in_thread = None

try:
    from utils import parse_isoformat_utc
except Exception:
    parse_isoformat_utc = None

logger = logging.getLogger(__name__)

MessageKey = str


@dataclass
class ArkMessageRef:
    channel_id: int
    message_id: int


@dataclass
class ArkMessageState:
    registration: ArkMessageRef | None = None
    confirmation: ArkMessageRef | None = None
    confirmation_updates: list[str] = field(default_factory=list)


@dataclass
class ArkReminderState:
    sent_at_utc: datetime


@dataclass
class ArkCaches:
    open_match_cache: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    roster_cache: dict[int, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass
class ArkJsonState:
    message_state_path: str = os.path.join(DATA_DIR, "ark_message_state.json")
    reminder_state_path: str = os.path.join(DATA_DIR, "ark_reminder_state.json")
    messages: dict[int, ArkMessageState] = field(default_factory=dict)
    reminders: dict[MessageKey, ArkReminderState] = field(default_factory=dict)

    @staticmethod
    def reminder_key(match_id: int, user_id: int, reminder_type: str) -> MessageKey:
        return f"{match_id}|{user_id}|{reminder_type}"

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            if parse_isoformat_utc:
                return parse_isoformat_utc(value)
        except Exception:
            pass
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except Exception:
            return None

    def _serialize_messages(self) -> dict[str, Any]:
        out: dict[str, Any] = {"matches": {}}
        for match_id, state in (self.messages or {}).items():
            payload: dict[str, Any] = {}
            if state.registration:
                payload["registration"] = {
                    "channel_id": int(state.registration.channel_id),
                    "message_id": int(state.registration.message_id),
                }
            if state.confirmation:
                payload["confirmation"] = {
                    "channel_id": int(state.confirmation.channel_id),
                    "message_id": int(state.confirmation.message_id),
                }
            if state.confirmation_updates:
                payload["confirmation_updates"] = list(state.confirmation_updates)
            out["matches"][str(match_id)] = payload
        return out

    def _serialize_reminders(self) -> dict[str, Any]:
        out: dict[str, Any] = {"reminders": {}}
        for key, state in (self.reminders or {}).items():
            try:
                out["reminders"][key] = state.sent_at_utc.isoformat()
            except Exception:
                out["reminders"][key] = None
        return out

    def _load_messages_from_json(self, data: dict[str, Any]) -> None:
        matches = (data or {}).get("matches") or {}
        parsed: dict[int, ArkMessageState] = {}
        for match_id_str, block in matches.items():
            try:
                match_id = int(match_id_str)
            except Exception:
                continue

            reg = block.get("registration")
            conf = block.get("confirmation")
            updates = block.get("confirmation_updates") or []
            parsed[match_id] = ArkMessageState(
                registration=(
                    ArkMessageRef(
                        channel_id=int(reg["channel_id"]),
                        message_id=int(reg["message_id"]),
                    )
                    if reg
                    else None
                ),
                confirmation=(
                    ArkMessageRef(
                        channel_id=int(conf["channel_id"]),
                        message_id=int(conf["message_id"]),
                    )
                    if conf
                    else None
                ),
                confirmation_updates=[str(u) for u in updates if u],
            )
        self.messages = parsed

    def _load_reminders_from_json(self, data: dict[str, Any]) -> None:
        reminders = (data or {}).get("reminders") or {}
        parsed: dict[MessageKey, ArkReminderState] = {}
        for key, sent_at in reminders.items():
            dt = self._parse_dt(str(sent_at) if sent_at is not None else None)
            if dt is None:
                continue
            parsed[str(key)] = ArkReminderState(sent_at_utc=dt)
        self.reminders = parsed

    def load(self) -> None:
        if read_json_safe is None:
            logger.warning("[ARK_STATE] read_json_safe unavailable; cannot load JSON state.")
            return
        msg_data = read_json_safe(self.message_state_path, default={}) or {}
        rem_data = read_json_safe(self.reminder_state_path, default={}) or {}
        self._load_messages_from_json(msg_data)
        self._load_reminders_from_json(rem_data)

    def save(self) -> None:
        if atomic_write_json is None:
            logger.warning("[ARK_STATE] atomic_write_json unavailable; cannot save JSON state.")
            return

        msg_payload = self._serialize_messages()
        rem_payload = self._serialize_reminders()

        if acquire_lock:
            with acquire_lock(self.message_state_path + ".lock", timeout=5.0):
                atomic_write_json(self.message_state_path, msg_payload, ensure_parent_dir=True)
            with acquire_lock(self.reminder_state_path + ".lock", timeout=5.0):
                atomic_write_json(self.reminder_state_path, rem_payload, ensure_parent_dir=True)
        else:
            atomic_write_json(self.message_state_path, msg_payload, ensure_parent_dir=True)
            atomic_write_json(self.reminder_state_path, rem_payload, ensure_parent_dir=True)

    async def load_async(self) -> None:
        if run_blocking_in_thread:
            await run_blocking_in_thread(self.load, name="ark_state_load")
            return
        import asyncio

        await asyncio.to_thread(self.load)

    async def save_async(self) -> None:
        if run_blocking_in_thread:
            await run_blocking_in_thread(self.save, name="ark_state_save")
            return
        import asyncio

        await asyncio.to_thread(self.save)
