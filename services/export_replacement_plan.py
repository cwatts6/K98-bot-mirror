"""Deterministic destination-only proposals; no admission or provider authority.

The recovery authority must verify containment and fresh-file evidence before
activating any proposal. These transformations preserve the source registration
and never establish that an unknown write succeeded or stopped.
"""

from copy import deepcopy
import hashlib
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_execution_protocol import uuid_text
from services.export_runtime_composition import RuntimeRegistration


def _mapping(registration, targets, replacements):
    if (
        not isinstance(targets, list)
        or not targets
        or any(not isinstance(f, str) for f in targets)
        or targets != sorted(set(targets))
        or not isinstance(replacements, dict)
        or set(replacements) != set(targets)
        or any(
            not isinstance(f, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", f)
            for f in replacements.values()
        )
        or len(set(replacements.values())) != len(targets)
    ):
        raise SourceConflict("One distinct fresh file is required for every isolated target.")
    current = set(registration["protected_file_ids"])
    for pool in registration["pools"]:
        current.update([pool["index_file_id"], *pool["slot_file_ids"]])
    if not set(targets) <= current or set(replacements.values()) & current:
        raise SourceConflict("Replacement files must be separate from every registered file.")
    return deepcopy(replacements)


def replacement_registration(registration, *, targets, replacements, replacement_id):
    """Build the exact proposed registration while preserving policy and history.

    The caller supplies targets reconstructed from an authenticated containment
    receipt, not an admin-selected old scope. File values are still unverified
    proposals. Historical global fences must also be checked at activation.
    """
    if not isinstance(registration, RuntimeRegistration):
        raise SourceConflict("Protected original runtime registration required.")
    uuid_text(replacement_id)
    before = registration.value()
    mapping = _mapping(before, targets, replacements)
    projected = deepcopy(before)
    affected = [
        p for p in projected["pools"] if set(targets) & {p["index_file_id"], *p["slot_file_ids"]}
    ]
    pool_document = None
    if affected:
        if len(affected) != 1 or set(targets) != {
            affected[0]["index_file_id"],
            *affected[0]["slot_file_ids"],
        }:
            raise SourceConflict("Replacement must cover one entire isolated output pool.")
        pool = affected[0]
        old_id = pool["pool_id"]
        if replacement_id in {p["pool_id"] for p in before["pools"]}:
            raise SourceConflict("Replacement requires a new immutable pool identity.")
        pool_document = dict(
            schema="output-pool-replacement/1",
            replacement_id=replacement_id,
            previous_pool_id=old_id,
            previous_registration_sha256=pool["registration_sha256"],
            account=before["account"],
            owner_email=pool["owner_email"],
            editor_email=before["service_account_email"],
            audience=pool["audience"],
            index_file_id=mapping[pool["index_file_id"]],
            slot_file_ids=[mapping[f] for f in pool["slot_file_ids"]],
        )
        pool.update(
            pool_id=replacement_id,
            registration_sha256=digest(pool_document).hex(),
            index_file_id=pool_document["index_file_id"],
            slot_file_ids=pool_document["slot_file_ids"],
        )
        for binding in projected.get("reader_exports", []):
            if binding["pool_id"] == old_id:
                binding["pool_id"] = replacement_id
    else:
        scopes = projected["legacy_configuration"]
        if set(targets) & set(scopes["config"]["destinations"]):
            raise SourceConflict(
                "A configuration input cannot be replaced with a blank output workbook."
            )
        writable = {f for kind in ("scan_data", "all_kvk") for f in scopes[kind]["destinations"]}
        if not set(targets) <= writable:
            raise SourceConflict("Only registered legacy output destinations can be rebound.")
        for kind in ("scan_data", "all_kvk"):
            scope = scopes[kind]
            scope["destinations"] = [mapping.get(f, f) for f in scope["destinations"]]
            if "spreadsheets" in scope:
                scope["spreadsheets"] = {
                    title: mapping.get(f, f) for title, f in scope["spreadsheets"].items()
                }
            if "grid_ids" in scope:
                scope["grid_ids"] = {
                    mapping.get(f, f): tabs for f, tabs in scope["grid_ids"].items()
                }
        projected["protected_file_ids"] = sorted(
            mapping.get(f, f) for f in before["protected_file_ids"]
        )
        if "legacy_file_access" in projected:
            projected["legacy_file_access"] = {
                mapping.get(f, f): policy for f, policy in projected["legacy_file_access"].items()
            }
    result = RuntimeRegistration(projected)
    return dict(
        schema="export-replacement-registration/1",
        replacement_id=replacement_id,
        base_registration_sha256=registration.fingerprint,
        registration_sha256=result.fingerprint,
        registration=result.value(),
        mapping=dict(sorted(mapping.items())),
        pool_registration=pool_document,
    )


def verified_registration(proposal, files):
    """Resolve fresh-grid collisions without changing queries, data or policies."""
    projected = deepcopy(proposal)
    if {f["file_id"] for f in files} != set(proposal["mapping"].values()) or len(files) != len(
        proposal["mapping"]
    ):
        raise SourceConflict("Complete verified file descriptors required for activation.")
    if projected["pool_registration"] is None:
        scopes = projected["registration"]["legacy_configuration"]
        for file in files:
            # The original default worksheet can remain as an unused blank tab.
            # Route an identically named output to it; move conflicting IDs to
            # unused integers consistently across both legacy consumers.
            configured = {}
            for kind in ("scan_data", "all_kvk"):
                tabs = scopes[kind].get("grid_ids", {}).get(file["file_id"], {})
                for title, grid_id in tabs.items():
                    if title in configured and configured[title] != grid_id:
                        raise SourceConflict("Shared legacy tab registrations disagree.")
                    configured[title] = grid_id
            configured[file["title"]] = file["sheet_id"]
            used = set(configured.values())
            for title in sorted(configured):
                if title != file["title"] and configured[title] == file["sheet_id"]:
                    candidate = (
                        int.from_bytes(hashlib.sha256(title.encode()).digest()[:4], "big")
                        & 0x7FFFFFFF
                    )
                    while candidate in used:
                        candidate = (candidate + 1) & 0x7FFFFFFF
                    configured[title] = candidate
                    used.add(candidate)
            for kind in ("scan_data", "all_kvk"):
                if file["file_id"] in scopes[kind]["destinations"]:
                    scopes[kind].setdefault("grid_ids", {})[file["file_id"]] = deepcopy(configured)
    effective = RuntimeRegistration(projected["registration"])
    projected["registration_sha256"] = effective.fingerprint
    return projected
