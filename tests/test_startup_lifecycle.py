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

    runner_call = next(
        node
        for node in ast.walk(on_ready)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_startup_phases"
    )
    phases_arg = runner_call.args[0]
    assert isinstance(phases_arg, ast.List)

    startup_phase_names = []
    for phase_call in phases_arg.elts:
        assert isinstance(phase_call, ast.Call)
        assert isinstance(phase_call.func, ast.Name)
        assert phase_call.func.id == "StartupPhase"
        assert phase_call.args
        assert isinstance(phase_call.args[0], ast.Constant)
        assert isinstance(phase_call.args[0].value, str)
        startup_phase_names.append(phase_call.args[0].value)

    assert startup_phase_names == ["ready_runtime_bootstrap"]
