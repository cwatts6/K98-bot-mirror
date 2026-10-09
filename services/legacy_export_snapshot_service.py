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
import logging
import math
import time
from uuid import UUID

from services.export_contention import (
    CoordinationLockRefused,
    admission_diagnostics_enabled,
    sql_error_facts,
)
from services.export_snapshot_store import SnapshotReceipt

logger = logging.getLogger(__name__)


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
    current = _runtime.get()
    owner = _owner.get()
    if (current is not None and current is not runtime) or (
        owner is not None and owner.runtime is not runtime
    ):
        raise SnapshotUnavailable("An inherited export scope cannot switch runtime.")
    token = _runtime.set(runtime)
    try:
        yield runtime
    finally:
        _runtime.reset(token)


def current_owner():
    return _owner.get()


def has_runtime_context():
    """Identify an inherited export scope without admitting a new writer."""
    return _runtime.get() is not None


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


def verify_producer_cursor(cursor, *, before_side_effects=False):
    """Actual connection gate; a separate snapshot guard session is insufficient."""
    runtime = _writer_runtime()
    if runtime is None:
        return
    owner = current_owner()
    if owner is None:
        raise SnapshotUnavailable("Actual SQL producer has no admitted writer owner.")
    runtime._require_writer(owner)
    _writer_event(owner, "pre_execution_authorization", "requested")
    try:
        runtime.dal.verify_producer_cursor(owner.claim, cursor)
    except BaseException as error:
        _writer_event(owner, "pre_execution_authorization", "failed", error)
        if (
            before_side_effects
            and not owner.producer_authorized
            and isinstance(error, CoordinationLockRefused)
            and error.result == -1
            and error.transaction_released
        ):
            owner.safe_pre_execution_refusal = True
        raise
    owner.producer_authorized = True
    _writer_event(owner, "pre_execution_authorization", "confirmed")


def _writer_event(owner, stage, outcome, error=None):
    from services.legacy_export_snapshot_dal import _diagnostic_counter, _diagnostic_uuid

    claim = owner.claim
    record = dict(
        preparation_id=_diagnostic_uuid(claim.preparation_id),
        owner_id=_diagnostic_uuid(claim.owner),
        fence=_diagnostic_counter(claim.fence),
        version=_diagnostic_counter(claim.version),
        writer_kind=owner.kind if owner.kind in {"all_kvk", "scan_data", "config"} else None,
        stage=stage,
        outcome=outcome,
    )
    if error is not None:
        record.update(sql_error_facts(error))
    logger.log(
        logging.WARNING if error is not None else logging.INFO,
        "export_writer_stage %s",
        json.dumps(record, sort_keys=True),
    )


def record_writer_stage(stage):
    """Local observation only; a log never substitutes for a durable receipt."""
    if stage not in {
        "producer_entered",
        "producer_returned",
        "commit_requested",
        "commit_confirmed",
    }:
        raise ValueError("Unknown producer diagnostic stage.")
    owner = current_owner()
    if owner is not None:
        _writer_event(owner, stage, "observed_not_durable_proof")


@contextmanager
def configuration_requests(*, wait_for_admission=False):
    runtime = _writer_runtime()
    if runtime is None:
        yield
    else:
        if current_owner() is not None and not current_owner().closed:
            raise SnapshotUnavailable("Collect provider configuration before SQL writer admission.")
        with runtime.configuration_requests(wait_for_admission=wait_for_admission):
            yield


def require_runtime():
    runtime = _runtime.get()
    if runtime is None:
        raise SnapshotUnavailable("Coordinated export setup is unavailable; no export started.")
    return runtime


def _writer_runtime():
    runtime = _runtime.get()
    if runtime is not None:
        from services.export_runtime_composition import validate_caller_context

        validate_caller_context(runtime)
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
    current = _owner.get()
    if owner_token is not None and current is not None and owner_token is not current:
        raise SnapshotUnavailable("Explicit writer owner differs from the inherited owner.")
    inherited = owner_token if owner_token is not None else current
    if runtime is None:
        if inherited is not None:
            raise SnapshotUnavailable("Owner token has no registered runtime.")
        yield None
        return
    if inherited is not None:
        # A delayed child or explicit stale token must not create a new root
        # writer after its original scope closed, even on the same runtime.
        runtime._require_writer(inherited)
        if inherited.kind != kind:
            raise SnapshotUnavailable("Nested writer belongs to another output scope.")
        runtime.authorize_writer(inherited)
        token = _owner.set(inherited)
        try:
            yield inherited
        except BaseException:
            # The root may catch a helper's failure. Keep that failure attached
            # to its shared owner so it cannot publish a partial generation.
            inherited.failed = True
            raise
        finally:
            _owner.reset(token)
        return
    owner = runtime.begin_writer(kind)
    token = _owner.set(owner)
    try:
        yield owner
    except BaseException as original:
        _writer_event(owner, "writer_body", "failed", original)
        try:
            recovered = False
            if owner.stats_execution_registered and owner.stats_execution_dispatched:
                from services.stats_import_outcome_service import recover_completed_writer

                try:
                    recovered = recover_completed_writer(runtime, owner)
                except Exception as recovery_error:
                    _writer_event(owner, "completion_recovery", "failed", recovery_error)
            if recovered:
                if not owner.closed:
                    runtime._close_writer(owner)
            elif (
                owner.stats_import_context
                and not owner.stats_execution_dispatched
                and not owner.stats_execution_registered
            ):
                runtime.unstarted_stats_writer(owner)
            elif owner.safe_pre_execution_refusal and isinstance(original, CoordinationLockRefused):
                runtime.refused_writer(owner)
            else:
                runtime.uncertain_writer(owner)
                if owner.stats_execution_registered:
                    from services.stats_import_outcome_service import settle_known_failure

                    settle_known_failure(runtime, owner.claim.preparation_id)
        except BaseException as cleanup:
            _writer_event(owner, "uncertain_cleanup", "failed", cleanup)
        # Retain the actual failure even when uncertainty persistence/close fails.
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
            if (
                owner is not None
                and owner.closed
                and owner.failed
                and not (isinstance(result, dict) and result.get("success") is False)
            ):
                raise SnapshotUnavailable("Writer outcome requires reconciliation.")
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


@contextmanager
def caller_runtime():
    """Bind each actual caller, including independently scheduled Discord tasks."""
    from services.export_runtime_composition import caller_scope

    with caller_scope(_runtime.get()) as runtime:
        if runtime is None:
            yield None
        else:
            with use_runtime(runtime):
                yield runtime


def bound_runtime(function):
    """Own the complete call and drain its async work before releasing admission."""
    import inspect

    if inspect.iscoroutinefunction(function):

        @wraps(function)
        async def asynchronous(*args, **kwargs):
            with caller_runtime() as runtime:
                if runtime is None:
                    return await function(*args, **kwargs)
                pending = asyncio.create_task(function(*args, **kwargs))
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
                    if pending.done() and not pending.cancelled():
                        pending.exception()
                    raise

        return asynchronous

    @wraps(function)
    def synchronous(*args, **kwargs):
        with caller_runtime():
            return function(*args, **kwargs)

    return synchronous


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
    runtime: object
    closed: bool = False
    failed: bool = False
    completion: dict | None = None
    producer_authorized: bool = False
    safe_pre_execution_refusal: bool = False
    stats_execution_registered: bool = False
    stats_import_context: bool = False
    stats_execution_dispatched: bool = False


class LegacyExportRuntime:
    """Injected S10C producer composition with immutable configuration per writer.

    `configuration` is an already collected/validated private registration mapping.
    `capture` reads complete SQL outputs on the supplied connection, returning
    sections and committed evidence. It must not contact providers or recompute.
    """

    def __init__(
        self,
        *,
        dal,
        coordinator,
        store,
        account,
        configuration,
        capture=None,
        authority_stream=None,
    ):
        self.dal, self.coordinator, self.store = dal, coordinator, store
        self.account = account
        self.configuration = _json(configuration)
        self.capture = capture or dal.capture_outputs
        self.authority_stream = authority_stream
        if not coordinator.preparations:
            raise ValueError("S10C preparation-aware coordinator required.")
        if (getattr(dal, "execution_evidence", False) is True) != (
            getattr(coordinator, "execution_evidence", False) is True
        ):
            raise ValueError("Configuration preparation and coordinator evidence gates differ.")

    def configuration_health_destination(self, preferred):
        """Select a representative from the immutable admitted health scope."""
        scope = json.loads(self.configuration).get("config", {})
        destinations = scope.get("destinations")
        if (
            not isinstance(destinations, list)
            or not destinations
            or any(not isinstance(value, str) or not value for value in destinations)
        ):
            raise SnapshotUnavailable("Registered configuration health scope is unavailable.")
        return preferred if preferred in destinations else min(destinations)

    @contextmanager
    def configuration_requests(self, *, wait_for_admission=False):
        from uuid import uuid4

        from services.export_provider_adapter import ProviderAdapter, use_provider
        from services.export_request_budget import RequestBudget

        if getattr(self.dal, "execution_evidence", False) is True and self.authority_stream is None:
            raise SnapshotUnavailable("S11 configuration reads need an exact authority probe.")
        if (
            getattr(self.dal, "execution_evidence", False) is not True
            and self.authority_stream is not None
        ):
            raise SnapshotUnavailable("Authority probe requires the matching SQL evidence gate.")

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
        claim = self._claim_unstarted(
            identifier,
            account=self.account,
            storage_owner=self.store.storage_owner,
            stage="preflight",
            resource_keys=keys,
            wait_for_admission=wait_for_admission,
        )
        if claim is None:
            self.dal.withdraw_unstarted(identifier)
            raise SnapshotUnavailable("Configuration read unavailable: account admission refused.")

        def authorize(*, mutation):
            if mutation:
                raise SnapshotUnavailable("Configuration collection is read-only.")
            self.dal.authorize(claim)

        from contextlib import nullcontext

        owner = (
            self.authority_stream(claim, scope["destinations"])
            if self.authority_stream is not None
            else nullcontext(None)
        )
        try:
            with owner as stream:
                adapter = ProviderAdapter(
                    budget=RequestBudget(self.coordinator, self.account),
                    authorize=authorize,
                    destinations=scope["destinations"],
                    execution=stream.execute if stream is not None else None,
                    stream_id=stream.stream_id if stream is not None else None,
                )
                with use_provider(adapter):
                    yield
            self.dal.transition(claim, expected="preflight", state="completed", release=True)
        except BaseException:
            self.dal.uncertain(claim)
            raise

    def _claim_unstarted(self, identifier, *, wait_for_admission=True, **kwargs):
        """Wait only after an acknowledged refusal, before any execution starts.

        Keep the same durable queue ticket. An exception can mean an unknown
        claim outcome and must escape immediately; it is never retried here.
        Health probes opt out so their short observation timeout stays intact.
        """
        from services.legacy_export_snapshot_dal import _diagnostic_uuid

        started = time.monotonic()
        deadline = started + 60.0

        def report(outcome, attempt, now, error_type=None):
            record = dict(
                preparation_id=_diagnostic_uuid(identifier),
                stage=kwargs["stage"],
                outcome=outcome,
                attempt=attempt + 1,
                elapsed_ms=max(0, int((now - started) * 1000)),
                wait_enabled=bool(wait_for_admission),
            )
            if error_type is not None:
                record["error_type"] = (
                    error_type[:64]
                    if error_type.isascii() and error_type.isidentifier()
                    else "UnknownError"
                )
            logger.info(
                "export_admission_result %s",
                json.dumps(record, sort_keys=True, separators=(",", ":")),
            )

        for attempt in range(61):
            diagnostic_token = admission_diagnostics_enabled.set(attempt % 30 == 0)
            try:
                claim = self.dal.claim(identifier, **kwargs)
            except CoordinationLockRefused as exc:
                if exc.result in {-2, -3, -999} and exc.transaction_released:
                    # A terminal attributed refusal with acknowledged rollback
                    # and close cannot have admitted this attempt. The caller is
                    # abandoning its exact ticket; leave no pending queue blocker.
                    # The DAL CAS still rejects admitted/owned or captured work.
                    try:
                        self.dal.withdraw_unstarted(identifier)
                    except BaseException as cleanup:
                        report(
                            "withdrawal_unknown", attempt, time.monotonic(), type(cleanup).__name__
                        )
                        raise
                    report(
                        "terminal_refusal_withdrawn", attempt, time.monotonic(), type(exc).__name__
                    )
                    raise
                if exc.result != -1 or not exc.transaction_released:
                    report("unknown", attempt, time.monotonic(), type(exc).__name__)
                    raise
                # The exact ticket is unchanged by the acknowledged rollback.
                # This existing outer wait owns the budget; no nested retry loop.
                claim = None
            except BaseException as exc:
                report("unknown", attempt, time.monotonic(), type(exc).__name__)
                raise
            finally:
                admission_diagnostics_enabled.reset(diagnostic_token)
            now = time.monotonic()
            if claim is not None:
                report("admitted", attempt, now)
                return claim
            try:
                remaining = deadline - now
                if not wait_for_admission or attempt == 60 or remaining <= 0:
                    report("confirmed_refusal", attempt, now)
                    return None
                if attempt % 30 == 0:
                    report("waiting", attempt, now)
                time.sleep(min(1.0, remaining))
            except BaseException as exc:
                # The preceding claim returned an acknowledged refusal. No
                # provider/SQL execution or subsequent claim began, so the
                # existing guarded CAS can withdraw this unstarted ticket.
                try:
                    self.dal.withdraw_unstarted(identifier)
                except BaseException as cleanup:
                    report("withdrawal_unknown", attempt, time.monotonic(), type(cleanup).__name__)
                    raise
                report("wait_aborted_withdrawn", attempt, time.monotonic(), type(exc).__name__)
                raise
        return None

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
        claim = self._claim_unstarted(
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
        claim = self._claim_unstarted(
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
        owner = WriterOwner(claim, connection, guard, kind, self)
        _writer_event(owner, "writer_admission", "confirmed")
        return owner

    def _require_writer(self, owner):
        if not isinstance(owner, WriterOwner) or owner.runtime is not self:
            raise SnapshotUnavailable("Writer owner belongs to another runtime.")

    def authorize_writer(self, owner):
        self._require_writer(owner)
        if owner.closed:
            raise SnapshotUnavailable("Writer admission has ended.")
        if owner.failed:
            raise SnapshotUnavailable("Writer outcome requires reconciliation.")
        return self.dal.authorize(owner.claim)

    def _close_writer(self, owner):
        self._require_writer(owner)
        owner.closed = True
        try:
            owner.session_guard.__exit__(None, None, None)
        finally:
            owner.connection.close()

    def uncertain_writer(self, owner):
        self._require_writer(owner)
        if owner.closed:
            return
        try:
            self.dal.uncertain(owner.claim)
        finally:
            self._close_writer(owner)

    def refused_writer(self, owner):
        """Release only this live, explicitly unstarted writer after lock refusal.

        This proof cannot be reconstructed after restart and never applies to a
        retained uncertain preparation. A failed release keeps durable ownership.
        """
        self._require_writer(owner)
        if owner.closed or owner.producer_authorized or not owner.safe_pre_execution_refusal:
            raise SnapshotUnavailable("Exact live pre-execution refusal required.")
        self._close_writer(owner)
        owner.claim = self.dal.transition(
            owner.claim, expected="writing", state="unavailable", release=True
        )
        _writer_event(owner, "pre_execution_refusal", "withdrawal_commit_acknowledged")

    def unstarted_stats_writer(self, owner):
        """Live proof that this invocation never entered the SQL import wrapper.

        This proof is not reconstructed from age or process absence after restart.
        The normal exact-owner/version CAS still refuses any changed preparation.
        """
        self._require_writer(owner)
        if (
            owner.closed
            or owner.kind != "scan_data"
            or not owner.stats_import_context
            or owner.stats_execution_dispatched
            or owner.completion is not None
        ):
            raise SnapshotUnavailable("Exact live unstarted stats invocation required.")
        self._close_writer(owner)
        owner.claim = self.dal.transition(
            owner.claim, expected="writing", state="unavailable", release=True
        )
        _writer_event(owner, "pre_import_failure", "withdrawal_commit_acknowledged")

    def checkpoint_writer(self, owner, evidence, *, cursor=None):
        self._require_writer(owner)
        if owner.closed:
            raise SnapshotUnavailable("Writer admission has ended.")
        if owner.failed:
            raise SnapshotUnavailable("Writer outcome requires reconciliation.")
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
        _writer_event(owner, "durable_checkpoint", "requested")
        try:
            owner.claim = self.dal.transition(
                owner.claim,
                expected="writing",
                state="committed",
                generation=pending,
                external_cursor=cursor,
            )
        except BaseException as error:
            _writer_event(owner, "durable_checkpoint", "failed", error)
            raise
        _writer_event(
            owner,
            "durable_checkpoint",
            "pending_caller_commit" if cursor is not None else "commit_acknowledged",
        )
        owner.completion = pending

    def finish_writer(self, owner):
        self._require_writer(owner)
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
            _writer_event(owner, "snapshot_capture", "requested")
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
            _writer_event(owner, "snapshot_capture", "commit_acknowledged")
            self.collect_capture(owner)
        except BaseException as original:
            # No automatic recapture after a post-commit/spool/receipt failure.
            # An unknown acknowledgment leaves its durable row/claim intact.
            _writer_event(owner, "writer_completion", "failed", original)
            try:
                self._close_writer(owner)
            except BaseException as cleanup:
                _writer_event(owner, "writer_close", "failed", cleanup)
            raise
        finally:
            if not owner.closed:
                self._close_writer(owner)

    def collect_capture(self, owner):
        self._require_writer(owner)
        scope = json.loads(self.configuration)[owner.kind]
        collection = _captures.get()
        capture = (scope["consumer"], scope.get("kvk_no"), owner.claim.preparation_id)
        if collection is not None and capture not in collection:
            collection.append(capture)

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
        job = self.coordinator.enqueue(
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
        return str(job["JobID"])

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
