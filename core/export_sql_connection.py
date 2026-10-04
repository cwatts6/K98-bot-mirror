"""Explicit dedicated SQL credentials for coordinated S11 work.

Legacy workload credentials and Windows/Google identities are unchanged. No
connection or secret read occurs at import time and no fallback is allowed when
dedicated S11 credentials are required.
"""

import os
from pathlib import Path
import re

from core.sql_log_policy import DEFAULT_ABORT_THRESHOLD, DEFAULT_WARN_THRESHOLD


class ExportSqlConfigurationError(ValueError):
    """Deliberately excludes secret contents and driver connection strings."""


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
            headroom=dict(
                warn_used_percent=DEFAULT_WARN_THRESHOLD,
                max_used_percent=DEFAULT_ABORT_THRESHOLD,
            ),
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
    try:
        connection = pyodbc.connect(target, autocommit=True, timeout=5)
        connection.timeout = 15
        cursor = connection.cursor()
        try:
            cursor.execute("SET LOCK_TIMEOUT 1000")
        finally:
            cursor.close()
        connection.autocommit = False
        return connection
    except Exception:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        raise ExportSqlConfigurationError(
            "S11 SQL connection failed; retain the operation for reconciliation."
        ) from None


def producer_connection(legacy_factory):
    """Use the admitted runtime's factory; never reuse its guard connection."""
    from services.legacy_export_snapshot_service import has_runtime_context, require_runtime

    if has_runtime_context():
        return require_runtime().dal.connect()
    return legacy_factory()
