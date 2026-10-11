"""Receipt action policy over durable facts, independent of Discord and SQL."""

from dataclasses import dataclass
from datetime import UTC, datetime


def accepted_details(row):
    """Return acceptance and its own proposal, never a later proposal's metadata."""
    payload = row["payload"]
    entries = [payload, *reversed(payload.get("history", []))]
    for entry in entries:
        # Legacy cancellation entries copy outcomes without accepting any input.
        # Configuration outcomes also repeat a B0 revision without accepting input.
        if (
            entry.get("action") == "cancel"
            or (entry.get("proposal") or {}).get("action") == "configure"
        ):
            continue
        outcome = entry.get("outcome")
        if outcome and (
            outcome.get("observation_revision_id") or outcome.get("aggregate_revision_id")
        ):
            # Older cancellation history may repeat an outcome without its proposal.
            proposal = next(
                (
                    item["proposal"]
                    for item in entries
                    if item.get("outcome") == outcome
                    and item.get("proposal")
                    and item["proposal"].get("action") != "configure"
                ),
                {},
            )
            return outcome, proposal
    if row["Status"] in ("accepted", "duplicate"):
        return {
            "observation_revision_id": row.get("ObservationRevisionID"),
            "aggregate_revision_id": row.get("AggregateRevisionID"),
        }, (
            {}
            if (payload.get("proposal") or {}).get("action") == "configure"
            else (payload.get("proposal") or {})
        )
    return {}, {}


def accepted_outcome(row):
    """Keep accepted inputs visible while a later proposal is pending or cancelled."""
    return accepted_details(row)[0]


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
