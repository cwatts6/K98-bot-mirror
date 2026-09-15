"""Immutable legacy/daily output payloads; no provider calls or implicit rebuilds.

The producer DAL must supply committed evidence under shared writer admission.
Serialization deliberately supports SQL scalar types without pickle, lossy decimal
conversion, or a live DataFrame retained by a queued job.
"""

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
import hashlib
import json
import math
from uuid import UUID

from services.export_snapshot_store import SnapshotReceipt


class SnapshotUnavailable(ValueError):
    """Missing generation evidence is an unavailable output, never a fallback."""


def _json(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _cell(value):
    if value is None or type(value) in (str, bool, int):
        return ["scalar", value]
    if type(value) is float and math.isfinite(value):
        return ["scalar", value]
    if isinstance(value, Decimal) and value.is_finite():
        return ["decimal", str(value)]
    if isinstance(value, datetime):
        return ["datetime", value.isoformat()]
    if isinstance(value, date):
        return ["date", value.isoformat()]
    raise SnapshotUnavailable("Unsupported or non-finite SQL output cell.")


def _uncell(value):
    if not isinstance(value, list) or len(value) != 2:
        raise SnapshotUnavailable("Invalid retained cell.")
    kind, item = value
    if kind == "scalar" and (item is None or type(item) in (str, bool, int, float)):
        if type(item) is float and not math.isfinite(item):
            raise SnapshotUnavailable("Non-finite retained cell.")
        return item
    if not isinstance(item, str):
        raise SnapshotUnavailable("Invalid typed retained cell.")
    if kind == "decimal":
        result = Decimal(item)
        if result.is_finite():
            return result
    if kind == "datetime":
        return datetime.fromisoformat(item)
    if kind == "date":
        return date.fromisoformat(item)
    raise SnapshotUnavailable("Unknown retained cell type.")


@dataclass(frozen=True)
class OutputSection:
    name: str
    columns: tuple[str, ...]
    rows: tuple[tuple, ...]

    def document(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise SnapshotUnavailable("A named result section is required.")
        if not self.columns or any(not isinstance(c, str) or not c for c in self.columns):
            raise SnapshotUnavailable(
                "Complete result headers are required, including empty outputs."
            )
        if len(set(self.columns)) != len(self.columns):
            raise SnapshotUnavailable("Duplicate result headers are ambiguous.")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise SnapshotUnavailable("Output row does not match its headers.")
        return dict(
            name=self.name,
            columns=list(self.columns),
            rows=[[_cell(v) for v in row] for row in self.rows],
        )


@dataclass(frozen=True)
class LegacySnapshot:
    """Frozen bytes are the authority; every decode returns independent values."""

    payload: bytes

    @classmethod
    def capture(cls, *, consumer, preparation_id, generation, config, provenance, sections):
        if consumer not in {"all_kvk", "scan_data"}:
            raise SnapshotUnavailable("Unsupported snapshot consumer.")
        preparation_id = str(UUID(preparation_id))
        if not isinstance(generation, dict) or generation.get("completion") != "committed":
            raise SnapshotUnavailable("Committed output proof is required.")
        # A scan alone is not a generation. The DAL owns these identities and
        # hashes; manual export cannot construct them from MAX(ScanID).
        for key in ("output_sha256", "config_sha256", "commit_identity"):
            item = generation.get(key)
            if not isinstance(item, str) or not item:
                raise SnapshotUnavailable("Incomplete committed output proof.")
        if not isinstance(config, dict) or not isinstance(provenance, dict):
            raise SnapshotUnavailable("Complete configuration and provenance are required.")
        documents = [section.document() for section in sections]
        if not documents or len({s["name"] for s in documents}) != len(documents):
            raise SnapshotUnavailable("Unique complete result sections are required.")
        if hashlib.sha256(_json(documents).encode()).hexdigest() != generation["output_sha256"]:
            raise SnapshotUnavailable("Output differs from its committed generation.")
        if hashlib.sha256(_json(config).encode()).hexdigest() != generation["config_sha256"]:
            raise SnapshotUnavailable("Configuration differs from its committed generation.")
        return cls(
            _json(
                dict(
                    schema="legacy-export/1",
                    consumer=consumer,
                    preparation_id=preparation_id,
                    generation=generation,
                    config=config,
                    provenance=provenance,
                    sections=documents,
                )
            ).encode()
        )

    @classmethod
    def load(cls, payload):
        try:
            document = json.loads(payload)
            if (
                set(document)
                != {
                    "schema",
                    "consumer",
                    "preparation_id",
                    "generation",
                    "config",
                    "provenance",
                    "sections",
                }
                or document["schema"] != "legacy-export/1"
            ):
                raise SnapshotUnavailable("Unsupported retained snapshot schema.")
            sections = tuple(
                OutputSection(
                    s["name"],
                    tuple(s["columns"]),
                    tuple(tuple(_uncell(v) for v in row) for row in s["rows"]),
                )
                for s in document["sections"]
            )
            rebuilt = cls.capture(
                **{
                    k: document[k]
                    for k in ("consumer", "preparation_id", "generation", "config", "provenance")
                },
                sections=sections,
            )
            if rebuilt.payload != payload:
                raise SnapshotUnavailable("Retained snapshot is not canonical.")
            return rebuilt
        except (KeyError, TypeError, ValueError, ArithmeticError, UnicodeError) as exc:
            raise SnapshotUnavailable("Invalid retained snapshot or generation evidence.") from exc

    def sections(self):
        document = json.loads(self.payload)
        return tuple(
            OutputSection(
                s["name"],
                tuple(s["columns"]),
                tuple(tuple(_uncell(v) for v in row) for row in s["rows"]),
            )
            for s in document["sections"]
        )

    def metadata(self):
        return {k: v for k, v in json.loads(self.payload).items() if k != "sections"}

    def persist(self, store) -> SnapshotReceipt:
        # Existing store owns exclusive creation, fsync, hash/length verification
        # and storage affinity. SQL registration belongs to the producer DAL.
        return store.put(self.payload)


def output_digest(sections):
    return hashlib.sha256(_json([section.document() for section in sections]).encode()).hexdigest()


def configuration_digest(config):
    return hashlib.sha256(_json(config).encode()).hexdigest()


_runtime = ContextVar("legacy_export_runtime", default=None)
_owner = ContextVar("legacy_export_owner", default=None)
_captures = ContextVar("legacy_export_captures", default=None)


@contextmanager
def use_runtime(runtime):
    """Explicit composition only. No environment flag constructs live clients."""
    token = _runtime.set(runtime)
    try:
        yield runtime
    finally:
        _runtime.reset(token)


def current_owner():
    return _owner.get()


def validate_writer_season(kvk_no):
    owner = current_owner()
    if owner is not None:
        scope = json.loads(require_runtime().configuration)[owner.kind]
        if owner.kind != "all_kvk" or scope.get("kvk_no") != kvk_no:
            raise SnapshotUnavailable("Producer season differs from admitted capture registration.")


def record_writer_completion(*, cursor=None, **evidence):
    """Called only after the real producer acknowledges all its SQL phases."""
    owner = current_owner()
    if owner is not None:
        require_runtime().checkpoint_writer(owner, evidence, cursor=cursor)


@contextmanager
def configuration_requests():
    runtime = _writer_runtime()
    if runtime is None:
        yield
    else:
        if current_owner() is not None and not current_owner().closed:
            raise SnapshotUnavailable("Collect provider configuration before SQL writer admission.")
        with runtime.configuration_requests():
            yield


def require_runtime():
    runtime = _runtime.get()
    if runtime is None:
        raise SnapshotUnavailable("Coordinated export setup is unavailable; no export started.")
    return runtime


def _writer_runtime():
    runtime = _runtime.get()
    if runtime is None:
        # Existing imports remain unchanged while the new coordinator is disabled.
        # An enabling flag cannot allow partially upgraded writers to bypass it.
        import bot_config

        if bot_config.EXPORT_COORDINATION_ENABLED:
            raise SnapshotUnavailable("Writer admission requires verified S10C composition.")
    return runtime


@contextmanager
def writer_scope(kind, *, owner_token=None):
    runtime = _writer_runtime()
    inherited = owner_token or _owner.get()
    if runtime is None:
        if inherited is not None:
            raise SnapshotUnavailable("Owner token has no registered runtime.")
        yield None
        return
    if inherited is not None and not inherited.closed:
        if inherited.kind != kind:
            raise SnapshotUnavailable("Nested writer belongs to another output scope.")
        runtime.authorize_writer(inherited)
        token = _owner.set(inherited)
        try:
            yield inherited
        finally:
            _owner.reset(token)
        return
    owner = runtime.begin_writer(kind)
    token = _owner.set(owner)
    try:
        yield owner
    except BaseException:
        runtime.uncertain_writer(owner)
        raise
    else:
        if owner.failed:
            runtime.uncertain_writer(owner)
        else:
            runtime.finish_writer(owner)
    finally:
        _owner.reset(token)


def admitted_writer(kind):
    """Compatibility seam for synchronous writers and explicitly passed tokens."""

    def decorate(function):
        @wraps(function)
        def run(*args, owner_token=None, **kwargs):
            with writer_scope(kind, owner_token=owner_token) as owner:
                result = function(*args, **kwargs)
                if (
                    owner is not None
                    and isinstance(result, dict)
                    and result.get("success") is False
                ):
                    owner.failed = True
            if owner is not None and owner.closed and not owner.failed and isinstance(result, dict):
                result["export_preparation_id"] = owner.claim.preparation_id
            return result

        return run

    return decorate


def collect_producer_captures(function):
    @wraps(function)
    async def run(*args, **kwargs):
        token = _captures.set([])
        try:
            return await function(*args, **kwargs)
        finally:
            _captures.reset(token)

    return run


async def drain_thread(function, *args, **kwargs):
    """Cancellation never releases a writer while its SQL thread is still alive."""
    pending = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    try:
        return await asyncio.shield(pending)
    except asyncio.CancelledError:
        while not pending.done():
            try:
                await asyncio.shield(pending)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        # Retrieve exceptions while preserving cancellation as the caller outcome.
        if pending.done() and not pending.cancelled():
            pending.exception()
        raise


@dataclass
class WriterOwner:
    claim: object
    connection: object
    session_guard: object
    kind: str
    closed: bool = False
    failed: bool = False
    completion: dict | None = None


class LegacyExportRuntime:
    """Injected S10C producer composition with immutable configuration per writer.

    `configuration` is an already collected/validated private registration mapping.
    `capture` reads complete SQL outputs on the supplied connection, returning
    sections and committed evidence. It must not contact providers or recompute.
    """

    def __init__(self, *, dal, coordinator, store, account, configuration, capture=None):
        self.dal, self.coordinator, self.store = dal, coordinator, store
        self.account = account
        self.configuration = _json(configuration)
        self.capture = capture or dal.capture_outputs
        if not coordinator.preparations:
            raise ValueError("S10C preparation-aware coordinator required.")

    @contextmanager
    def configuration_requests(self):
        from uuid import uuid4

        from services.export_provider_adapter import ProviderAdapter, use_provider
        from services.export_request_budget import RequestBudget

        scope = json.loads(self.configuration)["config"]
        identifier = self.dal.request(
            account=self.account,
            consumer="config",
            kvk_no=None,
            request={"read_configuration": str(uuid4())},
            storage_owner=self.store.storage_owner,
            actor="system:configuration",
            reason="Read immutable configuration inputs",
        )
        keys = tuple(
            sorted(
                {"account:" + self.account, *("destination:" + d for d in scope["destinations"])}
            )
        )
        claim = self.dal.claim(
            identifier,
            account=self.account,
            storage_owner=self.store.storage_owner,
            stage="preflight",
            resource_keys=keys,
        )
        if claim is None:
            self.dal.withdraw_unstarted(identifier)
            raise SnapshotUnavailable("Configuration read unavailable: account admission refused.")

        def authorize(*, mutation):
            if mutation:
                raise SnapshotUnavailable("Configuration collection is read-only.")
            self.dal.authorize(claim)

        adapter = ProviderAdapter(
            budget=RequestBudget(self.coordinator, self.account),
            authorize=authorize,
            destinations=scope["destinations"],
        )
        try:
            with use_provider(adapter):
                yield
            self.dal.transition(claim, expected="preflight", state="completed", release=True)
        except BaseException:
            self.dal.uncertain(claim)
            raise

    def begin_writer(self, kind):
        from uuid import uuid4

        configuration = json.loads(self.configuration)
        scope = configuration[kind]
        identifier = self.dal.request(
            account=self.account,
            consumer=scope["consumer"],
            kvk_no=scope.get("kvk_no"),
            request={"operation": str(uuid4()), "kind": kind, "config": scope},
            storage_owner=self.store.storage_owner,
            actor="system:legacy_writer",
            reason=kind,
        )
        claim = self.dal.claim(
            identifier,
            account=self.account,
            storage_owner=self.store.storage_owner,
            stage="preflight",
            resource_keys=("account:" + self.account,),
        )
        if claim is None:
            self.dal.withdraw_unstarted(identifier)
            raise SnapshotUnavailable(
                "Writer unavailable: account admission refused before execution."
            )
        claim = self.dal.transition(claim, expected="preflight", state="sql_pending", release=True)
        claim = self.dal.claim(
            identifier,
            account=self.account,
            storage_owner=self.store.storage_owner,
            stage="writing",
            resource_keys=("sql_snapshot:legacy_outputs",),
        )
        if claim is None:
            self.dal.withdraw_unstarted(identifier)
            raise SnapshotUnavailable("Writer unavailable: SQL admission refused before execution.")
        collection = _captures.get()
        if collection is not None:
            # Invalidate an earlier producer in this pipeline as soon as a later
            # writer starts. Its failure cannot silently select the older capture.
            collection.append((scope["consumer"], scope.get("kvk_no"), None))
        connection = None
        try:
            connection = self.dal.connect()
            connection.autocommit = True
            guard = self.dal.session(claim, connection)
            guard.__enter__()
        except BaseException:
            try:
                self.dal.uncertain(claim)
            finally:
                if connection is not None:
                    connection.close()
            raise
        return WriterOwner(claim, connection, guard, kind)

    def authorize_writer(self, owner):
        if owner.closed:
            raise SnapshotUnavailable("Writer admission has ended.")
        return self.dal.authorize(owner.claim)

    def _close_writer(self, owner):
        owner.closed = True
        try:
            owner.session_guard.__exit__(None, None, None)
        finally:
            owner.connection.close()

    def uncertain_writer(self, owner):
        if owner.closed:
            return
        try:
            self.dal.uncertain(owner.claim)
        finally:
            self._close_writer(owner)

    def checkpoint_writer(self, owner, evidence, *, cursor=None):
        if owner.completion is not None:
            raise SnapshotUnavailable("A producer cannot overwrite its completed generation.")
        scope = json.loads(self.configuration)[owner.kind]
        pending = dict(
            completion="committed",
            commit_identity=owner.claim.preparation_id,
            capture="pending",
            registration_sha256=configuration_digest(scope),
            producer=json.loads(_json(evidence)),
        )
        owner.claim = self.dal.transition(
            owner.claim,
            expected="writing",
            state="committed",
            generation=pending,
            external_cursor=cursor,
        )
        owner.completion = pending

    def finish_writer(self, owner):
        if owner.closed:
            return
        try:
            self.authorize_writer(owner)
            scope = json.loads(self.configuration)[owner.kind]
            if scope["consumer"] == "config":
                owner.claim = self.dal.transition(
                    owner.claim, expected="writing", state="completed", release=True
                )
                return
            pending = owner.completion
            if pending is None:
                raise SnapshotUnavailable("Producer did not acknowledge complete SQL output.")
            sections, planned = self.capture(owner.connection, scope)
            proof = dict(
                pending,
                capture="complete",
                output_sha256=output_digest(sections),
                config_sha256=configuration_digest(planned),
            )
            snapshot = LegacySnapshot.capture(
                consumer=scope["consumer"],
                preparation_id=owner.claim.preparation_id,
                generation=proof,
                config=planned,
                provenance={"owner": owner.claim.owner, "fence": owner.claim.fence},
                sections=sections,
            )
            owner.claim = self.dal.transition(
                owner.claim, expected="committed", state="committed", generation=proof
            )
            receipt = snapshot.persist(self.store)
            self.dal.captured(owner.claim, receipt)
            collection = _captures.get()
            if collection is not None:
                collection.append(
                    (scope["consumer"], scope.get("kvk_no"), owner.claim.preparation_id)
                )
        except BaseException:
            # No automatic recapture after a post-commit/spool/receipt failure.
            # An unknown acknowledgment leaves its durable row/claim intact.
            raise
        finally:
            self._close_writer(owner)

    def enqueue_snapshot(self, preparation_id):
        from services.export_coordination_dal import JobSpec

        row = self.dal.read(preparation_id)
        if row["AccountKey"] != self.account or row["StorageOwner"] != self.store.storage_owner:
            raise SnapshotUnavailable("Capture belongs to another account or storage owner.")
        if row["State"] not in {"captured", "materialized"}:
            raise SnapshotUnavailable("Committed capture is pending or unavailable.")
        receipt = SnapshotReceipt(
            row["SpoolKey"], row["SpoolBytes"], bytes(row["SpoolHash"]).hex(), row["StorageOwner"]
        )
        snapshot = LegacySnapshot.load(self.store.read(receipt))
        metadata = snapshot.metadata()
        if metadata["preparation_id"] != str(row["PreparationID"]).lower():
            raise SnapshotUnavailable("Snapshot preparation identity differs.")
        config = metadata["config"]
        registered = json.loads(self.configuration)[row["ConsumerKind"]]
        if metadata["generation"].get("registration_sha256") != configuration_digest(registered):
            raise SnapshotUnavailable("Retained output registration differs from this runtime.")
        return self.coordinator.enqueue(
            JobSpec(
                account=row["AccountKey"],
                consumer=row["ConsumerKind"],
                kvk_no=row["KVK_NO"],
                input_hash=bytes.fromhex(receipt.sha256),
                destinations=tuple(sorted(set(config["destinations"]))),
                actor=row["Actor"],
                reason=row["Reason"],
                spool_key=receipt.key,
                spool_bytes=receipt.byte_count,
                storage_owner=receipt.storage_owner,
                provenance=_json(metadata["generation"]),
            ),
            preparation_id=preparation_id,
        )

    def validate_destination(self, *, kvk_no, sheet_name):
        scope = json.loads(self.configuration)["all_kvk"]
        if (scope["kvk_no"], scope["primary_sheet"]) != (kvk_no, sheet_name):
            raise SnapshotUnavailable("Requested season/destination has no matching registration.")

    def submit(self, *, consumer, kvk_no=None, preparation_id=None):
        if preparation_id is None:
            owner = _owner.get()
            if owner is not None and not owner.closed:
                raise SnapshotUnavailable("Capture cannot finish inside an active producer.")
            else:
                captures = _captures.get()
                if captures is not None:
                    matching = [p for c, k, p in captures if (c, k) == (consumer, kvk_no)]
                    if not matching or matching[-1] is None:
                        raise SnapshotUnavailable(
                            "This producer has no verified committed capture."
                        )
                    preparation_id = matching[-1]
                else:
                    preparation_id = self.dal.latest_ready(
                        account=self.account,
                        consumer=consumer,
                        kvk_no=kvk_no,
                        storage_owner=self.store.storage_owner,
                    )
        row = self.dal.read(preparation_id)
        if (row["ConsumerKind"], row["KVK_NO"]) != (consumer, kvk_no):
            raise SnapshotUnavailable("Capture belongs to another consumer or season.")
        return self.enqueue_snapshot(preparation_id)
