"""Process-local cache observations; never SQL or delivery receipts."""

from dataclasses import asdict, dataclass, field
from uuid import uuid4

PROCESS_ID = uuid4().hex


@dataclass(frozen=True)
class CacheOutcome:
    operation: str
    origin: str
    invocation_id: str = field(default_factory=lambda: uuid4().hex)
    process_id: str = PROCESS_ID
    execution: str = "not_entered"
    availability: str = "unavailable"
    source: str = "unavailable"
    persistence: str = "not_applicable"
    verification: str = "unavailable"
    generation: int = 0
    count: int = 0
    source_time: float = 0.0
    duration_seconds: float = 0.0
    timings: tuple[tuple[str, float], ...] = ()
    diagnostic: str | None = None
    enrichment_omitted: tuple[str, ...] = ()

    def report(self):
        return asdict(self)
