"""Endpoint-only policy for the authorized source configuration import boundary."""

from kvk.dal.new_source_config_dal import snapshot_endpoint_request
from kvk.models.new_source_reporting import PeriodKind


def validate_endpoint_order(config):
    start, end = config.start_scan_id, config.end_scan_id
    if start is None or end is None:
        return
    if config.period_kind == PeriodKind.NO_FIGHT:
        if start != end:
            raise ValueError("No-fight configuration requires identical endpoints.")
    elif end < start:
        raise ValueError("EndScanID must be greater than or equal to StartScanID.")


def request_endpoint_update(cursor, *, authorized: bool, **request):
    """Caller must establish authorization; this adapter never owns its transaction."""
    if authorized is not True:
        raise PermissionError("Authorized configuration import is required.")
    return snapshot_endpoint_request(cursor, **request)


def confirm_endpoint_pair(
    service, context, *, authorized, player=None, aggregate=None, counterpart_revision_id=None
):
    """Bind separately supplied pair attestation to existing endpoint authority.

    The unattended config importer never calls this or manufactures confirmation.
    A pending exact slot may be recorded in context.confirmation_json.pending_player;
    arrival resumes using the durable SourceConfigRequest without another command.
    """
    if authorized is not True or context.request_id is None:
        raise PermissionError("Confirmed endpoint request and pair authority are required.")
    update = service.create(context, authorized=True)
    if player is not None or aggregate is not None:
        return service.associate(
            update["UpdateID"],
            expected_version=update["Version"],
            player=player,
            aggregate=aggregate,
            counterpart_revision_id=counterpart_revision_id,
            authorized=True,
        )
    return update
