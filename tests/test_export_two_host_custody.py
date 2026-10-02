"""Synthetic two-host records only; no Windows/SQL/provider observation."""

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from uuid import uuid4

import pytest

from core.export_execution_host import DeploymentBoundary, HostBoundaryError
from services.export_execution_protocol import encode
from tests.test_export_single_account import shared_deployment


def fixture(tmp_path):
    m, records, reads = shared_deployment(tmp_path)
    b = m["deployment_boundary"]
    b["version"] = 4
    b["identity"].pop("previous_service_account_email")
    stamp = "2026-09-24T12:00:00Z"
    row = records["identity_issuance"]["observations"][0]
    row.pop("created_utc")
    row["observed_utc"] = row.pop("issued_utc")
    row["reviewing_administrator"] = row.pop("issuing_administrator")
    row["provenance"] = "existing"
    copies = [
        dict(
            host=b["host"],
            role="development",
            user_sid=m["authority_sid"],
            credential_path=m["credentials_file"],
            credential_sha256=b["identity"]["credential_sha256"],
        )
    ]
    copies.append(
        dict(
            host=dict(machine_guid=str(uuid4()), hostname="production-fixture"),
            role="production",
            user_sid="S-1-5-21-111-222-333-777",
            credential_path=r"C:\fixture\key.json",
            credential_sha256=b["identity"]["credential_sha256"],
        )
    )
    custody = dict(
        version=1,
        copies=copies,
        active_host=b["host"],
        window_id=str(uuid4()),
        not_before_utc=stamp,
        dispatch_until_utc="2026-09-24T13:00:00Z",
        release_rule="explicit_after_all_writer_drain",
    )
    b["key_custody"] = custody
    inventory = records["key_inventory"]["observations"][0]
    inventory.pop("credential_holders")
    inventory["credential_copies"] = deepcopy(copies)
    records["writer_drain"]["observations"] = [
        dict(
            host=c["host"],
            window_id=custody["window_id"],
            writer_inventory=["fixture-writer"],
            launch_controls=[
                dict(
                    writer="fixture-writer",
                    mechanism="scheduled_task",
                    state="disabled_until_explicit_release",
                    evidence_sha256="a" * 64,
                )
            ],
            processes=[],
            sql_sessions=[],
            remaining_writers=[],
            observed_utc=stamp,
            reviewer=b["review"]["administrators"]["windows"],
            release_rule=custody["release_rule"],
        )
        for c in copies
    ]
    reads["now"] = lambda: datetime(2026, 9, 24, 12, 1, tzinfo=UTC)
    return m, records, reads


def seal(m, records):
    for kind, record in records.items():
        record["version"] = 4
        ref = m["deployment_boundary"]["review"]["records"][kind]
        raw = encode(record)
        Path(ref["path"]).write_bytes(raw)
        ref["sha256"] = hashlib.sha256(raw).hexdigest()


def test_both_custody_identities_required_without_fabricated_exited_processes(tmp_path):
    m, records, reads = fixture(tmp_path)
    seal(m, records)
    boundary = DeploymentBoundary(m, **reads)
    assert boundary.recheck() == boundary.fingerprint
    boundary._now = lambda: datetime(2026, 9, 24, 13, tzinfo=UTC)
    with pytest.raises(HostBoundaryError, match="window"):
        boundary.recheck()


@pytest.mark.parametrize(
    "damage",
    [
        "missing_host",
        "extra_copy",
        "different_key",
        "enabled_launcher",
        "remaining_writer",
        "wrong_window",
        "foreign_reviewer",
        "automatic_release",
        "future_observation",
        "missing_inventory",
        "empty_controls",
        "old_sid_list",
        "relative_path",
        "duplicate_host",
        "empty_window",
        "future_window",
        "unclosed_process",
        "unclosed_sql",
    ],
)
def test_two_host_contract_fails_closed(tmp_path, damage):
    m, r, reads = fixture(tmp_path)
    b = m["deployment_boundary"]
    c = b["key_custody"]
    w = r["writer_drain"]["observations"][1]
    if damage == "missing_host":
        r["writer_drain"]["observations"].pop()
    elif damage == "extra_copy":
        c["copies"].append(deepcopy(c["copies"][1]))
    elif damage == "different_key":
        r["key_inventory"]["observations"][0]["user_managed_key_ids"].append("b" * 40)
    elif damage == "enabled_launcher":
        w["launch_controls"][0]["state"] = "enabled"
    elif damage == "remaining_writer":
        w["remaining_writers"] = ["pid:123"]
    elif damage == "wrong_window":
        w["window_id"] = str(uuid4())
    elif damage == "foreign_reviewer":
        w["reviewer"] = "unknown"
    elif damage == "automatic_release":
        c["release_rule"] = "on_expiry"
    elif damage == "future_observation":
        w["observed_utc"] = "2026-09-24T12:30:00Z"
    elif damage == "missing_inventory":
        w["writer_inventory"] = []
    elif damage == "empty_controls":
        w["launch_controls"] = []
    elif damage == "old_sid_list":
        r["key_inventory"]["observations"][0]["credential_holders"] = [m["authority_sid"]]
    elif damage == "relative_path":
        c["copies"][1]["credential_path"] = "key.json"
    elif damage == "duplicate_host":
        c["copies"][1]["host"] = deepcopy(c["copies"][0]["host"])
    elif damage == "empty_window":
        c["dispatch_until_utc"] = c["not_before_utc"]
    elif damage == "future_window":
        c["not_before_utc"] = "2026-09-24T12:30:00Z"
    elif damage == "unclosed_process":
        w["processes"] = [dict(pid=123, started_utc=w["observed_utc"], image_sha256="a" * 64)]
    elif damage == "unclosed_sql":
        w["sql_sessions"] = [dict(session_id=51, login_name="fixture")]
    seal(m, r)
    with pytest.raises(HostBoundaryError):
        DeploymentBoundary(m, **reads)
