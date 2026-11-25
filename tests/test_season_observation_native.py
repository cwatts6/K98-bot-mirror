"""Real season tuple and weight discovery snapshots in a new disposable database."""

from datetime import datetime
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal import season_source_dal as seasons, source_routing_dal as routing
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import ExportCoordinationDAL
from tests.test_kvk_public_routing import RoutingStore

TABLES = tuple(
    "KVK." + name
    for name in (
        "SeasonSource",
        "SourceRouting",
        "SourceCompleteSelection",
        "SourceUpdate",
        "SourcePublication",
        "SourceConfigVersion",
        "SourceConfigRequest",
        "SourceExportIntentPublication",
        "SourceWeightConfig",
        "SourceAdminReview",
        "KVK_CampMap",
        "KVK_DKPWeights",
        "KVK_Windows",
    )
)


@pytest.fixture(scope="module")
def database(snapshot_database):
    import pyodbc

    cn = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    cn.timeout = 5
    try:
        assert (
            cn.execute("SELECT used_log_space_in_percent FROM sys.dm_db_log_space_usage").fetchval()
            < 70
        )
        cn.execute("CREATE SCHEMA KVK")
        for name in TABLES:
            raw = (Path("C:/K98-bot-SQL-Server/sql_schema") / (name + ".Table.sql")).read_text(
                encoding="utf-8-sig"
            )
            if ".KVK_" in name:
                # These authoritative legacy scripts include their own guarded
                # table/index/default/check definitions, with no external FKs.
                assert "FOREIGN KEY" not in raw
                cn.execute(raw)
            else:
                body = re.search(r"CREATE TABLE " + re.escape(name) + r"\s*\(.*?\n\);", raw, re.S)
                assert body, name
                sql = "\n".join(line for line in body[0].splitlines() if "FOREIGN KEY" not in line)
                cn.execute(re.sub(r",\s*\);", "\n);", sql))
        cn.execute(
            "CREATE USER preview_reader WITHOUT LOGIN; GRANT SELECT ON SCHEMA::KVK TO preview_reader"
        )
    finally:
        cn.close()
    return snapshot_database


@pytest.fixture
def state(database):
    import pyodbc

    root = pyodbc.connect(database.connection_string, autocommit=True, timeout=5)
    root.timeout = 5
    handles = []
    store = RoutingStore()
    stamp = datetime(2026, 10, 15)
    try:
        for name in reversed(TABLES):
            root.execute("DELETE " + name)

        def insert(name, row):
            assert name in TABLES
            columns = {
                r[0]
                for r in root.execute(
                    "SELECT name FROM sys.columns WHERE object_id=OBJECT_ID(?)", name
                )
            }
            values = {
                k: v.replace(tzinfo=None) if isinstance(v, datetime) else v
                for k, v in row.items()
                if k in columns
            }
            root.execute(
                f"INSERT {name} ({','.join('['+k+']' for k in values)}) VALUES ({','.join('?' for _ in values)})",
                *values.values(),
            )

        insert(
            "KVK.SeasonSource",
            dict(
                store.choice,
                ChosenBy="test",
                ChosenUTC=stamp,
                Reason="fixture",
                ProvenanceJson="{}",
            ),
        )
        insert("KVK.SourceRouting", dict(store.routing, ApprovedBy="test", ApprovedUTC=stamp))
        insert("KVK.SourceCompleteSelection", dict(store.selection, SelectedUTC=stamp))
        insert("KVK.SourceUpdate", dict(store.update, PeriodKind=store.update["UpdateKind"]))
        insert(
            "KVK.SourcePublication",
            dict(
                store.publication,
                Generation=1,
                CalculationVersion="fixture",
                EligibleCount=store.publication["ResultCount"],
                CreatedUTC=stamp,
                CompletedUTC=stamp,
            ),
        )
        config = store.update["ConfigVersionID"]
        insert(
            "KVK.SourceConfigVersion",
            dict(
                ConfigVersionID=config,
                SourceKey="snapshot_report_v1",
                KVK_NO=16,
                ConfigVersion=1,
                RosterID=store.update["RosterID"],
                ConfigContentHash=b"c" * 32,
                WindowDigest=b"w" * 32,
                MappingDigest=b"m" * 32,
                WeightDigest=b"z" * 32,
                ApprovedUTC=stamp,
                ApprovedBy="test",
                Reason="fixture",
                ProvenanceJson="{}",
            ),
        )
        intent = str(uuid4())
        insert(
            "KVK.SourceExportIntentPublication",
            dict(store.selection, IntentID=intent, ConfigVersionID=config),
        )
        insert(
            "KVK.SourceWeightConfig",
            dict(
                ConfigVersionID=config,
                SourceKey="snapshot_report_v1",
                KVK_NO=16,
                WeightT4X=1,
                WeightT5Y=2,
                WeightDeadsZ=3,
                WeightT4XSource="1",
                WeightT5YSource="2",
                WeightDeadsZSource="3",
                EffectiveFromUTC=stamp,
            ),
        )
        insert(
            "KVK.KVK_DKPWeights",
            dict(KVK_NO=16, WeightT4X=1, WeightT5Y=2, WeightDeadsZ=3, EffectiveFromUTC=stamp),
        )

        def connect():
            cn = pyodbc.connect(database.connection_string, autocommit=True, timeout=5)
            handles.append(cn)
            cn.timeout = 5
            cn.execute("EXECUTE AS USER='preview_reader'")
            cn.autocommit = False
            return cn

        yield SimpleNamespace(
            root=root,
            connect=connect,
            handles=handles,
            store=store,
            insert=insert,
            stamp=stamp,
            intent=dict(KVK_NO=16, IntentID=intent),
        )
    finally:
        for cn in handles:
            try:
                cn.close()
            except pyodbc.ProgrammingError:
                pass
        root.execute("IF @@TRANCOUNT>0 ROLLBACK")
        root.close()


def assert_closed(s):
    import pyodbc

    for cn in s.handles:
        with pytest.raises(pyodbc.ProgrammingError):
            cn.cursor()


def test_writer_first_season_routing_and_weights_keep_committed_tuple(state):
    s = state
    s.root.execute("BEGIN TRANSACTION")
    try:
        s.root.execute("UPDATE KVK.SeasonSource SET SeasonVersion=2")
        s.root.execute("UPDATE KVK.SourceRouting SET RoutingVersion=2")
        s.root.execute("UPDATE KVK.KVK_DKPWeights SET WeightT4X=9")
        assert seasons.SeasonSourceDAL(s.connect).read(16)["SeasonVersion"] == 1
        read = routing.resolve_season_read(16, connect=s.connect)
        assert read.availability == "current"
        assert read.season_version == read.routing_version == 1
        ExportCoordinationDAL(s.connect).check_intent_weights(s.intent)
        assert_closed(s)
    finally:
        s.root.execute("ROLLBACK")


def test_observer_first_never_mixes_choice_routing_selection(state, monkeypatch):
    s = state
    original = routing.read_season
    fired = False

    def choice(cursor, season):
        nonlocal fired
        row = original(cursor, season)
        if not fired:
            fired = True
            s.root.execute("BEGIN TRANSACTION")
            s.root.execute("UPDATE KVK.SeasonSource SET SeasonVersion=2")
            s.root.execute("UPDATE KVK.SourceRouting SET RoutingVersion=2")
            s.root.execute("UPDATE KVK.SourceCompleteSelection SET PublicSelectionVersion=8")
            s.root.execute("COMMIT")
        return row

    monkeypatch.setattr(routing, "read_season", choice)
    old = routing.resolve_season_read(16, connect=s.connect)
    new = routing.resolve_season_read(16, connect=s.connect)
    assert (old.season_version, old.routing_version, old.public_selection_version) == (1, 1, 7)
    assert (new.season_version, new.routing_version, new.public_selection_version) == (2, 2, 8)
    assert old.availability == new.availability == "current"
    assert_closed(s)


@pytest.mark.parametrize("corruption", ["hash", "choice", "publication", "missing"])
def test_partial_or_cross_scope_tuple_is_unavailable(state, corruption):
    s = state
    if corruption == "hash":
        s.root.execute("UPDATE KVK.SourceUpdate SET ContentHash=?", b"x" * 32)
    elif corruption == "choice":
        s.root.execute("UPDATE KVK.SourceUpdate SET ChoiceID=?", str(uuid4()))
    elif corruption == "publication":
        s.root.execute("UPDATE KVK.SourcePublication SET ConfigVersionID=?", str(uuid4()))
    else:
        s.root.execute("DELETE KVK.SourcePublication")
    read = routing.resolve_season_read(16, connect=s.connect)
    assert read.availability == "unavailable" and read.publication_id is None
    assert_closed(s)


def test_snapshot_unavailable_has_no_locking_or_legacy_fallback(state, database):
    s = state
    # Every prior observation is closed before changing this disposable setting.
    s.root.execute("ALTER DATABASE [" + database.name + "] SET ALLOW_SNAPSHOT_ISOLATION OFF")
    try:
        read = routing.resolve_season_read(16, connect=s.connect)
        assert read.availability == "unavailable" and read.reason == "authority_unavailable"
        assert_closed(s)
    finally:
        s.root.execute("ALTER DATABASE [" + database.name + "] SET ALLOW_SNAPSHOT_ISOLATION ON")


def test_stale_weights_are_still_refused(state):
    s = state
    s.root.execute("UPDATE KVK.KVK_DKPWeights SET WeightT4X=9")
    with pytest.raises(SourceConflict, match="current season weights"):
        ExportCoordinationDAL(s.connect).check_intent_weights(s.intent)
    assert_closed(s)


def test_weight_gate_keeps_season_and_configuration_in_same_snapshot(state, monkeypatch):
    s = state
    original = seasons.require_source
    fired = False

    def require(cursor, *args, **kwargs):
        nonlocal fired
        choice = original(cursor, *args, **kwargs)
        if not fired:
            fired = True
            s.root.execute("UPDATE KVK.KVK_DKPWeights SET WeightT4X=9")
        return choice

    monkeypatch.setattr(seasons, "require_source", require)
    ExportCoordinationDAL(s.connect).check_intent_weights(s.intent)
    with pytest.raises(SourceConflict, match="current season weights"):
        ExportCoordinationDAL(s.connect).check_intent_weights(s.intent)
    assert_closed(s)


def test_permission_denied_is_unavailable_and_reader_closed(state):
    s = state
    s.root.execute("DENY SELECT ON KVK.SourceCompleteSelection TO preview_reader")
    try:
        assert routing.resolve_season_read(16, connect=s.connect).availability == "unavailable"
        assert_closed(s)
    finally:
        s.root.execute("REVOKE SELECT ON KVK.SourceCompleteSelection TO preview_reader")
