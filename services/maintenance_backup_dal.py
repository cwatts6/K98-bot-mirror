"""Durable claim/ack on the same maintenance session throughout one dispatch."""

from uuid import UUID, uuid4

FIELDS = ("State", "DueGeneration", "RequestedGeneration", "ClaimedGeneration", "ClaimID")


def _receipt(cursor):
    if tuple(column[0] for column in (cursor.description or ())) != FIELDS:
        raise ValueError("Missing backup maintenance receipt.")
    rows = cursor.fetchmany(2)
    if len(rows) != 1:
        raise ValueError("Backup maintenance receipt must be the singleton.")
    row = dict(zip(FIELDS, rows[0], strict=True))
    while cursor.nextset():
        raise ValueError("Unexpected backup maintenance result.")
    if row["ClaimID"] is not None:
        row["ClaimID"] = str(UUID(str(row["ClaimID"])))
    validate(row)
    return row


def validate(row):
    if row["State"] not in {"busy", "pending", "running", "requested", "failed", "unknown"}:
        raise ValueError("Invalid backup request state.")
    due, requested = row["DueGeneration"], row["RequestedGeneration"]
    if not isinstance(due, int) or not isinstance(requested, int) or not 0 <= requested <= due:
        raise ValueError("Invalid backup request generation.")
    if row["State"] == "requested" and requested != due:
        raise ValueError("Unacknowledged backup demand labelled requested.")


def run(cursor, dispatch=None):
    if dispatch is None:
        from log_backup import trigger_log_backup_sync

        dispatch = trigger_log_backup_sync
    claim = str(uuid4())
    cursor.execute("EXEC dbo.usp_MaintenanceBackupClaim @ClaimID=?", claim)
    receipt = _receipt(cursor)
    if receipt["State"] != "running" or receipt["ClaimID"] != claim:
        return receipt
    generation = receipt["ClaimedGeneration"]
    if not isinstance(generation, int) or not 0 < generation <= receipt["DueGeneration"]:
        raise ValueError("Invalid claimed backup generation.")
    try:
        outcome = dispatch()
    except Exception:
        outcome = {"outcome": "unknown", "error": "dispatch_unknown"}
    # Whitelist evidence; never persist credentials, SQL or driver prose.
    state = {"requested": "requested", "not_attempted": "failed"}.get(
        outcome.get("outcome"), "unknown"
    )
    failure = (
        None
        if state == "requested"
        else "not_attempted" if state == "failed" else "dispatch_unknown"
    )
    cursor.execute(
        "EXEC dbo.usp_MaintenanceBackupAcknowledge @ClaimID=?,@Generation=?,@Outcome=?,@Failure=?",
        claim,
        generation,
        state,
        failure,
    )
    return dict(
        _receipt(cursor),
        backup_completed=None,
        dispatch_cleanup=outcome.get("cleanup", "confirmed"),
    )


def requested(receipt):
    validate(receipt)
    return receipt["State"] == "requested" and receipt.get("dispatch_cleanup") != "unconfirmed"
