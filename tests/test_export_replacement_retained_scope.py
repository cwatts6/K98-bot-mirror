"""Unrelated registration changes do not strand immutable queued legacy work."""

from copy import deepcopy
import json

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_runtime_composition import RuntimeRegistration, _legacy_configuration
from services.legacy_export_snapshot_service import configuration_digest
from tests.test_export_runtime_composition import legacy_stream_fixture, registration_fixture


def scope_fixture():
    old = registration_fixture()
    old["legacy_configuration"]["scan_data"]["destinations"].append("other-old-file")
    old["protected_file_ids"] = sorted([*old["protected_file_ids"], "other-old-file"])
    new = deepcopy(old)
    new["legacy_configuration"]["scan_data"]["destinations"][-1] = "other-new-file"
    new["protected_file_ids"] = sorted(
        f for f in new["protected_file_ids"] if f != "other-old-file"
    ) + ["other-new-file"]
    new["protected_file_ids"].sort()
    scope = dict(
        AccountKey="account-a",
        OwnerKind="job",
        Purpose="mutation",
        Epoch=None,
        NestedToken=None,
        RegistrationHash=configuration_digest(old["legacy_configuration"]["scan_data"]),
        ScopeJson=dict(
            resources=[
                dict(key="account:account-a", version=1),
                dict(key="destination:legacy-scan_data", version=1),
            ]
        ),
    )
    return RuntimeRegistration(old), RuntimeRegistration(new), scope


def test_only_unchanged_destinations_can_use_retained_registration():
    old, current, scope = scope_fixture()
    with pytest.raises(SourceConflict):
        current.authorize_scope(scope)
    current.authorize_retained_scope(scope, (old, current))
    with pytest.raises(SourceConflict):
        current.authorize_retained_scope(scope, (current,))
    scope["ScopeJson"]["resources"][-1]["key"] = "destination:other-old-file"
    with pytest.raises(SourceConflict, match="destinations"):
        current.authorize_retained_scope(scope, (old, current))


@pytest.mark.parametrize("damage", ["grid", "owner_kind", "purpose", "account"])
def test_retained_history_cannot_override_new_scope_policy(damage):
    old, current, scope = scope_fixture()
    if damage == "grid":
        value = current.value()
        value["legacy_configuration"]["scan_data"]["grid_ids"] = {
            "legacy-scan_data": {"Report": 99}
        }
        current = RuntimeRegistration(value)
    elif damage == "owner_kind":
        scope["OwnerKind"] = "preparation"
    elif damage == "purpose":
        scope["Purpose"] = "probe"
    else:
        scope["AccountKey"] = "other-account"
    with pytest.raises(SourceConflict):
        current.authorize_retained_scope(scope, (old, current))


def test_legacy_stream_uses_original_capture_hash_after_unrelated_registration_change():
    f = legacy_stream_fixture(consumer="scan_data")
    before = f.streams.configuration_json
    changed = json.loads(before)
    changed["scan_data"]["destinations"].append("new-other-output")
    f.streams.configuration_json = _legacy_configuration(changed)
    f.streams.configuration_history = (before, f.streams.configuration_json)
    f.streams.delivery(f.row, f.claim, f.files)
    assert f.client.stream.call_args.args[0]["RegistrationHash"] == configuration_digest(
        f.configuration["scan_data"]
    )
    changed["scan_data"]["destinations"].remove(f.files[0])
    f.streams.configuration_json = _legacy_configuration(changed)
    with pytest.raises(SourceConflict):
        f.streams.delivery(f.row, f.claim, f.files)
