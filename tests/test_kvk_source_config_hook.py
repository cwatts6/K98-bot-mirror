"""Synthetic S5B transaction boundary tests; no default SQL or provider access."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

import bot_config
from kvk.dal import new_source_recovery_dal as dal
from kvk.services import new_source_recovery_service as recovery
import proc_config_import as pci
from tests.test_proc_config_import_phase2 import FakeConn


def windows(end=14):
    return pd.DataFrame(
        [
            dict(
                KVK_NO=1,
                WindowName="Fight",
                WindowSeq=1,
                StartScanID=10,
                EndScanID=end,
                Notes="synthetic",
            )
        ]
    )


def fake_import(monkeypatch, tmp_path, connection=None):
    import stats_alerts.kvk_meta as kvk_meta

    monkeypatch.setattr(kvk_meta, "get_latest_kvk_metadata_sql", lambda: None)
    conn = connection or FakeConn()
    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(pci, "KVK_SHEET_ID", "synthetic-sheet")
    monkeypatch.setattr(pci, "IMPORT_TRANSACTIONAL", True)
    monkeypatch.setattr(pci, "IMPORT_CAPTURE_LOGSPACE", False)
    monkeypatch.setattr(pci, "_validate_import_config", lambda: (True, []))
    monkeypatch.setattr(pci, "_get_sheet_service", lambda: SimpleNamespace())
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: (
            windows()
            if rng.startswith("KVK_Windows")
            else (
                pd.DataFrame([{"KVK_NO": 1, "SomeCol": "A"}])
                if rng.startswith("ProcConfig")
                else pd.DataFrame()
            )
        ),
    )
    monkeypatch.setattr(pci, "_get_import_connection_with_retry", lambda: conn)
    monkeypatch.setattr(pci, "preflight_or_raise", lambda *a, **k: None)
    monkeypatch.setattr(pci, "log_backup_context", lambda *a, **k: None)
    monkeypatch.setattr(
        pci,
        "write_df_to_staging_and_upsert",
        lambda *a, **k: dict(staging=dict(status="ok"), upsert=dict(status="ok")),
    )
    monkeypatch.setattr(pci, "write_df_to_table", lambda *a, **k: dict(status="ok"))
    return conn


def test_disabled_hook_does_not_touch_cursor_or_schema(monkeypatch):
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", False)
    cursor = Mock()
    assert recovery.snapshot_config_import(cursor, object()) == ()
    cursor.execute.assert_not_called()


@pytest.mark.parametrize("actor", [None, "operator:synthetic"])
def test_hook_provenance_and_exact_values(monkeypatch, actor):
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", True)
    snapshot = Mock(return_value=("request",))
    monkeypatch.setattr(dal, "snapshot_import", snapshot)
    cursor = Mock()
    assert recovery.snapshot_config_import(cursor, windows(), actor=actor) == ("request",)
    args, kw = snapshot.call_args
    assert args[0] is cursor
    assert args[1][0]["StartScanID"] == 10 and args[1][0]["EndScanID"] == 14
    assert kw["actor"] == (actor or "system:proc_config_import")
    assert kw["origin"] == ("authorized_import" if actor else "system")
    assert len(kw["provenance"]["windows_digest"]) == 64
    assert kw["requested_utc"].tzinfo is UTC


@pytest.mark.parametrize("value", [0, -1, 1.2, True, 2147483648])
def test_hook_rejects_bad_endpoint_before_sql(monkeypatch, value):
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", True)
    cursor = Mock()
    with pytest.raises(ValueError):
        recovery.snapshot_config_import(cursor, windows(value))
    cursor.execute.assert_not_called()


def test_hook_inside_import_commit(monkeypatch, tmp_path):
    conn = fake_import(monkeypatch, tmp_path)
    calls = []

    def snapshot(cursor, df, **kwargs):
        assert cursor is conn._cursor and not conn.committed
        assert not conn.autocommit
        calls.append((df.to_dict("records"), kwargs))

    monkeypatch.setattr(recovery, "snapshot_config_import", snapshot)
    ok, _ = pci.run_proc_config_import(source_actor="operator:synthetic")
    assert ok and conn.committed and len(calls) == 1
    assert calls[0][1]["actor"] == "operator:synthetic"


def test_enabled_schema_failure_rolls_back_import(monkeypatch, tmp_path):
    conn = fake_import(monkeypatch, tmp_path)
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", True)
    monkeypatch.setattr(dal, "require_schema", Mock(side_effect=RuntimeError("schema missing")))
    ok, _ = pci.run_proc_config_import()
    assert not ok and conn.rolled_back and not conn.committed


def test_importer_return_error_keeps_committed_intent(monkeypatch, tmp_path):
    conn = fake_import(monkeypatch, tmp_path)
    intent, durable = [], []
    monkeypatch.setattr(
        recovery, "snapshot_config_import", lambda *a, **kw: intent.append("request")
    )

    def commit():
        conn.committed = True
        durable.extend(intent)

    conn.commit = commit
    original = conn._cursor.execute

    def execute(sql, *args, **kw):
        if "sp_TARGETS_MASTER" in sql:
            raise RuntimeError("deterministic postcommit failure")
        return original(sql, *args, **kw)

    conn._cursor.execute = execute
    ok, _ = pci.run_proc_config_import()
    assert not ok and conn.committed and durable == ["request"]


def test_nontransactional_import_never_calls_hook(monkeypatch, tmp_path):
    fake_import(monkeypatch, tmp_path)
    monkeypatch.setattr(pci, "IMPORT_TRANSACTIONAL", False)
    hook = Mock(side_effect=AssertionError("Unexpected Windows hook"))
    monkeypatch.setattr(recovery, "snapshot_config_import", hook)
    pci.run_proc_config_import()
    hook.assert_not_called()


def test_dal_refuses_no_transaction():
    cursor = Mock()
    cursor.fetchone.return_value = (0,)
    with pytest.raises(ValueError, match="transaction"):
        dal.snapshot_import(
            cursor,
            [],
            actor="system:test",
            origin="system",
            provenance={},
            requested_utc=datetime.now(UTC),
        )
    cursor.connection.commit.assert_not_called()


@pytest.fixture
def s5b_database(tmp_path):
    """Opt-in only; prerequisite schema is installed separately under exact authorization."""
    import os
    import re
    from uuid import uuid4

    from kvk.services.new_source_artifact_store import ArtifactStore

    server = os.environ.get("KVK_S5B_SQL_SERVER")
    name = os.environ.get("KVK_S5B_SQL_DATABASE")
    if not server and not name:
        pytest.skip("Exact authorized S5B disposable SQL target required.")
    if server not in (r"9SX2VF4\K98DEV", r"localhost\K98DEV") or not re.fullmatch(
        r"K98_S5B_Disposable_[0-9]{8}", name or ""
    ):
        pytest.fail("Refusing a non-S5B disposable target.")
    import pyodbc

    def connect():
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:"
            + server
            + ";DATABASE="
            + name
            + ";Trusted_Connection=yes;TrustServerCertificate=yes",
            autocommit=False,
            timeout=10,
        )
        conn.timeout = 30
        cur = conn.cursor()
        cur.execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()")
        if tuple(cur.fetchone()) != (r"9SX2VF4\K98DEV", name):
            conn.close()
            pytest.fail("Connected target differs from authorization.")
        cur.close()
        conn.rollback()
        return conn

    return (
        connect,
        1000000 + int(uuid4().hex[:7], 16),
        ArtifactStore(tmp_path / "synthetic-originals"),
    )


@pytest.mark.parametrize("rollback", [False, True])
def test_disposable_import_transaction_and_restart(monkeypatch, tmp_path, s5b_database, rollback):
    from kvk.dal.new_source_import_dal import SourceImportDAL, transaction
    from kvk.dal.new_source_reporting_dal import load_snapshot
    from kvk.services.new_source_publication_service import PublicationService
    from tests.test_kvk_source_sql_integration import accepted_event, seed_config

    connect, season, store = s5b_database
    importer = SourceImportDAL(connect, store)
    b0 = accepted_event(importer, season, 1, store)
    accepted_event(importer, season, 2, store)
    accepted_event(importer, season, 3, store)
    config = seed_config(connect, season, b0)
    service = recovery.RecoveryService(dal.RecoveryDAL(connect), PublicationService(connect))
    service.recover_period(season, config.period_id)
    before = load_snapshot(connect, kvk_no=season, period_id=config.period_id)

    class Cursor:
        def __init__(self, inner):
            self.inner = inner

        def __getattr__(self, key):
            return getattr(self.inner, key)

        def execute(self, sql, *args, **kwargs):
            if "sp_TARGETS_MASTER" in sql:
                raise RuntimeError("S5B deterministic return error after commit")
            self.inner.execute(sql, *args, **kwargs)
            return self

    class Connection:
        def __init__(self):
            self.inner = connect()

        def __getattr__(self, key):
            return getattr(self.inner, key)

        @property
        def autocommit(self):
            return self.inner.autocommit

        @autocommit.setter
        def autocommit(self, value):
            self.inner.autocommit = value

        def cursor(self):
            return Cursor(self.inner.cursor())

        def commit(self):
            if rollback:
                raise RuntimeError("S5B deterministic precommit failure")
            self.inner.commit()

    connection = Connection()
    fake_import(monkeypatch, tmp_path, connection)
    monkeypatch.setattr(bot_config, "KVK_SOURCE_RECOVERY_ENABLED", True)
    frame = windows(4)
    frame["KVK_NO"] = season
    frame["StartScanID"] = 1
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: (
            frame
            if rng.startswith("KVK_Windows")
            else (
                pd.DataFrame([{"KVK_NO": season}])
                if rng.startswith("ProcConfig")
                else pd.DataFrame()
            )
        ),
    )

    def write(cursor, conn, df, table, **kwargs):
        if table == "KVK.KVK_Windows":
            cursor.execute(
                "INSERT KVK.KVK_Windows (KVK_NO,WindowName,WindowSeq,StartScanID,EndScanID,Notes) VALUES (?,'Fight',1,1,4,'synthetic S5B')",
                season,
            )
        return dict(status="ok")

    monkeypatch.setattr(pci, "write_df_to_table", write)
    ok, _ = pci.run_proc_config_import()
    assert not ok
    with transaction(connect) as cursor:
        cursor.execute("SELECT COUNT(*) FROM KVK.SourceConfigRequest WHERE KVK_NO=?", season)
        assert cursor.fetchone()[0] == (0 if rollback else 1)
        cursor.execute("SELECT COUNT(*) FROM KVK.KVK_Windows WHERE KVK_NO=?", season)
        assert cursor.fetchone()[0] == (0 if rollback else 1)
    if rollback:
        return
    pending = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert not pending["is_current"]
    assert pending["publication"]["PublicationID"] == before["publication"]["PublicationID"]
    # Discard all caller instances, recover the committed request while scan 4 is missing.
    restarted = recovery.RecoveryService(dal.RecoveryDAL(connect), PublicationService(connect))
    restarted.recover_period(season, config.period_id)
    interim = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert interim["publication"]["PlayerState"] == "live"
    assert interim["pending_request"] is not None
    accepted_event(importer, season, 4, store)
    restarted = recovery.RecoveryService(dal.RecoveryDAL(connect), PublicationService(connect))
    restarted.recover_period(season, config.period_id)
    final = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert final["is_current"] and final["publication"]["EndScanID"] == 4
    assert final["publication"]["PlayerState"] == "corrected_final"
    assert final["pending_request"] is None
    assert restarted.recover_period(season, config.period_id) is None


def test_disposable_two_imports_before_recovery(s5b_database):
    from kvk.dal.new_source_import_dal import SourceImportDAL, transaction
    from kvk.dal.new_source_reporting_dal import load_snapshot
    from kvk.services.new_source_publication_service import PublicationService
    from tests.test_kvk_source_sql_integration import accepted_event, seed_config

    connect, season, store = s5b_database
    importer = SourceImportDAL(connect, store)
    b0 = accepted_event(importer, season, 1, store)
    accepted_event(importer, season, 2, store)
    accepted_event(importer, season, 3, store)
    config = seed_config(connect, season, b0)
    service = recovery.RecoveryService(dal.RecoveryDAL(connect), PublicationService(connect))
    service.recover_period(season, config.period_id)
    for end in (4, 3):
        with transaction(connect) as cursor:
            dal.snapshot_import(
                cursor,
                [dict(KVK_NO=season, WindowName="Fight", StartScanID=1, EndScanID=end)],
                actor="synthetic",
                origin="system",
                provenance={},
                requested_utc=datetime.now(UTC).replace(microsecond=0),
            )
    assert service.recover_period(season, config.period_id) is not None
    final = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert final["is_current"] and final["publication"]["EndScanID"] == 3
    assert service.recover_period(season, config.period_id) is None


def test_disposable_applied_request_does_not_own_later_publication(s5b_database):
    from kvk.dal.new_source_import_dal import SourceImportDAL, transaction
    from kvk.services.new_source_publication_service import PublicationService
    from tests.test_kvk_source_sql_integration import accepted_event, seed_config

    connect, season, store = s5b_database
    importer = SourceImportDAL(connect, store)
    b0 = accepted_event(importer, season, 1, store)
    accepted_event(importer, season, 2, store)
    accepted_event(importer, season, 3, store)
    config = seed_config(connect, season, b0)
    service = recovery.RecoveryService(dal.RecoveryDAL(connect), PublicationService(connect))
    service.recover_period(season, config.period_id)
    with transaction(connect) as cursor:
        request_ids = dal.snapshot_import(
            cursor,
            [dict(KVK_NO=season, WindowName="Fight", StartScanID=1, EndScanID=None)],
            actor="synthetic-admin",
            origin="admin",
            provenance={},
            requested_utc=datetime.now(UTC).replace(microsecond=0),
        )
    transition = service.recover_period(season, config.period_id)
    accepted_event(importer, season, 4, store)
    later = service.recover_period(season, config.period_id)
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT Actor,Reason,RequestID,ActionType FROM KVK.SourceAction WHERE NewPublicationID=?",
            later.publication_id,
        )
        action = cursor.fetchone()
        assert tuple(action) == (
            "system:kvk_source_recovery",
            "Recover accepted source inputs",
            None,
            "publish",
        )
        cursor.execute(
            "SELECT RequestState,AppliedPublicationID FROM KVK.SourceConfigRequest WHERE RequestID=?",
            request_ids[0],
        )
        state, applied = cursor.fetchone()
        assert state == "applied" and str(applied).lower() == transition.publication_id.lower()
    assert service.recover_period(season, config.period_id) is None


def test_disposable_numeric_text_recovery_preserves_publication(s5b_database):
    from kvk.dal.new_source_import_dal import SourceImportDAL, transaction
    from kvk.dal.new_source_reporting_dal import load_snapshot
    from kvk.models.new_source_reporting import ObservationInput
    from kvk.services.new_source_publication_service import PublicationService
    from tests.test_kvk_source_sql_integration import admission, observation, seed_config

    connect, season, store = s5b_database
    importer = SourceImportDAL(connect, store)
    events = []
    for number in (1, 2, 3):
        prepared, artifact = observation(season, number, store, value=str(number * 10))
        accepted = importer.accept_observation(prepared, artifact, admission())
        event = ObservationInput(
            accepted.logical_scan_id,
            accepted.identity_id,
            accepted.revision_id,
            prepared,
            prepared.metadata.scope.period_keys,
        )
        events.append(event)
        with transaction(connect) as cursor:
            restored = dal.RecoveryDAL._observation(cursor, accepted.revision_id)
        assert restored.observation.rows == prepared.rows
    config = seed_config(connect, season, events[0])
    expected_publisher = PublicationService(Mock())
    expected_publisher.dal.build_candidate = Mock(return_value={"Generation": 1})
    expected = expected_publisher.build_candidate(
        config=config, observations=tuple(events), b0=events[0]
    )
    service = recovery.RecoveryService(dal.RecoveryDAL(connect), PublicationService(connect))
    service.recover_period(season, config.period_id)
    actual = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    from kvk.dal.new_source_publication_dal import result_values

    assert actual["players"] == [
        result_values(player) for player in expected.snapshot.calculation.players
    ]
    assert actual["players"][0]["kp_t4_t5"] == 200
