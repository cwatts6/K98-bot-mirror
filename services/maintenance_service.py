"""Explicit maintenance results, kept separate from committed business outcomes."""


def result(receipt):
    rows = receipt["maintenance"]
    return all(row["State"] == "complete" for row in rows), receipt


def evidence(value):
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or not isinstance(value[1], dict)
        or "maintenance" not in value[1]
    ):
        return {"outcome": "unconfirmed", "procedure": "dbo.usp_update_stats"}, False
    receipt = value[1]
    from services.maintenance_dal import validate_receipts

    validate_receipts(receipt["maintenance"])
    complete = all(row["State"] == "complete" for row in receipt["maintenance"])
    return dict(receipt, outcome="complete" if complete else "maintenance_outstanding"), complete
