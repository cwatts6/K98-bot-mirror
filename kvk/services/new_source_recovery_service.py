"""Default-off S5B config intent and recovery; daily claims have no owner here."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import logging
import threading

from kvk.dal.new_source_import_dal import SourceConflict, canonical

logger = logging.getLogger(__name__)
_worker = None
_worker_loop = None


def snapshot_config_import(cursor, windows, *, actor=None, provenance=None):
    import bot_config

    if not bot_config.KVK_SOURCE_RECOVERY_ENABLED:
        return ()
    import pandas as pd

    from kvk.dal.new_source_recovery_dal import snapshot_import

    records = []
    for record in windows.to_dict("records"):

        row = {"WindowName": str(record["WindowName"])}
        for key in ("KVK_NO", "StartScanID", "EndScanID"):
            value = record[key]
            if pd.isna(value):
                if key == "KVK_NO":
                    raise ValueError("Source KVK is required.")
                row[key] = None
            elif (
                isinstance(value, bool) or int(value) != value or not 1 <= int(value) <= 2147483647
            ):
                raise ValueError("Invalid source endpoint integer.")
            else:
                row[key] = int(value)
        records.append(row)
    if len({(r["KVK_NO"], r["WindowName"].casefold()) for r in records}) != len(records):
        raise ValueError("Duplicate imported source windows.")
    evidence = dict(provenance or {})
    evidence.update(
        importer="proc_config_import.run_proc_config_import",
        windows_digest=hashlib.sha256(canonical(records).encode()).hexdigest(),
    )
    return snapshot_import(
        cursor,
        records,
        actor=actor or "system:proc_config_import",
        origin="authorized_import" if actor else "system",
        provenance=evidence,
        requested_utc=datetime.now(UTC).replace(microsecond=0),
    )


def wake_recovery():
    """Wake is a hint; periodic SQL discovery survives lost hints/other processes."""
    if _worker is not None and _worker_loop is not None and not _worker_loop.is_closed():
        try:
            _worker_loop.call_soon_threadsafe(_worker.wake.set)
        except RuntimeError:
            # The loop may close between the check and enqueue. SQL remains authoritative.
            logger.debug("Source recovery wake deferred until next startup.")


class RecoveryIntakeAdapter:
    """Retain existing S5A authorization; wake only after durable confirmation."""

    def __init__(self, service):
        self.service = service

    def __getattr__(self, name):
        return getattr(self.service, name)

    def confirm(self, *args, **kwargs):
        result = self.service.confirm(*args, **kwargs)
        wake_recovery()
        return result


@dataclass(frozen=True)
class ExportTarget:
    kvk_no: int
    destination: object
    transport: object


def deliver_current_exports(dal, repository, targets, season, *, changed=None):
    """Compatibility boundary: S8B retains intents until the S10 worker is installed."""
    raise SourceConflict("Automatic export execution requires the S10 coordinator.")


class RecoveryService:
    def __init__(self, dal, publisher, delivery_repository=None, targets=()):
        self.dal, self.publisher = dal, publisher
        self.delivery_repository, self.targets = delivery_repository, targets
        self.after = (0, "")

    def recover_period(self, season, period):
        from kvk.services.source_update_service import SourceUpdateService

        updates = self.dal.ready_updates(season, period)
        service = SourceUpdateService(self.dal.connect)
        result = None
        for update in updates:
            try:
                result = service.publish(update["UpdateID"])
            except SourceConflict:
                logger.warning(
                    "Source update remains pending kvk=%s period=%s update=%s",
                    season,
                    period,
                    update["UpdateID"],
                )
        return result

    def run_batch(self, stop, limit=8):
        periods = self.dal.periods(self.after, limit)
        if not periods:
            self.after = (0, "")
            return
        for season, period in periods:
            if stop.is_set():
                break
            try:
                self.recover_period(season, period)
            except Exception as exc:
                logger.warning(
                    "Source recovery pending kvk=%s period=%s error=%s",
                    season,
                    period,
                    type(exc).__name__,
                )
            # S8B commits durable full-vector intents. S10 owns provider admission
            # and execution; never deliver raw component selections from this worker.
            self.after = (season, period)


class RecoveryWorker:
    def __init__(self, factory, *, interval=30, batch_size=8):
        if not 1 <= interval <= 300 or not 1 <= batch_size <= 32:
            raise ValueError("Invalid recovery bounds.")
        self.factory, self.interval, self.batch_size = factory, interval, batch_size
        self.wake = asyncio.Event()
        self.stop = threading.Event()

    async def run(self):
        service = None
        pending = None
        self.stop.clear()
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
                    logger.warning("Source recovery unavailable error=%s", type(exc).__name__)
                try:
                    await asyncio.wait_for(self.wake.wait(), timeout=self.interval)
                except TimeoutError:
                    pass
        finally:
            self.stop.set()
            # Cancellation must not detach a still-running SQL job and start its replacement.
            if pending is not None:
                try:
                    await asyncio.shield(pending)
                except Exception as exc:
                    logger.warning("Source recovery stopped error=%s", type(exc).__name__)


def parse_export_registrations(value, *, protected_file_ids=()):
    """Validate operator configuration before opening SQL or credentials."""
    from kvk.services.new_source_export_service import SheetsRegistration

    try:
        records = json.loads(value)
    except (TypeError, ValueError):
        raise ValueError("Export registrations must be a JSON array.") from None
    if not isinstance(records, list) or len(records) > 8:
        raise ValueError("At most eight explicit export registrations are supported.")
    result, used = [], set(protected_file_ids)
    required = {"kvk_no", "index_file_id", "slot_file_ids", "owner_email", "service_account_email"}
    for record in records:
        if (
            not isinstance(record, dict)
            or not required <= record.keys()
            or record.keys() - required - {"audience"}
        ):
            raise ValueError("Export registration fields do not match the documented schema.")
        season = record["kvk_no"]
        if type(season) is not int or not 1 <= season <= 2147483647:
            raise ValueError("Explicit export KVK is required.")
        slots = record["slot_file_ids"]
        if (
            not isinstance(slots, list)
            or not 2 <= len(slots) <= 16
            or any(not isinstance(x, str) for x in slots)
        ):
            raise ValueError("Register two to sixteen workbook slot IDs.")
        if any(
            not isinstance(record[k], str)
            for k in ("index_file_id", "owner_email", "service_account_email")
        ):
            raise ValueError("Export identity fields must be strings.")
        registration = SheetsRegistration(
            record["index_file_id"],
            tuple(slots),
            record["owner_email"],
            record["service_account_email"],
            record.get("audience", "private"),
        )
        ids = {registration.index_file_id, *registration.slot_file_ids}
        if used.intersection(ids):
            raise ValueError(
                "Export workbooks must be distinct and cannot use protected workbooks."
            )
        used.update(ids)
        result.append((season, registration))
    return tuple(result)


def configured_recovery():
    import bot_config
    from constants import ALL_KVK_SHEET_ID, KVK_SHEET_ID
    from kvk.dal.new_source_admin_dal import configured_connection
    from kvk.dal.new_source_recovery_dal import RecoveryDAL
    from kvk.services.new_source_publication_service import PublicationService

    def connect():
        connection = configured_connection()
        connection.timeout = 30
        return connection

    protected = tuple(x for x in (KVK_SHEET_ID, ALL_KVK_SHEET_ID) if x)
    parse_export_registrations(
        bot_config.KVK_SOURCE_EXPORT_REGISTRATIONS, protected_file_ids=protected
    )
    dal = RecoveryDAL(connect)
    dal.check_schema()
    return RecoveryService(dal, PublicationService(connect))


def register_recovery(task_monitor, *, factory=None):
    import bot_config

    if not bot_config.KVK_SOURCE_RECOVERY_ENABLED:
        return None
    global _worker, _worker_loop
    if task_monitor.is_running("kvk_source_recovery"):
        return _worker
    _worker_loop = asyncio.get_running_loop()
    _worker = RecoveryWorker(
        factory or configured_recovery,
        interval=bot_config.KVK_SOURCE_RECOVERY_INTERVAL_SECONDS,
        batch_size=bot_config.KVK_SOURCE_RECOVERY_BATCH_SIZE,
    )
    task_monitor.create("kvk_source_recovery", _worker.run)
    return _worker
