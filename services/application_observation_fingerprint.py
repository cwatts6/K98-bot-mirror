"""Explicit observer successor format; historical application hashes stay exact.

Only the six source-pinned procedures and four protocol triggers admit the
qualified header/LF transport form. Every body byte and other catalogue field
remains part of the complete fingerprint.
"""

import hashlib
import json

from kvk.dal.new_source_import_dal import digest
from services.catalogue_observation_contract import reviewed_protocol_modules
from services.catalogue_observation_dal import canonical_module
from services.export_contract_resources import read_contract_resource
from services.export_execution_protocol import encode
from services.export_schema_fingerprint import (
    SchemaFingerprintError,
    canonical_application_metadata,
)

FORMAT = "application_observer_schema_v1"
LEGACY_SOURCE_SHA256 = "3cf2fbef5f1f53e170d7ccc7832bf60870a86dc6fccd5944cfb11555a4631d68"
PROCEDURES = frozenset(
    {
        "dbo.sp_ExcelOutput_ByKVK",
        "dbo.usp_RunMaintenance",
        "dbo.usp_S11ValidateStatsReportStage",
        "dbo.usp_P02BeginCatalogueMutation",
        "dbo.usp_P02EndCatalogueMutation",
        "dbo.usp_P02ReadObservationBoundary",
    }
)
TRIGGERS = {
    "tr_P02HeaderObservation": "dbo.KVKFinalReportHeader",
    "tr_P02KvkWorkObservation": "dbo.MaintenanceKvkWork",
    "tr_P02MaintenanceObservation": "dbo.MaintenanceWork",
}


def reviewed_procedure_hashes():
    try:
        source = json.loads(read_contract_resource("p02_observer_legacy_source.json"))
        if digest(source).hex() != LEGACY_SOURCE_SHA256:
            raise ValueError("Observer legacy source differs")
        rows = [row for row in source["modules"] if "definition_format" in row]
        if (
            len(rows) != len(PROCEDURES)
            or {row["name"] for row in rows} != PROCEDURES
            or any(row["definition_format"] != "module_header_lf_body_exact_v1" for row in rows)
        ):
            raise ValueError("Observer procedure source closure differs")
        return {row["name"]: row["definition_sha256"] for row in rows}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SchemaFingerprintError(
            "Exact reviewed observer procedure source required."
        ) from error


def canonical_observer_metadata(metadata, identity, *, protocol_sha256=None):
    result = canonical_application_metadata(metadata, identity)
    procedure_hashes = reviewed_procedure_hashes()
    protocol = (
        reviewed_protocol_modules()
        if protocol_sha256 is None
        else reviewed_protocol_modules(protocol_sha256)
    )
    seen = set()
    for category in ("objects", "triggers", "database_triggers"):
        for row in result["metadata"][category]:
            name = row["ObjectName"] if category == "objects" else row["TriggerName"]
            if category == "objects" and name in PROCEDURES:
                if row["ObjectType"] != "P":
                    raise SchemaFingerprintError("Observer procedure kind differs.")
                body = canonical_module(row["ModuleDefinition"])
                if hashlib.sha256(body.encode("utf-16-le")).hexdigest() != procedure_hashes[name]:
                    raise SchemaFingerprintError(
                        "Observer procedure body differs from reviewed source."
                    )
            elif category == "triggers" and name in TRIGGERS:
                if row["ObjectName"] != TRIGGERS[name]:
                    raise SchemaFingerprintError("Observer lifecycle trigger parent differs.")
                body = canonical_module(row["ModuleDefinition"])
                if body != canonical_module(protocol[name]):
                    raise SchemaFingerprintError(
                        "Observer trigger body differs from reviewed source."
                    )
            elif category == "database_triggers" and name == "tr_P02CatalogueObservation":
                body = canonical_module(row["ModuleDefinition"])
                if body != canonical_module(protocol[name]):
                    raise SchemaFingerprintError(
                        "Observer database trigger differs from reviewed source."
                    )
            else:
                continue
            if name in seen:
                raise SchemaFingerprintError("Duplicate observer module identity.")
            seen.add(name)
            row["ModuleDefinition"] = body
        result["metadata"][category].sort(key=encode)
    if seen != PROCEDURES | TRIGGERS.keys() | {"tr_P02CatalogueObservation"}:
        raise SchemaFingerprintError("Complete observer source closure required.")
    result["format"] = FORMAT
    return result
