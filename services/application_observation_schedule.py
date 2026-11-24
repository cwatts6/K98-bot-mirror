"""Finite read continuation inside an existing startup or producer owner.

This owns no thread, SQL connection, business lock or durable claim. Callbacks
must finish physical cleanup before raising a deferred result. A successful
producer callback may return its existing live admission owner. Only an explicit
coherence deferral can schedule another read; business work is never replayed.
"""

from contextlib import contextmanager
from threading import Condition, get_ident
import time

from core.sql_connection_custody import require_sql_admission
from services.catalogue_observation_dal import ObservationDeferred


class ObservationLane:
    """Bound read scheduling only; SQL claims and proof validity remain independent."""

    def __init__(self):
        self._condition = Condition()
        self._active = None
        self._waiting = None

    @contextmanager
    def enter(self, request, *, wait=True):
        ticket = (object(), get_ident())
        with self._condition:
            request.check()
            if self._waiting is not None:
                raise ObservationDeferred("observation_pending")
            if self._active is not None:
                if not wait or self._waiting is not None or self._active[1] == get_ident():
                    raise ObservationDeferred("observation_pending")
                self._waiting = ticket
                try:
                    while self._active is not None:
                        request.check()
                        self._condition.wait(timeout=max(0.0, request.deadline - request.clock()))
                    request.check()
                finally:
                    self._waiting = None
            self._active = ticket
        try:
            yield
        finally:
            with self._condition:
                self._active = None
                self._condition.notify_all()


# The protected Bot has one runtime per process. Independent tools/processes
# retain independent lanes and rely on SQL generation checks for correctness.
observation_lane = ObservationLane()


class ObservationRequest:
    """One logical request, including any bounded continuation and later reuse."""

    def __init__(self, *, clock=None, wait=None, deadline=None):
        self.clock = clock or time.monotonic
        self.wait = wait or time.sleep
        self.deadline = self.clock() + 45.0
        if deadline is not None:
            self.deadline = min(self.deadline, deadline)
        self.statements = 0
        self.collections = 0
        self.boundary_checks = 0
        self._collection_deadline = None
        self._started = False

    def check(self):
        require_sql_admission()
        now = self.clock()
        if now >= self.deadline or (
            self._collection_deadline is not None and now >= self._collection_deadline
        ):
            raise ObservationDeferred("observation_deadline")

    @contextmanager
    def collection(self):
        self.check()
        if self._collection_deadline is not None or self.collections >= 2:
            raise ObservationDeferred("observation_limit")
        self.collections += 1
        self._collection_deadline = min(self.deadline, self.clock() + 15.0)
        try:
            yield
            self.check()
        finally:
            self._collection_deadline = None

    def cursor(self, cursor):
        if isinstance(cursor, _ReadCursor):
            if cursor.request is not self:
                raise ValueError("Observation cursor belongs to another request.")
            return cursor
        return _ReadCursor(self, cursor)

    def run(self, collect, probe):
        """One initial read and one continuation after an acknowledged quiet check.

        Existing caller/producer admission coalesces nested requests. This finite
        continuation does not add a worker queue or share proof between claims.
        No connection may remain open from a deferred callback during wait().
        """
        if self._started:
            raise ValueError("An observation request cannot be restarted.")
        self._started = True
        with observation_lane.enter(self):
            return self._run(collect, probe)

    def _run(self, collect, probe):
        self.check()
        try:
            return collect()
        except ObservationDeferred as error:
            if error.reason not in {"active_writer", "generation_changed", "catalogue_busy"}:
                raise
            first = error
        for attempt in range(3):
            self.check()
            now = self.clock()
            # Keep the first cheap check prompt. Spread the remaining two over
            # the existing deadline, reserving a full collection interval when
            # possible. Three one-second checks would abandon ordinary longer
            # writers while most of the same request budget remained unused.
            delay = 1.0 if attempt == 0 else max(1.0, (self.deadline - 15.0 - now) / (3 - attempt))
            if self.deadline - now <= delay:
                raise ObservationDeferred("observation_deadline") from first
            self.wait(delay)
            self.check()
            self.boundary_checks += 1
            try:
                probe()
            except ObservationDeferred as error:
                if error.reason not in {"active_writer", "generation_changed", "catalogue_busy"}:
                    raise
                continue
            self.check()
            return collect()
        raise first


class _ReadCursor:
    """Budget only read dispatch/consumption; the real owner performs cleanup."""

    def __init__(self, request, cursor):
        self.request, self.raw = request, cursor

    @property
    def connection(self):
        return self.raw.connection

    @property
    def description(self):
        return self.raw.description

    def execute(self, *args):
        self.request.check()
        if self.request.statements >= 256:
            raise ObservationDeferred("statement_limit")
        self.request.statements += 1
        self.raw.execute(*args)
        self.request.check()
        return self

    def _read(self, method):
        self.request.check()
        result = getattr(self.raw, method)()
        self.request.check()
        return result

    def fetchone(self):
        return self._read("fetchone")

    def fetchall(self):
        return self._read("fetchall")

    def nextset(self):
        return self._read("nextset")


def observe_application(connect, approved, *, request=None, after_read=None):
    """Complete successor comparison on owned connections, closing before waits.

    Startup and sealed verification share this path. The supplied factory may
    impose a tighter all-contract budget; it remains the same factory on every
    attempt. No borrowed business connection or predecessor fallback is used.
    """
    from services.catalogue_observation_dal import (
        CoherentObservation,
        ObservationContractError,
        read_boundary,
    )
    from services.export_observer_contract import observation_installation
    from services.export_runtime_composition import (
        application_contract_scope,
        application_snapshot_for_contract,
        verify_application_installation_contract,
    )

    application_contract_scope(approved)  # Full protected source validation before connecting.
    installation = observation_installation(approved)
    request = request or ObservationRequest()

    def collect():
        def compare(cursor):
            with request.collection():
                result = application_snapshot_for_contract(cursor, approved)
                if type(result) is not CoherentObservation:
                    raise ObservationContractError("Complete coherent observation required.")
                verify_application_installation_contract(result.value, approved, observation=result)
                if after_read is not None:
                    after_read(cursor)
                return result

        return read_owned_observation(connect, compare, request=request)

    def probe():
        return read_owned_observation(
            connect,
            lambda cursor: read_boundary(
                cursor, dict(installation.modules), installation=installation
            ),
            request=request,
        )

    result = request.run(collect, probe)
    request.check()
    return result


def read_owned_observation(connect, read, *, request=None):
    """Own an autocommit observer through acknowledged cursor/connection close."""
    from types import SimpleNamespace

    from core.sql_connection_custody import (
        SqlCleanupUnknown,
        connection_retained,
        preserve_failure,
        retain_connection,
        retain_connection_resource,
    )

    require_sql_admission()
    if request is not None:
        request.check()
    connection = connect()
    cursor = None
    failure = None
    result = None
    try:
        connection.autocommit = True
        cursor = connection.cursor()
        result = read(request.cursor(cursor) if request is not None else cursor)
    except BaseException as error:
        failure = error
    finally:
        if retain_connection_resource(connection, cursor):
            raise SqlCleanupUnknown("Observation connection remains retained.") from failure
        try:
            if cursor is not None:
                cursor.close()
            if not connection_retained(connection):
                connection.close()
        except BaseException as cleanup:
            failure = preserve_failure(failure, cleanup, "observation_close")
            retain_connection(
                SimpleNamespace(connection=connection, cursor=cursor),
                effect="not_applicable",
                first_failure=failure,
                cleanup_error=cleanup,
            )
            raise SqlCleanupUnknown("Observation cleanup is unconfirmed.") from failure
    if failure is not None:
        raise failure
    return result
