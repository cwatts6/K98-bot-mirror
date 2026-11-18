"""Stage 3 reader composition against the approved disposable Stage 2 fixture."""

from kvk.services.new_source_reader_service import load_reader_projection
from tests.test_kvk_source_history_sql import (
    GUILD,
    database,  # noqa: F401
    selected,
    source_database,  # noqa: F401
)


def test_engine_reader_composition_and_fresh_connection_replay(request):
    fixture = request.getfixturevalue("database")
    connect, season, _ = fixture
    result = selected(fixture)
    from kvk.dal.new_source_import_dal import transaction
    from kvk.dal.source_update_dal import read_export_intent

    with transaction(connect) as cursor:
        intent, _ = read_export_intent(cursor, result.intent_id)
    args = dict(
        connect=connect,
        intent_id=result.intent_id,
        kvk_no=season,
        guild_id=GUILD,
        expected_hash=bytes(intent["VectorHash"]),
    )
    first = load_reader_projection(**args)
    second = load_reader_projection(**args)
    assert first.key == second.key
    assert len(first.sheets) == 11
    players = next(
        s for s in first.sheets if s.key == first.audit.selections[0].period_id + ":player"
    )
    assert len(players.rows) == 2
    assert len(next(s for s in first.sheets if s.key == "sources").rows) == 3
    assert len(first.audit.tables) == 12


def test_engine_checkpoint_composition_and_manifest_replay(request):
    fixture = request.getfixturevalue("database")
    connect, season, _ = fixture
    result = selected(fixture)
    from kvk.dal.new_source_import_dal import transaction
    from kvk.dal.source_update_dal import read_export_intent

    with transaction(connect) as cursor:
        intent, _ = read_export_intent(cursor, result.intent_id)
    args = dict(
        connect=connect,
        intent_id=result.intent_id,
        kvk_no=season,
        guild_id=GUILD,
        expected_hash=bytes(intent["VectorHash"]),
        with_checkpoints=True,
    )
    first = load_reader_projection(**args)
    second = load_reader_projection(**args)
    assert first.key == second.key
    assert len(first.sheets) == 38
    assert len(first.checkpoints) == 1
    assert len(first.checkpoints[0].sheet_keys) == 3
    assert first.checkpoints == second.checkpoints


def test_engine_physical_workbook_generation_replays_pinned_history(request):
    fixture = request.getfixturevalue("database")
    connect, season, _ = fixture
    result = selected(fixture)
    from kvk.dal.new_source_import_dal import transaction
    from kvk.dal.source_update_dal import read_export_intent
    from kvk.rendering.new_source_workbook import build_workbook_generation, partition_workbook

    with transaction(connect) as cursor:
        intent, _ = read_export_intent(cursor, result.intent_id)
    args = dict(
        connect=connect,
        intent_id=result.intent_id,
        kvk_no=season,
        guild_id=GUILD,
        expected_hash=bytes(intent["VectorHash"]),
        with_checkpoints=True,
    )
    first = build_workbook_generation(load_reader_projection(**args))
    second = build_workbook_generation(load_reader_projection(**args))
    assert first.key == second.key
    assert first.manifest() == second.manifest()
    assert partition_workbook(first.manifest()) == partition_workbook(second.manifest())
    assert len(first.tables) == 38
    assert next(t for t in first.tables if t.name == "Source Files").data_rows == 3


def test_engine_reader_coordinated_delivery_uses_exact_sql_guild_scope(request):
    from threading import Event
    from types import SimpleNamespace
    from unittest.mock import Mock

    from kvk.dal.new_source_import_dal import digest, transaction
    from kvk.dal.source_update_dal import read_export_intent
    from kvk.services.new_source_delivery_service import deliver_coordinated_export
    from tests.test_kvk_source_workbooks import setup_reader

    fixture = request.getfixturevalue("database")
    connect, season, _ = fixture
    result = selected(fixture)
    with transaction(connect) as cursor:
        intent, _ = read_export_intent(cursor, result.intent_id)
    args, _, api = setup_reader()
    dal = Mock()
    dal.begin_attempt.return_value = "sql-reader-attempt"
    receipt = deliver_coordinated_export(
        job=dict(
            ConsumerKind="new_source",
            IntentID=result.intent_id,
            InputHash=bytes(intent["VectorHash"]),
            KVK_NO=season,
            DestinationSetHash=digest(tuple(sorted(("fake-index", "fake-1", "fake-2")))),
        ),
        claim=SimpleNamespace(fence=10),
        dal=dal,
        transport=args["transport"],
        connect=connect,
        budget=lambda: None,
        stop=Event(),
        reader_guild_id=GUILD,
    )
    assert receipt["files"] == ["fake-index", "fake-1"]
    manifest = dal.begin_attempt.call_args.args[1]
    assert len(manifest["tables"]) == 38
    assert manifest["tables"]["Source Files"]["rows"] == 3
    assert len(api.grids["fake-1"]) == 39
    dal.confirm.assert_called_once()
