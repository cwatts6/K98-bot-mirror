from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from scripts import validate_k98_update_compatibility as compatibility
from scripts.prepare_k98_update import (
    APPLICATION_METHODS,
    TOOL_SOURCE_PATHS,
    check_application_change,
    check_source_only,
    sha256,
    source_plan,
)
from scripts.validate_k98_update_compatibility import classify

BEFORE, AFTER = "a" * 40, "b" * 40
PATH = "services/export_coordination_dal.py"
OLD = b"""import json
CONTRACT = 1
class ExportCoordinationDAL:
    def enqueue(self, spec, *, preparation_id=None):
        return spec
    def verify_contract(self, value):
        return value == CONTRACT
"""
NEW = OLD.replace(b"return spec", b"self.check_intent_weights(spec)\n        return spec") + b"""
    def check_intent_weights(self, intent):
        return intent
"""


def installed_manifest(policy="a" * 64):
    files = {path.rsplit("/", 1)[1]: "a" * 64 for path in TOOL_SOURCE_PATHS}
    files.update({"EmptyGitConfig.txt": sha256(b""), "prepare_k98_update.py": policy})
    import hashlib
    from pathlib import Path

    from scripts.verify_k98_update_pair import build_contract_archive

    files["contract_verifier.zip"] = hashlib.sha256(
        build_contract_archive(Path(__file__).resolve().parents[1])
    ).hexdigest()
    return {"version": 1, "files": files}


def test_application_change_retains_exact_source_and_policy_hashes():
    previous = {"AutomaticStartupPolicy.json": {"source_hashes": {PATH: sha256(OLD)}}}
    preserved = deepcopy(previous)
    plan, payload = source_plan(
        previous, BEFORE, AFTER, [PATH], lambda commit, path: OLD if commit == BEFORE else NEW
    )
    assert previous == preserved
    assert plan["new_pins"][PATH] == sha256(NEW)
    assert plan["source_members"][0]["before_sha256"] == [sha256(OLD)]
    assert payload[PATH] == NEW


@pytest.mark.parametrize("path", APPLICATION_METHODS)
def test_supported_application_bodies_allow_successive_changes(path):
    cls, methods = APPLICATION_METHODS[path]
    method = next(iter(methods))
    old = f"class {cls}:\n    def {method}(self):\n        pass\n".encode()
    new = old.replace(b"pass", b"print('not executed')")
    check_application_change(path, old, new)
    check_application_change(path, new, new.replace(b"not executed", b"next release"))


@pytest.mark.parametrize(
    "bad",
    [
        NEW.replace(b"CONTRACT = 1", b"CONTRACT = 2"),
        NEW.replace(b"import json", b"import os"),
        NEW.replace(b"value == CONTRACT", b"True"),
        NEW.replace(b"preparation_id=None", b"preparation_id=True"),
        NEW.replace(b"class ExportCoordinationDAL:", b"class ExportCoordinationDAL(object):"),
        NEW.replace(b"    def enqueue", b"    @staticmethod\n    def enqueue"),
        NEW.replace(b"    def enqueue", b"    async def enqueue"),
        NEW.replace(b"def enqueue", b"def renamed"),
        NEW.replace(b"self, intent", b"self, intent=None"),
        NEW.replace(
            b"    def check_intent_weights", b"    @property\n    def check_intent_weights"
        ),
        NEW + b"    def enqueue(self, spec, *, preparation_id=None): pass\n",
        NEW + b"class ExportCoordinationDAL: pass\n",
        NEW + b"ExportCoordinationDAL.enqueue = lambda *a: None\n",
        NEW + b"    def unknown_method(self): pass\n",
        NEW.replace(b"return intent", b"break"),
        b"invalid source !",
        None,
        b"",
    ],
)
def test_unknown_or_protected_changes_are_refused(bad):
    with pytest.raises(ValueError):
        check_application_change(PATH, OLD, bad)


def test_added_helper_cannot_be_removed_in_later_update():
    with pytest.raises(ValueError, match="Protected application contract changed"):
        check_application_change(PATH, NEW, OLD)


def test_source_names_alone_never_authorize_mixed_modules():
    with pytest.raises(ValueError, match="non-routine"):
        check_source_only([PATH])


@pytest.mark.parametrize(
    "damage", [None, "before", "after", "missing_peer", "peer", "unregistered"]
)
def test_protected_application_change_needs_complete_installed_transition(monkeypatch, damage):
    from scripts import prepare_k98_update as update

    peer = "services/export_recovery_service.py"
    changed = OLD.replace(b"value == CONTRACT", b"value != CONTRACT")
    before = {PATH: OLD, peer: b"old peer\n"}
    after = {PATH: changed, peer: b"new peer\n"}
    transitions = [
        dict(
            id="fixture",
            members=[
                dict(path=p, before_sha256=sha256(before[p]), after_sha256=sha256(after[p]))
                for p in before
            ],
        )
    ]
    monkeypatch.setattr(update, "reviewed_transitions", lambda: transitions)
    if damage == "before":
        before[PATH] += b"# changed\n"
    elif damage == "after":
        after[PATH] += b"# changed\n"
    elif damage == "missing_peer":
        after.pop(peer)
    elif damage == "peer":
        after[peer] = before[peer]
    elif damage == "unregistered":
        transitions.clear()
    read = lambda commit, path: (before if commit == BEFORE else after).get(path)
    if damage:
        with pytest.raises(ValueError):
            check_source_only([PATH, peer], read_blob=read, before=BEFORE, target=AFTER)
    else:
        check_source_only([PATH, peer], read_blob=read, before=BEFORE, target=AFTER)
        previous = {
            "AutomaticStartupPolicy.json": {
                "source_hashes": {p: sha256(raw) for p, raw in before.items()}
            }
        }
        plan, payload = source_plan(previous, BEFORE, AFTER, [PATH, peer], read)
        assert payload == after
        assert plan["new_pins"][PATH] == sha256(changed)
        with pytest.raises(ValueError, match="Incomplete reviewed protocol transition"):
            source_plan(previous, BEFORE, AFTER, [PATH], read)
        # Registering an exact protected transition does not disable subsequent
        # ordinary enqueue-body edits under the existing application policy.
        check_source_only(
            [PATH], read_blob=lambda c, p: OLD if c == BEFORE else NEW, before=BEFORE, target=AFTER
        )


def test_application_compatibility_does_not_bypass_predecessor_authentication():
    previous = {"AutomaticStartupPolicy.json": {"source_hashes": {PATH: "f" * 64}}}
    with pytest.raises(ValueError, match="Installed policy does not match"):
        source_plan(
            previous, BEFORE, AFTER, [PATH], lambda commit, path: OLD if commit == BEFORE else NEW
        )


def test_classification_reports_every_blocker_and_tool_upgrade():
    paths = [PATH, "core/export_release_seed.py", "requirements.txt"]
    result = classify(BEFORE, AFTER, paths, lambda c, p: OLD if c == BEFORE else NEW)
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"
    assert len(result["blockers"]) == 2
    assert (
        classify(BEFORE, AFTER, [PATH], lambda c, p: OLD if c == BEFORE else NEW)["classification"]
        == "ROUTINE_COMPATIBLE"
    )
    tool = "scripts/prepare_k98_update.py"
    assert (
        classify(BEFORE, AFTER, [tool], lambda c, p: b"old" if c == BEFORE else b"new")[
            "classification"
        ]
        == "UPDATER_UPGRADE_REQUIRED"
    )
    installed = installed_manifest(sha256(b"new"))
    assert (
        classify(BEFORE, AFTER, [tool], lambda c, p: b"old" if c == BEFORE else b"new", installed)[
            "classification"
        ]
        == "ROUTINE_COMPATIBLE"
    )
    assert classify(BEFORE, AFTER, [tool], lambda *_: None, installed)["blockers"]


def test_target_cannot_supply_a_compatibility_exemption():
    result = classify(
        BEFORE, AFTER, ["services/export_unknown.py"], lambda *_: json.dumps({"compatible": True})
    )
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"


def test_candidate_policy_is_not_mistaken_for_installed_capability():
    result = classify(
        BEFORE,
        AFTER,
        [PATH],
        lambda c, p: OLD if c == BEFORE else NEW,
        installed_manifest(),
        policy_sha256="b" * 64,
    )
    assert result["classification"] == "UPDATER_UPGRADE_REQUIRED"
    assert result["updater_members"] == ["scripts/prepare_k98_update.py"]


@pytest.mark.parametrize("damage", ["version", "boolean", "missing", "extra", "hash", "fields"])
def test_invalid_installed_manifest_cannot_report_routine_compatibility(damage):
    installed = installed_manifest()
    if damage == "version":
        installed["version"] = 2
    elif damage == "boolean":
        installed["version"] = True
    elif damage == "missing":
        del installed["files"]["Deploy-K98Release.ps1"]
    elif damage == "extra":
        installed["files"]["unknown.py"] = "a" * 64
    elif damage == "hash":
        installed["files"]["Deploy-K98Release.ps1"] = "invalid"
    else:
        installed["unknown"] = True
    with pytest.raises(ValueError, match="supported installed-tool manifest"):
        classify(BEFORE, AFTER, [], lambda *_: None, installed, policy_sha256="a" * 64)


def test_supported_legacy_installed_manifest_reports_upgrade():
    installed = json.loads(Path("tests/fixtures/updater_installed_20261009.json").read_bytes())
    result = classify(
        BEFORE,
        AFTER,
        ["scripts/prepare_k98_release.py"],
        lambda commit, path: None if commit == BEFORE else b"new",
        installed,
        policy_sha256="b" * 64,
    )
    assert result["classification"] == "UPDATER_UPGRADE_REQUIRED"
    assert result["blockers"] == []
    assert "scripts/prepare_k98_release.py" in result["updater_members"]


def test_legacy_inventory_requires_upgrade_even_with_matching_policy():
    installed = installed_manifest()
    del installed["files"]["prepare_k98_release.py"]
    del installed["files"]["contract_verifier.zip"]
    del installed["files"]["k98_update_transitions.json"]
    for name in ("p0a_release.py", "p0a_release_spec.json", "recovery_release_seed.py"):
        del installed["files"][name]
    result = classify(BEFORE, AFTER, [], lambda *_: None, installed, policy_sha256="a" * 64)
    assert result["classification"] == "UPDATER_UPGRADE_REQUIRED"


@pytest.mark.parametrize("mode", ["120000", "160000", "100755", "100644"])
def test_cli_checks_all_changed_object_modes_and_distinct_blocker_exit(monkeypatch, capsys, mode):
    monkeypatch.setattr(sys, "argv", ["compatibility", "--base", BEFORE, "--head", AFTER])

    def git_output(command, **kwargs):
        args = command[2:]
        if args[0] == "rev-parse":
            return (args[-1].split("^")[0] + "\n").encode()
        if args[0] == "diff":
            return b"ordinary.py\0"
        if args[0] == "ls-tree":
            if "--name-only" in args:
                return b"ordinary.py\0"
            file_mode = "100644" if args[2] == BEFORE else mode
            kind = "commit" if file_mode == "160000" else "blob"
            return f"{file_mode} {kind} {'c' * 40}\tordinary.py\0".encode()
        if args[0] == "cat-file":
            return b"4\n" if args[1] == "-s" else b"same"
        raise AssertionError(command)

    monkeypatch.setattr(compatibility.subprocess, "check_output", git_output)
    assert compatibility.main() == compatibility.COORDINATED_RELEASE_EXIT == 3
    result = json.loads(capsys.readouterr().out)
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"
    assert (
        "Ordinary Git blob" in result["blockers"][0]
        if mode in ("120000", "160000")
        else "Changed-path inventory" in result["blockers"][0]
    )


def test_cli_unexpected_git_failure_does_not_report_a_classification(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["compatibility", "--base", BEFORE])

    def fail(*args, **kwargs):
        raise compatibility.subprocess.CalledProcessError(1, "git")

    monkeypatch.setattr(compatibility.subprocess, "check_output", fail)
    with pytest.raises(compatibility.subprocess.CalledProcessError):
        compatibility.main()
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "paths,inventory",
    [
        (["pkg/a.py", "PKG/A.py"], []),
        (["pkg/new.py"], ["PKG/unchanged.py"]),
        (["pkg/a.py", "pkg/A.py"], []),
    ],
)
def test_case_aliases_across_changed_and_retained_inventory_require_coordination(paths, inventory):
    result = classify(
        BEFORE,
        AFTER,
        paths,
        lambda c, p: b"old" if c == BEFORE else b"new",
        inventory_paths=inventory,
    )
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"
    assert any("Case-colliding" in blocker for blocker in result["blockers"])
