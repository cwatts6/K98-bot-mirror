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
    from services.legacy_export_snapshot_service import caller_runtime
    from services.stats_import_outcome_service import outcome_dal

    with caller_runtime() as runtime:
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
        adapter = ImportRecoveryAdapter(outcome_dal(runtime))
        adapters = {adapter.kind: adapter}
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
        return getattr(service, method)(*args)


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
                        service.store.observe(kind, source_id, evidence, token, resolved=resolved)
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
            try:
                service.refresh(incident["IncidentID"])
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
