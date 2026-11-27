"""Candidate P02 optimistic observation; not yet wired into runtime admission.

The caller owns its cursor, deadline and physical cleanup. This helper acquires
no SQL lock, starts no transaction, changes no session setting and never retries.
Expected module bodies must come from reviewed source, never the live database.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
import json
import re
from typing import TypeVar

from core.sql_connection_custody import require_sql_admission
from core.sql_observation import lock_contention
from kvk.dal.new_source_import_dal import SourceConflict

BOUNDARY_SQL = "EXEC dbo.usp_P02ReadObservationBoundary"
MODULES = frozenset(
    {
        "usp_P02BeginCatalogueMutation",
        "usp_P02EndCatalogueMutation",
        "usp_P02ReadObservationBoundary",
        "tr_P02HeaderObservation",
        "tr_P02KvkWorkObservation",
        "tr_P02MaintenanceObservation",
        "tr_P02CatalogueObservation",
    }
)
_HEADER = re.compile(
    r"\A\s*(?:CREATE(?:\s+OR\s+ALTER)?|ALTER)\s+(PROCEDURE|TRIGGER)\s+",
    re.IGNORECASE,
)
T = TypeVar("T")


class ObservationContractError(SourceConflict):
    """Missing/changed protocol evidence is not ordinary contention."""


class ObservationDeferred(SourceConflict):
    """No current result was admitted; this never authorises business replay."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Catalogue observation deferred: {reason}.")


def _defer_catalogue_lock_timeout(read):
    """Discard a busy catalogue read; never retry here or classify cleanup/work.

    A lock timeout can race the preceding quiet boundary. Only SQL Server's
    native 1222/42000 read failure is eligible. Deadlock victims, permission
    failures, lost transport and comparator failures retain their original path.
    The caller must close/unwind before its existing request can continue.
    """

    @wraps(read)
    def guarded(*args, **kwargs):
        try:
            return read(*args, **kwargs)
        except Exception as error:
            arguments = getattr(error, "args", ())
            if arguments and arguments[0] == "42000" and lock_contention(error):
                raise ObservationDeferred("catalogue_busy") from error
            raise

    return guarded


def canonical_module(definition: str) -> str:
    """Use LF transport and header normalization; retain the entire body.

    Raw source/catalogue bytes must be retained by the caller's proof artifact.
    Unlike legacy outer-trim contracts, trailing whitespace is significant here.
    """
    if not isinstance(definition, str):
        raise ObservationContractError("Protocol module definition is not visible.")
    definition = definition.replace("\r\n", "\n")
    match = _HEADER.match(definition)
    if match is None:
        raise ObservationContractError("Unsupported protocol module header.")
    return match[1].upper() + " " + definition[match.end() :]


def _health(raw: str, expected: Mapping[str, str]) -> None:
    if set(expected) != MODULES:
        raise ObservationContractError("Complete reviewed protocol source is required.")
    try:
        records = json.loads(raw)
    except (TypeError, ValueError) as error:
        raise ObservationContractError("Malformed protocol health evidence.") from error
    if not isinstance(records, list) or len(records) != len(MODULES):
        raise ObservationContractError("Incomplete protocol health evidence.")
    seen = set()
    fields = {
        "name",
        "definition",
        "uses_ansi_nulls",
        "uses_quoted_identifier",
        "execute_as_principal_id",
        "is_disabled",
        "is_not_for_replication",
    }
    for record in records:
        if not isinstance(record, dict) or set(record) != fields:
            raise ObservationContractError("Unexpected protocol health shape.")
        name = record["name"]
        if not isinstance(name, str) or name not in MODULES or name in seen:
            raise ObservationContractError("Unknown or duplicate protocol module.")
        seen.add(name)
        trigger = name.startswith("tr_")
        if (
            record["uses_ansi_nulls"] is not True
            or record["uses_quoted_identifier"] is not True
            or record["execute_as_principal_id"] is not None
            or record["is_disabled"] is not (False if trigger else None)
            or record["is_not_for_replication"] is not (False if trigger else None)
            or canonical_module(record["definition"]) != canonical_module(expected[name])
        ):
            raise ObservationContractError(f"Protocol source/options changed: {name}.")


@dataclass(frozen=True)
class ObservationBoundary:
    identity: tuple
    generation: int


@dataclass(frozen=True)
class CoherentObservation:
    """Point-in-time evidence, with no authority to mutate or to reuse later."""

    value: object
    boundary: ObservationBoundary
    guard: str = "catalogue_generation_v1"


@_defer_catalogue_lock_timeout
def read_boundary(
    cursor, expected_modules: Mapping[str, str], *, installation=None
) -> ObservationBoundary:
    require_sql_admission()
    if installation is not None:
        from services.catalogue_observation_contract import ObservationInstallation

        if type(installation) is not ObservationInstallation:
            raise ObservationContractError("Validated protected observation installation required.")
        installation.require_modules(expected_modules)
    cursor.execute(BOUNDARY_SQL)
    row = cursor.fetchone()
    if row is None or len(row) != 19 or cursor.fetchone() is not None:
        raise ObservationContractError("Exactly one complete observation boundary is required.")
    # Consume completion too: a late driver/SQL failure must not be lost when the
    # caller reuses its cursor for the next metadata batch.
    if cursor.nextset():
        raise ObservationContractError("Unexpected additional observation result.")
    (
        server,
        database,
        database_id,
        principal,
        login,
        session,
        transactions,
        state,
        isolation,
        before,
        absent,
        after,
        object_before,
        created_before,
        modified_before,
        object_after,
        created_after,
        modified_after,
        health,
    ) = row
    if (
        any(not isinstance(v, str) or not v for v in (server, database, principal, login))
        or any(
            type(v) is not int or v <= 0
            for v in (database_id, session, object_before, object_after)
        )
        or type(transactions) is not int
        or transactions not in (0, 1)
        or type(state) is not int
        # A procedure's autocommit statement can be active while explicit
        # user-transaction nesting remains zero (native VM evidence).
        or (transactions, state) not in {(0, 0), (0, 1), (1, 1)}
        or type(isolation) is not int
        or isolation != 2
        or any(type(v) is not int or not 1 <= v < 2**63 - 1 for v in (before, after))
        or type(absent) is not int
        or absent not in (0, 1)
        or any(
            type(v) is not datetime
            for v in (created_before, modified_before, created_after, modified_after)
        )
    ):
        raise ObservationContractError("Invalid native observation state or sequence contract.")
    if (object_before, created_before, modified_before) != (
        object_after,
        created_after,
        modified_after,
    ):
        raise ObservationContractError("Observation sequence identity changed.")
    identity = (
        server,
        database,
        database_id,
        principal,
        login,
        session,
        transactions,
        state,
        isolation,
        object_before,
        created_before,
        modified_before,
    )
    if installation is not None:
        # Check the installed identity even on the first read after a restart,
        # and before classifying an active writer as ordinary contention.
        installation.require_boundary(identity, before)
    if absent == 0:
        raise ObservationDeferred("active_writer")
    if before != after:
        raise ObservationDeferred("generation_changed")
    _health(health, expected_modules)
    return ObservationBoundary(identity, before)


@_defer_catalogue_lock_timeout
def observe_catalogue(
    cursor,
    expected_modules: Mapping[str, str],
    read_metadata: Callable[[Callable[[], None]], T],
    *,
    previous_boundary: ObservationBoundary | None = None,
    installation=None,
) -> CoherentObservation:
    """Bracket a full read; collectors call checkpoint between bounded batches.

    A changed candidate is discarded. The original caller handles its connection
    cleanup exactly as before, including custody after unknown acknowledgement.
    """
    first = read_boundary(cursor, expected_modules, installation=installation)
    if previous_boundary is not None:
        require_same_catalogue(previous_boundary, first)

    def checkpoint():
        current = read_boundary(cursor, expected_modules, installation=installation)
        if current.identity != first.identity:
            raise ObservationContractError("Observation connection/contract identity changed.")
        if current.generation != first.generation:
            raise ObservationDeferred("generation_changed")

    candidate = read_metadata(checkpoint)
    checkpoint()
    return CoherentObservation(candidate, first)


def require_same_catalogue(previous: ObservationBoundary, current: ObservationBoundary) -> None:
    """Permit another validated session, never a different target or incarnation.

    Each read_boundary independently validates transaction/isolation/marker state.
    Session IDs and supported transaction state may differ at actual producer entry.
    """
    if (
        not isinstance(previous, ObservationBoundary)
        or not isinstance(current, ObservationBoundary)
        or len(previous.identity) != 12
        or len(current.identity) != 12
        or previous.identity[:5] + previous.identity[9:]
        != current.identity[:5] + current.identity[9:]
    ):
        raise ObservationContractError("Observation target/principal/sequence identity changed.")
    if previous.generation != current.generation:
        raise ObservationDeferred("generation_changed")
