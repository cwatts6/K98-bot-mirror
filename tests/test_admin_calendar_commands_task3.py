"""Execute actual calendar command bodies with inert Discord/service boundaries."""

import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[1]


def command(name, namespace):
    tree = ast.parse((ROOT / "commands/admin_cmds.py").read_text(encoding="utf-8"))
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    node.decorator_list = []
    compiled = compile(
        ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
        "calendar_command_fixture",
        "exec",
    )
    exec(compiled, namespace)
    return namespace[name]


@pytest.mark.parametrize(
    "name", ["calendar_refresh", "calendar_generate", "calendar_publish_cache", "calendar_status"]
)
def test_existing_authorization_decorators_and_argument_bounds_preserved(name):
    tree = ast.parse((ROOT / "commands/admin_cmds.py").read_text(encoding="utf-8"))
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    decorators = [ast.unparse(d) for d in node.decorator_list]
    assert decorators[2:] == ["safe_command", "is_admin_and_notify_channel()", "track_usage()"]
    registration = node.decorator_list[0]
    assert ast.unparse(registration.func) == "ops_group.command"
    options = {item.arg: item.value for item in registration.keywords}
    assert ast.literal_eval(options["name"]) == name
    assert ast.unparse(options["guild_ids"]) == "[GUILD_ID]"
    assert ast.unparse(node.args.args[0].annotation) == "discord.ApplicationContext"
    if name in {"calendar_generate", "calendar_publish_cache"}:
        assert node.args.args[1].arg == "horizon_days"
        horizon = {
            item.arg: ast.literal_eval(item.value) for item in node.args.defaults[0].keywords
        }
        assert horizon == dict(required=False, default=365, min_value=1, max_value=1825)
        if name == "calendar_publish_cache":
            assert node.args.args[2].arg == "force_empty"
            force = {
                item.arg: ast.literal_eval(item.value) for item in node.args.defaults[1].keywords
            }
            assert force == dict(required=False, default=False)
    else:
        assert len(node.args.args) == 1 and not node.args.defaults


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,arguments,result,expected",
    [
        (
            "calendar_refresh",
            {},
            dict(
                ok=False,
                status="busy",
                stage="not_admitted",
                severity="pending",
                details="Calendar work is still running.",
            ),
            "unknown / not reached",
        ),
        (
            "calendar_generate",
            {"horizon_days": 30},
            dict(
                ok=True,
                status="success",
                severity="warning",
                instances_generated=12,
                instances_written=12,
                details="Business acknowledged; cleanup unconfirmed.",
            ),
            "written=12",
        ),
        (
            "calendar_publish_cache",
            {"horizon_days": 30, "force_empty": False},
            dict(
                ok=True,
                status="success_index_warning",
                severity="warning",
                events_written=12,
                details="Primary published; auxiliary index unavailable.",
            ),
            "12",
        ),
    ],
)
async def test_command_defers_and_renders_truthful_outcome(name, arguments, result, expected):
    from commands import admin_cmds

    calls = []
    deliveries = []
    result = dict(result, pipeline_run_id="fixture")

    async def execute(**kwargs):
        calls.append(kwargs)
        return deepcopy(result)

    svc = SimpleNamespace(
        refresh_pipeline=execute,
        generate=execute,
        publish_cache=execute,
        record_delivery=lambda *args: deliveries.append(args),
    )
    defer = AsyncMock()
    namespace = dict(vars(admin_cmds), get_calendar_service=lambda: svc, safe_defer=defer)
    edit = AsyncMock()
    ctx = SimpleNamespace(
        user=SimpleNamespace(id=7), interaction=SimpleNamespace(edit_original_response=edit)
    )
    await command(name, namespace)(ctx, **arguments)
    defer.assert_awaited_once_with(ctx, ephemeral=True)
    assert len(calls) == 1 and calls[0]["actor_user_id"] == 7
    embed = edit.await_args.kwargs["embed"].to_dict()
    assert expected in str(embed)
    assert deliveries == [("fixture", "succeeded")]


@pytest.mark.asyncio
async def test_delivery_failure_does_not_resubmit_business():
    from commands import admin_cmds

    calls = []
    deliveries = []

    async def execute(**kwargs):
        calls.append(kwargs)
        return dict(ok=True, status="success", events_written=12, pipeline_run_id="fixture")

    svc = SimpleNamespace(
        publish_cache=execute, record_delivery=lambda *args: deliveries.append(args)
    )
    namespace = dict(vars(admin_cmds), get_calendar_service=lambda: svc, safe_defer=AsyncMock())
    ctx = SimpleNamespace(
        user=SimpleNamespace(id=7),
        interaction=SimpleNamespace(
            edit_original_response=AsyncMock(side_effect=RuntimeError("expired response"))
        ),
    )
    with pytest.raises(RuntimeError):
        await command("calendar_publish_cache", namespace)(ctx, horizon_days=30, force_empty=False)
    assert len(calls) == 1 and deliveries == [("fixture", "failed", "RuntimeError")]
