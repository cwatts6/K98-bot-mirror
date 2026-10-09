"""Admin resolution orchestration, independent of Discord objects."""

from services.export_coordination_dal import identity


def operate_import_resolution(preparation_id, action, confirmation, reason, accept_partial, actor):
    from services.legacy_export_snapshot_service import caller_runtime
    from services.stats_import_outcome_service import event, outcome_dal

    identifier = identity(preparation_id)
    with caller_runtime() as runtime:
        if runtime is None:
            return "S11 runtime is unavailable. Check protected runtime readiness; no import or resource changes were made."
        dal = outcome_dal(runtime)
        if action == "resolve":
            result = dal.settle(
                identifier,
                token=confirmation,
                actor=actor,
                reason=reason,
                allow_partial=accept_partial,
            )
            event(
                identifier,
                "admin_resolution",
                "resolved",
                action="correct the root cause before a fresh upload",
                resolution=result,
                actor=actor,
                import_replayed=False,
            )
            return f"Preparation {identifier}: {result}. Input and committed data retained. No import/export was replayed. Correct the original source/configuration error before submitting a fresh upload."
        preview = dal.inspect(identifier)
        p, e = preview["preparation"] or {}, preview["execution"] or {}
        text = (
            f"Preparation: {identifier}\nPreparation state: {p.get('State', 'missing')}\n"
            f"SQL outcome: {e.get('State', 'no exact receipt')}\n"
            f"Committed scan: {e.get('ScanOrder') or 'none proven'}\n"
            f"SQL error: {e.get('ErrorNumber')} / {e.get('ErrorProcedure')} / line {e.get('ErrorLine')}\n"
        )
        decision = preview["action"]
        if decision == "hold":
            return text + "Action required: " + preview["explanation"]
        if decision == "resolved":
            return text + f"Already resolved: {e.get('Resolution')}. No further settlement needed."
        if decision == "supersede_partial":
            text += "Imported data is committed; later reporting failed. Resolution releases only the preparation so a fresh corrected upload can replace unfinished reports. It does not complete those reports or repeat the import. Explicit accept_partial:true is required.\n"
        else:
            text += "No business import commit is recorded by this exact execution. Resolution releases only the failed preparation after rechecking that SQL and its producer have ended. Correct the original error before a fresh upload.\n"
        if action == "preview":
            text += f"Confirm with /ops import_resolution action:resolve preparation_id:{identifier} confirmation:{preview['token']} reason:<your reason>"
            if decision == "supersede_partial":
                text += " accept_partial:true"
        else:
            text += "Next: /ops import_resolution action:preview with this preparation_id."
        return text
