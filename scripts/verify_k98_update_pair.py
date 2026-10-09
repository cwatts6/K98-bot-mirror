"""Verify the release's first protected publication and three live native identities.

Read-only. Invoke with the pinned installed venv Python after the runner seals this artifact.
No application entry point, SQL connection, recovery or provider work is invoked.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys


def read(path, expected=None, limit=1048576):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit:
        raise ValueError("File exceeds verification bound")
    if expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Pinned bytes differ")
    return raw


def verify_live_source(config, *, predecessor=False):
    """Use the real bootstrap's complete inventory and custody checks, read-only."""
    root = Path(config["root"])
    policy_path = (
        Path(config["old_policy"]["Path"])
        if predecessor
        else Path(config["new_seed_directory"]) / "AutomaticStartupPolicy.json"
    )
    policy_hash = config["old_policy"]["SHA256"] if predecessor else config["new_policy_sha256"]
    pins = config["old_pins"] if predecessor else config["new_pins"]
    policy = json.loads(read(policy_path, policy_hash))
    if policy["source_hashes"] != pins or policy["flags"] != config["flags"]:
        raise ValueError("Source policy or flags differ")
    if not predecessor and policy != config["new_policy"]:
        raise ValueError("Successor policy differs")
    authority_path = root / "scripts/run_export_authority.py"
    read(authority_path, pins["scripts/run_export_authority.py"])
    authority = runpy.run_path(str(authority_path))
    authority["bootstrap"](
        str(policy_path), script=str(root / "scripts/run_export_startup_issuer.py")
    )
    return policy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindings", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if not sys.flags.isolated:
        raise ValueError("Isolated Python required")
    config = json.loads(read(args.bindings, args.sha256))
    policy = verify_live_source(config, predecessor=args.preflight)
    if args.preflight:
        print(json.dumps(dict(stage="PREDECESSOR_LIVE_SOURCE_VERIFIED", sql_connected=False)))
        return
    policy_path = Path(config["new_seed_directory"]) / "AutomaticStartupPolicy.json"
    from core.export_process_identity import open_pinned_process
    from core.export_startup_windows import administrative_path

    def protected(path, expected=None):
        return read(administrative_path(path, private=True), expected)

    protected(args.bindings, args.sha256)
    protected(policy_path, config["new_policy_sha256"])
    state = administrative_path(policy["state_directory"], private=True)
    journals = list(Path(state).glob("incarnation-*.json"))
    if len(journals) != 1:
        raise ValueError("Exactly one first successor required; no second start")
    path = journals[0]
    match = re.fullmatch(
        r"incarnation-([0-9]{20})-([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.json", path.name
    )
    if match is None:
        raise ValueError("Canonical journal filename required")
    journal = json.loads(protected(path))
    predecessor = json.loads(
        protected(config["old_journal"]["Path"], config["old_journal"]["SHA256"])
    )
    sequence = predecessor["sequence"] + 1
    if (
        type(journal["sequence"]) is not int
        or journal["sequence"] != sequence
        or int(match[1]) != sequence
        or journal["policy_sha256"] != config["new_policy_sha256"]
    ):
        raise ValueError("Successor sequence or policy differs")
    seed = json.loads(protected(policy["seed_plan"]["path"], policy["seed_plan"]["sha256"]))
    live = Path(seed["commit_file"]).parent.parent / match[2]
    publication = json.loads(protected(live / "commit.json"))
    if publication != journal["publication"]:
        raise ValueError("Published commit differs from protected history")
    plan = json.loads(
        protected(live / "ManualProcessPairPlan-CANDIDATE.json", publication["plan_sha256"])
    )
    if set(publication["manifests"]) != {"authority", "bot"} or set(journal["bindings"]) != {
        "authority",
        "bot",
    }:
        raise ValueError("Exact supervised pair required")
    for role, digest in publication["manifests"].items():
        protected(plan["manifests"][role], digest)
    issuer = json.loads(protected(live / "AutomaticIssuer.json"))
    if issuer["plan_sha256"] != publication["plan_sha256"]:
        raise ValueError("Issuer plan differs from protected publication")
    bindings = [*journal["bindings"].values(), issuer["issuer"]]
    if len({binding["pid"] for binding in bindings}) != 3:
        raise ValueError("Three distinct process identities required")
    handles = []
    try:
        for binding in bindings:
            handles.append(open_pinned_process(binding["pid"], binding))
        print(
            json.dumps(
                dict(
                    stage="RELEASE_FIRST_PAIR_NATIVE_VERIFIED",
                    sequence=sequence,
                    authority_manifest=publication["manifests"]["authority"],
                    discord_ready_verified=False,
                    sql_connected=False,
                )
            ),
            flush=True,
        )
    finally:
        for handle in handles:
            handle.Close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            json.dumps(
                dict(
                    stage="STOP_NEW_PAIR_UNCONFIRMED",
                    failure_type=type(exc).__name__,
                    detail=str(exc),
                )
            ),
            flush=True,
        )
        raise SystemExit(1)
