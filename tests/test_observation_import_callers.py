"""Observer deferral at actual import and committed-capture entry boundaries."""

from contextlib import contextmanager
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core import sql_connection_custody as custody
from services import legacy_export_snapshot_service as snapshots
from services.all_kvk_capture_recovery_service import AllKvkCaptureRecovery
from services.catalogue_observation_dal import ObservationDeferred
from services.import_capture_recovery_service import ImportCaptureRecovery
from services.player_report_recovery_service import PlayerReportCaptureRecovery
import stats_module
from tests.test_legacy_export_snapshot import producer_runtime


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", [None, "guard_close", "connection_close", "withdrawal"])
async def test_actual_stats_import_deferral_never_dispatches_and_requires_cleanup(
    tmp_path, monkeypatch, fault
):
    from services import stats_import_outcome_service as outcomes

    scope = dict(consumer="scan_data", destinations=["file-a"])
    runtime, dal = producer_runtime(tmp_path, configuration={"scan_data": scope})
    connection = Mock(autocommit=True, timeout=15)
    connection.cursor.return_value.connection = connection
    dal.connect.return_value = connection
    original = ObservationDeferred("generation_changed")
    owners = []

    def refuse(*args, **kwargs):
        owners.append(snapshots.current_owner())
        raise original

    dal.verify_producer_cursor.side_effect = refuse

    @contextmanager
    def session(*args, **kwargs):
        yield None
        if fault == "guard_close":
            raise OSError("guard release acknowledgment lost")

    dal.session.side_effect = session
    if fault == "connection_close":
        connection.close.side_effect = OSError("connection close acknowledgment lost")
    if fault == "withdrawal":
        transition = dal.transition.side_effect

        def withdraw(claim, **kwargs):
            if kwargs.get("state") == "unavailable":
                raise OSError("withdrawal acknowledgment lost")
            return transition(claim, **kwargs)

        dal.transition.side_effect = withdraw

    async def direct_offload(fn, *args, **kwargs):
        return fn(*args)

    monkeypatch.setattr(stats_module, "_offload_callable_py", direct_offload)
    registration = Mock(side_effect=AssertionError("Must not register an execution"))
    business = Mock(side_effect=AssertionError("Must not dispatch UPDATE_ALL2"))
    capture = runtime.capture
    monkeypatch.setattr(outcomes, "register_execution", registration)
    monkeypatch.setattr(stats_module, "execute_update_all2_with_log_management", business)
    reconcile = Mock(return_value=None)
    monkeypatch.setattr(stats_module, "_fetch_immutable_import_outcome", reconcile)
    monkeypatch.setattr(stats_module, "emit_telemetry_event", Mock())
    with snapshots.use_runtime(runtime):
        success, message, _ = await stats_module.run_sql_procedure(
            completed_filename="stats_0123456789abcdef0123456789abcdef.ready.csv"
        )
    assert not success
    assert message
    if fault is None:
        assert "SQL import did not start" in message
        assert "completion is not verified" not in message
        reconcile.assert_not_called()
    else:
        assert "completion is not verified" in message
    assert len(owners) == 1
    owner = owners[0]
    assert owner.stats_import_context and owner.closed
    assert not owner.stats_execution_registered and not owner.stats_execution_dispatched
    unavailable = [
        c for c in dal.transition.call_args_list if c.kwargs.get("state") == "unavailable"
    ]
    if fault in {"guard_close", "connection_close"}:
        assert unavailable == []
        assert custody.connection_retained(connection)
        with pytest.raises(custody.SqlCleanupUnknown):
            custody.require_sql_admission()
    else:
        assert len(unavailable) == 1
        assert unavailable[0].kwargs["release"] is True
        assert not custody.connection_retained(connection)
    if fault == "guard_close":
        connection.close.assert_not_called()
    else:
        connection.close.assert_called_once()
    dal.request.assert_called_once()
    dal.verify_producer_cursor.assert_called_once()
    registration.assert_not_called()
    business.assert_not_called()
    capture.assert_not_called()
    dal.captured.assert_not_called()
    dal.uncertain.assert_not_called()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    assert connection.timeout == 15


@pytest.mark.parametrize(
    "recovery_type", [ImportCaptureRecovery, AllKvkCaptureRecovery, PlayerReportCaptureRecovery]
)
@pytest.mark.parametrize(
    "fault", [None, "capture_cursor_close", "guard_release", "connection_close"]
)
def test_actual_recovery_deferral_preserves_commit_and_physical_custody(
    monkeypatch, recovery_type, fault
):
    from services import import_capture_recovery_dal as capture_dal

    prep_id = str(uuid4())
    generation = dict(completion="committed", capture="pending", commit_identity=prep_id)
    saved = deepcopy(generation)
    preparation = dict(
        PreparationID=prep_id,
        State="committed",
        Resolution=None,
        GenerationJson=json.dumps(generation),
    )
    runtime = SimpleNamespace(
        configuration=json.dumps({recovery_type.consumer: dict(consumer=recovery_type.consumer)}),
        dal=Mock(),
        capture=Mock(),
        enqueue_snapshot=Mock(),
        store=Mock(),
    )
    outcomes = Mock()
    outcomes.inspect.return_value = dict(preparation=preparation, captured=False)
    connection = outcomes.connect.return_value
    guard_cursor, reader_cursor = Mock(), Mock()
    guard_cursor.connection = reader_cursor.connection = connection
    connection.cursor.side_effect = [guard_cursor, reader_cursor]
    service = recovery_type(runtime, outcomes)
    claim = SimpleNamespace(preparation_id=prep_id)
    adoption = Mock(return_value=(claim, generation))
    monkeypatch.setattr(service.dal, "adopt", adoption)
    original = ObservationDeferred("catalogue_busy")
    runtime.dal.verify_producer_cursor.side_effect = original
    if fault == "capture_cursor_close":
        reader_cursor.close.side_effect = OSError("capture cursor close lost")
    if fault == "connection_close":
        connection.close.side_effect = OSError("connection close lost")

    def row(cursor):
        sql = cursor.execute.call_args.args[0]
        if "sp_getapplock" in sql:
            return dict(LockResult=0)
        assert "sp_releaseapplock" in sql
        if fault == "guard_release":
            raise OSError("guard release lost")
        return dict(Mode="NoLock")

    monkeypatch.setattr(capture_dal, "one", row)
    with pytest.raises(custody.SqlCleanupUnknown if fault else ObservationDeferred) as caught:
        service.run(prep_id, "same-token", "same-actor")
    chain = []
    error = caught.value
    while error is not None:
        chain.append(error)
        error = error.__cause__
    assert original in chain
    assert generation == saved
    assert preparation["State"] == "committed"
    adoption.assert_called_once_with(
        connection, prep_id, "same-token", "same-actor", service.generation
    )
    runtime.dal.verify_producer_cursor.assert_called_once_with(claim, reader_cursor)
    runtime.dal.transition.assert_not_called()
    runtime.dal.captured.assert_not_called()
    runtime.capture.assert_not_called()
    runtime.enqueue_snapshot.assert_not_called()
    outcomes.connect.assert_called_once()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    reader_cursor.close.assert_called_once()
    if fault:
        assert custody.connection_retained(connection)
        with pytest.raises(custody.SqlCleanupUnknown):
            custody.require_sql_admission()
    else:
        assert not custody.connection_retained(connection)
        guard_cursor.close.assert_called_once()
    if fault in {"capture_cursor_close", "guard_release"}:
        connection.close.assert_not_called()
    else:
        connection.close.assert_called_once()
    release_calls = [
        c for c in guard_cursor.execute.call_args_list if "sp_releaseapplock" in c.args[0]
    ]
    if fault == "capture_cursor_close":
        assert release_calls == []
    elif fault == "guard_release":
        assert len(release_calls) == 1
    else:
        assert len(release_calls) == (2 if recovery_type is ImportCaptureRecovery else 1)


@pytest.mark.parametrize("consumer", ["scan_data", "all_kvk"])
@pytest.mark.parametrize("fault", [None, "fetch", "close", "fetch_and_close"])
def test_actual_capture_owner_retains_unknown_cursor_and_original_failure(
    tmp_path, monkeypatch, consumer, fault
):
    from constants import CONFIG_FILE
    import gsheet_module as sheets
    from services.legacy_export_snapshot_dal import LegacySnapshotDAL

    scope = dict(consumer=consumer, destinations=["file-a"])
    if consumer == "all_kvk":
        scope["kvk_no"] = 7
    else:
        with open(CONFIG_FILE, encoding="utf-8") as stream:
            scope["exports"] = json.load(stream)[:1]
    runtime, dal = producer_runtime(
        tmp_path, configuration={consumer: scope}, capture=LegacySnapshotDAL.capture_outputs
    )
    connection = Mock(autocommit=True, timeout=15)
    dal.connect.return_value = connection
    cursor = connection.cursor.return_value
    cursor.connection = connection
    cursor.description = [("id",)]
    original = OSError("capture fetch failed")
    if fault in {"fetch", "fetch_and_close"}:
        cursor.fetchall.side_effect = original
    else:
        cursor.fetchall.return_value = [(1,)]
    if fault in {"close", "fetch_and_close"}:
        cursor.close.side_effect = OSError("capture close acknowledgment lost")
    count = len(sheets.KVK_EXPORT_SECTION_NAMES) if consumer == "all_kvk" else 1
    cursor.nextset.side_effect = [True] * (count - 1) + [False]
    planned = Mock(return_value=((snapshots.OutputSection("data", ("id",), ((1,),)),), scope))
    monkeypatch.setattr(sheets, "plan_legacy_outputs", planned)
    owner = runtime.begin_writer(consumer)
    runtime.checkpoint_writer(owner, {"procedure": "capture fixture"})
    completed = deepcopy(owner.completion)
    dal.transition.reset_mock()
    if fault:
        expected = custody.SqlCleanupUnknown if fault in {"close", "fetch_and_close"} else OSError
        with pytest.raises(expected) as caught:
            runtime.finish_writer(owner)
        if fault in {"fetch", "fetch_and_close"}:
            assert original is caught.value or original is caught.value.__cause__
        assert owner.completion == completed
        dal.transition.assert_not_called()
        dal.captured.assert_not_called()
    else:
        runtime.finish_writer(owner)
        dal.captured.assert_called_once()
        assert dal.transition.call_args.kwargs["generation"]["capture"] == "complete"
    assert owner.closed
    cursor.close.assert_called_once()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    if fault in {"close", "fetch_and_close"}:
        assert custody.connection_retained(connection)
        connection.close.assert_not_called()
        with pytest.raises(custody.SqlCleanupUnknown):
            custody.require_sql_admission()
    else:
        assert not custody.connection_retained(connection)
        connection.close.assert_called_once()
