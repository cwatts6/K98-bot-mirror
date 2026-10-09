"""Evidence decisions must never turn absence, stale ownership or age into success."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import stats_import_outcome_service as service
from services.stats_import_outcome_dal import StatsImportOutcomeDAL as DAL


def evidence(state="rolled_back"):
    owner, prep = str(uuid4()), str(uuid4())
    return (
        dict(
            PreparationID=prep,
            OwnerID=owner,
            Fence=4,
            Version=5,
            State="uncertain",
            JobID=None,
            SpoolKey=None,
            GenerationJson=None,
            AccountKey="a",
            StorageOwner="disk-a",
            ConsumerKind="scan_data",
        ),
        dict(PreparationID=prep, OwnerID=owner, Fence=4, Version=2, State=state, Resolution=None),
        [
            dict(
                ResourceKey="sql_snapshot:legacy_outputs",
                OwnerID=owner,
                Fence=4,
                ActivePreparationID=prep,
                ActiveJobID=None,
                ActiveOutputOperationID=None,
                Version=8,
                BlockedReason="uncertain",
            )
        ],
    )


@pytest.mark.parametrize(
    "state,expected",
    [
        ("prepared", "release_failure"),
        ("rolled_back", "release_failure"),
        ("partial", "supersede_partial"),
    ],
)
def test_only_proven_states_admit_specific_resolution(state, expected):
    assert DAL.action(*evidence(state)) == expected


@pytest.mark.parametrize("state", ["running", "import_committed", "completed", "unknown"])
def test_nonterminal_or_completed_import_never_discarded(state):
    with pytest.raises(SourceConflict):
        DAL.action(*evidence(state))


@pytest.mark.parametrize(
    "target,key,value",
    [
        (0, "OwnerID", str(uuid4())),
        (0, "Fence", 99),
        (0, "JobID", str(uuid4())),
        (0, "SpoolKey", "retained-output"),
        (0, "State", "captured"),
        (0, "GenerationJson", '{"capture":"pending"}'),
        (1, "OwnerID", str(uuid4())),
        (1, "Fence", 99),
        (2, "OwnerID", str(uuid4())),
        (2, "Fence", 99),
        (2, "ActiveJobID", str(uuid4())),
        (2, "ActiveOutputOperationID", str(uuid4())),
        (2, "ResourceKey", "account:a"),
    ],
)
def test_stale_or_unrelated_work_retained(target, key, value):
    rows = evidence()
    (rows[2][0] if target == 2 else rows[target])[key] = value
    with pytest.raises(SourceConflict):
        DAL.action(*rows)


def test_missing_receipt_and_multiple_resources_not_adopted():
    p, e, r = evidence()
    for args in [(p, None, r), (None, e, r), (p, e, []), (p, e, r * 2)]:
        with pytest.raises(SourceConflict):
            DAL.action(*args)


@pytest.mark.parametrize("index,key", [(0, "Version"), (1, "Version"), (2, "Version")])
def test_preview_bound_to_all_versions(index, key):
    original = evidence()
    changed = deepcopy(original)
    (changed[2][0] if index == 2 else changed[index])[key] += 1
    assert DAL.token(*original) != DAL.token(*changed)


@pytest.mark.parametrize(
    "field,value",
    [("AccountKey", "b"), ("StorageOwner", "other-disk"), ("ConsumerKind", "all_kvk")],
)
def test_resolution_cannot_cross_runtime_scope(field, value):
    dal = DAL(Mock(), account="a", storage_owner="disk-a")
    p, _, _ = evidence()
    dal._scope(p)
    p[field] = value
    with pytest.raises(SourceConflict):
        dal._scope(p)


@pytest.mark.parametrize("action", ["hold", "supersede_partial"])
def test_automatic_observer_never_accepts_partial_or_unknown(monkeypatch, action):
    dal = Mock()
    dal.inspect.return_value = dict(action=action, execution={"State": "partial"})
    monkeypatch.setattr(service, "outcome_dal", lambda _: dal)
    assert service.settle_known_failure(object(), str(uuid4())) is False
    dal.settle.assert_not_called()


def test_automatic_resolution_uses_exact_preview_token(monkeypatch):
    dal = Mock()
    dal.settle.return_value = "release_failure"
    dal.inspect.return_value = dict(action="release_failure", token="proof")
    monkeypatch.setattr(service, "outcome_dal", lambda _: dal)
    prep = str(uuid4())
    assert service.settle_known_failure(object(), prep) is True
    assert dal.settle.call_args.args == (prep,)
    assert dal.settle.call_args.kwargs["token"] == "proof"
    assert "allow_partial" not in dal.settle.call_args.kwargs


def test_lost_resolution_acknowledgment_is_not_replayed(monkeypatch):
    dal = Mock()
    dal.inspect.return_value = dict(action="release_failure", token="proof")
    dal.settle.side_effect = TimeoutError()
    monkeypatch.setattr(service, "outcome_dal", lambda _: dal)
    prep = str(uuid4())
    assert service.settle_known_failure(object(), prep) is False
    dal.inspect.return_value = dict(action="resolved")
    assert service.settle_known_failure(object(), prep) is True
    assert dal.settle.call_count == 1


def test_recovered_captured_generation_remains_available_to_pipeline(monkeypatch):
    prep, owner_id = str(uuid4()), str(uuid4())
    owner = SimpleNamespace(
        stats_execution_registered=True,
        claim=SimpleNamespace(preparation_id=prep, owner=owner_id, fence=3),
    )
    runtime = Mock()
    runtime.dal.read.return_value = dict(State="captured", OwnerID=owner_id, Fence=3)
    receipt = Mock()
    receipt.read.return_value = dict(State="completed")
    monkeypatch.setattr(service, "outcome_dal", lambda _: receipt)
    assert service.recover_completed_writer(runtime, owner) is True
    runtime.collect_capture.assert_called_once_with(owner)
    runtime.finish_writer.assert_not_called()
    runtime.checkpoint_writer.assert_not_called()


def test_untrusted_preparation_text_not_logged(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(service, "logger", logger)
    service.event("secret\nforged log", "admin_resolution", "held", action="inspect")
    assert "secret" not in logger.log.call_args.args[-1]


def test_logging_failure_does_not_erase_settlement_acknowledgment(monkeypatch):
    dal = Mock()
    dal.inspect.return_value = dict(action="release_failure", token="proof")
    dal.settle.return_value = "release_failure"
    monkeypatch.setattr(service, "outcome_dal", lambda _: dal)
    logger = Mock()
    logger.log.side_effect = OSError("log disk unavailable")
    monkeypatch.setattr(service, "logger", logger)
    assert service.settle_known_failure(object(), str(uuid4())) is True
    dal.settle.assert_called_once()


@pytest.mark.parametrize("dispatched", [False, True])
def test_live_pre_import_failure_release_requires_no_dispatch(tmp_path, dispatched):
    from services import legacy_export_snapshot_service as snapshots
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(
        tmp_path, configuration={"scan_data": dict(consumer="scan_data", destinations=["file-a"])}
    )
    with snapshots.use_runtime(runtime), pytest.raises(RuntimeError, match="failure"):
        with snapshots.writer_scope("scan_data") as owner:
            owner.stats_import_context = True
            owner.stats_execution_dispatched = dispatched
            raise RuntimeError("preparation failure")
    releases = [
        c
        for c in dal.transition.call_args_list
        if c.kwargs.get("release") and c.kwargs.get("expected") == "writing"
    ]
    if dispatched:
        assert not releases
        dal.uncertain.assert_called_once()
    else:
        assert len(releases) == 1
        assert releases[0].kwargs["state"] == "unavailable"
        dal.uncertain.assert_not_called()
    runtime.capture.assert_not_called()


def test_registration_uses_output_acknowledgment_when_nocount_is_on(monkeypatch):
    from contextlib import contextmanager

    from services import stats_import_outcome_dal as module

    prep = str(uuid4())
    cursor = Mock(rowcount=-1, description=[("PreparationID",)])
    cursor.fetchone.return_value = (prep,)

    @contextmanager
    def transaction(_connect):
        yield cursor

    monkeypatch.setattr(module, "transaction", transaction)
    monkeypatch.setattr(module, "_mutex", lambda *_: None)
    claim = SimpleNamespace(
        account="a", preparation_id=prep, owner=str(uuid4()), fence=1, version=2
    )
    dal = DAL(Mock(), account="a", storage_owner="disk-a")
    dal.prepare(claim, "stats_" + uuid4().hex + ".ready.csv")
    cursor.fetchone.return_value = None
    with pytest.raises(SourceConflict):
        dal.prepare(claim, "stats_" + uuid4().hex + ".ready.csv")


@pytest.mark.parametrize(
    "observation", ["prepared", "absent", "unavailable", "wrong_owner", "running"]
)
def test_lost_registration_ack_is_reconciled_without_reinserting(monkeypatch, observation):
    from kvk.dal.new_source_import_dal import UncertainCommit
    from services import legacy_export_snapshot_service as snapshots

    prep, owner_id = str(uuid4()), str(uuid4())
    filename = "stats_" + uuid4().hex + ".ready.csv"
    owner = SimpleNamespace(
        stats_execution_registered=False,
        claim=SimpleNamespace(preparation_id=prep, owner=owner_id, fence=3),
    )
    dal = Mock()
    dal.prepare.side_effect = UncertainCommit("acknowledgment lost")
    evidence = dict(
        PreparationID=prep,
        OwnerID=owner_id,
        Fence=3,
        CompletedFileName=filename,
        State="prepared",
        Resolution=None,
    )
    if observation == "absent":
        evidence = None
    elif observation == "unavailable":
        dal.read.side_effect = TimeoutError("database unavailable")
    elif observation == "wrong_owner":
        evidence["OwnerID"] = str(uuid4())
    elif observation == "running":
        evidence["State"] = "running"
    dal.read.return_value = evidence
    monkeypatch.setattr(snapshots, "current_owner", lambda: owner)
    monkeypatch.setattr(snapshots, "require_runtime", lambda: object())
    monkeypatch.setattr(service, "outcome_dal", lambda _: dal)
    if observation == "prepared":
        assert service.register_execution(filename) == prep
    else:
        with pytest.raises((UncertainCommit, TimeoutError, SourceConflict)):
            service.register_execution(filename)
    assert owner.stats_execution_registered is (observation != "absent")
    dal.prepare.assert_called_once()
    dal.read.assert_called_once_with(prep)


def test_uncertain_registration_cannot_use_unregistered_cleanup(tmp_path):
    from services import legacy_export_snapshot_service as snapshots
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(
        tmp_path, configuration={"scan_data": dict(consumer="scan_data", destinations=["file-a"])}
    )
    with snapshots.use_runtime(runtime):
        owner = runtime.begin_writer("scan_data")
        owner.stats_import_context = True
        owner.stats_execution_registered = True
        calls_before = list(dal.transition.call_args_list)
        try:
            with pytest.raises(snapshots.SnapshotUnavailable, match="unstarted"):
                runtime.unstarted_stats_writer(owner)
            assert dal.transition.call_args_list == calls_before
        finally:
            runtime._close_writer(owner)
