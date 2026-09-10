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
