"""Classify an exact Git delta without preparing or deploying a release.

The checked-out updater supplies the policy. Run its reviewed version; target
source is read as Git blobs, never imported. This cannot attest machine custody,
live process state, or that this candidate updater is installed on the bot host.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess

from scripts.prepare_k98_update import (
    TOOL_SOURCE_PATHS,
    check_case_aliases,
    check_mge_release_binding,
    check_source_only,
    check_transition_inventory,
    coordinated_policy,
    sha256,
)
from scripts.verify_k98_update_pair import CONTRACT_ARCHIVE, build_contract_archive

COORDINATED_RELEASE_EXIT = 3


def classify(
    before,
    target,
    paths,
    read_blob,
    installed_tool=None,
    *,
    policy_sha256=None,
    inventory_paths=None,
    registry_sha256=None,
):
    blockers, tool_changes = [], []
    recovery = None
    try:
        policy = coordinated_policy()
        recovery = policy.selected(before, target, paths, read_blob) if policy else None
    except ValueError as exc:
        blockers.append(str(exc))
    admitted = {r["path"] for r in recovery["sources"]} if recovery else set()
    try:
        if len(paths) > 4096 or len(set(paths)) != len(paths):
            raise ValueError("Bounded unique changed paths required.")
        check_case_aliases(set(paths) | set(inventory_paths or ()))
        check_transition_inventory(paths, read_blob, before, target, admitted=admitted)
        check_mge_release_binding(before, target, paths, read_blob)
    except ValueError as exc:
        blockers.append(str(exc))
    if installed_tool is not None:
        expected = {Path(path).name for path in TOOL_SOURCE_PATHS} | {"EmptyGitConfig.txt"}
        registry = expected - {
            "p0a_release.py",
            "p0a_release_spec.json",
            "recovery_release_seed.py",
        }
        prior = registry - {"k98_update_transitions.json"}
        legacy = prior - {"prepare_k98_release.py"}
        if (
            not isinstance(installed_tool, dict)
            or set(installed_tool) != {"version", "files"}
            or type(installed_tool["version"]) is not int
            or installed_tool["version"] != 1
            or not isinstance(installed_tool["files"], dict)
            or set(installed_tool["files"])
            not in (expected | {CONTRACT_ARCHIVE}, expected, registry, prior, legacy)
            or any(
                not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                for value in installed_tool["files"].values()
            )
        ):
            raise ValueError("Exact version-1 supported installed-tool manifest required.")
        archive_hash = sha256(build_contract_archive(Path(__file__).resolve().parents[1]))
        if installed_tool["files"].get(CONTRACT_ARCHIVE) != archive_hash:
            tool_changes.append(CONTRACT_ARCHIVE)
        for missing in expected - set(installed_tool["files"]):
            tool_changes.append("scripts/" + missing)
    if recovery:
        # The exception belongs to the installed package, never the target tree.
        # Require its complete executable policy inventory, including unchanged
        # helper files that would not appear in the Git delta.
        for path in TOOL_SOURCE_PATHS:
            name = Path(path).name
            expected_hash = sha256(
                Path(__file__).with_name(name).read_bytes().replace(b"\r\n", b"\n")
            )
            if installed_tool is None or installed_tool["files"].get(name) != expected_hash:
                if path not in tool_changes:
                    tool_changes.append(path)
    if installed_tool is not None and policy_sha256 is not None:
        if installed_tool.get("files", {}).get("prepare_k98_update.py") != policy_sha256:
            tool_changes.append("scripts/prepare_k98_update.py")
    if installed_tool is not None and registry_sha256 is not None:
        if installed_tool["files"].get("k98_update_transitions.json") != registry_sha256:
            path = "scripts/k98_update_transitions.json"
            if path not in tool_changes:
                tool_changes.append(path)
    for path in paths:
        try:
            old, new = read_blob(before, path), read_blob(target, path)
            if old == new:
                raise ValueError(f"Changed-path inventory differs: {path}")
            if path in TOOL_SOURCE_PATHS:
                if new is None:
                    raise ValueError(f"Updater member removal is unsupported: {path}")
                if installed_tool is None or installed_tool["files"].get(Path(path).name) != sha256(
                    new
                ):
                    if path not in tool_changes:
                        tool_changes.append(path)
            check_source_only(
                [] if path in admitted else [path],
                tool_copies=TOOL_SOURCE_PATHS,
                read_blob=read_blob,
                before=before,
                target=target,
            )
        except ValueError as exc:
            blockers.append(str(exc))
    return dict(
        before=before,
        target=target,
        classification=(
            "COORDINATED_RELEASE_REQUIRED"
            if blockers
            else (
                "UPDATER_UPGRADE_REQUIRED"
                if tool_changes
                else "COORDINATED_COMPATIBLE" if recovery else "ROUTINE_COMPATIBLE"
            )
        ),
        changed_files=len(paths),
        updater_members=tool_changes,
        policy_sha256=policy_sha256,
        blockers=blockers,
        qualification="Source compatibility only; installed tooling and live preflight remain required.",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Installed Bot commit, not just PR base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--installed-tool-manifest")
    args = parser.parse_args()

    def git(*arguments):
        return subprocess.check_output(["git", "--no-optional-locks", *arguments], timeout=60)

    before, target = (
        git("rev-parse", "--verify", "--end-of-options", value + "^{commit}").decode().strip()
        for value in (args.base, args.head)
    )
    paths = git("diff", "--no-renames", "--name-only", "-z", before, target).decode().split("\0")
    paths = [path for path in paths if path]
    inventory = set()
    for commit in (before, target):
        tree = git("ls-tree", "-r", "--name-only", "-z", commit)
        if len(tree) > 4 * 1024 * 1024:
            raise ValueError("Git tree inventory exceeds bound.")
        inventory.update(path for path in tree.decode().split("\0") if path)

    def read_blob(commit, path):
        entry = git("ls-tree", "-z", commit, "--", path)
        if not entry:
            return None
        header, _ = entry.rstrip(b"\0").split(b"\t", 1)
        mode, kind, oid = header.split()
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ValueError(f"Ordinary Git blob required: {path}")
        if int(git("cat-file", "-s", oid.decode())) > 2 * 1024 * 1024:
            raise ValueError(f"Source member exceeds bound: {path}")
        return git("cat-file", "blob", oid.decode())

    installed = (
        json.loads(Path(args.installed_tool_manifest).read_bytes())
        if args.installed_tool_manifest
        else None
    )
    result = classify(
        before,
        target,
        paths,
        read_blob,
        installed,
        policy_sha256=sha256(
            Path(__file__).with_name("prepare_k98_update.py").read_bytes().replace(b"\r\n", b"\n")
        ),
        inventory_paths=inventory,
        registry_sha256=sha256(
            Path(__file__)
            .with_name("k98_update_transitions.json")
            .read_bytes()
            .replace(b"\r\n", b"\n")
        ),
    )
    print(json.dumps(result, indent=2))
    return COORDINATED_RELEASE_EXIT if result["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
