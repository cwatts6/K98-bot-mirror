"""Probe scheduling and held-read recovery ship together under exact pins."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_report_cache_transition_pins_complete_runtime():
    item = next(
        t for t in updater.reviewed_transitions() if t["id"] == "fresh_report_cache_diagnostics_v1"
    )
    assert {m["path"] for m in item["members"]} == updater.REPORT_CACHE_TRANSITION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_report_cache_transition_refuses_partial_or_unreviewed_bundle(
    tmp_path, monkeypatch, change
):
    item = deepcopy(
        next(
            t
            for t in updater.reviewed_transitions()
            if t["id"] == "fresh_report_cache_diagnostics_v1"
        )
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_report_cache"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
