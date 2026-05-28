from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.startup_lifecycle import StartupPhase, run_startup_phases


@pytest.mark.asyncio
async def test_run_startup_phases_runs_in_order():
    seen: list[str] = []

    async def first():
        seen.append("first")

    async def second():
        seen.append("second")

    await run_startup_phases(
        [
            StartupPhase("first", first),
            StartupPhase("second", second),
        ]
    )

    assert seen == ["first", "second"]


@pytest.mark.asyncio
async def test_run_startup_phases_propagates_phase_failure():
    async def boom():
        raise RuntimeError("phase failed")

    with pytest.raises(RuntimeError, match="phase failed"):
        await run_startup_phases([StartupPhase("boom", boom)])


def test_on_ready_uses_named_startup_lifecycle_boundary():
    src = Path("bot_instance.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    on_ready = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "on_ready"
    )

    startup_phase_names = []
    runner_calls = [
        node
        for node in ast.walk(on_ready)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_startup_phases"
    ]
    assert runner_calls
    runner_calls.sort(key=lambda node: getattr(node, "lineno", 0))

    for runner_call in runner_calls:
        phases_arg = runner_call.args[0]
        assert isinstance(phases_arg, ast.List)
        for phase_call in phases_arg.elts:
            assert isinstance(phase_call, ast.Call)
            assert isinstance(phase_call.func, ast.Name)
            assert phase_call.func.id == "StartupPhase"
            assert phase_call.args
            assert isinstance(phase_call.args[0], ast.Constant)
            assert isinstance(phase_call.args[0].value, str)
            startup_phase_names.append(phase_call.args[0].value)

    assert startup_phase_names == [
        "ready_runtime_bootstrap",
        "ready_runtime_services",
        "ready_command_sync",
        "ready_event_cache_rehydration",
        "ready_event_scheduler_tasks",
        "ready_event_cache_refresh_loop",
        "ready_view_rehydration",
        "ready_domain_scheduler_tasks",
        "ready_pinned_calendar_rehydration",
        "ready_calendar_scheduler_tasks",
    ]


def test_on_ready_command_sync_lifecycle_uses_dedicated_helper():
    src = Path("bot_instance.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    command_sync = _async_function(tree, "_run_ready_command_sync")
    on_ready = _async_function(tree, "on_ready")

    assert _calls_name(command_sync, "run_ready_command_sync")
    assert not _calls_name(on_ready, "commands_changed")
    assert not _calls_name(on_ready, "save_command_signatures")


def _async_function(tree: ast.AST, name: str) -> ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name
    )


def _calls_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == name
        for child in ast.walk(node)
    )


def _creates_task_monitor_task(node: ast.AST, task_name: str) -> bool:
    for child in ast.walk(node):
        if not (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "create"
            and isinstance(child.func.value, ast.Name)
            and child.func.value.id == "task_monitor"
            and child.args
            and isinstance(child.args[0], ast.Constant)
        ):
            continue
        if child.args[0].value == task_name:
            return True
    return False


def test_usage_tracking_lifecycle_owned_by_runtime_services_phase():
    src = Path("bot_instance.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    runtime_services = _async_function(tree, "_run_ready_runtime_services")
    full_startup = _async_function(tree, "full_startup_sequence")

    assert _calls_name(runtime_services, "start_usage_tracker")
    assert _creates_task_monitor_task(runtime_services, "usage_jsonl_prune")

    assert not _calls_name(full_startup, "start_usage_tracker")
    assert not _creates_task_monitor_task(full_startup, "usage_jsonl_prune")


def test_event_rehydration_lifecycle_uses_dedicated_helpers():
    src = Path("bot_instance.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    event_cache = _async_function(tree, "_run_ready_event_cache_rehydration")
    tracked_views = _async_function(tree, "_run_ready_view_rehydration")
    pinned_calendar = _async_function(tree, "_run_ready_pinned_calendar_rehydration")
    on_ready = _async_function(tree, "on_ready")

    assert _calls_name(event_cache, "run_ready_event_cache_rehydration")
    assert _calls_name(tracked_views, "run_ready_tracked_view_rehydration")
    assert _calls_name(pinned_calendar, "run_ready_pinned_calendar_rehydration")

    assert not _calls_name(on_ready, "load_event_cache")
    assert not _calls_name(on_ready, "load_active_reminders")
    assert not _calls_name(on_ready, "rehydrate_tracked_views")
    assert not _calls_name(on_ready, "rehydrate_pinned_calendar_view")


def test_queue_lifecycle_uses_dedicated_helper():
    src = Path("bot_instance.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    queue_lifecycle = _async_function(tree, "_run_ready_queue_lifecycle")
    full_startup = _async_function(tree, "full_startup_sequence")

    assert _calls_name(queue_lifecycle, "run_ready_queue_lifecycle")
    assert _calls_name(full_startup, "run_startup_phases")

    assert not _calls_name(full_startup, "queue_worker")
    assert not _calls_name(full_startup, "load_live_queue")
    assert not _calls_name(full_startup, "update_live_queue_embed")
    assert not _creates_task_monitor_task(full_startup, "queue_cleanup")
    assert not _creates_task_monitor_task(full_startup, "connection_watchdog")
