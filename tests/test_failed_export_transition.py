import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as update


def policy():
    return next(t for t in update.reviewed_transitions() if t["id"] == "failed_export_closeout_v1")


def install_fixture(monkeypatch, tmp_path, transition):
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[transition])), encoding="utf-8"
    )
    monkeypatch.setattr(update, "__file__", str(tmp_path / "prepare_k98_update.py"))


@pytest.mark.parametrize("damage", ["missing", "other_script", "wrong_id", "duplicate"])
def test_authority_exception_requires_exact_complete_named_bundle(monkeypatch, tmp_path, damage):
    transition = policy()
    if damage == "missing":
        transition["members"].pop()
    elif damage == "other_script":
        transition["members"][0]["path"] = "scripts/run_bot.py"
    elif damage == "wrong_id":
        transition["id"] = "other_transition"
    else:
        transition["members"].append(transition["members"][0])
    install_fixture(monkeypatch, tmp_path, transition)
    with pytest.raises(ValueError):
        update.reviewed_transitions()


@pytest.mark.parametrize("damage", [None, "changed_target", "changed_predecessor", "missing_peer"])
def test_exact_bundle_checks_every_reviewed_source_member(monkeypatch, damage):
    transition = policy()
    root = Path(update.__file__).resolve().parents[1]
    target = {m["path"]: (root / m["path"]).read_bytes() for m in transition["members"]}
    # Synthetic preimages exercise matching without relying on mirror Git history
    # in private or shallow CI checkouts. Real target pins remain independently
    # checked by the existing registry/current-runtime contract tests.
    before = {m["path"]: b"old\n" if m["before_sha256"] else None for m in transition["members"]}
    for member in transition["members"]:
        raw = before[member["path"]]
        member["before_sha256"] = update.sha256(raw) if raw else None
    monkeypatch.setattr(update, "reviewed_transitions", lambda: [transition])
    if damage == "changed_target":
        target["scripts/run_export_authority.py"] += b"\n# unreviewed\n"
    elif damage == "changed_predecessor":
        before["scripts/run_export_authority.py"] += b"\n# drift\n"
    elif damage == "missing_peer":
        target.pop("services/failed_export_closeout_dal.py")
    read = lambda rev, path: (before if rev == "before" else target).get(path)
    if damage:
        with pytest.raises(ValueError, match="transition"):
            update.check_protocol_transition(
                "scripts/run_export_authority.py", read, "before", "after"
            )
    else:
        assert (
            update.check_protocol_transition(
                "scripts/run_export_authority.py", read, "before", "after"
            )
            == update.FAILED_EXPORT_TRANSITION_PATHS
        )
        previous = {"AutomaticStartupPolicy.json": {"source_hashes": {}}}
        with pytest.raises(ValueError, match="transition"):
            update.source_plan(
                previous,
                "a" * 40,
                "b" * 40,
                ["scripts/run_export_authority.py"],
                lambda rev, path: read("before" if rev == "a" * 40 else "after", path),
            )


def test_unreviewed_authority_source_is_still_refused():
    with pytest.raises(ValueError, match="transition"):
        update.check_source_only(
            ["scripts/run_export_authority.py"],
            read_blob=lambda *_: b"unreviewed\n",
            before="before",
            target="after",
        )
