from copy import deepcopy
import json
from pathlib import PureWindowsPath

import pytest

from scripts.prepare_k98_update import (
    check_source_only,
    ordinary_path,
    release_seed,
    sha256,
    source_plan,
)
from services.export_execution_protocol import encode
from tests.test_export_release_seed import predecessor

BEFORE = "a" * 40
AFTER = "b" * 40


@pytest.mark.parametrize(
    "path",
    [
        "assets/helper.py",
        "data/helper.py",
        "downloads/helper.py",
        "artifacts/helper.py",
        "logs/helper.py",
        "smoke_artifacts/helper.py",
        "nested/docs/helper.py",
        "nested/tests/helper.py",
        "nested/.hidden/helper.py",
        "Assets/helper.py",
        "core/HELPER.PY",
        "nested/venv/helper.py",
        "core/.helper.py",
        "core/note.txt",
    ],
)
def test_update_pins_match_actual_bootstrap_inventory(tmp_path, path):
    from scripts.run_export_authority import code_files

    member = tmp_path / path
    member.parent.mkdir(parents=True, exist_ok=True)
    member.write_bytes(b"pass\n")
    previous = {"AutomaticStartupPolicy.json": {"source_hashes": {}}}
    plan, payload = source_plan(
        previous,
        BEFORE,
        AFTER,
        [path],
        lambda commit, name: b"pass\n" if commit == AFTER and name == path else None,
    )
    assert set(plan["new_pins"]) == code_files(tmp_path)
    assert payload[path] == b"pass\n"


def inventory(raw=b"old\r\n"):
    return {"AutomaticStartupPolicy.json": {"source_hashes": {"core/example.py": sha256(raw)}}}


def test_successive_updates_preserve_newlines_and_do_not_need_edited_inputs():
    previous = inventory()
    blobs = {(BEFORE, "core/example.py"): b"old\n", (AFTER, "core/example.py"): b"new\n"}
    first, payload = source_plan(
        previous, BEFORE, AFTER, ["core/example.py"], lambda *key: blobs.get(key)
    )
    assert payload["core/example.py"] == b"new\r\n"
    assert first["new_pins"]["core/example.py"] == sha256(b"new\r\n")
    next_commit = "c" * 40
    blobs[next_commit, "core/example.py"] = b"next\n"
    previous["AutomaticStartupPolicy.json"]["source_hashes"] = first["new_pins"]
    second, payload = source_plan(
        previous, AFTER, next_commit, ["core/example.py"], lambda *key: blobs.get(key)
    )
    assert payload["core/example.py"] == b"next\r\n"
    assert second["new_pins"]["core/example.py"] == sha256(b"next\r\n")


def test_add_delete_and_document_changes_have_exact_payload_and_pin_effects():
    blobs = {
        (BEFORE, "core/example.py"): b"old\n",
        (AFTER, "core/new.py"): b"new\n",
        (AFTER, "docs/operator.md"): b"instructions\n",
    }
    plan, payload = source_plan(
        inventory(b"old\n"),
        BEFORE,
        AFTER,
        ["core/example.py", "core/new.py", "docs/operator.md"],
        lambda *key: blobs.get(key),
    )
    assert plan["new_pins"] == {"core/new.py": sha256(b"new\n")}
    assert "core/example.py" not in payload
    assert next(member for member in plan["source_members"] if member["path"] == "core/example.py")[
        "deleted"
    ]
    assert payload["docs/operator.md"] == b"instructions\n"
    assert {member["path"] for member in plan["source_members"] if member["added"]} == {
        "core/new.py",
        "docs/operator.md",
    }


@pytest.mark.parametrize(
    "path",
    [
        "../escape.py",
        "C:/escape.py",
        "core\\escape.py",
        "core/CON.py",
        "core/name. ",
        "core/file:stream",
        "core//a.py",
        "venv/Scripts/python.exe",
        "core/../a.py",
    ],
)
def test_windows_path_ambiguity_is_refused(path):
    with pytest.raises(ValueError, match="path"):
        ordinary_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "requirements.txt",
        "requirements-dev.txt",
        "config/settings.json",
        "sql/migration.sql",
        "migrations/change.py",
        "pyproject.toml",
    ],
)
def test_non_source_updates_cannot_silently_enter_routine_mode(path):
    with pytest.raises(ValueError, match="non-source"):
        check_source_only([path])


@pytest.mark.parametrize(
    "path",
    [
        "core/helper.pyw",
        "core/helper.pyc",
        "core/helper.pyd",
        "core/helper.pyo",
        "core/helper.so",
        "core/helper.PYD",
        "core/__pycache__/helper.py",
        "core/__pycache__/note.txt",
        "__pycache__/note.txt",
    ],
)
def test_bootstrap_forbidden_artifacts_are_rejected_before_blob_reads(path):
    def forbidden_read(*_):
        pytest.fail("Forbidden release reached source preparation")

    with pytest.raises(ValueError, match="bootstrap-forbidden"):
        source_plan(inventory(), BEFORE, AFTER, [path], forbidden_read)


@pytest.mark.parametrize(
    "path",
    [
        "scripts/run_export_authority.py",
        "Scripts/RUN_EXPORT_AUTHORITY.PY",
        "core/export_release_seed.py",
        "core/export_process_pair.py",
        "core/export_automatic_pair.py",
        "core/export_process_identity.py",
        "core/export_startup_windows.py",
        "services/export_execution_protocol.py",
        "services/export_runtime_composition.py",
        "services/export_startup_reconciliation.py",
        "scripts/run_export_startup_issuer.py",
        "scripts/run_export_process_gate.py",
        "scripts/provision_export_process_pair.py",
        "scripts/prepare_k98_release.py",
        "scripts/prepare_k98_update.py",
        "scripts/verify_k98_update_pair.py",
        "scripts/package_k98_update_tool.py",
        "scripts/K98-SourceUpdate.ps1",
        "scripts/Deploy-K98Release.ps1",
        "scripts/Update-K98.ps1",
        "run_bot.py",
        "bot_config.py",
        "constants.py",
        "core/__init__.py",
        "services/__init__.py",
        "scripts/__init__.py",
    ],
)
def test_startup_contract_changes_are_rejected_before_blob_reads(path):
    def forbidden_read(*_):
        pytest.fail("Bootstrap contract change reached source preparation")

    with pytest.raises(ValueError, match=r"Startup/update contract change.*non-routine"):
        source_plan(inventory(), BEFORE, AFTER, [path], forbidden_read)


def test_predecessor_preparer_rejects_target_generator_and_consumer_changes():
    def forbidden_read(*_):
        pytest.fail("Target contract code must not run or supply seed inputs")

    with pytest.raises(ValueError, match="non-routine"):
        source_plan(
            inventory(),
            BEFORE,
            AFTER,
            ["core/export_release_seed.py", "scripts/run_export_startup_issuer.py"],
            forbidden_read,
        )


def test_ordinary_bot_and_queue_changes_remain_routine():
    check_source_only(
        ["DL_bot.py", "commands/kvk_admin.py", "services/legacy_export_snapshot_service.py"]
    )


def test_missing_diff_member_cannot_create_mixed_source_policy():
    blobs = {
        (BEFORE, "core/example.py"): b"old\n",
        (AFTER, "core/example.py"): b"new\n",
        (AFTER, "docs/note.md"): b"note",
    }
    with pytest.raises(ValueError, match="omitted"):
        source_plan(
            inventory(b"old\n"), BEFORE, AFTER, ["docs/note.md"], lambda *key: blobs.get(key)
        )


def test_unrecognized_installed_bytes_are_not_blessed_as_predecessor():
    with pytest.raises(ValueError, match="predecessor source"):
        source_plan(inventory(), BEFORE, AFTER, ["core/example.py"], lambda *_: b"unexpected")


def test_case_colliding_changes_are_refused():
    with pytest.raises(ValueError, match="Case-colliding"):
        source_plan(inventory(), BEFORE, AFTER, ["core/a.py", "core/A.py"], lambda *_: b"unused")


@pytest.mark.parametrize("path", ["Core/example.py", "core/EXAMPLE.py", "Core/new.py"])
def test_changed_paths_cannot_case_alias_retained_inventory(path):
    def forbidden_read(*_):
        pytest.fail("Case collision reached blob access")

    with pytest.raises(ValueError, match="Case-colliding source inventory"):
        source_plan(inventory(), BEFORE, AFTER, [path], forbidden_read)


@pytest.mark.parametrize("added", ["Docs/helper.py", "docs/OPERATOR.md"])
def test_cli_checks_unchanged_unpinned_git_paths_before_blob_acquisition(
    tmp_path, monkeypatch, added
):
    import subprocess
    import sys
    from types import SimpleNamespace

    from scripts.prepare_k98_update import main

    observation = tmp_path / "observation.json"
    observation.write_text(
        json.dumps(
            {
                "bindings": {
                    "before": BEFORE,
                    "target": AFTER,
                    "root": str(tmp_path),
                    "git_path": "git",
                },
                "seed": inventory(),
            }
        )
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare", "--observation", str(observation), "--output", str(tmp_path / "output")],
    )
    trees_read = []

    def git(args, **_kwargs):
        if "diff" in args:
            return SimpleNamespace(stdout=added.encode() + b"\0")
        if "ls-tree" in args:
            trees_read.append(args[-1])
            paths = ["core/example.py", "docs/operator.md"]
            if args[-1] == AFTER:
                paths.append(added)
            return SimpleNamespace(
                stdout=b"".join(
                    b"100644 blob " + b"a" * 40 + b" 1\t" + path.encode() + b"\0" for path in paths
                )
            )
        pytest.fail("Case collision reached blob acquisition")

    monkeypatch.setattr(subprocess, "run", git)
    with pytest.raises(ValueError, match="Case-colliding source inventory"):
        main()
    assert trees_read == [BEFORE, AFTER]
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "damage", [None, "oid", "kind", "size", "truncated", "separator", "suffix"]
)
def test_cli_batch_objects_are_verified_before_preparation(tmp_path, monkeypatch, damage):
    import subprocess
    import sys
    from types import SimpleNamespace

    from scripts import prepare_k98_update as updater

    observation = tmp_path / "observation.json"
    observation.write_text(
        json.dumps(
            {
                "bindings": {
                    "before": BEFORE,
                    "target": AFTER,
                    "root": str(tmp_path),
                    "git_path": "git",
                },
                "seed": inventory(),
            }
        )
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare", "--observation", str(observation), "--output", str(tmp_path / "output")],
    )
    contents = {BEFORE: b"old\n\x00", AFTER: b"new\n\x00"}
    oids = {BEFORE: b"a" * 40, AFTER: b"b" * 40}
    records = [oids[rev] + b" blob 5\n" + contents[rev] + b"\n" for rev in (BEFORE, AFTER)]
    batch = b"".join(records)
    if damage == "oid":
        batch = b"c" * 40 + batch[40:]
    elif damage == "kind":
        batch = batch.replace(b" blob ", b" tree ", 1)
    elif damage == "size":
        batch = batch.replace(b" blob 5\n", b" blob 6\n", 1)
    elif damage == "truncated":
        batch = batch[:-3]
    elif damage == "separator":
        batch = batch[:-1] + b"x"
    elif damage == "suffix":
        batch += b"extra"

    def git(args, **kwargs):
        if "diff" in args:
            return SimpleNamespace(stdout=b"core/example.py\0")
        if "ls-tree" in args:
            return SimpleNamespace(
                stdout=b"100644 blob " + oids[args[-1]] + b" 5\tcore/example.py\0"
            )
        assert "cat-file" in args
        assert kwargs["input"] == oids[BEFORE] + b"\n" + oids[AFTER] + b"\n"
        return SimpleNamespace(stdout=batch)

    prepared = []

    def prepare(_observation, _changes, read_blob, *_args, **_kwargs):
        prepared.append({rev: read_blob(rev, "core/example.py") for rev in (BEFORE, AFTER)})
        return {}

    monkeypatch.setattr(subprocess, "run", git)
    monkeypatch.setattr(updater, "prepare_update", prepare)
    if damage is None:
        updater.main()
        assert prepared == [contents]
    else:
        with pytest.raises(
            ValueError,
            match=r"Git object changed|Truncated Git object stream|Unexpected Git object stream suffix",
        ):
            updater.main()
        assert prepared == []


def test_two_successor_seeds_rebind_gate_without_reusing_release_identity(tmp_path, monkeypatch):
    original = predecessor(tmp_path, monkeypatch)
    previous = deepcopy(original)
    old = previous["AutomaticStartupPolicy.json"]
    gate = f"$policy='{PureWindowsPath(old['seed_plan']['path'])}'\n$policyHash='{sha256(encode(old))}'\n"
    histories = {old["state_directory"]}
    for value in ("a", "b"):
        payload = release_seed(previous, {"DL_bot.py": value * 64}, gate)
        gate = payload.pop("Start-ReviewedAutomaticStartup.ps1").decode()
        successor = {name: json.loads(raw) for name, raw in payload.items()}
        policy = successor["AutomaticStartupPolicy.json"]
        assert policy["state_directory"] not in histories
        histories.add(policy["state_directory"])
        assert policy["flags"] == original["AutomaticStartupPolicy.json"]["flags"]
        assert sha256(encode(policy)) in gate
        assert policy["predecessor"]["policy_sha256"] == sha256(
            encode(previous["AutomaticStartupPolicy.json"])
        )
        previous = successor
    assert len(histories) == 3


@pytest.mark.parametrize("scenario", ["ambiguous", "same", "cascade", "removed"])
def test_gate_digest_bindings_do_not_alias_or_cascade(tmp_path, monkeypatch, scenario):
    original = predecessor(tmp_path, monkeypatch)
    policy = original["AutomaticStartupPolicy.json"]
    gate = f"$policy='{PureWindowsPath(policy['seed_plan']['path'])}'\n$policyHash='{sha256(encode(policy))}'\n"
    old_pins = {
        "DL_bot.py": "a" * 64,
        "core/other.py": ("b" if scenario == "cascade" else "a") * 64,
    }
    first = release_seed(original, old_pins, gate)
    gate = first.pop("Start-ReviewedAutomaticStartup.ps1").decode()
    previous = {name: json.loads(raw) for name, raw in first.items()}
    gate += "\n".join(f"# {path}={digest}" for path, digest in old_pins.items())
    pins = {"DL_bot.py": "b" * 64, "core/other.py": "c" * 64}
    if scenario == "same":
        pins["core/other.py"] = "b" * 64
    elif scenario == "ambiguous":
        pins["core/other.py"] = "a" * 64
    elif scenario == "removed":
        del pins["core/other.py"]
    if scenario in {"ambiguous", "removed"}:
        with pytest.raises(ValueError, match=r"launch-gate|Launch-gate"):
            release_seed(previous, pins, gate)
    else:
        result = release_seed(previous, pins, gate)["Start-ReviewedAutomaticStartup.ps1"].decode()
        for path, digest in pins.items():
            assert f"# {path}={digest}" in result


def test_seed_preparation_refuses_unbound_gate(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="gate"):
        release_seed(
            predecessor(tmp_path, monkeypatch), {"DL_bot.py": "a" * 64}, "arbitrary script"
        )


def test_full_packages_for_two_updates_need_no_handwritten_specification(tmp_path, monkeypatch):
    from pathlib import Path
    from uuid import uuid4

    from core.export_release_seed import successor_seed
    from scripts.prepare_k98_release import validate_manifest
    from scripts.prepare_k98_update import prepare_update

    initial = predecessor(tmp_path, monkeypatch)
    raw = b"print('before')\n"
    previous = {
        name: json.loads(value)
        for name, value in successor_seed(
            initial,
            {"DL_bot.py": sha256(raw)},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        ).items()
    }
    tools = Path(__file__).resolve().parents[1] / "scripts"
    identities = set()
    for index, content in enumerate((b"print('first')\n", b"print('second')\n")):
        policy = previous["AutomaticStartupPolicy.json"]
        gate = f"$policy='{PureWindowsPath(policy['seed_plan']['path'])}'\n$policyHash='{sha256(encode(policy))}'\n"
        observation = dict(
            seed=previous,
            gate=gate,
            bindings=dict(
                before=str(index + 1) * 40,
                target=str(index + 2) * 40,
                root="C:\\fixture",
                host="FIXTURE",
                sid="S-1-5-21-1-2-3-1001",
                old_policy=dict(Path="C:\\fixture\\policy.json", SHA256=sha256(encode(policy))),
                old_plan=dict(Python="C:\\fixture\\python.exe", PythonSHA256="a" * 64),
            ),
        )
        blobs = {
            (str(index + 1) * 40, "DL_bot.py"): raw,
            (str(index + 2) * 40, "DL_bot.py"): content,
        }
        result = prepare_update(
            observation,
            ["DL_bot.py"],
            lambda *key: blobs.get(key),
            tmp_path / f"update-{index}",
            tools,
        )
        package = Path(result["manifest"]).parent
        assert not (package.parent / "inputs").exists()
        manifest_raw = Path(result["manifest"]).read_bytes()
        manifest = json.loads(manifest_raw)
        validate_manifest(manifest)
        assert result["manifest_sha256"] == sha256(manifest_raw)
        assert result["release_id"] not in identities
        identities.add(result["release_id"])
        assert [step["kind"] for step in manifest["steps"]] == [
            "source",
            "seed",
            "start",
            "readiness",
        ]
        for member in manifest["members"]:
            assert sha256((package / member["name"]).read_bytes()) == member["sha256"]
        bindings = json.loads((package / "ReleaseBindings.json").read_bytes())
        assert (package / bindings["source_members"][0]["payload"]).read_bytes() == content
        assert bindings["new_policy"]["flags"] == policy["flags"]
        previous = {name: json.loads((package / name).read_bytes()) for name in previous}
        raw = content
    assert len(identities) == 2


def test_one_time_tool_installer_contains_complete_self_checked_payload(tmp_path):
    import base64
    from pathlib import Path
    import re

    from scripts.package_k98_update_tool import package

    result = package(tmp_path)
    script = Path(result["installer"]).read_bytes()
    assert result["sha256"] == sha256(script)
    encoded = re.search(rb"\$encoded='([A-Za-z0-9+/=]+)'", script)[1]
    payload = {
        name: base64.b64decode(value)
        for name, value in json.loads(base64.b64decode(encoded)).items()
    }
    manifest = json.loads(payload.pop("update-tool.json"))
    assert set(manifest["files"]) == set(payload)
    for name, expected in manifest["files"].items():
        assert sha256(payload[name]) == expected
    assert result["production_changed"] is False
    with pytest.raises(FileExistsError):
        package(tmp_path)


@pytest.mark.parametrize(
    "extra", [None, "core/local.py", "core/helper.pyd", "core/__pycache__/note.txt"]
)
def test_live_preflight_uses_complete_production_bootstrap_inventory(tmp_path, monkeypatch, extra):
    from pathlib import Path
    import runpy
    import sys
    from types import SimpleNamespace

    from scripts import verify_k98_update_pair as verifier

    original_run = runpy.run_path
    bootstrap_path = Path(__file__).resolve().parents[1] / "scripts/run_export_authority.py"
    authority = original_run(str(bootstrap_path))
    runtime = tmp_path / "scripts/run_export_authority.py"
    runtime.parent.mkdir()
    runtime.write_bytes(bootstrap_path.read_bytes())
    core = tmp_path / "core/known.py"
    core.parent.mkdir()
    core.write_bytes(b"pass\n")
    pins = {
        path.relative_to(tmp_path).as_posix(): sha256(path.read_bytes()) for path in (runtime, core)
    }
    policy = {"source_hashes": pins, "flags": {"intake": False, "recovery": False}}
    policy_path = tmp_path / "policy.json"
    policy_path.write_bytes(encode(policy))
    config = {
        "root": str(tmp_path),
        "old_policy": {"Path": str(policy_path), "SHA256": sha256(encode(policy))},
        "old_pins": pins,
        "flags": policy["flags"],
    }
    if extra:
        extra_path = tmp_path / extra
        extra_path.parent.mkdir(exist_ok=True)
        extra_path.write_bytes(b"untracked")
    inspected = []

    def inspect(path, **_kwargs):
        inspected.append(Path(path))
        return Path(path)

    def bootstrap(path, **kwargs):
        return authority["bootstrap"](path, inspect_path=inspect, **kwargs)

    # Substitute native ACL inspection only; run the actual production bootstrap
    # enumeration, forbidden-artifact, exact-set and source-hash checks.
    monkeypatch.setattr(verifier.runpy, "run_path", lambda path: {"bootstrap": bootstrap})
    with monkeypatch.context() as state:
        state.setattr(sys, "flags", SimpleNamespace(isolated=True))
        state.setattr(sys, "path", list(sys.path))
        state.setattr(sys, "dont_write_bytecode", sys.dont_write_bytecode)
        if extra:
            with pytest.raises(authority["AuthorityStartupError"]):
                verifier.verify_live_source(config, predecessor=True)
        else:
            assert verifier.verify_live_source(config, predecessor=True) == policy
    assert core.parent in inspected


def test_installer_ignores_inherited_user_module_search(tmp_path):
    import os
    from pathlib import Path
    import subprocess

    from scripts.package_k98_update_tool import INSTALLER

    if os.name != "nt":
        pytest.skip("Native Windows PowerShell module resolution regression")
    module = tmp_path / "Modules" / "ScheduledTasks"
    module.mkdir(parents=True)
    (module / "ScheduledTasks.psm1").write_text(
        "function Get-ScheduledTask { 'UNTRUSTED_MODULE' }; "
        "Export-ModuleMember -Function Get-ScheduledTask\n"
    )
    # Exercise the real installer preamble without its host/token guards or any
    # task lookup. Resolving the command is enough to test executable discovery.
    preamble = INSTALLER.split("if($env:COMPUTERNAME", 1)[0]
    probe = tmp_path / "probe.ps1"
    probe.write_text(preamble + "\n(Get-Command Get-ScheduledTask).Module.Path\n")
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(probe),
        ],
        env={**os.environ, "PSModulePath": str(module.parent)},
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    resolved = Path(result.stdout.strip())
    assert resolved.is_relative_to(Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\Modules"))
    assert resolved.name == "ScheduledTasks.psd1"
