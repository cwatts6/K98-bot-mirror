"""Explicit maintenance results, kept separate from committed business outcomes."""


def result(receipt):
    from services.maintenance_dal import validate_receipts

    rows = receipt["maintenance"]
    validate_receipts(rows)
    return _complete(receipt), receipt


def _complete(receipt):
    from services.maintenance_backup_dal import requested

    rows = receipt["maintenance"]
    complete = all(row["State"] == "complete" for row in rows)
    if any(row["Kind"] == "final_stats" and row["DueGeneration"] > 0 for row in rows):
        backup = receipt.get("backup_request")
        complete = complete and backup is not None and requested(backup)
    return complete


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
    complete = _complete(receipt)
    return dict(receipt, outcome="complete" if complete else "maintenance_outstanding"), complete
