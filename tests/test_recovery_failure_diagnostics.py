"""Persisted recovery errors survive reconciliation without exposing SQL prose."""

import json
from uuid import uuid4

import pyodbc
import pytest

from services.recovery_failure_diagnostics import action_failure, action_result
from tests.test_guided_recovery import execute, setup


def test_sql_permission_failure_survives_not_applied_readback(caplog):
    service, _, store, row = setup()
    adapter = service.adapters[row["SourceKind"]]

    def fail(*args, **kwargs):
        raise pyodbc.ProgrammingError(
            "42000", "SECRET database password SQL denied (229) (SQLExecDirectW)"
        )

    adapter.execute = fail
    adapter.reconcile = lambda *_: "not_applied"
    current = execute(service, row)
    result = json.loads(store.actions[0]["ResultJson"])
    assert result["verification"] == "not_applied"
    assert result["failure"]["sql_numbers"] == [229]
    assert result["failure"]["sqlstates"] == ["42000"]
    assert "SQL denied permission (229)" in current["last_repair"]["explanation"]
    assert "SECRET" not in json.dumps(current, default=str) + caplog.text
    assert service.refresh(row["IncidentID"])["last_repair"] == current["last_repair"]


def test_lost_ack_failure_is_not_presented_as_failed_after_verification():
    service, dal, _, row = setup()
    dal.lose_ack = True
    current = execute(service, row)
    assert current["last_repair"]["state"] == "verified"
    assert "subsequently verified" in current["last_repair"]["explanation"]


@pytest.mark.parametrize(
    "result", [None, "bad json", "[]", "null", '{"failure": {"secret": "unsafe"}}']
)
def test_malformed_persisted_result_has_no_raw_fallback(result):
    assert (
        action_result(dict(ActionID=str(uuid4()), State="not_applied", ResultJson=result)) is None
    )


def test_failure_must_belong_to_the_same_action_and_projection_ignores_extra_keys():
    action = str(uuid4())
    failure = action_failure(ValueError("secret"), action)
    failure["secret"] = "unsafe"
    row = dict(ActionID=action, State="not_applied", ResultJson=json.dumps(dict(failure=failure)))
    assert "unsafe" not in json.dumps(action_result(row))
    row["ActionID"] = str(uuid4())
    assert action_result(row) is None


def test_report_and_embed_show_reconciled_failure_without_retrying():
    from services.recovery_report import incident_report
    from ui.views.recovery_view import incident_embed

    service, _, store, row = setup()
    adapter = service.adapters[row["SourceKind"]]

    def fail(*args, **kwargs):
        raise pyodbc.ProgrammingError("42000", "private SQL (229)")

    adapter.execute = fail
    adapter.reconcile = lambda *_: "not_applied"
    current = execute(service, row)
    report = incident_report(service, current)
    assert report["last_repair"]["failure"]["sql_numbers"] == [229]
    assert "corrective release" in report["next_step"]
    fields = incident_embed(current).to_dict()["fields"]
    assert any(f["name"] == "Last repair result" and "229" in f["value"] for f in fields)
    assert len(store.actions) == 1
