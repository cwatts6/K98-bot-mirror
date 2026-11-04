"""Offline presentation, ownership, interaction and lifecycle regression coverage."""

import ast
import asyncio
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from services import operator_status_service as status
from services.gsheets_health_service import HealthProbe
from services.health_observation import Observation
from ui.views.health_view import HealthView, build_health_embed

NOW = datetime(2026, 11, 4, 21, 0, tzinfo=UTC)


def bot_functions(*names, **namespace):
    tree = ast.parse(Path("bot_instance.py").read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if getattr(node, "name", None) in names]
    assert len(nodes) == len(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "health-adapters", "exec"), namespace)
    return namespace


def forbidden(*args, **kwargs):
    pytest.fail("Presentation performed work or acquired a lock")


@pytest.mark.parametrize(
    "minutes,freshness", [(0, "fresh"), (60, "fresh"), (61, "stale"), (-1, "unknown")]
)
def test_observation_age_is_not_render_time(minutes, freshness):
    stamp = (NOW - timedelta(minutes=minutes)).isoformat()
    item = Observation("SQL", "check", stamp, "settled", "success")
    result = item.project(NOW)
    assert result["observed_utc"] == stamp
    assert result["freshness"] == freshness


def test_missing_sources_never_import_bootstrap_or_probe(monkeypatch):
    for name in (
        "profile_cache",
        "services.recovery_health",
        "services.event_delivery_service",
        "core.startup_diagnostics",
    ):
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(status._probe, "observe", forbidden)
    monkeypatch.setattr(status, "check_sql", forbidden)
    before = set(sys.modules)
    for _ in range(30):
        projection = status.snapshot(NOW, 100)
        build_health_embed(projection)
    assert set(sys.modules) == before
    assert projection["components"]["profiles"]["reason"] == "source_unavailable"
    assert "All systems operational" not in str(build_health_embed(projection).to_dict())
    assert len(json.dumps(projection).encode()) < 16384


@pytest.mark.asyncio
async def test_late_result_snapshot_does_not_consume_or_replace_owned_thread():
    probe = HealthProbe()
    entered, release = threading.Event(), threading.Event()
    calls = []

    def work():
        calls.append(1)
        entered.set()
        release.wait(5)
        return False, "private failure text"

    async def run():
        return await asyncio.to_thread(work)

    try:
        assert (await probe.observe(run, timeout=0.01, scope="a"))[0] is None
        assert entered.is_set()
        task = probe._task
        assert (await probe.observe(run, timeout=0.01, scope="b"))[0] is None
        assert probe.snapshot(scope="b")[0].reason == "scope_mismatch"
        assert probe.snapshot(scope="a")[0].execution == "in_progress"
        release.set()
        await task
        for _ in range(100):
            current, latest, failure = probe.snapshot(scope="a")
            assert current.outcome == latest.outcome == failure.outcome == "failure"
            assert probe._task is task
        assert calls == [1]
        assert "private" not in repr(probe.snapshot())
        assert (await probe.observe(run, timeout=1, scope="a"))[0] is False
        assert probe._task is None
    finally:
        release.set()
        await probe.shutdown()


@pytest.mark.asyncio
async def test_success_retains_failure_and_scope_change_does_not_relabel():
    probe = HealthProbe()
    await probe.observe(AsyncMock(return_value=(False, "private")), timeout=1, scope="a")
    failed = probe.snapshot()[2]
    await probe.observe(AsyncMock(return_value=(True, "OK")), timeout=1, scope="a")
    assert probe.snapshot()[0].outcome == "success"
    assert probe.snapshot()[2] is failed
    await probe.observe(AsyncMock(return_value=(None, "busy")), timeout=1, scope="b")
    assert probe.snapshot()[0].outcome == "deferred"
    assert probe.snapshot()[2] is None


@pytest.mark.asyncio
async def test_optional_probe_publication_failure_preserves_result(monkeypatch):
    from services import gsheets_health_service as module

    monkeypatch.setattr(module, "utc", Mock(side_effect=ValueError("bad clock")))
    result = (True, "original")
    probe = HealthProbe()
    assert await probe.observe(AsyncMock(return_value=result), timeout=1) is result
    await probe.shutdown()


def test_readers_never_acquire_writer_locks(monkeypatch):
    from services import recovery_health
    from services.profile_cache_service import ProfileCacheService

    profile = ProfileCacheService()
    recovery_health.begin_cycle()
    old = recovery_health.health_snapshot()
    with pytest.raises(FrozenInstanceError):
        old[0].reason = "mutate"
    entered, release = threading.Event(), threading.Event()

    def hold():
        with profile._state, recovery_health._lock:
            entered.set()
            release.wait(5)

    worker = threading.Thread(target=hold)
    worker.start()
    try:
        assert entered.wait(1)
        monkeypatch.setitem(
            sys.modules, "profile_cache", SimpleNamespace(health_snapshot=profile.health_snapshot)
        )
        for _ in range(100):
            assert recovery_health.health_snapshot() is old
            assert (
                status.snapshot(NOW, 100)["components"]["profiles"]["reason"]
                != "source_unavailable"
            )
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()


def test_recovery_freshness_progress_and_stall_are_separate(monkeypatch):
    from services import recovery_health as monitor

    def publish(started=None, progress=None, failed=False):
        monkeypatch.setattr(
            monitor,
            "_health",
            (
                Observation("recovery", "monitor", NOW.isoformat()),
                (NOW - timedelta(seconds=91)).isoformat(),
                started,
                progress,
                failed,
                False,
            ),
        )

    publish()
    assert status.snapshot(NOW, 1000)["components"]["recovery"]["reason"] == "monitor_unestablished"
    publish(900, 999)
    assert status.snapshot(NOW, 1000)["components"]["recovery"]["reason"] == "monitor_progressing"
    publish(600, 699)
    assert status.snapshot(NOW, 1000)["components"]["recovery"]["reason"] == "monitor_stalled"


@pytest.mark.asyncio
async def test_event_summary_reads_no_journal(monkeypatch):
    from services import event_delivery_service as delivery

    monkeypatch.setattr(delivery, "receipt_rows", forbidden)
    monkeypatch.setattr(delivery.store, "rows", forbidden)
    monkeypatch.setattr(
        delivery,
        "_observation",
        dict(observed_utc=None, counts={}, changes_since_observation=False),
    )
    assert "unknown" in await delivery.evidence_summary()
    monkeypatch.setattr(
        delivery,
        "_observation",
        dict(
            observed_utc=NOW.isoformat(), counts={"acknowledged": 2}, changes_since_observation=True
        ),
    )
    assert "acknowledged=2" in await delivery.evidence_summary()
    assert "changes since observation=True" in await delivery.evidence_summary()


def interaction():
    return SimpleNamespace(
        guild_id=1,
        channel_id=2,
        message=SimpleNamespace(id=3, edit=AsyncMock()),
        response=SimpleNamespace(
            is_done=lambda: False, defer=AsyncMock(), send_message=AsyncMock()
        ),
        followup=SimpleNamespace(send=AsyncMock()),
    )


@pytest.mark.asyncio
async def test_persistent_refresh_acknowledges_before_render_and_after_idle(monkeypatch):
    click = interaction()
    render = Mock(
        side_effect=lambda: (
            click.response.defer.assert_awaited_once(),
            build_health_embed(status.snapshot()),
        )[1]
    )
    view = HealthView(guild_id=1, channel_id=2, render=render)
    view.message_id = 3
    assert view.is_persistent() and view.timeout is None
    bot = discord.Client(intents=discord.Intents.none())
    bot.add_view(view, message_id=3)
    assert view in bot.persistent_views
    monkeypatch.setattr("discord.ui.view.time.monotonic", lambda: 10**10)
    await view.children[0].callback(click)
    click.response.defer.assert_awaited_once_with(ephemeral=False, invisible=True)
    click.message.edit.assert_awaited_once()
    assert len(view.children) == 1
    view.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["guild", "channel", "message", "ack", "closed"])
async def test_refresh_rejection_never_renders_or_edits(failure):
    click = interaction()
    render = Mock(side_effect=forbidden)
    view = HealthView(guild_id=1, channel_id=2, render=render)
    view.message_id = 3
    if failure == "guild":
        click.guild_id = 9
    if failure == "channel":
        click.channel_id = 9
    if failure == "message":
        click.message.id = 9
    if failure == "ack":
        click.response.defer.side_effect = RuntimeError("token")
    if failure == "closed":
        view.close_admission()
    await view.children[0].callback(click)
    render.assert_not_called()
    click.message.edit.assert_not_awaited()
    click.followup.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_failure_never_reposts_and_shutdown_waits_for_edit():
    click = interaction()
    entered, release = asyncio.Event(), asyncio.Event()

    async def edit(**kwargs):
        entered.set()
        await release.wait()
        raise RuntimeError("private text")

    click.message.edit.side_effect = edit
    view = HealthView(
        guild_id=1, channel_id=2, render=lambda: build_health_embed(status.snapshot())
    )
    view.message_id = 3
    callback = asyncio.create_task(view.children[0].callback(click))
    await entered.wait()
    draining = asyncio.create_task(view.shutdown())
    await asyncio.sleep(0)
    assert not draining.done()
    release.set()
    await asyncio.gather(callback, draining)
    click.followup.send.assert_not_awaited()
    assert view._active is None


def alert_namespace():
    owner = SimpleNamespace(send=AsyncMock())
    ns = bot_functions(
        "_health_alerts",
        bot=SimpleNamespace(fetch_user=AsyncMock(return_value=owner)),
        _shutdown_once=asyncio.Event(),
        is_pytest_logging_mode=lambda: False,
        _last_health_alert_ts=None,
        _last_health_embed_update_ts=None,
        _health_alert_attempts={},
        _aware=lambda x: x,
        utcnow=lambda: NOW,
        STALENESS_THRESHOLD_MIN=15,
        _health_registered_id=3,
        GUILD_ID=1,
        STATUS_CHANNEL_ID=2,
        ADMIN_USER_ID=4,
        discord=discord,
        logger=Mock(),
    )
    return ns, owner


@pytest.mark.asyncio
async def test_only_actionable_failure_alerts_once_even_after_uncertain_delivery():
    ns, owner = alert_namespace()
    projection = status.snapshot(NOW, 100)
    row = projection["components"]["sql"]
    row.update(outcome="failure", freshness="fresh", reference="sql-1", action=None)
    await ns["_health_alerts"](projection)
    owner.send.assert_not_awaited()
    row["action"] = "verify_access"
    owner.send.side_effect = RuntimeError("lost response")
    await ns["_health_alerts"](projection)
    assert ns["_health_alert_attempts"]["sql"] == ("sql-1", "attempted_unconfirmed")
    ns["utcnow"] = lambda: NOW + timedelta(hours=1)
    await ns["_health_alerts"](projection)
    owner.send.assert_awaited_once()
    assert "https://discord.com/channels/1/2/3" in owner.send.call_args.args[0]


@pytest.mark.asyncio
async def test_cooldown_rechecks_current_state_without_probe():
    ns, owner = alert_namespace()
    ns["_last_health_alert_ts"] = NOW
    projection = status.snapshot(NOW, 100)
    row = projection["components"]["sql"]
    row.update(outcome="failure", freshness="fresh", reference="sql-1", action="verify_access")
    await ns["_health_alerts"](projection)
    ns["utcnow"] = lambda: NOW + timedelta(minutes=31)
    row["outcome"] = "success"
    await ns["_health_alerts"](projection)
    owner.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_transient_message_fetch_and_uncertain_send_never_repost():
    ns = bot_functions(
        "_ensure_pinned_health_message",
        _health_registered_id=3,
        _restore_health_view=lambda: 3,
        _shutdown_once=asyncio.Event(),
        _health_creation_unconfirmed=False,
        discord=discord,
        logger=Mock(),
    )
    channel = SimpleNamespace(
        fetch_message=AsyncMock(side_effect=RuntimeError("network")), send=AsyncMock()
    )
    assert await ns["_ensure_pinned_health_message"](channel) is None
    channel.send.assert_not_awaited()
    ns.update(
        _health_registered_id=None,
        _restore_health_view=lambda: None,
        _health_card=lambda: None,
        _get_health_view=lambda: None,
    )
    channel.send.side_effect = RuntimeError("send uncertain")
    with pytest.raises(RuntimeError):
        await ns["_ensure_pinned_health_message"](channel)
    assert await ns["_ensure_pinned_health_message"](channel) is None
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_card_registration_is_bounded_and_restart_uses_stable_id():
    def setup(client):
        return bot_functions(
            "_get_health_view",
            "_bind_health_view",
            bot=client,
            GUILD_ID=1,
            STATUS_CHANNEL_ID=2,
            _health_card=lambda: None,
            _health_view=None,
            _health_registered_id=None,
        )

    bot = discord.Client(intents=discord.Intents.none())
    ns = setup(bot)
    for _ in range(100):
        ns["_bind_health_view"](3)
    assert len(bot.persistent_views) == 1
    old = ns["_health_view"]
    ns["_bind_health_view"](4)
    assert old.is_finished()
    assert len(bot.persistent_views) == 1
    successor = discord.Client(intents=discord.Intents.none())
    new = setup(successor)["_bind_health_view"](4)
    assert new.children[0].custom_id == ns["_health_view"].children[0].custom_id
    assert new.message_id == 4


def test_command_and_all_adapters_have_no_active_health_edges():
    tree = ast.parse(Path("commands/admin_cmds.py").read_text(encoding="utf-8"))
    command = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "status_command"
    )
    assert "_health_card" in ast.unparse(command)
    for path in ("bot_instance.py", "ui/views/health_view.py"):
        source = Path(path).read_text(encoding="utf-8")
        for name in (
            "_check_sql_health",
            "_check_gsheets_health",
            "_count_errors_last_minutes",
            "show_last_errors",
        ):
            assert name not in source
    for name in ("check_sql", "check_health", "evidence_summary"):
        assert name not in ast.unparse(command)


def test_ordinary_report_uses_optional_passive_projection(monkeypatch):
    from services import recovery_report

    monkeypatch.setattr(status, "check_sql", forbidden)
    result = recovery_report._monitor_report()
    assert "health_observations_v1" in result
    assert "health_observations_v1" in result["component_coverage"]


@pytest.mark.asyncio
async def test_real_command_body_and_scheduled_adapter_share_passive_card(monkeypatch):
    from core.private_status_response import PrivateStatusResponse
    from services import event_delivery_service as events, gsheets_health_service as sheets

    monkeypatch.setattr(status, "check_sql", forbidden)
    monkeypatch.setattr(sheets, "check_health", forbidden)
    monkeypatch.setattr(events, "receipt_rows", forbidden)
    projection = status.snapshot(NOW, 100)
    card = lambda *_: build_health_embed(projection)
    message = SimpleNamespace(edit=AsyncMock())
    channel = SimpleNamespace(
        guild=SimpleNamespace(id=1), fetch_message=AsyncMock(return_value=message)
    )
    ns = bot_functions(
        "_update_health_embed",
        _shutdown_once=asyncio.Event(),
        _health_projection=lambda: projection,
        _health_card=card,
        bot=SimpleNamespace(get_channel=lambda _: channel),
        GUILD_ID=1,
        STATUS_CHANNEL_ID=2,
        _ensure_pinned_health_message=AsyncMock(return_value=3),
        _bind_health_view=lambda _: None,
        _health_alerts=AsyncMock(),
        _aware=lambda x: x,
        utcnow=lambda: NOW,
        logger=Mock(),
    )
    await ns["_update_health_embed"]()
    assert ns["_last_health_embed_update_ts"] == NOW
    tree = ast.parse(Path("commands/admin_cmds.py").read_text(encoding="utf-8"))
    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "status_command"
    )
    node.decorator_list = []
    command_ns = {"_validated_operator_embed": lambda value: value}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "status-command", "exec"), command_ns)
    monkeypatch.setitem(sys.modules, "bot_instance", SimpleNamespace(_health_card=card))
    monkeypatch.setitem(
        sys.modules, "ui.views.recovery_view", SimpleNamespace(RecoveryEntryView=lambda: None)
    )
    response = SimpleNamespace(acknowledge=AsyncMock(return_value=True), complete=AsyncMock())
    monkeypatch.setattr(
        sys.modules[PrivateStatusResponse.__module__], "PrivateStatusResponse", lambda _: response
    )
    await command_ns["status_command"](object())
    assert (
        response.complete.call_args.kwargs["embed"].to_dict()
        == message.edit.call_args.kwargs["embed"].to_dict()
    )
    response.acknowledge.return_value = False
    response.complete.reset_mock()
    await command_ns["status_command"](object())
    response.complete.assert_not_awaited()


@pytest.mark.asyncio
async def test_stop_dashboard_drains_and_does_not_self_cancel():
    entered, release = asyncio.Event(), asyncio.Event()

    async def loop():
        try:
            entered.set()
            await asyncio.Future()
        finally:
            await release.wait()

    task = asyncio.create_task(loop())
    await entered.wait()
    handle = SimpleNamespace(get_task=lambda: task, cancel=task.cancel, stop=Mock())
    ns = bot_functions(
        "_stop_health_dashboard", health_dashboard_task=handle, _health_view=None, asyncio=asyncio
    )
    shutdown = asyncio.create_task(ns["_stop_health_dashboard"]())
    await asyncio.sleep(0)
    assert not shutdown.done()
    release.set()
    await shutdown
    assert task.done()
    handle.get_task = asyncio.current_task
    handle.cancel = Mock(side_effect=forbidden)
    await ns["_stop_health_dashboard"]()
    handle.stop.assert_called_once()


def test_complete_report_health_component_is_optional_and_bounded(monkeypatch):
    from services import recovery_evidence_bundle as bundle

    monkeypatch.setattr(status, "check_sql", forbidden)
    components, coverage, _ = bundle.collect_components()
    health = json.loads(components["health-observations.json"])
    assert health["schema"] == "health_observations_v1"
    assert len(components["health-observations.json"]) < 16384
    assert coverage["health-observations.json"]["status"] == "available"
    monkeypatch.setattr(status, "snapshot", Mock(side_effect=ValueError("optional source")))
    components, coverage, _ = bundle.collect_components()
    assert coverage["health-observations.json"]["status"] != "available"
    assert "startup.json" in components


def test_startup_publication_is_bounded_and_does_not_copy_arbitrary_payloads(monkeypatch):
    from core import startup_diagnostics as startup

    monkeypatch.setattr(startup, "_health", ())
    monkeypatch.setattr(startup, "_steps", {})
    for label in startup._HEALTH_STEPS:
        startup._record(
            label,
            "completed",
            1,
            feature={"feature_outcome": "succeeded"},
            private="secret" * 100000,
        )
    for _ in range(50):
        startup._record(
            "warm_profile_cache", "completed", 1, feature={"feature_outcome": "partial"}
        )
    records = startup.health_snapshot()
    assert len(records) == 4
    assert records[-1].outcome == "partial"
    assert "secret" not in repr(records)
