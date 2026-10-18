"""Worker errors retain driver codes and locations without secret-bearing prose."""

import json
from threading import Event
from unittest.mock import Mock
from uuid import uuid4

import pyodbc

from services.export_coordination_service import ExportCoordinator
from services.export_failure_diagnostics import failure_record


def test_driver_diagnostics_redact_prose_and_bound_chain():
    error = pyodbc.ProgrammingError("42000", "PASSWORD=secret SQL text (156) (11501)")
    outer = RuntimeError("private cell contents")
    outer.__cause__ = error
    error.__cause__ = outer
    record = failure_record(outer, job_id="secret", stage="secret")
    assert record["exception_types"] == ["RuntimeError", "ProgrammingError"]
    assert record["sqlstates"] == ["42000"]
    assert record["sql_numbers"] == [156, 11501]
    assert record["stage"] == "unknown" and record["job_id"] is None
    assert "secret" not in json.dumps(record) and "private cell" not in json.dumps(record)


def test_non_driver_prose_cannot_supply_sql_codes():
    record = failure_record(ValueError("42000 PASSWORD=secret (156)"))
    assert record["sqlstates"] == record["sql_numbers"] == []


def test_worker_records_original_and_terminal_failure_without_changing_retention(caplog):
    dal, adapter = Mock(), Mock()
    job_id = str(uuid4())
    claim = Mock(job_id=job_id)
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["acct"]
    dal.claim_next.return_value = claim
    dal.authorize.return_value = dict(ConsumerKind="new_source", SpoolKey=None)
    adapter.side_effect = pyodbc.ProgrammingError("42000", "private SQL (156)")
    dal.fail.side_effect = pyodbc.OperationalError("08S01", "private connection (10054)")
    ExportCoordinator(dal, adapters={"new_source": adapter}).run_batch(Event())
    dal.fail.assert_called_once_with(claim, diagnostic=dal.fail.call_args.kwargs["diagnostic"])
    records = [
        json.loads(r.message.split(" ", 1)[1])
        for r in caplog.records
        if r.message.startswith("export_")
    ]
    assert [r["stage"] for r in records] == ["terminal_record", "delivery"]
    assert records[0]["sqlstates"] == ["08S01", "42000"]
    assert records[1]["sql_numbers"] == [156]
    assert records[1]["job_id"] == job_id
    assert any(f["function"] == "run_batch" for f in records[1]["code_locations"])
    assert "private" not in caplog.text


def test_saved_diagnostic_projection_rejects_prose_and_keeps_original_identity():
    from services.export_failure_diagnostics import recovery_failure_context, safe_failure_record

    job = str(uuid4())
    first = failure_record(ValueError("PASSWORD=secret"), job_id=job, stage="snapshot")
    first["message"] = "private cells"
    first["code_locations"] = [dict(file="private-secret.py", function="leak", line=1)]
    safe = safe_failure_record(first)
    assert "secret" not in json.dumps(safe) and "private" not in json.dumps(safe)
    assert safe["code_locations"] == []
    context = recovery_failure_context(dict(JobID=job), dict(first_failure=first))
    assert context["original_fault"] == "recorded"
    assert "retained input" in context["summary"]
    assert context["original"]["diagnostic_id"] == first["diagnostic_id"]
    other = recovery_failure_context(dict(JobID=str(uuid4())), dict(first_failure=first))
    assert other["original_fault"] == "not_recorded"


def test_historical_failure_is_not_invented_or_treated_as_corrected():
    from services.export_failure_diagnostics import recovery_failure_context

    context = recovery_failure_context(dict(JobID=str(uuid4())), {})
    assert context["original_fault"] == "not_recorded"
    assert "does not identify" in context["summary"]
