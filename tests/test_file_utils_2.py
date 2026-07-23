import json
import logging
import os

import file_utils

TELEMETRY_LOGGER = "telemetry"


def _read_json_from_temp(path):
    with open(path, "rb") as f:
        b = f.read()
    return json.loads(b.decode("utf-8"))


def test_group_args_offload_and_emits_telemetry(tmp_path, caplog):
    # Force low threshold to trigger grouping behavior for test
    file_utils.OFFLOAD_GROUP_THRESHOLD = 3

    # capture telemetry logger output
    caplog.set_level(logging.INFO, logger=TELEMETRY_LOGGER)

    # build a list of small row-like tuples (eligible for grouping)
    args = [(1, "alice", 100), (2, "bob", 200), (3, "carol", 300), (4, "dan", 400)]

    toks, paths = file_utils.serialize_args_for_subprocess(
        args=args, kwargs=None, tmp_dir=str(tmp_path)
    )

    # Expect a single OFFLOAD_JSON token for the grouped args
    assert len(toks) == 1
    assert toks[0].startswith(file_utils.OFFLOAD_JSON_PREFIX)
    assert len(paths) == 1
    assert os.path.exists(paths[0])

    # Verify the temp file contains our serialized JSON list
    loaded = _read_json_from_temp(paths[0])
    # JSON serialization converts tuples to lists; normalize the original for comparison
    expected = [list(t) for t in args]
    assert loaded == expected

    # Check telemetry emitted grouping event by parsing telemetry logger messages
    found = False
    for rec in caplog.records:
        try:
            msg = rec.getMessage()
            # telemetry logger emits JSON strings; try to parse and inspect
            payload = json.loads(msg)
            if payload.get("event") == "offload_grouping" and payload.get("target") == "args":
                found = True
                assert payload.get("count") == len(args)
                break
        except Exception:
            # fallback: simple substring check
            if "offload_grouping" in rec.getMessage():
                found = True
                break
    assert found, "Expected telemetry logger to receive an offload_grouping event"

    # cleanup
    file_utils.cleanup_temp_paths(paths)


def test_no_group_small_list_fallback(tmp_path):
    # Make threshold high so grouping does not trigger
    file_utils.OFFLOAD_GROUP_THRESHOLD = 1000

    args = [(1, "x", 10), (2, "y", 20), (3, "z", 30)]
    toks, paths = file_utils.serialize_args_for_subprocess(
        args=args, kwargs=None, tmp_dir=str(tmp_path)
    )

    # since grouping didn't trigger, expect per-arg tokens (each arg becomes OFFLOAD_JSON)
    assert len(toks) == len(args)
    assert all(t.startswith(file_utils.OFFLOAD_JSON_PREFIX) for t in toks)
    assert len(paths) == len(args)
    for p in paths:
        assert os.path.exists(p)
        # validate JSON decoding
        _ = _read_json_from_temp(p)

    file_utils.cleanup_temp_paths(paths)


def test_group_kwargs_value_offload_and_emits_telemetry(tmp_path, caplog):
    # Force low threshold to trigger grouping behavior for test
    file_utils.OFFLOAD_GROUP_THRESHOLD = 3

    caplog.set_level(logging.INFO, logger=TELEMETRY_LOGGER)
    big_list = [(1, "a", 10), (2, "b", 20), (3, "c", 30), (4, "d", 40)]
    kw = {"players": big_list}

    toks, paths = file_utils.serialize_args_for_subprocess(
        args=None, kwargs=kw, tmp_dir=str(tmp_path)
    )

    # Expect a flag + single OFFLOAD_JSON token for grouped kw value
    assert len(toks) == 2
    assert toks[0] == "--players"
    assert toks[1].startswith(file_utils.OFFLOAD_JSON_PREFIX)
    assert len(paths) == 1
    assert os.path.exists(paths[0])

    loaded = _read_json_from_temp(paths[0])
    # Normalize expected tuple->list conversion from JSON
    expected = [list(t) for t in big_list]
    assert loaded == expected

    # Check telemetry emitted grouping event for kwargs by parsing telemetry messages
    found = False
    for rec in caplog.records:
        try:
            msg = rec.getMessage()
            payload = json.loads(msg)
            if payload.get("event") == "offload_grouping" and payload.get("target") == "kwargs":
                assert payload.get("key") == "players"
                assert payload.get("count") == len(big_list)
                found = True
                break
        except Exception:
            if "offload_grouping" in rec.getMessage() and "kwargs" in rec.getMessage():
                found = True
                break

    assert found, "Expected telemetry logger to receive an offload_grouping event for kwargs"

    file_utils.cleanup_temp_paths(paths)
