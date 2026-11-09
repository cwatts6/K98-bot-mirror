"""Observation context for complete fixed read-only authority requests.

Selectors are deliberately explicit. Execute, reconcile, context (which may seal
input), proof publication and transport failures retain their original semantics.
The broker still authenticates and validates each request before accessing data.
"""

from collections import deque
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from copy import deepcopy
from threading import Condition, Thread, current_thread

from core.sql_connection_custody import custody_snapshot, require_sql_admission
from core.sql_observation import ObservationBusy, observe_call
from kvk.dal.new_source_import_dal import SourceBusy
from services.export_proof_progress import AuthorityProofBusy

_parallel = ContextVar("authority_parallel_observation", default=False)


def is_parallel_observation(message):
    # Configuration inspection can reconcile/close a stream. Its name is not a
    # read-only guarantee and it must retain the authoritative dispatcher.
    return is_observation(message) and message["action"] != "inspect_configuration_recovery"


@contextmanager
def parallel_observation():
    token = _parallel.set(True)
    try:
        yield
    finally:
        _parallel.reset(token)


def observation_guard(lock, *, read_only):
    """Only proved reads on the admitted worker may omit the mutation lock."""
    return nullcontext() if read_only and _parallel.get() else lock


class ObservationProgress:
    """One worker, one waiting request, and original transport custody until close.

    This owns no durable result cache, retry, provider or reconciliation action.
    A non-daemon worker stays owned after a caller's drain deadline has elapsed.
    """

    def __init__(self, dispatch, *, report_failure=None, report_connection_failure=None):
        self.dispatch = dispatch
        self.report_failure = report_failure
        self.report_connection_failure = report_connection_failure
        self._condition = Condition()
        self._pending = deque()
        self._active = None
        self._unconfirmed = []
        self._closed = False
        self._thread = None

    def submit(self, message, respond, close):
        if not is_parallel_observation(message):
            return False
        entry = (deepcopy(message), respond, close)
        with self._condition:
            if (
                self._closed
                or custody_snapshot()["unconfirmed"]
                or len(self._pending) + int(self._active is not None) >= 2
            ):
                return False
            if self._thread is None:
                thread = Thread(target=self._run, name="authority-observation", daemon=False)
                self._thread = thread
                try:
                    thread.start()
                except BaseException:
                    # Start can be interrupted after the OS thread exists. Keep
                    # that owner and wake it to exit; no transport transferred.
                    self._closed = True
                    self._condition.notify_all()
                    raise
            self._pending.append(entry)
            self._condition.notify_all()
            return True

    def snapshot(self):
        with self._condition:
            return dict(
                active=int(self._active is not None),
                waiting=len(self._pending),
                unconfirmed=len(self._unconfirmed),
                admission="closed" if self._closed or custody_snapshot()["unconfirmed"] else "open",
            )

    @staticmethod
    def _report(callback, *args):
        if callback is not None:
            try:
                callback(*args)
            except BaseException:
                pass  # Diagnostics cannot strand ownership or change the result.

    def _run(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._pending or self._closed)
                if not self._pending:
                    return
                entry = self._pending.popleft()
                self._active = entry
                cancelled = self._closed
            message, respond, close = entry
            cleanup_unknown = False
            try:
                if cancelled:
                    reply = dict(version=1, error="authority_busy")
                else:
                    try:
                        require_sql_admission()
                        with parallel_observation():
                            result = self.dispatch(message)
                        # A lower layer may present 'unavailable' after swallowing
                        # cleanup failure. Do not turn retained SQL custody into a
                        # successful preview or advertise a free worker.
                        require_sql_admission()
                    except AuthorityProofBusy:
                        reply = dict(version=1, error="authority_busy")
                    except BaseException as error:
                        self._report(self.report_failure, message, error)
                        reply = dict(version=1, error="unresolved_action")
                    else:
                        reply = dict(version=1, result=result)
                respond(reply)
            except BaseException as error:
                self._report(self.report_connection_failure, error)
            finally:
                try:
                    close()
                except BaseException as error:
                    cleanup_unknown = True
                    self._report(self.report_connection_failure, error)
                with self._condition:
                    if cleanup_unknown or custody_snapshot()["unconfirmed"]:
                        self._unconfirmed.append(entry)
                        self._closed = True
                    self._active = None
                    self._condition.notify_all()

    def stop_admission(self):
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def retain_transport(self, owner):
        """Retain a server-owned handle whose close acknowledgement failed."""
        with self._condition:
            self._unconfirmed.append(owner)
            self._closed = True
            self._condition.notify_all()

    def drain(self, *, timeout=30):
        if not 0 <= timeout <= 30:
            raise ValueError("Observation drain must use the existing bounded IPC horizon.")
        self.stop_admission()
        thread = self._thread
        if thread is not None:
            if thread is current_thread():
                return False
            try:
                thread.join(timeout)
            except RuntimeError:
                # An interrupted launch may not yet have acknowledged start.
                # Never infer physical completion from is_alive() in that gap.
                return False
        with self._condition:
            return not (
                (thread is not None and thread.is_alive())
                or self._pending
                or self._active is not None
                or self._unconfirmed
                or custody_snapshot()["unconfirmed"]
            )


def is_observation(message):
    if (
        not isinstance(message, dict)
        or type(message.get("version")) is not int
        or message["version"] != 1
    ):
        return False
    fields = set(message) - {"deployment_hash"}
    action = message.get("action")
    if action in {
        "failed_export_recovery",
        "replacement_recovery",
        "rollover_replacement_recovery",
    }:
        return message.get("operation") == "inspect" and fields == {
            "version",
            "action",
            "operation",
            "job_id",
        }
    if action == "inspect_configuration_recovery":
        return fields == {"version", "action", "preparation_id"}
    if action == "inspect_target_recovery":
        return fields == {"version", "action", "job_id"}
    if action == "evidence_recovery":
        operation = message.get("operation")
        if operation == "inspect":
            return fields == {"version", "action", "operation", "reference"}
        if operation in {"pending", "pending_page"}:
            return fields == {"version", "action", "operation", "after"}
    return False


def dispatch_observation(dispatch, message):
    if not is_observation(message):
        return dispatch(message)
    try:
        return observe_call(dispatch, message)
    except (ObservationBusy, SourceBusy) as error:
        raise AuthorityProofBusy("Recovery observation is waiting for active work.") from error
