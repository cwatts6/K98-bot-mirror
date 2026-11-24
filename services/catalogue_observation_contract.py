"""Bind the candidate reader to an independently protected SQL installation.

The release issuer must record the successful bootstrap and exact sequence
identity when installing SQL. This module never learns that identity from a
current observation, and does not select the candidate in runtime configuration.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import json

from kvk.dal.new_source_import_dal import digest
from services.catalogue_observation_dal import (
    MODULES,
    ObservationContractError,
    canonical_module,
)
from services.export_contract_resources import read_contract_resource

PROTOCOL_SHA256 = "73be803fe432907cccee0ed86fe593e733b6d682959f4e526f6d7ec47d7a53cc"


def reviewed_protocol_modules():
    """Read only the source resource accompanying this code, never live SQL."""
    try:
        source = json.loads(read_contract_resource("p02_observer_protocol.json"))
        if digest(source).hex() != PROTOCOL_SHA256:
            raise ValueError("Protocol source digest differs")
        rows = source["modules"]
        if len(rows) != len(MODULES) or {row["name"] for row in rows} != MODULES:
            raise ValueError("Protocol source closure differs")
        return {row["name"]: row["definition"] for row in rows}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ObservationContractError(
            "Exact reviewed observation protocol source required."
        ) from error


def _stamp(value):
    if not isinstance(value, str):
        raise ObservationContractError("Exact recorded sequence timestamp required.")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError as error:
        raise ObservationContractError("Exact recorded sequence timestamp required.") from error
    if parsed.isoformat(timespec="microseconds") != value:
        raise ObservationContractError("Canonical recorded sequence timestamp required.")
    return parsed


@dataclass(frozen=True, init=False)
class ObservationInstallation:
    """Immutable target/incarnation supplied by protected installation evidence.

    Bootstrap generation 1 is an issuer assertion from the committed install,
    not a fact inferred from current_value=1. Parent contract/release validation
    remains responsible for authenticating the issuer and migration receipt.
    """

    identity: tuple
    bootstrap_generation: int
    modules: tuple

    def __init__(self, approved):
        fields = {
            "version",
            "protocol_sha256",
            "server",
            "database",
            "database_id",
            "principal",
            "login",
            "sequence_object_id",
            "sequence_created",
            "sequence_modified",
            "bootstrap_generation",
        }
        if (
            not isinstance(approved, dict)
            or set(approved) != fields
            or type(approved["version"]) is not int
            or approved["version"] != 1
            or approved["protocol_sha256"] != PROTOCOL_SHA256
            or type(approved["bootstrap_generation"]) is not int
            or approved["bootstrap_generation"] != 1
            or any(
                type(approved[key]) is not int or not 0 < approved[key] < 2**31
                for key in ("database_id", "sequence_object_id")
            )
            or any(
                not isinstance(approved[key], str)
                or not 1 <= len(approved[key]) <= 128
                or approved[key] != approved[key].strip()
                for key in ("server", "database", "principal", "login")
            )
        ):
            raise ObservationContractError("Complete protected observation installation required.")
        created, modified = (
            _stamp(approved[key]) for key in ("sequence_created", "sequence_modified")
        )
        if created != modified:
            raise ObservationContractError("Unaltered bootstrapped observation sequence required.")
        identity = tuple(
            approved[key] for key in ("server", "database", "database_id", "principal", "login")
        )
        identity += (approved["sequence_object_id"], created, modified)
        object.__setattr__(self, "identity", identity)
        object.__setattr__(self, "bootstrap_generation", approved["bootstrap_generation"])
        object.__setattr__(self, "modules", tuple(sorted(reviewed_protocol_modules().items())))

    def require_modules(self, expected):
        if not isinstance(expected, Mapping):
            raise ObservationContractError("Reviewed observation modules required.")
        if set(expected) != MODULES or any(
            canonical_module(expected[name]) != canonical_module(body)
            for name, body in self.modules
        ):
            raise ObservationContractError("Observation modules differ from protected source.")

    def require_boundary(self, identity, generation):
        if identity[:5] + identity[9:] != self.identity or generation < self.bootstrap_generation:
            raise ObservationContractError(
                "Observation differs from protected target/sequence installation."
            )
