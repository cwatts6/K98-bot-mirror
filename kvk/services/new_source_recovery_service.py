"""Default-off S5B config intent and recovery; daily claims have no owner here."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import logging
import threading
from uuid import NAMESPACE_URL, uuid5

from kvk.dal.new_source_import_dal import SourceConflict, canonical
from kvk.models.new_source_reporting import EndpointChange

logger = logging.getLogger(__name__)
_worker = None
_worker_loop = None


def snapshot_config_import(cursor, windows, *, actor=None, provenance=None):
    import bot_config

    if not bot_config.KVK_SOURCE_RECOVERY_ENABLED:
        return ()
    from kvk.dal.new_source_recovery_dal import snapshot_import

    records = []
    for record in windows.to_dict("records"):
        import pandas as pd

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
    """Pick the changed anchor from durable receipts, including after worker restart."""
    from kvk.services.new_source_delivery_service import deliver_export
    from kvk.services.new_source_export_service import load_sheets_generation

    outcomes = []
    for target in targets:
        if target.kvk_no != season:
            continue
        if target.destination.kind == "discord":
            raise ValueError("Recovery never automatically posts Discord messages.")
        selections = dal.selections(season)
        if not selections:
            continue
        repository.check_selections(selections)
        generation = load_sheets_generation(connect=dal.connect, selections=selections)
        receipts = [(s, repository.read_receipt(s, target.destination)) for s in selections]
        # A confirmed anchor for an older combined generation cannot claim the new key.
        matching = [
            s
            for s, r in receipts
            if r
            and r.state == "confirmed"
            and r.receipt
            and json.loads(r.receipt).get("export_key") == generation.key
        ]
        if matching:
            # A completed combined receipt covers every included unchanged selection too.
            anchor = matching[0]
            outcomes.append(
                deliver_export(
                    generation=generation,
                    selection=anchor,
                    destination=target.destination,
                    repository=repository,
                    transport=target.transport,
                )
            )
            continue
        pending = [s for s, r in receipts if r is None or r.state != "confirmed"]
        anchor = changed if changed in pending else (pending[0] if pending else None)
        if anchor is None:
            raise SourceConflict("No changed delivery anchor for this generation.")
        outcomes.append(
            deliver_export(
                generation=generation,
                selection=anchor,
                destination=target.destination,
                repository=repository,
                transport=target.transport,
            )
        )
    return tuple(outcomes)


class RecoveryService:
    def __init__(self, dal, publisher, delivery_repository=None, targets=()):
        self.dal, self.publisher = dal, publisher
        self.delivery_repository, self.targets = delivery_repository, targets
        self.after = (0, "")

    def recover_period(self, season, period):
        data = self.dal.load_inputs(season, period)
        config, previous, request = data["config"], data["previous"], data["request"]
        change = None
        if previous and previous.config.version_id != config.version_id:
            if not request:
                raise SourceConflict("Changed configuration has no endpoint request.")
            # Validate chain in storage again under the publication CAS lock.
            from kvk.dal.new_source_recovery_dal import endpoint_chain

            chain = endpoint_chain(data["requests"], previous.config.version_id, config.version_id)
            first, last = chain[0], chain[-1]
            change = EndpointChange(
                str(last["RequestID"]),
                period,
                previous.config.version_id,
                config.version_id,
                first["OldEndScanID"],
                last["NewEndScanID"],
                last["Actor"],
                last["Reason"],
                first["OldStartScanID"],
                last["NewStartScanID"],
            )
            # A rapid round trip has authority but no net endpoint change. S3A's resolver
            # intentionally rejects a no-op transition; evaluate the exact desired slots.
            if (previous.config.start_scan_id, previous.config.end_scan_id) == (
                config.start_scan_id,
                config.end_scan_id,
            ):
                previous, change = None, None
        elif (
            previous
            and previous.player_state.value not in ("final", "corrected_final")
            and previous.endpoint_change is None
        ):
            previous = None  # Live input revisions are allowed to advance normally.
        candidate = self.publisher.build_candidate(
            config=config,
            observations=data["observations"],
            b0=data["b0"],
            aggregate=data["aggregate"],
            previous=previous,
            endpoint_change=change,
        )
        selected = data["selected"]
        if selected and str(selected["PublicationID"]) == candidate.snapshot.publication_id:
            return None
        old_config = data["previous"].config.version_id if data["previous"] else None
        endpoint = (
            request is not None and old_config is not None and old_config != config.version_id
        )
        version = selected["SelectionVersion"] if selected else 0
        action_id = str(
            uuid5(
                NAMESPACE_URL,
                canonical(
                    (
                        candidate.snapshot.publication_id,
                        version,
                        (data["routing"] or {}).get("RoutingVersion", 0),
                        str(request["RequestID"]) if request else None,
                    )
                ),
            )
        )
        destinations = tuple(
            (t.destination.kind, t.destination.destination_id)
            for t in self.targets
            if t.kvk_no == season
        )
        action = self.publisher.select_publication(
            candidate,
            action_id=action_id,
            expected_selection_version=version,
            expected_routing_version=(data["routing"] or {}).get("RoutingVersion", 0),
            actor=request["Actor"] if request else "system:kvk_source_recovery",
            reason=request["Reason"] if request else "Recover accepted source inputs",
            action_type="endpoint_update" if endpoint else "publish",
            request_id=str(request["RequestID"]) if request else None,
            destinations=destinations,
        )
        from kvk.services.new_source_export_service import ExportSelection

        return ExportSelection(
            season, period, candidate.snapshot.publication_id, action["NewSelectionVersion"]
        )

    def run_batch(self, stop, limit=8):
        periods = self.dal.periods(self.after, limit)
        if not periods:
            self.after = (0, "")
            return
        for season, period in periods:
            if stop.is_set():
                break
            changed = None
            try:
                changed = self.recover_period(season, period)
            except Exception as exc:
                logger.warning(
                    "Source recovery pending kvk=%s period=%s error=%s",
                    season,
                    period,
                    type(exc).__name__,
                )
            if self.delivery_repository is not None and not stop.is_set():
                try:
                    deliver_current_exports(
                        self.dal, self.delivery_repository, self.targets, season, changed=changed
                    )
                except Exception as exc:
                    logger.warning(
                        "Source export recovery pending kvk=%s error=%s", season, type(exc).__name__
                    )
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


def configured_recovery():
    import bot_config
    from constants import ALL_KVK_SHEET_ID, CREDENTIALS_FILE, KVK_SHEET_ID
    from kvk.dal.new_source_admin_dal import configured_connection
    from kvk.dal.new_source_delivery_dal import DeliveryRepository, Destination
    from kvk.dal.new_source_recovery_dal import RecoveryDAL
    from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration
    from kvk.services.new_source_publication_service import PublicationService

    def connect():
        connection = configured_connection()
        connection.timeout = 30
        return connection

    dal = RecoveryDAL(connect)
    dal.check_schema()
    repository = DeliveryRepository(connect)
    registrations = json.loads(bot_config.KVK_SOURCE_EXPORT_REGISTRATIONS)
    if not isinstance(registrations, list) or len(registrations) > 8:
        raise ValueError("At most eight explicit export registrations are supported.")
    targets = []
    for record in registrations:
        from google.oauth2.service_account import Credentials

        season = record["kvk_no"]
        if type(season) is not int or not 1 <= season <= 2147483647:
            raise ValueError("Explicit export KVK is required.")
        registration = SheetsRegistration(
            record["index_file_id"],
            tuple(record["slot_file_ids"]),
            record["owner_email"],
            record["service_account_email"],
            record.get("audience", "private"),
        )
        destination = Destination("sheets", registration.index_file_id)
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/spreadsheets",
            ],
        )
        transport = GoogleSheetsTransport.from_credentials(
            credentials=credentials,
            registration=registration,
            reuse_guard=repository.slot_reusable,
            protected_file_ids=tuple(x for x in (KVK_SHEET_ID, ALL_KVK_SHEET_ID) if x),
        )
        targets.append(ExportTarget(season, destination, transport))
    if len({t.destination for t in targets}) != len(targets):
        raise ValueError("Each source export destination must be registered once.")
    return RecoveryService(dal, PublicationService(connect), repository, tuple(targets))


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
