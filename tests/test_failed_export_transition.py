import json

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
    # This historical bundle's installed image can have a reviewed successor.
    # Use synthetic pre/post images to test matching in shallow CI without
    # incorrectly treating today's checkout as the historical target image.
    # Real registry/current-runtime pins are checked independently.
    target = {m["path"]: b"new\n" for m in transition["members"]}
    before = {m["path"]: b"old\n" if m["before_sha256"] else None for m in transition["members"]}
    for member in transition["members"]:
        raw = before[member["path"]]
        member["before_sha256"] = update.sha256(raw) if raw else None
        member["after_sha256"] = update.sha256(target[member["path"]])
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
