"""Present a saved publication decision without contacting the provider."""

from datetime import UTC, datetime


def _utc(value):
    # SQL datetime2 columns are UTC but pyodbc returns naive datetime values.
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return None


def publication_result(row, action):
    """Only the latest action and its exact settled proof can claim a result."""
    if row["SourceKind"] != "export_job" or not action:
        return None
    started, completed = _utc(action["CreatedUTC"]), _utc(action["UpdatedUTC"])
    state = action["State"]
    receipt = row["evidence"].get("publication_receipt") or {}
    outcome = "unverified"
    if state in {"dispatched", "unknown"}:
        outcome = "pending"
    elif state == "not_applied":
        outcome = "not_verified"
    elif (
        state == "verified"
        and receipt.get("actor") == f"recovery:{str(action['ActionID']).lower()}"
        and receipt.get("proof_id")
        and receipt.get("state") in {"confirmed", "damaged", "absent"}
    ):
        outcome = receipt["state"]
    descriptions = {
        "confirmed": "The saved check verified the published output against its retained receipt and contents. This proves the result at that check; later spreadsheet changes are not covered.",
        "damaged": "The saved check verified damaged published contents. Review the separate guided recovery decision before rebuilding anything.",
        "absent": "The saved check verified the publication absent. Review the separate guided retry decision; no retry has been requested by this check.",
        "pending": "The accepted publication check is awaiting verification. Use Recheck for progress; do not submit another check or restart.",
        "not_verified": "The latest publication check did not establish a verified result. The original delivery receipt is preserved; it does not prove the current contents.",
        "unverified": "The latest action has no matching saved publication proof in this observation. Use Recheck to refresh the evidence; current contents are not established.",
    }
    return dict(
        outcome=outcome,
        explanation=descriptions[outcome],
        started_utc=started.isoformat() if started else None,
        completed_utc=completed.isoformat() if completed and outcome != "pending" else None,
        duration_seconds=(
            round(max(0, (completed - started).total_seconds()), 1)
            if started and completed and outcome != "pending"
            else None
        ),
    )
