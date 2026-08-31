from __future__ import annotations

import asyncio
import inspect
import logging

import pytest

from services.mge_results_import_audit_service import MgeResultsImportAuditContext


def _load_modules(monkeypatch):
    monkeypatch.setenv("WATCHDOG_RUN", "1")
    import DL_bot
    import file_utils

    return DL_bot, file_utils


def _install_exact_runner(monkeypatch, file_utils, calls):
    async def run_blocking_in_thread(func, *args, **kwargs):
        calls.append((func, args, kwargs))
        if inspect.iscoroutinefunction(func):
            return await func()
        return func()

    monkeypatch.setattr(file_utils, "run_blocking_in_thread", run_blocking_in_thread)


def _forbid_later_backend(monkeypatch, dl_bot):
    async def unexpected_to_thread(*_args, **_kwargs):
        raise AssertionError("asyncio.to_thread must not run after backend selection")

    monkeypatch.setattr(dl_bot.asyncio, "to_thread", unexpected_to_thread)


def _forbid_process_helpers(monkeypatch, file_utils):
    async def unexpected_maintenance(*_args, **_kwargs):
        raise AssertionError("maintenance runner is not an arbitrary-callable backend")

    def unexpected_launcher(*_args, **_kwargs):
        raise AssertionError("synchronous launcher is not an arbitrary-callable backend")

    monkeypatch.setattr(
        file_utils,
        "run_maintenance_with_isolation",
        unexpected_maintenance,
        raising=True,
    )
    monkeypatch.setattr(
        file_utils,
        "start_callable_offload",
        unexpected_launcher,
        raising=True,
    )


@pytest.mark.asyncio
async def test_four_argument_mge_failure_enters_callable_once(monkeypatch):
    dl_bot, file_utils = _load_modules(monkeypatch)
    runner_calls = []
    invocations = []
    _install_exact_runner(monkeypatch, file_utils, runner_calls)
    _forbid_later_backend(monkeypatch, dl_bot)
    _forbid_process_helpers(monkeypatch, file_utils)

    context = MgeResultsImportAuditContext(
        source_filename="mge_rankings_kd1198_20260311.xlsx",
        source_message_id=111,
        source_channel_id=10,
        actor_discord_id=123456789,
        source="auto",
        entry_point="mge_results_upload",
    )
    sentinel = RuntimeError("sentinel importer failure after entry")

    def importer(file_bytes, filename, uploader_id, audit_context):
        invocations.append((file_bytes, filename, uploader_id, audit_context))
        raise sentinel

    with pytest.raises(RuntimeError) as exc_info:
        await dl_bot._offload_callable(
            importer,
            b"xlsx",
            "mge_rankings_kd1198_20260311.xlsx",
            123456789,
            context,
            name="import_results_auto",
            prefer_process=True,
            meta={"filename": context.source_filename, "channel_id": 10},
        )

    assert exc_info.value is sentinel
    assert invocations == [(b"xlsx", "mge_rankings_kd1198_20260311.xlsx", 123456789, context)]
    assert len(runner_calls) == 1
    _func, runner_args, runner_kwargs = runner_calls[0]
    assert runner_args == ()
    assert runner_kwargs == {
        "name": "import_results_auto",
        "meta": {"filename": context.source_filename, "channel_id": 10},
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected",
    [
        17,
        {"success": True, "rows": 4},
        (True, "note", 4),
        ("value", {"backend": "metadata-shaped-but-callable-owned"}),
    ],
)
async def test_success_preserves_exact_result(monkeypatch, expected):
    dl_bot, file_utils = _load_modules(monkeypatch)
    runner_calls = []
    _install_exact_runner(monkeypatch, file_utils, runner_calls)
    _forbid_later_backend(monkeypatch, dl_bot)

    def callable_result():
        return expected

    result = await dl_bot._offload_callable(callable_result, name="result_shape")

    assert result is expected
    assert len(runner_calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("args", "call_kwargs", "expected"),
    [
        ((), {}, ((), {})),
        ((1, "two"), {}, ((1, "two"), {})),
        ((), {"flag": True}, ((), {"flag": True})),
        ((1,), {"flag": False, "timeout": 9}, ((1,), {"flag": False, "timeout": 9})),
    ],
)
async def test_argument_shapes_and_controls_remain_separate(
    monkeypatch, args, call_kwargs, expected
):
    dl_bot, file_utils = _load_modules(monkeypatch)
    runner_calls = []
    _install_exact_runner(monkeypatch, file_utils, runner_calls)
    _forbid_later_backend(monkeypatch, dl_bot)

    def record_arguments(*call_args, **call_keyword_args):
        return call_args, call_keyword_args

    result = await dl_bot._offload_callable(
        record_arguments,
        *args,
        name="argument_integrity",
        meta={"safe": "control"},
        prefer_process=False,
        **call_kwargs,
    )

    assert result == expected
    _func, runner_args, runner_kwargs = runner_calls[0]
    assert runner_args == ()
    assert runner_kwargs == {
        "name": "argument_integrity",
        "meta": {"safe": "control"},
    }


@pytest.mark.asyncio
async def test_missing_thread_runner_falls_back_once_for_sync_callable(monkeypatch):
    dl_bot, file_utils = _load_modules(monkeypatch)
    monkeypatch.setattr(file_utils, "run_blocking_in_thread", None)
    invocations = []
    submissions = []

    async def fake_to_thread(func, *args, **kwargs):
        submissions.append((func, args, kwargs))
        return func(*args, **kwargs)

    monkeypatch.setattr(dl_bot.asyncio, "to_thread", fake_to_thread)

    def callable_result(value, *, flag):
        invocations.append((value, flag))
        return "ok"

    result = await dl_bot._offload_callable(callable_result, 7, flag=True)

    assert result == "ok"
    assert invocations == [(7, True)]
    assert len(submissions) == 1
    _func, fallback_args, fallback_kwargs = submissions[0]
    assert fallback_args == ()
    assert fallback_kwargs == {}


@pytest.mark.asyncio
async def test_missing_thread_runner_awaits_async_callable_once(monkeypatch):
    dl_bot, file_utils = _load_modules(monkeypatch)
    monkeypatch.setattr(file_utils, "run_blocking_in_thread", None)
    invocations = []
    _forbid_later_backend(monkeypatch, dl_bot)

    async def async_callable(value, *, flag):
        invocations.append((value, flag))
        return {"value": value, "flag": flag}

    result = await dl_bot._offload_callable(async_callable, 3, flag=False)

    assert result == {"value": 3, "flag": False}
    assert invocations == [(3, False)]


@pytest.mark.asyncio
async def test_cancellation_after_entry_does_not_fallback(monkeypatch):
    dl_bot, file_utils = _load_modules(monkeypatch)
    runner_calls = []
    invocations = []
    _install_exact_runner(monkeypatch, file_utils, runner_calls)
    _forbid_later_backend(monkeypatch, dl_bot)

    def cancelled_callable():
        invocations.append("entered")
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await dl_bot._offload_callable(cancelled_callable)

    assert invocations == ["entered"]
    assert len(runner_calls) == 1


@pytest.mark.asyncio
async def test_timeout_after_entry_does_not_fallback(monkeypatch):
    dl_bot, file_utils = _load_modules(monkeypatch)
    invocations = []
    runner_calls = []
    _forbid_later_backend(monkeypatch, dl_bot)

    async def timing_out_runner(func, *args, **kwargs):
        runner_calls.append((func, args, kwargs))
        func()
        raise TimeoutError("indeterminate after dispatch")

    monkeypatch.setattr(file_utils, "run_blocking_in_thread", timing_out_runner)

    def callable_result():
        invocations.append("entered")

    with pytest.raises(TimeoutError, match="indeterminate after dispatch"):
        await dl_bot._offload_callable(callable_result)

    assert invocations == ["entered"]
    assert len(runner_calls) == 1


@pytest.mark.asyncio
async def test_fallback_logging_excludes_callable_data(monkeypatch, caplog):
    dl_bot, file_utils = _load_modules(monkeypatch)
    monkeypatch.setattr(file_utils, "run_blocking_in_thread", None)

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(dl_bot.asyncio, "to_thread", fake_to_thread)
    caplog.set_level(logging.DEBUG, logger=dl_bot.__name__)

    secret_argument = "SUPER_SECRET_PASSWORD"
    secret_filename = "sensitive-upload.xlsx"

    def callable_result(value):
        return value

    result = await dl_bot._offload_callable(
        callable_result,
        secret_argument,
        name="safe_static_operation",
        meta={"filename": secret_filename, "password": secret_argument},
        prefer_process=True,
    )

    assert result == secret_argument
    assert "offload_backend_unavailable" in caplog.text
    assert "backend=asyncio.to_thread" in caplog.text
    assert secret_argument not in caplog.text
    assert secret_filename not in caplog.text
