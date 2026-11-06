"""Retained verification history must not consume pool enrollment capacity."""

import json
from uuid import uuid4

import pytest

from services.export_replacement_verification import ReplacementVerificationPlan
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_enrollment_service import plan_value
from tests.test_export_manual_enrollment import manual_value
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    verification as verification,
)


@pytest.fixture
def enrollment_capacity(monkeypatch, request):
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (
            *fixture_module.PROCEDURES,
            "dbo.usp_ExportManualOutputEnrollmentTransition",
            "dbo.usp_ExportOutputEnrollmentTransition",
        ),
    )
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (*fixture_module.TABLES, "dbo.ExportReplacementActivation"),
    )
    return request.getfixturevalue("verification")


@pytest.mark.parametrize("settlement", ["verified", "discarded"])
@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("matching_receipts", [True, False])
def test_repeated_replacement_checks_do_not_exhaust_ordinary_enrollment(
    enrollment_capacity, settlement, manual, matching_receipts
):
    import pyodbc

    r = enrollment_capacity
    for _ in range(8):
        plan = ReplacementVerificationPlan(r.plan.value() | dict(plan_id=str(uuid4())))
        key = plan.value()["plan_id"]
        if settlement == "verified":
            r.runtime.plan = plan
            r.service.run(plan, actor="recovery:" + key, reason="Verify replacement files")
        else:
            r.begin(plan)
            pending = r.service.inspect(key)
            r.service.discard(
                key,
                token=pending["token"],
                actor="recovery:" + str(uuid4()),
                reason="Discard unused read check",
            )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 8
    assert (
        r.f.sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 0
    )
    value = (manual_value() if manual else plan_value()) | dict(
        account="ordinary-enrollment",
        manifest_sha256=(b"m" * 32).hex(),
    )
    procedure = (
        "#usp_ExportManualOutputEnrollmentTransition"
        if manual
        else "#usp_ExportOutputEnrollmentTransition"
    )

    def begin():
        return r.f.sql.execute(
            f"EXEC {procedure} @SessionID=?,@PreparationID=?,@Action='begin',"
            "@ExpectedVersion=0,@AccountKey=?,@OwnerID=?,@PlanJson=?,@Actor='test',"
            "@Reason='Enroll an additional actual pool'",
            r.f.session,
            str(uuid4()),
            value["account"],
            str(uuid4()),
            json.dumps(value),
        ).fetchone()

    if matching_receipts:
        assert begin().State == "preflight"
    else:
        # A preparation that no longer matches the protected verification
        # cannot use this exception to bypass ordinary capacity reservations.
        r.f.sql.execute(
            "UPDATE #ExportPreparation SET RequestHash=HASHBYTES('SHA2_256',RequestHash)"
        )
        r.f.sql.commit()
        with pytest.raises(pyodbc.Error, match="capacity"):
            begin()
    # History stays intact; capacity accounting cannot erase audit evidence.
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 8
