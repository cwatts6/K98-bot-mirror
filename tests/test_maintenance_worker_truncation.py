# tests/test_maintenance_worker_truncation.py
# Verifies maintenance_worker._print_result_json does not emit very large 'result' blobs.

import io
import json
import sys

import maintenance_worker as mw


def test_print_result_json_truncates_large_result(monkeypatch):
    # Create a very large result (nested dict with big string)
    big_str = "X" * 5000
    big_result = {"huge": big_str, "meta": {"a": 1}}

    fake_out = io.StringIO()
    # monkeypatch sys.__stdout__ which _print_result_json writes to
    monkeypatch.setattr(sys, "__stdout__", fake_out)

    mw._print_result_json("testcmd", "success", returncode=0, result=big_result)
    out = fake_out.getvalue().strip()
    assert out, "Expected JSON line printed to sys.__stdout__"

    parsed = json.loads(out)
    # The module should not include the full huge result; it should include 'result_summary' or truncated 'result'
    assert (
        "result_summary" in parsed or "result" in parsed
    ), "Expected either result_summary or result key to be present"
    if "result" in parsed:
        # If included, it must not be the full huge string
        serialized = json.dumps(parsed["result"], default=str)
        assert len(serialized) <= mw._MAX_RESULT_SNIPPET + 10
    if "result_summary" in parsed:
        assert parsed["result_summary"]["type"] in ("dict", "dict") or isinstance(
            parsed["result_summary"], dict
        )
        assert parsed["result_summary"]["length"] >= 5000
        assert "preview" in parsed["result_summary"]


def test_print_result_json_small_result_included(monkeypatch):
    # Small result should be included in full
    small = {"k": "short"}
    fake_out = io.StringIO()
    monkeypatch.setattr(sys, "__stdout__", fake_out)
    mw._print_result_json("cmd", "success", returncode=0, result=small)
    parsed = json.loads(fake_out.getvalue().strip())
    assert "result" in parsed
    assert parsed["result"]["k"] == "short"
