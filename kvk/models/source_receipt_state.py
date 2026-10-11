"""Receipt action policy over durable facts, independent of Discord and SQL."""

from dataclasses import dataclass
from datetime import UTC, datetime


def accepted_outcome(row):
    """Keep accepted inputs visible while a later proposal is pending or cancelled."""
    payload = row["payload"]
    outcomes = [payload.get("outcome")] + [
        entry.get("outcome") for entry in reversed(payload.get("history", []))
    ]
    for outcome in outcomes:
        if outcome and (
            outcome.get("observation_revision_id") or outcome.get("aggregate_revision_id")
        ):
            return outcome
    if row["Status"] in ("accepted", "duplicate"):
        return {
            "observation_revision_id": row.get("ObservationRevisionID"),
            "aggregate_revision_id": row.get("AggregateRevisionID"),
        }
    return {}


def has_accepted_input(row):
    outcome = accepted_outcome(row)
    return bool(outcome.get("observation_revision_id") or outcome.get("aggregate_revision_id"))


def pending_work(row):
    return (
        row["Status"] in ("received", "validated")
        and not row["payload"].get("cancelled")
        and not row["payload"].get("outcome")
    )


def preparation_error(row, action):
    accepted = has_accepted_input(row)
    if action not in ("accept", "correct", "finalize", "configure"):
        return "Choose an explicit source action before preparing this receipt."
    if row["payload"].get("cancelled") and not accepted:
        return "This intake was cancelled. Retain its receipt and use a new upload."
    if row["Status"] not in ("received", "validated", "accepted", "duplicate"):
        return "This receipt cannot be prepared; inspect its retained state."
    if action == "accept" and (accepted or row["Status"] in ("accepted", "duplicate")):
        return "This input is already accepted. Use an explicit administrator follow-up action."
    if action == "configure" and not accepted_outcome(row).get("observation_revision_id"):
        return "Configuration requires an accepted player receipt."
    return None


def unexpired(expires, now):
    try:
        expiry = datetime.fromisoformat(expires) if isinstance(expires, str) else expires
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return now < expiry
    except (AttributeError, TypeError, ValueError):
        return False


@dataclass(frozen=True)
class ReceiptActions:
    prepare: bool
    confirm: bool
    cancel: bool
    pair: bool


def receipt_actions(row, action, now, *, roster_correction=False):
    proposal = row["payload"].get("proposal", {})
    pending = pending_work(row)
    return ReceiptActions(
        prepare=preparation_error(row, action) is None,
        confirm=(
            pending
            and row["Status"] == "validated"
            and proposal.get("action") == action
            and (not roster_correction or proposal.get("mode") == "roster")
            and unexpired(proposal.get("expires"), now)
        ),
        cancel=pending,
        pair=has_accepted_input(row) and not pending,
    )
