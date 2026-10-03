from types import SimpleNamespace

import pytest

from core import export_sql_connection as connection
from scripts.prepare_s11_sql_account import render
from services.export_sql_health_dal import verify_headroom


def configuration():
    return dict(
        version=1,
        server="mini_AMD",
        database="ROK_TRACKER",
        username="S11_ExportApplication",
        password="synthetic;secret}value",
        headroom=dict(min_free_bytes=100, max_used_percent=85),
    )


@pytest.fixture
def protected_settings(monkeypatch):
    monkeypatch.setattr(connection, "_load_environment", lambda: None)
    for key, value in {
        "SQL_SERVER": "mini_AMD",
        "SQL_DATABASE": "ROK_TRACKER",
        "S11_SQL_USERNAME": "S11_ExportApplication",
        "S11_SQL_PASSWORD": "synthetic;secret}value",
        "S11_SQL_MIN_FREE_LOG_BYTES": "100",
        "S11_SQL_MAX_LOG_USED_PERCENT": "85",
    }.items():
        monkeypatch.setenv(key, value)
    return monkeypatch


@pytest.mark.parametrize(
    "key,value",
    [
        ("SQL_SERVER", "mini_AMD;UID=other"),
        ("SQL_DATABASE", "master"),
        ("S11_SQL_USERNAME", "SHEETS_USER"),
        ("S11_SQL_PASSWORD", ""),
        ("S11_SQL_MIN_FREE_LOG_BYTES", "0"),
        ("S11_SQL_MIN_FREE_LOG_BYTES", "1.5"),
        ("S11_SQL_MAX_LOG_USED_PERCENT", "nan"),
        ("S11_SQL_MAX_LOG_USED_PERCENT", "100"),
    ],
)
def test_invalid_configuration_fails_without_secret(protected_settings, key, value):
    protected_settings.setenv(key, value)
    with pytest.raises(connection.ExportSqlConfigurationError) as error:
        connection.settings()
    assert "synthetic" not in str(error.value)


def test_target_and_principal_match_required(protected_settings):
    assert (
        connection.settings(
            server="mini_AMD", database="ROK_TRACKER", principal="S11_ExportApplication"
        )["username"]
        == "S11_ExportApplication"
    )
    with pytest.raises(connection.ExportSqlConfigurationError):
        connection.settings(principal="SHEETS_USER")


@pytest.mark.parametrize(
    "key",
    [
        "S11_SQL_USERNAME",
        "S11_SQL_PASSWORD",
        "S11_SQL_MIN_FREE_LOG_BYTES",
        "S11_SQL_MAX_LOG_USED_PERCENT",
    ],
)
def test_missing_dedicated_environment_never_falls_back(protected_settings, key):
    protected_settings.delenv(key, raising=False)
    protected_settings.setenv("SQL_USERNAME", "SHEETS_USER")
    protected_settings.setenv("SQL_PASSWORD", "legacy-synthetic")
    with pytest.raises(connection.ExportSqlConfigurationError):
        connection.settings()


def test_odbc_password_quoted_and_connection_timeouts(protected_settings, monkeypatch):
    calls = []
    cursor = SimpleNamespace(execute=lambda sql: calls.append(sql), close=lambda: None)
    session = SimpleNamespace(cursor=lambda: cursor, autocommit=True, close=lambda: None)
    import pyodbc

    import services.export_sql_health_dal

    monkeypatch.setattr(
        pyodbc, "connect", lambda target, **kw: (calls.append((target, kw)) or session)
    )
    monkeypatch.setattr(
        services.export_sql_health_dal, "verify_headroom", lambda cur, cfg: calls.append("healthy")
    )
    assert connection.connect(server="mini_AMD", database="ROK_TRACKER") is session
    assert "PWD={synthetic;secret}}value};Encrypt=yes;TrustServerCertificate=no;" in calls[0][0]
    assert calls[0][1] == dict(autocommit=True, timeout=5)
    assert session.timeout == 15 and session.autocommit is False
    assert calls[1:] == ["SET LOCK_TIMEOUT 1000"]


def test_connection_exception_is_sanitized(protected_settings, monkeypatch):
    import pyodbc

    def failed(*args, **kwargs):
        raise RuntimeError(configuration()["password"])

    monkeypatch.setattr(pyodbc, "connect", failed)
    with pytest.raises(connection.ExportSqlConfigurationError) as error:
        connection.connect(server="mini_AMD", database="ROK_TRACKER")
    assert "synthetic" not in str(error.value) and error.value.__suppress_context__


@pytest.mark.parametrize("active", [True, False])
def test_coordinated_connection_does_not_use_legacy_credentials(monkeypatch, active):
    import services.legacy_export_snapshot_service as legacy

    dedicated = object()
    old = object()
    used = []
    monkeypatch.setattr(legacy, "has_runtime_context", lambda: active)
    monkeypatch.setattr(
        legacy,
        "require_runtime",
        lambda: SimpleNamespace(dal=SimpleNamespace(connect=lambda: dedicated)),
    )
    result = connection.producer_connection(lambda: used.append(True) or old)
    assert result is (dedicated if active else old)
    assert used == ([] if active else [True])


@pytest.mark.parametrize(
    "row",
    [
        None,
        ("ROK_TRACKER", "SHEETS_USER", 1000, 10, "FULL", "NOTHING"),
        ("ROK_TRACKER", "S11_ExportApplication", 1000, 950, "FULL", "NOTHING"),
        ("ROK_TRACKER", "S11_ExportApplication", 1000, 10, "FULL", "AVAILABILITY_REPLICA"),
        ("ROK_TRACKER", "S11_ExportApplication", None, 10, "FULL", "NOTHING"),
    ],
)
def test_headroom_rejects_unknown_pressure_or_wrong_identity(row):
    from kvk.dal.new_source_import_dal import SourceConflict

    values = iter([row, None])
    cursor = SimpleNamespace(execute=lambda q: None, fetchone=lambda: next(values))
    with pytest.raises(SourceConflict):
        verify_headroom(cursor, configuration())


@pytest.mark.parametrize("reuse", ["NOTHING", "ACTIVE_TRANSACTION", "LOG_BACKUP"])
def test_headroom_reads_only_one_target_and_reports_free_bytes(reuse):
    values = iter([("ROK_TRACKER", "S11_ExportApplication", 1000, 100, "FULL", reuse), None])
    queries = []
    cursor = SimpleNamespace(execute=queries.append, fetchone=lambda: next(values))
    assert verify_headroom(cursor, configuration())["free_bytes"] == 900
    assert len(queries) == 1 and "DBCC" not in queries[0] and "EXEC" not in queries[0]


def test_grants_are_exact_and_bound_to_actual_login_sid():
    plan = dict(version=1, grants=[dict(object="KVK.KVK_AllPlayers_Stage", permission="INSERT")])
    sql = render(
        plan,
        server="mini_AMD",
        database="ROK_TRACKER",
        principal="S11_ExportApplication",
        login_sid="0x" + "12" * 16,
    )
    assert "GRANT INSERT ON OBJECT::[KVK].[KVK_AllPlayers_Stage]" in sql
    assert "S11 login SID mismatch" in sql and "Existing user is not adopted" in sql
    assert "g.class=100 AND g.major_id=0" in sql
    assert "g.permission_name=N'CONNECT SQL' AND g.state=N'G'" in sql
    assert "GRANT ALTER" not in sql and "WITH GRANT OPTION" not in sql


@pytest.mark.parametrize(
    "grant",
    [
        dict(object="dbo.ExportJob;DROP TABLE X", permission="SELECT"),
        dict(object="dbo.ExportJob", permission="CONTROL"),
        dict(object="dbo.ExportJob", permission="SELECT", column="x] DROP"),
    ],
)
def test_grant_renderer_rejects_broader_effects(grant):
    with pytest.raises(ValueError):
        render(
            dict(version=1, grants=[grant]),
            server="mini_AMD",
            database="ROK_TRACKER",
            principal="S11_ExportApplication",
            login_sid="0x" + "12" * 16,
        )


def test_application_authority_cannot_fall_back_when_credentials_missing(
    protected_settings, monkeypatch
):
    import pyodbc

    from scripts.run_export_authority import connection_factory

    used = []
    monkeypatch.setattr(pyodbc, "connect", lambda *a, **k: used.append(True))
    protected_settings.delenv("S11_SQL_PASSWORD")
    with pytest.raises(connection.ExportSqlConfigurationError):
        connection_factory(
            dict(
                sql_server="mini_AMD",
                sql_database="ROK_TRACKER",
                sql_contract=dict(profile="application", principal="S11_ExportApplication"),
            )
        )
    assert used == []


def test_login_template_creates_disabled_login_and_never_adopts_existing_account():
    from scripts.prepare_s11_sql_account import render_login

    sql = render_login(server="mini_AMD", principal="S11_ExportApplication")
    assert "Existing login is not adopted" in sql
    assert "ALTER LOGIN [S11_ExportApplication] DISABLE" in sql
    assert "CHECK_POLICY=ON" in sql
    assert "REPLACE_IN_PRIVATE_SSMS" in sql
    assert "ALTER LOGIN sa" not in sql and "GRANT" not in sql


@pytest.mark.parametrize("profile", ["reader", "application"])
def test_bot_startup_connection_respects_reviewed_profile(monkeypatch, profile):
    from unittest.mock import Mock

    import bot_config
    import file_utils
    from kvk.dal.new_source_admin_dal import configured_connection

    monkeypatch.setattr(bot_config, "EXPORT_COORDINATION_ENABLED", True)
    dedicated = Mock(return_value=Mock())
    legacy = Mock(return_value=Mock())
    monkeypatch.setattr(connection, "connect", dedicated)
    monkeypatch.setattr(file_utils, "get_conn_with_retries", legacy)
    actual = configured_connection(sql_profile=profile)
    if profile == "reader":
        assert actual is legacy.return_value
        legacy.assert_called_once_with(operational=True)
        dedicated.assert_not_called()
    else:
        assert actual is dedicated.return_value
        dedicated.assert_called_once()
        legacy.assert_not_called()


def test_private_controls_reuse_admitted_profile_factory(monkeypatch):
    from unittest.mock import Mock

    import bot_config
    from kvk.dal.new_source_admin_dal import configured_connection
    from services import export_runtime_composition as runtime

    factory = Mock(return_value=object())
    monkeypatch.setattr(bot_config, "EXPORT_COORDINATION_ENABLED", True)
    monkeypatch.setattr(runtime, "configured_runtime", lambda: SimpleNamespace(connect=factory))
    assert configured_connection() is factory.return_value
    factory.assert_called_once_with()
