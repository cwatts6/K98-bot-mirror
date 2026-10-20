"""Bounded local progress for authority-authored proofs, never ownership evidence.

SQL proof receipts and private journals remain authoritative. A missing local
request after restart is unavailable; polling never starts or replays work.
"""

from copy import deepcopy
from threading import Lock, Thread, current_thread
from time import monotonic

from services.stats_import_outcome_dal import ImportExecutionActive


class AuthorityProofBusy(ImportExecutionActive):
    """The authenticated authority is occupied by an existing proof."""


class ProofProgress:
    def __init__(self, issue):
        self.issue = issue
        self._lock = Lock()
        self._entries = {}
        self._active = None
        self._closed = False

    def owns_current_thread(self):
        with self._lock:
            return self._active is not None and self._active["thread"] is current_thread()

    def busy(self):
        with self._lock:
            return self._active is not None

    def start(self, request_id, selector):
        with self._lock:
            if self._closed:
                raise AuthorityProofBusy("Authority proof admission is closed.")
            old = self._entries.get(request_id)
            if old is not None:
                self._match(old, selector)
                return self._view(request_id, old)
            if self._active is not None:
                raise AuthorityProofBusy("A publication check is already running.")
            # Only completed progress entries are evicted. Their durable proof
            # remains in SQL/private storage and is never reconstructed here.
            while len(self._entries) >= 16:
                del self._entries[next(iter(self._entries))]
            entry = dict(
                selector=deepcopy(selector), state="running", result=None, started=monotonic()
            )
            thread = Thread(
                target=self._run, args=(entry,), name="authority-publication-proof", daemon=False
            )
            entry["thread"] = thread
            self._entries[request_id] = self._active = entry
            try:
                thread.start()
            except BaseException:
                self._active = None
                entry["state"] = "unavailable"
                raise
            return self._view(request_id, entry)

    def poll(self, request_id, selector):
        with self._lock:
            entry = self._entries.get(request_id)
            if entry is None:
                return dict(
                    request_id=request_id, state="unavailable", elapsed_seconds=0, result=None
                )
            self._match(entry, selector)
            return self._view(request_id, entry)

    @staticmethod
    def _match(entry, selector):
        if entry["selector"] != selector:
            raise ValueError("Proof progress belongs to another exact selector.")

    @staticmethod
    def _view(request_id, entry):
        return dict(
            request_id=request_id,
            state=entry["state"],
            elapsed_seconds=max(0, int(monotonic() - entry["started"])),
            result=deepcopy(entry["result"]),
        )

    def _run(self, entry):
        try:
            result = self.issue(deepcopy(entry["selector"]))
        except BaseException:
            # Exception prose may include private SQL/provider details.
            with self._lock:
                entry["state"] = "unavailable"
        else:
            with self._lock:
                entry.update(state="complete", result=result)
        finally:
            with self._lock:
                self._active = None

    def drain(self):
        with self._lock:
            self._closed = True
            active = self._active
        if active is not None and active["thread"] is not current_thread():
            active["thread"].join()
