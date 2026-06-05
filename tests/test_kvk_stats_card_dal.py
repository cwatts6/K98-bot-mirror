from __future__ import annotations

from kvk.dal import kvk_stats_card_dal


class _Cursor:
    def __init__(self, rows: list[dict], *, fail_rank_query: bool = False):
        self._rows = rows
        self._index = 0
        self._fail_rank_query = fail_rank_query
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql: str, params=None):
        self.executed.append((sql, params))
        if self._fail_rank_query and "vw_Player_Overall_KVK_Rank" in sql:
            raise RuntimeError("view missing")
        return None

    def fetchone(self):
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row


class _Connection:
    def __init__(self, cursor: _Cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def cursor(self):
        return self._cursor


def test_fetch_context_includes_overall_kvk_rank(monkeypatch):
    cursor = _Cursor(
        [
            {"KVK_NAME": "Tides of War"},
            {"kingdom": 1978, "campid": 2, "camp_name": "Wind"},
            {
                "overall_kvk_rank": 41,
                "overall_kvk_total_governors": 8734,
                "overall_kvk_percentile": 0.47,
            },
        ]
    )
    monkeypatch.setattr(kvk_stats_card_dal, "get_conn_with_retries", lambda: _Connection(cursor))
    monkeypatch.setattr(kvk_stats_card_dal, "cursor_row_to_dict", lambda _cur, row: row)

    context = kvk_stats_card_dal.fetch_kvk_stats_card_context(54, "58744139")

    assert context["kvk_name"] == "Tides of War"
    assert context["kingdom"] == 1978
    assert context["camp_id"] == 2
    assert context["camp_name"] == "Wind"
    assert context["overall_kvk_rank"] == 41
    assert context["overall_kvk_total_governors"] == 8734
    assert context["overall_kvk_percentile"] == 0.47
    assert any("vw_Player_Overall_KVK_Rank" in sql for sql, _params in cursor.executed)


def test_fetch_context_preserves_existing_context_when_rank_view_missing(monkeypatch, caplog):
    cursor = _Cursor(
        [
            {"KVK_NAME": "Tides of War"},
            {"kingdom": 1978, "campid": 2, "camp_name": "Wind"},
        ],
        fail_rank_query=True,
    )
    monkeypatch.setattr(kvk_stats_card_dal, "get_conn_with_retries", lambda: _Connection(cursor))
    monkeypatch.setattr(kvk_stats_card_dal, "cursor_row_to_dict", lambda _cur, row: row)

    context = kvk_stats_card_dal.fetch_kvk_stats_card_context(54, "58744139")

    assert context["kvk_name"] == "Tides of War"
    assert context["camp_name"] == "Wind"
    assert "overall_kvk_rank" not in context
    assert "kvk_stats_card_overall_rank_unavailable" in caplog.text
