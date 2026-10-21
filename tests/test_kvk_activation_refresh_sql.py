"""Opt-in tests for the exact operator-approved local activation fixture.

Schema installation is separate. No production connection or default execution.
"""

from dataclasses import replace
from datetime import UTC, datetime
import os
from pathlib import Path
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, one, transaction
from kvk.dal.source_admin_review_dal import SourceAdminReviewDAL
from kvk.services.source_admin_review_service import SourceAdminReviewService
from tests.test_kvk_source_admin import ACCESS, ADMIN

SERVER = r"localhost\K98DEV"
DATABASE = "K98_ReaderActivation_Disposable_20261014"
TARGET = SERVER + "|" + DATABASE


def connect(*, autocommit=False, restricted=False):
    import pyodbc

    # Impersonated fixture sessions must never return to a shared ODBC pool.
    pyodbc.pooling = False
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:"
        + SERVER
        + ";DATABASE="
        + DATABASE
        + ";Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=autocommit,
        timeout=10,
    )
    actual = connection.execute(
        "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()"
    ).fetchone()
    if tuple(actual) != (r"9SX2VF4\K98DEV", DATABASE):
        connection.close()
        raise AssertionError("Disposable target differs from authorization")
    if not autocommit:
        connection.rollback()
    if restricted:
        connection.execute("EXECUTE AS USER=N'ReaderHistoryFixture'")
        connection.commit()
    return connection


@pytest.fixture
def database(tmp_path, monkeypatch):
    if os.getenv("KVK_READER_ACTIVATION_SQL_APPROVED_TARGET") != TARGET:
        pytest.skip("Exact disposable activation target approval required.")
    from kvk.services.new_source_artifact_store import ArtifactStore
    from kvk.services.season_source_service import SeasonSourceService
    from tests import test_kvk_source_sql_integration as fixtures

    season = 1000000 + int(uuid4().hex[:7], 16)
    choices = SeasonSourceService(connect)
    choices.choose(
        season,
        "snapshot_report_v1",
        actor="synthetic",
        reason="activation fixture",
        provenance={},
        authorized=True,
    )
    choices.transition(
        season,
        "open",
        expected_version=1,
        actor="synthetic",
        reason="activation fixture",
        authorized=True,
    )
    original = fixtures.admission
    monkeypatch.setattr(
        fixtures,
        "admission",
        lambda *a, **kw: replace(original(*a, **kw), guild_id=str(ADMIN.guild_id)),
    )
    return connect, season, ArtifactStore(tmp_path / "artifacts")


def selected_old(database, monkeypatch):
    from kvk.services import new_source_calculation
    from tests.test_kvk_source_sql_integration import sealed_fixture

    service, update = sealed_fixture(database)
    with monkeypatch.context() as patch:
        patch.setattr(
            new_source_calculation, "CALCULATION_VERSION", "snapshot_report_calculation_v2"
        )
        result = service.publish(update["UpdateID"])
    return result


def test_engine_refresh_restarts_replays_and_preserves_old_result(database, monkeypatch):
    from kvk.dal.source_update_dal import CONTEXT_COLUMNS, INPUT_COLUMNS, load_update
    from kvk.models.new_source_reporting import CALCULATION_VERSION

    old = selected_old(database, monkeypatch)
    _, season, _ = database
    service = SourceAdminReviewService(
        ACCESS, SourceAdminReviewDAL(connect), lambda: datetime.now(UTC).replace(microsecond=0)
    )
    review = service.prepare_refresh(
        ADMIN, season=season, period="fight:pass4", reason="Synthetic v2 to v3 refresh"
    )
    assert (
        service.repository.refresh_context(season, "fight:pass4")["PublicationID"]
        == old.publication_id
    )
    # A new service/connection confirms the durable payload; no in-memory approval.
    resumed = SourceAdminReviewService(
        ACCESS, SourceAdminReviewDAL(connect), lambda: datetime.now(UTC).replace(microsecond=0)
    )
    outcome = resumed.confirm(ADMIN, review["ReviewID"], review["Version"])
    replay = resumed.confirm(ADMIN, review["ReviewID"], review["Version"])
    assert outcome["outcome"] == replay["outcome"]
    new = outcome["outcome"]["result"]
    assert new["publication_id"] != old.publication_id
    assert new["update_id"] != old.update_id
    current = service.repository.refresh_context(season, "fight:pass4")
    assert current["CalculationVersion"] == CALCULATION_VERSION
    with transaction(connect) as cursor:
        before = load_update(cursor, old.update_id)
        after = load_update(cursor, new["update_id"])
        assert all(before[k] == after[k] for k in (*CONTEXT_COLUMNS, *INPUT_COLUMNS))
        cursor.execute(
            "SELECT COUNT(*) AS N FROM KVK.SourcePublication WHERE PublicationID IN (?,?) AND BuildState='complete'",
            old.publication_id,
            new["publication_id"],
        )
        assert one(cursor)["N"] == 2
        cursor.execute("SELECT COUNT(*) AS N FROM KVK.SourceExportIntent WHERE KVK_NO=?", season)
        assert one(cursor)["N"] == 2
    with pytest.raises(SourceConflict, match="already uses"):
        service.prepare_refresh(ADMIN, season=season, period="fight:pass4", reason="Duplicate")


def test_engine_competing_review_is_stale_after_one_refresh(database, monkeypatch):
    selected_old(database, monkeypatch)
    service = SourceAdminReviewService(
        ACCESS, SourceAdminReviewDAL(connect), lambda: datetime.now(UTC).replace(microsecond=0)
    )
    args = dict(season=database[1], period="fight:pass4", reason="Competing refresh")
    first = service.prepare_refresh(ADMIN, **args)
    second = service.prepare_refresh(ADMIN, **args)
    service.confirm(ADMIN, first["ReviewID"], first["Version"])
    with pytest.raises(SourceConflict, match="base changed"):
        service.confirm(ADMIN, second["ReviewID"], second["Version"])
    assert service.read(ADMIN, second["ReviewID"])["ReviewState"] == "pending"


def test_engine_preview_mismatch_rolls_back_selection_and_export_intent(database, monkeypatch):
    old = selected_old(database, monkeypatch)
    service = SourceAdminReviewService(
        ACCESS, SourceAdminReviewDAL(connect), lambda: datetime.now(UTC).replace(microsecond=0)
    )
    review = service.prepare_refresh(
        ADMIN, season=database[1], period="fight:pass4", reason="Rollback proof"
    )
    with monkeypatch.context() as patch:
        patch.setattr(
            "kvk.dal.source_calculation_refresh_dal.publication_result_hash", lambda *_: "0" * 64
        )
        with pytest.raises(SourceConflict, match="preview"):
            service.confirm(ADMIN, review["ReviewID"], review["Version"])
    assert service.read(ADMIN, review["ReviewID"])["ReviewState"] == "pending"
    assert (
        service.repository.refresh_context(database[1], "fight:pass4")["PublicationID"]
        == old.publication_id
    )
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS N FROM KVK.SourceExportIntent WHERE KVK_NO=?", database[1]
        )
        assert one(cursor)["N"] == 1
    assert (
        service.confirm(ADMIN, review["ReviewID"], review["Version"])["ReviewState"] == "completed"
    )


def amendment(action):
    path = (
        Path(os.environ["KVK_READER_ACTIVATION_SQL_SOURCE"])
        / "deploy/amendments/20261014_reader_history_permissions.sql"
    )
    with connect(autocommit=True) as conn:
        sid = conn.execute(
            "SELECT sid FROM sys.database_principals WHERE name=N'ReaderHistoryFixture'"
        ).fetchval()
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE #ReaderHistoryPermissionAmendment(ExpectedServer nvarchar(128),ExpectedDatabase nvarchar(128),PrincipalName nvarchar(128),LoginSid varbinary(85),Action varchar(8))"
        )
        cursor.execute(
            "INSERT #ReaderHistoryPermissionAmendment VALUES(?,?,?,?,?)",
            r"9SX2VF4\K98DEV",
            DATABASE,
            "ReaderHistoryFixture",
            sid,
            action,
        )
        cursor.execute(path.read_text(encoding="utf-8"))
        while cursor.nextset():
            pass


def test_engine_history_minimal_rights_capture_retry_and_denials(database, monkeypatch):
    import pyodbc

    from kvk.dal.new_source_history_dal import capture_history, iter_history

    result = selected_old(database, monkeypatch)
    with connect(autocommit=True) as conn:
        conn.execute(
            "IF USER_ID(N'ReaderHistoryFixture') IS NULL CREATE USER ReaderHistoryFixture WITHOUT LOGIN"
        )
        names = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sys.tables WHERE schema_id=SCHEMA_ID('KVK') AND name NOT IN ('SourceExportHistory','SourceExportHistoryRow')"
            )
        ]
        for name in names:
            assert name.replace("_", "").isalnum()
            conn.execute("GRANT SELECT ON OBJECT::KVK.[" + name + "] TO ReaderHistoryFixture")
    amendment("Rollback")
    args = dict(
        connect=lambda: connect(restricted=True),
        intent_id=result.intent_id,
        kvk_no=database[1],
        guild_id=str(ADMIN.guild_id),
    )
    with pytest.raises(pyodbc.Error):
        capture_history(**args)
    amendment("Apply")
    amendment("Apply")
    first = capture_history(**args)
    assert first.row_count == 3
    assert capture_history(**args) == first
    assert len(list(iter_history(connect=args["connect"], snapshot=first))) == 3
    for sql in (
        "DELETE FROM KVK.SourceExportHistoryRow WHERE 1=0",
        "UPDATE KVK.SourceExportHistoryRow SET PayloadJson=N'{}' WHERE 1=0",
        "UPDATE KVK.SourceExportHistory SET GuildID='999' WHERE 1=0",
        "DELETE FROM KVK.SourceExportHistory WHERE 1=0",
    ):
        conn = connect(restricted=True)
        try:
            with pytest.raises(pyodbc.Error):
                conn.execute(sql)
        finally:
            conn.rollback()
            conn.close()
    amendment("Rollback")
    amendment("Rollback")
    amendment("Apply")
