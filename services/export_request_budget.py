"""Durable Google pacing. Reservations commit before any wait or provider request."""

from datetime import UTC
from email.utils import parsedate_to_datetime
import math
import time


class BudgetCompletionUnknown(RuntimeError):
    """The request ended but its durable spacing checkpoint is unconfirmed."""


def retry_delay(value, *, attempt=0):
    """Bound untrusted Retry-After; never store provider prose or retry mutations."""
    fallback = min(60, 2 ** min(max(attempt, 0), 6))
    try:
        delay = float(value)
    except (TypeError, ValueError):
        # Preserve absolute HTTP dates; only SQL server UTC may turn one into a
        # bounded duration. A skewed bot wall clock must not shorten cooldown.
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                return fallback
            return date.astimezone(UTC)
        except (TypeError, ValueError, OverflowError):
            return fallback
    return min(3600, max(1, delay)) if math.isfinite(delay) else fallback


class RequestBudget:
    def __init__(self, dal, account_key, *, sleep=time.sleep, stop=None):
        self.dal, self.account_key = dal, account_key
        self.sleep, self.stop = sleep, stop

    def _wait(self, seconds):
        if seconds <= 0:
            return
        if self.stop is not None:
            if self.stop.wait(seconds):
                raise InterruptedError("Export admission stopped.")
        else:
            self.sleep(seconds)

    def __call__(self):
        if self.stop is not None and self.stop.is_set():
            raise InterruptedError("Export admission stopped.")
        reservation = self.dal.reserve_request(self.account_key)
        # Another process may extend the cooldown while this reservation sleeps.
        # Query server time again; local wall-clock changes cannot dispatch early.
        while True:
            self._wait(reservation["WaitSeconds"])
            reservation = self.dal.refresh_reservation(self.account_key, reservation["ReservedUTC"])
            if reservation["WaitSeconds"] <= 0:
                return

    def rejected(self, error, *, attempt=0):
        response = getattr(error, "resp", None)
        status = getattr(response, "status", None)
        if status in (429, 503):
            header = response.get("retry-after") if hasattr(response, "get") else None
            try:
                self.dal.extend_cooldown(self.account_key, retry_delay(header, attempt=attempt))
            except Exception as exc:
                raise BudgetCompletionUnknown("Provider cooldown requires reconciliation.") from exc

    def completed(self):
        # Account admission remains held until this checkpoint commits. Starting
        # the next interval after completion covers a delayed pre-request guard.
        try:
            self.dal.complete_request(self.account_key)
        except Exception as exc:
            raise BudgetCompletionUnknown("Request spacing requires reconciliation.") from exc
