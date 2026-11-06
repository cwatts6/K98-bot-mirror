from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Any

from constants import DATA_DIR
from file_utils import atomic_write_json

STATE_SCHEMA_VERSION = 1
DEFAULT_REMINDER_STATE_PATH = Path(DATA_DIR) / "event_calendar_reminder_state.json"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _from_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(UTC)


def make_key(event_instance_id: str, user_id: int, reminder_type: str) -> str:
    return f"{str(event_instance_id).strip()}|{int(user_id)}|{str(reminder_type).strip().lower()}"


@dataclass
class CalendarReminderState:
    path: Path = field(default_factory=lambda: DEFAULT_REMINDER_STATE_PATH)
    sent: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> CalendarReminderState:
        resolved = path or DEFAULT_REMINDER_STATE_PATH
        if not resolved.exists():
            return cls(path=resolved)

        try:
            raw = json.loads(resolved.read_text(encoding="utf-8"))
        except Exception:
            return cls(path=resolved)

        sent = raw.get("sent", {})
        if not isinstance(sent, dict):
            sent = {}
        return cls(path=resolved, sent=sent)

    def save(self) -> None:
        payload: dict[str, Any] = {
            "schema_version": STATE_SCHEMA_VERSION,
            "sent": self.sent,
        }
        atomic_write_json(self.path, payload)

    def mark_sent(self, key: str, sent_at: datetime | None = None) -> None:
        self.sent[key] = _to_iso(sent_at or _utcnow())

    def was_sent(self, key: str) -> bool:
        return key in self.sent

    def sent_at(self, key: str) -> datetime | None:
        value = self.sent.get(key)
        if not value:
            return None
        try:
            return _from_iso(value)
        except Exception:
            return None

    def should_send_with_grace(
        self,
        *,
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
