"""Explicit refresh approval preserves historical deduplication and selected inputs."""

from copy import deepcopy
import json
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.dal.source_update_dal import CONTEXT_COLUMNS, INPUT_COLUMNS, update_hash
from kvk.models.new_source_reporting import CALCULATION_VERSION
from kvk.services.source_admin_review_service import SourceAdminReviewService
from tests.test_kvk_source_admin import ACCESS, ADMIN, NOW, UPLOADER
from tests.test_kvk_source_admin_review import Reviews


def repository():
    repo = Reviews()
    context = repo.context
    context["base_update_id"] = str(uuid4())
    context["aggregate"] = dict(ReportID=str(uuid4()), RevisionID=str(uuid4()))
    selected = dict(
        UpdateID=context["base_update_id"],
        PublicationID=str(uuid4()),
        PublicSelectionVersion=1,
        CalculationVersion="snapshot_report_calculation_v2",
        **context["config"],
        StartRevisionID=context["scans"]["17"],
        EndRevisionID=context["scans"]["18"],
        AggregateRevisionID=context["aggregate"]["RevisionID"],
        CoverageStartUTC="2026-09-01T00:00:00+00:00",
        CoverageEndUTC="2026-09-02T00:00:00+00:00",
        AsOfUTC="2026-09-02T00:00:00+00:00",
    )
    repo.refresh_context = lambda *args: deepcopy(selected)
    return repo, selected


def test_refresh_is_owner_review_with_derived_inputs_and_no_selection(monkeypatch):
    repo, selected = repository()
    repo.refresh_preview_inputs = lambda *args: (None, None)
    monkeypatch.setattr(
        "kvk.services.source_calculation_refresh_service.preview",
        lambda *_: dict(
            eligible_players=2,
            ratios_available_before=1,
            ratios_available_after=2,
            ratio_values_changed=1,
            result_hash="a" * 64,
        ),
    )
    service = SourceAdminReviewService(ACCESS, repo, lambda: NOW)
    row = service.prepare_refresh(ADMIN, season=16, period="fight:two", reason="Recalculate ratios")
    assert row["ReviewState"] == "pending" and row["outcome"] is None
    payload = row["payload"]
    assert payload["calculation_refresh"] == selected
    proof = json.loads(payload["context"]["confirmation_json"])
    assert proof["calculation_refresh"]["to_calculation"] == CALCULATION_VERSION
    assert proof["counterpart"]["revision_id"] == selected["AggregateRevisionID"]
    assert payload["end_scan_id"] == 18
    assert "Confirm selects" in service.summary(row)
    assert service.read(ADMIN, row["ReviewID"])["payload"] == payload


@pytest.mark.parametrize("fault", ["permission", "version", "config", "scan", "request", "weights"])
def test_refresh_refuses_changed_context_or_already_current(fault):
    repo, selected = repository()
    actor = ADMIN
    if fault == "permission":
        actor = UPLOADER
    if fault == "version":
        selected["CalculationVersion"] = CALCULATION_VERSION
    if fault == "config":
        repo.context["config"]["ConfigVersionID"] = str(uuid4())
    if fault == "scan":
        repo.context["scans"]["18"] = str(uuid4())
    if fault == "request":
        repo.context["request_id"] = str(uuid4())
    if fault == "weights":
        repo.context["current_weights"] = True
    with pytest.raises((PermissionError, SourceConflict)):
        SourceAdminReviewService(ACCESS, repo, lambda: NOW).prepare_refresh(
            actor, season=16, period="fight:two", reason="Recalculate ratios"
        )
    assert not repo.saved


def test_refresh_hash_preserves_all_old_hashes_and_deduplicates_same_refresh():
    record = dict.fromkeys((*CONTEXT_COLUMNS, *INPUT_COLUMNS), "fixture")
    before = digest(record)
    record["ConfirmationJson"] = '{"action":"correct","reason":"historical"}'
    assert update_hash(record) == before
    record["BaseUpdateID"] = str(uuid4())
    refresh = dict(
        base_update_id=record["BaseUpdateID"],
        base_publication_id=str(uuid4()),
        from_calculation="snapshot_report_calculation_v2",
        to_calculation=CALCULATION_VERSION,
    )
    record["ConfirmationJson"] = json.dumps(dict(action="correct", calculation_refresh=refresh))
    after = update_hash(record)
    assert after != before
    replay = dict(record, UpdateID=str(uuid4()), ConfirmedBy="another admin")
    assert update_hash(replay) == after
    refresh["to_calculation"] = "unapproved-version"
    record["ConfirmationJson"] = json.dumps(dict(action="correct", calculation_refresh=refresh))
    with pytest.raises(SourceConflict):
        update_hash(record)


def test_preview_counts_ratio_repairs_and_rejects_other_metric_changes():
    from kvk.dal.new_source_publication_dal import result_values
    from kvk.services.new_source_calculation import calculate_period
    from kvk.services.new_source_window_resolver import resolve_window
    from kvk.services.source_calculation_refresh_service import preview
    from tests.kvk_source_fixtures import calculation_config, worked_calculation_inputs

    b0, start, middle, end = worked_calculation_inputs()
    data = dict(config=calculation_config(), observations=(start, middle, end), b0=b0)
    calculation = calculate_period(resolve_window(data["config"], data["observations"]), b0)
    rows = [result_values(player) for player in calculation.players]
    row = next(r for r in rows if r["dkp_power_ratio"] is not None)
    row["dkp_power_ratio"] = None
    states = json.loads(row["FieldStatusJson"])
    states["dkp_power_ratio"] = "invalid"
    row["FieldStatusJson"] = json.dumps(states)
    result = preview(data, rows)
    assert result["ratio_values_changed"] == result["ratio_states_changed"] == 1
    assert result["ratios_available_after"] == result["ratios_available_before"] + 1
    assert result["other_metrics_unchanged"] is True
    row["dkp"] += 1
    with pytest.raises(SourceConflict, match="more than DKP/power"):
        preview(data, rows)
