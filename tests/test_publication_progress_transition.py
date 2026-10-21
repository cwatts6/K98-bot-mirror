"""The new progress protocol ships only as its complete reviewed bundle."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_progress_transition_pins_complete_runtime():
    item = next(t for t in updater.reviewed_transitions() if t["id"] == "publication_progress_v1")
    assert {m["path"] for m in item["members"]} == updater.PUBLICATION_PROGRESS_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        assert updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n")) == next(
            (
                m["after_sha256"]
                for t in reversed(updater.reviewed_transitions())
                if t["id"]
                in {
                    "guided_rollover_v1",
                    "publication_timing_v1",
                    "probe_busy_recovery_v1",
                    "configuration_read_request_v1",
                    "fresh_report_cache_diagnostics_v1",
                    "report_cache_handoff_v1",
                    "publication_result_v1",
                }
                for m in t["members"]
                if m["path"] == member["path"]
            ),
            member["after_sha256"],
        )


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_progress_transition_refuses_partial_or_unreviewed_bundle(tmp_path, monkeypatch, change):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "publication_progress_v1")
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_progress"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
