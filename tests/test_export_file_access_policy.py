import copy
import hashlib
from pathlib import Path

import pytest

from core.export_execution_host import DeploymentBoundary, HostBoundaryError
from services.export_execution_protocol import encode
from services.export_runtime_composition import RuntimeRegistration
from tests.test_export_execution_host import deployment_fixture
from tests.test_export_runtime_composition import registration_fixture


def policy(editor):
    return dict(
        editors=sorted([editor, "outside@example.iam.gserviceaccount.com", "anyone"]),
        audience="anyone_writer",
        coordination_scope="application_writers_only",
    )


def test_registration_preserves_sealed_legacy_policy_and_copies_input():
    value = registration_fixture()
    value["legacy_file_access"] = {"legacy-scan_data": policy(value["service_account_email"])}
    registration = RuntimeRegistration(value)
    original = registration.fingerprint
    value["legacy_file_access"]["legacy-scan_data"]["editors"].append("new@example.com")
    assert registration.fingerprint == original
    assert RuntimeRegistration(registration.value()).fingerprint == original
    assert (
        "new@example.com"
        not in registration.value()["legacy_file_access"]["legacy-scan_data"]["editors"]
    )


@pytest.mark.parametrize(
    "damage",
    [
        "pool",
        "protected_only",
        "missing_authority",
        "duplicate",
        "scope",
        "audience",
        "unknown_field",
        "malformed",
    ],
)
def test_registration_rejects_policy_outside_reviewed_legacy_scope(damage):
    from kvk.dal.new_source_import_dal import SourceConflict

    value = registration_fixture()
    target = "legacy-scan_data"
    entry = policy(value["service_account_email"])
    if damage == "pool":
        target = value["pools"][0]["index_file_id"]
    elif damage == "protected_only":
        value["protected_file_ids"].append("excluded-file")
        value["protected_file_ids"].sort()
        target = "excluded-file"
    elif damage == "missing_authority":
        entry["editors"].remove(value["service_account_email"])
    elif damage == "duplicate":
        entry["editors"].append(entry["editors"][0])
    elif damage == "scope":
        entry["coordination_scope"] = "all_writers"
    elif damage == "audience":
        entry["audience"] = "anyone_reader"
    elif damage == "unknown_field":
        entry["approved"] = True
    else:
        entry["editors"] = [None]
    value["legacy_file_access"] = {target: entry}
    with pytest.raises(SourceConflict):
        RuntimeRegistration(value)


def sealed_fixture(tmp_path):
    manifest, records, reads = deployment_fixture(tmp_path)
    entry = policy(manifest["service_account_email"])
    manifest["runtime_registration"]["legacy_file_access"] = {"legacy-scan_data": entry}
    manifest["deployment_boundary"]["registration_hash"] = hashlib.sha256(
        encode(manifest["runtime_registration"])
    ).hexdigest()
    for row in records["file_access"]["observations"]:
        if row["file_id"] == "legacy-scan_data":
            row.update(editors=copy.deepcopy(entry["editors"]), audience=entry["audience"])
    reseal(manifest, records)
    return manifest, records, reads


def reseal(manifest, records):
    reference = manifest["deployment_boundary"]["review"]["records"]["file_access"]
    raw = encode(records["file_access"])
    Path(reference["path"]).write_bytes(raw)
    reference["sha256"] = hashlib.sha256(raw).hexdigest()


def test_boundary_accepts_exact_legacy_sharing_without_widening_pools(tmp_path):
    manifest, _, reads = sealed_fixture(tmp_path)
    assert DeploymentBoundary(manifest, **reads).recheck()


@pytest.mark.parametrize(
    "damage",
    [
        "extra_editor",
        "missing_editor",
        "audience",
        "owner",
        "pool_editor",
        "pool_policy",
        "unsealed_policy",
    ],
)
def test_boundary_refuses_changed_sharing_or_pool_exception(tmp_path, damage):
    manifest, records, reads = sealed_fixture(tmp_path)
    rows = records["file_access"]["observations"]
    legacy = next(row for row in rows if row["file_id"] == "legacy-scan_data")
    pool_id = manifest["runtime_registration"]["pools"][0]["index_file_id"]
    if damage == "extra_editor":
        legacy["editors"].append("new@example.com")
    elif damage == "missing_editor":
        legacy["editors"].remove("outside@example.iam.gserviceaccount.com")
    elif damage == "audience":
        legacy["audience"] = "private"
    elif damage == "owner":
        legacy["owner_email"] = "other@example.com"
    elif damage == "pool_editor":
        next(row for row in rows if row["file_id"] == pool_id)["editors"].append(
            "outside@example.com"
        )
    else:
        manifest["runtime_registration"]["legacy_file_access"][pool_id] = policy(
            manifest["service_account_email"]
        )
        if damage == "pool_policy":
            manifest["deployment_boundary"]["registration_hash"] = hashlib.sha256(
                encode(manifest["runtime_registration"])
            ).hexdigest()
    reseal(manifest, records)
    with pytest.raises(HostBoundaryError):
        DeploymentBoundary(manifest, **reads)
