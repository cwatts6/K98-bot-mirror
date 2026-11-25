"""Single-admission metadata reuse inside the existing producer session owner.

This object is neither a global cache nor mutation authority. Its owner keeps the
original admission cursor alive. Actual entry consumes the candidate once, reads
fresh authority/lifecycle on the business cursor and runs the full comparator.
Existing claim authorization, headroom, business locks and physical cleanup stay
with the caller. Exiting the context discards all reusable evidence.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass
import os
import re
from threading import get_ident

from core.sql_connection_custody import connection_retained
from kvk.dal.new_source_import_dal import digest
from services.catalogue_observation_dal import (
    CoherentObservation,
    ObservationContractError,
    read_boundary,
    require_same_catalogue,
)


@dataclass(frozen=True)
class AdmissionBinding:
    claim_sha256: str
    configuration_sha256: str
    registration_sha256: str
    contract_sha256: str
    protocol_sha256: str

    @classmethod
    def for_claim(cls, claim, *, configuration, registration, approved, expected_modules):
        from services.legacy_export_snapshot_dal import PreparationClaim

        if not isinstance(claim, PreparationClaim):
            raise ObservationContractError("Exact preparation claim required for metadata reuse.")
        if any(
            not isinstance(value, (str, dict, list, tuple)) or not value
            for value in (configuration, registration)
        ):
            raise ObservationContractError("Current configuration and registration are required.")
        return cls(
            digest(asdict(claim)).hex(),
            digest(configuration).hex(),
            digest(registration).hex(),
            digest(approved).hex(),
            digest(dict(expected_modules)).hex(),
        )


class AdmissionMetadata:
    """At most one saved observation and one consumption in an owned admission."""

    def __init__(self, binding, *, approved, expected_modules):
        from services.export_observer_contract import observation_installation, observer_contract

        if (
            not isinstance(binding, AdmissionBinding)
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v)
                for v in asdict(binding).values()
            )
            or binding.contract_sha256 != digest(approved).hex()
            or binding.protocol_sha256 != digest(dict(expected_modules)).hex()
        ):
            raise ObservationContractError("Complete source/claim/configuration binding required.")
        self._binding = binding
        self._approved = deepcopy(approved)
        self._modules = dict(expected_modules)
        self._installation = (
            observation_installation(approved) if observer_contract(approved) else None
        )
        if self._installation is not None:
            self._installation.require_modules(self._modules)
        self._entered = False
        self._active = False
        self._saved = None
        self._origin = None
        self._remembered = False
        self._request = None

    def __enter__(self):
        if self._entered:
            raise ObservationContractError("An observation admission cannot be reopened.")
        self._entered = self._active = True
        self._process_thread = (os.getpid(), get_ident())
        return self

    def __exit__(self, *_):
        self._active = False
        self._saved = self._origin = None

    def _require_owner(self):
        if not self._active or self._process_thread != (os.getpid(), get_ident()):
            raise ObservationContractError("Metadata reuse requires its live physical owner.")

    def remember(self, cursor, observation):
        """Validate and keep metadata only, bound to the still-owned original cursor."""
        self._require_owner()
        if self._remembered or not isinstance(observation, CoherentObservation):
            raise ObservationContractError("One complete observation per admission is required.")
        self._remembered = True
        if connection_retained(cursor.connection):
            raise ObservationContractError("Retained SQL custody cannot supply reusable metadata.")
        current = read_boundary(cursor, self._modules, installation=self._installation)
        if current.identity != observation.boundary.identity:
            raise ObservationContractError("Original observation cursor identity changed.")
        require_same_catalogue(observation.boundary, current)
        return self._save(cursor, observation)

    def collect(self, cursor, *, request=None):
        """Observe on this owned cursor and retain the result without another read.

        Unlike importing an existing proof through remember(), the collector call
        itself establishes the cursor lineage. Its final boundary already checks
        the entire read; the consumer checks origin liveness again at entry.
        """
        self._require_owner()
        if self._remembered or self._installation is None:
            raise ObservationContractError("One protected full observation per admission required.")
        self._remembered = True
        if connection_retained(cursor.connection):
            raise ObservationContractError("Retained SQL custody cannot supply reusable metadata.")
        if request is not None:
            from services.application_observation_schedule import ObservationRequest

            if type(request) is not ObservationRequest:
                raise ObservationContractError("Exact observation request budget required.")
            self._request = request
            cursor = request.cursor(cursor)
            with request.collection():
                return self._collect_and_save(cursor)
        return self._collect_and_save(cursor)

    def _collect_and_save(self, cursor):
        from services.export_runtime_composition import application_snapshot_for_contract

        observation = application_snapshot_for_contract(cursor, self._approved)
        if type(observation) is not CoherentObservation:
            raise ObservationContractError("Complete protected coherent observation required.")
        return self._save(cursor, observation)

    def _save(self, cursor, observation):
        from services.export_runtime_composition import verify_application_installation_contract

        verified = verify_application_installation_contract(
            observation.value, self._approved, observation=observation
        )
        self._saved = (
            observation.boundary,
            deepcopy(observation.value["metadata"]),
            deepcopy(observation.value["schema_identity"]),
        )
        self._origin = cursor
        return verified

    def consume(self, cursor, binding):
        """Fresh actual-session authority/lifecycle, with no second metadata scan.

        Failure consumes the candidate too. Scheduling another full observation
        is an explicit caller decision; this helper never retries business work.
        """
        from services.application_maintenance_contract import policy_objects
        from services.application_maintenance_dal import _lifecycle
        from services.export_execution_dal import application_authority_snapshot
        from services.export_runtime_composition import (
            application_contract_scope,
            verify_application_installation_contract,
        )

        self._require_owner()
        saved, origin = self._saved, self._origin
        self._saved = self._origin = None
        if saved is None or binding != self._binding:
            raise ObservationContractError("Unconsumed metadata for this exact admission required.")
        if connection_retained(origin.connection) or connection_retained(cursor.connection):
            raise ObservationContractError("Retained SQL custody invalidates metadata reuse.")
        previous, metadata, identity = saved
        if self._request is not None:
            cursor = self._request.cursor(cursor)
        current = read_boundary(origin, self._modules, installation=self._installation)
        if current.identity != previous.identity:
            raise ObservationContractError("Original admission connection lineage changed.")
        require_same_catalogue(previous, current)
        scope = application_contract_scope(self._approved)

        # Exactly two tokens bracket the read across the still-owned origin and
        # the actual producer connection. Permission batches remain bounded but
        # need no intermediate token: any change invalidates the final result.
        # No business statement is dispatched before that final comparison.
        authority = application_authority_snapshot(
            cursor,
            scope=scope,
            checkpoint=self._require_owner,
            observation_batches=True,
        )
        value = dict(version=2, metadata=metadata, schema_identity=identity, **authority)
        value["maintenance_lifecycle"] = _lifecycle(
            cursor, policy_objects(self._approved), "catalogue_generation_v1"
        )
        final = read_boundary(cursor, self._modules, installation=self._installation)
        require_same_catalogue(current, final)
        if connection_retained(origin.connection) or connection_retained(cursor.connection):
            raise ObservationContractError("Retained SQL custody invalidates metadata reuse.")
        result = CoherentObservation(value, final)
        verify_application_installation_contract(result.value, self._approved, observation=result)
        if self._request is not None:
            self._request.check()
        return result
