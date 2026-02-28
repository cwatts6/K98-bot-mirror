# tests/test_rehydrate_sanitize_and_fileio.py
"""
Tests for:
 - rehydrate_views._sanitize_prefix behavior (sanitization, fallback, truncation)
 - file_utils.atomic_write_json + file_utils.read_json_safe basic semantics (atomic write/read)
"""

from datetime import UTC, datetime
import json

from file_utils import atomic_write_json, read_json_safe
import rehydrate_views


def test_sanitize_prefix_basic_cases():
    # None / empty -> fallback non-empty token
    p1 = rehydrate_views._sanitize_prefix(None)
    assert isinstance(p1, str) and p1 != ""
    assert " " not in p1

    # String with disallowed chars -> underscores normalized
    s = "Hello, world! @# $%^&*()"
    out = rehydrate_views._sanitize_prefix(s)
    assert " " not in out
    assert "," not in out
    assert out.count("_") >= 1

    # Very long string -> truncated to limit
    long_s = "x" * (rehydrate_views._PREFIX_MAX_LEN + 50)
    out_long = rehydrate_views._sanitize_prefix(long_s)
    assert len(out_long) <= rehydrate_views._PREFIX_MAX_LEN


def test_atomic_write_and_read_json_safe_and_missing_file(tmp_path):
    # create a temporary file path
    tmp_file = tmp_path / "atomic_test.json"
    data = {"a": 1, "b": "text", "ts": datetime.now(UTC).isoformat()}

    # Atomic write
    atomic_write_json(str(tmp_file), data)

    # read back via read_json_safe
    loaded = read_json_safe(str(tmp_file), default=None)
    assert isinstance(loaded, dict)
    assert loaded.get("a") == 1
    assert loaded.get("b") == "text"
    assert "ts" in loaded

    # read_json_safe returns default for missing file
    missing = read_json_safe(str(tmp_path / "does_not_exist.json"), default={"x": "y"})
    assert missing == {"x": "y"}

    # ensure file contains valid JSON
    with open(tmp_file, encoding="utf-8") as f:
        raw = json.load(f)
    assert raw == loaded
