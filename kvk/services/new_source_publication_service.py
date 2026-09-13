"""Pure S3A calculation reused behind durable, explicit publication policy."""

from dataclasses import dataclass, replace
from uuid import NAMESPACE_URL, uuid5

from kvk.dal.new_source_import_dal import canonical
from kvk.dal.new_source_publication_dal import PublicationDAL, validate_snapshot_inputs
from kvk.models.new_source_reporting import TERMINAL_STATES, ReportSnapshotV2, StreamState
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_config_service import validate_endpoint_order
from kvk.services.new_source_window_resolver import resolve_window


@dataclass(frozen=True, slots=True)
class Candidate:
    snapshot: ReportSnapshotV2
    b0: object
    generation: int
    update_id: str | None = None
    update_version: int | None = None


class PublicationService:
    def __init__(self, connect):
        self.dal = PublicationDAL(connect)

    def build_candidate(
        self,
        *,
        config,
        observations,
        b0,
        aggregate=None,
        previous=None,
        endpoint_change=None,
        publication_id=None,
        sealed_update=None,
    ):
        validate_endpoint_order(config)
        if config.is_no_fight and aggregate is not None:
            raise ValueError("No-fight publications cannot include aggregate reports.")
        selection = resolve_window(
            config, observations, previous=previous, endpoint_change=endpoint_change
        )
        if (
            selection.start
            and selection.end
            and not config.is_no_fight
            and selection.end.logical_scan_id <= selection.start.logical_scan_id
        ):
            raise ValueError("Selected combat scan ID must increase with UTC.")
        calculation = calculate_period(selection, b0)
        aggregate_state = (
            StreamState(aggregate.report.metadata.candidate.report_state.value)
            if aggregate
            else (StreamState.NOT_APPLICABLE if config.is_no_fight else StreamState.NOT_RECEIVED)
        )
        period_state = StreamState.LIVE
        if selection.player_state in TERMINAL_STATES and aggregate_state in TERMINAL_STATES:
            period_state = (
                StreamState.CORRECTED_FINAL
                if StreamState.CORRECTED_FINAL in (selection.player_state, aggregate_state)
                else StreamState.FINAL
            )
        identity = canonical(
            {
                "source": config.source_key,
                "season": config.kvk_no,
                "period": config.period_id,
                "config": config.version_id,
                "start": selection.start.revision_id if selection.start else None,
                "end": selection.end.revision_id if selection.end else None,
                "aggregate": aggregate.revision_id if aggregate else None,
                "player_state": selection.player_state.value,
                "aggregate_state": aggregate_state.value,
                "calculation": calculation.calculation_version,
            }
        )
        snapshot = ReportSnapshotV2(
            publication_id or str(uuid5(NAMESPACE_URL, identity)),
            1,
            1,
            config,
            calculation,
            aggregate,
            selection.player_state,
            aggregate_state,
            period_state,
        )

        def validate(cursor):
            if sealed_update is None:
                return validate_snapshot_inputs(cursor, snapshot, b0)
            from kvk.dal.source_update_dal import validate_sealed_snapshot

            return validate_sealed_snapshot(
                cursor, snapshot, b0, sealed_update["UpdateID"], sealed_update["Version"]
            )

        stored = self.dal.build_candidate(snapshot, validate_inputs=validate)
        return Candidate(
            replace(snapshot, generation=stored["Generation"]),
            b0,
            stored["Generation"],
            sealed_update["UpdateID"] if sealed_update else None,
            sealed_update["Version"] if sealed_update else None,
        )

    def select_publication(self, candidate, **action):
        config = candidate.snapshot.calculation.selection.config

        def validate(cursor):
            if candidate.update_id:
                from kvk.dal.source_update_dal import validate_sealed_snapshot

                return validate_sealed_snapshot(
                    cursor,
                    candidate.snapshot,
                    candidate.b0,
                    candidate.update_id,
                    candidate.update_version,
                )
            return validate_snapshot_inputs(
                cursor,
                candidate.snapshot,
                candidate.b0,
                require_selected=action.get("action_type") != "rollback",
            )

        return self.dal.select_publication(
            kvk_no=config.kvk_no,
            period_id=config.period_id,
            publication_id=candidate.snapshot.publication_id,
            update_id=candidate.update_id,
            expected_update_version=candidate.update_version,
            validate_inputs=validate,
            **action,
        )
