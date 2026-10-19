"""Pure fresh-incarnation derivation from an administrator-reviewed deployment.

Deployment/review identities and historical observations stay fixed. Only the
current ordinary token observation, instance paths and IPC nonce are renewed.
No process, filesystem, SQL or provider action occurs in this module.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import PureWindowsPath
import re

from core.export_process_identity import validate_process_descriptor, validate_token_profile
from core.export_process_pair import validate_plan
from services.export_execution_protocol import encode, uuid_text

RECORDS = frozenset(
    {
        "host_acl",
        "bot_identity",
        "identity_issuance",
        "file_access",
        "sql_installation",
        "key_inventory",
        "writer_drain",
    }
)


def validate_issuer_record(record, plan, raw):
    if (
        not isinstance(record, dict)
        or set(record) != {"version", "issuer", "pipe_id", "plan_sha256"}
        or type(record["version"]) is not int
        or record["version"] != 1
    ):
        raise ValueError("Exact protected startup issuer record required.")
    uuid_text(record["pipe_id"])
    if record["plan_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("Issuer record belongs to another incarnation.")
    issuer = record["issuer"]
    validate_process_descriptor(issuer, plan["application_sid"])
    profile = issuer["token_profile"]
    if (
        not profile["elevated"]
        or profile["ui_access"]
        or profile["elevation_type"] != 2
        or PureWindowsPath(issuer["executable"]) != PureWindowsPath(plan["python"])
        or issuer["sha256"] != plan["python_sha256"]
    ):
        raise ValueError("Pinned administrative startup issuer required.")
    return issuer


def verify_automatic_token(actual, reviewed, sid):
    """Permit only the native logon SID to change within the reviewed profile."""
    for profile in (actual, reviewed):
        validate_token_profile(profile, sid)
        if profile["elevated"] or profile["ui_access"] or profile["elevation_type"] != 3:
            raise ValueError("Reviewed filtered interactive application token required.")
        logons = [s for s in profile["group_sids"] if re.fullmatch(r"S-1-5-5-[0-9]+-[0-9]+", s)]
        if len(logons) != 1:
            raise ValueError("Exactly one native interactive logon SID required.")
    normalized = []
    for profile in (actual, reviewed):
        value = deepcopy(profile)
        value["group_sids"] = [
            s for s in value["group_sids"] if not re.fullmatch(r"S-1-5-5-[0-9]+-[0-9]+", s)
        ]
        normalized.append(value)
    if normalized[0] != normalized[1]:
        raise ValueError("Application identity, groups or privileges changed.")


def incarnation_files(plan, templates, records, *, profile, directory, nonce, observed_utc):
    """Return ten immutable files; publisher still verifies actual live handles."""
    validate_plan(plan)
    if set(templates) != {"authority", "bot"} or set(records) != RECORDS:
        raise ValueError("Exact reviewed templates and seven observations required.")
    for expected in plan["token_profiles"].values():
        verify_automatic_token(profile, expected, plan["application_sid"])
    instant = datetime.fromisoformat(observed_utc.replace("Z", "+00:00"))
    if instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0:
        raise ValueError("Current native observation must use UTC.")
    uuid_text(nonce)
    target = PureWindowsPath(directory)
    old_parent = PureWindowsPath(plan["commit_file"]).parent
    if (
        not target.is_absolute()
        or target.parent != old_parent.parent
        or target.name != nonce
        or target == old_parent
    ):
        raise ValueError("Fresh sibling incarnation directory required.")
    candidate = deepcopy(templates)
    authority, bot = candidate["authority"], candidate["bot"]
    boundary = authority["deployment_boundary"]
    if (
        boundary.get("version") != 5
        or boundary.get("process_bindings") is not None
        or authority.get("process_bindings") is not None
        or bot["authority"].get("process_bindings") is not None
        or bot["authority"].get("deployment_hash") is not None
    ):
        raise ValueError("Unbound version-five deployment templates required.")
    if set(boundary["review"]["records"]) != RECORDS:
        raise ValueError("Complete reviewed record references required.")
    output = {}
    for kind in sorted(RECORDS):
        record = deepcopy(records[kind])
        if (
            record.get("kind") != kind
            or record.get("deployment_id") != boundary["deployment_id"]
            or record.get("review_id") != boundary["review"]["review_id"]
            or record.get("trust_model") != authority["trust_model"]
            or record.get("version") != 5
        ):
            raise ValueError("Historical review belongs to another deployment.")
        if (
            hashlib.sha256(encode(record)).hexdigest()
            != boundary["review"]["records"][kind]["sha256"]
        ):
            raise ValueError("Reviewed record bytes differ.")
        if kind == "bot_identity":
            record["observations"] = [
                dict(profile, host=deepcopy(boundary["host"]), observed_utc=observed_utc)
            ]
        raw = encode(record)
        output[kind + ".json"] = raw
        boundary["review"]["records"][kind] = dict(
            path=str(target / (kind + ".json")), sha256=hashlib.sha256(raw).hexdigest()
        )
    authority["pipe_id"] = bot["authority"]["pipe_id"] = nonce
    renewed = deepcopy(plan)
    renewed["token_profiles"] = {role: deepcopy(profile) for role in candidate}
    renewed["commit_file"] = str(target / "commit.json")
    for role, template in candidate.items():
        raw = encode(template)
        output[role + "-template.json"] = raw
        renewed["templates"][role] = dict(
            path=str(target / (role + "-template.json")), sha256=hashlib.sha256(raw).hexdigest()
        )
        renewed["manifests"][role] = str(target / (role + "-manifest.json"))
    validate_plan(renewed)
    output["ManualProcessPairPlan-CANDIDATE.json"] = encode(renewed)
    return output, renewed, candidate
