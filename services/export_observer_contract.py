"""Explicit observer successor selection over the retained D4 contract.

Selection comes only from protected release configuration. Live SQL cannot
select this format or supply the expected installation incarnation. The release
issuer and combined migration coordinator remain separate from these readers.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.application_observation_fingerprint import (
    LEGACY_SOURCE_SHA256 as LEGACY_SOURCE_SHA256,
    PROCEDURES,
    reviewed_procedure_hashes,
)
from services.catalogue_observation_contract import ObservationInstallation
from services.catalogue_observation_dal import (
    CoherentObservation,
    ObservationBoundary,
    canonical_module,
)
from services.export_contract_resources import read_contract_resource
from services.export_d4_contract import d4_contract

MIGRATION_ID = "20261120_001_p02_catalogue_observer"
PROFILE_SHA256 = "cd3bcb8c1f7303b8b45d5dc2b3d118aad70002f684ae847ffaf400c056bc1692"
APPLICATION_SOURCE_SHA256 = "778fe6257f99ce38d2563aeaafa90e2acbc595e3c0aee9c0a0f55158155eb3ab"
ACTIVATION_SCOPE_SHA256 = "ae5ea09dcb4f6120e983cd3b6a5a82ea111b6158be60a93552a1689d858551cc"
LEGACY_FINGERPRINT_FORMAT = "legacy_observer_metadata_v1"


def observer_contract(approved):
    if not isinstance(approved, dict) or "observer_installation" not in approved:
        return False
    if approved["observer_installation"] != MIGRATION_ID or not d4_contract(approved):
        raise SourceConflict("Exact observer successor over the retained D4 lineage required.")
    return True


def observer_activation_scope():
    value = json.loads(read_contract_resource("p02_observer_activation_scope.json"))
    if digest(value).hex() != ACTIVATION_SCOPE_SHA256:
        raise SourceConflict("Exact reviewed observer dependency scope required.")
    return value["objects"]


def observation_installation(approved):
    if not observer_contract(approved):
        raise SourceConflict("Explicit protected observer installation required.")
    value = approved.get("observation_installation")
    installation = ObservationInstallation(value)
    if (
        value["database"] != "ROK_TRACKER"
        or any(value[k] != approved[k] for k in ("server", "database", "principal"))
        or value["login"] != approved["principal"]
    ):
        raise SourceConflict("Observer binding requires the exact application target and login.")
    return installation


def require_observer_contract_pair(fixed, legacy, application):
    """Do not combine a successor catalogue with predecessor authority checks."""
    selected = (observer_contract(legacy), observer_contract(application))
    if selected[0] != selected[1]:
        raise SourceConflict("Legacy and application observer selections must agree.")
    if selected[0]:
        if fixed.get("version") != 4 or fixed.get("profile") != "application":
            raise SourceConflict("Observer requires the direct application permission profile.")
        if any(
            contract.get(key) != fixed.get(key)
            for contract in (legacy, application)
            for key in ("server", "database", "principal")
        ):
            raise SourceConflict("All observer contracts must bind the same application target.")
        observation_installation(application)


def canonical_legacy_observation(observed):
    """Normalize only six independently pinned bodies; retain every other value.

    Existing module, permission and receipt comparators still run before this
    full fingerprint check. Native observations are preserved without editing.
    """
    result = deepcopy(observed)
    pinned = reviewed_procedure_hashes()
    seen = set()
    for row in result["modules"]:
        name = row["ObjectName"]
        if name not in PROCEDURES:
            continue
        body = canonical_module(row["ModuleDefinition"])
        if name in seen or hashlib.sha256(body.encode("utf-16-le")).hexdigest() != pinned[name]:
            raise SourceConflict("Observer legacy body differs from independently pinned source.")
        seen.add(name)
        row["ModuleDefinition"] = body
    if seen != PROCEDURES:
        raise SourceConflict("Complete observer legacy source closure required.")
    return dict(format=LEGACY_FINGERPRINT_FORMAT, observation=result)


def observation_record(observation):
    """Serialize comparison evidence only; this is never a reusable admission."""
    if (
        type(observation) is not CoherentObservation
        or type(observation.boundary) is not ObservationBoundary
    ):
        raise SourceConflict("Exact coherent comparison evidence required.")
    identity = list(observation.boundary.identity)
    identity[10:] = [value.isoformat(timespec="microseconds") for value in identity[10:]]
    record = dict(
        version=1,
        guard=observation.guard,
        identity=identity,
        generation=observation.boundary.generation,
    )
    retained_observation(observation.value, record)
    return record


def retained_observation(value, record):
    """Decode historical evidence for the full comparator, never current admission.

    The caller authenticates the receipt. Target/incarnation/source checks and
    the complete schema/permission comparison still apply after decoding.
    """
    if (
        not isinstance(record, dict)
        or set(record) != {"version", "guard", "identity", "generation"}
        or type(record["version"]) is not int
        or record["version"] != 1
        or record["guard"] != "catalogue_generation_v1"
        or type(record["generation"]) is not int
        or not 1 <= record["generation"] < 2**63 - 1
        or not isinstance(record["identity"], list)
        or len(record["identity"]) != 12
    ):
        raise SourceConflict("Complete retained observer comparison evidence required.")
    identity = list(record["identity"])
    if (
        any(
            not isinstance(identity[i], str) or not 1 <= len(identity[i]) <= 128
            for i in (0, 1, 3, 4)
        )
        or any(type(identity[i]) is not int or not 0 < identity[i] < 2**31 for i in (2, 5, 9))
        or any(type(identity[i]) is not int for i in (6, 7, 8))
        or (identity[6], identity[7]) not in {(0, 0), (0, 1), (1, 1)}
        or identity[8] != 2
    ):
        raise SourceConflict("Invalid retained observer session evidence.")
    try:
        for i in (10, 11):
            stamp = datetime.strptime(identity[i], "%Y-%m-%dT%H:%M:%S.%f")
            if stamp.isoformat(timespec="microseconds") != identity[i]:
                raise ValueError("Noncanonical sequence timestamp")
            identity[i] = stamp
    except (TypeError, ValueError) as error:
        raise SourceConflict("Exact retained sequence timestamps required.") from error
    return CoherentObservation(value, ObservationBoundary(tuple(identity), record["generation"]))
