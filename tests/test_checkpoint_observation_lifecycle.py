"""Checkpoint retries and observations cannot replay producers or settle uncertainty."""

from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from core.sql_observation import ObservationBusy, observe_call, observing
from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services import export_contention as contention
from services.authority_observation import dispatch_observation
from services.export_proof_progress import AuthorityProofBusy
from tests.test_export_contention import clock


@pytest.mark.parametrize("state,number", [("42000", 1222), ("40001", 1205)])
def test_checkpoint_retry_waits_after_rollback_and_close(monkeypatch, state, number):
    clock(monkeypatch)
    connections = []

    @contention.retry_coordination(budget_seconds=5)
    def checkpoint():
        cn = MagicMock(autocommit=False)
        connections.append(cn)
        with contention.transaction(lambda: cn, retry_metadata=True):
            if len(connections) == 1:
                raise Exception(state, f"private SQL contents ({number})")
        return "committed"

    assert checkpoint() == "committed"
    assert len(connections) == 2
    connections[0].rollback.assert_called_once()
    connections[0].close.assert_called_once()
    connections[0].commit.assert_not_called()
    connections[1].commit.assert_called_once()


@pytest.mark.parametrize("stage", ["rollback", "close", "commit"])
def test_lifecycle_ack_failure_never_authorizes_retry(monkeypatch, stage):
    clock(monkeypatch)
    cn = MagicMock(autocommit=False)
    # Even another matching SQL timeout from cleanup is not the body error.
    getattr(cn, stage).side_effect = Exception("42000", "cleanup (1222)")
    connect = Mock(return_value=cn)

    @contention.retry_coordination
    def checkpoint():
        with contention.transaction(connect, retry_metadata=True):
            if stage != "commit":
                raise Exception("42000", "body (1222)")

    with pytest.raises(UncertainCommit if stage == "commit" else Exception) as caught:
        checkpoint()
    assert not isinstance(caught.value, contention.MetadataContention)
    connect.assert_called_once()


@pytest.mark.parametrize("error", [Exception("42000", "(1222)"), Exception("40001", "(1205)")])
def test_other_transactions_never_gain_row_retry(monkeypatch, error):
    clock(monkeypatch)
    connect = Mock(return_value=Mock(autocommit=False))

    @contention.retry_coordination
    def mutate():
        with contention.transaction(connect):
            raise error

    with pytest.raises(Exception) as caught:
        mutate()
    assert caught.value is error
    connect.assert_called_once()


@pytest.mark.parametrize("state,number", [("42000", 1222), ("40001", 1205)])
def test_busy_observer_closes_before_reporting_wait(state, number):
    cn = Mock(autocommit=False)

    def inspect():
        with contention.transaction(lambda: cn):
            raise Exception(state, f"private ({number})")

    with pytest.raises(ObservationBusy):
        observe_call(inspect)
    cn.rollback.assert_called_once()
    cn.close.assert_called_once()
    cn.commit.assert_not_called()


READS = [
    dict(action=action, operation="inspect", job_id="job")
    for action in (
        "failed_export_recovery",
        "replacement_recovery",
        "rollover_replacement_recovery",
    )
] + [
    dict(action="inspect_configuration_recovery", preparation_id="prep"),
    dict(action="inspect_target_recovery", job_id="job"),
    dict(action="evidence_recovery", operation="inspect", reference="ref"),
    dict(action="evidence_recovery", operation="pending_page", after=None),
]


@pytest.mark.parametrize("message", READS)
def test_whole_readonly_authority_call_observes_initial_selection(message):
    def early_read(request):
        assert observing()
        with contention.transaction(lambda: Mock(autocommit=False)):
            raise Exception("42000", "initial read (1222)")

    with pytest.raises(AuthorityProofBusy):
        dispatch_observation(early_read, dict(version=1, **message))
    assert not observing()


@pytest.mark.parametrize("operation", ["execute", "reconcile", "context", "attest", "restore"])
def test_mutations_and_sealing_do_not_inherit_readonly_semantics(operation):
    error = Exception("42000", "(1222)")

    def mutate(request):
        assert not observing()
        raise error

    with pytest.raises(Exception) as caught:
        dispatch_observation(
            mutate,
            dict(version=1, action="replacement_recovery", operation=operation, job_id="job"),
        )
    assert caught.value is error


@pytest.mark.parametrize(
    "error", [OSError("lost reply"), UncertainCommit("unknown"), SourceConflict("owner changed")]
)
def test_observation_never_converts_transport_commit_or_scope_failure(error):
    with pytest.raises(type(error)) as caught:
        dispatch_observation(Mock(side_effect=error), dict(version=1, **READS[0]))
    assert caught.value is error


@pytest.mark.parametrize(
    "defect", [None, "missing", "State", "OwnerID", "Fence", "Resolution", "CompletedFileName"]
)
def test_checkpoint_validates_exact_completed_receipt_before_metadata_write(monkeypatch, defect):
    from services import legacy_export_snapshot_dal as module

    claim = module.PreparationClaim(str(uuid4()), "account", str(uuid4()), 1, 2, ())
    receipt = dict(
        State="completed", OwnerID=claim.owner, Fence=1, Resolution=None, CompletedFileName="file"
    )
    if defect == "missing":
        receipt = None
    elif defect:
        receipt[defect] = {
            "State": "running",
            "OwnerID": str(uuid4()),
            "Fence": 2,
            "Resolution": "supersede_partial",
            "CompletedFileName": "other",
        }[defect]
    cn = MagicMock(autocommit=False)
    cn.cursor.return_value.fetchone.return_value = None
    dal = module.LegacySnapshotDAL(lambda: cn)
    dal._authorize = Mock(return_value=dict(State="writing", ConsumerKind="scan_data"))
    monkeypatch.setattr(module, "one", lambda _: receipt)
    cas = Mock(return_value=dict(Version=3))
    monkeypatch.setattr(module, "_cas", cas)
    args = dict(
        expected="writing",
        state="committed",
        generation=dict(producer=dict(procedure="dbo.UPDATE_ALL2", completed_filename="file")),
    )
    if defect:
        with pytest.raises(SourceConflict):
            dal.transition(claim, **args)
        cas.assert_not_called()
        cn.rollback.assert_called_once()
    else:
        assert dal.transition(claim, **args).version == 3
        cas.assert_called_once()
        cn.commit.assert_called_once()


def test_external_atomic_cursor_is_not_reopened_or_retried(monkeypatch):
    from services import legacy_export_snapshot_dal as module

    claim = module.PreparationClaim(str(uuid4()), "account", str(uuid4()), 1, 2, ())
    connect = Mock()
    dal = module.LegacySnapshotDAL(connect)
    error = Exception("42000", "producer transaction (1222)")
    dal._authorize = Mock(side_effect=error)
    with pytest.raises(Exception) as caught:
        dal.transition(
            claim, expected="writing", state="committed", generation={}, external_cursor=object()
        )
    assert caught.value is error
    dal._authorize.assert_called_once()
    connect.assert_not_called()
