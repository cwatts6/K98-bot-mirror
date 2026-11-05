"""Destination proposals cannot change data selection, audience or other pools."""

from copy import deepcopy
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_replacement_plan import replacement_registration
from services.export_runtime_composition import RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture


def legacy_fixture():
    value = registration_fixture(pool_count=2)
    value["legacy_configuration"]["scan_data"].update(
        spreadsheets={"Daily": "legacy-scan_data"},
        grid_ids={"legacy-scan_data": {"Data": 17}},
        exports=[dict(sheet="Daily", query="SELECT 'legacy-scan_data' AS value")],
    )
    value["legacy_file_access"] = {
        "legacy-scan_data": dict(
            editors=[value["service_account_email"]],
            audience="anyone_reader",
            coordination_scope="application_writers_only",
        )
    }
    return value


def test_legacy_proposal_preserves_queries_grids_policy_and_original_registration():
    original = legacy_fixture()
    registered = RuntimeRegistration(original)
    before = deepcopy(original)
    result = replacement_registration(
        registered,
        targets=["legacy-scan_data"],
        replacements={"legacy-scan_data": "fresh-daily"},
        replacement_id=str(uuid4()),
    )
    expected = deepcopy(before)
    scope = expected["legacy_configuration"]["scan_data"]
    scope["destinations"] = ["fresh-daily"]
    scope["spreadsheets"]["Daily"] = "fresh-daily"
    scope["grid_ids"] = {"fresh-daily": {"Data": 17}}
    expected["protected_file_ids"] = sorted(
        "fresh-daily" if f == "legacy-scan_data" else f for f in before["protected_file_ids"]
    )
    expected["legacy_file_access"] = {
        "fresh-daily": before["legacy_file_access"]["legacy-scan_data"]
    }
    assert result["registration"] == expected
    assert result["registration_sha256"] == RuntimeRegistration(expected).fingerprint
    assert result["base_registration_sha256"] == registered.fingerprint
    assert result["pool_registration"] is None
    result["registration"]["account"] = "tampered"
    assert registered.value() == original == before


def test_pool_replacement_keeps_slot_order_audience_and_reader_destination():
    from kvk.models.new_source_reporting import CALCULATION_VERSION

    value = registration_fixture(pool_count=2, slot_count=3)
    old_pool = deepcopy(value["pools"][0])
    value.update(
        version=2,
        reader_exports=[
            dict(
                pool_id=old_pool["pool_id"],
                kvk_no=42,
                guild_id="123456789",
                calculation_version=CALCULATION_VERSION,
            )
        ],
    )
    original = RuntimeRegistration(value)
    targets = sorted([old_pool["index_file_id"], *old_pool["slot_file_ids"]])
    mapping = {f: "fresh-" + f for f in targets}
    replacement_id = str(uuid4())
    result = replacement_registration(
        original,
        targets=targets,
        replacements=mapping,
        replacement_id=replacement_id,
    )
    projected = result["registration"]
    assert projected["pools"][1] == value["pools"][1]
    assert projected["legacy_configuration"] == value["legacy_configuration"]
    assert projected["protected_file_ids"] == value["protected_file_ids"]
    assert projected["reader_exports"] == [value["reader_exports"][0] | {"pool_id": replacement_id}]
    replacement = projected["pools"][0]
    assert replacement == old_pool | dict(
        pool_id=replacement_id,
        index_file_id="fresh-index-0",
        slot_file_ids=["fresh-" + f for f in old_pool["slot_file_ids"]],
        registration_sha256=digest(result["pool_registration"]).hex(),
    )
    assert (
        result["pool_registration"]["previous_registration_sha256"]
        == old_pool["registration_sha256"]
    )
    assert original.value() == value


@pytest.mark.parametrize(
    "fresh",
    [
        "index-1",
        "slot-1-0",
        "legacy-config",
        "legacy-scan_data",
        "../file",
        "https://other/file",
        "short",
        None,
    ],
)
def test_fresh_destination_cannot_alias_registered_or_unbounded_input(fresh):
    with pytest.raises(SourceConflict):
        replacement_registration(
            RuntimeRegistration(legacy_fixture()),
            targets=["legacy-scan_data"],
            replacements={"legacy-scan_data": fresh},
            replacement_id=str(uuid4()),
        )


@pytest.mark.parametrize(
    "targets",
    [
        [],
        ["unknown-file"],
        ["legacy-config"],
        ["index-0"],
        ["index-0", "index-1"],
        ["legacy-scan_data", "legacy-scan_data"],
    ],
)
def test_scope_must_be_registered_output_or_one_complete_pool(targets):
    with pytest.raises(SourceConflict):
        replacement_registration(
            RuntimeRegistration(legacy_fixture()),
            targets=targets,
            replacements={f: "fresh-" + f for f in targets},
            replacement_id=str(uuid4()),
        )


def test_shared_legacy_output_updates_both_consumers_without_changing_generation_rules():
    value = legacy_fixture()
    value["legacy_configuration"]["all_kvk"]["destinations"] = ["legacy-scan_data"]
    result = replacement_registration(
        RuntimeRegistration(value),
        targets=["legacy-scan_data"],
        replacements={"legacy-scan_data": "fresh-shared"},
        replacement_id=str(uuid4()),
    )["registration"]
    assert result["legacy_configuration"]["all_kvk"] == value["legacy_configuration"]["all_kvk"] | {
        "destinations": ["fresh-shared"]
    }
    assert result["legacy_configuration"]["config"] == value["legacy_configuration"]["config"]


def test_cannot_reuse_current_pool_identity_or_map_two_outputs_to_one_file():
    value = registration_fixture()
    targets = sorted([value["pools"][0]["index_file_id"], *value["pools"][0]["slot_file_ids"]])
    with pytest.raises(SourceConflict, match="immutable pool"):
        replacement_registration(
            RuntimeRegistration(value),
            targets=targets,
            replacements={f: "fresh-" + f for f in targets},
            replacement_id=value["pools"][0]["pool_id"],
        )
    with pytest.raises(SourceConflict, match="distinct fresh"):
        replacement_registration(
            RuntimeRegistration(value),
            targets=targets,
            replacements={f: "fresh-shared" for f in targets},
            replacement_id=str(uuid4()),
        )
