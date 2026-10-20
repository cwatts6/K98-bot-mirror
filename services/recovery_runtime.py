"""Composition and bounded independent discovery for the recovery centre."""

from contextlib import contextmanager
import logging

from kvk.dal.new_source_import_dal import SourceConflict
from services import recovery_health
from services.import_recovery_service import ImportRecoveryAdapter
from services.recovery_dal import RecoveryDAL
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from services.stats_import_outcome_dal import ImportExecutionActive

logger = logging.getLogger(__name__)
_cursors = {}
_incident_cursor = None
_priority_incident_cursor = None


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
        from services.recovery_backlog_service import EvidenceBatchAdapter

        batch = EvidenceBatchAdapter(store)
        if getattr(runtime, "recovery_only", False):
            from services.export_evidence_recovery import EvidenceRecoveryAdapter

            adapter = EvidenceRecoveryAdapter(runtime.recovery_client)
            yield RecoveryService(
                store,
                {adapter.kind: adapter, batch.kind: batch},
                admin_id=bot_config.ADMIN_USER_ID,
                guild_id=bot_config.GUILD_ID,
                channel_id=bot_config.NOTIFY_CHANNEL_ID,
                presentation_policy=p0a_presentation,
            )
            return
        outcomes = outcome_dal(runtime)
        adapter = ImportRecoveryAdapter(outcomes, ImportCaptureRecovery(runtime, outcomes))
        adapters = {adapter.kind: adapter, batch.kind: batch}
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
    except Exception as exc:
        recovery_health.record_check("registration_admission", exc)
        logger.warning("recovery_admission_unavailable error_type=%s", type(exc).__name__)
        return False


def observe_recovery():
    global _incident_cursor, _priority_incident_cursor
    failures = []
    recovery_health.record_progress("opening_recovery_scope")
    with recovery_service() as service:
        from services.recovery_backlog_dal import RecoveryBacklogDAL

        # Durable accepted copy repairs must not wait behind thousands of
        # untouched incidents. Domain reconciliation retains exact hash checks.
        if "private_evidence" in service.adapters:
            recovery_health.record_progress("accepted_evidence_repairs")
            for incident_id in RecoveryBacklogDAL(service.store).pending_repairs():
                try:
                    service.refresh(incident_id)
                except ImportExecutionActive as exc:
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
                    service.refresh(incident_id)
                except ImportExecutionActive as exc:
                    recovery_health.record_check("accepted_repairs", exc, waiting=True)
                except Exception as exc:
                    detail = recovery_health.record_check("accepted_repairs", exc)
                    service.store.check_failed(incident_id, detail)
                    failures.append(type(exc).__name__)
                finally:
                    service.store.touch_pending(incident_id)
                    recovery_health.record_progress("accepted_historical_retirements")
        for kind, adapter in service.adapters.items():
            recovery_health.record_progress("discovery:" + kind)
            try:
                after = _cursors.get((scope, kind))
                for source_id in adapter.pending_recovery(after=after):
                    _cursors[(scope, kind)] = source_id
                    try:
                        evidence, token, resolved = adapter.inspect(source_id)
                        if resolved and not getattr(adapter, "observe_healthy", True):
                            # Existing open incidents are reconciled below. A
                            # healthy receipt is not a new admin notification.
                            continue
                        row = service.store.observe(
                            kind, source_id, evidence, token, resolved=resolved
                        )
                        if getattr(adapter, "automatic_action", None):
                            service.recover_automatic(row["IncidentID"])
                    except ImportExecutionActive as exc:
                        recovery_health.record_check("discovery:" + kind, exc, waiting=True)
                        continue
                    except Exception as exc:
                        recovery_health.record_check("discovery:" + kind, exc)
                        failures.append(type(exc).__name__)
            except ImportExecutionActive as exc:
                recovery_health.record_check("discovery:" + kind, exc, waiting=True)
            except Exception as exc:
                recovery_health.record_check("discovery:" + kind, exc)
                failures.append(type(exc).__name__)
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
        visited = set()
        for incident in priority + incidents:
            if incident["IncidentID"] in visited:
                continue
            visited.add(incident["IncidentID"])
            if incident["SourceKind"] not in service.adapters:
                # Evidence repair remains available while other domain adapters
                # await authenticated registration. Do not mutate their history.
                continue
            try:
                service.recover_automatic(incident["IncidentID"])
            except ImportExecutionActive as exc:
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
                    "recovery_recheck_unavailable incident=%s error_type=%s",
                    incident["IncidentID"],
                    type(exc).__name__,
                )
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
        summary = RecoveryBacklogDAL(service.store).summary()
        open_count = sum(g["Total"] for g in summary["groups"] if g["State"] == "open")
        copies = sum(
            g["Total"]
            for g in summary["groups"]
            if g["State"] == "open" and g["SourceKind"] == "private_evidence"
        )
        pending = sum(
            a["Total"] for a in summary["actions"] if a["State"] in {"dispatched", "unknown"}
        )
        evidence = dict(
            title="Recovery overview",
            actions={},
            outcome="attention_required" if open_count else "clear",
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
            resolved=open_count == 0,
        )
        return [service.present(service.store.get(key)) for key in service.store.alerts_due()]


def record_alert(incident_id, revision, channel_id, message_id):
    with recovery_service() as service:
        service.store.alert_sent(incident_id, revision, channel_id, message_id)


def claim_alert(incident_id):
    with recovery_service() as service:
        return service.store.claim_alert(incident_id)
