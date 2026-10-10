from copy import deepcopy
import json
from pathlib import Path, PureWindowsPath
import subprocess
from uuid import uuid4

import pytest

from scripts.prepare_k98_update import combined_description, combined_payload, sha256


def fixture():
    module = b"CREATE OR ALTER PROCEDURE [dbo].[Example]\nAS SELECT N'caf\xc3\xa9';\n"
    profile = dict(
        version=1,
        profile="module_grants_v1",
        migration_id="20261010_901_example",
        database_collation="Latin1_General_CI_AS",
        tempdb_collation="SQL_Latin1_General_CP1_CI_AS",
        compatibility_level=160,
        modules=[
            dict(
                schema="dbo",
                name="Example",
                type="P",
                before_sha256="c" * 64,
                file="Example.sql",
                sha256=sha256(module),
            )
        ],
        grants=[],
        requires=[],
    )
    raw = json.dumps(profile).encode()
    description = dict(
        version=1,
        profile="module_grants_v1",
        bot_predecessors=["a" * 40],
        sql_commit="b" * 40,
        migrations=[dict(id=profile["migration_id"], sha256=sha256(raw))],
    )
    files = {
        "deploy/Deploy-SqlMigration.ps1": b"runner",
        "deploy/SqlDeploy.ModuleRelease.ps1": b"library",
        "migrations/20261010_901_example.release.json": raw,
        "migrations/Example.sql": module,
    }
    return description, profile, files


def test_sql_order_and_unicode_bytes_remain_exact():
    d, _, files = fixture()
    assert combined_description(json.dumps(d).encode(), "a" * 40) == d
    binding, payload = combined_payload(d, files.get)
    assert binding["commit"] == "b" * 40
    assert binding["profiles"][0]["id"] == d["migrations"][0]["id"]
    assert payload["Example.sql"] == files["migrations/Example.sql"]
    assert all(m["sha256"] == sha256(payload[m["name"]]) for m in binding["members"])


def test_committed_descriptor_ci_validation_reads_actual_input(tmp_path):
    from scripts.validate_k98_release_description import main

    path = tmp_path / "k98-release.json"
    args = ["--descriptor", str(path)]
    assert main(args) == 0
    d, _, _ = fixture()
    path.write_text(json.dumps(d))
    assert main(args) == 0
    d["sql_commit"] = "main"
    path.write_text(json.dumps(d))
    assert main(args) == 1
    path.write_text('{"version":')
    assert main(args) == 1


def test_descriptor_ci_refuses_deletion_but_allows_source_only(tmp_path, monkeypatch):
    from scripts.validate_k98_release_description import main

    monkeypatch.chdir(tmp_path)

    def git(*args):
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init")
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        "source",
    )
    source_base = git("rev-parse", "HEAD")
    assert main(["--base-revision", source_base]) == 0
    path = Path("deploy/k98-release.json")
    path.parent.mkdir()
    path.write_text(json.dumps(fixture()[0]))
    assert main(["--base-revision", source_base]) == 0
    git("add", path.as_posix())
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "combined")
    combined_base = git("rev-parse", "HEAD")
    assert main(["--base-revision", combined_base]) == 0
    path.unlink()
    assert main(["--base-revision", combined_base]) == 1
    assert main(["--base-revision", "f" * 40]) == 1
    assert main(["--base-revision", "main"]) == 1


@pytest.mark.parametrize("damage", ["profile", "before", "commit", "order", "extra", "hash"])
def test_unreviewed_release_description_refused(damage):
    d, _, _ = fixture()
    if damage == "profile":
        d["profile"] = "arbitrary_sql"
    elif damage == "before":
        d["bot_predecessors"] = ["f" * 40]
    elif damage == "commit":
        d["sql_commit"] = "main"
    elif damage == "order":
        d["migrations"] *= 2
    elif damage == "extra":
        d["force"] = True
    else:
        d["migrations"][0]["sha256"] = "observed"
    with pytest.raises(ValueError):
        combined_description(json.dumps(d).encode(), "a" * 40)


@pytest.mark.parametrize("damage", ["module", "profile", "runner", "traversal", "overlap"])
def test_payload_refuses_drift_or_unsafe_composition(damage):
    d, p, files = fixture()
    if damage == "module":
        files["migrations/Example.sql"] += b"\r\n"
    elif damage == "profile":
        files["migrations/20261010_901_example.release.json"] += b" "
    elif damage == "runner":
        del files["deploy/Deploy-SqlMigration.ps1"]
    elif damage == "traversal":
        p["modules"][0]["file"] = "../Example.sql"
        raw = json.dumps(p).encode()
        files["migrations/20261010_901_example.release.json"] = raw
        d["migrations"][0]["sha256"] = sha256(raw)
    else:
        second = deepcopy(p)
        second["migration_id"] = "20261010_902_example"
        raw = json.dumps(second).encode()
        files["migrations/20261010_902_example.release.json"] = raw
        d["migrations"].append(dict(id=second["migration_id"], sha256=sha256(raw)))
    with pytest.raises(ValueError):
        combined_payload(d, files.get)


def test_protected_sql_module_and_principal_changes_are_refused():
    d, p, files = fixture()
    with pytest.raises(ValueError, match="protected startup"):
        combined_payload(d, files.get, protected_objects=["DBO.EXAMPLE"])
    p["grants"] = [
        dict(schema="dbo", name="Example", principal="Bot", permission="EXECUTE", before="ABSENT")
    ]
    raw = json.dumps(p).encode()
    files["migrations/20261010_901_example.release.json"] = raw
    d["migrations"][0]["sha256"] = sha256(raw)
    with pytest.raises(ValueError, match="protected startup"):
        combined_payload(d, files.get, protected_principals=["bot"])


@pytest.mark.parametrize("installed", [False, True])
def test_reusable_upgrade_package_binds_previous_and_new_manifests(tmp_path, installed):
    import base64
    import re

    from scripts.package_k98_update_tool import package

    first = package(tmp_path / "first")
    text = Path(first["installer"]).read_text()
    payload = json.loads(base64.b64decode(re.search(r"\$encoded='([^']+)'", text)[1]))
    manifest = tmp_path / "installed.json"
    manifest.write_bytes(base64.b64decode(payload["update-tool.json"]))
    if installed:
        manifest.write_bytes(
            (Path(__file__).parent / "fixtures" / "updater_installed_20261009.json").read_bytes()
        )
        assert sha256(manifest.read_bytes()) == (
            "6562c4cf8970c8fe5c776d10275aab6f2211fc2e814a9d3a529a56a15c34c50b"
        )
    second = package(tmp_path / "second", previous_manifest=manifest)
    upgrade = Path(second["upgrade"]).read_text()
    new_text = Path(second["installer"]).read_text()
    new_payload = json.loads(base64.b64decode(re.search(r"\$encoded='([^']+)'", new_text)[1]))
    new_hash = sha256(base64.b64decode(new_payload["update-tool.json"]))
    assert f"$PreviousManifestSHA256='{sha256(manifest.read_bytes())}'" in upgrade
    assert f"$InstallerSHA256='{second['sha256']}'" in upgrade
    assert f"$TargetManifestSHA256='{new_hash}'" in upgrade
    assert "updater-before-'+$PreviousManifestSHA256" in upgrade
    assert "Active release exists; tool replacement refused" in upgrade


def test_complete_combined_packet_binds_sql_then_source_and_preserves_contracts(
    tmp_path, monkeypatch
):
    from core.export_release_seed import successor_seed
    from scripts.prepare_k98_update import RELEASE_DESCRIPTION, prepare_update
    from services.export_execution_protocol import encode
    import services.export_runtime_composition as composition
    from tests.test_export_release_seed import predecessor

    initial = predecessor(tmp_path, monkeypatch)
    bot = initial["bot-template.json"]
    bot["sql_contract"]["principal"] = "restricted"
    bot["application_sql_contract"] = {"principal": "restricted"}
    bot["legacy_sql_contract"] = {"principal": "restricted", "source": {"modules": []}}
    initial["ManualProcessPairPlan-CANDIDATE.json"]["templates"]["bot"]["sha256"] = sha256(
        encode(bot)
    )
    initial["AutomaticStartupPolicy.json"]["seed_plan"]["sha256"] = sha256(
        encode(initial["ManualProcessPairPlan-CANDIDATE.json"])
    )
    # Scope computation is independently tested with complete startup contracts;
    # the packet fixture supplies the already-validated closure, not live metadata.
    monkeypatch.setattr(composition, "application_contract_scope", lambda _: ["dbo.Protected"])
    previous = {
        name: json.loads(raw)
        for name, raw in successor_seed(
            initial,
            {"DL_bot.py": sha256(b"old\n")},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        ).items()
    }
    policy = previous["AutomaticStartupPolicy.json"]
    d, _, files = fixture()
    observation = dict(
        seed=previous,
        gate=f"$policy='{PureWindowsPath(policy['seed_plan']['path'])}'\n$policyHash='{sha256(encode(policy))}'\n",
        bindings=dict(
            before="a" * 40,
            target="c" * 40,
            root="C:\\fixture",
            host="FIXTURE",
            sid="S-1-5-21-1-2-3-1001",
            old_policy=dict(Path="C:\\fixture\\policy.json", SHA256=sha256(encode(policy))),
            old_plan=dict(Python="C:\\fixture\\python.exe", PythonSHA256="a" * 64),
        ),
    )
    blobs = {
        ("a" * 40, "DL_bot.py"): b"old\n",
        ("c" * 40, "DL_bot.py"): b"new\n",
        ("c" * 40, RELEASE_DESCRIPTION): json.dumps(d).encode(),
    }
    result = prepare_update(
        observation,
        ["DL_bot.py", RELEASE_DESCRIPTION],
        lambda *key: blobs.get(key),
        tmp_path / "packet",
        Path(__file__).resolve().parents[1] / "scripts",
        read_sql_blob=files.get,
    )
    package = Path(result["manifest"]).parent
    manifest = json.loads(Path(result["manifest"]).read_bytes())
    assert manifest["version"] == 4
    assert [s["kind"] for s in manifest["steps"]] == [
        "sql",
        "source",
        "seed",
        "start",
        "readiness",
    ]
    assert manifest["steps"][0]["apply"]["arguments"]["MigrationId"] == d["migrations"][0]["id"]
    assert (
        json.loads((package / "bot-template.json").read_bytes())["sql_contract"]
        == bot["sql_contract"]
    )
    assert (
        json.loads((package / "AutomaticStartupPolicy.json").read_bytes())["flags"]
        == policy["flags"]
    )
    for member in manifest["members"]:
        assert sha256((package / member["name"]).read_bytes()) == member["sha256"]
    from scripts.prepare_k98_release import validate_updater_manifest

    validate_updater_manifest(manifest)
    for damage in ("adapter", "action", "binding", "migration", "argument"):
        invalid = deepcopy(manifest)
        call = invalid["steps"][0]["verify"]
        if damage == "adapter":
            call["file"] = "Deploy-SqlMigration.ps1"
        elif damage == "action":
            call["arguments"]["Action"] = "VerifySource"
        elif damage == "binding":
            call["arguments"]["ExpectedBindingsSHA256"] = "f" * 64
        elif damage == "migration":
            call["arguments"]["MigrationId"] = "20261010_902_other"
        else:
            call["arguments"]["Force"] = "true"
        with pytest.raises(ValueError, match="exact normal-updater"):
            validate_updater_manifest(invalid)
