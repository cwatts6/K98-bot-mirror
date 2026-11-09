"""Recalculate current player weights atomically; no provider or aggregate mutations."""

from datetime import UTC, datetime
import logging
from uuid import uuid4

from kvk.dal.new_source_admin_dal import _BorrowedConnection
from kvk.dal.new_source_import_dal import SourceConflict, canonical, lock_scope, transaction
from kvk.dal.source_admin_review_dal import SourceAdminReviewDAL
from kvk.dal.source_weight_dal import (
    refresh_requests,
    selected_weights_current,
    stale_weight_periods,
)
from kvk.models.source_configuration import weight_values
from kvk.models.source_integration import AggregateRevision, PlayerRevisions, UpdateContext
from kvk.services.source_update_service import SourceUpdateService

logger = logging.getLogger(__name__)


def refresh_season_weights(connect, season, *, require_current=False):
    now = datetime.now(UTC).replace(microsecond=0)
    with transaction(connect) as cursor:
        lock_scope(cursor, season)
        imported = SourceAdminReviewDAL.imported_configuration(cursor, season)
        pending = refresh_requests(cursor, season, imported, now)
        if stale_weight_periods(cursor, season, weight_values(imported["weights"])) - {
            base["PeriodID"] for base, _ in pending
        }:
            pending = []  # Preserve the entire previous complete vector until all are ready.
        service = SourceUpdateService(lambda: _BorrowedConnection(cursor))
        for index, (base, request) in enumerate(pending):
            config_id = request["DesiredConfigVersionID"]
            actor = "system:current_season_weights"
            proof = dict(
                action="correct",
                reason="Current season player weights; retained source facts",
                current_weights=True,
                automatic_weight_refresh=True,
            )
            proof["period_assignment"] = dict(
                period_id=base["PeriodID"],
                config_version_id=config_id,
                start_scan_id=base["StartScanID"],
                end_scan_id=base["EndScanID"],
                actor=actor,
            )
            counterpart = base["AggregateRevisionID"]
            if counterpart:
                proof["counterpart"] = dict(
                    base_update_id=base["UpdateID"],
                    revision_id=counterpart,
                    config_version_id=config_id,
                    roster_id=base["RosterID"],
                    coverage_start_utc=base["CoverageStartUTC"].isoformat(),
                    coverage_end_utc=base["CoverageEndUTC"].isoformat(),
                    as_of_utc=base["AsOfUTC"].isoformat(),
                    actor=actor,
                )
            context = UpdateContext(
                str(uuid4()),
                season,
                base["PeriodID"],
                base["PeriodKey"],
                base["ChoiceID"],
                config_id,
                base["RosterID"],
                *(
                    base[k].replace(tzinfo=UTC)
                    for k in ("CoverageStartUTC", "CoverageEndUTC", "AsOfUTC")
                ),
                base["UpdateKind"],
                actor,
                now,
                canonical(proof),
                request["RequestID"],
                base["UpdateID"],
            )
            update = service.create(context, authorized=True, admin_authorized=True)
            update = service.associate(
                update["UpdateID"],
                expected_version=update["Version"],
                player=PlayerRevisions(
                    *(
                        base[k]
                        for k in ("StartScanID", "EndScanID", "StartRevisionID", "EndRevisionID")
                    )
                ),
                aggregate=(
                    AggregateRevision(base["AggregateReportID"], counterpart)
                    if counterpart
                    else None
                ),
                counterpart_revision_id=counterpart,
                authorized=True,
            )
            result = service.publish(
                update["UpdateID"], emit_export_intent=index == len(pending) - 1
            )
            if result is None:
                raise SourceConflict("Weight refresh did not select every planned complete update.")
        current = selected_weights_current(cursor, season, weight_values(imported["weights"]))
        if pending and not current:
            raise SourceConflict("Weight refresh did not produce a consistent season selection.")
    if require_current and not current:
        raise SourceConflict(
            "Current-weight export is waiting for a compatible matched update for the revised window."
        )
    if pending:
        logger.info(
            "Season player weights refreshed kvk=%s periods=%s current=%s",
            season,
            len(pending),
            current,
        )
    return current
