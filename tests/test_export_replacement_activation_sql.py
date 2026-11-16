"""Atomic activation and immutable lineage on session-local SQL tables."""

import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.export_replacement_activation import ReplacementActivationService
from services.export_replacement_activation_dal import ReplacementActivationDAL
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    recovery as recovery,
    verification as verification,
)

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def activation(monkeypatch, request):
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (*fixture_module.TABLES, "dbo.ExportReplacementActivation", "KVK.SourceOutputFile"),
    )
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (*fixture_module.PROCEDURES, "dbo.usp_ExportReplacementActivate"),
    )
    r = request.getfixturevalue("verification")
    key = r.plan.value()["plan_id"]
    checked = r.service.run(r.plan, actor="recovery:" + key, reason="Verify replacements")
    r.activation = ReplacementActivationService(
        dal=ReplacementActivationDAL(r.f.connect),
        proposals=r.service.proposals,
        verification=r.service,
        authority=r.service.authority,
    )
    r.arguments = dict(
        token=checked["token"], actor="recovery:" + str(uuid4()), reason="Use verified replacements"
    )

    def apply():
        return r.activation.apply(r.plan.value()["replacement_id"], key, **r.arguments)

    r.apply = apply
    return r


def test_activation_binds_verified_files_without_rewriting_unknown_business_result(activation):
    r = activation
    result = r.apply()
    assert result["business_resolved"] is False
    assert result["registration"]["legacy_configuration"]["scan_data"]["destinations"] == [
        "fresh-file"
    ]
    assert result["registration"]["legacy_configuration"]["scan_data"]["grid_ids"][
        "fresh-file"
    ] == {"Sheet1": 42}
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert r.apply() == result
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 1


def test_activation_lost_reply_reads_original_receipt(activation, monkeypatch):
    r = activation
    original = r.activation.dal.activate

    def lose(**kwargs):
        original(**kwargs)
        raise UncertainCommit("Injected lost activation reply")

    monkeypatch.setattr(r.activation.dal, "activate", lose)
    with pytest.raises(UncertainCommit):
        r.apply()
    assert r.apply()["registration_sha256"]
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 1


@pytest.mark.parametrize("damage", ["token", "receipt", "proposal", "fresh_target"])
def test_changed_verification_or_target_prevents_activation(activation, damage):
    import pyodbc

    r = activation
    if damage == "token":
        r.arguments["token"] = "0" * 64
    elif damage == "receipt":
        reference = r.f.sql.execute(
            "SELECT ReceiptReference FROM #ExportReplacementVerification"
        ).fetchval()
        r.docs[str(reference).lower()] += b" "
    elif damage == "proposal":
        r.f.sql.execute(
            "UPDATE #ExportReplacementPlan SET BaseRegistrationHash=CAST(? AS binary(32))",
            b"x" * 32,
        )
    else:
        r.f.sql.execute(
            "INSERT #ExportJobResource(JobID,ResourceKey) VALUES(?,'destination:fresh-file')",
            r.f.job,
        )
    with pytest.raises((SourceConflict, pyodbc.Error)):
        r.apply()
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 0
