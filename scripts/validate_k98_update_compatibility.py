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

from scripts.prepare_k98_update import TOOL_SOURCE_PATHS, check_source_only, sha256


def classify(before, target, paths, read_blob, installed_tool=None, *, policy_sha256=None):
    blockers, tool_changes = [], []
    if installed_tool is not None:
        expected = {Path(path).name for path in TOOL_SOURCE_PATHS} | {"EmptyGitConfig.txt"}
        if (
            not isinstance(installed_tool, dict)
            or set(installed_tool) != {"version", "files"}
            or type(installed_tool["version"]) is not int
            or installed_tool["version"] != 1
            or not isinstance(installed_tool["files"], dict)
            or set(installed_tool["files"]) != expected
            or any(
                not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                for value in installed_tool["files"].values()
            )
        ):
            raise ValueError("Exact version-1, eight-member installed-tool manifest required.")
    if installed_tool is not None and policy_sha256 is not None:
        if installed_tool.get("files", {}).get("prepare_k98_update.py") != policy_sha256:
            tool_changes.append("scripts/prepare_k98_update.py")
    for path in paths:
        if path in TOOL_SOURCE_PATHS:
            raw = read_blob(target, path)
            if raw is None:
                blockers.append(f"Updater member removal is unsupported: {path}")
            elif installed_tool is None or installed_tool.get("files", {}).get(
                Path(path).name
            ) != sha256(raw):
                if path not in tool_changes:
                    tool_changes.append(path)
        try:
            check_source_only(
                [path],
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
            else "UPDATER_UPGRADE_REQUIRED" if tool_changes else "ROUTINE_COMPATIBLE"
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
    )
    print(json.dumps(result, indent=2))
    return 1 if result["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
