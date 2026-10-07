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


def request_configuration_update(cursor, *, authorized, review_id, snapshot, **request):
    """Only a durable, explicitly approved review can extend endpoint-only authority."""
    if authorized is not True:
        raise PermissionError("Explicit configuration review is required.")
    return snapshot_endpoint_request(
        cursor, review_id=review_id, reviewed_configuration=snapshot, **request
    )


def source_weight_tokens(frame):
    """Capture text before the legacy float coercion; never reverse-engineer precision."""
    import bot_config

    if not bot_config.KVK_SOURCE_INTAKE_ENABLED or frame.empty:
        return None
    from decimal import Decimal

    import pandas as pd

    result = {}
    for row in frame.to_dict("records"):
        raw_season = row["KVK_NO"]
        if pd.isna(raw_season) or not str(raw_season).strip():
            continue
        season = int(raw_season)
        tokens = [row[key] for key in ("WeightT4X", "WeightT5Y", "WeightDeadsZ")]
        if (
            season in result
            or not 1 <= season <= 2147483647
            or isinstance(raw_season, bool)
            or Decimal(str(raw_season)) != season
        ):
            raise ValueError("Source weights require one row per integer season.")
        result[season] = tokens
    return result
