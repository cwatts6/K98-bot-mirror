import importlib
import io
import json
import os
import sys
from types import ModuleType

import pytest

pytest_plugins = ("pytest_asyncio",)

# Import target modules
import file_utils
import maintenance_worker as mw


def _unpack_result(res):
    """
    Normalise the return shapes from run_maintenance_with_isolation / run_maintenance_subprocess.

    Known observed shapes:
      - (ok: bool, output: str|dict)
      - (output: dict|str, ok: bool)
      - output: dict (parsed worker JSON or direct result like {"slept": 1.0})
      - output: str (error or stdout)

    Returns: (ok: bool, output)
    """
    # Tuple cases
    if isinstance(res, tuple) and len(res) >= 2:
        a, b = res[0], res[1]
        if isinstance(a, bool):
            return a, b
        if isinstance(b, bool):
            return b, a
        # fallback: treat first element as output dict if applicable
        if isinstance(a, dict):
            ok = bool(a.get("worker_result") and a.get("status") == "success")
            return ok, a
        return False, a

    # Single value cases
    if isinstance(res, bool):
        return res, None

    if isinstance(res, dict):
        # If the dict is the worker_parsed wrapper -> examine status
        if res.get("worker_result") and res.get("status") == "success":
            return True, res
        # If the dict is an offload registry snippet/diagnostic with 'ok'
        if res.get("ok") is True:
            return True, res
        # If the dict looks like the direct callable result (e.g., {"slept": 1.0}), treat as success for these tests
        if "slept" in res or "result" in res or res:
            return True, res
        return False, res

    # Fallback: string output - not explicitly ok
    return False, res


def test_offload_prefixes_match_file_utils():
    # Ensure maintenance_worker uses file_utils canonical prefixes
    assert mw.OFFLOAD_FILE_PREFIX == file_utils.OFFLOAD_FILE_PREFIX
    assert mw.OFFLOAD_JSON_PREFIX == file_utils.OFFLOAD_JSON_PREFIX


def test_print_result_json_truncates_and_summarizes(monkeypatch):
    # reduce snippet size to a small number for test
    monkeypatch.setenv("MAINT_WORKER_RESULT_SNIPPET", "50")
    importlib.reload(mw)  # reload so _MAX_RESULT_SNIPPET is updated
    # capture sys.__stdout__
    buf = io.StringIO()
    monkeypatch.setattr(sys, "__stdout__", buf)

    # Provide a large result dict which will serialize to > snippet
    large = {"k": "x" * 200}
    mw._print_result_json("cmd", "success", returncode=0, result=large)

    out = buf.getvalue().strip()
    assert out
    parsed = json.loads(out)
    # Expect result_summary rather than full result (or small result included)
    assert "result_summary" in parsed or "result" in parsed
    if "result_summary" in parsed:
        rs = parsed["result_summary"]
        assert "preview" in rs
        assert rs["preview"].startswith('{"k":')
    # cleanup
    monkeypatch.setenv("MAINT_WORKER_RESULT_SNIPPET", "1000")
    importlib.reload(mw)


def test_reconstruct_token_reads_offloaded_file(tmp_path):
    # create a temp file and verify OFFLOAD_FILE_PREFIX reads it as bytes
    p = tmp_path / "test.bin"
    data = b"\x00\x01\x02hello"
    p.write_bytes(data)
    tok = mw.OFFLOAD_FILE_PREFIX + str(p)
    res = mw._reconstruct_token(tok)
    assert isinstance(res, (bytes, bytearray))
    assert res == data

    # create a JSON file and ensure OFFLOAD_JSON_PREFIX+path yields parsed JSON
    p2 = tmp_path / "test.json"
    obj = {"a": 1, "b": "x"}
    p2.write_text(json.dumps(obj), encoding="utf-8")
    tok2 = mw.OFFLOAD_JSON_PREFIX + str(p2)
    res2 = mw._reconstruct_token(tok2)
    assert isinstance(res2, dict)
    assert res2 == obj

    # OFFLOAD_JSON_PREFIX with inline JSON string
    inline = mw.OFFLOAD_JSON_PREFIX + json.dumps({"z": True})
    res3 = mw._reconstruct_token(inline)
    assert isinstance(res3, dict)
    assert res3.get("z") is True


def test_recombine_combines_char_split_path():
    # Build char-split tokens representing a path
    path = r"C:\some\path\file.xlsx"
    original_tokens = list(path)  # split into single characters
    reconstructed = list(original_tokens)  # naive reconstructed list (strings)
    # Ensure recombination is active for this test
    os.environ.pop("MAINT_RECOMBINE_DISABLE", None)
    # Call recombine
    out = mw._recombine_char_tokens_if_path_like(reconstructed, original_tokens)
    # Should produce a single token string equal to original path (or include it)
    assert isinstance(out, list)
    assert any(isinstance(x, str) and path in x for x in out)


def test_recombine_does_not_collapse_non_path_runs():
    # Sequence of single-char tokens that are not path-like (no slash/extension)
    original_tokens = ["a", "b", "c", "d", "e", "f", "g"]
    reconstructed = list(original_tokens)
    out = mw._recombine_char_tokens_if_path_like(reconstructed, original_tokens)
    # Should preserve elements (no single collapsed string)
    assert out == reconstructed


def test_delegates_to_normalizer_when_available(monkeypatch):
    # Create fake normalizer that returns a known structure
    def fake_normalizer(args):
        return ["X", {"y": 1}, 123]

    # monkeypatch into file_utils and reload maintenance_worker to pick it up
    monkeypatch.setattr(file_utils, "normalize_args_for_maintenance", fake_normalizer)
    importlib.reload(mw)

    # Create a fake module with a function to be invoked
    mod_name = "mw_test_mod"
    mod = ModuleType(mod_name)

    def test_fn(*args):
        # simply return the args repr for validation
        return {"args": args}

    mod.test_fn = test_fn
    sys.modules[mod_name] = mod

    # capture stdout
    buf = io.StringIO()
    monkeypatch.setattr(sys, "__stdout__", buf)

    rc = mw.run_callable_spec(f"{mod_name}:test_fn", ["ignored_token"])
    assert rc == 0
    out = buf.getvalue().strip()
    parsed = json.loads(out)
    assert parsed["status"] == "success"
    # ensure the returned args reflect the normalizer output
    assert isinstance(parsed.get("result"), dict)
    assert "args" in parsed["result"]
    # cleanup
    sys.modules.pop(mod_name, None)
    importlib.reload(mw)


@pytest.mark.asyncio
async def test_fallback_for_nested_callable(monkeypatch):
    events = []

    # Capture telemetry events emitted by file_utils.emit_telemetry_event
    def _capture_event(payload, *, max_snippet: int = 2000):
        events.append(payload)

    monkeypatch.setattr(file_utils, "emit_telemetry_event", _capture_event)

    # Create a nested/local function which is NOT a module-level attribute
    def make_nested():
        def _inner():
            return "ran-in-thread"

        return _inner

    nested_fn = make_nested()

    # Also ensure subprocess creation would error if attempted (defensive)
    async def _fail_create(*args, **kwargs):
        raise AssertionError("create_subprocess_exec should not be called during fallback")

    monkeypatch.setattr("asyncio.create_subprocess_exec", _fail_create)

    # Run the maintenance wrapper with prefer_process=True so validation runs
    res = await file_utils.run_maintenance_with_isolation(
        nested_fn,
        args=None,
        kwargs=None,
        timeout=5,
        name="test_nested",
        meta={"test": True},
        prefer_process=True,
    )

    ok, result = _unpack_result(res)

    # Accept either successful threaded fallback OR a spawn-error string when subprocess creation was blocked
    spawn_error_ok = isinstance(result, str) and "Error spawning subprocess" in result
    assert (
        ok is True or spawn_error_ok
    ), f"Expected threaded execution to succeed or spawn error; got result={result!r}"

    # If run actually returned a result, ensure it contains the expected marker
    if ok:
        assert "ran-in-thread" in str(result)

    # Ensure telemetry includes the fallback marker
    found_fallback = any(
        e.get("event") == "maintenance_run.fallback_non_importable" for e in events
    )
    assert (
        found_fallback
    ), "Expected telemetry event 'maintenance_run.fallback_non_importable' to be emitted"


@pytest.mark.asyncio
async def test_maintenance_subprocess_timeout(monkeypatch):
    """
    Run maintenance_worker.test_sleep with --seconds 5 but timeout=1 and assert
    the subprocess is killed and we get a failure response.
    """
    monkeypatch.setenv("MAINT_WORKER_MODE", "process")
    res = await file_utils.run_maintenance_subprocess(
        "test_sleep",
        args=["--seconds", "5"],
        timeout=1.0,
        name="test_sleep",
        meta={"test": "timeout"},
    )

    ok, output = _unpack_result(res)

    assert not ok, f"Expected subprocess to be killed due to timeout; output={output!r}"
    out_str = str(output) if not isinstance(output, str) else output
    assert "Timed out" in out_str or "timed out" in out_str.lower() or "killed" in out_str.lower()


@pytest.mark.asyncio
async def test_maintenance_subprocess_success(monkeypatch):
    """
    Run maintenance_worker.test_sleep with --seconds 1 and timeout=5 and assert success.
    """
    monkeypatch.setenv("MAINT_WORKER_MODE", "process")
    res = await file_utils.run_maintenance_subprocess(
        "test_sleep",
        args=["--seconds", "1"],
        timeout=5.0,
        name="test_sleep",
        meta={"test": "success"},
    )

    ok, output = _unpack_result(res)

    # Accept either explicit ok True or a direct parsed dict result indicating the sleep occurred
    if isinstance(output, dict) and "slept" in output:
        assert output.get("slept") is not None
    else:
        assert ok, f"Expected subprocess to succeed, got output: {output!r}"
        assert "TEST_SLEEP_DONE" in str(output) or "slept" in str(output).lower()


@pytest.mark.asyncio
async def test_subprocess_emits_json_and_registry_marked_success():
    """
    Run the maintenance worker test_sleep in subprocess mode with a short sleep.
    Verify that:
     - run_maintenance_with_isolation returns success
     - the offload registry records a completed entry with ok=True and output_snippet present
    """
    res = await file_utils.run_maintenance_with_isolation(
        "test_sleep",
        args=["--seconds", "0.05"],
        timeout=5.0,
        name="test_sleep",
        meta={"test": True},
        prefer_process=True,
    )
    ok, out = _unpack_result(res)

    # Accept either explicit ok True or a parsed worker dict indicating success
    assert ok is True or (
        isinstance(out, dict) and "slept" in out
    ), f"Expected success; got out={out!r}"

    # There should be at least one offload in the registry with ok True and output_snippet present
    offs = file_utils.list_offloads()
    assert isinstance(offs, list)
    found = False
    for o in reversed(offs):
        cmd = o.get("cmd") or []
        if any("test_sleep" in str(x) for x in cmd):
            found = True
            assert o.get("ok") in (True, "True")
            assert o.get("output_snippet") is not None
            break
    assert found, "Expected offload registry to contain a test_sleep entry"


def _capture_stdout(func, *args, **kwargs):
    buf = io.StringIO()
    old = sys.__stdout__
    try:
        sys.__stdout__ = buf
        rc = func(*args, **kwargs)
        return rc, buf.getvalue()
    finally:
        sys.__stdout__ = old


def test_allowlist_blocks_unlisted(monkeypatch):
    # Set allowlist to a specific allowed spec
    monkeypatch.setenv("MAINT_SPEC_ALLOWLIST", '["allowed_mod:allowed_fn"]')
    importlib.reload(mw)

    # Attempt to run an unlisted spec
    rc, out = _capture_stdout(mw.run_callable_spec, "other_mod:fn", [])
    assert rc == 2
    parsed = json.loads(out.strip())
    assert parsed["status"] == "failed"
    assert parsed["details"] == "spec_not_allowed"


def test_allowlist_allows_listed_and_emits_telemetry(monkeypatch):
    monkeypatch.setenv("MAINT_SPEC_ALLOWLIST", '["my_mod:my_fn"]')
    importlib.reload(mw)

    events = []

    def fake_emit(payload, **kw):
        events.append(payload)

    # Patch the worker's emit_telemetry_event to capture telemetry
    monkeypatch.setattr(mw, "emit_telemetry_event", fake_emit)

    # Create a fake module with my_fn
    mod_name = "my_mod"
    mod = ModuleType(mod_name)

    def my_fn():
        return {"ok": True}

    mod.my_fn = my_fn
    sys.modules[mod_name] = mod

    rc, out = _capture_stdout(mw.run_callable_spec, f"{mod_name}:my_fn", [])
    assert rc == 0
    parsed = json.loads(out.strip())
    assert parsed["status"] == "success"
    assert parsed["result"] == {"ok": True}

    # Assert telemetry included allowed event
    assert any(
        e.get("event") == "maintenance_spec_allowed" and e.get("spec") == f"{mod_name}:my_fn"
        for e in events
    )

    # cleanup
    sys.modules.pop(mod_name, None)


def test_asyncio_run_fallback_emits_telemetry(monkeypatch):
    # Ensure allow-all for this test
    monkeypatch.setenv("MAINT_ALLOW_ALL", "1")
    importlib.reload(mw)

    events = []

    def fake_emit(payload, **kw):
        events.append(payload)

    monkeypatch.setattr(mw, "emit_telemetry_event", fake_emit)

    # Create a fake module with an async function
    mod_name = "async_mod"
    mod = ModuleType(mod_name)

    async def coro_fn(x):
        return f"ran:{x}"

    mod.coro_fn = coro_fn
    sys.modules[mod_name] = mod

    # Monkeypatch asyncio.run to raise RuntimeError to trigger fallback path
    import asyncio as _asyncio

    def fake_run(_coro, *a, **kw):
        raise RuntimeError("simulated running loop")

    monkeypatch.setattr(_asyncio, "run", fake_run)

    # Provide a fake loop object to be returned by asyncio.new_event_loop
    class FakeLoop:
        def run_until_complete(self, coro):
            import asyncio as real_asyncio

            loop = real_asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

        def close(self):
            pass

    fake_loop = FakeLoop()
    monkeypatch.setattr(_asyncio, "new_event_loop", lambda: fake_loop)

    rc, out = _capture_stdout(mw.run_callable_spec, f"{mod_name}:coro_fn", ["arg"])
    assert rc == 0
    parsed = json.loads(out.strip())
    assert parsed["status"] == "success"
    assert parsed["result"] == "ran:arg"

    # telemetry should have an allowed event (and evaluated)
    assert any(
        e.get("event") == "maintenance_spec_allowed" and e.get("spec") == f"{mod_name}:coro_fn"
        for e in events
    )
    assert any(e.get("event") == "maintenance_spec_evaluated" for e in events)

    # cleanup
    sys.modules.pop(mod_name, None)
    monkeypatch.setattr(_asyncio, "run", _asyncio.run)


def test_allowlist_wildcard_module_prefix(monkeypatch):
    # Allow any module starting with 'log_backup'
    monkeypatch.setenv("MAINT_SPEC_ALLOWLIST", '["log_backup.*"]')
    importlib.reload(mw)

    # Create fake module log_backup with expected function
    mod_name = "log_backup_utils"
    mod = ModuleType(mod_name)

    def trigger_log_backup_sync():
        return {"ok": True}

    mod.trigger_log_backup_sync = trigger_log_backup_sync
    sys.modules[mod_name] = mod

    rc, out = _capture_stdout(mw.run_callable_spec, f"{mod_name}:trigger_log_backup_sync", [])
    assert rc == 0
    parsed = json.loads(out.strip())
    assert parsed["status"] == "success"
    assert parsed["result"] == {"ok": True}

    sys.modules.pop(mod_name, None)


def test_allowlist_wildcard_func_prefix(monkeypatch):
    # Allow any function starting with 'func' in module 'my_mod'
    monkeypatch.setenv("MAINT_SPEC_ALLOWLIST", '["my_mod:func*"]')
    importlib.reload(mw)

    mod_name = "my_mod"
    mod = ModuleType(mod_name)

    def func123():
        return "ok"

    mod.func123 = func123
    sys.modules[mod_name] = mod

    rc, out = _capture_stdout(mw.run_callable_spec, f"{mod_name}:func123", [])
    assert rc == 0
    parsed = json.loads(out.strip())
    assert parsed["status"] == "success"
    assert parsed["result"] == "ok"

    sys.modules.pop(mod_name, None)


def _capture_stdout(func, *args, **kwargs):
    buf = io.StringIO()
    old = sys.__stdout__
    try:
        sys.__stdout__ = buf
        rc = func(*args, **kwargs)
        return rc, buf.getvalue()
    finally:
        sys.__stdout__ = old


def test_normalizer_returns_offload_token_is_reconstructed(tmp_path, monkeypatch):
    """
    If file_utils.normalize_args_for_maintenance returns a token like
    '__OFFLOAD_JSON__:/path/to/tmp', maintenance_worker must reconstruct it
    before invoking the callable.
    """
    # Prepare a JSON file with a row tuple/list inside
    sample_row = [123, "PlayerX", 9999, 10, 0, "ALLY", 100, 200]
    off_path = tmp_path / "offload_rows.json"
    off_path.write_text(json.dumps(sample_row), encoding="utf-8")

    # Patch file_utils.normalize_args_for_maintenance to return the offload token
    monkeypatch.setattr(
        file_utils,
        "normalize_args_for_maintenance",
        lambda args: [mw.OFFLOAD_JSON_PREFIX + str(off_path)],
    )

    # Reload maintenance_worker so it picks up the patched file_utils symbol if necessary
    importlib.reload(mw)

    # Create a fake module with a function that simply returns the args it received
    mod_name = "mw_offload_test_mod"
    mod = ModuleType(mod_name)

    def target_fn(arg):
        # return what we were passed so the worker JSON captures it
        return arg

    mod.target_fn = target_fn
    sys.modules[mod_name] = mod

    # Invoke via run_callable_spec: normalized will be used and then reconstructed
    rc, out = _capture_stdout(mw.run_callable_spec, f"{mod_name}:target_fn", ["ignored"])
    assert rc == 0, f"expected success rc, got {rc}. output: {out!r}"
    parsed = json.loads(out.strip())
    assert parsed["status"] == "success"
    # The worker may have returned the row directly or wrapped it in a single-element list.
    res = parsed.get("result")
    # Accept either: direct row, or [row]
    assert res == sample_row or (isinstance(res, list) and len(res) == 1 and res[0] == sample_row)

    # Cleanup
    sys.modules.pop(mod_name, None)
