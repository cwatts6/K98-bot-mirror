from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kvk.dal import kvk_target_publication_dal as dal


class _Cursor:
    def __init__(self):
        self.executions: list[tuple[str, list[int]]] = []

    def execute(self, sql, params):
        self.executions.append((sql, params))

    def close(self):
        return None


class _Connection:
    def __init__(self):
        self.cursor_value = _Cursor()

    def cursor(self):
        return self.cursor_value

    def close(self):
        return None


def _row(governor_id: int, *, row_count: int = 2) -> dict[str, object]:
    return {
        "PublicationId": 41,
        "KVK_NO": 16,
        "PublicationState": "OFFICIAL",
        "SourceScanOrder": 1059,
        "SourceScanType": "MATCHMAKING_SCAN",
        "ConfiguredDraftScan": 1040,
        "ConfiguredMatchmakingScan": 1059,
        "PublishedAtUtc": datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        "TargetRowCount": row_count,
        "OutputObjectName": "dbo.EXCEL_EXPORT_KVK_TARGETS_16",
        "PublicationVersion": 1,
        "PublicationSignature": "2ad2a141-c5bf-4075-927b-832e44477e55",
        "TargetRank": governor_id,
        "GovernorID": governor_id,
        "GovernorName": f"Governor {governor_id}",
        "Power": "123,000,000",
        "Kill_Target": 200,
        "Min_Kill_Target": 50,
        "Deads_Target": 10,
        "DKP_Target": 100,
    }


def test_full_publication_read_is_explicit_parameterized_and_single_rowset(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(dal, "_open_connection", lambda: connection)
    monkeypatch.setattr(dal, "fetch_all_dicts", lambda _cursor: [_row(123), _row(456)])

    snapshot = dal.fetch_current_target_publication(16)

    assert snapshot is not None
    assert snapshot.metadata.source_scan_order == 1059
    assert len(snapshot.rows) == 2
    assert snapshot.rows[0]["Power"] == 123_000_000
    sql, params = connection.cursor_value.executions[0]
    assert "dbo.v_KVK_TARGETS_FOR_BOT" in sql
    assert "WHERE KVK_NO = ?" in sql
    assert params == [16]


def test_full_publication_read_rejects_row_count_mismatch(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(dal, "_open_connection", lambda: connection)
    monkeypatch.setattr(dal, "fetch_all_dicts", lambda _cursor: [_row(123, row_count=2)])

    with pytest.raises(dal.TargetPublicationContractError, match="row_count_mismatch"):
        dal.fetch_current_target_publication(16)


def test_full_publication_read_rejects_mixed_publication_identity(monkeypatch):
    connection = _Connection()
    mixed = _row(456)
    mixed["PublicationVersion"] = 2
    monkeypatch.setattr(dal, "_open_connection", lambda: connection)
    monkeypatch.setattr(dal, "fetch_all_dicts", lambda _cursor: [_row(123), mixed])

    with pytest.raises(dal.TargetPublicationContractError, match="inconsistent"):
        dal.fetch_current_target_publication(16)


def test_full_publication_read_preserves_unset_target_amounts(monkeypatch):
    connection = _Connection()
    row = _row(123, row_count=1)
    for field in ("Kill_Target", "Min_Kill_Target", "Deads_Target", "DKP_Target"):
        row[field] = None
    monkeypatch.setattr(dal, "_open_connection", lambda: connection)
    monkeypatch.setattr(dal, "fetch_all_dicts", lambda _cursor: [row])

    snapshot = dal.fetch_current_target_publication(16)

    assert snapshot is not None
    assert snapshot.rows[0]["Kill_Target"] is None
    assert snapshot.rows[0]["Min_Kill_Target"] is None
    assert snapshot.rows[0]["Deads_Target"] is None
    assert snapshot.rows[0]["DKP_Target"] is None
