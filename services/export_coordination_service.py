"""Shared durable export worker. Production admission is gated until S10C/S11.

Injected adapters operate only on claimed jobs. A running thread is never detached
to make a replacement eligible. Memory wakeups and the local task monitor are hints;
the coordinator database remains the ownership authority.
"""

import asyncio
from dataclasses import dataclass
import logging
import threading

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import JobSpec
from services.export_request_budget import BudgetCompletionUnknown, RequestBudget
from services.export_snapshot_store import SnapshotReceipt

logger = logging.getLogger(__name__)
_worker = None
_loop = None


@dataclass(frozen=True)
class ExportRegistration:
    kvk_no: int
    account: str
    epoch: int
    destinations: tuple[str, ...]


class ExportCoordinator:
    def __init__(self, dal, *, adapters, registrations=(), storage=None):
        self.dal, self.adapters = dal, dict(adapters)
        self.registrations, self.storage = tuple(registrations), storage
        self.after = (0, 0)
        self.last_account = ""

    def discover(self):
        intents = self.dal.pending_intents(after=self.after)
        if not intents:
            self.after = (0, 0)
        for intent in intents:
            for registration in self.registrations:
                if registration.kvk_no != intent["KVK_NO"]:
                    continue
                try:
                    self.dal.enqueue(
                        JobSpec(
                            account=registration.account,
                            consumer="new_source",
                            input_hash=bytes(intent["VectorHash"]),
                            destinations=registration.destinations,
                            actor="system:export_coordinator",
                            reason="Committed complete export intent",
                            kvk_no=registration.kvk_no,
                            intent_id=intent["IntentID"],
                            epoch=registration.epoch,
                        )
                    )
                except SourceConflict:
                    logger.info(
                        "Export intent remains pending kvk=%s intent=%s",
                        intent["KVK_NO"],
                        intent["IntentID"],
                    )
            self.after = (intent["KVK_NO"], intent["CommitSequence"])

    def run_batch(self, stop, limit=8):
        if stop.is_set():
            return
        self.discover()
        processed = 0
        accounts = sorted(self.dal.accounts())
        accounts = [a for a in accounts if a > self.last_account] + [
            a for a in accounts if a <= self.last_account
        ]
        for account in accounts:
            if stop.is_set() or processed >= limit:
                return
            self.last_account = account
            try:
                claim = self.dal.claim_next(
                    account, storage_owner=self.storage.storage_owner if self.storage else None
                )
            except Exception as exc:
                logger.warning("Export admission deferred error_type=%s", type(exc).__name__)
                continue
            if claim is None:
                continue
            processed += 1
            try:
                job = self.dal.authorize(claim)
                adapter = self.adapters.get(job["ConsumerKind"])
                if adapter is None:
                    raise SourceConflict("Required consumer adapter is unavailable.")
                snapshot = None
                if job["SpoolKey"] is not None:
                    if self.storage is None:
                        raise SourceConflict("Registered durable storage is unavailable.")
                    snapshot = self.storage.read(
                        SnapshotReceipt(
                            job["SpoolKey"],
                            job["SpoolBytes"],
                            bytes(job["InputHash"]).hex(),
                            job["StorageOwner"],
                        )
                    )
                adapter(
                    job,
                    claim,
                    self.dal,
                    RequestBudget(self.dal, account, stop=stop),
                    stop,
                    snapshot,
                )
            except BaseException as exc:
                try:
                    if isinstance(exc, BudgetCompletionUnknown):
                        self.dal.fail(claim, retain_claims=True)
                    else:
                        self.dal.fail(claim)
                except Exception:
                    # Commit acknowledgment loss or newer durable state: retain it.
                    # Never release independently after a failed terminal write.
                    logger.warning("Export stop retained ownership job=%s", claim.job_id)
                logger.warning(
                    "Export worker stopped job=%s error_type=%s", claim.job_id, type(exc).__name__
                )
                if not isinstance(exc, Exception):
                    raise


class ExportWorker:
    def __init__(self, factory, *, interval=30, batch_size=8):
        if (
            type(interval) is not int
            or not 1 <= interval <= 300
            or type(batch_size) is not int
            or not 1 <= batch_size <= 32
        ):
            raise ValueError("Bounded export discovery required.")
        self.factory, self.interval, self.batch_size = factory, interval, batch_size
        self.stop = threading.Event()
        self.wake = asyncio.Event()

    async def run(self):
        service = None
        pending = None
        try:
            while not self.stop.is_set():
                self.wake.clear()
                try:
                    if service is None:
                        pending = asyncio.create_task(asyncio.to_thread(self.factory))
                        service = await asyncio.shield(pending)
                    pending = asyncio.create_task(
                        asyncio.to_thread(service.run_batch, self.stop, self.batch_size)
                    )
                    await asyncio.shield(pending)
                except Exception as exc:
                    logger.warning(
                        "Export coordinator unavailable error_type=%s", type(exc).__name__
                    )
                if not self.stop.is_set():
                    try:
                        await asyncio.wait_for(self.wake.wait(), self.interval)
                    except TimeoutError:
                        pass
        finally:
            self.stop.set()
            if pending is not None:
                # Repeated cancellation still must not make a live thread replaceable.
                while not pending.done():
                    try:
                        await asyncio.shield(pending)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break


def wake_exports():
    if _worker is not None and _loop is not None and not _loop.is_closed():
        try:
            _loop.call_soon_threadsafe(_worker.wake.set)
        except RuntimeError:
            logger.debug("Export wake deferred to durable discovery.")


def configured_coordinator():
    # S10B has no legacy/scan adapters or deployment-attestation owner. An enabling
    # environment flag cannot stand in for those later gates. No SQL/credentials
    # are opened and no directories created by this fail-closed factory.
    raise SourceConflict("Export admission requires S10C adapters and deployment gates.")


def register_exports(task_monitor, *, factory=None):
    import bot_config

    if not bot_config.EXPORT_COORDINATION_ENABLED:
        return None
    global _worker, _loop
    if task_monitor.is_running("export_coordination"):
        return _worker
    # Production remains closed; dependency injection is for offline composition.
    if factory is None:
        logger.warning("Export admission disabled pending S10C adapters and deployment gates.")
        return None
    _loop = asyncio.get_running_loop()
    _worker = ExportWorker(factory)
    task_monitor.create("export_coordination", _worker.run)
    return _worker


def stop_export_admission():
    if _worker is not None:
        _worker.stop.set()
        wake_exports()
