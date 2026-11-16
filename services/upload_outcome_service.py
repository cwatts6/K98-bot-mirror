"""Primitive upload evidence; never grants admission, retries, or export authority."""

from dataclasses import dataclass

from stats_alerts.delivery_outcomes import DeliveryResult


@dataclass(frozen=True)
class UploadOutcome:
    business: str = "not_started"
    execution: str = "queued"

    def details(self):
        return {
            "outcome_version": 1,
            "business_outcome": self.business,
            "execution": self.execution,
        }


def display_count(value):
    return "Unavailable" if value is None else str(value)


def display_delivery(value, error=None):
    if error is not None:
        return "Unavailable; import remains committed"
    details = delivery_details(value)
    if not details["attempts"]:
        return "Unverified (no delivery receipt)"
    return "; ".join(f"{item['component']}: {item['outcome']}" for item in details["attempts"])[
        :1000
    ]


def delivery_details(value):
    """Keep mixed attempts distinct; a legacy None return is not a receipt."""
    if not isinstance(value, DeliveryResult):
        return {"delivery": "unverified", "attempts": []}
    return {
        "delivery": "observed",
        "attempts": [
            {
                "component": item.component,
                "outcome": item.outcome,
                "acknowledged": item.acknowledged,
                "persistence": item.persistence,
            }
            for item in value.attempts
        ],
    }


class CommittedKvkResult(dict):
    """Created only after the ingest/recompute transaction commit acknowledges."""


class LocationWriteResult(tuple):
    """Tuple-compatible acknowledged result, including unavailable counts/cleanup."""

    def __new__(cls, imported, total):
        result = super().__new__(cls, (imported, total))
        result.cleanup = "settled"
        return result
