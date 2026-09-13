"""Recovery caller, typed reload and lifecycle tests using synthetic state only."""

import asyncio
from contextlib import nullcontext
from dataclasses import asdict
from threading import Event, get_ident
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import bot_config
from kvk.dal.new_source_import_dal import SourceConflict, canonical
from kvk.dal.new_source_recovery_dal import _metadata, _row, endpoint_chain
from kvk.services import new_source_recovery_service as recovery
from tests.kvk_source_fixtures import worked_calculation_inputs


def test_sealed_update_loads_each_endpoint_once(monkeypatch):
    from kvk.dal import new_source_recovery_dal as dal

    cursor = Mock()
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    monkeypatch.setattr(dal, "locked_period", lambda *_: (None, None, []))
    monkeypatch.setattr(dal, "current_config", lambda *_: "c")
    monkeypatch.setattr(dal, "one", Mock(side_effect=[{"SeasonVersion": 2}, None]))
    loader = dal.RecoveryDAL(Mock())
    loader._config = Mock(
        return_value=SimpleNamespace(
            version_id="c",
            b0_revision_id="b0",
            is_no_fight=True,
        )
    )
    events = {
        key: SimpleNamespace(logical_scan_id=index)
        for index, key in enumerate(("b0", "start", "end"))
    }
    loader._observation = Mock(side_effect=lambda _, revision: events[revision])
    result = loader.load_inputs(
        16,
        "p",
        update=dict(
            ConfigVersionID="c",
            KVK_NO=16,
            PeriodID="p",
            ConfirmationJson="{}",
            StartRevisionID="start",
            EndRevisionID="end",
        ),
    )
    assert loader._observation.call_args_list == [
        call(cursor, "b0"),
        call(cursor, "start"),
        call(cursor, "end"),
    ]
    assert result["observations"] == (events["start"], events["end"])
    assert result["b0"] is events["b0"]
    assert result["previous"] is None


def test_typed_rows_roundtrip_preserves_decimals_and_missingness():
    b0, start, _, _ = worked_calculation_inputs()
    for event in (b0, start):
        for row in event.observation.rows:
            assert _row(canonical(asdict(row))) == row
        meta = _metadata(canonical(asdict(event.observation.metadata)))
        assert meta.candidate == event.observation.metadata.candidate
        assert meta.scope == event.observation.metadata.scope


@pytest.mark.parametrize("text_storage", [False, True])
def test_parser_metric_roundtrip_independent_of_excel_storage(text_storage):
    from kvk.services.new_source_parser import parse_aggregate_workbook, parse_player_workbook
    from tests.kvk_source_fixtures import (
        MAPPING,
        aggregate_bytes,
        metadata,
        player_bytes,
        player_row,
    )

    values = player_row(Name="123", Alliance="456", Civilization="789")
    if text_storage:
        values = {key: str(value) for key, value in values.items()}
    player = parse_player_workbook(player_bytes([values]), metadata())
    aggregate = parse_aggregate_workbook(aggregate_bytes(), metadata(aggregate=True), MAPPING)
    for row in (*player.rows, *aggregate.kingdom_rows, *aggregate.camp_rows):
        assert _row(canonical(asdict(row))) == row


def request(base, desired, old, new, *, period="p"):
    return dict(
        RequestID=desired,
        SourceKey="snapshot_report_v1",
        KVK_NO=1,
        PeriodID=period,
        BaseConfigVersionID=base,
        DesiredConfigVersionID=desired,
        OldStartScanID=10,
        NewStartScanID=10,
        OldEndScanID=old,
        NewEndScanID=new,
        RequestState="pending",
        Actor="system:synthetic",
        Reason="Authorized endpoints",
    )


def test_endpoint_roundtrip_chain_is_distinct_and_ordered():
    a, b = request("c1", "c2", 13, 14), request("c2", "c3", 14, 13)
    assert endpoint_chain([b, a], "c1", "c3") == (a, b)


@pytest.mark.parametrize("mutation", ["missing", "period", "bounds", "rejected", "cycle"])
def test_endpoint_chain_rejects_broken_authority(mutation):
    a, b = request("c1", "c2", 13, 14), request("c2", "c3", 14, 13)
    chain = [b, a]
    if mutation == "missing":
        chain.pop()
    if mutation == "period":
        a["PeriodID"] = "other"
    if mutation == "bounds":
        a["NewEndScanID"] = 15
    if mutation == "rejected":
        a["RequestState"] = "rejected"
    if mutation == "cycle":
        a["BaseConfigVersionID"] = "c3"
    with pytest.raises(SourceConflict):
        endpoint_chain(chain, "c1", "c3")


def test_default_off_registration_has_no_factory_or_task(monkeypatch):
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", False)
    monitor, factory = Mock(), Mock()
    assert recovery.register_recovery(monitor, factory=factory) is None
    monitor.create.assert_not_called()
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_register_once_and_offloop_cancel_waits_for_inflight(monkeypatch):
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", True)
    monkeypatch.setattr(recovery, "_worker", None)
    monkeypatch.setattr(recovery, "_worker_loop", None)
    entered, released, finished = Event(), Event(), Event()
    main_thread = get_ident()
    calls = []

    def batch(stop, limit):
        calls.append(get_ident())
        entered.set()
        assert released.wait(3)
        assert stop.is_set()
        finished.set()

    def factory():
        assert get_ident() != main_thread
        return SimpleNamespace(run_batch=batch)

    monitor = Mock()
    monitor.is_running.return_value = False
    worker = recovery.register_recovery(monitor, factory=factory)
    task = asyncio.create_task(worker.run())
    assert await asyncio.to_thread(entered.wait, 3)
    monitor.is_running.return_value = True
    assert recovery.register_recovery(monitor, factory=factory) is worker
    assert monitor.create.call_count == 1
    task.cancel()
    await asyncio.sleep(0.01)
    assert not task.done()
    released.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set() and len(calls) == 1 and calls[0] != main_thread


@pytest.mark.asyncio
async def test_worker_startup_and_wake_reload_durable_state():
    calls = []
    ready = Event()

    def batch(stop, limit):
        calls.append(limit)
        ready.set()

    worker = recovery.RecoveryWorker(lambda: SimpleNamespace(run_batch=batch))
    task = asyncio.create_task(worker.run())
    assert await asyncio.to_thread(ready.wait, 3)
    ready.clear()
    worker.wake.set()
    assert await asyncio.to_thread(ready.wait, 3)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(calls) == 2


def test_acceptance_wake_only_after_confirm(monkeypatch):
    wake = Mock()
    monkeypatch.setattr(recovery, "wake_recovery", wake)
    service = Mock()
    adapter = recovery.RecoveryIntakeAdapter(service)
    assert adapter.confirm("actor", "receipt", 1) is service.confirm.return_value
    wake.assert_called_once()
    service.confirm.side_effect = PermissionError("revoked")
    with pytest.raises(PermissionError):
        adapter.confirm("actor", "receipt", 2)
    assert wake.call_count == 1


def test_recovery_discovers_explicit_updates_only(monkeypatch):
    from kvk.services import source_update_service

    paired = Mock()
    monkeypatch.setattr(source_update_service, "SourceUpdateService", lambda connect: paired)
    dal = Mock()
    dal.ready_updates.return_value = [{"UpdateID": "first"}, {"UpdateID": "second"}]
    worker = recovery.RecoveryService(dal, Mock())
    assert worker.recover_period(16, "period") is paired.publish.return_value
    assert [call.args[0] for call in paired.publish.call_args_list] == ["first", "second"]
    dal.load_inputs.assert_not_called()
    dal.ready_updates.return_value = []
    assert worker.recover_period(16, "period") is None


def test_recovery_does_not_deliver_after_pair_failure(monkeypatch):
    worker = recovery.RecoveryService(Mock(), Mock(), Mock(), (Mock(),))
    worker.dal.periods.return_value = [(16, "period")]
    worker.recover_period = Mock(side_effect=SourceConflict("stale pair"))
    deliver = Mock()
    monkeypatch.setattr(recovery, "deliver_current_exports", deliver)
    worker.run_batch(Event())
    deliver.assert_not_called()
    assert worker.after == (16, "period")


def test_closed_loop_wake_cannot_break_committed_confirm(monkeypatch):
    loop = Mock()
    loop.is_closed.return_value = False
    loop.call_soon_threadsafe.side_effect = RuntimeError("closed during shutdown")
    monkeypatch.setattr(recovery, "_worker_loop", loop)
    monkeypatch.setattr(recovery, "_worker", SimpleNamespace(wake=Mock()))
    recovery.wake_recovery()


def test_batch_advances_past_failed_period_and_stops_cooperatively():
    dal = Mock()
    dal.periods.return_value = ((1, "a"), (1, "b"))
    service = recovery.RecoveryService(dal, Mock())
    service.recover_period = Mock(side_effect=[SourceConflict("pending"), None])
    service.run_batch(Event(), 2)
    assert service.after == (1, "b") and service.recover_period.call_count == 2
    stop = Event()
    stop.set()
    service.run_batch(stop, 2)
    assert service.recover_period.call_count == 2


def test_automatic_discord_recovery_is_refused():
    target = recovery.ExportTarget(1, SimpleNamespace(kind="discord"), Mock())
    with pytest.raises(ValueError, match="S10"):
        recovery.deliver_current_exports(Mock(), Mock(), (target,), 1)


@pytest.mark.parametrize("kind", ["sheets", "file"])
def test_recovery_component_export_bypass_is_refused(kind):
    target = recovery.ExportTarget(16, SimpleNamespace(kind=kind), Mock())
    with pytest.raises(SourceConflict, match="S10"):
        recovery.deliver_current_exports(Mock(), Mock(), (target,), 16)
    target.transport.assert_not_called()


def export_record():
    return dict(
        kvk_no=1,
        index_file_id="synthetic_index",
        slot_file_ids=["synthetic_slot_a", "synthetic_slot_b"],
        owner_email="owner@example.invalid",
        service_account_email="bot@synthetic.iam.gserviceaccount.com",
    )


def test_registration_parser_default_and_explicit_schema():
    import json

    assert recovery.parse_export_registrations("[]") == ()
    result = recovery.parse_export_registrations(json.dumps([export_record()]))
    assert result[0][0] == 1 and result[0][1].audience == "private"


@pytest.mark.parametrize(
    "change",
    [
        dict(kvk_no=True),
        dict(slot_file_ids="abc"),
        dict(slot_file_ids=["one"]),
        dict(slot_file_ids=[str(i) for i in range(17)]),
        dict(owner_email=None),
        dict(audience="unknown"),
        dict(extra="unsupported"),
        dict(index_file_id="bad id"),
    ],
)
def test_registration_parser_rejects_malformed_records(change):
    import json

    with pytest.raises(ValueError):
        recovery.parse_export_registrations(json.dumps([dict(export_record(), **change)]))


def test_registration_parser_rejects_shared_and_protected_workbooks():
    import json

    row = export_record()
    with pytest.raises(ValueError):
        recovery.parse_export_registrations(json.dumps([row, row]))
    with pytest.raises(ValueError):
        recovery.parse_export_registrations(
            json.dumps([row]), protected_file_ids=[row["index_file_id"]]
        )


def test_invalid_registration_fails_before_sql_or_credentials(monkeypatch):
    from kvk.dal import new_source_recovery_dal

    monkeypatch.setattr(bot_config, "KVK_SOURCE_EXPORT_REGISTRATIONS", "not json")
    sql = Mock(side_effect=AssertionError("Must validate before SQL"))
    monkeypatch.setattr(new_source_recovery_dal.RecoveryDAL, "check_schema", sql)
    with pytest.raises(ValueError, match="JSON"):
        recovery.configured_recovery()
    sql.assert_not_called()
