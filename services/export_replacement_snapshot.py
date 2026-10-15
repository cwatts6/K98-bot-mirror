"""Rebind retained outputs only; never repeat SQL selection or committed imports."""

from copy import deepcopy
import hashlib

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_legacy_grid_identity import legacy_grid_identity
from services.legacy_export_snapshot_service import LegacySnapshot, configuration_digest


def rebind_snapshot(original, *, job, activation):
    if not isinstance(original, LegacySnapshot):
        raise SourceConflict("Verified immutable retained output required.")
    old = original.metadata()
    original_hash = hashlib.sha256(original.payload).hexdigest()
    job_hash = (
        job["InputHash"] if isinstance(job["InputHash"], str) else bytes(job["InputHash"]).hex()
    )
    if original_hash != job_hash or old["consumer"] != job["ConsumerKind"]:
        raise SourceConflict("Retained input differs from the original export.")
    mapping = activation["mapping"]
    config = deepcopy(old["config"])
    if not set(config["destinations"]) <= set(mapping) or set(config["destinations"]) != {
        o["file_id"] for o in config["outputs"]
    }:
        raise SourceConflict("Every retained output needs an activated replacement.")
    registered = activation["registration"]["legacy_configuration"][old["consumer"]]
    config["destinations"] = sorted(mapping[f] for f in config["destinations"])
    if not set(config["destinations"]) <= set(registered["destinations"]):
        raise SourceConflict("Replacement outputs escape the activated registration.")
    seen = set()
    for output in config["outputs"]:
        old_grid = output["grid_id"]
        output["file_id"] = mapping[output["file_id"]]
        output["grid_id"] = legacy_grid_identity(
            output["tab"], registered.get("grid_ids", {}).get(output["file_id"], {})
        )
        key = (output["file_id"], output["grid_id"])
        if key in seen:
            raise SourceConflict("Retained output tabs collide after replacement.")
        seen.add(key)
        for request in output.get("format_requests", []):
            if set(request) == {"repeatCell"}:
                target = request["repeatCell"]["range"]
            elif set(request) == {"updateSheetProperties"}:
                target = request["updateSheetProperties"]["properties"]
            else:
                raise SourceConflict("Unsupported retained formatting instruction.")
            if target.get("sheetId") != old_grid:
                raise SourceConflict("Retained formatting escapes its original grid.")
            target["sheetId"] = output["grid_id"]
    lineage = dict(
        original_job_id=job["JobID"],
        original_input_sha256=original_hash,
        activation_id=activation["activation_id"],
        replacement_id=activation["replacement_id"],
        original_config_sha256=old["generation"]["config_sha256"],
        **(
            {"input_evidence": activation["input_evidence"]}
            if "input_evidence" in activation
            else {}
        ),
    )
    generation = deepcopy(old["generation"])
    generation.update(
        config_sha256=configuration_digest(config),
        registration_sha256=configuration_digest(registered),
        replacement=lineage,
    )
    result = LegacySnapshot.capture(
        consumer=old["consumer"],
        preparation_id=old["preparation_id"],
        generation=generation,
        config=config,
        provenance=deepcopy(old["provenance"]) | {"replacement": lineage},
        sections=original.sections(),
    )
    # The committed generation identity and every section remain byte-identical.
    if (
        result.metadata()["generation"]["output_sha256"] != old["generation"]["output_sha256"]
        or result.metadata()["generation"]["commit_identity"]
        != old["generation"]["commit_identity"]
    ):
        raise SourceConflict("Replacement must preserve the original committed output.")
    return result
