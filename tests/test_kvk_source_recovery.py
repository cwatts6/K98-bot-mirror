"""Recovery caller, typed reload and lifecycle tests using synthetic state only."""

import asyncio
from dataclasses import asdict, replace
from threading import Event, get_ident
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import bot_config
from kvk.dal.new_source_import_dal import SourceConflict, canonical
from kvk.dal.new_source_recovery_dal import _metadata, _row, endpoint_chain
from kvk.services import new_source_recovery_service as recovery
from kvk.services.new_source_publication_service import PublicationService
from tests.kvk_source_fixtures import calculation_config, worked_calculation_inputs


def test_typed_rows_roundtrip_preserves_decimals_and_missingness():
    b0, start, _, _ = worked_calculation_inputs()
    for event in (b0, start):
        for row in event.observation.rows:
            assert _row(canonical(asdict(row))) == row
        meta = _metadata(canonical(asdict(event.observation.metadata)))
        assert meta.candidate == event.observation.metadata.candidate
        assert meta.scope == event.observation.metadata.scope


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


def test_recovery_builds_normal_interim_and_deduplicates_selected():
    b0, start, middle, _ = worked_calculation_inputs()
    config = calculation_config(end_scan_id=None)
    publisher = PublicationService(Mock())
    publisher.dal = Mock()
    publisher.dal.build_candidate.return_value = {"Generation": 1}
    publisher.dal.select_publication.return_value = {"NewSelectionVersion": 1}
    dal = Mock()
    # Use canonical UUIDs for actual ExportSelection construction.
    config = replace(config, period_id="00000000-0000-0000-0000-000000000001")
    data = dict(
        config=config,
        observations=(start, middle),
        b0=b0,
        previous=None,
        aggregate=None,
        request=None,
        requests=[],
        selected=None,
        routing=None,
    )
    dal.load_inputs.return_value = data
    service = recovery.RecoveryService(dal, publisher)
    result = service.recover_period(config.kvk_no, config.period_id)
    snapshot = publisher.dal.build_candidate.call_args.args[0]
    assert snapshot.calculation.selection.end.logical_scan_id == 11
    assert snapshot.player_state.value == "live"
    data["selected"] = dict(PublicationID=result.publication_id, SelectionVersion=1)
    assert service.recover_period(config.kvk_no, config.period_id) is None
    assert publisher.dal.select_publication.call_count == 1


def test_interim_final_pending_and_authorized_replacement_sequence():
    from datetime import timedelta

    b0, start, eleven, thirteen = worked_calculation_inputs()

    def event(source, number, delta):
        metadata = source.observation.metadata
        return replace(
            source,
            logical_scan_id=number,
            observation_id=f"observation-{number}",
            revision_id=f"revision-{number}",
            observation=replace(
                source.observation,
                metadata=replace(
                    metadata,
                    candidate=replace(
                        metadata.candidate, scan_start_utc=metadata.candidate.scan_start_utc + delta
                    ),
                ),
            ),
        )

    twelve = event(eleven, 12, timedelta(hours=12))
    fourteen = event(thirteen, 14, timedelta(days=1))
    config = replace(calculation_config(), period_id="00000000-0000-0000-0000-000000000001")
    data = dict(
        config=config,
        observations=(start, eleven),
        b0=b0,
        previous=None,
        aggregate=None,
        request=None,
        requests=[],
        selected=None,
        routing=None,
    )
    publisher = PublicationService(Mock())
    publisher.dal = Mock()
    publisher.dal.build_candidate.return_value = {"Generation": 1}
    stored = []

    def select(**kwargs):
        version = len(stored) + 1
        snapshot = publisher.dal.build_candidate.call_args.args[0]
        stored.append(snapshot)
        data["selected"] = dict(PublicationID=snapshot.publication_id, SelectionVersion=version)
        data["previous"] = snapshot.calculation.selection
        return {"NewSelectionVersion": version}

    publisher.dal.select_publication.side_effect = select
    dal = Mock()
    dal.load_inputs.return_value = data
    service = recovery.RecoveryService(dal, publisher)

    def run():
        return service.recover_period(config.kvk_no, config.period_id)

    run()
    data["observations"] = (start, eleven, twelve)
    run()
    data["observations"] = (start, eleven, twelve, thirteen)
    run()
    assert [
        (s.calculation.selection.end.logical_scan_id, s.player_state.value) for s in stored
    ] == [(11, "live"), (12, "live"), (13, "final")]
    req = request(config.version_id, "desired-14", 13, 14, period=config.period_id)
    req["KVK_NO"] = config.kvk_no
    data.update(
        config=replace(config, version_id="desired-14", end_scan_id=14), request=req, requests=[req]
    )
    run()
    assert stored[-1].calculation.selection.endpoint_pending
    assert stored[-1].player_state.value == "live"
    assert stored[-1].calculation.selection.end.logical_scan_id == 13
    data["observations"] = (*data["observations"], fourteen)
    run()
    assert stored[-1].player_state.value == "corrected_final"
    assert stored[-1].calculation.selection.end.logical_scan_id == 14
    assert run() is None and len(stored) == 5
    assert all(len(s.calculation.players) == 4 for s in stored)
    assert all(s.aggregate is None for s in stored)


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
    with pytest.raises(ValueError, match="Discord"):
        recovery.deliver_current_exports(Mock(), Mock(), (target,), 1)


@pytest.mark.parametrize("changed_period", [0, 1])
def test_recovery_caller_composes_s4b_multi_period_delivery(monkeypatch, changed_period):
    """Reuse S4B-MP01's full synthetic SQL/Google assertions through the S5B caller."""
    import json

    import kvk.services.new_source_export_service as exports
    import tests.test_kvk_source_delivery as component

    direct = component.deliver_export

    def through_recovery(**args):
        # Keep the component's explicit stale-anchor rejection as a direct negative check.
        if args["selection"] not in args["generation"].selections:
            return direct(**args)
        repository = args["repository"]
        stored = repository.claims.get(args["destination"])
        if (
            stored
            and stored.state == "confirmed"
            and stored.selection == args["selection"]
            and json.loads(stored.receipt)["export_key"] != args["generation"].key
        ):
            return direct(**args)
        dal = SimpleNamespace(
            connect=Mock(), selections=lambda season: args["generation"].selections
        )

        # Fresh repository instances in MP01 load durable rows using its actual claim DAL.
        def read(selection, destination):
            if stored and stored.selection == selection:
                return stored
            # Let the real claim path perform final receipt reconciliation/deduplication.
            return None

        repository.read_receipt = read
        monkeypatch.setattr(exports, "load_sheets_generation", lambda **kw: args["generation"])
        target = recovery.ExportTarget(
            args["selection"].kvk_no, args["destination"], args["transport"]
        )
        return recovery.deliver_current_exports(
            dal, repository, (target,), target.kvk_no, changed=args["selection"]
        )[0]

    monkeypatch.setattr(component, "deliver_export", through_recovery)
    component.test_multi_period_delivery_uses_changed_anchor_and_deduplicates(
        monkeypatch, changed_period
    )


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
