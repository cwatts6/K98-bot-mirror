# tests/test_usage_pruning.py
"""
Tests for prune_usage_jsonl: filename parsing, pruning decisions,
malformed filename safety, current-day protection, and dry-run mode.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
import os
import sys
import tempfile
import types

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

from usage_tracker import prune_usage_jsonl

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date(2026, 4, 21)  # fixed anchor for tests
OLD_DATE = date(2026, 3, 1)  # 51 days before TODAY → older than 30-day default
RECENT_DATE = date(2026, 4, 10)  # 11 days before TODAY → within 30-day default


def _write(directory: str, filename: str, content: str = "{}") -> str:
    path = os.path.join(directory, filename)
    with open(path, "w") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# Tests: basic pruning
# ---------------------------------------------------------------------------


def test_prune_removes_old_command_usage_file():
    with tempfile.TemporaryDirectory() as d:
        old_file = f"command_usage_{OLD_DATE.strftime('%Y%m%d')}.jsonl"
        _write(d, old_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert old_file in result["removed"]
        assert not os.path.exists(os.path.join(d, old_file))


def test_prune_removes_old_metrics_file():
    with tempfile.TemporaryDirectory() as d:
        old_file = f"metrics_{OLD_DATE.strftime('%Y%m%d')}.jsonl"
        _write(d, old_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert old_file in result["removed"]


def test_prune_removes_old_alerts_file():
    with tempfile.TemporaryDirectory() as d:
        old_file = f"alerts_{OLD_DATE.strftime('%Y%m%d')}.jsonl"
        _write(d, old_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert old_file in result["removed"]


def test_prune_keeps_recent_file():
    """Files within the retention window should be kept."""
    with tempfile.TemporaryDirectory() as d:
        recent_file = f"command_usage_{RECENT_DATE.strftime('%Y%m%d')}.jsonl"
        _write(d, recent_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert recent_file in result["kept"]
        assert os.path.exists(os.path.join(d, recent_file))


def test_prune_never_deletes_todays_file():
    """The current-day file must never be deleted."""
    with tempfile.TemporaryDirectory() as d:
        today_file = f"command_usage_{TODAY.strftime('%Y%m%d')}.jsonl"
        _write(d, today_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert today_file in result["kept"]
        assert os.path.exists(os.path.join(d, today_file))


def test_prune_never_deletes_future_file():
    """A file dated in the future should be kept."""
    with tempfile.TemporaryDirectory() as d:
        future_date = date(2026, 12, 31)
        future_file = f"command_usage_{future_date.strftime('%Y%m%d')}.jsonl"
        _write(d, future_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert future_file in result["kept"]
        assert os.path.exists(os.path.join(d, future_file))


# ---------------------------------------------------------------------------
# Tests: dry-run mode
# ---------------------------------------------------------------------------


def test_prune_dry_run_does_not_delete():
    with tempfile.TemporaryDirectory() as d:
        old_file = f"command_usage_{OLD_DATE.strftime('%Y%m%d')}.jsonl"
        path = _write(d, old_file)
        result = prune_usage_jsonl(d, dry_run=True, today=TODAY)
        assert old_file in result["removed"]  # reported as "would remove"
        assert os.path.exists(path), "dry_run=True must not actually delete the file"


# ---------------------------------------------------------------------------
# Tests: malformed filenames
# ---------------------------------------------------------------------------


def test_prune_skips_malformed_date():
    """Files with an unparseable date should be skipped, not deleted."""
    with tempfile.TemporaryDirectory() as d:
        bad_file = "command_usage_99991399.jsonl"  # month=13, invalid
        path = _write(d, bad_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert bad_file in result["skipped"]
        assert os.path.exists(path), "Malformed filename must not be deleted"


def test_prune_ignores_non_jsonl_files():
    """Non-JSONL files and unrecognised patterns must not be touched."""
    with tempfile.TemporaryDirectory() as d:
        unrelated_files = [
            "event_cache.json",
            "player_stats_cache.json",
            "some_log.csv",
            "command_usage_notes.txt",  # wrong extension
            "my_data.jsonl",  # wrong prefix
        ]
        for f in unrelated_files:
            _write(d, f)
        result = prune_usage_jsonl(d, today=TODAY)
        for f in unrelated_files:
            assert f not in result["removed"], f"{f!r} should not be touched by pruning"
            assert os.path.exists(os.path.join(d, f)), f"{f!r} must not be deleted"


# ---------------------------------------------------------------------------
# Tests: retention=0 disables pruning for that family
# ---------------------------------------------------------------------------


def test_prune_zero_retention_keeps_old_file(monkeypatch):
    """When USAGE_JSONL_RETENTION_DAYS=0, old command_usage files should be kept."""
    monkeypatch.setattr(_ut, "USAGE_JSONL_RETENTION_DAYS", 0)
    # Rebuild families tuple to pick up the patched value
    monkeypatch.setattr(
        _ut,
        "_JSONL_FAMILIES",
        (
            ("command_usage_", 0),
            ("metrics_", _ut.USAGE_METRICS_JSONL_RETENTION_DAYS),
            ("alerts_", _ut.USAGE_ALERTS_JSONL_RETENTION_DAYS),
        ),
    )
    with tempfile.TemporaryDirectory() as d:
        old_file = f"command_usage_{OLD_DATE.strftime('%Y%m%d')}.jsonl"
        path = _write(d, old_file)
        result = prune_usage_jsonl(d, today=TODAY)
        assert old_file in result["kept"]
        assert os.path.exists(path)


# ---------------------------------------------------------------------------
# Tests: return value structure
# ---------------------------------------------------------------------------


def test_prune_return_has_expected_keys():
    with tempfile.TemporaryDirectory() as d:
        result = prune_usage_jsonl(d, today=TODAY)
        assert set(result.keys()) == {"kept", "removed", "skipped"}


def test_prune_mixed_files():
    """Mix of old, recent, current, and unrelated files — each handled correctly."""
    with tempfile.TemporaryDirectory() as d:
        old_file = f"command_usage_{OLD_DATE.strftime('%Y%m%d')}.jsonl"
        recent_file = f"command_usage_{RECENT_DATE.strftime('%Y%m%d')}.jsonl"
        today_file = f"command_usage_{TODAY.strftime('%Y%m%d')}.jsonl"
        unrelated = "event_cache.json"

        for f in (old_file, recent_file, today_file, unrelated):
            _write(d, f)

        result = prune_usage_jsonl(d, today=TODAY)

        assert old_file in result["removed"]
        assert recent_file in result["kept"]
        assert today_file in result["kept"]
        assert unrelated not in result["removed"]
