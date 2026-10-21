from contextlib import contextmanager
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import processing_notification_dal as dal


def setup(monkeypatch, *, state="confirmed"):
    prep_id, job_id, attempt_id, owner = (str(uuid4()) for _ in range(4))
    run = dict(account="a", storage_owner="disk", preparation_id=prep_id)
    scope = dict(AccountKey="a", StorageOwner="disk", ConsumerKind="scan_data")
    prep = dict(scope, JobID=job_id)
    job = dict(scope, JobID=job_id, State=state, OwnerID=owner, Fence=3)
    parts = [
        dict(
            FileID="public-sheet",
            VerificationState="verified",
            QuarantineState="none",
            AclState="public_viewer",
        ),
        dict(
            FileID="private-sheet",
            VerificationState="verified",
            QuarantineState="none",
            AclState="private",
        ),
    ]
    attempt = dict(
        AttemptID=attempt_id,
        PartCount=2,
        ReceiptJson=json.dumps(
            dict(attempt_id=attempt_id, fence=3, files=[p["FileID"] for p in parts])
        ),
    )
    cursor = Mock()

    @contextmanager
    def transaction(connect):
        yield cursor

    monkeypatch.setattr(dal, "transaction", transaction)
    monkeypatch.setattr(dal, "one", Mock(side_effect=[prep, job]))
    monkeypatch.setattr(dal, "rows", Mock(side_effect=[[attempt], parts]))
    runtime = SimpleNamespace(
        account="a",
        store=SimpleNamespace(storage_owner="disk"),
        dal=SimpleNamespace(connect=Mock()),
    )
    return runtime, run, prep, job, attempt, parts, cursor


def test_exact_published_evidence_and_lost_enqueue_ack_can_be_observed(monkeypatch):
    runtime, run, _, job, _, _, cursor = setup(monkeypatch)
    result = dal.read_export_outcome(runtime, run)
    assert result == dict(
        state="confirmed",
        job_id=job["JobID"],
        links=["https://docs.google.com/spreadsheets/d/public-sheet"],
    )
    assert all(call.args[0].startswith("SELECT ") for call in cursor.execute.call_args_list)


@pytest.mark.parametrize("state", ["ready", "running", "failed", "uncertain", "cancelled"])
def test_other_states_have_no_analysis_success_link(monkeypatch, state):
    runtime, run, *_ = setup(monkeypatch, state=state)
    assert dal.read_export_outcome(runtime, run)["links"] == []
    dal.rows.assert_not_called()


@pytest.mark.parametrize("target", ["account", "storage", "job", "parts", "receipt"])
def test_unrelated_or_incomplete_evidence_cannot_announce_success(monkeypatch, target):
    runtime, run, prep, job, attempt, parts, _ = setup(monkeypatch)
    if target == "account":
        prep["AccountKey"] = "other"
    elif target == "storage":
        job["StorageOwner"] = "other"
    elif target == "job":
        run["job_id"] = str(uuid4())
    elif target == "parts":
        parts[0]["VerificationState"] = "pending"
    else:
        attempt["ReceiptJson"] = "{}"
    with pytest.raises(SourceConflict):
        dal.read_export_outcome(runtime, run)
