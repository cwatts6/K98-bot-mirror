# tests/test_offload_serialization.py
import json
import os

from file_utils import (
    OFFLOAD_FILE_PREFIX,
    OFFLOAD_JSON_PREFIX,
    build_maintenance_cmd,
    cleanup_temp_paths,
    serialize_args_for_subprocess,
)


def read_bytes_from_path_token(token: str) -> bytes:
    """Helper: token is OFFLOAD_*:<abs_path>"""
    assert ":" in token
    _, path = token.split(":", 1)
    with open(path, "rb") as f:
        return f.read()


def test_serialize_args_writes_files_and_returns_tokens(tmp_path):
    tmp_dir = str(tmp_path)
    # make representative binary (XLSX starts with PK)
    binary = b"PK\x03\x04\x00\x11\x22\x33"
    obj = {"foo": "bar", "n": 123}
    s = "hello"

    argv_tokens, temp_paths = serialize_args_for_subprocess(
        args=[binary, obj, s], kwargs=None, tmp_dir=tmp_dir
    )

    # Expect at least one OFFLOAD_FILE token and one OFFLOAD_JSON token
    assert any(t.startswith(OFFLOAD_FILE_PREFIX) for t in argv_tokens), argv_tokens
    assert any(t.startswith(OFFLOAD_JSON_PREFIX) for t in argv_tokens), argv_tokens

    # Check files exist and contents match
    file_token = next(t for t in argv_tokens if t.startswith(OFFLOAD_FILE_PREFIX))
    json_token = next(t for t in argv_tokens if t.startswith(OFFLOAD_JSON_PREFIX))

    blob = read_bytes_from_path_token(file_token)
    assert blob == binary

    json_bytes = read_bytes_from_path_token(json_token)
    # JSON file was written in UTF-8
    parsed = json.loads(json_bytes.decode("utf-8"))
    assert parsed["foo"] == "bar"
    assert parsed["n"] == 123

    # cleanup and ensure removal
    cleanup_temp_paths(temp_paths)
    for p in temp_paths:
        assert not os.path.exists(p)


def test_build_maintenance_cmd_includes_offload_token_and_cleans(tmp_path):
    tmp_dir = str(tmp_path)
    binary = b"PK\x03\x04\xaa\xbb"
    cmd, temp_paths = build_maintenance_cmd(
        "some.module:func", args=[binary], kwargs=None, tmp_dir=tmp_dir
    )

    # Third token onward should include OFFLOAD_FILE token
    assert any(t.startswith(OFFLOAD_FILE_PREFIX) for t in cmd), cmd

    # temp_paths should list created files
    assert temp_paths and all(os.path.exists(p) for p in temp_paths)

    # read back and confirm content
    file_token = next(t for t in cmd if t.startswith(OFFLOAD_FILE_PREFIX))
    _, path = file_token.split(":", 1)
    with open(path, "rb") as f:
        assert f.read() == binary

    cleanup_temp_paths(temp_paths)
    for p in temp_paths:
        assert not os.path.exists(p)
