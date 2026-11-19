"""Ordinary season metadata is passive; mutation admission remains locked."""

from unittest.mock import Mock

import pytest

from kvk.dal import season_source_dal as seasons, source_routing_dal as routing
from services import export_coordination_dal as queue
from tests.test_kvk_public_routing import RoutingStore
from tests.test_recovery_sql_snapshot import assert_no_producer_locks


def test_public_resolution_is_one_short_noncommitting_read():
    store = RoutingStore()
    connection = store.connect()
    read = routing.resolve_season_read(16, connect=lambda: connection)
    assert read.availability == "current"
    sql = [sql for _, sql, _ in store.events]
    assert_no_producer_locks(sql)
    assert not any("FROM KVK.SourceSelection " in s for s in sql)
    assert connection.timeout == 3
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_season_read_owns_snapshot_without_writer_locks(monkeypatch):
    connection = Mock(autocommit=False)
    monkeypatch.setattr("kvk.dal.new_source_import_dal.one", lambda _: {"SeasonVersion": 1})
    assert seasons.SeasonSourceDAL(lambda: connection).read(16) == {"SeasonVersion": 1}
    queries = [c.args[0] for c in connection.cursor.return_value.execute.call_args_list]
    assert_no_producer_locks(queries)
    assert connection.timeout == 3
    connection.commit.assert_not_called()


def test_weight_discovery_reads_source_and_vector_in_owned_snapshot(monkeypatch):
    from kvk.dal import source_weight_dal

    connection = Mock(autocommit=False)
    require = Mock()
    weights = Mock()
    monkeypatch.setattr(seasons, "require_source", require)
    monkeypatch.setattr(source_weight_dal, "require_current_export_weights", weights)
    monkeypatch.setattr(queue, "rows", lambda _: [{"ConfigVersionID": "config"}])
    intent = dict(KVK_NO=16, IntentID="fixture")
    queue.ExportCoordinationDAL(lambda: connection).check_intent_weights(intent)
    assert require.call_args.kwargs == {"passive": True}
    assert require.call_args.args[0] is weights.call_args.args[0]
    assert connection.timeout == 3
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


@pytest.mark.parametrize("passive", [False, True])
def test_require_source_preserves_default_writer_locks(monkeypatch, passive):
    cursor = Mock()
    monkeypatch.setattr(
        "kvk.dal.new_source_import_dal.one",
        lambda _: dict(SourceKey="snapshot_report_v1", SeasonState="open", SeasonVersion=1),
    )
    seasons.require_source(
        cursor, 16, "snapshot_report_v1", **({"passive": True} if passive else {})
    )
    assert ("UPDLOCK,HOLDLOCK" in cursor.execute.call_args.args[0]) is not passive


@pytest.mark.parametrize("season", [True, 0, -1, 2**31, "16"])
def test_passive_season_read_retains_input_validation(season):
    cursor = Mock()
    with pytest.raises(ValueError, match="Invalid source season"):
        seasons.read_season(cursor, season)
    cursor.execute.assert_not_called()
