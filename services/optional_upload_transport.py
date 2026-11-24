"""Bounded single-writer transport for optional upload observations only.

No retry, spill, background replacement, or business admission. close() discards
unentered work and joins entered work; returning is the physical drain receipt.
"""

from collections import deque
import threading


class OptionalWriter:
    def __init__(self, *, capacity, max_bytes, name):
        self.capacity = capacity
        self.max_bytes = max_bytes
        self._queue = deque()
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._closed = False
        self._started = False
        self.dropped = 0
        self.failures = 0
        self.high_water = 0
        self.entered = 0
        self.settled = 0
        self.first_failure = None
        self.latest = "not_started"
        self._cleanup_unconfirmed = None
        self._discarded = ()
        self._thread = threading.Thread(target=self._run, name=name, daemon=False)

    def start(self):
        if self._started or self._closed:
            raise RuntimeError("Optional writer cannot restart")
        try:
            self._thread.start()
        except Exception as exc:
            self._closed = True
            self.first_failure = type(exc).__name__
            self.latest = "start_failed"
            raise
        self._started = True
        self.latest = "running"
        return self

    def offer(self, payload):
        if type(payload) is not bytes or len(payload) > self.max_bytes:
            self.dropped += 1
            return False
        if not self._lock.acquire(blocking=False):
            self.dropped += 1
            return False
        try:
            if not self._started or self._closed or len(self._queue) >= self.capacity:
                self.dropped += 1
                return False
            self._queue.append(payload)
            self.high_water = max(self.high_water, len(self._queue))
            self._wake.set()
            return True
        finally:
            self._lock.release()

    def request_close(self):
        """Close admission before any physical wait; retain bounded discard custody."""
        with self._lock:
            self._closed = True
            self.dropped += len(self._queue)
            if self._queue:
                self._discarded = tuple(self._queue)
            self._queue.clear()
            self._wake.set()
        self.latest = "closing"

    def wait_closed(self):
        if self._started:
            self._thread.join()  # Never report a timed-out join as drained.
        self._discarded = ()
        if self._cleanup_unconfirmed is not None:
            self.latest = "cleanup_unconfirmed"
            raise self._cleanup_unconfirmed
        self.latest = "drained"

    def close(self):
        self.request_close()
        self.wait_closed()

    def _run(self):
        while True:
            self._wake.wait()
            with self._lock:
                if self._closed:
                    return
                if not self._queue:
                    self._wake.clear()
                    continue
                payload = self._queue.popleft()
                self.entered += 1
            try:
                self.write(payload)
                self.latest = "settled"
            except Exception as exc:
                self.failures += 1
                self.first_failure = self.first_failure or type(exc).__name__
                self.latest = "failed"
            finally:
                self.settled += 1
                try:
                    self.observe_settlement()
                except Exception:
                    # Observation failure cannot reinterpret or replay entered I/O.
                    pass

    def write(self, payload):
        raise NotImplementedError

    def observe_settlement(self):
        """Optional adapter hook; never part of the physical write outcome."""
