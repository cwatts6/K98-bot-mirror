"""Optional CSV download log, isolated from upload locks and required file custody."""

import csv
import io
import logging
from pathlib import Path
from uuid import uuid4

from services.optional_upload_transport import OptionalWriter


class FileCleanupUnconfirmed(RuntimeError):
    """Retain the exact file handle; never retry close or certify drainage."""

    def __init__(self, stream):
        super().__init__("Optional download log cleanup is unconfirmed")
        self.stream = stream


class DownloadLogWriter(OptionalWriter):
    def __init__(self, path):
        super().__init__(capacity=64, max_bytes=2048, name="upload-download-log")
        self.path = Path(path)
        self.reference = str(uuid4())

    def _observe(self, state):
        try:
            from services.operation_diagnostics import (
                offer_upload_observation,
                upload_worker_summary,
            )

            offer_upload_observation(
                self.reference, state, self.dropped + self.failures, kind="file"
            )
            upload_worker_summary(
                "file",
                self.latest,
                error_type=self.first_failure,
                dropped=self.dropped,
                failures=self.failures,
            )
        except Exception:
            self.observation_unavailable = True

    def offer_row(self, row):
        # No arbitrary objects, filenames/rows over budget, or staged file handles.
        try:
            if type(row) not in (list, tuple) or len(row) != 5:
                raise ValueError("Invalid download row")
            if any(type(value) is not str or len(value) > 2048 for value in row):
                raise ValueError("Invalid download field")
            buffer = io.StringIO(newline="")
            csv.writer(buffer).writerow(row)
            accepted = self.offer(buffer.getvalue().encode("utf-8"))
            self._observe("observed" if accepted else "failed")
            return accepted
        except Exception:
            self.dropped += 1
            self._observe("failed")
            return False

    def write(self, payload):
        stream = self.path.open("ab")
        try:
            stream.write(payload)
        finally:
            try:
                stream.close()
            except Exception as exc:
                self._cleanup_unconfirmed = FileCleanupUnconfirmed(stream)
                self.request_close()
                self._observe("failed")
                raise self._cleanup_unconfirmed from exc

    def wait_closed(self):
        try:
            super().wait_closed()
        finally:
            self._observe("failed" if self._cleanup_unconfirmed else "settled")

    def observe_settlement(self):
        self._observe("failed" if self.latest == "failed" else "completed")


_writer = None
_start_attempted = False
_stopped = False
_startup_error = None
_unavailable_offers = 0
# E91: local four-configuration, independent-file and physical-drain gates passed.
QUALIFIED = True


def configure(path):
    global _writer, _start_attempted, _startup_error
    if not QUALIFIED or _start_attempted or _stopped:
        return
    _start_attempted = True
    try:
        _writer = DownloadLogWriter(path).start()
    except Exception as exc:
        _startup_error = type(exc).__name__
        try:
            logging.getLogger(__name__).warning(
                "Optional download log unavailable: %s", _startup_error
            )
        except Exception:
            pass
    _summary()


def _summary():
    from services.operation_diagnostics import upload_worker_summary

    upload_worker_summary(
        "file",
        _writer.latest if _writer else "unavailable",
        _unavailable_offers,
        _startup_error,
        dropped=_writer.dropped if _writer else 0,
        failures=_writer.failures if _writer else 0,
    )


def offer(row):
    global _unavailable_offers
    if _writer is not None:
        return _writer.offer_row(row)
    _unavailable_offers = min(_unavailable_offers + 1, 2**63 - 1)
    _summary()
    return False


async def record_download(path, row):
    """Adoption is gated; after adoption overload never falls back to awaited I/O."""
    if QUALIFIED or _start_attempted:
        return offer(row)
    from file_utils import append_csv_line

    try:
        await append_csv_line(path, row)
        return True
    except Exception:
        return False


def request_close():
    global _stopped
    _stopped = True
    if _writer is not None:
        _writer.request_close()


def wait_closed():
    try:
        if _writer is not None:
            _writer.wait_closed()
    finally:
        _summary()


def shutdown():
    request_close()
    wait_closed()
