"""Offline regression coverage for the native-diagnosed catalog and cleanup failures."""

import hashlib
import json
from unittest.mock import Mock

import pytest

from core.sql_connection_custody import SqlCleanupUnknown, connection_retained
from scripts.verify_k98_running_release import (
    ObservationConnections,
    VerificationBudgetExceeded,
    failure_result,
)
from services import export_execution_dal as catalog
from services.application_maintenance_contract import RESOURCE
from services.application_maintenance_dal import (
    SCHEMA_ACQUIRE_SQL,
    SCHEMA_RELEASE_SQL,
    SchemaObservationRefused,
    schema_observation,
)


@pytest.mark.parametrize(
    "group,name,expected",
    [
        ("metadata", "columns", "f420c154cd7d995fec02dd93c06d860430ccdcef38a2e10fa6618e8b96145dfe"),
        (
            "metadata",
            "foreign_keys",
            "e4486e1a17e218425e0fad6dfd33a905c15a50a0559a15d0910fa8d5cb47288e",
        ),
        (
            "identity",
            "foreign_keys",
            "dcc50e40d0a63ed7184e86ec52ece2a3b1fec6fdb84db86aced1fcd33b715796",
        ),
        (
            "identity",
            "key_constraints",
            "25183278198fe360a0e66e35d710d88267d38f8db6329f4fd1cd31ac8d3518d4",
        ),
    ],
)
def test_sql_is_exactly_the_native_observed_candidate(group, name, expected):
    queries = (
        catalog._APPLICATION_SCOPED_METADATA
        if group == "metadata"
        else catalog._APPLICATION_IDENTITY_QUERIES
    )
    sql = queries[name].replace("@scope", "?")
    assert hashlib.sha256(sql.encode()).hexdigest() == expected


@pytest.mark.parametrize("scope", [None, [], ["dbo.example", "dbo.example", "dbo.missing"]])
def test_application_dispatch_keeps_scope_parameterized_and_unscoped_queries_original(scope):
    cursor = Mock()
    cursor.description = [("ViewDefinition",)]
    cursor.fetchone.return_value = (1,)
    cursor.fetchall.return_value = []
    catalog.application_installation_snapshot(cursor, scope=scope)
    calls = cursor.execute.call_args_list
    for ordinal, (name, original) in enumerate(catalog._METADATA_QUERIES.items(), start=1):
        sql, *parameters = calls[ordinal].args
        if scope is not None and name in catalog._APPLICATION_SCOPED_METADATA:
            assert sql == catalog._APPLICATION_SCOPED_METADATA[name].replace("@scope", "?")
            assert parameters == [json.dumps(scope)]
        else:
            assert sql.endswith(original)
    # These legacy templates remain shared with export installation reads.
    assert "FROM required)" in catalog._METADATA_QUERIES["foreign_keys"]
    assert "OBJECT_SCHEMA_NAME(c.object_id)" in catalog._METADATA_QUERIES["columns"]


class DriverError(Exception):
    pass


class RawCursor:
    def __init__(self, state):
        self.state = state
        self.sql = None

    def execute(self, sql, *parameters):
        self.sql = sql
        self.state["calls"].append((sql, parameters))
        if sql == SCHEMA_RELEASE_SQL and self.state.get("release_execute_error"):
            raise DriverError("HYT00", "secret driver value (0)")
        if sql == "SELECT fixture" and self.state.get("query_error"):
            raise DriverError("HYT00", "secret SQL credentials (0)")

    def fetchone(self):
        if "dm_exec_sessions" in self.sql:
            return self.state.get("preconditions", ("NoLock", "NoLock", 2))
        if self.sql == SCHEMA_ACQUIRE_SQL:
            if self.state.get("acquire_late"):
                self.state["now"] = 46
            if self.state.get("acquire_error"):
                raise DriverError("08S01", "secret acknowledgement (10054)")
            return (self.state.get("acquire_result", 0),)
        if self.sql == SCHEMA_RELEASE_SQL:
            if self.state.get("release_fetch_error"):
                raise DriverError("08S01", "secret release (10054)")
            return self.state.get("release_result", (0, "NoLock"))
        self.state["now"] += self.state.get("fetch_seconds", 0)
        return (1,)

    def close(self):
        pass


def observation(**options):
    state = dict(now=0, calls=[], **options)
    raw = Mock()
    raw.cursor.side_effect = lambda: RawCursor(state)
    owner = ObservationConnections(lambda: raw, clock=lambda: state["now"])
    return owner, state, raw


@pytest.mark.parametrize("expiry", ["deadline", "statements", "fetch", "acquire_late"])
def test_expiry_refuses_acceptance_but_releases_acknowledged_schema_once(expiry):
    owner, state, raw = observation(acquire_late=expiry == "acquire_late")
    with pytest.raises(VerificationBudgetExceeded) as caught, owner:
        connection = owner()
        cursor = connection.cursor()
        with schema_observation(cursor):
            if expiry == "deadline":
                state["now"] = 46
            elif expiry == "statements":
                owner.statements = 256
            elif expiry == "fetch":
                state["fetch_seconds"] = 46
            cursor.execute("SELECT fixture")
            cursor.fetchone()
    releases = [c for c in state["calls"] if c[0] == SCHEMA_RELEASE_SQL]
    assert releases == [(SCHEMA_RELEASE_SQL, (RESOURCE, RESOURCE))]
    assert not connection_retained(connection)
    assert raw.close.call_count == 1
    assert failure_result(caught.value)[1]["verified"] is False
    with pytest.raises(ValueError, match="repeated"):
        cursor.release_schema_observation(RESOURCE)
    assert len([c for c in state["calls"] if c[0] == SCHEMA_RELEASE_SQL]) == 1


@pytest.mark.parametrize(
    "fault", ["release_execute_error", "release_fetch_error", "release_result"]
)
def test_unknown_release_preserves_first_failure_and_never_retries_or_accepts(fault):
    options = {fault: (1, "Exclusive") if fault == "release_result" else True}
    owner, state, raw = observation(query_error=True, **options)
    with pytest.raises(SqlCleanupUnknown) as caught, owner:
        connection = owner()
        cursor = connection.cursor()
        with schema_observation(cursor):
            cursor.execute("SELECT fixture")
    assert connection_retained(connection)
    assert raw.close.call_count == 0
    code, record = failure_result(caught.value)
    assert code == 1 and record["verified"] is False
    assert record["sql_observation"]["first_failure"]["sqlstate"] == "HYT00"
    assert "secret" not in json.dumps(record)
    assert len([c for c in state["calls"] if c[0] == SCHEMA_RELEASE_SQL]) == 1


@pytest.mark.parametrize("result", [-1, -2, -3, -999, 99])
def test_unowned_or_unknown_acquisition_cannot_dispatch_release(result):
    owner, state, raw = observation(acquire_result=result)
    expected = SqlCleanupUnknown if result == 99 else SchemaObservationRefused
    with pytest.raises(expected), owner:
        connection = owner()
        cursor = connection.cursor()
        with schema_observation(cursor):
            pytest.fail("Refused or unknown ownership must not admit reads")
    assert not any(c[0] == SCHEMA_RELEASE_SQL for c in state["calls"])
    with pytest.raises(ValueError):
        cursor.release_schema_observation(RESOURCE)


def test_lost_acquisition_acknowledgement_never_guesses_cleanup():
    owner, state, raw = observation(acquire_error=True)
    with pytest.raises(SqlCleanupUnknown), owner:
        connection = owner()
        with schema_observation(connection.cursor()):
            pytest.fail("Unknown acquisition cannot admit reads")
    assert connection_retained(connection) and raw.close.call_count == 0
    assert not any(c[0] == SCHEMA_RELEASE_SQL for c in state["calls"])


def test_safe_diagnostics_record_exact_query_and_fetch_stage_without_values():
    owner, state, raw = observation(query_error=True)
    with pytest.raises(DriverError) as caught, owner:
        connection = owner()
        owner.observation_phase("application")
        with schema_observation(connection.cursor()):
            connection.cursor().execute("SELECT fixture", "secret parameter")
    _, record = failure_result(caught.value)
    first = record["sql_observation"]["first_failure"]
    assert first == dict(
        phase="application",
        operation="execute",
        error_type="DriverError",
        sqlstate="HYT00",
        native_code=0,
        ordinal=4,
        sql_sha256=hashlib.sha256(b"SELECT fixture").hexdigest(),
    )
    assert "secret" not in json.dumps(record)
    assert raw.close.call_count == 1


@pytest.mark.parametrize("fault", [None, "metadata_drift", "late_catalog", "busy"])
def test_complete_contract_readers_and_comparators_share_bounded_owner(monkeypatch, fault):
    """Exercise every real reader/comparator, including the locked lifecycle read.

    Only driver rows/time are modeled. This does not substitute for native SQL
    result equivalence or certify the cost of taking the schema lock on the host.
    """
    from collections import deque

    from scripts.verify_k98_update_pair import verify_bot_sql_contracts
    from tests.test_application_maintenance_contract import defer, opt_in, sample
    from tests.test_recovery_release_seed import evidence

    bot, _, collected = evidence(monkeypatch)
    application, approved, outputs = sample.__wrapped__(monkeypatch)
    defer(application)
    opt_in(application, approved, outputs)
    bot["application_sql_contract"] = approved
    if fault == "metadata_drift":
        application["metadata"]["columns"][0]["Nullable"] = True
    installed = collected["installation"]
    legacy = collected["legacy"]
    answers = {
        "export": deque(
            [[installed["target"]], installed["migrations"]]
            + [installed["metadata"][name] for name in catalog._METADATA_QUERIES]
            + [installed["permissions"]]
        ),
        "legacy": deque(
            legacy[name]
            for name in catalog.legacy_permission_queries(bot["legacy_sql_contract"]["source"])
        ),
        "application": deque(
            [[application["target"]]]
            + [application["metadata"][name] for name in catalog._METADATA_QUERIES]
            + [
                application["metadata"][name]
                for name in ("table_types", "dependencies", "synonyms", "database_triggers")
            ]
            + [
                application[name]
                for name in ("schema_permissions", "object_permissions", "column_permissions")
            ]
            + [
                application["schema_identity"][name]
                for name in catalog._APPLICATION_IDENTITY_QUERIES
            ]
            + [outputs]
        ),
    }
    state = dict(now=0, calls=[], acquire_result=-1 if fault == "busy" else 0)
    raw_connections = []

    class CatalogCursor(RawCursor):
        def execute(self, sql, *parameters):
            super().execute(sql, *parameters)
            if (
                sql == "SET LOCK_TIMEOUT 0"
                or sql in (SCHEMA_ACQUIRE_SQL, SCHEMA_RELEASE_SQL)
                or "dm_exec_sessions" in sql
            ):
                return
            self.result = deque(answers[owner.phase].popleft())
            self.description = [(key,) for key in self.result[0]] if self.result else []
            if (
                fault == "late_catalog"
                and owner.phase == "application"
                and "FROM sys.columns c" in sql
            ):
                state["now"] = 46
            else:
                state["now"] += 0.1

        def fetchone(self):
            if (
                self.sql in (SCHEMA_ACQUIRE_SQL, SCHEMA_RELEASE_SQL)
                or "dm_exec_sessions" in self.sql
            ):
                return super().fetchone()
            return tuple(self.result.popleft().values()) if self.result else None

        def fetchall(self):
            result = [tuple(row.values()) for row in self.result]
            self.result.clear()
            return result

    def connect():
        raw = Mock()
        raw.cursor.side_effect = lambda: CatalogCursor(state)
        raw_connections.append(raw)
        return raw

    owner = ObservationConnections(connect, clock=lambda: state["now"])
    if fault:
        with pytest.raises(Exception) as caught, owner:
            verify_bot_sql_contracts(bot, connection_factory=owner)
        _, result = failure_result(caught.value)
        assert result["verified"] is False
        assert result["sql_observation"]["first_failure"]["phase"] == "application"
    else:
        with owner:
            result = verify_bot_sql_contracts(bot, connection_factory=owner)
        assert result["application"] == application
        assert not any(answers.values())
        assert {row["phase"] for row in owner.observations} == {"export", "legacy", "application"}
    assert all(raw.close.call_count == 1 for raw in raw_connections)
    releases = [c for c in state["calls"] if c[0] == SCHEMA_RELEASE_SQL]
    assert len(releases) == (0 if fault == "busy" else 1)
