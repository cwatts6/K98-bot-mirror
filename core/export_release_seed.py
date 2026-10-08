"""Derive a reviewed successor seed without inventing fresh runtime observations."""

from copy import deepcopy
import hashlib
from pathlib import PureWindowsPath
import re

from core.export_automatic_pair import RECORDS
from core.export_process_pair import validate_plan
from services.export_execution_protocol import encode, uuid_text


def successor_seed(previous, source_hashes, *, deployment_id, review_id, pipe_id):
    """Pure preparation; installation must verify source, ACLs and unchanged contracts.

    The caller supplies reviewed source hashes, not an observation accepted as its
    own expected value. SQL and dependency observations retain their original dates.
    """
    for value in (deployment_id, review_id, pipe_id):
        uuid_text(value)
    if (
        not isinstance(source_hashes, dict)
        or not 0 < len(source_hashes) <= 4096
        or any(
            not isinstance(path, str)
            or not path.endswith(".py")
            or "\\" in path
            or path.startswith("/")
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or ":" in path
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            for path, digest in source_hashes.items()
        )
    ):
        raise ValueError("Reviewed bounded source inventory required.")
    names = {
        "authority-template.json",
        "bot-template.json",
        "ManualProcessPairPlan-CANDIDATE.json",
        "AutomaticStartupPolicy.json",
        *(kind + ".json" for kind in RECORDS),
    }
    if set(previous) != names:
        raise ValueError("Exact predecessor seed members required.")
    old_policy = previous["AutomaticStartupPolicy.json"]
    old_plan = previous["ManualProcessPairPlan-CANDIDATE.json"]
    validate_plan(old_plan)
    if any(
        previous[name]["source_hashes"] != old_plan["source_hashes"]
        for name in ("authority-template.json", "bot-template.json", "AutomaticStartupPolicy.json")
    ):
        raise ValueError("Predecessor source inventories differ.")
    if hashlib.sha256(encode(old_plan)).hexdigest() != old_policy["seed_plan"]["sha256"]:
        raise ValueError("Predecessor plan checksum differs.")
    old_authority = previous["authority-template.json"]
    boundary = old_authority["deployment_boundary"]
    for role in ("authority", "bot"):
        if (
            hashlib.sha256(encode(previous[role + "-template.json"])).hexdigest()
            != old_plan["templates"][role]["sha256"]
        ):
            raise ValueError("Predecessor template checksum differs.")
    for kind in RECORDS:
        if (
            hashlib.sha256(encode(previous[kind + ".json"])).hexdigest()
            != boundary["review"]["records"][kind]["sha256"]
        ):
            raise ValueError("Predecessor observation checksum differs.")
    replacements = {
        boundary["deployment_id"]: deployment_id,
        boundary["review"]["review_id"]: review_id,
        old_authority["pipe_id"]: pipe_id,
    }
    if (
        len(replacements) != 3
        or len(set(replacements.values())) != 3
        or set(replacements) & set(replacements.values())
    ):
        raise ValueError("Fresh distinct release identities required.")

    def rebase(value):
        if isinstance(value, dict):
            return {key: rebase(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rebase(item) for item in value]
        if isinstance(value, str):
            for old, new in replacements.items():
                value = value.replace(old, new)
        return value

    values = rebase(deepcopy(previous))
    for name in (
        "authority-template.json",
        "bot-template.json",
        "ManualProcessPairPlan-CANDIDATE.json",
    ):
        values[name]["source_hashes"] = deepcopy(source_hashes)
    boundary = values["authority-template.json"]["deployment_boundary"]
    boundary["source_hash"] = hashlib.sha256(encode(source_hashes)).hexdigest()
    for kind, reference in boundary["review"]["records"].items():
        reference["sha256"] = hashlib.sha256(encode(values[kind + ".json"])).hexdigest()
    plan = values["ManualProcessPairPlan-CANDIDATE.json"]
    for role in ("authority", "bot"):
        plan["templates"][role]["sha256"] = hashlib.sha256(
            encode(values[role + "-template.json"])
        ).hexdigest()
    validate_plan(plan)
    target = PureWindowsPath(plan["commit_file"]).parent
    policy = values["AutomaticStartupPolicy.json"]
    policy.update(
        source_hashes=deepcopy(source_hashes),
        seed_plan=dict(
            path=str(target / "ManualProcessPairPlan-CANDIDATE.json"),
            sha256=hashlib.sha256(encode(plan)).hexdigest(),
        ),
        predecessor=dict(
            state_directory=old_policy["state_directory"],
            policy_sha256=hashlib.sha256(encode(old_policy)).hexdigest(),
        ),
    )
    if policy["flags"] != old_policy["flags"]:
        raise ValueError("A release seed must preserve activation flags.")
    return {name: encode(value) for name, value in values.items()}
