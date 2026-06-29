from stats.dal import import_audit_dal


class _FakeCursor:
    def __init__(self, row=None, columns=None):
        self.calls = []
        self.description = [(name,) for name in (columns or [])]
        self._row = row

    def execute(self, sql, *params):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._row


class _FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.autocommit = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_obj


def _factory(cursor):
    conn = _FakeConnection(cursor)

    def make_conn():
        return conn

    return make_conn, conn


def test_start_import_audit_batch_executes_writer_proc():
    cursor = _FakeCursor(
        row=(42, "11111111-1111-1111-1111-111111111111"),
        columns=["ImportAuditBatchId", "CorrelationId"],
    )
    factory, conn = _factory(cursor)

    ref = import_audit_dal.start_import_audit_batch(
        import_kind="fallback",
        source_type="fallback_source_file",
        source_filename="stats.xlsx",
        details_json='{"ok": true}',
        connection_factory=factory,
    )

    assert conn.autocommit is True
    sql, params = cursor.calls[0]
    assert "dbo.usp_ImportAudit_StartBatch" in sql
    assert params[0:3] == ("fallback", "fallback_source_file", "stats.xlsx")
    assert params[13] == '{"ok": true}'
    assert ref.import_audit_batch_id == 42
    assert ref.correlation_id == "11111111-1111-1111-1111-111111111111"


def test_record_import_audit_phase_executes_writer_proc():
    cursor = _FakeCursor(row=(7,), columns=["ImportAuditPhaseId"])
    factory, conn = _factory(cursor)

    phase_id = import_audit_dal.record_import_audit_phase(
        import_audit_batch_id=42,
        phase_name="fallback_file_prepare",
        phase_status="completed",
        rows_in=3,
        rows_out=2,
        set_batch_status="staged",
        connection_factory=factory,
    )

    assert conn.autocommit is True
    sql, params = cursor.calls[0]
    assert "dbo.usp_ImportAudit_RecordPhase" in sql
    assert params[0:3] == (42, "fallback_file_prepare", "completed")
    assert params[6] == 2
    assert params[11] == "staged"
    assert phase_id == 7


def test_complete_import_audit_batch_executes_writer_proc():
    cursor = _FakeCursor(row=(42,), columns=["ImportAuditBatchId"])
    factory, conn = _factory(cursor)

    import_audit_dal.complete_import_audit_batch(
        import_audit_batch_id=42,
        rows_in_source=11,
        rows_staged=10,
        rows_written=9,
        external_batch_table="dbo.FallbackImportBatchControl",
        external_batch_id="123",
        connection_factory=factory,
    )

    assert conn.autocommit is True
    sql, params = cursor.calls[0]
    assert "dbo.usp_ImportAudit_CompleteBatch" in sql
    assert params[0:5] == (42, "completed", 11, 10, 9)
    assert params[6:8] == ("dbo.FallbackImportBatchControl", "123")


def test_fail_import_audit_batch_executes_writer_proc():
    cursor = _FakeCursor(row=(42,), columns=["ImportAuditBatchId"])
    factory, conn = _factory(cursor)

    import_audit_dal.fail_import_audit_batch(
        import_audit_batch_id=42,
        rows_in_source=5,
        error_type="ImportStepFailed",
        error_text="boom",
        rows_staged=4,
        external_batch_table="dbo.FallbackImportBatchControl",
        external_batch_id="456",
        connection_factory=factory,
    )

    assert conn.autocommit is True
    sql, params = cursor.calls[0]
    assert "dbo.usp_ImportAudit_FailBatch" in sql
    assert params[0:6] == (42, "failed", 5, "ImportStepFailed", "boom", 4)
    assert params[8:10] == ("dbo.FallbackImportBatchControl", "456")
