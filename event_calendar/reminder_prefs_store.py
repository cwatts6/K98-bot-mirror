from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from constants import DATA_DIR
from event_calendar.reminder_prefs import default_prefs, normalize_prefs
from file_utils import atomic_write_json

_REMINDER_PREFS_PATH = Path(DATA_DIR) / "event_calendar_reminder_prefs.json"


def prefs_store_path() -> Path:
    return _REMINDER_PREFS_PATH


def load_all_user_prefs() -> dict[str, dict[str, Any]]:
    p = prefs_store_path()
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        out[str(k)] = normalize_prefs(v)
    return out


def save_all_user_prefs(payload: dict[str, dict[str, Any]]) -> None:
    cleaned: dict[str, dict[str, Any]] = {}
    for k, v in (payload or {}).items():
        if not isinstance(v, dict):
            continue
        cleaned[str(k)] = normalize_prefs(v)
    atomic_write_json(prefs_store_path(), cleaned)


def get_user_prefs(user_id: int) -> dict[str, Any]:
    all_prefs = load_all_user_prefs()
    return normalize_prefs(all_prefs.get(str(int(user_id))) or default_prefs())


def set_user_prefs(user_id: int, prefs: dict[str, Any]) -> None:
    uid = str(int(user_id))
    all_prefs = load_all_user_prefs()
    all_prefs[uid] = normalize_prefs(prefs)
    save_all_user_prefs(all_prefs)
