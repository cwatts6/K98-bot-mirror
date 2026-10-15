"""Actual replacement-proposal transactions, entirely in session-local objects."""

import json
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests import test_export_target_containment_sql as fixture_module

contained_job = fixture_module.contained_job
pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def replacement_sql(monkeypatch, request):
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (*fixture_module.TABLES, "dbo.ExportReplacementPlan", "dbo.ExportReplacementTarget",
         "dbo.ExportReplacementVerification", "dbo.ExportReplacementActivation"),
    )
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (*fixture_module.PROCEDURES, "dbo.usp_ExportReplacementPlanCreate"),
    )
    f = request.getfixturevalue("contained_job")
    f.apply()
    args = dict(
        ReplacementID=str(uuid4()),
        ContainmentID=f.arguments["ContainmentID"],
        AccountKey="test-account",
        BaseRegistrationHash=b"a" * 32,
        ProjectedRegistrationHash=b"b" * 32,
        ReceiptHash=b"r" * 32,
        ReceiptReference=str(uuid4()),
        MappingJson=json.dumps([dict(old="old-file", new="fresh-file")]),
        Actor="recovery:" + str(uuid4()),
        Reason="Prepare fresh outputs",
    )

    def create(**changes):
        values = args | changes
        f.sql.execute("BEGIN TRANSACTION")
        try:
            result = f.sql.execute(
                "EXEC #usp_ExportReplacementPlanCreate " + ",".join("@" + k + "=?" for k in values),
                *values.values(),
            ).fetchone()
            f.sql.execute("COMMIT")
            return result
        except Exception:
            f.sql.execute("IF @@TRANCOUNT>0 ROLLBACK")
            raise

    return SimpleNamespace(f=f, args=args, create=create)


def test_proposal_preserves_unknown_outcome_and_does_not_admit_or_activate(replacement_sql):
    r = replacement_sql
    sql = r.f.sql
    job = sql.execute("SELECT * FROM #ExportJob").fetchone()
    resources = sql.execute("SELECT * FROM #ExportResource ORDER BY ResourceKey").fetchall()
    stream = sql.execute("SELECT * FROM #ExportExecutionStream").fetchone()
    result = r.create()
    assert str(result.ReplacementID).lower() == r.args["ReplacementID"]
    assert result.MappingJson == r.args["MappingJson"]
    assert bytes(result.ReceiptHash) == r.args["ReceiptHash"]
    assert tuple(
        sql.execute("SELECT OldFileID,NewFileID FROM #ExportReplacementTarget").fetchone()
    ) == (
        "old-file",
        "fresh-file",
    )
    assert sql.execute("SELECT * FROM #ExportJob").fetchone() == job
    assert sql.execute("SELECT * FROM #ExportResource ORDER BY ResourceKey").fetchall() == resources
    assert sql.execute("SELECT * FROM #ExportExecutionStream").fetchone() == stream
    assert sql.execute("SELECT COUNT(*) FROM #ExportManualFileOrigin").fetchval() == 0
    assert (
        sql.execute(
            "SELECT COUNT(*) FROM #ExportProviderRequestEvent WHERE State='unknown'"
        ).fetchval()
        == 1
    )


@pytest.mark.parametrize(
    "mapping",
    [
        [],
        {},
        [dict(old="other-file", new="fresh-file")],
        [dict(old="old-file", new="old-file")],
        [dict(old="old-file", new="fresh-file", extra=True)],
        [dict(old="old-file", new="fresh-file ")],
        [dict(old="old-file", new="x" * 129)],
        [dict(old="old-file", new="fresh/file")],
        [dict(old="old-file", new=123456)],
        [dict(old="old-file", new="fresh-file"), dict(old="old-file", new="fresh-other")],
    ],
)
def test_invalid_mapping_has_no_partial_proposal(replacement_sql, mapping):
    import pyodbc

    r = replacement_sql
    with pytest.raises(pyodbc.Error):
        r.create(MappingJson=json.dumps(mapping))
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 0
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementTarget").fetchval() == 0


@pytest.mark.parametrize(
    "changes",
    [
        dict(AccountKey="foreign-account"),
        dict(ContainmentID=str(uuid4())),
        dict(ProjectedRegistrationHash=b"a" * 32),
        dict(ReceiptHash=None),
        dict(ReceiptReference=None),
        dict(Actor=""),
        dict(Reason=""),
    ],
)
def test_scope_and_evidence_failures_retain_original_isolation(replacement_sql, changes):
    import pyodbc

    r = replacement_sql
    with pytest.raises(pyodbc.Error):
        r.create(**changes)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 0
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportContainedTarget WHERE FileID='old-file'"
        ).fetchval()
        == 1
    )


def test_existing_target_history_is_not_adopted_and_lost_reply_cannot_duplicate(replacement_sql):
    import pyodbc

    r = replacement_sql
    r.f.insert(
        "ExportResource",
        dict(ResourceKey="destination:used-file", ResourceKind="destination", Fence=0, Version=1),
    )
    with pytest.raises(pyodbc.Error, match="existing execution"):
        r.create(MappingJson=json.dumps([dict(old="old-file", new="used-file")]))
    r.create()
    with pytest.raises(pyodbc.Error, match="already recorded"):
        r.create()
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 1
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementTarget").fetchval() == 1
