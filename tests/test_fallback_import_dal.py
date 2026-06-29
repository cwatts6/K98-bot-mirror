import json

import pytest

from stats.dal import fallback_import_dal


class _FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, *params):
        self.calls.append((sql, params))


def test_record_fallback_import_control_ignores_empty_metadata():
    cur = _FakeCursor()

    fallback_import_dal.record_fallback_import_control(cur, {})

    assert cur.calls == []


def test_record_fallback_import_control_allows_full_import_when_table_missing(monkeypatch):
    cur = _FakeCursor()
    monkeypatch.setattr(fallback_import_dal, "fetch_one_dict", lambda _cur: {"ObjectId": None})

    fallback_import_dal.record_fallback_import_control(
        cur,
        {
            "source_type": "full_fallback_snapshot",
            "source_filename": "stats.xlsx",
        },
    )

    assert len(cur.calls) == 1
    assert "FallbackImportBatchControl" in cur.calls[0][0]


def test_record_fallback_import_control_requires_table_for_partial(monkeypatch):
    cur = _FakeCursor()
    monkeypatch.setattr(fallback_import_dal, "fetch_one_dict", lambda _cur: {"ObjectId": None})

    with pytest.raises(RuntimeError, match="FallbackImportBatchControl is required"):
        fallback_import_dal.record_fallback_import_control(
            cur,
            {
                "source_type": "interim_auto_partial_snapshot",
                "source_filename": "partial.xlsx",
            },
        )


def test_record_fallback_import_control_inserts_metadata(monkeypatch):
    cur = _FakeCursor()
    monkeypatch.setattr(fallback_import_dal, "fetch_one_dict", lambda _cur: {"ObjectId": 123})

    fallback_import_dal.record_fallback_import_control(
        cur,
        {
            "source_type": "interim_auto_partial_snapshot",
            "source_filename": "partial.xlsx",
            "score_header": "Conduct Score",
            "columns_present": ["Governor ID", "Name", "Civilization"],
            "rows_in_source": "2",
            "rows_written": 10,
        },
    )

    assert len(cur.calls) == 2
    sql, params = cur.calls[1]
    assert "INSERT INTO dbo.FallbackImportBatchControl" in sql
    assert params[:3] == (
        "interim_auto_partial_snapshot",
        "partial.xlsx",
        "Conduct Score",
    )
    assert json.loads(params[3]) == ["Governor ID", "Name", "Civilization"]
    assert params[4:] == (2, 10)
