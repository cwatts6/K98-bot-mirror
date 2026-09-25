"""Authenticated Bot client for the separately provisioned export authority.

No connector, credential, pipe, process or SQL session is opened at import time.
The actual production service factory remains gated on the complete S11 packet.
"""

from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import json
import re
import threading
from uuid import UUID, uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_execution_authority import ExecutionUncertain
from services.export_execution_protocol import ProviderRequest, uuid_text

_installed = None
_installing = False
_runtime_stopped = False
_installation_lock = threading.RLock()
_caller = ContextVar("export_runtime_caller", default=None)


@dataclass(eq=False)
class RuntimeCall:
    bundle: object
    active: bool = True
    references: int = 1


class RuntimeLifetime:
    """Local drain bookkeeping only; durable writer ownership remains in SQL."""

    def __init__(self, legacy):
        self.legacy = legacy
        self._condition = threading.Condition()
        self._calls = set()
        self._accepting = True

    @contextmanager
    def owned(self):
        inherited = _caller.get()
        with self._condition:
            if inherited is not None:
                if (
                    inherited.bundle is not self
                    or not inherited.active
                    or inherited not in self._calls
                ):
                    raise SourceConflict(
                        "Inherited export call is stale or belongs to another runtime."
                    )
                root = False
                call = inherited
                call.references += 1
            else:
                if not self._accepting:
                    raise SourceConflict("Export runtime admission is closed.")
                call, root = RuntimeCall(self), True
                self._calls.add(call)
        token = _caller.set(call)
        try:
            yield self
        finally:
            _caller.reset(token)
            with self._condition:
                if root:
                    call.active = False
                call.references -= 1
                if call.references == 0:
                    self._calls.remove(call)
                    self._condition.notify_all()

    def stop(self):
        with self._condition:
            self._accepting = False

    def drain(self):
        if _caller.get() is not None:
            raise SourceConflict("An owned export call cannot wait for itself to drain.")
        self.stop()
        with self._condition:
            self._condition.wait_for(lambda: not self._calls)


def configured_runtime():
    with _installation_lock:
        if _installed is None:
            raise SourceConflict("Protected S11 runtime readiness has not completed.")
        return _installed


def validate_caller_context(runtime):
    call = _caller.get()
    if call is not None:
        with call.bundle._condition:
            if (
                not call.active
                or call not in call.bundle._calls
                or call.bundle.legacy is not runtime
            ):
                raise SourceConflict("Inherited caller cannot start work after its root finished.")


@contextmanager
def caller_scope(injected=None):
    # Explicit injected scopes remain useful for offline services. Production
    # binds the installed bundle independently in every actual caller/task.
    inherited = _caller.get()
    if inherited is not None:
        bundle = inherited.bundle
        if injected is not None and injected is not bundle.legacy:
            raise SourceConflict("Caller cannot replace its inherited runtime.")
        with bundle.owned():
            yield bundle.legacy
    elif injected is not None:
        with _installation_lock:
            bundle = _installed
        if bundle is None:
            yield injected
        else:
            if injected is not bundle.legacy:
                raise SourceConflict("Caller cannot replace the installed runtime.")
            with bundle.owned():
                yield injected
    else:
        import bot_config

        if not bot_config.EXPORT_COORDINATION_ENABLED:
            yield None
        else:
            bundle = configured_runtime()
            with bundle.owned():
                yield bundle.legacy


def stop_runtime_admission():
    global _runtime_stopped
    with _installation_lock:
        _runtime_stopped = True
        if _installed is not None:
            _installed.stop()


async def drain_runtime():
    from services.legacy_export_snapshot_service import drain_thread

    with _installation_lock:
        bundle = _installed
    if bundle is not None:
        await drain_thread(bundle.drain)


class AuthorityReconciler:
    """Bot-side selectors only; the protected authority authors every proof."""

    def __init__(self, client):
        self.client = client

    def probe(self, snapshot):
        kind = (
            "retirement_recovery"
            if any(s["State"] == "retired" for s in snapshot["pool"]["slots"])
            else "publication"
        )
        return self.client.prove(kind, snapshot["job"]["JobID"], digest(snapshot).hex())

    def probe_rollover(self, snapshot):
        return self.client.prove(
            "rollover_complete", snapshot["operation"]["OperationID"], digest(snapshot).hex()
        )

    def drain(self, snapshot):
        return self.client.prove(
            "rollover_drain", uuid_text(snapshot["pool"]["OwnerID"]), digest(snapshot).hex()
        )

    def retirement(self, snapshot, current_attempt_id, old_attempt_id):
        attempts = [a for a in snapshot["attempts"] if a["AttemptID"] == current_attempt_id]
        if len(attempts) != 1:
            raise SourceConflict("Exact current retirement attempt required.")
        return self.client.prove(
            "retirement",
            attempts[0]["JobID"],
            digest(snapshot).hex(),
            current_attempt_id=current_attempt_id,
            old_attempt_id=old_attempt_id,
        )


class ExportRuntime(RuntimeLifetime):
    """One admitted bundle for worker, commands and every shared legacy writer.

    Construction is local composition only. The installation function validates
    protected readiness before publishing this bundle to actual callers. SDK
    clients here are request descriptions with an unconditional no-network HTTP
    fallback; only the separately authenticated authority holds provider keys.
    """

    def __init__(
        self, *, connect, registration, store, client, legacy_sql_contract, application_sql_contract
    ):
        from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
        from kvk.services.new_source_admin_service import access_from_config
        from kvk.services.new_source_export_service import load_intent_generation
        from kvk.services.source_export_operator_service import SourceExportOperatorService
        from kvk.services.source_output_pool_service import (
            RetirementRecovery,
            SourceOutputPlanner,
            SourceOutputPoolService,
        )
        from services.export_coordination_dal import ExportCoordinationDAL
        from services.export_coordination_service import ExportCoordinator
        from services.export_provider_adapter import LegacyProviderJob, recorded_clients
        from services.export_request_budget import RequestBudget
        from services.legacy_export_snapshot_dal import LegacySnapshotDAL
        from services.legacy_export_snapshot_service import LegacyExportRuntime

        if not isinstance(registration, RuntimeRegistration) or not isinstance(
            client, AuthorityClient
        ):
            raise SourceConflict("Typed protected runtime and authority client required.")
        validate_application_installation_contract(application_sql_contract)
        if client.deployment_hash is None:
            raise SourceConflict("Runtime requires the approved authority deployment identity.")
        self.connect, self.registration, self.client = connect, registration, client
        config = registration.value()
        if store.storage_owner != config["storage_owner"]:
            raise SourceConflict("Spool custody differs from runtime registration.")
        self.dal = ExportCoordinationDAL(
            connect, preparations=True, output_operations=True, execution_evidence=True
        )
        self.pools = SourceOutputPoolDAL(connect, execution_evidence=True)
        preparations = LegacySnapshotDAL(
            connect,
            output_operations=True,
            execution_evidence=True,
            legacy_sql_contract=legacy_sql_contract,
            application_sql_contract=application_sql_contract,
        )
        self.jobs = NewSourceJobStreams(coordinator=self.dal, client=client)
        self.operations = OutputOperationStreams(pools=self.pools, client=client)
        legacy_streams = LegacyExecutionStreams(
            coordinator=self.dal,
            preparations=preparations,
            client=client,
            account=config["account"],
            storage_owner=store.storage_owner,
            configuration=config["legacy_configuration"],
        )
        legacy = LegacyExportRuntime(
            dal=preparations,
            coordinator=self.dal,
            store=store,
            account=config["account"],
            configuration=config["legacy_configuration"],
            authority_stream=legacy_streams.configuration,
        )
        super().__init__(legacy)
        self.reconciler = AuthorityReconciler(client)
        budget = lambda account: RequestBudget(self.dal, account)
        self.rollover = SourceOutputPoolService(
            self.pools,
            transport_factory=self.transport,
            termination_verifier=self.reconciler.drain,
            budget_factory=budget,
            authority_stream_factory=self.operations,
        )
        generation_loader = lambda intent, fingerprint: load_intent_generation(
            connect=connect, intent_id=intent, expected_hash=fingerprint
        )
        recovery = RetirementRecovery(
            pools=self.pools,
            coordinator=self.dal,
            transport_factory=self.transport,
            budget_factory=budget,
            stream_factory=self.jobs.retirement,
        )
        self.operator = SourceExportOperatorService(
            access_factory=access_from_config,
            pools=self.pools,
            coordinator=self.dal,
            rollover=self.rollover,
            generation_loader=generation_loader,
            reconciler=self.reconciler,
            retirement_recovery=recovery,
        )
        legacy_adapter = LegacyProviderJob(
            lambda _: recorded_clients(), authority_stream=legacy_streams.delivery
        )
        self.coordinator = ExportCoordinator(
            self.dal,
            adapters={
                "all_kvk": legacy_adapter,
                "scan_data": legacy_adapter,
                "new_source": self.deliver,
            },
            storage=store,
            output_planner=SourceOutputPlanner(self.pools, generation_loader),
            rollover=self.rollover,
        )

    def transport(self, context, stream):
        from kvk.services.new_source_export_service import GoogleSheetsTransport

        if stream.scope["OwnerKind"] == "operation":
            context = self.pools.operation_snapshot(stream.scope["ObjectID"])["pool"]
        elif "pool" in context.get("pool", {}):
            context = context["pool"]
        registration = self.registration.sheets(context)
        return GoogleSheetsTransport.from_authority(
            registration=registration,
            reuse_guard=lambda *_: False,
            protected_file_ids=self.registration.value()["protected_file_ids"],
            execution=stream.execute,
            stream_id=stream.stream_id,
            authorize=lambda **_: None,
        )

    def deliver(self, job, claim, dal, budget, stop, snapshot):
        from kvk.services.new_source_delivery_service import deliver_coordinated_export

        if dal is not self.dal or snapshot is not None:
            raise SourceConflict("Exact new-source coordinator and intent generation required.")
        stream = self.jobs.delivery(claim)
        context = self.dal.operator_snapshot(claim.job_id)["pool"]
        transport = self.transport(context, stream)
        return deliver_coordinated_export(
            job=job,
            claim=claim,
            dal=dal,
            transport=transport,
            connect=self.connect,
            budget=budget,
            stop=stop,
            retirement_verifier=self.reconciler.retirement,
            authority_stream=stream,
            retirement_stream_factory=self.jobs.retirement,
            retirement_transport_factory=self.transport,
        )

    def run_batch(self, stop, limit=8):
        from services.export_coordination_service import ExportRegistration
        from services.legacy_export_snapshot_service import use_runtime

        with self.owned(), use_runtime(self.legacy):
            if stop.is_set():
                return
            registrations = []
            for configured in self.registration.value()["pools"]:
                context = self.pools.snapshot(configured["pool_id"])
                sheets = self.registration.sheets(context)
                pool = context["pool"]
                if pool["PoolState"] == "active" and pool["OwnerID"] is None:
                    registrations.append(
                        ExportRegistration(
                            pool["ActiveKVK"],
                            pool["AccountKey"],
                            pool["Epoch"],
                            tuple(sorted((sheets.index_file_id, *sheets.slot_file_ids))),
                        )
                    )
            # Refresh exact epoch/season after rollover, before discovery. SQL
            # registration-aware intents and CAS still decide actual admission.
            self.coordinator.registrations = tuple(registrations)
            self.coordinator.run_batch(stop, limit)


def install_configured_runtime():
    import bot_config

    if not bot_config.EXPORT_COORDINATION_ENABLED:
        return None
    global _installed, _installing
    with _installation_lock:
        if _runtime_stopped:
            raise SourceConflict("A stopped runtime cannot be activated in this process.")
        if _installed is not None:
            return _installed
        if _installing:
            raise SourceConflict("Protected runtime readiness is already in progress.")
        _installing = True
    try:
        # No event-loop caller waits on a lock held across filesystem, SQL or IPC.
        bundle = _prepare_configured_runtime()
        with _installation_lock:
            if _runtime_stopped:
                bundle.stop()
                raise SourceConflict("Shutdown closed admission during runtime readiness.")
            _installed = bundle
        return bundle
    finally:
        with _installation_lock:
            _installing = False


def _prepare_configured_runtime():
    """Explicit enabled startup only; publish nothing until every gate succeeds.

    The path is a deployment input, not a credential. Its admin-owned manifest
    contains reviewed expected pins; startup never creates directories, discovers
    provider files, learns an expected SQL fingerprint or launches the authority.
    """
    import hashlib
    import os
    from pathlib import Path

    from core.export_execution_host import assert_protected_path, current_sid, machine_identity
    from kvk.dal.new_source_admin_dal import configured_connection
    from scripts.run_export_authority import code_files
    from services.export_execution_dal import (
        ExportExecutionDAL,
        application_installation_snapshot,
        legacy_installation_snapshot,
    )
    from services.export_execution_protocol import decode
    from services.export_snapshot_store import ExportSnapshotStore

    path = os.environ.get("K98_EXPORT_RUNTIME_MANIFEST")
    if not path:
        raise SourceConflict("Protected S11 runtime manifest is required before admission.")
    manifest_path = assert_protected_path(path, allow_current_identity=False)
    from services.export_execution_protocol import MAX_MESSAGE_BYTES

    with manifest_path.open("rb") as source:
        config = decode(source.read(MAX_MESSAGE_BYTES + 1))
    fields = {
        "version",
        "authority",
        "registration",
        "sql_contract",
        "legacy_sql_contract",
        "application_sql_contract",
        "spool_root",
        "source_hashes",
        "export_config_file",
        "export_config_sha256",
    }
    if set(config) != fields or type(config["version"]) is not int or config["version"] != 1:
        raise SourceConflict("Complete protected Bot runtime manifest required.")
    registration = RuntimeRegistration(config["registration"])
    authority = config["authority"]
    if (
        not isinstance(authority, dict)
        or set(authority) != {"host", "authority_sid", "bot_sid", "pipe_id", "deployment_hash"}
        or authority["host"] != machine_identity()
        or authority["bot_sid"] != current_sid()
    ):
        raise SourceConflict("Bot runtime belongs to another host or identity.")
    validate_installation_contract(config["sql_contract"])
    validate_legacy_installation_contract(config["legacy_sql_contract"])
    validate_application_installation_contract(config["application_sql_contract"])
    if config["sql_contract"]["profile"] != "reader" or any(
        any(
            config[name][key] != config["sql_contract"][key]
            for key in ("server", "database", "principal")
        )
        for name in ("legacy_sql_contract", "application_sql_contract")
    ):
        raise SourceConflict(
            "All readiness contracts must target the same restricted Bot principal."
        )
    root = Path(__file__).resolve().parents[1]
    hashes = config["source_hashes"]
    if not isinstance(hashes, dict) or set(hashes) != code_files(root):
        raise SourceConflict("Complete reviewed Bot source inventory required.")
    for name, expected in hashes.items():
        source = assert_protected_path(root / name, allow_current_identity=False)
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise SourceConflict("Bot source differs from the reviewed deployment.")
    from constants import CONFIG_FILE

    export_config = assert_protected_path(
        config["export_config_file"], allow_current_identity=False
    )
    if (
        export_config.resolve() != Path(CONFIG_FILE).resolve()
        or hashlib.sha256(export_config.read_bytes()).hexdigest() != config["export_config_sha256"]
    ):
        raise SourceConflict("Legacy query configuration differs from its reviewed source.")
    validate_capture_configuration(
        registration.value()["legacy_configuration"], json.loads(export_config.read_bytes())
    )
    # Connection factories are existing application owners. Each readiness
    # observation checks its actual target; no SQL identity is inferred from
    # environment names or from the authority's separate database session.
    verify_installation_contract(
        ExportExecutionDAL(configured_connection).installation_snapshot(), config["sql_contract"]
    )
    connection = configured_connection()
    try:
        connection.autocommit = True
        cursor = connection.cursor()
        try:
            verify_legacy_installation_contract(
                legacy_installation_snapshot(cursor, config["legacy_sql_contract"]["source"]),
                config["legacy_sql_contract"],
            )
            verify_application_installation_contract(
                application_installation_snapshot(cursor), config["application_sql_contract"]
            )
        finally:
            cursor.close()
    finally:
        connection.close()
    client = AuthorityClient(
        **{k: authority[k] for k in ("pipe_id", "authority_sid", "bot_sid", "deployment_hash")}
    )
    if client._invoke(dict(version=1, action="ready")) != dict(
        deployment_hash=authority["deployment_hash"], registration_hash=registration.fingerprint
    ):
        raise SourceConflict("Protected authority registration/deployment differs.")
    spool = assert_protected_path(config["spool_root"], private=True)
    store = ExportSnapshotStore(spool, registration.value()["storage_owner"])
    bundle = ExportRuntime(
        connect=configured_connection,
        registration=registration,
        store=store,
        client=client,
        legacy_sql_contract=config["legacy_sql_contract"],
        application_sql_contract=config["application_sql_contract"],
    )
    return bundle


def validate_capture_configuration(configuration, export_jobs):
    """Refuse incomplete capture plans before any legacy producer can write SQL."""
    from gsheet_module import validate_export_config

    _legacy_configuration(configuration)
    if not isinstance(export_jobs, list) or not export_jobs:
        raise SourceConflict("Complete reviewed scan export configuration required.")
    validate_export_config(export_jobs)
    if configuration["scan_data"].get("exports") != export_jobs:
        raise SourceConflict("Scan capture must use the exact reviewed query/format list.")
    for kind in ("all_kvk", "scan_data"):
        scope = configuration[kind]
        sheets = scope.get("spreadsheets")
        if (
            not isinstance(sheets, dict)
            or not sheets
            or any(not isinstance(name, str) or not 1 <= len(name) <= 256 for name in sheets)
            or len(sheets) != len(set(sheets.values()))
            or set(sheets.values()) != set(scope["destinations"])
        ):
            raise SourceConflict("Complete non-aliased legacy title/file registration required.")
        grids = scope.get("grid_ids", {})
        if not isinstance(grids, dict) or not set(grids) <= set(scope["destinations"]):
            raise SourceConflict("Grid identities must belong to the registered files.")
        for tabs in grids.values():
            if (
                not isinstance(tabs, dict)
                or any(not isinstance(title, str) or not title for title in tabs)
                or any(
                    type(grid) is not int or not 0 <= grid <= 0x7FFFFFFF for grid in tabs.values()
                )
                or len(tabs) != len(set(tabs.values()))
            ):
                raise SourceConflict("Distinct exact grid identities required per registered file.")
        if kind == "all_kvk" and scope.get("primary_sheet") not in sheets:
            raise SourceConflict("Primary legacy KVK sheet is not registered.")
        if kind == "scan_data" and any(job["sheet"] not in sheets for job in export_jobs):
            raise SourceConflict("A scan output has no registered destination.")


def enrollment_profile(value):
    """Separate protected human OAuth profile; never part of Bot IPC/configuration."""
    from services.export_execution_protocol import decode, encode

    value = decode(encode(value))
    if (
        set(value) != {"version", "owner_email", "client_id", "scopes"}
        or type(value["version"]) is not int
        or value["version"] != 1
        or not isinstance(value["owner_email"], str)
        or not re.fullmatch(
            r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}", value["owner_email"]
        )
        or value["owner_email"].endswith("gserviceaccount.com")
        or len(value["owner_email"]) > 254
        or not isinstance(value["client_id"], str)
        or not re.fullmatch(r"[a-z0-9-]{1,200}\.apps\.googleusercontent\.com", value["client_id"])
        or value["scopes"] != ["https://www.googleapis.com/auth/drive.file"]
    ):
        raise SourceConflict(
            "Exact human owner/client and narrow drive.file enrollment profile required."
        )
    return value


def _legacy_configuration(configuration):
    from services.export_coordination_dal import bounded_json

    if not isinstance(configuration, dict) or set(configuration) != {
        "all_kvk",
        "scan_data",
        "config",
    }:
        raise SourceConflict("All legacy and configuration registrations are required.")
    document = bounded_json(configuration)
    for kind, configured in json.loads(document).items():
        if not isinstance(configured, dict):
            raise SourceConflict("Exact legacy/configuration registration required.")
        files = configured.get("destinations")
        if (
            configured.get("consumer") != kind
            or not isinstance(files, list)
            or not 1 <= len(files) <= 1024
            or any(
                not isinstance(f, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", f)
                for f in files
            )
            or len(files) != len(set(files))
            or (
                kind == "all_kvk"
                and (type(configured.get("kvk_no")) is not int or configured["kvk_no"] <= 0)
            )
            or (kind != "all_kvk" and configured.get("kvk_no") is not None)
        ):
            raise SourceConflict("Exact legacy/configuration registration required.")
    return document


@dataclass(frozen=True, init=False)
class RuntimeRegistration:
    """Immutable protected scope, not historical coverage or deployment proof.

    This document is supplied by the provisioned authority manifest, never by
    Bot IPC. SQL still independently validates the current epoch, claim and full
    owner/resource membership. A rollover can change a pool's season/epoch but
    cannot silently change its registered files, identity or intended audience.
    """

    document: str

    def __init__(self, value):
        from kvk.services.new_source_export_service import SheetsRegistration
        from services.export_coordination_dal import bounded_json
        from services.legacy_export_snapshot_service import configuration_digest

        fields = {
            "version",
            "account",
            "storage_owner",
            "service_account_email",
            "legacy_configuration",
            "pools",
            "protected_file_ids",
        }
        if (
            not isinstance(value, dict)
            or set(value) != fields
            or type(value["version"]) is not int
            or value["version"] != 1
            or any(
                not isinstance(value[k], str)
                or not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", value[k])
                for k in ("account", "storage_owner")
            )
            or not isinstance(value["service_account_email"], str)
            or not value["service_account_email"].endswith(".iam.gserviceaccount.com")
        ):
            raise SourceConflict("Complete protected runtime registration required.")
        legacy = json.loads(_legacy_configuration(value["legacy_configuration"]))
        protected = value["protected_file_ids"]
        if (
            not isinstance(protected, list)
            or not 1 <= len(protected) <= 3072
            or any(
                not isinstance(f, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", f)
                for f in protected
            )
            or protected != sorted(set(protected))
            or not {f for c in legacy.values() for f in c["destinations"]} <= set(protected)
        ):
            raise SourceConflict("Complete protected legacy/configuration file inventory required.")
        pools = value["pools"]
        if not isinstance(pools, list) or not 1 <= len(pools) <= 8:
            raise SourceConflict("All one through eight output registrations are required.")
        pool_ids, hashes, used = (
            set(),
            {configuration_digest(c) for c in legacy.values()},
            set(protected),
        )
        for pool in pools:
            if not isinstance(pool, dict) or set(pool) != {
                "pool_id",
                "registration_sha256",
                "index_file_id",
                "slot_file_ids",
                "owner_email",
                "audience",
            }:
                raise SourceConflict("Exact protected output registration required.")
            uuid_text(pool["pool_id"])
            slots = pool["slot_file_ids"]
            fingerprint = pool["registration_sha256"]
            if (
                pool["pool_id"] in pool_ids
                or not isinstance(fingerprint, str)
                or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
                or fingerprint in hashes
                or not isinstance(slots, list)
                or not 2 <= len(slots) <= 16
                or any(
                    not isinstance(f, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", f)
                    for f in slots
                )
                or not isinstance(pool["index_file_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", pool["index_file_id"])
            ):
                raise SourceConflict("Unique bounded output registrations required.")
            SheetsRegistration(
                pool["index_file_id"],
                tuple(slots),
                pool["owner_email"],
                value["service_account_email"],
                pool["audience"],
            )
            files = {pool["index_file_id"], *slots}
            if files & used:
                raise SourceConflict(
                    "Output pools must be distinct from all protected/shared files."
                )
            pool_ids.add(pool["pool_id"])
            hashes.add(fingerprint)
            used.update(files)
        object.__setattr__(self, "document", bounded_json(value))

    def value(self):
        return json.loads(self.document)

    @property
    def fingerprint(self):
        return digest(self.value()).hex()

    def authorize_scope(self, scope):
        """Reject unregistered accounts/files before child creation or SQL mutation."""
        from services.legacy_export_snapshot_service import configuration_digest

        registered = self.value()
        if scope["AccountKey"] != registered["account"]:
            raise SourceConflict("Authority account differs from its protected registration.")
        resources = scope["ScopeJson"]["resources"]
        keys = {r["key"] for r in resources}
        files = {k.removeprefix("destination:") for k in keys if k.startswith("destination:")}
        if not files or keys != {
            "account:" + registered["account"],
            *("destination:" + f for f in files),
        }:
            raise SourceConflict(
                "Only exact registered account and destination resources are admitted."
            )
        for pool in registered["pools"]:
            if scope["RegistrationHash"] == pool["registration_sha256"]:
                if (
                    scope["OwnerKind"] not in {"job", "operation"}
                    or type(scope["Epoch"]) is not int
                    or scope["Epoch"] <= 0
                    or files != {pool["index_file_id"], *pool["slot_file_ids"]}
                ):
                    raise SourceConflict("Complete registered pool scope required.")
                return
        for kind, config in registered["legacy_configuration"].items():
            if scope["RegistrationHash"] == configuration_digest(config):
                if (
                    scope["Epoch"] is not None
                    or scope["NestedToken"] is not None
                    or scope["OwnerKind"] != ("preparation" if kind == "config" else "job")
                    or scope["Purpose"] != ("probe" if kind == "config" else "mutation")
                    or not files <= set(config["destinations"])
                    or (kind == "config" and files != set(config["destinations"]))
                ):
                    raise SourceConflict("Exact registered legacy/configuration scope required.")
                return
        raise SourceConflict("Stream registration is absent from the protected authority manifest.")

    def sheets(self, context):
        """Resolve one exact current SQL pool; never infer a file from a title."""
        from kvk.services.new_source_export_service import SheetsRegistration

        value = self.value()
        pool = context["pool"]
        registered = next((p for p in value["pools"] if p["pool_id"] == pool["PoolID"]), None)
        if (
            registered is None
            or pool["AccountKey"] != value["account"]
            or pool["SourceKey"] != "snapshot_report_v1"
            or pool["RegistrationHash"] != registered["registration_sha256"]
            or digest(json.loads(pool["RegistrationJson"])).hex()
            != registered["registration_sha256"]
            or pool["ExpectedOwner"] != registered["owner_email"]
            or pool["IndexFileID"] != registered["index_file_id"]
            or len(context["slots"]) != len(registered["slot_file_ids"])
            or {s["FileID"] for s in context["slots"]} != set(registered["slot_file_ids"])
            or context["registration_count"] != len(value["pools"])
        ):
            raise SourceConflict("Current SQL pool differs from immutable runtime registration.")
        return SheetsRegistration(
            registered["index_file_id"],
            tuple(registered["slot_file_ids"]),
            registered["owner_email"],
            value["service_account_email"],
            registered["audience"],
        )


def validate_installation_contract(approved):
    """Validate the protected contract before any SQL connection can be opened."""
    from services.export_execution_dal import INSTALLATION_MIGRATIONS

    fields = {
        "version",
        "server",
        "database",
        "collation",
        "principal",
        "profile",
        "migration_hashes",
        "metadata_hash",
    }
    hexadecimal = lambda value: isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
    if (
        not isinstance(approved, dict)
        or set(approved) != fields
        or type(approved["version"]) is not int
        or approved["version"] != 2
        or approved["profile"] not in {"authority", "reader"}
        or any(
            not isinstance(approved[k], str)
            or not 1 <= len(approved[k]) <= 128
            or approved[k] != approved[k].strip()
            for k in ("server", "database", "collation", "principal")
        )
        or not isinstance(approved["migration_hashes"], dict)
        or set(approved["migration_hashes"]) != set(INSTALLATION_MIGRATIONS)
        or not all(hexadecimal(v) for v in approved["migration_hashes"].values())
        or not hexadecimal(approved["metadata_hash"])
    ):
        raise SourceConflict("Complete approved SQL installation contract required.")


def verify_installation_contract(observed, approved):
    """Match one SQL installation observation to protected, pre-approved bytes.

    This is one readiness prerequisite, never a factory or release switch. The
    composition must obtain `approved` from its protected immutable deployment
    manifest, never populate its expected hashes from this live observation or
    a Bot IPC payload. The fixed export object permissions are necessary; other
    application dependencies, registered writers, OS and provider evidence still
    require their own checks.
    """
    from services.export_execution_dal import (
        INSTALLATION_METADATA,
        INSTALLATION_MIGRATIONS,
        INSTALLATION_OBJECTS,
        installation_permissions,
    )

    validate_installation_contract(approved)
    if (
        not isinstance(observed, dict)
        or set(observed) != {"version", "target", "migrations", "metadata", "permissions"}
        or type(observed["version"]) is not int
        or observed["version"] != 2
    ):
        raise SourceConflict("Complete installation observation required.")
    target = observed["target"]
    expected_target = dict(
        ServerName=approved["server"],
        DatabaseName=approved["database"],
        DatabaseCollation=approved["collation"],
        Principal=approved["principal"],
        Sysadmin=0,
        DatabaseOwner=0,
        ViewDefinition=1,
        AuthorityRole=int(approved["profile"] == "authority"),
        ReaderRole=int(approved["profile"] == "reader"),
        ControlDatabase=0,
        AlterRole=0,
        AlterUser=0,
        ImpersonateUser=0,
    )
    if target != expected_target:
        raise SourceConflict("SQL target, metadata visibility or restricted principal differs.")
    migrations = observed["migrations"]
    if (
        not isinstance(migrations, list)
        or len(migrations) != len(INSTALLATION_MIGRATIONS)
        or {m["MigrationId"] for m in migrations} != set(INSTALLATION_MIGRATIONS)
        or any(
            m["Status"] != "Applied"
            or not isinstance(m["ChecksumSha256"], str)
            or m["ChecksumSha256"].lower() != approved["migration_hashes"][m["MigrationId"]]
            for m in migrations
        )
    ):
        raise SourceConflict("Required SQL migration is absent, failed or changed.")
    metadata = observed["metadata"]
    if not isinstance(metadata, dict) or set(metadata) != INSTALLATION_METADATA:
        raise SourceConflict("Complete installed definition metadata required.")
    objects = metadata["objects"]
    if (
        len(objects) != len(INSTALLATION_OBJECTS)
        or {o["ObjectName"]: o["ObjectType"] for o in objects} != INSTALLATION_OBJECTS
        or any(
            o["ExecuteAsPrincipal"] is not None
            or (
                o["ObjectType"] == "P"
                and (
                    not isinstance(o["ModuleDefinition"], str)
                    or not o["ModuleDefinition"].strip()
                    or o["AnsiNulls"] != 1
                    or o["QuotedIdentifier"] != 1
                )
            )
            or (o["ObjectType"] == "U" and (o["MemoryOptimized"] != 0 or o["TemporalType"] != 0))
            for o in objects
        )
    ):
        raise SourceConflict(
            "Required installed table/procedure definition is unavailable or unsupported."
        )
    tables = {name for name, kind in INSTALLATION_OBJECTS.items() if kind == "U"}
    columns = metadata["columns"]
    if (
        not isinstance(columns, list)
        or {c["ObjectName"] for c in columns} != tables
        or len({(c["ObjectName"], c["ColumnName"]) for c in columns}) != len(columns)
        or len({(c["ObjectName"], c["Ordinal"]) for c in columns}) != len(columns)
        or any(
            not isinstance(c["ColumnName"], str)
            or not 1 <= len(c["ColumnName"]) <= 128
            or type(c["Ordinal"]) is not int
            or c["Ordinal"] <= 0
            for c in columns
        )
    ):
        raise SourceConflict("Required installed column metadata is incomplete.")
    if (
        any(
            c["Disabled"] != 0 or c["Untrusted"] != 0
            for c in metadata["checks"] + metadata["foreign_keys"]
        )
        or any(i["Disabled"] != 0 or i["Hypothetical"] != 0 for i in metadata["indexes"])
        or any(
            not t["ModuleDefinition"] or t["ExecuteAsPrincipal"] is not None
            for t in metadata["triggers"]
        )
    ):
        raise SourceConflict("Disabled, untrusted or opaque installed contract metadata.")
    if digest(metadata).hex() != approved["metadata_hash"]:
        raise SourceConflict(
            "Installed SQL definitions differ from the approved metadata fingerprint."
        )
    expected_permissions = installation_permissions(approved["profile"])
    for column in columns:
        for permission in ("SELECT", "UPDATE"):
            expected_permissions[(column["ObjectName"], column["ColumnName"], permission)] = (
                expected_permissions[(column["ObjectName"], None, permission)]
            )
    permissions = observed["permissions"]
    if (
        not isinstance(permissions, list)
        or len(permissions) != len(expected_permissions)
        or any(
            not isinstance(p, dict)
            or set(p) != {"ObjectName", "ColumnName", "PermissionName", "Allowed"}
            or not isinstance(p["ObjectName"], str)
            or (p["ColumnName"] is not None and not isinstance(p["ColumnName"], str))
            or not isinstance(p["PermissionName"], str)
            or type(p["Allowed"]) is not int
            or p["Allowed"] not in (0, 1)
            for p in permissions
        )
        or {
            (p["ObjectName"], p["ColumnName"], p["PermissionName"]): p["Allowed"]
            for p in permissions
        }
        != expected_permissions
    ):
        raise SourceConflict("Effective export permissions differ from the restricted SQL profile.")
    return digest(observed).hex()


def validate_application_installation_contract(approved):
    from services.export_execution_dal import APPLICATION_SCHEMA_SOURCE_HASH

    fields = {
        "version",
        "server",
        "database",
        "principal",
        "sources",
        "dynamic_objects",
        "metadata_hash",
        "permissions_hash",
        "review_id",
    }
    if (
        not isinstance(approved, dict)
        or set(approved) != fields
        or type(approved["version"]) is not int
        or approved["version"] != 1
        or approved["database"] != "ROK_TRACKER"
        or any(
            not isinstance(approved[k], str) or not 1 <= len(approved[k]) <= 128
            for k in ("server", "principal")
        )
        or any(
            not isinstance(approved[k], str) or not re.fullmatch(r"[0-9a-f]{64}", approved[k])
            for k in ("metadata_hash", "permissions_hash")
        )
        or not isinstance(approved["sources"], list)
        or digest(approved["sources"]).hex() != APPLICATION_SCHEMA_SOURCE_HASH
    ):
        raise SourceConflict("Complete independently reviewed application SQL contract required.")
    uuid_text(approved["review_id"])
    names = {s["name"] for s in approved["sources"]}
    modules = {s["name"] for s in approved["sources"] if s["type"] in {"P", "FN", "IF", "TF"}}
    dynamic = approved["dynamic_objects"]
    if not isinstance(dynamic, list) or len(dynamic) > 1024:
        raise SourceConflict("Bounded source-backed dynamic output inventory required.")
    for row in dynamic:
        if (
            not isinstance(row, dict)
            or set(row) != {"name", "type", "producer_modules"}
            or not isinstance(row["name"], str)
            or not re.fullmatch(r"(?:dbo|KVK)\.[A-Za-z0-9_]{1,128}", row["name"])
            or row["name"] in names
            or row["type"] not in {"U", "V"}
            or not isinstance(row["producer_modules"], list)
            or not row["producer_modules"]
            or len(row["producer_modules"]) != len(set(row["producer_modules"]))
            or not set(row["producer_modules"]) <= modules
        ):
            raise SourceConflict("Exact dynamic output and reviewed producer source required.")
        names.add(row["name"])


def verify_application_installation_contract(observed, approved):
    """Check whole schema, UDTs, dependencies and effective permissions separately."""
    from services.export_execution_dal import INSTALLATION_METADATA

    validate_application_installation_contract(approved)
    if (
        not isinstance(observed, dict)
        or set(observed)
        != {
            "version",
            "target",
            "metadata",
            "schema_permissions",
            "object_permissions",
            "column_permissions",
        }
        or type(observed["version"]) is not int
        or observed["version"] != 1
        or observed["target"]
        != dict(
            ServerName=approved["server"],
            DatabaseName=approved["database"],
            Principal=approved["principal"],
            ViewDefinition=1,
        )
    ):
        raise SourceConflict("Exact complete application SQL target required.")
    metadata = observed["metadata"]
    if (
        not isinstance(metadata, dict)
        or set(metadata)
        != {*INSTALLATION_METADATA, "table_types", "dependencies", "synonyms", "database_triggers"}
        or any(not isinstance(v, list) for v in metadata.values())
    ):
        raise SourceConflict("Whole application metadata categories are incomplete.")
    expected = {
        s["name"]: s["type"]
        for s in approved["sources"] + approved["dynamic_objects"]
        if s["type"] != "TT"
    }
    objects = metadata["objects"]
    if (
        len(objects) != len(expected)
        or {r["ObjectName"]: r["ObjectType"] for r in objects} != expected
        or any(
            r["ObjectType"] in {"P", "V", "FN", "IF", "TF"} and not r["ModuleDefinition"]
            for r in objects
        )
        # Historical application constraint/trigger dispositions are reviewed
        # and pinned in metadata_hash, rather than requiring unrelated schema
        # repairs here. The fixed coordination contract has its own strict gate.
        or any(
            not r["ModuleDefinition"] for r in metadata["triggers"] + metadata["database_triggers"]
        )
        or {r["TypeName"] for r in metadata["table_types"]}
        != {s["name"] for s in approved["sources"] if s["type"] == "TT"}
        or digest(metadata).hex() != approved["metadata_hash"]
    ):
        raise SourceConflict(
            "Installed application schema/dependencies differ from reviewed source shapes."
        )
    permissions = {
        k: observed[k] for k in ("schema_permissions", "object_permissions", "column_permissions")
    }
    if (
        any(not isinstance(v, list) for v in permissions.values())
        or any(
            type(r["Allowed"]) is not int or r["Allowed"] not in {0, 1}
            for r in permissions["column_permissions"]
        )
        or digest(permissions).hex() != approved["permissions_hash"]
    ):
        raise SourceConflict("Whole application effective permissions differ or are unknown.")
    return digest(observed).hex()


def validate_legacy_installation_contract(approved):
    """Validate independently approved source and installation pins before SQL I/O.

    This permission prerequisite does not certify output shapes, transaction
    behavior, host containment or complete writer exclusion. Those remain
    separate prerequisites of the still-closed production factory.
    """
    from services.export_execution_dal import validate_legacy_permission_source

    fields = {
        "version",
        "server",
        "database",
        "principal",
        "source",
        "certificate_pins",
        "signature_hashes",
        "migration_hash",
        "metadata_hash",
    }
    hexadecimal = lambda value, length=64: isinstance(value, str) and re.fullmatch(
        rf"[0-9a-f]{{{length}}}", value
    )
    if (
        not isinstance(approved, dict)
        or set(approved) != fields
        or type(approved["version"]) is not int
        or approved["version"] != 1
        or approved["database"] != "ROK_TRACKER"
        or any(
            not isinstance(approved[k], str)
            or not 1 <= len(approved[k]) <= 128
            or approved[k] != approved[k].strip()
            for k in ("server", "principal")
        )
        or not hexadecimal(approved["migration_hash"])
        or not hexadecimal(approved["metadata_hash"])
    ):
        raise SourceConflict("Complete protected legacy SQL permission contract required.")
    validate_legacy_permission_source(approved["source"])
    signatures = approved["source"]["signatures"]
    certificates = {s["certificate"] for s in signatures}
    pins = approved["certificate_pins"]
    hashes = approved["signature_hashes"]
    if (
        not isinstance(pins, dict)
        or set(pins) != certificates
        or any(
            not isinstance(p, dict)
            or set(p) != {"thumbprint", "public_key_hash"}
            or not hexadecimal(p["thumbprint"], 40)
            or not hexadecimal(p["public_key_hash"])
            for p in pins.values()
        )
        or len({p["thumbprint"] for p in pins.values()}) != len(pins)
        or not isinstance(hashes, dict)
        or set(hashes)
        != {"|".join((s["module"], s["certificate"], s["crypt_type"])) for s in signatures}
        or not all(hexadecimal(h) for h in hashes.values())
    ):
        raise SourceConflict("Exact independently approved certificates/signature hashes required.")


def verify_legacy_installation_contract(observed, approved):
    """Check source bodies, exact signing privileges and this producer's SQL token."""
    from services.export_execution_dal import (
        LEGACY_PERMISSION_MIGRATION,
        legacy_definition_hash,
        legacy_permission_queries,
    )

    validate_legacy_installation_contract(approved)
    source = approved["source"]
    queries = legacy_permission_queries(source)
    if (
        not isinstance(observed, dict)
        or set(observed) != {"version", *queries}
        or type(observed["version"]) is not int
        or observed["version"] != 1
        or any(
            not isinstance(observed[k], list) or any(not isinstance(r, dict) for r in observed[k])
            for k in queries
        )
    ):
        raise SourceConflict("Complete legacy SQL permission observation required.")
    expected_target = dict(
        ServerName=approved["server"],
        DatabaseName=approved["database"],
        Principal=approved["principal"],
        DefaultSchema="dbo",
        MajorVersion=16,
        Sysadmin=0,
        DatabaseOwner=0,
        ViewDefinition=1,
        EntryRole=1,
        ReaderRole=1,
        AuthorityRole=0,
    )
    if observed["target"] != [expected_target] or any(
        type(observed["target"][0][k]) is not int
        for k, v in expected_target.items()
        if type(v) is int
    ):
        raise SourceConflict(
            "Legacy SQL target, metadata visibility or application identity differs."
        )
    modules = {m["name"]: m for m in source["modules"]}
    actual = observed["modules"]
    if len(actual) != len(modules) or {m.get("ObjectName") for m in actual} != set(modules):
        raise SourceConflict("Exact legacy module inventory required.")
    for row in actual:
        expected = modules[row["ObjectName"]]
        if (
            set(row)
            != {
                "ObjectName",
                "ObjectType",
                "ModuleDefinition",
                "AnsiNulls",
                "QuotedIdentifier",
                "ExecuteAsPrincipal",
                "OwnerName",
            }
            or row["ObjectType"] != expected["object_type"]
            or row["OwnerName"] != "dbo"
            or row["ExecuteAsPrincipal"] != expected["execute_as"]
            or type(row["AnsiNulls"]) is not int
            or row["AnsiNulls"] != 1
            or type(row["QuotedIdentifier"]) is not int
            or row["QuotedIdentifier"] != 1
            or legacy_definition_hash(row["ModuleDefinition"]) != expected["definition_sha256"]
        ):
            raise SourceConflict("Legacy source definition, execution context or owner differs.")
    expected_signatures = []
    for signature in source["signatures"]:
        module, certificate, kind = (signature[k] for k in ("module", "certificate", "crypt_type"))
        expected_signatures.append(
            dict(
                ObjectName=module,
                CertificateName=certificate,
                CryptType=kind,
                Thumbprint=approved["certificate_pins"][certificate]["thumbprint"],
                SignatureHash=approved["signature_hashes"]["|".join((module, certificate, kind))],
                IsSigned=1,
                IsValid=1,
            )
        )

    # Sorted canonical rows preserve duplicate detection, exact fields and types.
    def exact_rows(actual_rows, expected_rows):
        return sorted(json.dumps(r, sort_keys=True) for r in actual_rows) == sorted(
            json.dumps(r, sort_keys=True) for r in expected_rows
        )

    if not exact_rows(observed["signatures"], expected_signatures):
        raise SourceConflict("Missing, extra, changed or invalid legacy module signature.")
    expected_certs = []
    for name, pin in approved["certificate_pins"].items():
        for database in (
            ["ROK_TRACKER", "master"] if name == "S11LegacyImport" else ["ROK_TRACKER"]
        ):
            expected_certs.append(
                dict(
                    DatabaseName=database,
                    CertificateName=name,
                    OwnerName="dbo",
                    PrivateKeyType="NA",
                    Thumbprint=pin["thumbprint"],
                    PublicKeyHash=pin["public_key_hash"],
                )
            )
    if not exact_rows(
        observed["certificates"], [c for c in expected_certs if c["DatabaseName"] == "ROK_TRACKER"]
    ) or not exact_rows(
        observed["master_certificates"],
        [c for c in expected_certs if c["DatabaseName"] == "master"],
    ):
        raise SourceConflict(
            "Signing certificate, public key, owner or private-key boundary differs."
        )
    expected_grants = [
        dict(
            DatabaseName=g["database"],
            PrincipalName=g["principal"],
            SecurableClass=g["securable_class"],
            TargetName=g["target"],
            PermissionName=g["permission"],
            GrantState="G",
            MinorID=0,
        )
        for g in source["grants"]
    ]
    if not exact_rows(observed["grants"], expected_grants):
        raise SourceConflict(
            "Certificate or entry-role permissions differ from the exact grant set."
        )
    expected_principals = {
        ("ROK_TRACKER", name + "User"): name for name in approved["certificate_pins"]
    } | {
        ("master", "S11LegacyImportUser"): "S11LegacyImport",
        ("server", "S11LegacyImportLogin"): "S11LegacyImport",
    }
    principals = observed["principals"]
    if (
        len(principals) != len(expected_principals)
        or {
            (p.get("DatabaseName"), p.get("PrincipalName")): p.get("CertificateName")
            for p in principals
        }
        != expected_principals
        or any(
            set(p)
            != {
                "DatabaseName",
                "PrincipalName",
                "PrincipalType",
                "PrincipalSID",
                "CertificateSID",
                "CertificateName",
            }
            or p["PrincipalType"] != "C"
            or not isinstance(p["PrincipalSID"], str)
            or not re.fullmatch(r"[0-9a-f]{2,170}", p["PrincipalSID"])
            or p["PrincipalSID"] != p["CertificateSID"]
            for p in principals
        )
    ):
        raise SourceConflict("Exact certificate-mapped principals required.")
    capability_input = json.loads(queries["capabilities"][1][0])
    expected_capabilities = [
        dict(
            SecurableClass=p["kind"],
            TargetName=p["target"],
            PermissionName=p["permission"],
            Allowed=0,
        )
        for p in capability_input
    ]
    expected_permissions = [
        dict(
            ObjectName=name,
            PermissionName=p,
            Allowed=int(p == "EXECUTE" and name in source["roots"]),
        )
        for name in modules
        for p in ("EXECUTE", "ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    if (
        not exact_rows(observed["capabilities"], expected_capabilities)
        or not exact_rows(observed["module_permissions"], expected_permissions)
        or observed["memberships"]
        or observed["token_grants"]
        or not exact_rows(
            observed["ownership"],
            [dict(OwnedSchemas=0, OwnedObjects=0, OwnedPrincipals=0, OwnedServerPrincipals=0)],
        )
    ):
        raise SourceConflict("Application token can cross the legacy/evidence privilege boundary.")
    if not exact_rows(
        observed["migration"],
        [
            dict(
                MigrationId=LEGACY_PERMISSION_MIGRATION,
                ChecksumSha256=approved["migration_hash"],
                Status="Applied",
            )
        ],
    ):
        raise SourceConflict("Exact legacy permission migration receipt required.")
    if digest(observed).hex() != approved["metadata_hash"]:
        raise SourceConflict(
            "Legacy permission metadata differs from the protected approved fingerprint."
        )
    return digest(observed).hex()


def output_operation_scope(snapshot, *, purpose):
    """Bind an operation snapshot without creating a worker owner for a drain probe.

    SQL repeats owner/resource/registration predicates at admission and dispatch.
    This preparation neither changes ownership nor establishes historical finality.
    """
    op, context = snapshot["operation"], snapshot["pool"]
    pool, slots = context["pool"], context["slots"]
    resources = snapshot["resources"]
    identifier = lambda value: str(UUID(str(value))) if value is not None else None
    operation_id = identifier(op["OperationID"])
    owner = identifier(op["OwnerID"])
    plan = json.loads(op["PlanJson"])
    registered = json.loads(pool["RegistrationJson"])
    plan_pool = plan["snapshot"]["pool"]
    file_ids = [pool["IndexFileID"], *(s["FileID"] for s in slots)]
    if (
        purpose not in {"probe", "mutation"}
        or digest(plan).hex() != op["PlanHash"]
        or digest(registered).hex() != pool["RegistrationHash"]
        or plan_pool["RegistrationHash"] != pool["RegistrationHash"]
        or plan_pool["IndexFileID"] != pool["IndexFileID"]
        or {s["FileID"] for s in plan["snapshot"]["slots"]} != set(file_ids[1:])
        or not 2 <= len(slots) <= 16
        or len(file_ids) != len(set(file_ids))
        or not 1 <= context["registration_count"] <= 8
        or identifier(op["PoolID"]) != identifier(pool["PoolID"])
        or identifier(op["ActivePoolID"]) != identifier(pool["PoolID"])
        or pool["AccountKey"] != op["AccountKey"]
        or pool["PoolState"] != "closing"
        or identifier(pool["OwnerID"]) != operation_id
        or pool["Epoch"] != op["OldEpoch"]
        or any(type(op[k]) is not int or op[k] <= 0 for k in ("Version", "OldEpoch"))
    ):
        raise SourceConflict("Exact operation plan and closing registration required.")
    if owner is None:
        if (purpose, op["State"], op["Phase"], op["Fence"]) != (
            "probe",
            "closing",
            "draining",
            0,
        ) or type(op["Fence"]) is not int:
            raise SourceConflict("Only an unowned closing operation may use the drain probe.")
    elif (
        type(op["Fence"]) is not int
        or op["Fence"] <= 0
        or op["State"]
        not in ({"running"} if purpose == "mutation" else {"running", "uncertain", "blocked"})
    ):
        raise SourceConflict("Operation writer ownership is unavailable.")
    expected = {"account:" + op["AccountKey"], *("destination:" + f for f in file_ids)}
    if len(resources) != len(expected) or {r["ResourceKey"] for r in resources} != expected:
        raise SourceConflict("Exact account and registered file membership required.")
    for resource in resources:
        if (
            type(resource["Version"]) is not int
            or resource["Version"] <= 0
            or resource["ActiveJobID"] is not None
            or resource["ActivePreparationID"] is not None
            or identifier(resource["OwnerID"]) != owner
            or identifier(resource["ActiveOutputOperationID"]) != (operation_id if owner else None)
            or (owner is not None and resource["Fence"] != op["Fence"])
            or (purpose == "mutation" and resource["BlockedReason"] is not None)
        ):
            raise SourceConflict("Operation resource is still owned or its scope changed.")
    return dict(
        AccountKey=op["AccountKey"],
        OwnerKind="operation",
        ObjectID=operation_id,
        OwnerID=owner,
        Fence=op["Fence"],
        ClaimVersion=op["Version"],
        NestedToken=None,
        RegistrationHash=pool["RegistrationHash"],
        Epoch=op["OldEpoch"],
        SnapshotHash=digest(context if owner is None else snapshot).hex(),
        ScopeJson={
            "resources": [
                {"key": r["ResourceKey"], "version": r["Version"]}
                for r in sorted(resources, key=lambda r: r["ResourceKey"])
            ]
        },
        Purpose=purpose,
    )


class OutputOperationStreams:
    """Explicit binding for rollover's phase factory and read-only drain probes."""

    def __init__(self, *, pools, client):
        if pools.execution_evidence is not True:
            raise SourceConflict("Operation streams require S11 evidence on the pool DAL.")
        self.pools, self.client = pools, client

    def __call__(self, claim, operation, phase, file_id):
        snapshot = self.pools.operation_snapshot(claim.operation_id)
        op = snapshot["operation"]
        scope = output_operation_scope(snapshot, purpose="mutation")
        if (
            (
                scope["ObjectID"],
                scope["AccountKey"],
                scope["OwnerID"],
                scope["Fence"],
                scope["ClaimVersion"],
            )
            != (claim.operation_id, claim.account, claim.owner, claim.fence, claim.version)
            or tuple((r["key"], r["version"]) for r in scope["ScopeJson"]["resources"])
            != claim.resources
            or snapshot["pool"]["pool"]["Version"] != claim.pool_version
            or (op["Phase"], op["CurrentFileID"]) != (phase, file_id)
            or phase not in {"private_pending", "clear_pending", "setup_pending"}
            or op["PlanHash"] != operation["PlanHash"]
        ):
            raise SourceConflict("Rollover phase differs from its exact claimed version.")
        return self.client.stream(scope)

    def closing_probe(self, snapshot):
        scope = output_operation_scope(snapshot, purpose="probe")
        if scope["OwnerID"] is not None:
            raise SourceConflict("Closing probe cannot adopt a worker owner.")
        if self.pools.operation_snapshot(scope["ObjectID"]) != snapshot:
            raise SourceConflict("Closing operation snapshot changed before probe admission.")
        return self.client.stream(scope)

    def completion_probe(self, snapshot):
        scope = output_operation_scope(snapshot, purpose="probe")
        if scope["OwnerID"] is None or snapshot["operation"]["State"] not in {
            "running",
            "uncertain",
        }:
            raise SourceConflict("Completion probe requires the retained operation owner.")
        if self.pools.operation_snapshot(scope["ObjectID"]) != snapshot:
            raise SourceConflict("Completion operation snapshot changed before probe admission.")
        return self.client.stream(scope)


def new_source_job_scope(snapshot, claim, *, purpose="mutation"):
    """Describe an already-owned job; SQL rechecks it at admission and dispatch."""
    job, context = snapshot["job"], snapshot["pool"]
    pool, slots = context["pool"], context["slots"]
    resources = snapshot["resources"]
    file_ids = [pool["IndexFileID"], *(slot["FileID"] for slot in slots)]
    expected = {"account:" + claim.account, *("destination:" + f for f in file_ids)}
    provenance = json.loads(job["ProvenanceJson"])
    recovery = provenance.get("retirement_recovery")
    if (
        tuple(
            job.get(k)
            for k in ("JobID", "AccountKey", "OwnerID", "Fence", "Version", "ConsumerKind")
        )
        != (
            claim.job_id,
            claim.account,
            claim.owner_id,
            claim.fence,
            claim.version,
            "new_source",
        )
        or purpose not in {"mutation", "probe"}
        or job["State"]
        not in ({"running"} if purpose == "mutation" else {"running", "uncertain", "confirmed"})
        or any(type(v) is not int or v <= 0 for v in (claim.fence, claim.version, pool["Epoch"]))
        or pool["AccountKey"] != claim.account
        or pool["Epoch"] != job["PoolEpoch"]
        or pool["ActiveKVK"] != job["KVK_NO"]
        or pool["PoolState"] not in {"active", "closing"}
        or (pool["PoolState"] == "active" and pool["OwnerID"] is not None)
        or digest(json.loads(pool["RegistrationJson"])).hex() != pool["RegistrationHash"]
        or not 2 <= len(slots) <= 16
        or len(set(file_ids)) != len(file_ids)
        or not 1 <= context["registration_count"] <= 8
        or len(resources) != len(expected)
        or {r["ResourceKey"] for r in resources} != expected
        or tuple(sorted((r["ResourceKey"], r["Version"]) for r in resources))
        != tuple(sorted(claim.resources))
        or digest(tuple(sorted(file_ids))).hex() != job["DestinationSetHash"]
    ):
        raise SourceConflict("Exact current new-source job/registration claim required.")
    nested_token = None
    if recovery is not None:
        if (
            not isinstance(recovery, dict)
            or type(recovery.get("version")) is not int
            or recovery["version"] <= 0
            or (
                recovery.get("pool_id"),
                recovery.get("epoch"),
                recovery.get("registration_hash"),
            )
            != (pool["PoolID"], pool["Epoch"], pool["RegistrationHash"])
        ):
            raise SourceConflict("Exact nested retirement recovery owner required.")
        uuid_text(recovery.get("token"))
        if recovery.get("state") == "owned" and (
            recovery.get("version") == claim.version
            or (
                purpose == "probe"
                and job["State"] == "uncertain"
                and recovery.get("version") == claim.version - 1
            )
        ):
            nested_token = recovery["token"]
        elif (
            purpose != "probe"
            or recovery.get("state") != "complete"
            or recovery["version"] >= claim.version
        ):
            raise SourceConflict("Exact current or interrupted nested owner version required.")
        if (
            len(snapshot["attempts"]) != 1
            or recovery.get("attempt_id") != snapshot["attempts"][0]["AttemptID"]
        ):
            raise SourceConflict("Nested recovery belongs to another publishing attempt.")
    for resource in resources:
        unowned_probe = purpose == "probe" and all(
            resource[k] is None
            for k in (
                "ActiveJobID",
                "OwnerID",
                "ActivePreparationID",
                "ActiveOutputOperationID",
            )
        )
        if (
            (
                not unowned_probe
                and (
                    resource["ActiveJobID"] != claim.job_id
                    or resource["OwnerID"] != claim.owner_id
                    or resource["Fence"] != claim.fence
                )
            )
            or type(resource["Version"]) is not int
            or resource["Version"] <= 0
            or resource["ActivePreparationID"] is not None
            or resource["ActiveOutputOperationID"] is not None
            or (purpose == "mutation" and resource["BlockedReason"] is not None)
        ):
            raise SourceConflict("Job resource owner/fence/version changed.")
    return dict(
        AccountKey=claim.account,
        OwnerKind="job",
        ObjectID=claim.job_id,
        OwnerID=claim.owner_id,
        Fence=claim.fence,
        ClaimVersion=claim.version,
        NestedToken=nested_token,
        RegistrationHash=pool["RegistrationHash"],
        Epoch=pool["Epoch"],
        SnapshotHash=digest(snapshot).hex(),
        Purpose=purpose,
        ScopeJson={
            "resources": [
                {"key": key, "version": version} for key, version in sorted(claim.resources)
            ]
        },
    )


class NewSourceJobStreams:
    """Fresh delivery/retirement scopes, preserving current and nested claim identity."""

    def __init__(self, *, coordinator, client):
        if coordinator.execution_evidence is not True or coordinator.output_operations is not True:
            raise SourceConflict("Job streams require the complete S11 DAL contract.")
        self.coordinator, self.client = coordinator, client

    def delivery(self, claim):
        snapshot = self.coordinator.operator_snapshot(claim.job_id)
        scope = new_source_job_scope(snapshot, claim)
        if scope["NestedToken"] is not None:
            raise SourceConflict("A retirement recovery owner cannot replay delivery.")
        if snapshot["attempts"]:
            raise SourceConflict("Attempted delivery requires reconciliation, never replay.")
        return self.client.stream(scope)

    def retirement(self, claim, retirement, member):
        from kvk.dal.source_output_pool_dal import pending_retirements

        snapshot = self.coordinator.operator_snapshot(claim.job_id)
        scope = new_source_job_scope(snapshot, claim)
        if not any(
            all(
                token[k] == retirement[k]
                for k in ("operation_id", "pool_id", "epoch", "current_attempt_id")
            )
            and member in token["slots"]
            for token in pending_retirements(snapshot)
        ):
            raise SourceConflict("Retirement member differs from the exact durable journal.")
        return self.client.stream(scope)

    def probe(self, snapshot):
        """Observe the exact retained owner; never claim or revive a mutation stream."""
        from services.export_coordination_dal import Claim

        job = snapshot["job"]
        if self.coordinator.operator_snapshot(job["JobID"]) != snapshot:
            raise SourceConflict("Publication probe snapshot changed before admission.")
        claim = Claim(
            job["JobID"],
            job["AccountKey"],
            job["OwnerID"],
            job["Fence"],
            job["Version"],
            tuple((r["ResourceKey"], r["Version"]) for r in snapshot["resources"]),
            job["IntentID"],
        )
        return self.client.stream(new_source_job_scope(snapshot, claim, purpose="probe"))

    def retirement_probe(self, snapshot, claim, current_attempt_id):
        """Bind an owned retirement observation to its pool-context consuming CAS."""
        actual = self.coordinator.operator_snapshot(claim.job_id)
        scope = new_source_job_scope(actual, claim, purpose="probe")
        if (
            actual["pool"] != snapshot
            or actual["job"]["State"] != "running"
            or snapshot["pool"]["PoolState"] != "active"
            or scope["NestedToken"] is not None
            or len(actual["attempts"]) != 1
            or actual["attempts"][0]["AttemptID"] != current_attempt_id
            or actual["attempts"][0]["Phase"] != "publication_pending"
        ):
            raise SourceConflict("Exact publishing owner and active retirement context required.")
        # retire_generation consumes the pool snapshot, not the wider operator
        # snapshot. Keep the same exact claim/resources and bind these bytes.
        scope["SnapshotHash"] = digest(snapshot).hex()
        return self.client.stream(scope)


class LegacyExecutionStreams:
    """Bind captured delivery and configuration reads to current S10C ownership.

    Configuration is copied into canonical bytes once. This factory creates no
    SQL/provider owner; callers supply the already admitted exact claim. SQL
    independently checks the complete resource membership before child dispatch.
    """

    def __init__(self, *, coordinator, preparations, client, account, storage_owner, configuration):
        if (
            coordinator.execution_evidence is not True
            or coordinator.output_operations is not True
            or coordinator.preparations is not True
            or preparations.execution_evidence is not True
            or preparations.output_operations is not True
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", v)
                for v in (account, storage_owner)
            )
        ):
            raise SourceConflict("Complete registered S11 legacy composition required.")
        self.coordinator, self.preparations, self.client = coordinator, preparations, client
        self.account, self.storage_owner = account, storage_owner
        self.configuration_json = _legacy_configuration(configuration)

    def _scope(self, row, claim, destinations, *, kind, configured):
        from kvk.dal.source_output_pool_dal import _wire
        from services.legacy_export_snapshot_service import configuration_digest

        row = _wire(row)
        identifier = claim.job_id if kind == "job" else claim.preparation_id
        owner = claim.owner_id if kind == "job" else claim.owner
        uuid_text(identifier)
        uuid_text(owner)
        files = tuple(sorted(destinations))
        resources = tuple(sorted(claim.resources))
        expected = {"account:" + self.account, *("destination:" + f for f in files)}
        if (
            not files
            or len(set(files)) != len(files)
            or not set(files) <= set(configured["destinations"])
            or row["JobID" if kind == "job" else "PreparationID"] != identifier
            or (row["AccountKey"], claim.account) != (self.account,) * 2
            or row["StorageOwner"] != self.storage_owner
            or (row["OwnerID"], row["Fence"], row["Version"]) != (owner, claim.fence, claim.version)
            or any(type(v) is not int or v <= 0 for v in (claim.fence, claim.version))
            or len(resources) != len(expected)
            or {key for key, _ in resources} != expected
            or any(type(v) is not int or v <= 0 for _, v in resources)
        ):
            raise SourceConflict("Exact legacy owner, storage and resource versions required.")
        return dict(
            AccountKey=self.account,
            OwnerKind=kind,
            ObjectID=identifier,
            OwnerID=owner,
            Fence=claim.fence,
            ClaimVersion=claim.version,
            NestedToken=None,
            Epoch=None,
            RegistrationHash=configuration_digest(configured),
            SnapshotHash=digest(dict(row=row, resources=resources)).hex(),
            Purpose="mutation" if kind == "job" else "probe",
            ScopeJson={"resources": [{"key": k, "version": v} for k, v in resources]},
        )

    def delivery(self, job, claim, destinations):
        from kvk.dal.source_output_pool_dal import _wire
        from services.legacy_export_snapshot_service import configuration_digest

        current = _wire(self.coordinator.authorize(claim))
        configured = json.loads(self.configuration_json).get(current["ConsumerKind"])
        if (
            configured is None
            or current["ConsumerKind"] not in {"all_kvk", "scan_data"}
            or current != _wire(job)
            or current["State"] != "running"
            or current["PoolEpoch"] is not None
            or current["SourceKey"] is not None
            or current["IntentID"] is not None
            or current["KVK_NO"] != configured.get("kvk_no")
            or current["DestinationSetHash"] != digest(tuple(sorted(destinations))).hex()
            or json.loads(current["ProvenanceJson"]).get("registration_sha256")
            != configuration_digest(configured)
        ):
            raise SourceConflict("Exact captured legacy job and immutable registration required.")
        scope = self._scope(current, claim, destinations, kind="job", configured=configured)
        return self.client.stream(scope)

    def configuration(self, claim, destinations):
        from kvk.dal.source_output_pool_dal import _wire

        current = _wire(self.preparations.authorize(claim))
        configured = json.loads(self.configuration_json)["config"]
        if (
            (current["ConsumerKind"], current["State"], current["KVK_NO"])
            != ("config", "preflight", None)
            or set(destinations) != set(configured["destinations"])
            or current["RequestHash"] != digest(json.loads(current["RequestJson"])).hex()
            or any(current[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID"))
        ):
            raise SourceConflict("Exact read-only configuration preparation required.")
        scope = self._scope(current, claim, destinations, kind="preparation", configured=configured)
        return self.client.stream(scope)


class AuthorityClient:
    def __init__(
        self,
        *,
        pipe_id,
        authority_sid,
        bot_sid,
        pipe_factory=None,
        verify_server=None,
        deployment_hash=None,
    ):
        uuid_text(pipe_id)
        if authority_sid == bot_sid or not all(
            isinstance(value, str) and value.startswith("S-1-")
            for value in (authority_sid, bot_sid)
        ):
            raise ValueError("Distinct registered Windows identities required.")
        self.pipe_id, self.authority_sid, self.bot_sid = pipe_id, authority_sid, bot_sid
        if deployment_hash is not None and (
            not isinstance(deployment_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", deployment_hash)
        ):
            raise ValueError("Exact expected deployment hash required.")
        self.deployment_hash = deployment_hash
        self.pipe_factory = pipe_factory or self._connect_pipe
        self.verify_server = verify_server or self._verify_server

    def _connect_pipe(self):
        from core.export_execution_host import open_message_pipe

        return open_message_pipe("\\\\.\\pipe\\K98Export-" + self.pipe_id)

    def _verify_server(self, handle):
        from core.export_execution_host import authenticated_server, current_sid

        if current_sid() != self.bot_sid:
            raise ExecutionUncertain("Bot process identity differs from provisioned caller.")
        return authenticated_server(handle, self.authority_sid)

    def _invoke(self, message):
        from core.export_execution_host import MessagePipe

        if self.deployment_hash is not None:
            message = dict(message, deployment_hash=self.deployment_hash)
        handle = None
        server = None
        try:
            handle = self.pipe_factory()
            server = self.verify_server(handle)
            pipe = MessagePipe(handle)
            pipe.send(message)
            reply = pipe.receive()
            if set(reply) != {"version", "result"} or reply["version"] != 1:
                raise ExecutionUncertain("Authority action has no exact acknowledgment.")
            return reply["result"]
        except BaseException as exc:
            raise ExecutionUncertain("Authority action outcome requires reconciliation.") from exc
        finally:
            if server is not None:
                server.Close()
            if handle is not None:
                handle.Close()

    def open_stream(self, stream_id, scope):
        uuid_text(stream_id)
        result = self._invoke(dict(version=1, action="open", stream_id=stream_id, scope=scope))
        if result != {"stream_id": stream_id, "state": "open"}:
            raise ExecutionUncertain("Stream admission acknowledgment differs.")

    def execute(self, message):
        request = ProviderRequest.parse(message)
        result = self._invoke(dict(version=1, action="execute", request=request.message()))
        if (
            not isinstance(result, dict)
            or set(result) != {"request_id", "result"}
            or result["request_id"] != request.request_id
        ):
            raise ExecutionUncertain("Provider request acknowledgment differs.")
        return result["result"]

    def close_stream(self, stream_id):
        uuid_text(stream_id)
        result = self._invoke(dict(version=1, action="close", stream_id=stream_id))
        if (
            not isinstance(result, dict)
            or set(result) != {"stream_id", "version"}
            or result["stream_id"] != stream_id
            or type(result["version"]) is not int
            or result["version"] <= 0
        ):
            raise ExecutionUncertain("Stream closure acknowledgment differs.")
        return result

    def stream(self, scope):
        return AuthorityStream(self, scope)

    def prove(
        self, kind, object_id, snapshot_hash, *, current_attempt_id=None, old_attempt_id=None
    ):
        uuid_text(object_id)
        result = self._invoke(
            dict(
                version=1,
                action="prove",
                kind=kind,
                object_id=object_id,
                snapshot_hash=snapshot_hash,
                current_attempt_id=current_attempt_id,
                old_attempt_id=old_attempt_id,
            )
        )
        if (
            not isinstance(result, dict)
            or result.get("snapshot_hash") != snapshot_hash
            or result.get("state")
            not in (
                {"confirmed", "damaged", "absent"}
                if kind == "publication"
                else {"completed" if kind == "rollover_complete" else "confirmed"}
            )
        ):
            raise ExecutionUncertain("Fixed proof acknowledgment differs.")
        uuid_text(result.get("proof_id"))
        return result


class LocalAuthorityClient(AuthorityClient):
    """Parent-owned probe transport through the same broker, without self-IPC.

    The authenticated broker serves Bot requests synchronously. Its fixed proof
    producer must not connect to its own pipe and wait for that same serve loop.
    Registration and SQL admission still run through the identical typed actions.
    """

    def __init__(self, broker):
        from scripts.run_export_authority import AuthorityBroker

        if not isinstance(broker, AuthorityBroker) or broker.authority.enrollment_plan is not None:
            raise SourceConflict("Registered normal execution broker required for local probes.")
        self.broker = broker

    def _invoke(self, message):
        try:
            if self.broker.boundary is not None:
                message = dict(message, deployment_hash=self.broker.boundary.fingerprint)
            if (
                message.get("action") == "open"
                and message.get("scope", {}).get("Purpose") != "probe"
            ):
                raise SourceConflict("Local proof producers may open only observational streams.")
            if (
                message.get("action") == "execute"
                and ProviderRequest.parse(message["request"]).mutation
            ):
                raise SourceConflict("Local proof producers cannot dispatch a mutation.")
            return self.broker.dispatch(message)
        except BaseException as exc:
            raise ExecutionUncertain("Local authority action requires reconciliation.") from exc


class AuthorityStream(AbstractContextManager):
    def __init__(self, client, scope):
        self.client, self.scope = client, scope
        self.stream_id = str(uuid4())
        self._entered = self._closed = False
        self.closure = None

    def __enter__(self):
        if self._entered or self._closed:
            raise ExecutionUncertain("Authority stream cannot be reopened or adopted.")
        self._entered = True
        self.client.open_stream(self.stream_id, self.scope)
        return self

    def execute(self, message):
        if not self._entered or self._closed:
            raise ExecutionUncertain("Provider stream is not open.")
        if message.get("stream_id") != self.stream_id:
            raise ExecutionUncertain("Provider request belongs to another stream.")
        return self.client.execute(message)

    def __exit__(self, _type, _value, _traceback):
        if not self._entered or self._closed:
            raise ExecutionUncertain("Stream closure cannot be repeated.")
        self._closed = True  # Even a lost acknowledgment cannot cause a second close.
        self.closure = self.client.close_stream(self.stream_id)
        return False


def require_bound_transport(transport, stream):
    """Check the service owns this exact live stream before any provider operation."""
    from kvk.services.new_source_export_service import GoogleSheetsTransport

    adapter = getattr(transport, "_authority_adapter", None)
    if (
        not isinstance(transport, GoogleSheetsTransport)
        or not isinstance(stream, AuthorityStream)
        or not stream._entered
        or stream._closed
        or adapter is None
        or adapter.stream_id != stream.stream_id
        or getattr(adapter.execution, "__self__", None) is not stream
    ):
        raise SourceConflict("Transport must bind the exact live authority stream.")
