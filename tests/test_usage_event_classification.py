# tests/test_usage_event_classification.py
"""
Tests for is_user_facing_event() and related event classification helpers.
"""

from __future__ import annotations

from datetime import UTC, datetime
import sys
import types

import pytest

# ---------------------------------------------------------------------------
# Stub heavy deps
# ---------------------------------------------------------------------------
for _mod in ("pyodbc",):
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

_constants_stub = types.ModuleType("constants")
_constants_stub.BASE_DIR = "/tmp"
_constants_stub.DATA_DIR = "/tmp/data"
_constants_stub._conn = None
_constants_stub.USAGE_JSONL_RETENTION_DAYS = 30
_constants_stub.USAGE_METRICS_JSONL_RETENTION_DAYS = 30
_constants_stub.USAGE_ALERTS_JSONL_RETENTION_DAYS = 30
sys.modules["constants"] = _constants_stub

_utils_stub = types.ModuleType("utils")
_utils_stub.ensure_aware_utc = lambda dt: dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt
_utils_stub.utcnow = lambda: datetime.now(UTC)
sys.modules["utils"] = _utils_stub

import importlib

import usage_tracker as _ut

importlib.reload(_ut)

from usage_tracker import is_user_facing_event

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event(command_name: str, app_context: str = "slash") -> dict:
    return {
        "command_name": command_name,
        "app_context": app_context,
        "success": True,
    }


# ---------------------------------------------------------------------------
# User-facing events (should return True)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command_name",
    [
        "ping",
        "mykvktargets",
        "player_profile",
        "usage",
        "usage_detail",
        "my_registrations",
    ],
)
def test_slash_commands_are_user_facing(command_name: str):
    assert is_user_facing_event(_event(command_name, "slash")) is True


@pytest.mark.parametrize(
    "command_name",
    [
        "autocomplete:ping",
        "autocomplete:mykvktargets",
    ],
)
def test_autocomplete_events_are_user_facing(command_name: str):
    assert is_user_facing_event(_event(command_name, "autocomplete")) is True


@pytest.mark.parametrize(
    "command_name",
    [
        "register_start_button",
        "gov_select_123",
        "some_custom_id",
    ],
)
def test_component_events_are_user_facing(command_name: str):
    assert is_user_facing_event(_event(command_name, "button")) is True


# ---------------------------------------------------------------------------
# Internal pseudo-events (should return False)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command_name",
    [
        "metric:calendar_sync",
        "metric:stats_update",
        "metric:reminder_sent",
        "metric:any_name",
    ],
)
def test_metric_events_are_not_user_facing(command_name: str):
    assert is_user_facing_event(_event(command_name, "metric")) is False


@pytest.mark.parametrize(
    "command_name",
    [
        "metric_alert:calendar_sync",
        "metric_alert:high_volume",
        "metric_alert:any",
    ],
)
def test_metric_alert_events_are_not_user_facing(command_name: str):
    assert is_user_facing_event(_event(command_name, "internal")) is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_command_name_is_user_facing():
    """An empty command_name does not start with an internal prefix."""
    assert is_user_facing_event({"command_name": ""}) is True


def test_none_command_name_is_user_facing():
    """None command_name does not start with an internal prefix."""
    assert is_user_facing_event({"command_name": None}) is True


def test_missing_command_name_is_user_facing():
    """Missing command_name key treated as empty string."""
    assert is_user_facing_event({}) is True


def test_command_name_with_metric_infix_is_user_facing():
    """'mymetric:value' does not start with the internal prefix 'metric:'."""
    assert is_user_facing_event(_event("mymetric:value")) is True


def test_command_name_exact_prefix_metric():
    """'metric:' alone (no suffix) is still internal."""
    assert is_user_facing_event(_event("metric:")) is False


def test_command_name_exact_prefix_metric_alert():
    """'metric_alert:' alone is still internal."""
    assert is_user_facing_event(_event("metric_alert:")) is False
