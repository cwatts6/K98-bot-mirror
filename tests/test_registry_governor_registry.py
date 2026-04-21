# tests/test_registry_governor_registry.py
"""
Unit tests for registry.governor_registry façade.

Verifies the backward-compat shim behaviour introduced in Phase 3:
  - load_registry() reads from SQL and returns the legacy dict shape.
  - load_registry() returns {} (not raise) on SQL failure and logs at ERROR.
  - save_registry() is a no-op that logs a warning and does not write.
"""

import logging

import registry.governor_registry as gg

_SAMPLE_DICT = {
    "111": {
        "discord_id": "111",
        "discord_name": "Alice",
        "accounts": {
            "Main": {"GovernorID": "2441482", "GovernorName": "Chrislos"},
        },
    }
}


# ---------------------------------------------------------------------------
# load_registry()
# ---------------------------------------------------------------------------


def test_load_registry_returns_sql_data(monkeypatch):
    import registry.registry_service as svc

    monkeypatch.setattr(svc, "load_registry_as_dict", lambda: _SAMPLE_DICT)
    result = gg.load_registry()
    assert "111" in result
    assert result["111"]["accounts"]["Main"]["GovernorID"] == "2441482"


def test_load_registry_returns_empty_dict_on_sql_failure(monkeypatch):
    """
    Phase 6 requirement: load_registry() must not raise on SQL failure.
    It must return {} and log at ERROR level so the caller can detect degraded state.
    """
    import registry.registry_service as svc

    monkeypatch.setattr(
        svc, "load_registry_as_dict", lambda: (_ for _ in ()).throw(RuntimeError("SQL down"))
    )
    result = gg.load_registry()
    assert result == {}


def test_load_registry_logs_error_on_sql_failure(monkeypatch, caplog):
    import registry.registry_service as svc

    monkeypatch.setattr(
        svc, "load_registry_as_dict", lambda: (_ for _ in ()).throw(RuntimeError("SQL down"))
    )
    with caplog.at_level(logging.ERROR, logger="registry.governor_registry"):
        gg.load_registry()
    assert "FAILED" in caplog.text or "failed" in caplog.text.lower()


# ---------------------------------------------------------------------------
# save_registry()
# ---------------------------------------------------------------------------


def test_save_registry_is_noop_does_not_raise(monkeypatch):
    """save_registry() must not raise — it is a deprecated no-op."""
    gg.save_registry({"some": "data"})  # must not raise


def test_save_registry_logs_warning(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger="registry.governor_registry"):
        gg.save_registry({})
    assert "no-op" in caplog.text.lower() or "save_registry" in caplog.text


# ---------------------------------------------------------------------------
# get_user_main_governor_id() / get_user_main_governor_name()
# ---------------------------------------------------------------------------


def test_get_user_main_governor_id_from_dict(monkeypatch):
    gid = gg.get_user_main_governor_id(_SAMPLE_DICT, 111)
    assert gid == "2441482"


def test_get_user_main_governor_id_fallback_to_sql(monkeypatch):
    """If not in dict, falls back to registry_service.get_user_main_governor_id."""
    import registry.registry_service as svc

    monkeypatch.setattr(svc, "get_user_main_governor_id", lambda uid: "9999999")
    gid = gg.get_user_main_governor_id({}, 111)
    assert gid == "9999999"


def test_get_user_main_governor_id_returns_none_when_no_main(monkeypatch):
    import registry.registry_service as svc

    monkeypatch.setattr(svc, "get_user_main_governor_id", lambda uid: None)
    gid = gg.get_user_main_governor_id({}, 999)
    assert gid is None
