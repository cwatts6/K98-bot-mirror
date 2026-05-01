# tests/test_registry_governor_registry.py
"""
Unit tests for registry.governor_registry façade.

Verifies the backward-compat shim behaviour:
  - load_registry() reads from SQL and returns the legacy dict shape.
  - load_registry() returns {} (not raise) on SQL failure and logs at ERROR.
  - KVKStatsView has been moved to ui/views/stats_views.py.
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

    monkeypatch.setattr(svc, "load_registry_as_dict", lambda **kw: _SAMPLE_DICT)
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
        svc, "load_registry_as_dict", lambda **kw: (_ for _ in ()).throw(RuntimeError("SQL down"))
    )
    result = gg.load_registry()
    assert result == {}


def test_load_registry_logs_error_on_sql_failure(monkeypatch, caplog):
    import registry.registry_service as svc

    monkeypatch.setattr(
        svc, "load_registry_as_dict", lambda **kw: (_ for _ in ()).throw(RuntimeError("SQL down"))
    )
    with caplog.at_level(logging.ERROR, logger="registry.governor_registry"):
        gg.load_registry()
    assert "FAILED" in caplog.text or "failed" in caplog.text.lower()


def test_load_registry_uses_cache_path(monkeypatch):
    """load_registry() must call load_registry_as_dict with use_cache=True."""
    import registry.registry_service as svc

    calls = []

    def _fake_load(**kw):
        calls.append(kw)
        return _SAMPLE_DICT

    monkeypatch.setattr(svc, "load_registry_as_dict", _fake_load)
    gg.load_registry()
    assert calls, "load_registry_as_dict was not called"
    assert calls[0].get("use_cache") is True


# ---------------------------------------------------------------------------
# KVKStatsView location
# ---------------------------------------------------------------------------


def test_kvkstatsview_not_in_governor_registry():
    """KVKStatsView must have been removed from governor_registry."""
    assert not hasattr(
        gg, "KVKStatsView"
    ), "KVKStatsView should no longer live in governor_registry — it was moved to ui/views/stats_views.py"


def test_kvkstatsview_importable_from_stats_views():
    """KVKStatsView must be importable from ui.views.stats_views."""
    import sys
    import types

    # Stub heavy deps that require env vars (matching test_stats_views_smoke.py pattern)
    if "utils" not in sys.modules:
        utils_stub = types.ModuleType("utils")
        utils_stub.fmt_short = lambda v: str(v)
        sys.modules["utils"] = utils_stub

    # Force re-import by temporarily removing cached module if needed
    was_present = "ui.views.stats_views" in sys.modules
    if was_present:
        # Module already cached — just check the class is there
        from ui.views.stats_views import KVKStatsView  # must not raise
    else:
        try:
            from ui.views.stats_views import KVKStatsView  # noqa: F401  # must not raise
        except RuntimeError as exc:
            if "OUR_KINGDOM" in str(exc) or "env var" in str(exc).lower():
                import pytest

                pytest.skip(f"Skipped: env vars not available in test environment — {exc}")
            raise


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
