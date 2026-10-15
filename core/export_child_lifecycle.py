"""Strict private child-birth bindings for restart closure; no process operations here."""

import hashlib
import json
import re

from services.export_execution_protocol import uuid_text


def validate_host_birth(birth):
    if not isinstance(birth, dict) or set(birth) != {
        "child_id",
        "pid",
        "job_name",
        "machine",
        "authority_sid",
        "limit_flags",
        "assigned",
    }:
        raise ValueError("Complete private child birth required.")
    uuid_text(birth["child_id"])
    if (
        type(birth["pid"]) is not int
        or birth["pid"] <= 0
        or not isinstance(birth["job_name"], str)
        or re.fullmatch(r"Global\\K98ExportChild-[0-9a-f]{64}", birth["job_name"]) is None
        or not isinstance(birth["authority_sid"], str)
        or re.fullmatch(r"S-1-[0-9-]+", birth["authority_sid"]) is None
        or type(birth["limit_flags"]) is not int
        or birth["limit_flags"] != 0x2000
        or birth["assigned"] is not True
        or not isinstance(birth["machine"], dict)
        or set(birth["machine"]) != {"machine_guid", "hostname"}
        or not isinstance(birth["machine"]["hostname"], str)
        or not birth["machine"]["hostname"]
    ):
        raise ValueError("Exact contained child birth required.")
    uuid_text(birth["machine"]["machine_guid"])
    return birth


def read_birth(store, stream):
    scope = json.loads(stream["ScopeJson"])
    if set(scope) != {"resources", "host_birth"}:
        raise ValueError("This stream has no bound restart birth evidence.")
    binding = scope["host_birth"]
    if (
        not isinstance(binding, dict)
        or set(binding) != {"reference", "sha256"}
        or not isinstance(binding["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", binding["sha256"]) is None
    ):
        raise ValueError("Exact private child-birth reference required.")
    uuid_text(binding["reference"])
    raw = store.read_reference(binding["reference"], bytes.fromhex(binding["sha256"]))
    if hashlib.sha256(raw).hexdigest() != binding["sha256"]:
        raise ValueError("Private child-birth bytes differ.")
    birth = json.loads(raw)
    if (
        not isinstance(birth, dict)
        or set(birth) != {"kind", "stream_id", "session_id", "account", "host"}
        or (birth["kind"], birth["stream_id"], birth["session_id"], birth["account"])
        != (
            "provider_child_birth/1",
            str(stream["StreamID"]).lower(),
            str(stream["SessionID"]).lower(),
            stream["AccountKey"],
        )
    ):
        raise ValueError("Private child birth belongs to another stream/session/account.")
    host = validate_host_birth(birth["host"])
    if host["child_id"] != str(stream["ChildIdentity"]).lower():
        raise ValueError("Private child birth belongs to another child.")
    return host, binding["sha256"]


def validate_retirement(observed, birth, birth_hash):
    """Validate a trusted host's job-lifecycle observation, not an admin assertion."""
    if (
        observed.get("termination_method") not in {"named_job_destroyed", "named_job_empty"}
        or observed.get("child_id") != birth["child_id"]
        or observed.get("pid") != birth["pid"]
        or observed.get("birth_sha256") != birth_hash
        or observed.get("job_name_sha256") != hashlib.sha256(birth["job_name"].encode()).hexdigest()
        or observed.get("job_empty") is not True
        or observed.get("process_terminated") is not True
    ):
        raise ValueError("Exact named-job retirement observation required.")
