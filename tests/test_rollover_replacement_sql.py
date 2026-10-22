"""Rollover isolation through fresh read verification and pool activation."""

from datetime import datetime
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.export_replacement_dal import ExportReplacementDAL
from services.rollover_replacement_dal import RolloverReplacementDAL
from tests import (
    test_export_replacement_service as proposal_fixture,
    test_export_target_containment_sql as fixture_module,
)
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_verification_sql import verification as verification
from tests.test_rollover_containment_sql import contained_job as contained_job, recovery as recovery

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def proposal_service(monkeypatch, request):
    monkeypatch.setattr(fixture_module, "TABLES", (*fixture_module.TABLES, "KVK.SeasonSource"))

    # Reuse the real end-to-end provider-read harness with a typed rollover owner.
    class RolloverRequest:
        def getfixturevalue(self, name):
            containment, fixture, docs = request.getfixturevalue(name)
            fixture.original_job = fixture.job
            fixture.job = fixture.operation
            return containment, fixture, docs

    service, fixture, docs, args = proposal_fixture.proposal_service.__wrapped__(
        monkeypatch, RolloverRequest()
    )
    service.dal = ExportReplacementDAL(fixture.connect, owner_kind="rollover")
    return service, fixture, docs, args


def seed_choices(r, activation):
    r.f.sql.autocommit = True
    original = activation["input_commitment"]
    for number, choice in (
        (original["OldKVK"], original["OldChoiceID"]),
        (original["NewKVK"], original["NewChoiceID"]),
    ):
        r.f.insert(
            "SeasonSource",
            dict(
                KVK_NO=number,
                SourceKey="snapshot_report_v1",
                ChoiceID=choice,
                ChosenBy="test",
                ChosenUTC=datetime(2026, 10, 1),
                Reason="Synthetic choice",
                ProvenanceJson="{}",
                SeasonState="open",
                SeasonVersion=1,
            ),
        )
    pools = r.service.proposals.containment.pools
    return RolloverReplacementDAL(pools)


def test_complete_fresh_pool_is_verified_and_activated_without_old_replay(activation):
    r = activation
    result = r.apply()
    assert result["business_resolved"] is False
    assert result["input_commitment"]["OperationID"] == r.f.operation
    assert result["input_commitment"]["NewKVK"] == 8
    assert r.apply() == result
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 1
    assert r.f.sql.execute("SELECT State FROM #SourceOutputOperation").fetchval() == "uncertain"
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActiveOutputOperationID IS NOT NULL"
        ).fetchval()
        == 0
    )
    assert all(
        request.operation
        in {"drive.files.get", "drive.permissions.list", "sheets.get", "sheets.values.batchGet"}
        for request in r.runtime.sent
    )
    assert r.service.proposals.containment.inspect(r.f.operation)["outcome"] == "targets_isolated"


@pytest.mark.parametrize("lost", ["containment", "activation"])
def test_rollover_history_loss_uses_separate_verified_attestation(activation, lost):
    from tests.registration_attestation_harness import qualify_pool_attestation

    qualify_pool_attestation(activation, lost=lost)


def test_replacement_queue_preserves_original_choices_and_reconciles_lost_ack(
    activation, monkeypatch
):
    r = activation
    activated = r.apply()
    dal = seed_choices(r, activated)
    args = dict(actor="recovery:" + str(uuid4()), reason="Continue original season change")
    confirm = dal.pools.confirm
    calls = []

    def lost(*values):
        calls.append(1)
        confirm(*values)
        raise UncertainCommit("Synthetic lost queue reply")

    monkeypatch.setattr(dal.pools, "confirm", lost)
    with pytest.raises(UncertainCommit):
        dal.enqueue(r.f.operation, activated, **args)
    queued = dal.enqueue(r.f.operation, activated, **args)
    assert queued["State"] == "closing" and queued["OldKVK"] == 7 and queued["NewKVK"] == 8
    assert queued["OperationID"] == args["actor"][9:]
    assert len(calls) == 1
    assert dal.read(r.f.operation, activated) == queued
    with pytest.raises(SourceConflict, match="Another action"):
        dal.enqueue(
            r.f.operation, activated, actor="recovery:" + str(uuid4()), reason=args["reason"]
        )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #SourceOutputOperation").fetchval() == 2


def test_changed_season_choice_cannot_silently_change_rollover_intent(activation):
    r = activation
    activated = r.apply()
    dal = seed_choices(r, activated)
    r.f.sql.execute("UPDATE #SeasonSource SET ChoiceID=NEWID() WHERE KVK_NO=8")
    with pytest.raises(SourceConflict, match="original season choices"):
        dal.enqueue(r.f.operation, activated, actor="recovery:" + str(uuid4()), reason="Continue")
    assert r.f.sql.execute("SELECT COUNT(*) FROM #SourceOutputOperation").fetchval() == 1
