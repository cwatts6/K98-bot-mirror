"""Prepare a separately receipted correction for an exact pre-incarnation failure.

The administrative launcher owns exclusion, current SQL/native checks and all
installation. This helper only transforms an authenticated unused normal packet.
It preserves the original release and its start intent, and never starts a role.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import runpy
from typing import Any
from uuid import UUID

FAILED_TARGET = "3d702510229460f740d66708fe64e00959f54838"
ISSUER = "scripts/run_export_startup_issuer.py"
FIXED_ISSUER = "e9735585cf74c4af60df50a47691eccbba8af5dbe9852695221388c5baaae3ff"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read(path, expected=None, limit=4 * 1024 * 1024):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit or (expected is not None and digest(raw) != expected):
        raise ValueError("Exact bounded correction input required.")
    return raw


def correction_files(original, files, *, recovery_id, target):
    """Rebind an unused candidate; never revise an executed packet in place."""
    if str(UUID(recovery_id)) != recovery_id or not re.fullmatch(r"[a-f0-9]{40}", target):
        raise ValueError("Canonical correction identity required.")
    if original["target"] != FAILED_TARGET or "sql" in original or "recovery_seed" in original:
        raise ValueError("Only the reviewed source-only failed target is supported.")
    predecessor = dict(
        policy_sha256=original["old_policy"]["SHA256"],
        state_directory=original["old_policy"]["StateDirectory"],
    )
    if original["new_policy"]["predecessor"] != predecessor:
        raise ValueError("Exact original predecessor lineage required.")
    result = dict(files)
    binding = json.loads(result["ReleaseBindings.json"])
    policy = json.loads(result["AutomaticStartupPolicy.json"])
    if (
        binding["before"] != FAILED_TARGET
        or binding["target"] != target
        or binding["old_pins"] != original["new_pins"]
        or binding["flags"] != original["flags"]
        or binding["new_policy"] != policy
        or binding["new_policy_sha256"] != digest(result["AutomaticStartupPolicy.json"])
        or "sql" in binding
        or "recovery_seed" in binding
    ):
        raise ValueError("Candidate differs from the exact failed source and flags.")
    for key in (
        "root",
        "host",
        "sid",
        "account",
        "git_path",
        "git_sha256",
        "venv",
        "contract_verifier_sha256",
        "old_journal",
        "old_native",
        "old_session",
        "expected_preparation",
        "expected_resources",
    ):
        if binding[key] != original[key]:
            raise ValueError("Original ownership/drain binding must be preserved.")
    failed_policy_path = str(
        PureWindowsPath(original["new_seed_directory"]) / "AutomaticStartupPolicy.json"
    )
    if binding["old_policy"] != dict(
        Path=failed_policy_path,
        SHA256=original["new_policy_sha256"],
        StateDirectory=original["new_state_directory"],
    ):
        raise ValueError("Candidate must derive from the exact failed seed.")
    if policy["predecessor"] != dict(
        policy_sha256=original["new_policy_sha256"], state_directory=original["new_state_directory"]
    ):
        raise ValueError("Unused candidate lineage differs.")
    if (
        binding["new_state_directory"]
        in {original["new_state_directory"], original["old_policy"]["StateDirectory"]}
        or binding["new_seed_directory"] == original["new_seed_directory"]
        or policy["state_directory"] != binding["new_state_directory"]
        or str(PureWindowsPath(policy["seed_plan"]["path"]).parent) != binding["new_seed_directory"]
    ):
        raise ValueError("Fresh correction seed and history required.")
    members = [m for m in binding["source_members"] if m.get("path") == ISSUER]
    if len(members) != 1:
        raise ValueError("Exactly one reviewed issuer source member required.")
    member = members[0]
    payload_name = member.get("payload")
    issuer = result.get(payload_name) if isinstance(payload_name, str) else None
    if not isinstance(issuer, bytes):
        raise ValueError("Reviewed issuer payload is missing or invalid.")
    if (
        digest(issuer.replace(b"\r\n", b"\n")) != FIXED_ISSUER
        or digest(issuer) != binding["new_pins"].get(ISSUER)
        or member.get("target_sha256") != digest(issuer)
    ):
        raise ValueError("Exact reviewed issuer correction required.")
    # There was no failed incarnation: preserve the last actual predecessor,
    # never invent an incarnation or point reconciliation at an empty history.
    old_hash = digest(result["AutomaticStartupPolicy.json"])
    policy["predecessor"] = predecessor
    result["AutomaticStartupPolicy.json"] = encode(policy)
    new_hash = digest(result["AutomaticStartupPolicy.json"])
    gate = result["Start-ReviewedAutomaticStartup.ps1"].decode("utf-8")
    if gate.count("$policyHash='" + old_hash + "'") != 1:
        raise ValueError("Exact candidate gate policy pin required.")
    result["Start-ReviewedAutomaticStartup.ps1"] = gate.replace(old_hash, new_hash).encode()
    binding["release_id"] = original["release_id"]
    binding["old_policy"] = deepcopy(original["old_policy"])
    binding["old_plan"] = deepcopy(original["old_plan"])
    binding["new_policy"] = policy
    binding["new_policy_sha256"] = new_hash
    for item in binding["seed_members"]:
        if item["name"] in {"AutomaticStartupPolicy.json", "Start-ReviewedAutomaticStartup.ps1"}:
            item["sha256"] = digest(result[item["name"]])
    result["ReleaseBindings.json"] = encode(binding)
    # Reuse the fixed source adapter with one literal backup-ref substitution.
    # The original before-update ref and its start/source/seed receipts remain.
    step = result["Release-Step.ps1"].decode("utf-8")
    old_ref = "'update-ref refs/heads/codex/before-update-'+$c.release_id+' '"
    if step.count(old_ref) != 1:
        raise ValueError("Reviewed source adapter backup expression differs.")
    result["Release-Step.ps1"] = step.replace(
        old_ref, "'update-ref refs/heads/codex/before-recovery-" + recovery_id + " '"
    ).encode()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profile-sha256", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--prepared-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    profile = json.loads(read(args.profile, args.profile_sha256))
    original = json.loads(read(profile["bindings"], profile["bindings_sha256"]))
    prepared = json.loads(read(args.prepared, args.prepared_sha256))
    manifest = json.loads(read(prepared["manifest"], prepared["manifest_sha256"], 65536))
    tools = Path(__file__).parent
    tool_manifest = json.loads(read(tools / "update-tool.json"))
    verifier_path = tools / "verify_k98_update_pair.py"
    verifier_raw = read(verifier_path, tool_manifest["files"][verifier_path.name])
    verifier: dict[str, Any] = {"__name__": "correction_verifier", "__file__": str(verifier_path)}
    exec(compile(verifier_raw, str(verifier_path), "exec"), verifier)
    verifier["activate_contract_archive"](
        tools / "contract_verifier.zip", original["contract_verifier_sha256"], original["root"]
    )
    preparer = runpy.run_path(str(tools / "prepare_k98_update.py"))
    validator = runpy.run_path(str(tools / "prepare_k98_release.py"))
    validator["validate_updater_manifest"](manifest)
    if [s["id"] for s in manifest["steps"]] != ["source", "seed", "start", "readiness"]:
        raise ValueError("Only source/seed/start/readiness correction supported.")
    package = Path(prepared["manifest"]).parent
    files = {}
    for item in manifest["members"]:
        # The normal manifest validator has already restricted names to flat files.
        if item["name"] == "EmptyGitConfig.txt":
            raw = (package / item["name"]).read_bytes()
            if raw or digest(raw) != item["sha256"]:
                raise ValueError("Empty configuration sentinel differs.")
        else:
            raw = read(package / item["name"], item["sha256"], 16 * 1024 * 1024)
        files[item["name"]] = raw
    files = correction_files(
        original, files, recovery_id=profile["recovery_id"], target=profile["target"]
    )
    directory = Path(args.output)
    mkdir, write = preparer["output_writers"](original["sid"], secure_output=True)
    mkdir(directory)
    for name, raw in sorted(files.items()):
        write(directory / name, raw)
    plan = dict(
        version=1,
        kind="startup_evidence_correction_v1",
        recovery_id=profile["recovery_id"],
        original_release_id=original["release_id"],
        original_bindings_sha256=profile["bindings_sha256"],
        profile_sha256=args.profile_sha256,
        target=profile["target"],
        bindings_sha256=digest(files["ReleaseBindings.json"]),
        members=[dict(name=name, sha256=digest(raw)) for name, raw in sorted(files.items())],
    )
    write(directory / "correction-plan.json", encode(plan))
    print(
        json.dumps(
            dict(
                stage="CORRECTION_PREPARED_NOT_INSTALLED",
                directory=str(directory),
                plan_sha256=digest(encode(plan)),
            )
        )
    )


if __name__ == "__main__":
    main()
