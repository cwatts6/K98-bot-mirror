"""The installed tool accepts only the complete named monitor/admission transition."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import historical_runtime_hash


def test_monitor_admission_transition_pins_every_runtime_member():
    bundle = next(
        t for t in updater.reviewed_transitions() if t["id"] == "monitor_admission_closeout_v1"
    )
    assert {m["path"] for m in bundle["members"]} == updater.MONITOR_ADMISSION_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in bundle["members"]:
        assert historical_runtime_hash(root, member["path"]) == next(
            (
                m["after_sha256"]
                for t in reversed(updater.reviewed_transitions())
                if t["id"]
                in {
                    "guided_rollover_v1",
                    "publication_timing_v1",
                    "configuration_intent_replay_v1",
                    "publication_detail_v1",
                    "publication_readback_batches_v1",
                    "evidence_backup_collection_v1",
                    "configuration_pipeline_continuation_v1",
                    "monitor_admission_closeout_v1",
                    "startup_cache_completion_v1",
                    "guided_replacement_release_v1",
                    "guided_publication_recovery_v1",
                    "publication_progress_v1",
                    "probe_busy_recovery_v1",
                    "configuration_read_request_v1",
                    "fresh_report_cache_diagnostics_v1",
                    "report_cache_handoff_v1",
                    "publication_result_v1",
                    "publication_result_handoff_v1",
                }
                for m in t["members"]
                if m["path"] == member["path"]
            ),
            member["after_sha256"],
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed"])
def test_monitor_admission_transition_cannot_authorize_a_partial_or_foreign_bundle(
    tmp_path, monkeypatch, damage
):
    bundle = deepcopy(
        next(
            t for t in updater.reviewed_transitions() if t["id"] == "monitor_admission_closeout_v1"
        )
    )
    if damage == "missing":
        bundle["members"].pop()
    elif damage == "extra":
        bundle["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        bundle["id"] = "foreign_completion_v1"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[bundle]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
