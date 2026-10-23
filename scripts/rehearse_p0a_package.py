"""Assemble a non-deployable P0a package from retained seed and reviewed Git bytes.

This offline qualification does not collect live process bindings, install any
source, connect to SQL or start the bot. The installed updater must independently
prepare the actual deployment package from fresh observations and private main.
"""

import argparse
import io
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MIRROR_BASE = "02b57ac682e988c5fefece5669f40de31936a756"
sys.path.insert(0, str(ROOT))

from scripts.p0a_release import specification
from scripts.prepare_k98_release import validate_updater_manifest
from scripts.prepare_k98_update import TOOL_SOURCE_PATHS, prepare_update, sha256


def git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "core.eol=lf",
            "-c",
            "safe.directory=" + root.as_posix(),
            "-C",
            str(root),
            *args,
        ]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-directory", type=Path, required=True)
    parser.add_argument("--sql-source", type=Path, required=True)
    args = parser.parse_args()
    spec = specification()
    source = args.seed_directory.resolve(strict=True)
    old = json.loads((source / "ReleaseBindings.json").read_bytes())
    names = (
        "authority-template.json",
        "bot-template.json",
        "AutomaticStartupPolicy.json",
        "ManualProcessPairPlan-CANDIDATE.json",
        "host_acl.json",
        "bot_identity.json",
        "identity_issuance.json",
        "file_access.json",
        "key_inventory.json",
        "writer_drain.json",
        "sql_installation.json",
    )
    seed = {name: json.loads((source / name).read_bytes()) for name in names}
    policy = seed["AutomaticStartupPolicy.json"]
    policy_raw = (source / "AutomaticStartupPolicy.json").read_bytes()
    before = spec["before"]
    # Include saved implementation edits. Hashes below identify the actual bytes;
    # the synthetic target label is never represented as a deployable Git commit.
    target = "0" * 40
    with zipfile.ZipFile(io.BytesIO(git(ROOT, "archive", "--format=zip", before))) as archive:
        if sum(item.file_size for item in archive.infolist()) > 256 * 1024 * 1024:
            raise ValueError("Predecessor archive exceeds rehearsal bound.")
        old_files = {
            item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()
        }
    with zipfile.ZipFile(io.BytesIO(git(ROOT, "archive", "--format=zip", MIRROR_BASE))) as archive:
        mirror_files = {
            item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()
        }
    new_names = set(
        git(ROOT, "ls-files", "--cached", "--others", "--exclude-standard").decode().splitlines()
    )
    new_files = {}
    for path in new_names:
        file = ROOT / path
        if file.is_file():
            raw = file.read_bytes()
            new_files[path] = raw.replace(b"\r\n", b"\n") if b"\0" not in raw else raw
    # Rehearse the patch on private history. Never model promotion by replacing
    # the private tree with the scrubbed mirror (which would delete private files).
    changes = sorted(
        path
        for path in set(mirror_files) | set(new_files)
        if mirror_files.get(path) != new_files.get(path)
    )
    for path in changes:
        if old_files.get(path) != mirror_files.get(path):
            raise ValueError(
                "Private/mirror preimage requires explicit patch reconciliation: " + path
            )
    cache = {}

    def blob(commit, path):
        key = (commit, path)
        if key not in cache:
            if commit == before:
                cache[key] = old_files.get(path)
            else:
                cache[key] = new_files.get(path) if path in changes else old_files.get(path)
        return cache[key]

    output = Path(tempfile.mkdtemp(prefix="K98_P0a_Package_"))
    tools = output / "tool"
    tools.mkdir()
    for path in TOOL_SOURCE_PATHS:
        (tools / Path(path).name).write_bytes(blob(target, path))
    sql_contract = spec["contracts"]["sql_contract"]["before"]
    bindings = dict(old)
    bindings.update(
        before=before,
        target=target,
        old_policy=dict(
            Path=str(
                PureWindowsPath(policy["seed_plan"]["path"]).with_name(
                    "AutomaticStartupPolicy.json"
                )
            ),
            SHA256=sha256(policy_raw),
            StateDirectory=policy["state_directory"],
        ),
        # Explicit qualification environment, not an installed production fact.
        sql_environment=dict(
            server=sql_contract["server"],
            database=sql_contract["database"],
            database_collation=sql_contract["collation"],
            tempdb_collation="Latin1_General_CI_AS",
            compatibility_level=160,
        ),
    )
    observation = dict(
        seed=seed,
        gate=(source / "Start-ReviewedAutomaticStartup.ps1").read_text(encoding="utf-8"),
        bindings=bindings,
    )
    result = prepare_update(
        observation,
        changes,
        blob,
        output / "packet",
        tools,
        read_sql_blob=lambda path: git(args.sql_source, "show", spec["sql"]["commit"] + ":" + path),
    )
    manifest_raw = Path(result["manifest"]).read_bytes()
    manifest = json.loads(manifest_raw)
    validate_updater_manifest(manifest)
    package = Path(result["manifest"]).parent
    for member in manifest["members"]:
        assert sha256((package / member["name"]).read_bytes()) == member["sha256"], member["name"]
    config = json.loads((package / "ReleaseBindings.json").read_bytes())
    assert config["flags"] == policy["flags"]
    assert config["new_policy"]["flags"] == policy["flags"]
    assert config["recovery_seed"] == "live_sql_observation_v1"
    assert [s["kind"] for s in manifest["steps"]] == ["sql", "source", "seed", "start", "readiness"]
    candidate = json.loads((package / "bot-template.json").read_bytes())
    for name, pair in spec["contracts"].items():
        assert candidate[name] == pair["after"], name
    report = dict(
        status="OFFLINE_PACKAGE_VERIFIED_NOT_DEPLOYABLE",
        production_touched=False,
        sql_connected=False,
        source_changes=len(changes),
        protected_changes=len(spec["sources"]),
        members=len(manifest["members"]),
        manifest_bytes=len(manifest_raw),
        manifest_sha256=sha256(manifest_raw),
        sql_commit=spec["sql"]["commit"],
        environment="EXPLICIT_FIXTURE_VALUES_NOT_PRODUCTION_OBSERVATION",
        output=str(output),
        source_inventory={
            p: sha256(blob(target, p)) if blob(target, p) is not None else None for p in changes
        },
    )
    (output / "qualification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "source_inventory"}))


if __name__ == "__main__":
    main()
