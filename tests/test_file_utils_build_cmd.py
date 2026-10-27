# tests/test_file_utils_build_cmd.py
# Ensures run_maintenance_subprocess(build_only=True) returns a sensible command and that normalize_args is used by top-level wrapper.

import asyncio

import file_utils as fu


def test_run_maintenance_subprocess_build_only_with_single_string_arg():
    s = r"C:\tmp\dummy.xlsx"
    cmd = asyncio.run(
        fu.run_maintenance_subprocess(
            "forts_ingest:import_rally_daily_xlsx", args=[s], build_only=True
        )
    )
    assert isinstance(cmd, list)
    # The path should appear as a single token, not exploded into characters
    assert any(tok == s for tok in cmd), f"path token not found: {cmd}"


def test_normalize_args_for_maintenance_behavior():
    s = r"C:\tmp\dummy.xlsx"
    # scalar should become one-element list
    assert fu.normalize_args_for_maintenance(s) == [s]
    # list-of-chars should be preserved (caller explicit)
    chars = list(s)
    assert fu.normalize_args_for_maintenance(chars) == chars
