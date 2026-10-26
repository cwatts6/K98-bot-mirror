"""Offline workload/barrier checks; no SQL, provider or production history."""

import ast
import asyncio
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from services import recovery_health as health, recovery_runtime as runtime


@pytest.fixture
def workload(monkeypatch):
    clock, seen, active = [0.0], [], []
    references = [f"{i:05}" for i in range(1, 17632)]
    broken = set()
    row = dict(IncidentID="active", SourceKind="stats_import", SourceID="active-source")

    def page(*, after):
        selected = [r for r in references if after is None or r > after][:100]
        return dict(
            references=selected or references[:100], wrapped=not selected and after is not None
        )

    def inspect(reference):
        seen.append(reference)
        clock[0] += 1
        if reference in broken:
            raise PermissionError("private path must not escape")
        return {}, "token", True

    def recover(identifier):
        active.append((identifier, clock[0]))
        return row

    store = SimpleNamespace(
        scope="fixture",
        list_open=lambda **_: [row],
        has_failed_checks=lambda: False,
        observe=Mock(),
        check_failed=Mock(),
        touch_pending=Mock(),
    )
    adapter = SimpleNamespace(discovery_page=page, inspect=inspect, observe_healthy=False)
    service = SimpleNamespace(
        store=store,
        adapters={
            "private_evidence": adapter,
            "stats_import": SimpleNamespace(pending_recovery=lambda **_: ["active-source"]),
        },
        recover_automatic=recover,
        refresh=recover,
    )

    @contextmanager
    def context():
        yield service

    monkeypatch.setattr(runtime, "recovery_service", context)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(runtime.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(runtime, "_cursors", {})
    monkeypatch.setattr(runtime, "_history_coverage", {})
    for name in ("_incident_cursor", "_priority_incident_cursor", "_failed_incident_cursor"):
        monkeypatch.setattr(runtime, name, None)
    monkeypatch.setattr(
        "services.recovery_backlog_dal.RecoveryBacklogDAL.pending_repairs", lambda *a: []
    )
    return SimpleNamespace(**locals())


def test_active_priority_and_bounded_history_with_17631_records(workload):
    w = workload
    health.begin_cycle()
    assert runtime.observe_recovery() == []
    assert w.active == [("active", 0)]  # Deduplicated across failed/open/priority/discovery.
    assert len(w.seen) == 10 and w.clock[0] == 10
    coverage = health.observation()["history"]
    assert coverage["budget_exhausted"] and coverage["attempted"] == 10
    assert not coverage["complete"] and not w.store.observe.called
    # New UUID-order predecessors remain eligible on the next wrap.
    w.references.insert(0, "00000")
    for _ in range(1764):
        runtime.observe_recovery()
    assert set(w.references) <= set(w.seen)
    assert health.observation()["history"]["wraps"] >= 1


def test_failure_cannot_starve_history_or_clear_on_an_unrelated_page(workload, monkeypatch):
    w = workload
    w.references[:] = ["00001", "00002", "00003"]
    w.broken.add("00001")
    monkeypatch.setattr(runtime, "HISTORY_SLICE_SECONDS", 1)
    assert "PermissionError" in runtime.observe_recovery()
    assert runtime.observe_recovery() == ["HistoricalChecksUnconfirmed"]
    assert w.seen == ["00001", "00002"]
    runtime.observe_recovery()
    w.broken.clear()
    # One clean sweep is required, not the first unrelated successful item.
    for _ in range(3):
        assert runtime.observe_recovery() == ["HistoricalChecksUnconfirmed"]
    assert runtime.observe_recovery() == []
    assert not health.observation()["history"]["unconfirmed_failure"]


def test_slow_item_finishes_without_cancellation_and_next_cycle_keeps_cursor(workload, monkeypatch):
    w = workload
    original = w.adapter.inspect

    def slow(reference):
        w.clock[0] += 20
        return original(reference)

    w.adapter.inspect = slow
    assert runtime.observe_recovery() == []
    assert w.seen == ["00001"] and w.clock[0] == 21
    assert runtime.observe_recovery() == []
    assert w.seen == ["00001", "00002"]


def test_waiting_sweep_cannot_clear_prior_failure(workload):
    w = workload
    w.references[:] = ["00001"]
    w.broken.add("00001")
    assert runtime.observe_recovery()

    def waiting(_):
        from services.stats_import_outcome_dal import ImportExecutionActive

        raise ImportExecutionActive("existing work")

    original = w.adapter.inspect
    w.adapter.inspect = waiting
    for _ in range(3):
        assert runtime.observe_recovery() == ["HistoricalChecksUnconfirmed"]
    w.adapter.inspect = original
    w.broken.clear()
    assert runtime.observe_recovery() == ["HistoricalChecksUnconfirmed"]
    assert runtime.observe_recovery() == []


def test_verified_empty_catalog_recovers_from_initial_inventory_failure(workload):
    w = workload
    original = w.adapter.discovery_page
    w.adapter.discovery_page = Mock(side_effect=TimeoutError())
    assert runtime.observe_recovery()
    w.references.clear()
    w.adapter.discovery_page = original
    assert runtime.observe_recovery() == []
    assert not health.observation()["history"]["unconfirmed_failure"]


def test_active_history_overlap_advances_cursor_without_reinspection(workload):
    w = workload
    w.row.update(SourceKind="private_evidence", SourceID="00001")
    w.service.adapters.pop("stats_import")
    assert runtime.observe_recovery() == []
    assert "00001" not in w.seen
    assert w.seen == w.references[1:11]


@pytest.mark.asyncio
async def test_dashboard_and_operator_share_one_retained_sql_worker(monkeypatch):
    from services import operator_status_service as service
    from services.gsheets_health_service import HealthProbe

    # Load just the thin dashboard adapter; importing the bot starts lifecycles.
    source = ast.parse(
        (Path(__file__).parents[1] / "bot_instance.py").read_text(encoding="utf-8-sig")
    )
    node = next(n for n in source.body if getattr(n, "name", None) == "_check_sql_health")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "dashboard-adapter", "exec"), namespace)
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def worker(_):
        calls.append(1)
        entered.set()
        await release.wait()
        return True, "SQL connected"

    monkeypatch.setattr(service, "_probe", HealthProbe(label="SQL"))
    monkeypatch.setattr(service, "drain_thread", worker)
    first = asyncio.create_task(namespace["_check_sql_health"](0.001))
    await entered.wait()
    second = await service.check_sql(timeout=0.001)
    assert (await first)[0] is None and second[0] is None and calls == [1]
    release.set()
    await service.shutdown()


def test_active_summary_uses_scoped_counts_without_historical_json(monkeypatch):
    from services import recovery_backlog_dal as module

    cursor = SimpleNamespace(execute=Mock())

    @contextmanager
    def transaction(_):
        yield cursor

    monkeypatch.setattr(module, "transaction", transaction)
    monkeypatch.setattr(
        module,
        "rows",
        lambda _: [
            dict(SourceKind="private_evidence", Total=2),
            dict(SourceKind="stats_import", Total=1),
        ],
    )
    monkeypatch.setattr(module, "one", lambda _: dict(Total=4))
    result = module.RecoveryBacklogDAL(
        SimpleNamespace(connect=None, scope="scope")
    ).active_summary()
    assert (result["open_count"], result["copies"], result["pending"]) == (3, 2, 4)
    calls = cursor.execute.call_args_list
    assert all(call.args[1:] == ("scope",) for call in calls)
    assert "State='open'" in calls[0].args[0]
    assert "'dispatched','unknown'" in calls[1].args[0]
    assert all("JSON_VALUE" not in call.args[0] for call in calls)


@pytest.mark.asyncio
async def test_dashboard_pending_probe_preserves_alert_for_actual_failure():
    import discord

    source = ast.parse(
        (Path(__file__).parents[1] / "bot_instance.py").read_text(encoding="utf-8-sig")
    )
    node = next(n for n in source.body if getattr(n, "name", None) == "_update_health_embed")
    message = SimpleNamespace(edit=AsyncMock())
    owner = SimpleNamespace(send=AsyncMock())

    class Channel:
        fetch_message = AsyncMock(return_value=message)

    channel = Channel()
    now = datetime(2026, 10, 26, tzinfo=UTC)
    namespace = dict(
        bot=SimpleNamespace(
            get_channel=Mock(return_value=channel),
            fetch_user=AsyncMock(return_value=owner),
            latency=None,
        ),
        discord=SimpleNamespace(
            TextChannel=Channel, Thread=Channel, VoiceChannel=Channel, Embed=discord.Embed
        ),
        STATUS_CHANNEL_ID=1,
        ADMIN_USER_ID=2,
        ERROR_SPIKE_THRESHOLD=10,
        STALENESS_THRESHOLD_MIN=10,
        LAST_DISCONNECT_UTC=None,
        LAST_RESUME_UTC=None,
        _ensure_pinned_health_message=AsyncMock(return_value=3),
        _uptime_hms=lambda: (0, 0, 0, 0),
        _check_sql_health=AsyncMock(
            side_effect=[(None, "Pending"), (True, "OK"), (False, "Unavailable")]
        ),
        _check_gsheets_health=AsyncMock(return_value=(True, "OK")),
        _count_errors_last_minutes=AsyncMock(return_value=0),
        _get_queue_depth_safe=lambda: 0,
        get_cache_stats=lambda: {},
        _summarize_tasks=lambda: "idle",
        HealthView=lambda: None,
        _aware=lambda value: value,
        utcnow=lambda: now,
        _last_health_embed_update_ts=None,
        _last_health_alert_ts=None,
        is_pytest_logging_mode=lambda: False,
        logger=Mock(),
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), "dashboard-alert", "exec"), namespace)
    update = namespace["_update_health_embed"]
    await update()
    assert "Pending" in message.edit.call_args.kwargs["embed"].description
    owner.send.assert_not_awaited()
    assert namespace["_last_health_alert_ts"] is None
    await update()
    owner.send.assert_not_awaited()
    assert namespace["_last_health_alert_ts"] is None
    await update()
    owner.send.assert_awaited_once()
    assert "DB check failed: Unavailable" in owner.send.call_args.args[0]
    assert namespace["_last_health_alert_ts"] == now
