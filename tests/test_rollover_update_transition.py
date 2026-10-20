"""Rollover exposure and responsive authority proofs require one exact transition."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_guided_rollover_pins_complete_runtime():
    item = next(t for t in updater.reviewed_transitions() if t["id"] == "guided_rollover_v1")
    assert {m["path"] for m in item["members"]} == updater.ROLLOVER_GUIDED_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        source = root / member["path"]
        if member["path"] == "services/rollover_replacement_authority.py" and not source.exists():
            continue  # Scrubbed mirror; exact source is checked in the private checkout.
        expected = member["after_sha256"]
        for transition in updater.reviewed_transitions():
            if transition["id"] == "publication_timing_v1":
                for successor in transition["members"]:
                    if successor["path"] == member["path"]:
                        assert successor["before_sha256"] == expected
                        expected = successor["after_sha256"]
        assert updater.sha256(source.read_bytes().replace(b"\r\n", b"\n")) == expected
        assert member["before_sha256"] and member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_guided_rollover_rejects_incomplete_or_foreign_transition(tmp_path, monkeypatch, change):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "guided_rollover_v1")
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "unreviewed_rollover"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
