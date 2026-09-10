from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path
from typing import Any

from constants import DATA_DIR
from file_utils import atomic_write_json

DEFAULT_REMINDER_STATE_PATH = Path(DATA_DIR) / "ark_reminder_state.json"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _from_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(UTC)


def make_dm_key(match_id: int, user_id: int, reminder_type: str) -> str:
    return f"{match_id}|{user_id}|{reminder_type}"


def make_channel_key(match_id: int, channel_id: int, reminder_type: str) -> str:
    return f"{match_id}|channel:{channel_id}|{reminder_type}"


def make_channel_daily_key(
    match_id: int, channel_id: int, reminder_type: str, day_utc: date
) -> str:
    return f"{match_id}|channel:{channel_id}|{reminder_type}|{day_utc.isoformat()}"


@dataclass
class ArkReminderState:
    path: Path = field(default_factory=lambda: DEFAULT_REMINDER_STATE_PATH)
    reminders: dict[str, str] = field(default_factory=dict)
    # schema: { "<match_id>": { "<reminder_type>": {"channel_id": int, "message_id": int} } }
    message_refs: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> ArkReminderState:
        resolved = path or DEFAULT_REMINDER_STATE_PATH
        if not resolved.exists():
            return cls(path=resolved)

        try:
            raw = json.loads(resolved.read_text(encoding="utf-8"))
        except Exception:
            return cls(path=resolved)

        reminders = raw.get("reminders") or {}
        message_refs = raw.get("message_refs") or {}
        if not isinstance(reminders, dict):
            reminders = {}
        if not isinstance(message_refs, dict):
            message_refs = {}

        return cls(path=resolved, reminders=reminders, message_refs=message_refs)

    def save(self) -> None:
        payload: dict[str, Any] = {"reminders": self.reminders, "message_refs": self.message_refs}
        atomic_write_json(self.path, payload)

    def mark_sent(self, key: str, sent_at: datetime | None = None) -> None:
        self.reminders[key] = _to_iso(sent_at or _utcnow())

    def was_sent(self, key: str) -> bool:
        return key in self.reminders

    def sent_at(self, key: str) -> datetime | None:
        value = self.reminders.get(key)
        if not value:
            return None
        try:
            return _from_iso(value)
        except Exception:
            return None

    def should_send_with_grace(
        self,
        key: str,
        scheduled_for: datetime,
        now: datetime | None = None,
        grace: timedelta = timedelta(minutes=15),
    ) -> bool:
        if self.was_sent(key):
            return False
        current = now or _utcnow()
        if current < scheduled_for:
            return False
        if current - scheduled_for > grace:
            return False
        return True

    def set_channel_message_ref(
        self,
        match_id: int,
        reminder_type: str,
        channel_id: int,
        message_id: int,
    ) -> None:
        mkey = str(match_id)
        bucket = self.message_refs.setdefault(mkey, {})
        bucket[reminder_type] = {"channel_id": channel_id, "message_id": message_id}

    def get_channel_message_ref(
        self,
        match_id: int,
        reminder_type: str,
    ) -> dict[str, int] | None:
        return (self.message_refs.get(str(match_id)) or {}).get(reminder_type)
