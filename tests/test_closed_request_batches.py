"""Bounded SQL reads preserve transcript checks without per-request connections."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_dal import ExportExecutionDAL


def database(count=130, damage=None):
    stream = str(uuid4())
    requests = [dict(RequestID=str(uuid4()), StreamID=stream, Sequence=i + 1) for i in range(count)]
    events = [
        dict(RequestID=r["RequestID"], EventSequence=i + 1) for r in requests for i in range(3)
    ]
    connections = []

    def connect():
        connection = Mock()
        cursor = connection.cursor.return_value

        def execute(sql, *args):
            assert args[0] == stream
            if "SELECT TOP (64)" in sql:
                selected = [r.copy() for r in requests if r["Sequence"] > args[1]][:64]
                if damage == "gap" and selected:
                    selected[0]["Sequence"] += 1
                if damage == "foreign_stream" and selected:
                    selected[0]["StreamID"] = str(uuid4())
                if damage == "duplicate" and len(selected) > 1:
                    selected[1]["RequestID"] = selected[0]["RequestID"]
            else:
                ids = {r["RequestID"] for r in requests if args[1] < r["Sequence"] <= args[2]}
                selected = [e.copy() for e in events if e["RequestID"] in ids]
                if damage == "foreign_event" and selected:
                    selected[0]["RequestID"] = str(uuid4())
                if damage == "sql_error":
                    raise OSError("SQL unavailable")
            cursor.description = [(k,) for k in selected[0]] if selected else []
            cursor.fetchall.return_value = [tuple(r.values()) for r in selected]

        cursor.execute.side_effect = execute
        connections.append(connection)
        return connection

    return ExportExecutionDAL(connect), stream, requests, events, connections


@pytest.mark.parametrize("count", [0, 1, 64, 65, 130, 1024])
def test_batches_are_complete_bounded_and_release_sql_before_yield(count):
    dal, stream, requests, events, connections = database(count)
    result = []
    for row in dal.request_records(stream):
        for connection in connections:
            connection.close.assert_called_once()
            connection.cursor().close.assert_called_once()
        result.append(row)
    assert [r for _, r, _ in result] == requests
    assert [e for _, _, values in result for e in values] == events
    pages = (count + 63) // 64
    assert len(connections) == pages + 1
    assert sum(c.cursor().execute.call_count for c in connections) == 2 * pages + 1


@pytest.mark.parametrize(
    "damage", ["gap", "foreign_stream", "duplicate", "foreign_event", "sql_error"]
)
def test_corrupt_page_or_sql_failure_cannot_escape_or_leak_connections(damage):
    dal, stream, _, _, connections = database(damage=damage)
    with pytest.raises((SourceConflict, OSError)):
        list(dal.request_records(stream))
    for connection in connections:
        connection.close.assert_called_once()
        connection.cursor().close.assert_called_once()


def test_early_exit_closes_iterator_without_fetching_more_pages():
    dal, stream, _, _, connections = database()
    iterator = dal.request_records(stream)
    next(iterator)
    iterator.close()
    assert len(connections) == 1
    connections[0].close.assert_called_once()


@pytest.mark.parametrize("broken", [False, True])
def test_verifier_checks_private_evidence_with_batch_records(broken):
    from tests.test_export_reconciliation_service import closed_stream_fixture

    verifier, stream, request, events, _ = closed_stream_fixture()
    dal = verifier.dal
    dal.request_records = lambda _: iter([(str(request["RequestID"]).lower(), request, events)])
    dal.request_ids = Mock(side_effect=AssertionError("per-request query used"))
    dal.read_request = Mock(side_effect=AssertionError("per-request query used"))
    if broken:
        events[-1]["EvidenceHash"] = b"x" * 32
    if broken:
        with pytest.raises(SourceConflict):
            verifier.verify(stream["StreamID"], account="account-a", registration_hash=b"r" * 32)
    else:
        assert (
            verifier.verify(
                stream["StreamID"], account="account-a", registration_hash=b"r" * 32
            ).request_count
            == 1
        )
