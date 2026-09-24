from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from services.export_snapshot_store import ExportSnapshotStore
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    OutputSection,
    SnapshotUnavailable,
    configuration_digest,
    output_digest,
)


def test_evidence_preparation_requires_protected_legacy_sql_contract_before_connecting():
    from unittest.mock import Mock

    from kvk.dal.new_source_import_dal import SourceConflict

    connect = Mock()
    with pytest.raises(SourceConflict, match="protected legacy SQL"):
        LegacySnapshotDAL(connect, output_operations=True, execution_evidence=True)
    connect.assert_not_called()


@pytest.mark.parametrize("drift", [False, True])
def test_evidence_session_checks_same_connection_before_producer_and_preserves_transaction(
    monkeypatch, drift
):
    from unittest.mock import Mock

    from kvk.dal.new_source_import_dal import SourceConflict
    import services.export_execution_dal as evidence
    from tests.test_export_runtime_composition import legacy_permission_fixture

    observed, approved = legacy_permission_fixture(monkeypatch)
    dal = LegacySnapshotDAL(
        Mock(), output_operations=True, execution_evidence=True, legacy_sql_contract=approved
    )
    # The caller cannot change the retained contract by mutating its input object.
    approved["principal"] = "changed-after-composition"
    assert dal.legacy_sql_contract["principal"] == "fixture-bot"
    dal.authorize = Mock()
    cursor = Mock()
    connection = Mock(autocommit=True)
    connection.cursor.return_value = cursor
    collected = Mock(return_value=observed)
    monkeypatch.setattr(evidence, "legacy_installation_snapshot", collected)
    entered = []
    if drift:
        observed["target"][0]["AuthorityRole"] = 1
        with pytest.raises(SourceConflict):
            with dal.session("claim", connection):
                entered.append(True)
        assert entered == []
        cursor.execute.assert_not_called()
    else:
        with dal.session("claim", connection):
            entered.append(True)
        assert entered == [True]
        assert "sp_getapplock" in cursor.execute.call_args_list[0].args[0]
        assert "sp_releaseapplock" in cursor.execute.call_args_list[-1].args[0]
    collected.assert_called_once_with(cursor, dal.legacy_sql_contract["source"])
    cursor.close.assert_called_once()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    connection.close.assert_not_called()
    assert connection.autocommit is True


def producer_runtime(tmp_path, *, capture=None):
    from contextlib import nullcontext
    from dataclasses import replace
    from unittest.mock import Mock

    from services.legacy_export_snapshot_dal import PreparationClaim
    from services.legacy_export_snapshot_service import LegacyExportRuntime

    tmp_path.mkdir(exist_ok=True)
    dal = Mock()
    claim = PreparationClaim(
        str(uuid4()), "acct", "owner", 1, 1, (("sql_snapshot:legacy_outputs", 1),)
    )
    dal.request.return_value = claim.preparation_id
    dal.claim.return_value = claim
    dal.transition.side_effect = lambda c, **kw: replace(c, version=c.version + 1)
    dal.session.return_value = nullcontext()
    scope = dict(consumer="all_kvk", kvk_no=7, destinations=["file-a"])
    outputs = ((OutputSection("data", ("id",), ((1,),)),), scope)
    runtime = LegacyExportRuntime(
        dal=dal,
        coordinator=Mock(preparations=True),
        account="acct",
        store=ExportSnapshotStore(tmp_path, "storage"),
        configuration={"all_kvk": scope},
        capture=capture or Mock(return_value=outputs),
    )
    return runtime, dal


def test_later_failed_producer_invalidates_earlier_pipeline_capture(tmp_path):
    from services.legacy_export_snapshot_service import _captures, admitted_writer, use_runtime

    runtime, dal = producer_runtime(tmp_path)

    @admitted_writer("all_kvk")
    def later_writer():
        raise OSError("later output unknown")

    token = _captures.set([("all_kvk", 7, "capture-A")])
    try:
        with use_runtime(runtime):
            with pytest.raises(OSError):
                later_writer()
            with pytest.raises(SnapshotUnavailable, match="no verified committed capture"):
                runtime.submit(consumer="all_kvk", kvk_no=7)
        dal.latest_ready.assert_not_called()
        dal.read.assert_not_called()
    finally:
        _captures.reset(token)


@pytest.mark.parametrize("consumer,season", [("all_kvk", 7), ("scan_data", None)])
@pytest.mark.parametrize("state", ["captured", "materialized"])
def test_submission_returns_only_job_id_from_dal_job_row(tmp_path, consumer, season, state):
    import json

    runtime, dal = producer_runtime(tmp_path)
    registration = dict(consumer=consumer, kvk_no=season, destinations=["file-a"])
    runtime.configuration = json.dumps({consumer: registration})
    preparation_id, job_id = str(uuid4()), uuid4()
    sections = (OutputSection("data", ("id",), ((1,),)),)
    output = LegacySnapshot.capture(
        consumer=consumer,
        preparation_id=preparation_id,
        config=registration,
        generation=dict(
            completion="committed",
            commit_identity="committed-A",
            registration_sha256=configuration_digest(registration),
            output_sha256=output_digest(sections),
            config_sha256=configuration_digest(registration),
        ),
        provenance={},
        sections=sections,
    )
    receipt = output.persist(runtime.store)
    dal.read.return_value = dict(
        AccountKey="acct",
        StorageOwner=runtime.store.storage_owner,
        State=state,
        PreparationID=preparation_id,
        ConsumerKind=consumer,
        KVK_NO=season,
        SpoolKey=receipt.key,
        SpoolBytes=receipt.byte_count,
        SpoolHash=bytes.fromhex(receipt.sha256),
        Actor="operator",
        Reason="test",
    )
    runtime.coordinator.enqueue.return_value = {"JobID": job_id, "ProvenanceJson": "internal-row"}
    result = runtime.submit(consumer=consumer, kvk_no=season, preparation_id=preparation_id)
    assert result == str(job_id)
    assert isinstance(result, str) and "internal-row" not in result
    runtime.coordinator.enqueue.assert_called_once()
    assert runtime.coordinator.enqueue.call_args.kwargs["preparation_id"] == preparation_id


@pytest.mark.parametrize(
    "changed",
    [
        "OwnerID",
        "Fence",
        "Version",
        "ActivePreparationID",
        "ActiveOutputOperationID",
        "BlockedReason",
    ],
)
def test_preparation_authorization_requires_every_resource_cas_field(monkeypatch, changed):
    from unittest.mock import Mock

    from kvk.dal.new_source_import_dal import SourceConflict
    from services import legacy_export_snapshot_dal as module
    from services.legacy_export_snapshot_dal import PreparationClaim

    claim = PreparationClaim(str(uuid4()), "acct", str(uuid4()), 3, 5, (("account:acct", 8),))
    row = dict(
        ActivePreparationID=claim.preparation_id,
        ActiveJobID=None,
        OwnerID=claim.owner,
        Fence=3,
        Version=8,
        BlockedReason=None,
    )
    row[changed] = "changed" if changed not in {"Version", "Fence"} else 99
    monkeypatch.setattr(module, "_mutex", lambda *args: None)
    monkeypatch.setattr(module, "one", lambda cursor: row)
    with pytest.raises(SourceConflict, match="ownership"):
        LegacySnapshotDAL(Mock())._authorize(Mock(), claim)


def test_unstarted_withdrawal_has_version_and_no_active_resource_guard(monkeypatch):
    from contextlib import contextmanager
    from unittest.mock import Mock

    from services import legacy_export_snapshot_dal as module

    cursor = Mock()

    @contextmanager
    def txn(_):
        yield cursor

    monkeypatch.setattr(module, "transaction", txn)
    monkeypatch.setattr(module, "_mutex", lambda *args: None)
    cas = Mock(return_value={"Version": 4})
    monkeypatch.setattr(module, "_cas", cas)
    dal = LegacySnapshotDAL(Mock())
    dal.read = Mock(return_value={"AccountKey": "acct", "Version": 3})
    dal.withdraw_unstarted("preparation")
    statement = cas.call_args.args[1]
    assert "Version=?" in statement and "NOT EXISTS" in statement
    assert "State IN ('pending','sql_pending')" in statement
    assert "ActivePreparationID=p.PreparationID" in statement
    assert "OwnerID=NULL" not in statement and "DELETE" not in statement


def test_nested_writer_reuses_owner_and_captures_only_after_root_returns(tmp_path):
    from services.legacy_export_snapshot_service import (
        admitted_writer,
        current_owner,
        record_writer_completion,
        use_runtime,
    )

    runtime, dal = producer_runtime(tmp_path)

    @admitted_writer("all_kvk")
    def nested():
        record_writer_completion(procedure="recompute", kvk_no=7)
        return {"success": True}

    @admitted_writer("all_kvk")
    def outer():
        owner = current_owner()
        result = nested(owner_token=owner)
        assert current_owner() is owner and not owner.closed
        assert "export_preparation_id" not in result
        runtime.capture.assert_not_called()
        return result

    with use_runtime(runtime):
        result = outer()
    assert result["export_preparation_id"] == dal.request.return_value
    assert dal.request.call_count == 1
    runtime.capture.assert_called_once()
    dal.captured.assert_called_once()


def test_explicit_owner_is_inherited_by_nested_helpers(tmp_path):
    from services.legacy_export_snapshot_service import (
        admitted_writer,
        current_owner,
        use_runtime,
    )

    runtime, dal = producer_runtime(tmp_path)

    @admitted_writer("all_kvk")
    def nested():
        return current_owner()

    @admitted_writer("all_kvk")
    def outer():
        return nested()

    with use_runtime(runtime):
        owner = runtime.begin_writer("all_kvk")
        assert current_owner() is None
        assert outer(owner_token=owner) is owner
        assert current_owner() is None
        assert not owner.closed
    dal.request.assert_called_once()
    runtime.capture.assert_not_called()
    dal.uncertain.assert_not_called()


@pytest.mark.parametrize("replacement", ["another", "none"])
def test_nested_runtime_cannot_replace_or_disable_an_inherited_scope(tmp_path, replacement):
    from services.legacy_export_snapshot_service import require_runtime, use_runtime

    runtime, dal = producer_runtime(tmp_path / "first")
    other, other_dal = producer_runtime(tmp_path / "second")
    with use_runtime(runtime):
        with use_runtime(runtime):
            assert require_runtime() is runtime
        with pytest.raises(SnapshotUnavailable, match="cannot switch runtime"):
            with use_runtime(other if replacement == "another" else None):
                pytest.fail("An inherited scope must remain pinned")
        assert require_runtime() is runtime
    dal.request.assert_not_called()
    other_dal.request.assert_not_called()
    with pytest.raises(SnapshotUnavailable, match="unavailable"):
        require_runtime()


@pytest.mark.parametrize("explicit", [False, True])
def test_closed_writer_token_cannot_create_a_new_root_writer(tmp_path, explicit):
    from contextvars import copy_context

    from services.legacy_export_snapshot_service import (
        admitted_writer,
        record_writer_completion,
        use_runtime,
        writer_scope,
    )

    runtime, dal = producer_runtime(tmp_path)
    ran = []

    @admitted_writer("all_kvk")
    def delayed():
        ran.append(True)

    with use_runtime(runtime):
        with writer_scope("all_kvk") as owner:
            inherited = copy_context()
            record_writer_completion(procedure="recompute")
        assert owner.closed
        before = list(dal.mock_calls)
        with pytest.raises(SnapshotUnavailable, match="ended"):
            if explicit:
                delayed(owner_token=owner)
            else:
                inherited.run(delayed)
        assert dal.mock_calls == before
    assert not ran
    dal.request.assert_called_once()
    dal.captured.assert_called_once()


def test_owner_from_another_runtime_is_refused_before_nested_sql_or_new_admission(tmp_path):
    from services.legacy_export_snapshot_service import admitted_writer, use_runtime

    runtime, dal = producer_runtime(tmp_path / "first")
    other, other_dal = producer_runtime(tmp_path / "second")
    owner = runtime.begin_writer("all_kvk")
    before = list(dal.mock_calls)

    @admitted_writer("all_kvk")
    def wrong_scope():
        pytest.fail("A foreign owner must never enter a producer")

    try:
        with use_runtime(other), pytest.raises(SnapshotUnavailable, match="another runtime"):
            wrong_scope(owner_token=owner)
        assert dal.mock_calls == before
        assert not other_dal.mock_calls
        assert not owner.closed
    finally:
        runtime._close_writer(owner)


@pytest.mark.parametrize(
    "action",
    ["authorize_writer", "checkpoint_writer", "finish_writer", "uncertain_writer", "_close_writer"],
)
def test_foreign_runtime_cannot_checkpoint_release_or_close_an_owner(tmp_path, action):
    runtime, dal = producer_runtime(tmp_path / "first")
    other, other_dal = producer_runtime(tmp_path / "second")
    owner = runtime.begin_writer("all_kvk")
    before = list(dal.mock_calls)
    try:
        with pytest.raises(SnapshotUnavailable, match="another runtime"):
            getattr(other, action)(
                owner, *([{"procedure": "recompute"}] if action == "checkpoint_writer" else [])
            )
        assert dal.mock_calls == before
        assert not other_dal.mock_calls
        assert not owner.closed
    finally:
        runtime._close_writer(owner)


def test_explicit_owner_cannot_replace_a_different_inherited_owner(tmp_path):
    from services.legacy_export_snapshot_service import (
        current_owner,
        record_writer_completion,
        use_runtime,
        writer_scope,
    )

    runtime, dal = producer_runtime(tmp_path)
    with use_runtime(runtime), writer_scope("all_kvk") as owner:
        before = list(dal.mock_calls)
        with pytest.raises(SnapshotUnavailable, match="differs from the inherited owner"):
            with writer_scope("all_kvk", owner_token=object()):
                pytest.fail("The explicit token must not override inherited ownership")
        assert current_owner() is owner
        assert dal.mock_calls == before
        record_writer_completion(procedure="recompute")
    dal.captured.assert_called_once()


def test_closed_owner_cannot_checkpoint_after_its_scope_ends(tmp_path):
    runtime, dal = producer_runtime(tmp_path)
    owner = runtime.begin_writer("all_kvk")
    runtime._close_writer(owner)
    before = list(dal.mock_calls)
    with pytest.raises(SnapshotUnavailable, match="ended"):
        runtime.checkpoint_writer(owner, {"procedure": "recompute"})
    assert dal.mock_calls == before


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_caught_nested_failure_retains_owner_and_cannot_capture_partial_generation(
    tmp_path, failure
):
    from services.legacy_export_snapshot_service import (
        admitted_writer,
        current_owner,
        record_writer_completion,
        use_runtime,
    )

    runtime, dal = producer_runtime(tmp_path)

    @admitted_writer("all_kvk")
    def nested():
        raise failure("nested producer did not complete")

    @admitted_writer("all_kvk")
    def outer():
        owner = current_owner()
        with pytest.raises(failure):
            nested()
        assert owner.failed and not owner.closed
        dal.uncertain.assert_not_called()  # The root still owns its SQL work.
        before = list(dal.mock_calls)
        with pytest.raises(SnapshotUnavailable, match="requires reconciliation"):
            record_writer_completion(procedure="recompute")
        with pytest.raises(SnapshotUnavailable, match="requires reconciliation"):
            nested()
        assert dal.mock_calls == before
        return {"success": True}

    with use_runtime(runtime), pytest.raises(SnapshotUnavailable, match="requires reconciliation"):
        outer()
    dal.request.assert_called_once()
    dal.uncertain.assert_called_once()
    dal.captured.assert_not_called()
    runtime.capture.assert_not_called()
    dal.connect.return_value.close.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_tasks_keep_exact_runtime_and_nested_owner_in_offloaded_threads(tmp_path):
    import asyncio

    from services.legacy_export_snapshot_service import (
        admitted_writer,
        current_owner,
        drain_thread,
        record_writer_completion,
        require_runtime,
        use_runtime,
    )

    first, first_dal = producer_runtime(tmp_path / "first")
    second, second_dal = producer_runtime(tmp_path / "second")
    ready = asyncio.Event()

    @admitted_writer("all_kvk")
    def nested(expected, owner):
        assert require_runtime() is expected
        assert current_owner() is owner
        record_writer_completion(procedure="recompute")

    @admitted_writer("all_kvk")
    def producer(expected):
        assert require_runtime() is expected
        owner = current_owner()
        nested(expected, owner, owner_token=owner)
        return {"success": True}

    async def task(runtime):
        with use_runtime(runtime):
            await ready.wait()
            result = await drain_thread(producer, runtime)
            assert require_runtime() is runtime
            assert current_owner() is None
            return result

    pending = [asyncio.create_task(task(runtime)) for runtime in (first, second)]
    ready.set()
    results = await asyncio.gather(*pending)
    assert [r["export_preparation_id"] for r in results] == [
        dal.request.return_value for dal in (first_dal, second_dal)
    ]
    for dal in (first_dal, second_dal):
        dal.request.assert_called_once()
        dal.captured.assert_called_once()
        dal.uncertain.assert_not_called()
    with pytest.raises(SnapshotUnavailable, match="unavailable"):
        require_runtime()


def test_structured_producer_failure_never_invents_committed_generation(tmp_path):
    from services.legacy_export_snapshot_service import admitted_writer, use_runtime

    runtime, dal = producer_runtime(tmp_path)

    @admitted_writer("all_kvk")
    def rejected():
        return {"success": False, "error": "invalid input"}

    with use_runtime(runtime):
        assert rejected() == {"success": False, "error": "invalid input"}
    runtime.capture.assert_not_called()
    dal.uncertain.assert_called_once()
    assert all(c.kwargs["state"] != "committed" for c in dal.transition.call_args_list)


@pytest.mark.parametrize("empty", [False, True])
def test_invalid_workbook_does_not_acquire_shared_writer(tmp_path, monkeypatch, empty):
    from types import SimpleNamespace
    from unittest.mock import Mock

    import kvk_all_importer as importer
    from services.legacy_export_snapshot_service import use_runtime

    runtime, dal = producer_runtime(tmp_path)
    prepare = Mock(
        return_value=SimpleNamespace(
            dataframe=SimpleNamespace(empty=True), sheet_name="Full Data", schema_metadata={}
        )
    )
    if not empty:
        prepare.side_effect = ValueError("invalid workbook")
    monkeypatch.setattr(importer, "prepare_kvk_all_import", prepare)
    connect = Mock()
    monkeypatch.setattr(importer.kvk_all_import_dal, "connect_sql_server", connect)
    with use_runtime(runtime):
        for _ in range(2):
            result = importer.ingest_kvk_all_excel(
                content=b"invalid",
                source_filename="input.xlsx",
                uploader_id=1,
                scan_ts_utc=datetime.now(UTC),
                server="unused",
                database="unused",
                username="unused",
                password="unused",
            )
            assert result["success"] is False
    dal.request.assert_not_called()
    dal.uncertain.assert_not_called()
    connect.assert_not_called()
    runtime.capture.assert_not_called()


def test_valid_workbook_owns_connection_until_close_and_capture(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock

    import kvk_all_importer as importer
    from services.legacy_export_snapshot_service import (
        current_owner,
        record_writer_completion,
        use_runtime,
    )

    runtime, dal = producer_runtime(tmp_path)
    prepared = SimpleNamespace(dataframe=SimpleNamespace(empty=False))
    monkeypatch.setattr(importer, "prepare_kvk_all_import", Mock(return_value=prepared))
    connection = Mock()

    def connect(**kwargs):
        assert current_owner() is not None
        return connection

    def ingest(**kwargs):
        assert kwargs["prepared"] is prepared
        assert current_owner() is not None
        record_writer_completion(procedure="recompute", kvk_no=7)
        return {"success": True}

    original_capture = runtime.capture

    def capture(*args):
        connection.close.assert_called_once()
        return original_capture(*args)

    runtime.capture = capture
    monkeypatch.setattr(importer.kvk_all_import_dal, "connect_sql_server", connect)
    monkeypatch.setattr(importer.kvk_all_import_dal, "ingest_prepared_import", ingest)
    with use_runtime(runtime):
        result = importer.ingest_kvk_all_excel(
            content=b"valid",
            source_filename="input.xlsx",
            uploader_id=1,
            scan_ts_utc=datetime.now(UTC),
            server="unused",
            database="unused",
            username="unused",
            password="unused",
        )
    assert result["export_preparation_id"] == dal.request.return_value
    assert "duration_s" in result and "prepare_ms" in result
    dal.request.assert_called_once()
    dal.uncertain.assert_not_called()


def test_success_without_completion_evidence_cannot_capture(tmp_path):
    from services.legacy_export_snapshot_service import admitted_writer, use_runtime

    runtime, dal = producer_runtime(tmp_path)

    @admitted_writer("all_kvk")
    def no_receipt():
        return {"success": True}

    with use_runtime(runtime), pytest.raises(SnapshotUnavailable, match="acknowledge"):
        no_receipt()
    dal.captured.assert_not_called()
    runtime.capture.assert_not_called()
    # No release call follows the last writing claim, regardless of session close.
    assert dal.transition.call_count == 1


@pytest.mark.parametrize("failure", ["connect", "session", "close"])
def test_writer_setup_failure_marks_durable_claim_uncertain(tmp_path, failure):
    from services.legacy_export_snapshot_service import _captures, use_runtime

    runtime, dal = producer_runtime(tmp_path)
    if failure == "connect":
        dal.connect.side_effect = OSError("connect failed")
    else:
        dal.session.side_effect = OSError("session failed")
        if failure == "close":
            dal.connect.return_value.close.side_effect = OSError("close failed")
    token = _captures.set([("all_kvk", 7, "older")])
    try:
        with use_runtime(runtime), pytest.raises(OSError):
            runtime.begin_writer("all_kvk")
        assert _captures.get()[-1] == ("all_kvk", 7, None)
    finally:
        _captures.reset(token)
    dal.uncertain.assert_called_once_with(dal.claim.return_value)
    dal.captured.assert_not_called()
    runtime.capture.assert_not_called()


@pytest.mark.parametrize("stage", ["preflight", "writing"])
def test_refused_unstarted_operation_is_withdrawn_without_executing(tmp_path, stage):
    from services.legacy_export_snapshot_service import admitted_writer, use_runtime

    runtime, dal = producer_runtime(tmp_path)
    claim = dal.claim.return_value
    dal.claim.side_effect = [None] if stage == "preflight" else [claim, None]
    ran = []

    @admitted_writer("all_kvk")
    def producer():
        ran.append(True)

    with use_runtime(runtime), pytest.raises(SnapshotUnavailable, match="before execution"):
        producer()
    assert not ran
    dal.withdraw_unstarted.assert_called_once_with(dal.request.return_value)
    dal.connect.assert_not_called()


def test_capture_failure_retains_committed_pending_evidence(tmp_path):
    from unittest.mock import Mock

    from services.legacy_export_snapshot_service import (
        admitted_writer,
        record_writer_completion,
        use_runtime,
    )

    runtime, dal = producer_runtime(tmp_path, capture=Mock(side_effect=OSError("capture failed")))

    @admitted_writer("all_kvk")
    def producer():
        record_writer_completion(procedure="recompute")

    with use_runtime(runtime), pytest.raises(OSError):
        producer()
    checkpoint = dal.transition.call_args_list[-1]
    assert checkpoint.kwargs["generation"]["capture"] == "pending"
    assert not checkpoint.kwargs.get("release")
    dal.captured.assert_not_called()
    dal.connect.return_value.close.assert_called_once()


def test_completion_uses_exact_producer_cursor_and_rejects_wrong_season(tmp_path):
    from services.legacy_export_snapshot_service import (
        admitted_writer,
        record_writer_completion,
        use_runtime,
        validate_writer_season,
    )

    runtime, dal = producer_runtime(tmp_path)
    cursor = object()

    @admitted_writer("all_kvk")
    def producer():
        validate_writer_season(7)
        with pytest.raises(SnapshotUnavailable):
            validate_writer_season(8)
        record_writer_completion(cursor=cursor, procedure="recompute")

    with use_runtime(runtime):
        producer()
    checkpoint = next(
        c for c in dal.transition.call_args_list if c.kwargs.get("expected") == "writing"
    )
    assert checkpoint.kwargs["external_cursor"] is cursor


@pytest.mark.asyncio
async def test_cancelled_sql_thread_drains_before_returning():
    import asyncio
    from threading import Event

    from services.legacy_export_snapshot_service import drain_thread

    entered, release, finished = Event(), Event(), Event()

    def worker():
        entered.set()
        assert release.wait(5)
        finished.set()

    task = asyncio.create_task(drain_thread(worker))
    await asyncio.to_thread(entered.wait, 5)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set()


def snapshot(sections=None, **changes):
    sections = sections or (
        OutputSection(
            "players",
            ("id", "dkp", "utc"),
            ((1, Decimal("1.00000000000001"), datetime(2026, 9, 14, tzinfo=UTC)),),
        ),
    )
    config = {"sort": ["id"], "source": "legacy_full_data"}
    args = dict(
        consumer="all_kvk",
        preparation_id=str(uuid4()),
        generation=dict(
            completion="committed",
            commit_identity="receipt-1",
            output_sha256=output_digest(sections),
            config_sha256=configuration_digest(config),
        ),
        config=config,
        provenance={"actor": "test"},
        sections=sections,
    )
    args.update(changes)
    return LegacySnapshot.capture(**args)


def test_snapshot_preserves_exact_scalar_types_and_complete_empty_headers(tmp_path):
    empty = OutputSection("empty", ("GovernorID",), ())
    output = snapshot(
        (OutputSection("data", ("amount",), ((Decimal("1.00000000000001"),),)), empty)
    )
    store = ExportSnapshotStore(tmp_path, "owner-a")
    receipt = output.persist(store)
    restored = LegacySnapshot.load(store.read(receipt))
    assert restored.sections()[0].rows == ((Decimal("1.00000000000001"),),)
    assert restored.sections()[1] == empty


def test_mutating_input_or_decoded_metadata_cannot_retarget_snapshot():
    config = {"tabs": ["one"]}
    sections = (OutputSection("data", ("id",), ((1,),)),)
    generation = dict(
        completion="committed",
        commit_identity="A",
        output_sha256=output_digest(sections),
        config_sha256=configuration_digest(config),
    )
    output = snapshot(sections, config=config, generation=generation)
    config["tabs"].append("two")
    generation["commit_identity"] = "B"
    output.metadata()["generation"]["commit_identity"] = "C"
    assert output.metadata()["generation"]["commit_identity"] == "A"
    assert output.metadata()["config"] == {"tabs": ["one"]}


@pytest.mark.parametrize(
    "generation",
    [
        {"ScanID": 14},
        {"completion": "pending"},
        {
            "completion": "committed",
            "commit_identity": "A",
            "output_sha256": "0" * 64,
            "config_sha256": "0" * 64,
        },
    ],
)
def test_missing_or_advanced_generation_is_unavailable(generation):
    with pytest.raises(SnapshotUnavailable):
        snapshot(generation=generation)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), Decimal("NaN"), b"unsafe", object()])
def test_no_lossy_or_executable_cell_encoding(value):
    with pytest.raises(SnapshotUnavailable):
        snapshot((OutputSection("data", ("value",), ((value,),)),))


def test_snapshot_does_not_accept_noncanonical_or_unknown_payload():
    with pytest.raises(SnapshotUnavailable):
        LegacySnapshot.load(b'{"schema":"unknown"}')
    output = snapshot()
    with pytest.raises(SnapshotUnavailable):
        LegacySnapshot.load(output.payload + b" ")


def test_complete_result_capture_counts_empty_sections():
    class Cursor:
        index = 0

        @property
        def description(self):
            return [("id",)]

        def fetchall(self):
            return [(1,)] if self.index == 0 else []

        def nextset(self):
            self.index += 1
            return self.index < 2

    assert LegacySnapshotDAL.capture_result_sets(Cursor(), ("data", "empty"))[1].rows == ()
    with pytest.raises(SnapshotUnavailable):
        LegacySnapshotDAL.capture_result_sets(Cursor(), ("data",))
    with pytest.raises(SnapshotUnavailable):
        LegacySnapshotDAL.capture_result_sets(Cursor(), ("data", "empty", "missing"))


@pytest.mark.parametrize("operation_state", ["closing", "ready"])
def test_earlier_rollover_blocks_later_preflight(monkeypatch, operation_state):
    from contextlib import contextmanager
    from unittest.mock import Mock

    from services import legacy_export_snapshot_dal as module

    cursor = Mock()

    @contextmanager
    def transaction(_):
        yield cursor

    monkeypatch.setattr(module, "transaction", transaction)
    monkeypatch.setattr(module, "_mutex", lambda *a: None)
    answers = iter(
        [
            dict(
                ActiveJobID=None,
                ActivePreparationID=None,
                ActiveOutputOperationID=None,
                BlockedReason=None,
            ),
            dict(AccountKey="acct", StorageOwner="storage", State="pending", EnqueueSequence=9),
            dict(Ticket=8, State=operation_state),
        ]
    )
    monkeypatch.setattr(module, "one", lambda c: next(answers))
    dal = LegacySnapshotDAL(Mock(), output_operations=True)
    assert (
        dal.claim(
            str(uuid4()),
            account="acct",
            storage_owner="storage",
            stage="preflight",
            resource_keys=("account:acct",),
        )
        is None
    )
    sql = cursor.execute.call_args.args[0]
    assert "State IN ('closing','ready')" in sql
    assert not any(c.args[0].startswith("UPDATE") for c in cursor.execute.call_args_list)


@pytest.mark.parametrize("drift", [None, "legacy", "application"])
def test_actual_producer_cursor_is_checked_without_transaction_side_effects(monkeypatch, drift):
    from unittest.mock import Mock

    from kvk.dal.new_source_import_dal import SourceConflict
    import services.export_execution_dal as evidence
    from tests.test_export_runtime_composition import (
        application_installation_fixture,
        legacy_permission_fixture,
    )

    legacy_observed, legacy = legacy_permission_fixture(monkeypatch)
    app_observed, application = application_installation_fixture(monkeypatch)
    connect, cursor = Mock(), Mock()
    dal = LegacySnapshotDAL(
        connect,
        output_operations=True,
        execution_evidence=True,
        legacy_sql_contract=legacy,
        application_sql_contract=application,
    )
    dal.authorize = Mock()
    legacy_read = Mock(return_value=legacy_observed)
    app_read = Mock(return_value=app_observed)
    monkeypatch.setattr(evidence, "legacy_installation_snapshot", legacy_read)
    monkeypatch.setattr(evidence, "application_installation_snapshot", app_read)
    if drift == "legacy":
        legacy_observed["target"][0]["AuthorityRole"] = 1
    elif drift == "application":
        app_observed["target"]["Principal"] = "another"
    if drift:
        with pytest.raises(SourceConflict):
            dal.verify_producer_cursor("claim", cursor)
    else:
        dal.verify_producer_cursor("claim", cursor)
    dal.authorize.assert_called_once_with("claim")
    legacy_read.assert_called_once_with(cursor, legacy["source"])
    if drift != "legacy":
        app_read.assert_called_once_with(cursor)
    cursor.commit.assert_not_called()
    cursor.rollback.assert_not_called()
    cursor.close.assert_not_called()
    connect.assert_not_called()
