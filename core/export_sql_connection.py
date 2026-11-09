"""Explicit dedicated SQL credentials for coordinated S11 work.

Legacy workload credentials and Windows/Google identities are unchanged. No
connection or secret read occurs at import time and no fallback is allowed when
dedicated S11 credentials are required.
"""

import os
from pathlib import Path
import re
from threading import Lock

from event_calendar.sql_lifecycle import SqlOutcome, error_facts

_setup_guard = Lock()
_setup_holds: dict[int, SqlOutcome] = {}


class ExportSqlConfigurationError(ValueError):
    """Deliberately excludes secret contents and driver connection strings."""


class ExportSqlSetupAdmissionClosed(ExportSqlConfigurationError):
    """A failed setup still owns its connection; do not admit another attempt."""


def setup_custody_snapshot():
    """Passive process-local counts; never expose handles, targets or driver prose."""
    with _setup_guard:
        return {
            "admission": "closed" if _setup_holds else "open",
            "pending": sum(value.cleanup == "pending" for value in _setup_holds.values()),
            "unconfirmed": sum(value.cleanup == "unconfirmed" for value in _setup_holds.values()),
        }


def _require_setup_admission():
    # Caller holds _setup_guard. Never hold it across driver work.
    if _setup_holds:
        raise ExportSqlSetupAdmissionClosed(
            "S11 SQL setup cleanup is not settled; retain the operation for reconciliation."
        )


def _close_failed_setup(connection, cursor, failure):
    outcome = SqlOutcome(
        effect="not_applicable",
        cleanup="pending",
        error=error_facts(failure),
        retained_connection=connection,
    )
    token = id(outcome)
    with _setup_guard:
        _setup_holds[token] = outcome
    if cursor is not None:
        try:
            cursor.close()
        except BaseException as error:
            outcome.cleanup_error = error_facts(error)
    try:
        # Setup has not handed out the connection or executed business work.
        # Driver close owns any transaction created by the autocommit switch.
        connection.close()
    except BaseException as error:
        with _setup_guard:
            outcome.cleanup = "unconfirmed"
            outcome.cleanup_error = error_facts(error)
    else:
        with _setup_guard:
            outcome.cleanup = "settled"
            outcome.retained_connection = None
            del _setup_holds[token]
    return outcome


def _load_environment():
    from dotenv import load_dotenv

    from core.export_execution_host import assert_protected_path

    path = Path(__file__).resolve().parents[1] / ".env"
    if path.exists():
        path = assert_protected_path(path, private=True, allow_current_identity=True)
    load_dotenv(path, override=False)


def settings(*, server=None, database=None, principal=None):
    """Load dedicated SQL credentials from the existing application .env.

    Existing process environment takes precedence. Missing dedicated values never
    select legacy SQL or Windows credentials. Headroom uses the established import percentage policy.
    """
    try:
        _load_environment()
        value = dict(
            version=1,
            server=os.environ["SQL_SERVER"],
            database=os.environ["SQL_DATABASE"],
            username=os.environ["S11_SQL_USERNAME"],
            password=os.environ["S11_SQL_PASSWORD"],
        )
        if value["database"] != "ROK_TRACKER":
            raise ValueError()
        for key in ("server", "database", "username"):
            if not re.fullmatch(r"[A-Za-z0-9_\\.@-]{1,128}", value[key]):
                raise ValueError()
        if not re.fullmatch(r"S11_ExportApplication(?:_[A-Za-z0-9_]+)?", value["username"]):
            raise ValueError()
        if not 1 <= len(value["password"]) <= 1024 or "\x00" in value["password"]:
            raise ValueError()
        for expected, key in ((server, "server"), (database, "database"), (principal, "username")):
            if expected is not None and value[key] != expected:
                raise ValueError()
    except Exception:
        raise ExportSqlConfigurationError(
            "Dedicated S11 SQL environment target or credentials are invalid."
        ) from None
    return value


def connect(*, server, database, principal=None):
    import pyodbc

    value = settings(server=server, database=database, principal=principal)
    # ODBC brace quoting preserves semicolons/braces in a password as data.
    quote = lambda text: "{" + text.replace("}", "}}") + "}"
    target = (
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER="
        + quote(value["server"])
        + ";DATABASE="
        + quote(value["database"])
        + ";UID="
        + quote(value["username"])
        + ";PWD="
        + quote(value["password"])
        + ";Encrypt=yes;TrustServerCertificate=no;"
    )
    connection = None
    cursor = None
    with _setup_guard:
        _require_setup_admission()
    try:
        connection = pyodbc.connect(target, autocommit=True, timeout=5)
        connection.timeout = 15
        cursor = connection.cursor()
        cursor.execute("SET LOCK_TIMEOUT 1000")
        closing, cursor = cursor, None
        closing.close()
        connection.autocommit = False
        with _setup_guard:
            # A peer may have failed while this already-admitted setup ran.
            _require_setup_admission()
            return connection
    except BaseException as failure:
        outcome = None
        if connection is not None:
            outcome = _close_failed_setup(connection, cursor, failure)
        if not isinstance(failure, Exception):
            raise
        if outcome is not None and outcome.cleanup != "settled":
            raise ExportSqlSetupAdmissionClosed(
                "S11 SQL setup cleanup is unconfirmed; retain the operation for reconciliation."
            ) from None
        if isinstance(failure, ExportSqlSetupAdmissionClosed):
            raise failure from None
        raise ExportSqlConfigurationError(
            "S11 SQL connection failed; retain the operation for reconciliation."
        ) from None


def producer_connection_factory(legacy_factory):
    """Select once before attempting connections, including any bounded retries.

    A failed attempt must not select a different credential profile if the runtime
    context changes. Returning the callable also avoids reusing the guard connection.
    """
    from services.legacy_export_snapshot_service import has_runtime_context, require_runtime

    if has_runtime_context():
        return require_runtime().dal.connect
    return legacy_factory


def producer_connection(legacy_factory):
    """Use the admitted runtime's factory; never reuse its guard connection."""
    return producer_connection_factory(legacy_factory)()
