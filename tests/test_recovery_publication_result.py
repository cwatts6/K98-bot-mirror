from copy import deepcopy
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from services.recovery_publication_result import publication_result
from tests.test_guided_recovery import setup
from ui.views.recovery_view import incident_embed


def fixture():
    service, adapter, store, row = setup()
    row["SourceKind"] = "export_job"
    row["State"] = "resolved"
    row["evidence"].update(outcome="confirmed")
    now = datetime(2026, 10, 20, 17, 52)
    action = dict(
        ActionID=str(uuid4()),
        State="verified",
        CreatedUTC=now,
        UpdatedUTC=now + timedelta(seconds=793),
    )
    row["evidence"]["publication_receipt"] = dict(
        actor=f"recovery:{action['ActionID']}", proof_id=str(uuid4()), state="confirmed"
    )
    return row, action


@pytest.mark.parametrize("outcome", ["confirmed", "damaged", "absent"])
def test_saved_result_has_exact_proof_outcome_and_real_completion_time(outcome):
    row, action = fixture()
    row["evidence"]["publication_receipt"]["state"] = outcome
    result = publication_result(row, action)
    assert result["outcome"] == outcome
    assert result["completed_utc"] == "2026-10-20T18:05:13+00:00"
    assert result["duration_seconds"] == 793
    row["publication_check"] = result
    embed = incident_embed(row)
    assert embed.title == "Published output check"
    assert any(f.name == "Publication check outcome" and f.value == outcome for f in embed.fields)
    assert embed.color.value == (0x2ECC71 if outcome == "confirmed" else 0xF1C40F)
    assert "not a fresh check" not in embed.description


@pytest.mark.parametrize(
    "state,expected",
    [
        ("dispatched", "pending"),
        ("unknown", "pending"),
        ("not_applied", "not_verified"),
    ],
)
def test_newer_unsuccessful_check_never_borrows_old_success(state, expected):
    row, action = fixture()
    action.update(ActionID=str(uuid4()), State=state)
    result = publication_result(row, action)
    assert result["outcome"] == expected
    if expected == "pending":
        assert result["completed_utc"] is None and result["duration_seconds"] is None
    row["publication_check"] = result
    assert incident_embed(row).color.value == 0xF1C40F


@pytest.mark.parametrize("missing", ["actor", "proof_id", "state"])
def test_verified_action_needs_its_own_settled_proof(missing):
    row, action = fixture()
    row["evidence"]["publication_receipt"].pop(missing)
    assert publication_result(row, action)["outcome"] == "unverified"


def test_historical_delivery_alone_is_not_a_fresh_check():
    row, _ = fixture()
    assert publication_result(row, None) is None
    row["SourceKind"] = "stats_import"
    assert publication_result(row, fixture()[1]) is None


def test_reopened_service_uses_saved_latest_action_without_provider_call():
    service, adapter, store, _ = setup()
    row, action = fixture()
    store.row = deepcopy(row)
    store.actions = [dict(action, ActionKind="verify_publication")]
    presented = service.present(store.get(row["IncidentID"]))
    assert presented["publication_check"]["outcome"] == "confirmed"
    assert not adapter.calls
    store.actions.append(
        dict(action, ActionID=str(uuid4()), State="not_applied", ActionKind="verify_publication")
    )
    assert (
        service.present(store.get(row["IncidentID"]))["publication_check"]["outcome"]
        == "not_verified"
    )


def test_report_preserves_saved_check_and_does_not_reassure_after_failure():
    from services.recovery_report import incident_report

    service, _, _, _ = setup()
    row, action = fixture()
    action["State"] = "not_applied"
    row["publication_check"] = publication_result(row, action)
    report = incident_report(service, row)
    assert report["publication_check"]["outcome"] == "not_verified"
    assert "did not establish" in report["next_step"]


@pytest.mark.parametrize("fails", [False, True])
def test_phase_timing_preserves_failure_and_never_logs_private_exception(
    caplog, monkeypatch, fails
):
    import logging

    from services import export_reconciliation_service as module

    times = iter([100.0, 272.5])
    monkeypatch.setattr(module, "monotonic", lambda: next(times))
    with caplog.at_level(logging.INFO, logger=module.__name__):
        if fails:
            with pytest.raises(ValueError, match="private"):
                with module.publication_phase("sealed_response_replay"):
                    raise ValueError("private spreadsheet contents")
        else:
            with module.publication_phase("sealed_response_replay"):
                pass
    assert "duration_ms=172500" in caplog.text
    assert f"completed={not fails}" in caplog.text
    assert "private spreadsheet" not in caplog.text
