from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime
import threading
from types import SimpleNamespace

import discord
import pytest

from player_self_service.stats_models import (
    PersonalStatsMetrics,
    PersonalStatsPayload,
    StatsCoverage,
    StatsDailyPoint,
    StatsGovernorOption,
    StatsMetricSummary,
    StatsMode,
    StatsPeriod,
    StatsResultState,
    StatsScopeType,
    StatsWindow,
)
from player_self_service.stats_renderer import RenderedStatsCard
from ui.views.player_self_service_stats_views import (
    PersonalStatsView,
    _attachment_description,
    show_personal_stats_for_interaction,
)


def _payload(option_count: int = 1) -> PersonalStatsPayload:
    empty = StatsMetricSummary(None, 0, 3)
    metrics = PersonalStatsMetrics(*((empty,) * 16))
    options = tuple(
        StatsGovernorOption(
            1000 + index,
            "Duplicate" if index < 2 else f"Governor {index}",
            "Main" if index == 0 else f"Farm{index}",
            index == 0,
        )
        for index in range(option_count)
    )
    return PersonalStatsPayload(
        discord_user_id=42,
        period=StatsPeriod.THIS_WEEK,
        window=StatsWindow(date(2026, 7, 13), date(2026, 7, 15)),
        stats_anchor_date=date(2026, 7, 15),
        scope_type=StatsScopeType.SELECTED,
        scope_governor_ids=(1000,),
        scope_label="Duplicate",
        governor_options=options,
        duplicate_id_warning=False,
        registry_fingerprint=tuple((option.slot, option.governor_id) for option in options),
        coverage=StatsCoverage(3, 0, option_count, 0, 3 * option_count, 0, 0, 0),
        state=StatsResultState.NO_DATA,
        metrics=metrics,
        data_refreshed_at_utc=datetime(2026, 7, 15, 11, 59, tzinfo=UTC),
        generated_at_utc=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("mode", "last_metric"),
    (
        (StatsMode.OVERVIEW, "Deads"),
        (StatsMode.ACTIVITY, "Forts joined"),
        (StatsMode.COMBAT, "Healed Troops gained"),
    ),
)
def test_attachment_description_preserves_accessible_metric_equivalents(
    mode: StatsMode, last_metric: str
) -> None:
    daily = (StatsDailyPoint(date(2026, 7, 15), 9_223_372_036_854_775_807),)
    maximum = StatsMetricSummary(
        9_223_372_036_854_775_807,
        180,
        180,
        daily=daily,
        peak_date=date(2026, 7, 15),
        peak_value=9_223_372_036_854_775_807,
    )
    payload = replace(_payload(), metrics=PersonalStatsMetrics(*((maximum,) * 16)))

    description = _attachment_description(payload, mode)

    assert last_metric in description
    assert "average" in description
    assert "peak" in description
    assert "coverage" in description
    assert len(description) <= 1024


class _Response:
    def __init__(self):
        self.done = False
        self.deferred = 0
        self.deferred_args = []
        self.messages = []
        self.edits = []

    def is_done(self):
        return self.done

    async def defer(self, **kwargs):
        self.done = True
        self.deferred += 1
        self.deferred_args.append(kwargs)

    async def send_message(self, *args, **kwargs):
        self.done = True
        self.messages.append((args, kwargs))

    async def edit_message(self, **kwargs):
        self.done = True
        self.edits.append(kwargs)


class _Interaction:
    def __init__(self, user_id: int = 42):
        self.user = SimpleNamespace(id=user_id)
        self.response = _Response()
        self.followup = SimpleNamespace(send=self._followup)
        self.followups = []
        self.original_edits = []
        self.message = None

    async def _followup(self, *args, **kwargs):
        self.followups.append((args, kwargs))

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return SimpleNamespace(edit=lambda **_kwargs: None)


@pytest.mark.asyncio
async def test_26_governors_use_safe_paging_opaque_tokens_and_exact_component_rows() -> None:
    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(26),
        avatar_bytes=None,
    )

    navigation = [
        child for child in view.children if isinstance(child, discord.ui.Button) and child.row == 0
    ]
    modes = [
        child for child in view.children if isinstance(child, discord.ui.Button) and child.row == 1
    ]
    period = [
        child for child in view.children if isinstance(child, discord.ui.Select) and child.row == 2
    ]
    scope = next(
        child for child in view.children if isinstance(child, discord.ui.Select) and child.row == 3
    )
    paging = [
        child
        for child in view.children
        if isinstance(child, discord.ui.Button)
        and child.row == 4
        and str(child.custom_id).startswith("me:stats:scope:")
    ]
    dashboard = [
        child
        for child in view.children
        if isinstance(child, discord.ui.Button) and child.custom_id == "me:stats:dashboard"
    ]

    assert [button.label for button in navigation] == [
        "Accounts",
        "Reminders",
        "Preferences",
        "Stats",
    ]
    assert navigation[-1].disabled is True
    assert [button.label for button in modes] == ["Overview", "Activity", "Combat"]
    assert len(period) == 1
    assert len(scope.options) == 25  # All Linked plus 24 governor slots.
    assert {button.label for button in paging} == {"Previous Governors", "Next Governors"}
    assert [button.label for button in dashboard] == ["Dashboard"]
    assert all(
        option.value not in {str(1000 + index) for index in range(26)} for option in scope.options
    )
    duplicate_labels = [option.label for option in scope.options if "Duplicate" in option.label]
    assert duplicate_labels and all("ID" in label for label in duplicate_labels)

    last_governor_view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=replace(_payload(26), scope_governor_ids=(1025,), scope_label="Governor 25"),
        avatar_bytes=None,
    )
    assert last_governor_view.scope_page == 1


@pytest.mark.asyncio
async def test_one_linked_governor_has_no_redundant_scope_selector() -> None:
    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(1),
        avatar_bytes=None,
    )

    assert not any(
        isinstance(child, discord.ui.Select) and child.row == 3 for child in view.children
    )


@pytest.mark.asyncio
async def test_stats_navigation_opens_shared_page_with_selected_governor(monkeypatch) -> None:
    from ui.views import player_self_service_views as page_views

    calls = []

    async def fake_show(interaction, **kwargs):
        calls.append((interaction, kwargs))
        assert kwargs["can_edit"]() is True
        return True

    monkeypatch.setattr(page_views, "show_player_self_service_page_for_interaction", fake_show)
    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(2),
        avatar_bytes=b"avatar",
    )
    interaction = _Interaction()

    await view.open_page(interaction, "preferences")

    assert len(calls) == 1
    assert calls[0][1]["page"] == "preferences"
    assert calls[0][1]["avatar_bytes"] == b"avatar"
    assert calls[0][1]["dashboard_governor_id"] == 1000


@pytest.mark.asyncio
async def test_stale_stats_initial_navigation_cannot_replace_newer_page() -> None:
    renderer_calls = []

    def renderer(*_args, **_kwargs):
        renderer_calls.append(True)
        return RenderedStatsCard("me_stats_42.png", b"png")

    interaction = _Interaction()
    result = await show_personal_stats_for_interaction(
        interaction,
        author_id=42,
        display_name="Player",
        entry_route="page",
        payload_loader=lambda *_args, **_kwargs: asyncio.sleep(0, result=_payload()),
        renderer=renderer,
        can_edit=lambda: False,
    )

    assert result is None
    assert renderer_calls == []
    assert interaction.original_edits == []


@pytest.mark.asyncio
async def test_author_check_and_forged_or_expired_token_are_private_and_do_not_load() -> None:
    calls = []

    async def payload_loader(*args, **kwargs):
        calls.append((args, kwargs))
        return _payload(2)

    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(2),
        avatar_bytes=None,
        payload_loader=payload_loader,
    )
    foreign = _Interaction(99)
    assert await view.interaction_check(foreign) is False
    assert foreign.response.messages[-1][1]["ephemeral"] is True

    forged = _Interaction()
    await view.change_scope(forged, "forged-token")
    assert calls == []
    assert forged.response.messages[-1][1]["ephemeral"] is True
    assert "expired or invalid" in forged.response.messages[-1][0][0]


@pytest.mark.asyncio
async def test_command_entry_is_explicitly_ephemeral_from_any_channel() -> None:
    interaction = _Interaction()

    async def payload_loader(*_args, **_kwargs):
        return _payload()

    await show_personal_stats_for_interaction(
        interaction,
        author_id=42,
        display_name="Player",
        entry_route="command",
        payload_loader=payload_loader,
        renderer=lambda *_args, **_kwargs: RenderedStatsCard("me_stats_42.png", b"png"),
    )

    assert interaction.response.deferred_args == [{"ephemeral": True}]
    description = interaction.original_edits[-1]["files"][0].description
    assert description.startswith("Period Performance Overview")
    assert "Power change" in description
    assert len(description) <= 1024


@pytest.mark.asyncio
async def test_initial_failure_does_not_expose_exception_or_sql_details() -> None:
    interaction = _Interaction()

    async def payload_loader(*_args, **_kwargs):
        raise RuntimeError("pyodbc secret SELECT failure")

    result = await show_personal_stats_for_interaction(
        interaction,
        author_id=42,
        display_name="Player",
        entry_route="command",
        payload_loader=payload_loader,
    )

    assert result is None
    content = interaction.original_edits[-1]["content"]
    assert content == "Period performance is temporarily unavailable. Please try again shortly."
    assert "RuntimeError" not in content
    assert "SELECT" not in content


@pytest.mark.asyncio
async def test_render_failure_uses_same_payload_fallback_without_second_fetch() -> None:
    interaction = _Interaction()
    payload_calls = 0

    async def payload_loader(*_args, **_kwargs):
        nonlocal payload_calls
        payload_calls += 1
        return _payload()

    def renderer(*_args, **_kwargs):
        raise OSError("renderer unavailable")

    result = await show_personal_stats_for_interaction(
        interaction,
        author_id=42,
        display_name="Player",
        entry_route="command",
        payload_loader=payload_loader,
        renderer=renderer,
    )

    assert result is not None
    assert payload_calls == 1
    assert interaction.original_edits[-1]["embed"].title.startswith("Period Performance")


@pytest.mark.asyncio
async def test_mode_change_reuses_payload_and_closes_attachment_stream() -> None:
    payload_calls = []

    async def payload_loader(*args, **kwargs):
        payload_calls.append((args, kwargs))
        return _payload()

    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(),
        avatar_bytes=None,
        payload_loader=payload_loader,
        renderer=lambda *_args, **_kwargs: RenderedStatsCard("me_stats_42.png", b"png"),
    )
    interaction = _Interaction()

    await view.change_mode(interaction, StatsMode.COMBAT)

    assert payload_calls == []
    assert view.mode is StatsMode.COMBAT
    assert interaction.response.deferred == 1
    attached = interaction.original_edits[-1]["files"][0]
    assert "T4+T5 combined" in attached.description
    assert "peak" in attached.description
    assert "coverage" in attached.description
    assert len(attached.description) <= 1024
    assert attached.fp.closed is True


@pytest.mark.asyncio
async def test_timeout_preserves_report_and_disables_every_control() -> None:
    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(2),
        avatar_bytes=None,
    )
    edits = []

    class Target:
        async def edit_original_response(self, **kwargs):
            edits.append(kwargs)

    view.set_timeout_target(Target())

    await view.on_timeout()

    assert edits == [
        {
            "content": "Report controls expired. Run /me stats to refresh.",
            "view": view,
        }
    ]
    assert all(child.disabled for child in view.children)
    assert "attachments" not in edits[0]


@pytest.mark.asyncio
async def test_latest_period_transition_wins_and_stale_work_cannot_replace_it() -> None:
    first_started = asyncio.Event()

    async def payload_loader(_user_id, *, period, **_kwargs):
        if period is StatsPeriod.LAST_WEEK:
            first_started.set()
            await asyncio.Event().wait()
        return replace(_payload(), period=period)

    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(),
        avatar_bytes=None,
        payload_loader=payload_loader,
        renderer=lambda *_args, **_kwargs: RenderedStatsCard("me_stats_42.png", b"png"),
    )
    stale_interaction = _Interaction()
    latest_interaction = _Interaction()

    stale = asyncio.create_task(view.change_period(stale_interaction, StatsPeriod.LAST_WEEK))
    await first_started.wait()
    latest = asyncio.create_task(view.change_period(latest_interaction, StatsPeriod.THIS_MONTH))
    await asyncio.gather(stale, latest)

    assert view.period is StatsPeriod.THIS_MONTH
    assert stale_interaction.original_edits == []
    assert len(latest_interaction.original_edits) == 1


@pytest.mark.asyncio
async def test_cancelled_render_transitions_remain_bounded_to_two_workers() -> None:
    lock = threading.Lock()
    release = threading.Event()
    active = 0
    maximum = 0

    def blocking_renderer(*_args, **_kwargs):
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
        release.wait(5)
        with lock:
            active -= 1
        return RenderedStatsCard("me_stats_42.png", b"png")

    view = PersonalStatsView(
        author_id=42,
        display_name="Player",
        payload=_payload(),
        avatar_bytes=None,
        renderer=blocking_renderer,
    )
    tasks: list[asyncio.Task] = []
    try:
        tasks = [
            asyncio.create_task(view._render(view.payload, StatsMode.ACTIVITY)) for _ in range(2)
        ]
        for _ in range(100):
            with lock:
                if maximum == 2:
                    break
            await asyncio.sleep(0.01)
        assert maximum == 2

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        replacement_tasks = [
            asyncio.create_task(view._render(view.payload, StatsMode.COMBAT)) for _ in range(3)
        ]
        tasks.extend(replacement_tasks)
        await asyncio.sleep(0.1)
        assert maximum == 2
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        release.set()
        await asyncio.sleep(0.05)
