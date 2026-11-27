"""Explicit P02 index lifecycle policy; all other schema evidence stays exact.

This classifies a retained observation. It never runs maintenance, changes a
receipt, or infers business completion from a released lock.
"""

import hashlib
import re

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_protocol import encode
from services.export_schema_fingerprint import canonical_application_metadata

POLICY = "p02_kvk_deferred_indexes_v1"
RESOURCE = "K98:maintenance-schema:v1"
PROOF_FIELDS = {
    "ObjectName",
    "ObjectID",
    "ObjectCreated",
    "HeaderRevision",
    "HeaderState",
    "KVKNo",
    "DueGeneration",
    "CompletedGeneration",
    "DueObjectID",
    "DueObjectCreated",
    "DueHeaderRevision",
    "State",
    "ClaimedGeneration",
    "AggregateDue",
    "AggregateCompleted",
    "AggregateState",
}


def _require(condition, message):
    if not condition:
        raise SourceConflict("Deferred maintenance contract: " + message)


def policy_objects(approved):
    """Only explicit D4 dynamic outputs qualify; no wildcard enrolment."""
    if "maintenance_policy" not in approved:
        return ()
    _require(
        approved.get("maintenance_policy") == POLICY
        and approved.get("version") == 3
        and approved.get("d4_installation") == "20261111_001_p02_d4_combined",
        "unsupported policy or installation.",
    )
    result = []
    for row in approved["dynamic_objects"]:
        match = re.fullmatch(r"dbo\.EXCEL_FOR_KVK_([1-9][0-9]{0,9})", row["name"])
        if match:
            season = int(match[1])
            _require(
                season < 2**31
                and row["type"] == "U"
                and "dbo.sp_ExcelOutput_ByKVK" in row["producer_modules"],
                "output is not bound to the reviewed producer.",
            )
            result.append((row["name"], season))
    _require(bool(result), "explicit KVK output inventory required.")
    return tuple(sorted(result))


def expected_index(name, suffix, column):
    """The exact nonunique, unfiltered index emitted by the reviewed worker."""
    return {
        "object": name,
        "identity": {"kind": "named", "name": "IX_" + name[4:] + "_" + suffix},
        "rows": [
            {
                "ObjectName": name,
                "IndexType": 2,
                "IsUnique": False,
                "IsPrimaryKey": False,
                "IsUniqueConstraint": False,
                "Disabled": False,
                "Hypothetical": False,
                "IgnoreDuplicateKey": False,
                "HasFilter": False,
                "FilterDefinition": None,
                "Ordinal": 1,
                "ColumnName": column,
                "KeyOrdinal": 1,
                "PartitionOrdinal": 0,
                "DescendingKey": False,
                "IncludedColumn": False,
            }
        ],
    }


def _generation(value):
    return type(value) is int and 0 <= value < 2**63


def _pending_publication(row, season):
    _require(
        type(row["KVKNo"]) is int
        and row["KVKNo"] == season
        and type(row["ObjectID"]) is int
        and row["ObjectID"] > 0
        and type(row["DueObjectID"]) is int
        and row["ObjectID"] == row["DueObjectID"]
        and isinstance(row["ObjectCreated"], str)
        and bool(row["ObjectCreated"])
        and row["ObjectCreated"] == row["DueObjectCreated"]
        and type(row["HeaderRevision"]) is int
        and row["HeaderRevision"] > 0
        and type(row["DueHeaderRevision"]) is int
        and row["HeaderRevision"] == row["DueHeaderRevision"]
        and row["HeaderState"] == "OUTPUT_COMPLETE",
        "current publication and due identity differ.",
    )
    _require(
        all(
            _generation(row[k])
            for k in ("DueGeneration", "CompletedGeneration", "AggregateDue", "AggregateCompleted")
        )
        and row["CompletedGeneration"] < row["DueGeneration"] <= row["AggregateDue"]
        and row["AggregateCompleted"] < row["DueGeneration"]
        and row["State"] in {"pending", "failed", "unknown"}
        and row["AggregateState"] in {"pending", "failed", "unknown"}
        and (
            row["ClaimedGeneration"] is None
            or (
                _generation(row["ClaimedGeneration"])
                and 0 < row["ClaimedGeneration"] <= row["DueGeneration"]
            )
        ),
        "outstanding generation proof is inconsistent or execution is unresolved.",
    )


def lifecycle_fingerprint(observed, approved, *, observation_guard="exclusive_schema_observation"):
    """Project only proved missing upkeep indexes into the fixed baseline shape.

    Canonicalize the *actual* complete catalogue first, retaining its provenance
    validation. Raw observations are never edited or replaced with expected rows.
    The returned hash must still match the independently pinned full baseline.
    """
    canonical = canonical_lifecycle_metadata(
        observed, approved, observation_guard=observation_guard
    )
    return hashlib.sha256(encode(canonical)).hexdigest()


def canonical_lifecycle_metadata(
    observed, approved, *, observation_guard="exclusive_schema_observation"
):
    """Preserve the full validated projection for source-derived contract preparation."""
    objects = policy_objects(approved)
    proof = observed.get("maintenance_lifecycle")
    _require(
        isinstance(proof, dict)
        and set(proof) == {"policy", "guard", "outputs"}
        and proof["policy"] == POLICY
        and observation_guard in {"exclusive_schema_observation", "catalogue_generation_v1"}
        and proof["guard"] == observation_guard
        and isinstance(proof["outputs"], list)
        and len(proof["outputs"]) == len(objects),
        "complete guarded observation required.",
    )
    rows = {}
    for row in proof["outputs"]:
        _require(isinstance(row, dict) and set(row) == PROOF_FIELDS, "invalid proof fields.")
        _require(
            all(value is None or type(value) in (str, int) for value in row.values()),
            "unsupported proof value type.",
        )
        _require(
            isinstance(row["ObjectName"], str) and row["ObjectName"] not in rows,
            "duplicate or invalid output evidence.",
        )
        rows[row["ObjectName"]] = row
    _require(set(rows) == {name for name, _ in objects}, "output proof coverage differs.")
    from services.application_observation_fingerprint import FORMAT as OBSERVER_FORMAT

    if approved.get("fingerprint_format") == OBSERVER_FORMAT:
        from services.application_observation_fingerprint import canonical_observer_metadata

        _require(
            observation_guard == "catalogue_generation_v1", "observer generation proof required."
        )
        canonical = canonical_observer_metadata(
            observed["metadata"],
            observed["schema_identity"],
            protocol_sha256=approved.get("observation_installation", {}).get("protocol_sha256"),
        )
    else:
        canonical = canonical_application_metadata(
            observed["metadata"], observed["schema_identity"]
        )
    indexes = canonical["metadata"]["indexes"]
    for name, season in objects:
        for suffix, column in (("GovID", "Gov_ID"), ("KVK_NO", "KVK_NO")):
            expected = expected_index(name, suffix, column)
            actual = [
                r for r in indexes if r["object"] == name and r["identity"] == expected["identity"]
            ]
            if actual:
                _require(actual == [expected], "approved performance index definition differs.")
            else:
                _pending_publication(rows[name], season)
                indexes.append(expected)
    indexes.sort(key=encode)
    return canonical
