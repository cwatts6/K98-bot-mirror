"""Versioned two-host custody observations; never discovers hosts or credentials.

The trusted operator pins both copies and keeps the other host excluded until
explicit release after drain. A time limit stops new dispatch, not that duty.
This is an application operating contract, not isolation from administrators.
"""

from datetime import UTC, datetime
from pathlib import PureWindowsPath
import re

from services.export_execution_protocol import uuid_text

OPERATOR_TRIGGERS = ["export_commands", "imports"]
OPERATOR_RELEASE = "explicit_after_completion_or_reconciliation"


def validate_operator_control(boundary):
    """Version 5 trusts the named operator, without pretending to disable hosts.

    The enclosing protected deployment record binds source, target and process
    incarnations. This is a per-deployment commitment, not a timed lease, remote
    process observation, or isolation from the trusted administrator.
    """
    control = boundary["operator_control"]
    exact(control, "version operator active_role credential_hosts triggers release_rule")
    if (
        type(control["version"]) is not int
        or control["version"] != 1
        or control["operator"] != boundary["review"]["administrators"]["windows"]
        or control["active_role"] not in {"production", "development"}
        or control["triggers"] != OPERATOR_TRIGGERS
        or control["release_rule"] != OPERATOR_RELEASE
    ):
        raise ValueError("Exact named operator, triggers and explicit release required.")
    hosts = control["credential_hosts"]
    exact(hosts, "production development")
    if (
        any(
            not isinstance(h, str) or not re.fullmatch(r"[a-z0-9_-]{1,63}", h)
            for h in hosts.values()
        )
        or hosts["production"] == hosts["development"]
        or hosts[control["active_role"]] != boundary["host"]["hostname"]
    ):
        raise ValueError("Both known credential hosts and this active host required.")


def validate_operator_observation(kind, row, boundary, *, now=None):
    control = boundary["operator_control"]
    common = "operator observed_utc"
    if kind == "key_inventory":
        exact(row, common + " service_account_email user_managed_key_ids credential_hosts")
        identity = boundary["identity"]
        if (
            row["service_account_email"] != identity["service_account_email"]
            or row["user_managed_key_ids"] != [identity["private_key_id"]]
            or row["credential_hosts"] != control["credential_hosts"]
        ):
            raise ValueError("Sole existing key and two operator-declared copies required.")
    elif kind == "writer_drain":
        exact(
            row,
            common + " deployment_id triggers exclusive_trigger_control "
            "no_outstanding_conflicting_work hold_other_host_triggers release_rule",
        )
        if (
            row["deployment_id"] != boundary["deployment_id"]
            or row["triggers"] != control["triggers"]
            or row["exclusive_trigger_control"] is not True
            or row["no_outstanding_conflicting_work"] is not True
            or row["hold_other_host_triggers"] is not True
            or row["release_rule"] != control["release_rule"]
        ):
            raise ValueError("Explicit per-deployment operator commitment required.")
    else:
        raise ValueError("Unsupported operator observation.")
    if row["operator"] != control["operator"] or instant(row["observed_utc"]) > (
        datetime.now(UTC) if now is None else now
    ):
        raise ValueError("Named operator and non-future confirmation required.")


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Exact UTC time required.")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None or result.utcoffset().total_seconds() != 0:
        raise ValueError("Exact UTC time required.")
    return result


def exact(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError("Exact versioned custody fields required.")


def validate_custody(boundary, manifest, *, now=None):
    """Validate pins and a bounded dispatch window; no live evidence is inferred."""
    value = boundary["key_custody"]
    exact(
        value, "version copies active_host window_id not_before_utc dispatch_until_utc release_rule"
    )
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Custody version differs.")
    uuid_text(value["window_id"])
    start, end = instant(value["not_before_utc"]), instant(value["dispatch_until_utc"])
    current = datetime.now(UTC) if now is None else now
    if not start <= current < end:
        raise ValueError("Custody dispatch window is not current.")
    if value["release_rule"] != "explicit_after_all_writer_drain":
        raise ValueError("Expiry must not release the excluded writer.")
    copies = value["copies"]
    if not isinstance(copies, list) or len(copies) != 2:
        raise ValueError("Exactly the reviewed production and development copies required.")
    ids, roles = set(), set()
    for copy in copies:
        exact(copy, "host role user_sid credential_path credential_sha256")
        host = copy["host"]
        exact(host, "machine_guid hostname")
        uuid_text(host["machine_guid"])
        if not isinstance(host["hostname"], str) or not re.fullmatch(
            r"[a-z0-9_-]{1,63}", host["hostname"]
        ):
            raise ValueError("Canonical host name required.")
        if (
            host["machine_guid"] in ids
            or copy["role"] not in {"production", "development"}
            or copy["role"] in roles
            or not isinstance(copy["user_sid"], str)
            or not re.fullmatch(r"S-1-5-(?:[0-9]+-)*[0-9]+", copy["user_sid"])
            or not isinstance(copy["credential_path"], str)
            or not PureWindowsPath(copy["credential_path"]).is_absolute()
            or copy["credential_sha256"] != boundary["identity"]["credential_sha256"]
        ):
            raise ValueError("Distinct exact host custody bindings required.")
        ids.add(host["machine_guid"])
        roles.add(copy["role"])
    if len({c["host"]["hostname"] for c in copies}) != 2:
        raise ValueError("Distinct host names required.")
    active = [c for c in copies if c["host"] == boundary["host"]]
    if (
        len(active) != 1
        or value["active_host"] != boundary["host"]
        or active[0]["user_sid"] != manifest["authority_sid"]
        or active[0]["credential_path"] != manifest["credentials_file"]
    ):
        raise ValueError("Active credential copy differs from this deployment.")
    return value


def validate_inventory(row, boundary, *, now=None):
    exact(row, "service_account_email user_managed_key_ids credential_copies observed_utc")
    identity, custody = boundary["identity"], boundary["key_custody"]
    observed = instant(row["observed_utc"])
    current = datetime.now(UTC) if now is None else now
    if (
        row["service_account_email"] != identity["service_account_email"]
        or row["user_managed_key_ids"] != [identity["private_key_id"]]
        or row["credential_copies"] != custody["copies"]
        or not instant(custody["not_before_utc"])
        <= observed
        <= current
        < instant(custody["dispatch_until_utc"])
    ):
        raise ValueError("Sole key and both reviewed custody copies required.")


def validate_exclusion(rows, boundary, *, now=None):
    """Both host inventories are closed; inactive launch controls stay disabled.

    Empty exited-process lists are legitimate only with a complete named writer
    inventory and a reviewed no-running-writers observation, never invented PIDs.
    """
    custody = boundary["key_custody"]
    current = datetime.now(UTC) if now is None else now
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("Writer exclusion observations for both hosts required.")
    found = set()
    for row in rows:
        exact(
            row,
            "host window_id writer_inventory launch_controls processes sql_sessions remaining_writers observed_utc reviewer release_rule",
        )
        copy = next((c for c in custody["copies"] if c["host"] == row["host"]), None)
        observed = instant(row["observed_utc"])
        if (
            copy is None
            or copy["role"] in found
            or row["window_id"] != custody["window_id"]
            or row["reviewer"] != boundary["review"]["administrators"]["windows"]
            or row["release_rule"] != custody["release_rule"]
            or row["remaining_writers"] != []
            or not instant(custody["not_before_utc"])
            <= observed
            <= current
            < instant(custody["dispatch_until_utc"])
        ):
            raise ValueError("Exact reviewed host/window exclusion required.")
        found.add(copy["role"])
        writers = row["writer_inventory"]
        controls = row["launch_controls"]
        if (
            not isinstance(writers, list)
            or not writers
            or len(writers) > 32
            or any(not isinstance(w, str) or not w.strip() or len(w) > 256 for w in writers)
            or writers != sorted(set(writers))
            or not isinstance(controls, list)
            or len(controls) != len(writers)
        ):
            raise ValueError("Complete bounded writer and launch-control inventory required.")
        for writer, control in zip(writers, controls, strict=True):
            exact(control, "writer mechanism state evidence_sha256")
            if (
                control["writer"] != writer
                or control["mechanism"] not in {"scheduled_task", "service", "manual_operator"}
                or control["state"] != "disabled_until_explicit_release"
                or not isinstance(control["evidence_sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", control["evidence_sha256"])
            ):
                raise ValueError("Every prior writer launch needs reviewed exclusion evidence.")
        for field in ("processes", "sql_sessions"):
            if not isinstance(row[field], list) or len(row[field]) > 256:
                raise ValueError("Bounded exited-writer observations required.")
        seen = set()
        for p in row["processes"]:
            exact(p, "pid started_utc image_sha256 exit_code exited_utc")
            if (
                type(p["pid"]) is not int
                or p["pid"] <= 0
                or type(p["exit_code"]) is not int
                or not isinstance(p["image_sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", p["image_sha256"])
                or not instant(p["started_utc"]) <= instant(p["exited_utc"]) <= observed
                or (p["pid"], p["started_utc"]) in seen
            ):
                raise ValueError("Exact exited process incarnation required.")
            seen.add((p["pid"], p["started_utc"]))
        seen = set()
        for s in row["sql_sessions"]:
            exact(s, "server database session_id login_name login_utc ended_utc")
            if (
                type(s["session_id"]) is not int
                or s["session_id"] <= 0
                or any(
                    not isinstance(s[k], str) or not s[k].strip()
                    for k in ("server", "database", "login_name")
                )
                or not instant(s["login_utc"]) <= instant(s["ended_utc"]) <= observed
                or (s["server"], s["session_id"], s["login_utc"]) in seen
            ):
                raise ValueError("Exact ended producer SQL session required.")
            seen.add((s["server"], s["session_id"], s["login_utc"]))
