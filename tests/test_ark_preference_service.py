from __future__ import annotations

import asyncio
import datetime
import importlib
import os
import sys
import types

import pytest

if not hasattr(datetime, "UTC"):
    datetime.UTC = datetime.UTC


def _load_service_module(monkeypatch):
    monkeypatch.setenv("OUR_KINGDOM", os.getenv("OUR_KINGDOM", "0") or "0")
    sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
    gspread_mod = types.ModuleType("gspread")
    gspread_exc = types.ModuleType("gspread.exceptions")
    gspread_exc.APIError = Exception
    gspread_exc.SpreadsheetNotFound = Exception
    sys.modules.setdefault("gspread", gspread_mod)
    sys.modules.setdefault("gspread.exceptions", gspread_exc)
    sqlalchemy_mod = types.ModuleType("sqlalchemy")
    sqlalchemy_mod.create_engine = lambda *args, **kwargs: None
    sys.modules.setdefault("sqlalchemy", sqlalchemy_mod)

    unidecode_mod = types.ModuleType("unidecode")
    unidecode_mod.unidecode = lambda value: value
    sys.modules.setdefault("unidecode", unidecode_mod)

    # Ensure we always import the service module after stubs are applied.
    sys.modules.pop("ark.ark_preference_service", None)
    return importlib.import_module("ark.ark_preference_service")


def test_set_preference_creates_preference(monkeypatch):
    service = _load_service_module(monkeypatch)
    service._name_cache["rows"] = [{"GovernorID": "123", "GovernorName": "Tester"}]

    async def _get_team_preference(*_a, **_k):
        return None

    async def _upsert_team_preference(governor_id: int, preferred_team: int, updated_by: str):
        return {
            "GovernorID": governor_id,
            "PreferredTeam": preferred_team,
            "IsActive": 1,
            "CreatedAtUTC": "created",
            "UpdatedAtUTC": "updated",
            "UpdatedBy": updated_by,
        }

    monkeypatch.setattr(service, "get_team_preference", _get_team_preference)
    monkeypatch.setattr(service, "upsert_team_preference", _upsert_team_preference)

    pref = asyncio.run(service.set_preference(123, 1, "discord:1"))

    assert pref["GovernorID"] == 123
    assert pref["GovernorName"] == "Tester"
    assert pref["PreferredTeam"] == 1
    assert pref["IsActive"] is True


def test_set_preference_rejects_unknown_governor(monkeypatch):
    service = _load_service_module(monkeypatch)
    service._name_cache["rows"] = []

    async def _refresh():
        return None

    monkeypatch.setattr(service, "refresh_name_cache_from_sql", _refresh)

    with pytest.raises(service.ArkPreferenceError, match="GovernorID not found"):
        asyncio.run(service.set_preference(999, 1, "discord:1"))


def test_set_preference_rejects_invalid_team(monkeypatch):
    service = _load_service_module(monkeypatch)
    service._name_cache["rows"] = [{"GovernorID": "123", "GovernorName": "Tester"}]

    with pytest.raises(service.ArkPreferenceError, match="Preferred team must be 1 or 2"):
        asyncio.run(service.set_preference(123, 3, "discord:1"))


def test_clear_preference_soft_deletes(monkeypatch):
    service = _load_service_module(monkeypatch)
    service._name_cache["rows"] = [{"GovernorID": "123", "GovernorName": "Tester"}]

    async def _clear_team_preference(governor_id: int, updated_by: str):
        return {
            "GovernorID": governor_id,
            "PreferredTeam": 2,
            "IsActive": 0,
            "CreatedAtUTC": "created",
            "UpdatedAtUTC": "updated",
            "UpdatedBy": updated_by,
        }

    monkeypatch.setattr(service, "clear_team_preference", _clear_team_preference)

    cleared = asyncio.run(service.clear_preference(123, "discord:1"))

    assert cleared is True


def test_get_all_active_preferences_returns_map(monkeypatch):
    service = _load_service_module(monkeypatch)

    async def _list_active_team_preferences():
        return [
            {"GovernorID": 123, "PreferredTeam": 1},
            {"GovernorID": 456, "PreferredTeam": 2},
        ]

    monkeypatch.setattr(service, "list_active_team_preferences", _list_active_team_preferences)

    prefs = asyncio.run(service.get_all_active_preferences())

    assert prefs == {123: 1, 456: 2}
