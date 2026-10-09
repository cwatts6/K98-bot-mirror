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
