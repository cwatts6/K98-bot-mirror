"""Both enrollment APIs require the exact rollover isolation receipt to proceed."""

import json
import os
from uuid import uuid4

import pytest

from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_enrollment_service import plan_value
from tests.test_export_manual_enrollment import manual_value
from tests.test_rollover_containment_sql import contained_job as contained_job, recovery as recovery

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def enrollment(monkeypatch, request):
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (
            *fixture_module.TABLES,
            "dbo.ExportReplacementPlan",
            "dbo.ExportReplacementTarget",
            "dbo.ExportReplacementVerification",
            "dbo.ExportReplacementActivation",
        ),
    )
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (
            *fixture_module.PROCEDURES,
            "dbo.usp_ExportManualOutputEnrollmentTransition",
            "dbo.usp_ExportOutputEnrollmentTransition",
        ),
    )
    service, f, _ = request.getfixturevalue("recovery")
    report = service.inspect(f.operation)
    service.apply(
        f.operation,
        token=report["token"],
        actor="recovery:" + str(uuid4()),
        reason="Retire old pool",
    )
    return f


@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("receipt", [True, False])
def test_enrollment_only_ignores_receipt_contained_rollover(enrollment, manual, receipt):
    import pyodbc

    f = enrollment
    f.sql.autocommit = True
    if not receipt:
        f.sql.execute("DELETE FROM #ExportTargetContainment WHERE OutputOperationID=?", f.operation)
    value = (manual_value() if manual else plan_value()) | dict(
        account="test-account", manifest_sha256=(b"m" * 32).hex()
    )
    name = (
        "#usp_ExportManualOutputEnrollmentTransition"
        if manual
        else "#usp_ExportOutputEnrollmentTransition"
    )

    def begin():
        return f.sql.execute(
            "EXEC " + name + " @SessionID=?,@PreparationID=?,@Action='begin',@ExpectedVersion=0,"
            "@AccountKey=?,@OwnerID=?,@PlanJson=?,@Actor='test',@Reason='Unrelated fresh enrollment'",
            f.session,
            str(uuid4()),
            value["account"],
            str(uuid4()),
            json.dumps(value),
        ).fetchone()

    if receipt:
        assert begin().State == "preflight"
    else:
        with pytest.raises(pyodbc.Error, match="Existing work"):
            begin()
        assert f.sql.execute("SELECT COUNT(*) FROM #ExportPreparation").fetchval() == 0
    assert (
        f.sql.execute(
            "SELECT State FROM #SourceOutputOperation WHERE OperationID=?", f.operation
        ).fetchval()
        == "uncertain"
    )
