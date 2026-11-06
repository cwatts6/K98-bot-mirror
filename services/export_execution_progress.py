"""Owned per-account execution with passive retained progress and physical drain.

The cache is only a response projection. Reconstruction invokes exact SQL/private
settlement and never uses a missing cache entry as permission to dispatch again.
"""

from contextvars import copy_context
from copy import deepcopy
from threading import Lock, Thread, current_thread
from time import monotonic

from services.export_proof_progress import AuthorityProofBusy


class ExecutionProgress:
    def __init__(self, issue, *, report_failure=None):
        self.issue, self.report_failure = issue, report_failure
        self._lock = Lock()
        self._entries, self._active = {}, {}
        self._closed = False

    def busy(self):
        with self._lock:
            return bool(self._active)

    def owns_current_thread(self):
        with self._lock:
            return any(entry["thread"] is current_thread() for entry in self._active.values())

    def start(self, identifier, account, selector):
        with self._lock:
            key = (selector["action"], identifier)
            previous = self._entries.get(key)
            if previous is not None:
                self._match(previous, selector)
                return self._view(identifier, previous)
            if self._closed or account in self._active:
                raise AuthorityProofBusy("An owned account operation is already in progress.")
            # Bounded result projection, not durable recovery authority. Never
            # evict active work; repeat starts resolve SQL before any dispatch.
            completed = [
                key
                for key, entry in self._entries.items()
                if entry["state"] in {"complete", "unavailable"}
            ]
            while len(self._entries) >= 16 and completed:
                del self._entries[completed.pop(0)]
            if len(self._entries) >= 16:
                raise AuthorityProofBusy("Owned execution capacity is in use.")
            entry = dict(
                selector=deepcopy(selector),
                account=account,
                state="running",
                result=None,
                started=monotonic(),
                needs_attention=False,
            )
            context = copy_context()
            worker = Thread(
                target=context.run,
                args=(self._run, entry),
                name="authority-execution-" + identifier,
                daemon=False,
            )
            entry["thread"] = worker
            self._entries[key] = self._active[account] = entry
            try:
                worker.start()
            except BaseException:
                del self._active[account]
                entry.update(state="unavailable", needs_attention=True)
                raise
            return self._view(identifier, entry)

    def poll(self, identifier, selector):
        with self._lock:
            entry = self._entries.get((selector["action"], identifier))
            if entry is None:
                return dict(
                    request_id=identifier,
                    state="unavailable",
                    result=None,
                    elapsed_seconds=0,
                    needs_attention=False,
                )
            self._match(entry, selector)
            return self._view(identifier, entry)

    @staticmethod
    def _match(entry, selector):
        if entry["selector"] != selector:
            raise ValueError("Execution progress belongs to another exact request.")

    @staticmethod
    def _view(identifier, entry):
        return dict(
            request_id=identifier,
            state=entry["state"],
            result=deepcopy(entry["result"]),
            elapsed_seconds=max(0, int(monotonic() - entry["started"])),
            needs_attention=entry["needs_attention"],
        )

    def _run(self, entry):
        def progress(state, attention=False):
            with self._lock:
                entry.update(state=state, needs_attention=attention)

        try:
            result = self.issue(deepcopy(entry["selector"]), progress)
        except BaseException as error:
            if self.report_failure is not None:
                try:
                    self.report_failure(deepcopy(entry["selector"]), error)
                except BaseException:
                    pass  # Diagnostics cannot strand physical admission.
            with self._lock:
                entry.update(state="unavailable", needs_attention=True)
        else:
            with self._lock:
                entry.update(state="complete", result=result, needs_attention=False)
        finally:
            with self._lock:
                del self._active[entry["account"]]

    def stop_admission(self):
        with self._lock:
            self._closed = True

    def drain(self):
        self.stop_admission()
        with self._lock:
            active = tuple(self._active.values())
        for entry in active:
            if entry["thread"] is not current_thread():
                entry["thread"].join()
