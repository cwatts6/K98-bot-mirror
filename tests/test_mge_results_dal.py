import json

import pytest

from mge.dal import mge_results_dal


class ImportCursor:
    """A later SQL batch cannot retrieve an earlier batch's scope identity."""

    def __init__(self, result=(37,)):
        self.result = result
        self.calls = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))

    def fetchone(self):
        sql = self.calls[-1][0]
        return self.result if "OUTPUT INSERTED.ImportId" in sql else (None,)


def create_batch(monkeypatch, cursor):
    monkeypatch.setattr(mge_results_dal, "exec_with_cursor", lambda fn: fn(cursor))
    return mge_results_dal.create_import_batch(
        1001, "controlled", "upload", "player's.csv", "a" * 64, 9001
    )


def test_import_identity_is_returned_by_insert_batch(monkeypatch):
    cursor = ImportCursor()
    assert create_batch(monkeypatch, cursor) == 37
    assert len(cursor.calls) == 1
    sql, params = cursor.calls[0]
    assert "player's.csv" not in sql
    assert params[:6] == (1001, "controlled", "upload", "player's.csv", "a" * 64, 9001)
    assert json.loads(params[6])["filename"] == "player's.csv"


@pytest.mark.parametrize("result", [None, (None,)])
def test_import_missing_identity_fails_transaction_callback(monkeypatch, result):
    with pytest.raises(RuntimeError, match="INSERT returned no ImportId"):
        create_batch(monkeypatch, ImportCursor(result))
