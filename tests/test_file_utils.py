# tests/test_file_utils.py
# Unit tests to validate the root-fix for arg normalization and maintenance command building.
# These tests are lightweight and do not spawn subprocesses or require DB access.

import asyncio
import os

import pytest

import file_utils as fu


def test_normalize_args_single_string():
    s = r"C:\discord_file_downloader\logs\downloads\Rally_data_04-12-2025.xlsx"
    normalized = fu.normalize_args_for_maintenance(s)
    assert isinstance(normalized, list)
    assert len(normalized) == 1
    assert normalized[0] == s


def test_normalize_args_list_of_chars_preserved():
    s = r"C:\discord_file_downloader\logs\downloads\Rally_data_04-12-2025.xlsx"
    char_list = list(s)
    normalized = fu.normalize_args_for_maintenance(char_list)
    # list-of-chars should be returned as-is (list preserved)
    assert isinstance(normalized, list)
    assert normalized == char_list
    assert len(normalized) == len(s)


def test_build_maintenance_cmd_with_single_string_arg():
    s = r"C:\discord_file_downloader\logs\downloads\Rally_data_04-12-2025.xlsx"
    # simulate caller that normalized args (root fix) — pass a one-element list
    cmd, temp_paths = fu.build_maintenance_cmd("forts_ingest:import_rally_daily_xlsx", args=[s])
    # The token representing the path should be present as a single argv element
    assert any(tok == s for tok in cmd), f"expected path token in cmd, got {cmd}"
    # no temp files should be created for a plain string
    assert temp_paths == []


def test_build_maintenance_cmd_with_expanded_char_list_shows_split():
    s = r"C:\discord_file_downloader\logs\downloads\Rally_data_04-12-2025.xlsx"
    char_list = list(s)
    cmd, tmp = fu.build_maintenance_cmd("forts_ingest:import_rally_daily_xlsx", args=char_list)
    # When args is an explicit list of characters, the resulting cmd will contain many tokens
    # (this demonstrates why normalization is required upstream).
    # Skip the first three tokens (python exe, script path, and command_str)
    tokens_after_base = cmd[3:]
    assert len(tokens_after_base) >= 5
    assert tokens_after_base[0] == char_list[0]


def test_integration_run_maintenance_subprocess_build_only_with_normalized_args():
    """
    Integration-style test (no subprocess spawn) that simulates the top-level wrapper
    normalizing a single string arg, then calling the maintenance subprocess builder.
    We assert the resulting cmd contains the path as a single token (not split into chars).
    """
    s = r"C:\discord_file_downloader\logs\downloads\Rally_data_04-12-2025.xlsx"
    # simulate top-level wrapper normalization
    normalized_args = fu.normalize_args_for_maintenance(s)
    # call the coroutine in build_only mode — returns the constructed cmd list
    cmd = asyncio.run(
        fu.run_maintenance_subprocess(
            "forts_ingest:import_rally_daily_xlsx",
            args=normalized_args,
            build_only=True,
        )
    )
    assert isinstance(cmd, list)
    # Ensure the path appears as one token in the command
    assert any(tok == s for tok in cmd), f"path token not found in cmd: {cmd}"
    # Ensure we don't have the pathological expansion (no sequence of single-char tokens equal to the path)
    # i.e., there shouldn't be len(s) separate single-character tokens that when joined equal the path
    # first three tokens are python exe, script, command_str
    after_base = cmd[3:]
    contiguous_chars = [t for t in after_base if isinstance(t, str) and len(t) == 1]
    assert not (len(contiguous_chars) >= len(s) and "".join(contiguous_chars[: len(s)]) == s)


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
