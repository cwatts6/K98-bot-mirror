"""Pure exact-slot selection from explicitly accepted and mapped player events."""

from kvk.models.new_source_reporting import (
    EndpointChange,
    ObservationInput,
    PeriodKind,
    StreamState,
    WindowConfig,
    WindowInputSelection,
)
from kvk.schemas.new_source_schema import PLAYER_SCHEMA_VERSION, SourceKind


def _validate_event(config: WindowConfig, event: ObservationInput) -> None:
    meta = event.observation.metadata.candidate
    if (meta.source_key, meta.kvk_no, meta.kind) != (
        config.source_key,
        config.kvk_no,
        SourceKind.PLAYERS,
    ) or event.observation.schema_version != PLAYER_SCHEMA_VERSION:
        raise ValueError("Player observation source/season/schema mismatch.")


def _validate_change(
    config: WindowConfig,
    previous: WindowInputSelection,
    change: EndpointChange | None,
    events: dict[int, ObservationInput],
) -> None:
    old = previous.config
    # An endpoint-only request cannot grant map, weights, roster, start or source corrections.
    components = (
        "source_key",
        "kvk_no",
        "period_id",
        "period_key",
        "period_kind",
        "label",
        "start_scan_id",
        "roster_id",
        "b0_revision_id",
        "map_version_id",
        "mapping",
        "weights",
        "closes_at_utc",
    )
    if any(getattr(config, key) != getattr(old, key) for key in components):
        raise ValueError("Non-endpoint changes require separate reviewed configuration authority.")
    if config != old:
        if config.version_id == old.version_id or change is None:
            raise ValueError(
                "Endpoint updates require a new config and authorized import provenance."
            )
        if not all((change.request_id, change.actor, change.reason)) or (
            change.period_id,
            change.base_config_id,
            change.desired_config_id,
            change.old_end_scan_id,
            change.new_end_scan_id,
        ) != (
            config.period_id,
            old.version_id,
            config.version_id,
            old.end_scan_id,
            config.end_scan_id,
        ):
            raise ValueError("Endpoint request does not match this exact configuration transition.")
        if config.end_scan_id == old.end_scan_id:
            raise ValueError("No endpoint transition was requested.")
    elif change is not None and change != previous.endpoint_change:
        raise ValueError("Unexpected endpoint request.")
    for pinned in (previous.start, previous.end):
        if pinned is not None and pinned.logical_scan_id in events:
            if events[pinned.logical_scan_id] != pinned:
                raise ValueError("Endpoint authority does not permit source-content corrections.")


def resolve_window(
    config: WindowConfig,
    observations: tuple[ObservationInput, ...],
    *,
    previous: WindowInputSelection | None = None,
    endpoint_change: EndpointChange | None = None,
) -> WindowInputSelection:
    """Resolve exact final or ordinary interim; never allocate IDs or mutate selections.

    Caller supplies one accepted revision per logical scan in this configuration's binding
    snapshot. Tied latest events reject for explicit selection; numeric IDs cannot break ties.
    S3B owns durable request authorization, immutability and CAS at the write boundary.
    """
    if not isinstance(observations, tuple):
        raise ValueError("Observation bindings must be immutable.")
    events = {}
    identities = set()
    revisions = set()
    for event in observations:
        _validate_event(config, event)
        if (
            event.logical_scan_id in events
            or event.observation_id in identities
            or event.revision_id in revisions
        ):
            raise ValueError("Duplicate/conflicting logical observation binding.")
        events[event.logical_scan_id] = event
        identities.add(event.observation_id)
        revisions.add(event.revision_id)
    if previous is not None:
        _validate_change(config, previous, endpoint_change, events)
    elif endpoint_change is not None:
        raise ValueError("Endpoint transition requires its prior selection.")
    change = endpoint_change or (previous.endpoint_change if previous else None)
    start = events.get(config.start_scan_id)
    final = events.get(config.end_scan_id)
    if config.start_scan_id is None:
        return WindowInputSelection(
            config, None, None, StreamState.MISSING_CONFIGURATION, True, change
        )
    if start is None:
        return WindowInputSelection(config, None, None, StreamState.MISSING_START, True, change)
    if config.period_key not in start.period_keys:
        raise ValueError("Exact start is not mapped to this period.")
    if config.closes_at_utc is not None and start.scan_start_utc > config.closes_at_utc:
        raise ValueError("Start event is after the configured close.")
    if config.period_kind == PeriodKind.NO_FIGHT:
        if config.end_scan_id != config.start_scan_id:
            raise ValueError("No-fight requires equal exact endpoints.")
        return WindowInputSelection(config, start, start, StreamState.NOT_APPLICABLE, False, change)
    if final is not None:
        if (
            config.period_key not in final.period_keys
            or final.scan_start_utc <= start.scan_start_utc
            or (config.closes_at_utc is not None and final.scan_start_utc > config.closes_at_utc)
        ):
            raise ValueError("Exact final event is outside the mapped temporal window.")
        state = StreamState.CORRECTED_FINAL if change is not None else StreamState.FINAL
        return WindowInputSelection(config, start, final, state, False, change)
    candidates = [
        event
        for event in observations
        if config.period_key in event.period_keys
        and event.scan_start_utc > start.scan_start_utc
        and (config.closes_at_utc is None or event.scan_start_utc <= config.closes_at_utc)
    ]
    if not candidates:
        return WindowInputSelection(config, start, None, StreamState.MISSING_END, True, change)
    latest_time = max(event.scan_start_utc for event in candidates)
    latest = [event for event in candidates if event.scan_start_utc == latest_time]
    if len(latest) != 1:
        raise ValueError("Latest event time is ambiguous; explicit event selection is required.")
    return WindowInputSelection(config, start, latest[0], StreamState.LIVE, True, change)
