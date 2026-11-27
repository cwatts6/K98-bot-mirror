"""Operator declarations remain distinct from observed process termination."""

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from uuid import uuid4

import pytest

from core.export_execution_host import DeploymentBoundary, HostBoundaryError
from core.export_key_custody import OPERATOR_RELEASE, OPERATOR_TRIGGERS
from services.export_execution_protocol import encode
from tests.test_export_two_host_custody import fixture as two_host_fixture


def fixture(tmp_path):
    m, records, reads = two_host_fixture(tmp_path)
    b = m["deployment_boundary"]
    b["version"] = 5
    b.pop("key_custody")
    control = dict(
        version=1,
        operator=b["review"]["administrators"]["windows"],
        active_role="development",
        credential_hosts={"development": b["host"]["hostname"], "production": "mini_amd"},
        triggers=deepcopy(OPERATOR_TRIGGERS),
        release_rule=OPERATOR_RELEASE,
    )
    b["operator_control"] = control
    common = dict(operator=control["operator"], observed_utc="2026-09-24T12:00:00Z")
    records["key_inventory"]["observations"] = [
        dict(
            **common,
            service_account_email=b["identity"]["service_account_email"],
            user_managed_key_ids=[b["identity"]["private_key_id"]],
            credential_hosts=deepcopy(control["credential_hosts"]),
        )
    ]
    records["writer_drain"]["observations"] = [
        dict(
            **common,
            deployment_id=b["deployment_id"],
            triggers=deepcopy(OPERATOR_TRIGGERS),
            exclusive_trigger_control=True,
            no_outstanding_conflicting_work=True,
            hold_other_host_triggers=True,
            release_rule=OPERATOR_RELEASE,
        )
    ]
    return m, records, reads


def seal(m, records):
    for kind, record in records.items():
        record["version"] = 5
        ref = m["deployment_boundary"]["review"]["records"][kind]
        raw = encode(record)
        Path(ref["path"]).write_bytes(raw)
        ref["sha256"] = hashlib.sha256(raw).hexdigest()


def test_operator_control_needs_no_remote_inventory_or_duration_cap(tmp_path):
    m, records, reads = fixture(tmp_path)
    seal(m, records)
    boundary = DeploymentBoundary(m, **reads)
    boundary._now = lambda: datetime(2026, 10, 2, tzinfo=UTC)
    assert boundary.recheck() == boundary.fingerprint
    # The reviewed commitment cannot be edited/released under a running authority.
    ref = m["deployment_boundary"]["review"]["records"]["writer_drain"]
    Path(ref["path"]).write_bytes(b"{}")
    with pytest.raises(HostBoundaryError, match="record differs"):
        boundary.recheck()


@pytest.mark.parametrize(
    "damage",
    [
        "missing_key",
        "extra_key",
        "unknown_copy",
        "wrong_active_host",
        "duplicate_host",
        "foreign_operator",
        "future_confirmation",
        "foreign_deployment",
        "automatic_release",
        "missing_import_trigger",
        "outstanding_work",
        "hold_false",
        "control_false",
        "integer_confirmation",
        "fake_process_fields",
        "missing_record",
        "mixed_version",
        "old_custody_fields",
        "wrong_trust_model",
    ],
)
def test_operator_mode_rejects_missing_or_contradictory_proof(tmp_path, damage):
    m, r, reads = fixture(tmp_path)
    b = m["deployment_boundary"]
    c = b["operator_control"]
    w = r["writer_drain"]["observations"][0]
    k = r["key_inventory"]["observations"][0]
    if damage == "missing_key":
        k["user_managed_key_ids"] = []
    elif damage == "extra_key":
        k["user_managed_key_ids"].append("a" * 40)
    elif damage == "unknown_copy":
        k["credential_hosts"]["other"] = "other"
    elif damage == "wrong_active_host":
        c["active_role"] = "production"
    elif damage == "duplicate_host":
        c["credential_hosts"]["production"] = b["host"]["hostname"]
    elif damage == "foreign_operator":
        w["operator"] = "someone-else"
    elif damage == "future_confirmation":
        w["observed_utc"] = "2026-10-02T00:00:00Z"
    elif damage == "foreign_deployment":
        w["deployment_id"] = str(uuid4())
    elif damage == "automatic_release":
        c["release_rule"] = "on_expiry"
    elif damage == "missing_import_trigger":
        w["triggers"] = ["export_commands"]
    elif damage == "outstanding_work":
        w["no_outstanding_conflicting_work"] = False
    elif damage == "hold_false":
        w["hold_other_host_triggers"] = False
    elif damage == "control_false":
        w["exclusive_trigger_control"] = False
    elif damage == "integer_confirmation":
        w["hold_other_host_triggers"] = 1
    elif damage == "fake_process_fields":
        w["processes"] = []
    elif damage == "missing_record":
        r["writer_drain"]["observations"] = []
    elif damage == "old_custody_fields":
        b["key_custody"] = {}
    elif damage == "wrong_trust_model":
        m["trust_model"] = "other"
    seal(m, r)
    if damage == "mixed_version":
        r["writer_drain"]["version"] = 4
        ref = b["review"]["records"]["writer_drain"]
        raw = encode(r["writer_drain"])
        Path(ref["path"]).write_bytes(raw)
        ref["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(HostBoundaryError):
        DeploymentBoundary(m, **reads)
