from datetime import UTC, datetime

from inventory.dal import inventory_dal
from inventory.models import InventoryFlowType, InventoryImportStatus


class _Cursor:
    def __init__(self):
        self.sql = ""
        self.params = ()

    def execute(self, sql, params):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return (12345,)


class _Conn:
    def __init__(self):
        self.cursor_obj = _Cursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass


def test_create_import_batch_uses_output_inserted_identity(monkeypatch):
    conn = _Conn()
    monkeypatch.setattr(inventory_dal, "_get_conn", lambda: conn)

    batch_id = inventory_dal.create_import_batch(
        governor_id=111,
        discord_user_id=222,
        flow_type=InventoryFlowType.COMMAND,
        status=InventoryImportStatus.AWAITING_UPLOAD,
        expires_at_utc=datetime.now(UTC),
    )

    assert batch_id == 12345
    assert "OUTPUT INSERTED.ImportBatchID" in conn.cursor_obj.sql
    assert "SCOPE_IDENTITY" not in conn.cursor_obj.sql
    assert conn.committed is True
