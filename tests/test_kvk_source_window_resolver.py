"""T31-T34/T68-T70: exact source slots, event-time interim and endpoint authority."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from kvk.models.new_source_reporting import EndpointChange, PeriodKind, StreamState
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_window_resolver import resolve_window
from tests.kvk_source_fixtures import (
    calculation_config,
    calculation_event,
    worked_calculation_inputs,
)


def request(old, new):
    return EndpointChange(
        "request-14",
        new.period_id,
        old.version_id,
        new.version_id,
        old.end_scan_id,
        new.end_scan_id,
        "synthetic-authorized-import",
        "endpoint update",
    )


def test_t68_interim_11_then_12_selected_by_event_time_not_larger_id():
    b0, start, middle, end = worked_calculation_inputs()
    config = calculation_config()
    first = resolve_window(config, (start, middle))
    assert first.end.logical_scan_id == 11 and first.player_state == StreamState.LIVE
    second_event = replace(end, logical_scan_id=12, observation_id="obs12", revision_id="rev12")
    delayed = calculation_event(220, day=6)
    second = resolve_window(config, (start, middle, second_event, delayed), previous=first)
    assert second.end.logical_scan_id == 12 and second.endpoint_pending
    assert calculate_period(second, b0).players[0].metric("dkp").value == 1800
    assert calculate_period(first, b0).players[0].metric("dkp").value == 1000
    assert (
        resolve_window(replace(config, end_scan_id=None), (start, second_event)).end == second_event
    )


def test_t69_t70_end_change_authority_pending_arrival_and_replay():
    _, start, middle, end = worked_calculation_inputs()
    old = calculation_config()
    final13 = resolve_window(old, (start, middle, end))
    assert final13.player_state == StreamState.FINAL
    desired = replace(old, version_id="config-2", end_scan_id=14)
    change = request(old, desired)
    pending = resolve_window(desired, (start, end), previous=final13, endpoint_change=change)
    assert pending.player_state == StreamState.LIVE and pending.endpoint_pending
    assert pending.end == end and final13.player_state == StreamState.FINAL
    final_event = calculation_event(14, day=8)
    replacement = resolve_window(desired, (start, end, final_event), previous=pending)
    assert replacement.player_state == StreamState.CORRECTED_FINAL
    assert replacement.end == final_event and not replacement.endpoint_pending
    assert resolve_window(desired, (start, end, final_event), previous=replacement) == replacement
    assert final13.config.end_scan_id == 13
    back = replace(old, version_id="config-3")
    returned = resolve_window(
        back,
        (start, end, final_event),
        previous=replacement,
        endpoint_change=request(desired, back),
    )
    assert returned.end == end


@pytest.mark.parametrize(
    "mutation", ["weights", "mapping", "roster", "start", "period", "close", "source_content"]
)
def test_endpoint_change_cannot_authorize_other_corrections(mutation):
    _, start, _, end = worked_calculation_inputs()
    old = calculation_config()
    selected = resolve_window(old, (start, end))
    new = replace(old, version_id="config-2", end_scan_id=14)
    events = (start, end, calculation_event(14, day=8))
    if mutation == "weights":
        new = replace(new, weights=replace(old.weights, x_source="11"))
    elif mutation == "mapping":
        new = replace(new, map_version_id="map-2")
    elif mutation == "roster":
        new = replace(new, roster_id="roster-2")
    elif mutation == "start":
        new = replace(new, start_scan_id=11)
    elif mutation == "period":
        new = replace(new, period_id="other")
    elif mutation == "close":
        new = replace(new, closes_at_utc=datetime(2026, 9, 9, tzinfo=UTC))
    else:
        events = (replace(start, revision_id="corrected-start"), end, events[2])
    with pytest.raises(ValueError):
        resolve_window(new, events, previous=selected, endpoint_change=request(old, new))


def test_stale_or_missing_endpoint_request_rejected():
    _, start, _, end = worked_calculation_inputs()
    old = calculation_config()
    selected = resolve_window(old, (start, end))
    new = replace(old, version_id="config-2", end_scan_id=14)
    with pytest.raises(ValueError):
        resolve_window(new, (start, end), previous=selected)
    with pytest.raises(ValueError):
        resolve_window(
            new,
            (start, end),
            previous=selected,
            endpoint_change=replace(request(old, new), base_config_id="stale"),
        )


def test_t31_t32_t33_exact_scope_and_unassociated_later_ignored():
    start = calculation_event(10)
    middle = calculation_event(11, day=6)
    unrelated = calculation_event(999, day=9, periods=("fight:other",))
    config = calculation_config()
    selected = resolve_window(config, (start, middle, unrelated))
    assert selected.end == middle and selected.player_state == StreamState.LIVE
    assert resolve_window(config, (start, unrelated)).player_state == StreamState.MISSING_END
    assert resolve_window(config, (middle, unrelated)).player_state == StreamState.MISSING_START
    assert (
        resolve_window(replace(config, start_scan_id=None), (start,)).player_state
        == StreamState.MISSING_CONFIGURATION
    )
    foreign_meta = replace(
        start.observation.metadata,
        candidate=replace(start.observation.metadata.candidate, kvk_no=17),
    )
    foreign = replace(start, observation=replace(start.observation, metadata=foreign_meta))
    with pytest.raises(ValueError, match="source/season/schema"):
        resolve_window(config, (foreign,))


@pytest.mark.parametrize("case", ["before", "unassociated", "after_close", "tie", "duplicate"])
def test_invalid_or_ambiguous_event_endpoints_reject(case):
    start = calculation_event(10)
    end = calculation_event(13, day=7)
    config = calculation_config()
    if case == "before":
        end = calculation_event(13, day=4)
    elif case == "unassociated":
        end = replace(end, period_keys=("overall",))
    elif case == "after_close":
        config = replace(config, closes_at_utc=datetime(2026, 9, 6, tzinfo=UTC))
    events = (start, end)
    if case == "tie":
        config = replace(config, end_scan_id=None)
        events += (calculation_event(14, day=7),)
    elif case == "duplicate":
        events += (end,)
    with pytest.raises(ValueError):
        resolve_window(config, events)


def test_utc_and_daily_namespace_are_not_inferred():
    event = calculation_event(220)
    config = calculation_config(
        start_scan_id=220,
        end_scan_id=220,
        period_kind=PeriodKind.NO_FIGHT,
        period_key="no_fight:baseline",
    )
    with pytest.raises(ValueError, match="not mapped"):
        resolve_window(config, (event,))
    meta = event.observation.metadata
    with pytest.raises(ValueError, match="UTC"):
        replace(
            event,
            observation=replace(
                event.observation,
                metadata=replace(
                    meta, candidate=replace(meta.candidate, scan_start_utc=datetime(2026, 9, 5))
                ),
            ),
        )


@pytest.mark.parametrize("missing", ["start", "end"])
@pytest.mark.parametrize("update", [False, True])
def test_previously_pinned_endpoint_cannot_disappear(missing, update):
    _, start, middle, end = worked_calculation_inputs()
    old = calculation_config()
    previous = resolve_window(old, (start, end))
    config = replace(old, version_id="config-2", end_scan_id=14) if update else old
    events = (middle, end) if missing == "start" else (start, middle)
    with pytest.raises(ValueError, match="missing previously pinned"):
        resolve_window(
            config,
            events,
            previous=previous,
            endpoint_change=request(old, config) if update else None,
        )
    assert previous.end == end and previous.player_state == StreamState.FINAL
