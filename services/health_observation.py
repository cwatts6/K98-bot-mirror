"""Small immutable presentation records; never work, receipts or write authority."""

from dataclasses import dataclass
from datetime import UTC, datetime
import math
from uuid import uuid4

PROCESS_ID = uuid4().hex


@dataclass(frozen=True, slots=True)
class Observation:
    source: str
    scope_label: str
    observed_utc: str | None = None
    execution: str = "unknown"
    outcome: str = "unknown"
    reason: str = "not_observed"
    reference: str | None = None
    action: str | None = None
    count: int | None = None
    source_utc: str | None = None
    counts: tuple[tuple[str, int], ...] = ()
    started_monotonic: float | None = None

    def project(self, now, *, freshness_seconds=3600, now_monotonic=None):
        age = age_seconds(self.observed_utc, now)
        elapsed = None
        if type(self.started_monotonic) in (int, float) and type(now_monotonic) in (int, float):
            value = now_monotonic - self.started_monotonic
            if math.isfinite(value) and value >= 0:
                elapsed = value
        return dict(
            source=self.source,
            scope_label=self.scope_label,
            observed_utc=self.observed_utc,
            age_seconds=age,
            freshness=(
                "unknown" if age is None else "stale" if age > freshness_seconds else "fresh"
            ),
            execution=self.execution,
            outcome=self.outcome,
            reason=self.reason,
            reference=self.reference,
            action=self.action,
            count=self.count,
            source_utc=self.source_utc,
            counts=dict(self.counts),
            elapsed_seconds=elapsed,
        )


def age_seconds(stamp, now):
    if type(stamp) is not str or len(stamp) > 40:
        return None
    try:
        observed = datetime.fromisoformat(stamp)
        if observed.tzinfo is None or now.tzinfo is None:
            return None
        age = (now - observed).total_seconds()
        return age if math.isfinite(age) and age >= 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def utc():
    return datetime.now(UTC).isoformat()
