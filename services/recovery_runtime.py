"""Composition and bounded independent discovery for the recovery centre."""

from contextlib import contextmanager
import logging

from kvk.dal.new_source_import_dal import SourceConflict
from services.import_recovery_service import ImportRecoveryAdapter
from services.recovery_dal import RecoveryDAL
from services.recovery_service import RecoveryService
from services.stats_import_outcome_dal import ImportExecutionActive

logger = logging.getLogger(__name__)
_cursors = {}
_incident_cursor = None


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
        if getattr(runtime, "recovery_only", False):
            from services.export_evidence_recovery import EvidenceRecoveryAdapter

            adapter = EvidenceRecoveryAdapter(runtime.recovery_client)
            yield RecoveryService(
                store,
                {adapter.kind: adapter},
                admin_id=bot_config.ADMIN_USER_ID,
                guild_id=bot_config.GUILD_ID,
                channel_id=bot_config.NOTIFY_CHANNEL_ID,
            )
            return
        outcomes = outcome_dal(runtime)
        adapter = ImportRecoveryAdapter(outcomes, ImportCaptureRecovery(runtime, outcomes))
        adapters = {adapter.kind: adapter}
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
            )
            adapters[read_adapter.kind] = read_adapter
        yield RecoveryService(
            store,
            adapters,
            admin_id=bot_config.ADMIN_USER_ID,
            guild_id=bot_config.GUILD_ID,
            channel_id=bot_config.NOTIFY_CHANNEL_ID,
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
        logger.warning("recovery_admission_unavailable error_type=%s", type(exc).__name__)
        return False


def observe_recovery():
    global _incident_cursor
    failures = []
    with recovery_service() as service:
        scope = service.store.scope
        for kind, adapter in service.adapters.items():
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
                    except ImportExecutionActive:
                        # An active execution lock is not an abandoned writer.
                        continue
                    except Exception as exc:
                        failures.append(type(exc).__name__)
            except Exception as exc:
                failures.append(type(exc).__name__)
        after = _incident_cursor[1] if _incident_cursor and _incident_cursor[0] == scope else None
        incidents = service.store.list_open(after=after)
        if not incidents:
            _incident_cursor = None
        for incident in incidents:
            _incident_cursor = (scope, incident["IncidentID"])
            if incident["SourceKind"] not in service.adapters:
                # Evidence repair remains available while other domain adapters
                # await authenticated registration. Do not mutate their history.
                continue
            try:
                service.recover_automatic(incident["IncidentID"])
            except Exception as exc:
                service.store.check_failed(incident["IncidentID"], type(exc).__name__)
                failures.append(type(exc).__name__)
                logger.warning(
                    "recovery_recheck_unavailable incident=%s error_type=%s",
                    incident["IncidentID"],
                    type(exc).__name__,
                )
        if service.store.has_failed_checks():
            failures.append("PersistedCheckUnavailable")
    if not _retry_admission():
        failures.append("RegistrationUnavailable")
    return failures


def alert_rows():
    with recovery_service() as service:
        return [service.present(service.store.get(key)) for key in service.store.alerts_due()]


def record_alert(incident_id, revision, channel_id, message_id):
    with recovery_service() as service:
        service.store.alert_sent(incident_id, revision, channel_id, message_id)


def claim_alert(incident_id):
    with recovery_service() as service:
        return service.store.claim_alert(incident_id)
