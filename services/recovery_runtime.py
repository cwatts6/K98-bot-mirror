"""Composition and bounded independent discovery for the recovery centre."""

from contextlib import contextmanager
from datetime import UTC, datetime
import logging
import time

from core.sql_observation import ObservationBusy, observe_call
from kvk.dal.new_source_import_dal import SourceBusy, SourceConflict
from services import recovery_health
from services.import_recovery_service import ImportRecoveryAdapter
from services.recovery_dal import RecoveryDAL
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService

logger = logging.getLogger(__name__)
_cursors = {}
_incident_cursor = None
_priority_incident_cursor = None
_failed_incident_cursor = None
HISTORY_SLICE_SECONDS = 10.0
_history_coverage = {}


def _inspect_discovered(service, adapter, source_id):
    from services.recovery_execution_guard import operation_key, recovery_execution

    with recovery_execution(
        source_id, operation=operation_key(service.store.scope, source_id)
    ) as acquired:
        if not acquired:
            raise SourceBusy("The original recovery operation is active; waiting for its receipt.")
        return observe_call(adapter.inspect, source_id)


@contextmanager
def recovery_service():
    import bot_config
    from services.export_runtime_composition import recovery_caller_scope
    from services.import_capture_recovery_service import ImportCaptureRecovery
    from services.stats_import_outcome_service import outcome_dal

    with recovery_caller_scope() as runtime:
        if runtime is None:
            raise SourceConflict(
                "Recovery checks are unavailable. Your incident remains open; use Recheck after service connectivity returns."
            )
        store = RecoveryDAL(
            runtime.dal.connect,
            account=runtime.account,
            storage_owner=runtime.store.storage_owner,
            guild_id=bot_config.GUILD_ID,
        )
        from constants import DATA_DIR
        from services.configuration_attempt_recovery import (
            AttemptJournal,
            ConfigurationAttemptRecovery,
            journal_root,
        )
        from services.recovery_backlog_service import EvidenceBatchAdapter

        attempts = ConfigurationAttemptRecovery(AttemptJournal(journal_root(DATA_DIR, runtime)))
        batch = EvidenceBatchAdapter(store)
        if getattr(runtime, "recovery_only", False):
            from services.export_evidence_recovery import EvidenceRecoveryAdapter

            adapter = EvidenceRecoveryAdapter(runtime.recovery_client)
            yield RecoveryService(
                store,
                {adapter.kind: adapter, batch.kind: batch, attempts.kind: attempts},
                admin_id=bot_config.ADMIN_USER_ID,
                guild_id=bot_config.GUILD_ID,
                channel_id=bot_config.NOTIFY_CHANNEL_ID,
                presentation_policy=p0a_presentation,
            )
            return
        outcomes = outcome_dal(runtime)
        adapter = ImportRecoveryAdapter(outcomes, ImportCaptureRecovery(runtime, outcomes))
        adapters = {adapter.kind: adapter, batch.kind: batch, attempts.kind: attempts}
        from services.unowned_sql_hold_dal import UnownedSqlHoldDAL
        from services.unowned_sql_hold_recovery import UnownedSqlHoldRecovery

        unowned = UnownedSqlHoldRecovery(UnownedSqlHoldDAL(runtime))
        adapters[unowned.kind] = unowned
        from services.stats_report_continuation import StatsReportContinuation
        from services.stats_report_continuation_dal import StatsReportContinuationDAL

        stats_reports = StatsReportContinuation(StatsReportContinuationDAL(outcomes))
        adapters[stats_reports.kind] = stats_reports
        from services.processing_pipeline_receipt_dal import PipelineReceiptDAL
        from services.processing_pipeline_recovery import ProcessingPipelineRecovery

        pipeline = ProcessingPipelineRecovery(PipelineReceiptDAL(runtime))
        adapters[pipeline.kind] = pipeline
        from services.historical_retirement_group_service import HistoricalBatchAdapter

        historical_batch = HistoricalBatchAdapter(store)
        adapters[historical_batch.kind] = historical_batch
        from services.queue_admission_recovery import QueueAdmissionRecovery
        from services.queue_admission_recovery_dal import QueueAdmissionDAL

        queued = QueueAdmissionRecovery(QueueAdmissionDAL(runtime), adapters)
        adapters[queued.kind] = queued
        from services.producer_refusal_dal import ProducerRefusalDAL
        from services.producer_refusal_recovery import ProducerRefusalRecovery

        refused = ProducerRefusalRecovery(ProducerRefusalDAL(runtime), adapter)
        adapters[refused.kind] = refused
        from services.all_kvk_capture_recovery_dal import AllKvkCaptureRecoveryDAL
        from services.all_kvk_capture_recovery_service import (
            AllKvkCaptureRecovery,
            AllKvkCaptureRecoveryAdapter,
        )

        kvk_outcomes = AllKvkCaptureRecoveryDAL(
            runtime.dal.connect,
            account=runtime.account,
            storage_owner=runtime.store.storage_owner,
        )
        kvk_adapter = AllKvkCaptureRecoveryAdapter(
            kvk_outcomes, AllKvkCaptureRecovery(runtime, kvk_outcomes)
        )
        adapters[kvk_adapter.kind] = kvk_adapter
        from services.player_report_recovery_dal import PlayerReportRecoveryDAL
        from services.player_report_recovery_service import (
            PlayerReportCaptureRecovery,
            PlayerReportRecoveryAdapter,
        )

        report_outcomes = PlayerReportRecoveryDAL(
            runtime.dal.connect, account=runtime.account, storage_owner=runtime.store.storage_owner
        )
        report_adapter = PlayerReportRecoveryAdapter(
            report_outcomes, PlayerReportCaptureRecovery(runtime, report_outcomes)
        )
        adapters[report_adapter.kind] = report_adapter
        from services.player_report_continuation import PlayerReportContinuation
        from services.player_report_continuation_dal import PlayerReportContinuationDAL

        report_continuation = PlayerReportContinuation(
            PlayerReportContinuationDAL(runtime, report_outcomes), report_adapter
        )
        adapters[report_continuation.kind] = report_continuation
        from services.configuration_producer_recovery import (
            ConfigurationProducerCapture,
            ConfigurationProducerDAL,
            ConfigurationProducerRecovery,
        )

        config_outcomes = ConfigurationProducerDAL(
            runtime.dal.connect, account=runtime.account, storage_owner=runtime.store.storage_owner
        )
        config_adapter = ConfigurationProducerRecovery(
            config_outcomes, ConfigurationProducerCapture(runtime, config_outcomes)
        )
        adapters[config_adapter.kind] = config_adapter
        from services.pipeline_capture_handoff_dal import PipelineCaptureHandoffDAL

        handoff = PipelineCaptureHandoffDAL(runtime)
        for producer_adapter in (adapter, report_adapter, config_adapter):
            producer_adapter.capture_recovery.pipeline_handoff = handoff
        from services.legacy_configuration_continuation import (
            LegacyConfigurationContinuation,
            LegacyConfigurationContinuationDAL,
        )
        from services.unreceipted_producer_recovery import (
            UnreceiptedProducerDAL,
            UnreceiptedProducerRecovery,
        )

        unknown = UnreceiptedProducerRecovery(
            UnreceiptedProducerDAL(
                runtime.dal.connect,
                account=runtime.account,
                storage_owner=runtime.store.storage_owner,
            ),
            configuration=runtime.configuration,
        )
        adapters[unknown.kind] = unknown
        legacy_config = LegacyConfigurationContinuation(
            LegacyConfigurationContinuationDAL(runtime, config_outcomes), config_adapter
        )
        adapters[legacy_config.kind] = legacy_config
        from services.configuration_continuation import ConfigurationContinuation
        from services.configuration_continuation_dal import ConfigurationContinuationDAL

        config_continuation = ConfigurationContinuation(
            ConfigurationContinuationDAL(runtime, config_outcomes), config_adapter
        )
        adapters[config_continuation.kind] = config_continuation
        from services.configuration_read_continuation import ConfigurationReadContinuation
        from services.configuration_read_continuation_dal import ConfigurationReadContinuationDAL

        read_continuation = ConfigurationReadContinuation(
            ConfigurationReadContinuationDAL(runtime, config_outcomes), config_adapter
        )
        adapters[read_continuation.kind] = read_continuation
        from services.configuration_attempt_recovery import attempt_resolver

        attempts.resolver = attempt_resolver(runtime, adapters)
        for export_adapter in getattr(runtime, "recovery_adapters", ()):
            adapters[export_adapter.kind] = export_adapter
        if runtime.recovery_client is not None:
            from services.config_preparation_recovery_dal import ConfigPreparationRecoveryDAL
            from services.config_read_recovery_adapter import ConfigReadRecoveryAdapter

            read_adapter = ConfigReadRecoveryAdapter(
                ConfigPreparationRecoveryDAL(runtime.dal.connect),
                runtime.recovery_client,
                account=runtime.account,
                storage_owner=runtime.store.storage_owner,
                queue_dal=queued.dal,
                continuation=read_continuation,
            )
            adapters[read_adapter.kind] = read_adapter
        yield RecoveryService(
            store,
            adapters,
            admin_id=bot_config.ADMIN_USER_ID,
            guild_id=bot_config.GUILD_ID,
            channel_id=bot_config.NOTIFY_CHANNEL_ID,
            presentation_policy=p0a_presentation,
        )


def call_recovery(method, *args):
    with recovery_service() as service:
        result = getattr(service, method)(*args)
    if method in {"execute", "execute_input"}:
        _retry_admission()
    return result


def _retry_admission():
    from services.export_runtime_composition import retry_recovery_admission

    try:
        retry_recovery_admission()
        return True
    except (SourceBusy, ObservationBusy) as exc:
        recovery_health.record_check("registration_admission", exc, waiting=True)
        return True
    except Exception as exc:
        recovery_health.record_check("registration_admission", exc)
        logger.warning("recovery_admission_unavailable error_type=%s", type(exc).__name__)
        return False


def observe_recovery():
    global _incident_cursor, _priority_incident_cursor, _failed_incident_cursor
    failures = []
    visited = set()
    visited_sources = set()
    recovery_health.record_progress("opening_recovery_scope")
    with recovery_service() as service:
        from services.recovery_backlog_dal import RecoveryBacklogDAL

        # Durable accepted copy repairs must not wait behind thousands of
        # untouched incidents. Domain reconciliation retains exact hash checks.
        if "private_evidence" in service.adapters:
            recovery_health.record_progress("accepted_evidence_repairs")
            for incident_id in RecoveryBacklogDAL(service.store).pending_repairs():
                try:
                    visited.add(incident_id)
                    row = service.refresh(incident_id)
                    if isinstance(row, dict) and row.get("SourceID") is not None:
                        visited_sources.add((row["SourceKind"], str(row["SourceID"])))
                except (SourceBusy, ObservationBusy) as exc:
                    recovery_health.record_check("accepted_repairs", exc, waiting=True)
                except Exception as exc:
                    detail = recovery_health.record_check("accepted_repairs", exc)
                    service.store.check_failed(incident_id, detail)
                    failures.append(type(exc).__name__)
                finally:
                    service.store.touch_pending(incident_id)
                    recovery_health.record_progress("accepted_evidence_repairs")
        scope = service.store.scope
        if "historical_batch" in service.adapters:
            recovery_health.record_progress("accepted_historical_retirements")
            for incident_id in RecoveryBacklogDAL(service.store).pending_repairs("stats_import"):
                try:
                    visited.add(incident_id)
                    row = service.refresh(incident_id)
                    if isinstance(row, dict) and row.get("SourceID") is not None:
                        visited_sources.add((row["SourceKind"], str(row["SourceID"])))
                except (SourceBusy, ObservationBusy) as exc:
                    recovery_health.record_check("accepted_repairs", exc, waiting=True)
                except Exception as exc:
                    detail = recovery_health.record_check("accepted_repairs", exc)
                    service.store.check_failed(incident_id, detail)
                    failures.append(type(exc).__name__)
                finally:
                    service.store.touch_pending(incident_id)
                    recovery_health.record_progress("accepted_historical_retirements")
        # Existing operational incidents must still be checked after their source
        # leaves discovery (for example a domain closes a queued preparation).
        # A separate bounded cursor prevents evidence-copy backlogs delaying them.
        priority_after = (
            _priority_incident_cursor[1]
            if _priority_incident_cursor and _priority_incident_cursor[0] == scope
            else None
        )
        recovery_health.record_progress("existing_incident_checks")
        priority = service.store.list_open(after=priority_after, non_evidence=True)
        _priority_incident_cursor = (scope, priority[-1]["IncidentID"]) if priority else None
        after = _incident_cursor[1] if _incident_cursor and _incident_cursor[0] == scope else None
        incidents = service.store.list_open(after=after)
        _incident_cursor = (scope, incidents[-1]["IncidentID"]) if incidents else None
        # A failed check must not disappear behind the rotating backlog while
        # its persisted failure keeps monitoring unhealthy. Recheck a bounded
        # page first; only an actual successful observation clears its failure.
        failed_after = (
            _failed_incident_cursor[1]
            if _failed_incident_cursor and _failed_incident_cursor[0] == scope
            else None
        )
        failed_checks = service.store.list_open(after=failed_after, failed_checks_only=True)
        _failed_incident_cursor = (
            (scope, failed_checks[-1]["IncidentID"]) if failed_checks else None
        )
        for incident in failed_checks + priority + incidents:
            if incident["IncidentID"] in visited:
                continue
            visited.add(incident["IncidentID"])
            if incident.get("SourceID") is not None:
                visited_sources.add((incident["SourceKind"], str(incident["SourceID"])))
            if incident["SourceKind"] not in service.adapters:
                # Evidence repair remains available while other domain adapters
                # await authenticated registration. Do not mutate their history.
                continue
            try:
                service.recover_automatic(incident["IncidentID"])
            except (SourceBusy, ObservationBusy) as exc:
                recovery_health.record_check(
                    "existing_incident_checks:" + incident["SourceKind"], exc, waiting=True
                )
            except Exception as exc:
                detail = recovery_health.record_check(
                    "existing_incident_checks:" + incident["SourceKind"], exc
                )
                service.store.check_failed(incident["IncidentID"], detail)
                failures.append(type(exc).__name__)
                logger.warning(
                    "recovery_recheck_unavailable incident=%s diagnostic=%s",
                    incident["IncidentID"],
                    detail,
                )
            finally:
                recovery_health.record_progress("existing_incident_checks")
        for kind, adapter in sorted(
            service.adapters.items(), key=lambda item: item[0] == "private_evidence"
        ):
            recovery_health.record_progress("discovery:" + kind)
            history = kind == "private_evidence"
            started = time.monotonic()
            inspected = 0
            exhausted = False
            wrapped = False
            history_failures = 0
            history_waiting = 0
            page_observed = False
            sources = []
            last_history_failure = None
            consumed = 0
            try:
                after = _cursors.get((scope, kind))
                if history and hasattr(adapter, "discovery_page"):
                    page = adapter.discovery_page(after=after)
                    sources, wrapped = page["references"], page["wrapped"]
                else:
                    sources = observe_call(adapter.pending_recovery, after=after)
                page_observed = True
                for source_id in sources:
                    if history and consumed and time.monotonic() - started >= HISTORY_SLICE_SECONDS:
                        exhausted = True
                        break
                    # Advance attempted references so one bad item cannot starve
                    # the catalog. A failure stays unconfirmed until a clean
                    # wrap-to-wrap sweep; another page cannot clear it.
                    _cursors[(scope, kind)] = source_id
                    consumed += 1
                    if (kind, str(source_id)) in visited_sources:
                        # The active path may have deferred to existing work;
                        # deduplication is not proof of a successful hash check.
                        if history:
                            history_waiting += 1
                        continue
                    inspected += 1
                    try:
                        evidence, token, resolved = _inspect_discovered(service, adapter, source_id)
                        recovery_health.record_progress("discovery:" + kind)
                        if resolved and not getattr(adapter, "observe_healthy", True):
                            # Existing open incidents were reconciled above. A
                            # healthy receipt is not a new admin notification.
                            continue
                        row = service.store.observe(
                            kind, source_id, evidence, token, resolved=resolved
                        )
                        if row["IncidentID"] not in visited and getattr(
                            adapter, "automatic_action", None
                        ):
                            visited.add(row["IncidentID"])
                            service.recover_automatic(row["IncidentID"])
                    except (SourceBusy, ObservationBusy) as exc:
                        recovery_health.record_check("discovery:" + kind, exc, waiting=True)
                        history_waiting += 1
                        continue
                    except Exception as exc:
                        last_history_failure = recovery_health.record_check(
                            "discovery:" + kind, exc
                        )
                        failures.append(type(exc).__name__)
                        history_failures += 1
            except (SourceBusy, ObservationBusy) as exc:
                recovery_health.record_check("discovery:" + kind, exc, waiting=True)
                history_waiting += 1
            except Exception as exc:
                last_history_failure = recovery_health.record_check("discovery:" + kind, exc)
                failures.append(type(exc).__name__)
                history_failures += 1
            finally:
                recovery_health.record_progress("discovery_finished:" + kind)
                if history:
                    # Keep only this runtime scope. This is diagnostic coverage,
                    # never authority to skip a receipt or certify a full report.
                    prior = _history_coverage.get(scope, {})
                    now = datetime.now(UTC).isoformat()
                    empty_catalog = page_observed and not sources and after is None
                    coverage = dict(
                        prior,
                        last_slice_utc=now,
                        attempted=inspected,
                        consumed=consumed,
                        elapsed_seconds=time.monotonic() - started,
                        budget_seconds=HISTORY_SLICE_SECONDS,
                        budget_exhausted=exhausted,
                        coverage="rotating_catalog_not_transactional",
                        complete=False,
                        sweep_failures=(
                            0 if wrapped or empty_catalog else prior.get("sweep_failures", 0)
                        )
                        + history_failures,
                        sweep_waiting=(
                            0 if wrapped or empty_catalog else prior.get("sweep_waiting", 0)
                        )
                        + history_waiting,
                        unconfirmed_failure=bool(
                            not empty_catalog
                            and (
                                history_failures
                                or (
                                    prior.get("sweep_failures", 0)
                                    or (
                                        prior.get("sweep_waiting", 0)
                                        and prior.get("unconfirmed_failure", False)
                                    )
                                    if wrapped
                                    else prior.get("unconfirmed_failure", False)
                                )
                            )
                        ),
                    )
                    if not prior or after is None or wrapped:
                        coverage["sweep_started_utc"] = now
                    coverage["sweep_age_seconds"] = max(
                        0.0,
                        (
                            datetime.now(UTC)
                            - datetime.fromisoformat(coverage["sweep_started_utc"])
                        ).total_seconds(),
                    )
                    if last_history_failure:
                        coverage["last_failure"] = last_history_failure
                    elif not coverage["unconfirmed_failure"]:
                        coverage.pop("last_failure", None)
                    if wrapped:
                        coverage["last_wrap_utc"] = now
                        coverage["wraps"] = prior.get("wraps", 0) + 1
                    _history_coverage.clear()
                    _history_coverage[scope] = coverage
                    recovery_health.record_history(coverage)
                    if coverage["unconfirmed_failure"]:
                        failures.append("HistoricalChecksUnconfirmed")
        if service.store.has_failed_checks():
            failures.append("PersistedCheckUnavailable")
    recovery_health.record_progress("registration_admission")
    if not _retry_admission():
        failures.append("RegistrationUnavailable")
    return failures


def alert_rows():
    from uuid import NAMESPACE_URL, uuid5

    from kvk.dal.new_source_import_dal import digest
    from kvk.dal.source_output_pool_dal import _wire
    from services.recovery_backlog_dal import RecoveryBacklogDAL

    with recovery_service() as service:
        summary = RecoveryBacklogDAL(service.store).active_summary()
        open_count, copies, pending = summary["open_count"], summary["copies"], summary["pending"]
        evidence = dict(
            title="Recovery overview",
            actions={},
            outcome="attention_required" if open_count or pending else "clear",
            summary_sha256=digest(_wire(summary)).hex(),
            explanation=(
                f"{open_count} open recovery records, including {copies} evidence-copy incidents. "
                f"{pending} accepted repairs await verification. Open the recovery centre for blocking work, grouped repairs and a complete report."
            ),
        )
        service.store.observe(
            "recovery_overview",
            str(uuid5(NAMESPACE_URL, service.store.scope + ":overview")),
            evidence,
            digest(evidence).hex(),
            resolved=open_count == 0 and pending == 0,
        )
        return [service.present(service.store.get(key)) for key in service.store.alerts_due()]


def record_alert(incident_id, revision, channel_id, message_id):
    with recovery_service() as service:
        service.store.alert_sent(incident_id, revision, channel_id, message_id)


def claim_alert(incident_id):
    with recovery_service() as service:
        return service.store.claim_alert(incident_id)
