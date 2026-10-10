"""Structured enqueue acknowledgment, distinct from provider confirmation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportSubmission:
    job_id: str
    preparation_id: str

    @property
    def log(self):
        return f"Queued export job {self.job_id}; provider completion is pending."

    def __iter__(self):
        # Preserve legacy callers that unpack the result; new pipeline uses fields.
        yield False
        yield self.log
