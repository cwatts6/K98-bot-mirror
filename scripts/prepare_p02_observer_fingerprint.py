"""Derive the complete successor metadata from accepted history and pinned SQL.

The native candidate is a comparison only. It cannot supply expected rows or
replace the three dynamic outputs absent from the representative observation.
This offline source projection is not a migration/installation approval.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_p02_observer_contract_sources import _definition
from scripts.project_application_permissions import project_new_object_permissions
from services.application_maintenance_contract import POLICY, canonical_lifecycle_metadata
from services.application_observation_fingerprint import (
    FORMAT,
    PROCEDURES,
    TRIGGERS,
    reviewed_procedure_hashes,
)
from services.catalogue_observation_contract import reviewed_protocol_modules
from services.catalogue_observation_dal import canonical_module
from services.export_contract_resources import read_contract_resource
from services.export_execution_protocol import encode

BASELINE_ARCHIVE = "64a8e25120771ec6ee4ce000cdc29ab9ae57ae9866f772ec2af435766c90fba0"
BASELINE_ROWS = "6917c822f5d4b34a3a79a9158b42627621bdf6b9a459f7de4bf1dceea6848e37"
BASELINE_OBSERVATION = "3d5fe82e4dac1cb1bcb27d6bc07e8f913ca5eff380da1d14127dc68ff2c2736a"
BASELINE_METADATA = "a78e17b2874340067d39b2ba49754b506b0d6dd965e21ae89276644b91113003"
BASELINE_PERMISSIONS = "2d1a6328f6310b3912a49ee0c793feb82334cb82a13e1f1c1d573350329d2767"
NATIVE_OBSERVATION = "de8bb1eb5acfdf0e1ae8a3ecdfd9ecebb510593ecb6bf23c35d9dac1ddd138b4"
AMENDED = frozenset(
    {
        "dbo.sp_ExcelOutput_ByKVK",
        "dbo.usp_RunMaintenance",
        "dbo.usp_S11ValidateStatsReportStage",
    }
)
UNOBSERVED = frozenset(
    {"dbo.EXCEL_EXPORT_KVK_TARGETS_16", "dbo.EXCEL_OUTPUT_KVK_TARGETS_16", "dbo.TARGETS_16"}
)
POLICY_SHAPE = dict(
    version=3,
    d4_installation="20261111_001_p02_d4_combined",
    maintenance_policy=POLICY,
    dynamic_objects=[
        dict(name="dbo.EXCEL_FOR_KVK_16", type="U", producer_modules=["dbo.sp_ExcelOutput_ByKVK"])
    ],
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(baseline_archive, sql_root, native_path, output):
    baseline_archive, sql_root, native_path, output = map(
        Path, (baseline_archive, sql_root, native_path, output)
    )
    if output.exists():
        raise ValueError("New source projection directory required")
    assert sha(baseline_archive.read_bytes()) == BASELINE_ARCHIVE
    with zipfile.ZipFile(baseline_archive) as archive:
        raw = archive.read("run-01/observations.jsonl")
    assert sha(raw) == BASELINE_ROWS
    observations = [json.loads(line) for line in raw.splitlines()]
    before = next(
        row["observation"] for row in observations if row["stage"] == "application_sql_contract"
    )
    assert sha(encode(before)) == BASELINE_OBSERVATION
    canonical_before = canonical_lifecycle_metadata(before, POLICY_SHAPE)
    assert sha(encode(canonical_before)) == BASELINE_METADATA

    source = json.loads(read_contract_resource("p02_observer_legacy_source.json"))
    pinned = reviewed_procedure_hashes()  # Authenticates the complete source inventory.
    definitions = {}
    source_files = {}
    for row in source["modules"]:
        if row["name"] not in PROCEDURES:
            continue
        raw = (sql_root / row["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert sha(raw) == row["source_sha256"], row["name"]
        body = canonical_module(_definition(raw, "PROCEDURE"))
        assert sha(body.encode("utf-16-le")) == pinned[row["name"]]
        assert all(
            re.search(setting, raw.decode("utf-8-sig"), re.I)
            for setting in (r"SET\s+ANSI_NULLS\s+ON", r"SET\s+QUOTED_IDENTIFIER\s+ON")
        )
        definitions[row["name"]] = body
        source_files[row["path"]] = sha(raw)
    assert set(definitions) == PROCEDURES
    protocol = reviewed_protocol_modules()
    expected = deepcopy(canonical_before)
    expected["format"] = FORMAT
    metadata = expected["metadata"]
    objects = {row["ObjectName"]: row for row in metadata["objects"]}
    assert AMENDED <= objects.keys() and not (PROCEDURES - AMENDED) & objects.keys()
    for name, body in definitions.items():
        descriptor = dict(
            ObjectName=name,
            ObjectType="P",
            AnsiNulls=True,
            QuotedIdentifier=True,
            ExecuteAsPrincipal=None,
            MemoryOptimized=None,
            TemporalType=None,
        )
        if name in AMENDED:
            assert {k: v for k, v in objects[name].items() if k != "ModuleDefinition"} == descriptor
        objects[name] = dict(descriptor, ModuleDefinition=body)
    metadata["objects"] = list(objects.values())
    for name, parent in TRIGGERS.items():
        assert not any(row["TriggerName"] == name for row in metadata["triggers"])
        metadata["triggers"].append(
            dict(
                ObjectName=parent,
                TriggerName=name,
                ModuleDefinition=canonical_module(protocol[name]),
                Disabled=False,
                InsteadOf=False,
                NotForReplication=False,
                AnsiNulls=True,
                QuotedIdentifier=True,
                ExecuteAsPrincipal=None,
            )
        )
    name = "tr_P02CatalogueObservation"
    assert not any(row["TriggerName"] == name for row in metadata["database_triggers"])
    metadata["database_triggers"].append(
        dict(
            TriggerName=name,
            Disabled=False,
            ExecuteAsPrincipal=None,
            ModuleDefinition=canonical_module(protocol[name]),
        )
    )
    edges = {(name, "usp_P02BeginCatalogueMutation") for name in AMENDED}
    edges |= {
        ("dbo.usp_RunMaintenance", "usp_P02EndCatalogueMutation"),
        ("dbo.usp_P02BeginCatalogueMutation", "P02ObservationGeneration"),
    }
    for origin, target in sorted(edges):
        pattern = (
            r"NEXT\s+VALUE\s+FOR\s+dbo\."
            if target == "P02ObservationGeneration"
            else r"EXEC\s+dbo\."
        )
        assert re.search(pattern + re.escape(target) + r"\b", definitions[origin], re.I)
        row = dict(
            ObjectName=origin,
            Origin=dict(kind="object", name=None),
            ReferencedClass=1,
            ReferencedColumn=None,
            ServerName=None,
            DatabaseName=None,
            SchemaName="dbo",
            EntityName=target,
            SchemaBound=False,
            CallerDependent=False,
            Ambiguous=False,
        )
        assert row not in metadata["dependencies"]
        metadata["dependencies"].append(row)
    for category in metadata:
        metadata[category].sort(key=encode)

    permissions = {
        section: deepcopy(before[section])
        for section in ("schema_permissions", "object_permissions", "column_permissions")
    }
    assert sha(encode(permissions)) == BASELINE_PERMISSIONS
    denials = [row for row in source["grants"] if row.get("state") == "D"]
    assert len(denials) == 3 and {row["target"] for row in denials} == set(TRIGGERS.values())
    for row in denials:
        assert (
            row["database"] == "ROK_TRACKER"
            and row["principal"] == "ExportLegacyEntryReader"
            and row["securable_class"] == "OBJECT"
            and row["permission"] == "ALTER"
        )
        removed = dict(ObjectName=row["target"], PermissionName="ALTER", Subentity="")
        assert permissions["object_permissions"].count(removed) == 1
        permissions["object_permissions"].remove(removed)
    new_objects = PROCEDURES - AMENDED
    grants = [row for row in source["grants"] if row["target"] in new_objects]
    assert len(grants) == 3 and {row["target"] for row in grants} == new_objects
    assert all(
        row["database"] == "ROK_TRACKER"
        and row["principal"] == "ExportLegacyEntryReader"
        and row["securable_class"] == "OBJECT"
        and row["permission"] == "EXECUTE"
        and row.get("state", "G") == "G"
        for row in grants
    )
    # Existing schema ALTER and database VIEW DEFINITION apply to each new
    # procedure. Preserve the native collation's qualified within-object order.
    additions = dict(
        schema_permissions=deepcopy(permissions["schema_permissions"]),
        object_permissions=[
            dict(ObjectName=name, PermissionName=permission, Subentity="")
            for name in sorted(new_objects)
            for permission in ("ALTER", "EXECUTE", "VIEW DEFINITION")
        ],
        column_permissions=[],
    )
    permissions = project_new_object_permissions(
        permissions,
        additions,
        before_sha256=sha(encode(permissions)),
        new_objects=new_objects,
    )

    raw = native_path.read_bytes()
    assert sha(raw) == NATIVE_OBSERVATION
    native = json.loads(raw)["value"]
    actual = canonical_lifecycle_metadata(
        native,
        dict(POLICY_SHAPE, fingerprint_format=FORMAT),
        observation_guard="catalogue_generation_v1",
    )
    selected = deepcopy(expected)
    for category in selected["metadata"]:
        selected["metadata"][category] = [
            row
            for row in selected["metadata"][category]
            if row.get("ObjectName", row.get("object")) not in UNOBSERVED
        ]
    assert actual == selected, "Source projection does not explain the entire retained candidate"
    for section, rows in permissions.items():
        assert native[section] == [
            row for row in rows if row.get("ObjectName") not in UNOBSERVED
        ], section
    output.mkdir()
    (output / "expected-metadata.json").write_bytes(encode(expected))
    (output / "expected-permissions.json").write_bytes(encode(permissions))
    report = dict(
        schema="p02-observer-metadata-projection/1",
        status="candidate_not_release_authority",
        before_metadata_sha256=BASELINE_METADATA,
        expected_metadata_sha256=sha(encode(expected)),
        before_permission_sha256=BASELINE_PERMISSIONS,
        expected_permission_sha256=sha(encode(permissions)),
        format=FORMAT,
        source_files=source_files,
        procedures_changed=sorted(AMENDED),
        procedures_added=sorted(PROCEDURES - AMENDED),
        triggers_added=sorted([*TRIGGERS, "tr_P02CatalogueObservation"]),
        dependency_edges_added=sorted(edges),
        native_subset_matches_exactly=True,
        unobserved_dynamic_objects=sorted(UNOBSERVED),
        expected_objects=len(metadata["objects"]),
        expected_source_plus_dynamic_scope=487,
        missing_native_rows={
            category: len(rows) - len(selected["metadata"][category])
            for category, rows in metadata.items()
            if rows != selected["metadata"][category]
        },
        native_permission_subset_matches_exactly=True,
        protected_contracts_issued=False,
        migration_contract_completed=False,
        production_operations=0,
    )
    (output / "projection.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-archive", required=True)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--native-observation", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            prepare(args.baseline_archive, args.sql_root, args.native_observation, args.output),
            indent=2,
        )
    )
