"""SQL bigint/null boundaries and retained claim compatibility; no SQL calls."""

from copy import deepcopy

import pytest

from services import maintenance_dal as dal, maintenance_service as service

MAX_GENERATION = 2**63 - 1
CLAIM = "11111111-1111-4111-8111-111111111111"


def receipt():
    return [
        dict(
            Kind=kind,
            DueGeneration=0,
            CompletedGeneration=0,
            ClaimedGeneration=None,
            ClaimID=None,
            State="complete",
            FirstErrorNumber=None,
            LastErrorNumber=None,
        )
        for kind in sorted(dal.KINDS)
    ]


@pytest.mark.parametrize("field", ["DueGeneration", "CompletedGeneration", "ClaimedGeneration"])
@pytest.mark.parametrize("invalid", [True, False, "1", 1.0, -1, 2**63])
@pytest.mark.parametrize("entry", ["validate", "result", "evidence"])
def test_generation_domain_rejected_at_every_entry(field, invalid, entry):
    rows = receipt()
    row = next(row for row in rows if row["Kind"] == "import")
    row.update(DueGeneration=1, CompletedGeneration=1, ClaimedGeneration=1, ClaimID=CLAIM)
    row[field] = invalid
    packet = dict(maintenance=rows)
    with pytest.raises(ValueError):
        if entry == "validate":
            dal.validate_receipts(rows)
        elif entry == "result":
            service.result(packet)
        else:
            service.evidence((True, packet))


@pytest.mark.parametrize("field", ["DueGeneration", "CompletedGeneration"])
def test_required_generations_cannot_be_null(field):
    rows = receipt()
    rows[0][field] = None
    with pytest.raises(ValueError):
        dal.validate_receipts(rows)


def test_seed_rows_and_maximum_bigint_are_valid():
    rows = receipt()
    dal.validate_receipts(rows)
    assert service.result(dict(maintenance=rows))[0]
    row = next(row for row in rows if row["Kind"] == "import")
    row.update(
        DueGeneration=MAX_GENERATION,
        CompletedGeneration=MAX_GENERATION,
        ClaimedGeneration=MAX_GENERATION,
        ClaimID=CLAIM,
    )
    dal.validate_receipts(rows)
    assert service.result(dict(maintenance=rows))[0]


@pytest.mark.parametrize("state", ["complete", "pending", "running", "failed", "unknown"])
def test_retained_claim_allowed_after_completion_or_new_due_work(state):
    rows = receipt()
    row = next(row for row in rows if row["Kind"] == "import")
    row.update(
        DueGeneration=2,
        CompletedGeneration=2 if state == "complete" else 1 if state == "pending" else 0,
        ClaimedGeneration=2 if state == "complete" else 1,
        ClaimID=CLAIM,
        State=state,
    )
    dal.validate_receipts(rows)
    assert service.result(dict(maintenance=rows))[0] is (state == "complete")


def test_valid_receipt_order_is_not_significant():
    rows = receipt()
    packet = dict(maintenance=list(reversed(deepcopy(rows))))
    assert service.result(packet)[0]
    assert service.evidence((True, packet))[1]
