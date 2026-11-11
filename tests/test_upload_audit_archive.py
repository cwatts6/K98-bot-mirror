import json

from services import operation_diagnostics
from services.optional_import_audit_worker import ImportAuditWriter
from tests.test_guided_recovery import ACTOR
from tests.test_optional_import_audit_worker import Dal, wait_for
from tests.test_p013_complete_archive import read_archive
from tests.test_recovery_report import report_service


def test_actual_archive_retains_first_loss_and_latest_terminal_after_restart(monkeypatch, tmp_path):
    sink = operation_diagnostics.DiagnosticSink(tmp_path).start()
    monkeypatch.setattr(operation_diagnostics, "_sink", sink)
    writer = ImportAuditWriter(lambda: None, dal=Dal()).start()
    try:
        handle = writer.start_batch(import_kind="honor", source_filename="PRIVATE_FILENAME")
        assert not writer.action(handle, "phase", {"details": b"PRIVATE_BYTES"})
        writer.action(handle, "complete", {"rows_written": 4, "status": "completed"})
        wait_for(lambda: writer.settled == 2)
    finally:
        writer.close()
        sink.close()
    restored = operation_diagnostics.DiagnosticSink(tmp_path).start()
    monkeypatch.setattr(operation_diagnostics, "_sink", restored)
    restored.close()
    service, _, _ = report_service(0)
    ordinary = json.loads(service.download_report(ACTOR)["content"])
    report = service.download_complete_report(ACTOR)
    members, manifest = read_archive(report)
    rows = [json.loads(line) for line in members["operations.jsonl"].splitlines()]
    row = next(row for row in rows if row["reference"] == handle.correlation_id)
    assert row["first_failure"]["state"] == "failed"
    assert row["first_failure"]["diagnostic_loss"] == 1
    assert row["transitions"][-1]["state"] == "settled"
    assert row["transitions"][-1]["diagnostic_loss"] == 1
    assert manifest["components"]["operations.jsonl"]["included"] >= 1
    assert handle.correlation_id in json.dumps(ordinary)
    assert b"PRIVATE_FILENAME" not in b"".join(members.values())
    assert b"PRIVATE_BYTES" not in b"".join(members.values())
    assert not writer._contexts  # Restored reports do not reconstruct work or bindings.
