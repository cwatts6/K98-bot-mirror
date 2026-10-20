"""Receipt transitions exercise the real DAL with a transactional in-memory cursor."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from unittest.mock import Mock

import pytest

from kvk.dal import new_source_admin_dal as dal_module
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.source_receipt_state import accepted_outcome, receipt_actions
from kvk.services.new_source_admin_service import SourceAdminService
from tests.test_kvk_source_admin import ADMIN, FIELDS, NOW, prepare, rig as rig, upload


def receipt(status="received", *, cancelled=False, accepted=False, action="accept"):
    outcome = {
        "state": "accepted; not published",
        "observation_revision_id": "revision",
        "scan_id": 6,
    }
    row = {
        "AttemptID": "receipt",
        "ActorID": "10",
        "KVK_NO": 16,
        "Status": status,
        "ObservationRevisionID": "revision" if status == "accepted" else None,
        "AggregateRevisionID": None,
        "payload": {
            "version": 2,
            "history": [],
            "proposal": {
                "action": action,
                "expires": (NOW + timedelta(minutes=5)).isoformat(),
                "candidate": {},
            },
        },
    }
    if status == "accepted":
        row["payload"]["outcome"] = outcome
    elif accepted:
        row["payload"]["history"] = [{"outcome": outcome}]
    if cancelled:
        row["payload"]["cancelled"] = True
    return row


@pytest.mark.parametrize(
    "status,cancelled,accepted,action,expected",
    [
        ("received", False, False, "accept", (True, False, True, False)),
        ("validated", False, False, "accept", (True, True, True, False)),
        ("accepted", False, True, "accept", (False, False, False, True)),
        ("accepted", False, True, "configure", (True, False, False, True)),
        ("accepted", False, True, "correct", (True, False, False, True)),
        ("received", True, False, "accept", (False, False, False, False)),
        ("validated", True, False, "correct", (False, False, False, False)),
        ("validated", True, True, "configure", (True, False, False, True)),
        ("validated", False, True, "configure", (True, True, True, False)),
    ],
)
def test_action_matrix(status, cancelled, accepted, action, expected):
    allowed = receipt_actions(
        receipt(status, cancelled=cancelled, accepted=accepted, action=action), action, NOW
    )
    assert (allowed.prepare, allowed.confirm, allowed.cancel, allowed.pair) == expected


@pytest.mark.parametrize(
    "expiry", [None, "invalid", NOW.isoformat(), (NOW - timedelta(seconds=1)).isoformat()]
)
def test_expired_or_invalid_proposal_requires_review(expiry):
    row = receipt("validated")
    row["payload"]["proposal"]["expires"] = expiry
    allowed = receipt_actions(row, "accept", NOW)
    assert allowed.prepare and allowed.cancel and not allowed.confirm


class DurableReceipt:
    """The actual DAL's SQL boundary is mocked; transition code is never replaced."""

    def __init__(self, monkeypatch, row):
        self.row = deepcopy(row)
        self.writes = []
        self.cursor = Mock()
        self.dal = dal_module.SourceAdminDAL(Mock(), Mock())

        @contextmanager
        def transaction(connect):
            before, writes = deepcopy(self.row), len(self.writes)
            try:
                yield self.cursor
            except BaseException:
                self.row = before
                del self.writes[writes:]
                raise

        def save(cursor, current, payload, status, observation=None, aggregate=None):
            # Mirror CK_SourceImportAttempt_Result, including its validated-null rule.
            assert (status in ("accepted", "duplicate")) == bool(observation or aggregate)
            self.writes.append(deepcopy(payload))
            self.row.update(
                payload=deepcopy(payload),
                Status=status,
                ObservationRevisionID=observation,
                AggregateRevisionID=aggregate,
            )

        monkeypatch.setattr(dal_module, "transaction", transaction)
        monkeypatch.setattr(dal_module, "lock_scope", Mock())
        monkeypatch.setattr(self.dal, "_receipt", lambda *args: deepcopy(self.row))
        monkeypatch.setattr(self.dal, "_save", save)
        monkeypatch.setattr(self.dal, "_context", lambda *args: {})

    def cancel(self, version=2):
        return self.dal.cancel("receipt", "10", "20", version)

    def prepare(self, action, version=2):
        return self.dal.prepare(
            "receipt", "10", "20", version, {"action": action, "candidate": {}, "guard": {}}
        )


@pytest.mark.parametrize("status", ["received", "validated"])
def test_real_dal_cancel_is_retained_and_idempotent(monkeypatch, status):
    store = DurableReceipt(monkeypatch, receipt(status))
    cancelled = store.cancel()
    assert cancelled["payload"]["cancelled"]
    assert cancelled["payload"]["version"] == 3
    assert cancelled["cancel_saved"] is True
    assert store.cancel(2) == store.cancel(3) == dict(cancelled, cancel_saved=False)
    assert "cancel_saved" not in store.row
    assert len(store.writes) == 1
    with pytest.raises(SourceConflict):
        store.prepare("accept", 3)
    operation = Mock()
    with pytest.raises(SourceConflict):
        store.dal.confirm("receipt", "10", "20", 3, operation)
    operation.assert_not_called()
    store.dal.artifacts.assert_not_called()


def test_real_dal_accepted_cancel_and_repeat_confirm_are_noops(monkeypatch):
    original = receipt("accepted")
    store = DurableReceipt(monkeypatch, original)
    assert store.cancel() == dict(original, cancel_saved=False)
    operation = Mock()
    assert store.dal.confirm("receipt", "10", "20", 2, operation) == original
    operation.assert_not_called()
    assert not store.writes
    with pytest.raises(SourceConflict):
        store.prepare("accept")
    with pytest.raises(SourceConflict):
        store.cancel(1)
    assert store.row == original


def test_cancelled_configuration_can_be_explicitly_reprepared_without_losing_acceptance(
    monkeypatch,
):
    store = DurableReceipt(monkeypatch, receipt("accepted"))
    store.prepare("configure")
    assert store.row["ObservationRevisionID"] is None
    assert accepted_outcome(store.row)["scan_id"] == 6
    store.cancel(3)
    before = deepcopy(store.row)
    with pytest.raises(SourceConflict):
        store.prepare("accept", 4)
    assert store.row == before
    renewed = store.prepare("configure", 4)
    assert renewed["payload"]["version"] == 5
    assert not renewed["payload"].get("cancelled")
    assert any(h.get("cancelled") for h in renewed["payload"]["history"])
    assert accepted_outcome(renewed)["observation_revision_id"] == "revision"


def test_stale_prepare_cannot_reopen_a_cancelled_receipt(monkeypatch):
    store = DurableReceipt(monkeypatch, receipt("validated"))
    store.cancel()
    before = deepcopy(store.row)
    with pytest.raises(SourceConflict):
        store.prepare("correct", 2)
    assert store.row == before and len(store.writes) == 1


def test_confirmation_wins_before_cancel_without_cancelling_accepted_data(monkeypatch):
    row = receipt("validated")
    row["payload"]["proposal"]["guard"] = {}
    store = DurableReceipt(monkeypatch, row)
    outcome = {"state": "accepted; not published", "observation_revision_id": "new-revision"}
    operation = Mock(return_value=outcome)
    result = store.dal.confirm("receipt", "10", "20", 2, operation)
    assert store.cancel() == dict(result, cancel_saved=False)
    assert len(store.writes) == 1
    operation.assert_called_once()


def test_service_rejects_accepted_generic_preparation_before_parsing(rig):
    service, repo = rig
    row = prepare(service, upload(service))
    row = service.confirm(ADMIN, row["AttemptID"], 2)
    before = deepcopy(repo.receipts)
    service._prepared = Mock(side_effect=AssertionError("must not parse"))
    with pytest.raises(SourceConflict, match="already accepted"):
        service.prepare_metadata(ADMIN, row["AttemptID"], 2, FIELDS, reason="review")
    assert repo.receipts == before
    service._prepared.assert_not_called()


def test_explicit_player_correction_still_works_from_accepted_receipt(rig):
    service, repo = rig
    row = prepare(service, upload(service))
    row = service.confirm(ADMIN, row["AttemptID"], 2)
    selected = row["ObservationRevisionID"]
    repo.guard["revision"] = {"SelectedRevisionID": selected, "SelectionVersion": 1}
    reviewed = service.prepare_metadata(
        ADMIN,
        row["AttemptID"],
        2,
        FIELDS,
        action="correct",
        reason="Explicit correction",
        expected_revision=selected,
        expected_revision_version=1,
    )
    assert reviewed["payload"]["version"] == 3
    assert accepted_outcome(reviewed)["observation_revision_id"] == selected
    service.confirm(ADMIN, row["AttemptID"], 3)
    assert repo.calls[-1][1].admin_authorized


def test_resume_does_not_implicitly_offer_another_completed_correction():
    assert SourceAdminService.resume_action(receipt("accepted", action="correct")) == "accept"
    assert SourceAdminService.resume_action(receipt("validated", action="correct")) == "correct"


def test_cancelled_followup_summary_keeps_accepted_identity():
    summary = SourceAdminService.summary(receipt("validated", cancelled=True, accepted=True))
    assert "State: pending work cancelled" in summary
    assert "observation_revision_id: revision" in summary
    assert "scan_id: 6" in summary


def test_receipt_modal_rechecks_durable_version_and_state(rig):
    service, repo = rig
    row = prepare(service, upload(service))
    rid = row["AttemptID"]
    service.confirm(ADMIN, rid, 2)
    with pytest.raises(SourceConflict, match="unavailable"):
        service.check_receipt_action(ADMIN, rid, 2, "accept", "prepare")
    with pytest.raises(SourceConflict, match="changed"):
        service.check_receipt_action(ADMIN, rid, 1, "accept", "pair")
    assert service.check_receipt_action(ADMIN, rid, 2, "accept", "pair")["Status"] == "accepted"


def test_cancel_then_reupload_does_not_allocate_a_scan_or_delete_original(rig, monkeypatch):
    service, repo = rig
    row = upload(service)
    store = DurableReceipt(monkeypatch, row)
    cancelled = store.dal.cancel(row["AttemptID"], "10", "20", 1)
    repo.receipts[row["AttemptID"]] = cancelled
    assert not repo.accepted and not repo.calls
    second = prepare(service, upload(service))
    result = service.confirm(ADMIN, second["AttemptID"], 2)
    assert result["payload"]["outcome"]["scan_id"] == 1
    assert repo.receipts[row["AttemptID"]]["payload"]["cancelled"]
    assert (service.artifacts.root / row["StorageKey"]).exists()


def test_recreated_service_prepares_cancelled_config_using_retained_b0(rig, monkeypatch):
    service, repo = rig
    row = service.confirm(ADMIN, prepare(service, upload(service))["AttemptID"], 2)
    store = DurableReceipt(monkeypatch, row)
    store.prepare("configure")
    store.cancel(3)
    repo.receipts[row["AttemptID"]] = store.row
    fresh = SourceAdminService(service.access, repo, service.artifacts, now=lambda: NOW)
    # Existing-window updates keep frozen scope/weights; only endpoints are proposed.
    repo.guard["config"] = {"ConfigVersionID": "config", "StartScanID": 1, "EndScanID": 2}
    reviewed = fresh.prepare_configuration(
        ADMIN,
        row["AttemptID"],
        4,
        window="fight:pass4 | Pass 4 | 1 | 3",
        coverage="",
        mapping="",
        weights="",
        reason="Explicit new configuration review",
    )
    assert reviewed["payload"]["proposal"]["b0_revision"] == row["ObservationRevisionID"]


@pytest.mark.parametrize("initial_proposal", ["absent", None])
def test_first_prepare_then_cancel_handles_null_historical_proposal(monkeypatch, initial_proposal):
    row = receipt("received")
    if initial_proposal == "absent":
        row["payload"].pop("proposal")
    else:
        row["payload"]["proposal"] = None
    store = DurableReceipt(monkeypatch, row)
    reviewed = store.prepare("accept")
    assert reviewed["payload"]["history"][0]["proposal"] is None
    assert accepted_outcome(reviewed) == {}
    assert receipt_actions(reviewed, "accept", NOW).cancel
    assert "State: validated" in SourceAdminService.summary(reviewed)
    cancelled = store.cancel(3)
    assert accepted_outcome(cancelled) == {}
    allowed = receipt_actions(cancelled, "accept", NOW)
    assert not any((allowed.prepare, allowed.confirm, allowed.cancel, allowed.pair))
    assert "pending work cancelled" in SourceAdminService.summary(cancelled)
    assert store.cancel(3)["cancel_saved"] is False
