"""Discord interaction coverage for the governor-first dashboard."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import discord
import pytest

from player_self_service.governor_dashboard_models import (
    GovernorDashboardAccessDecision,
    GovernorDashboardActivityHonours,
    GovernorDashboardContext,
    GovernorDashboardFreshness,
    GovernorDashboardHistoricalHighlights,
    GovernorDashboardIdentity,
    GovernorDashboardInventoryHighlights,
    GovernorDashboardLatestMetrics,
    GovernorDashboardOption,
    GovernorDashboardPayload,
    GovernorDashboardProfileStatus,
    GovernorDashboardResolution,
    GovernorDashboardSelfView,
)
from ui.views import player_self_service_governor_dashboard_views as views


@pytest.fixture(autouse=True)
def _fast_governor_card_renderer(monkeypatch):
    monkeypatch.setattr(
        views,
        "render_governor_dashboard",
        lambda payload, *, avatar_bytes=None: SimpleNamespace(
            filename="governor_dashboard.png",
            image_bytes=b"rendered-governor-card",
        ),
    )


class _Response:
    def __init__(self) -> None:
        self.deferred: list[dict] = []
        self.sent: list[tuple[tuple, dict]] = []
        self.edited: list[dict] = []
        self._done = False

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        self._done = True

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)
        self._done = True
        return SimpleNamespace(id=777)

    def is_done(self) -> bool:
        return self._done


class _Followup:
    def __init__(self) -> None:
        self.sent: list[tuple[tuple, dict, object]] = []

    async def send(self, *args, **kwargs):
        message = SimpleNamespace(id=888, edits=[])
        self.sent.append((args, kwargs, message))
        return message


class _User:
    def __init__(self, user_id: int = 42) -> None:
        self.id = user_id
        self.display_name = "Tester"
        self.name = "tester"


class _Interaction:
    def __init__(self, user_id: int = 42, *, component: bool = True) -> None:
        self.user = _User(user_id)
        self.response = _Response()
        self.followup = _Followup()
        self.message = SimpleNamespace(id=123) if component else None
        self.original_edits: list[dict] = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return SimpleNamespace(id=456)


class _EditableMessage:
    def __init__(self) -> None:
        self.edits: list[dict] = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)
        return self


def _option(
    governor_id: int,
    *,
    name: str | None = None,
    account_type: str = "Main",
    is_default: bool = False,
) -> GovernorDashboardOption:
    return GovernorDashboardOption(
        governor_id=governor_id,
        governor_id_str=str(governor_id),
        governor_name=name or f"Gov {governor_id}",
        account_type=account_type,
        is_default=is_default,
    )


def _context(option: GovernorDashboardOption, *, user_id: int = 42) -> GovernorDashboardContext:
    return GovernorDashboardContext(
        viewer_discord_id=user_id,
        viewer_mode="self",
        selected_governor_id=option.governor_id,
        selected_governor_name=option.governor_name,
        is_linked_to_viewer=True,
        account_type_for_self_view=option.account_type,
        access_decision=GovernorDashboardAccessDecision(
            allowed=True,
            reason="linked governor selected",
        ),
        privacy_profile="self_view",
    )


def _selected_resolution(
    option: GovernorDashboardOption,
    *,
    options: tuple[GovernorDashboardOption, ...] | None = None,
) -> GovernorDashboardResolution:
    return GovernorDashboardResolution(
        state="selected",
        options=options or (option,),
        context=_context(option),
        default_option=(options or (option,))[0],
    )


def _payload(
    context: GovernorDashboardContext,
    *,
    missing: bool = False,
) -> GovernorDashboardPayload:
    return GovernorDashboardPayload(
        context=context,
        identity=GovernorDashboardIdentity(
            governor_name=context.selected_governor_name or "Linked Gov",
            governor_id=context.selected_governor_id or 0,
            alliance=None if missing else "KD98",
            civilisation=None if missing else "France",
            location_x=None if missing else 123,
            location_y=None if missing else 456,
        ),
        latest_metrics=GovernorDashboardLatestMetrics(
            power=None if missing else 123456789,
            kill_points=None if missing else 987654321,
            dead=None if missing else 1234,
            helps=None if missing else 5678,
            healed=None if missing else 9999,
        ),
        historical_highlights=GovernorDashboardHistoricalHighlights(
            highest_acclaim=None if missing else 88,
            times_named_autarch=None if missing else 3,
            times_autarch_participated=None if missing else 6,
        ),
        activity_honours=GovernorDashboardActivityHonours(
            ark_joined=0 if missing else 10,
            ark_won=0 if missing else 7,
            ark_win_ratio=None if missing else 0.7,
            ark_win_ratio_label="N/A" if missing else "70%",
        ),
        profile_status=GovernorDashboardProfileStatus(
            conduct_score=None if missing else 94.5,
        ),
        freshness=GovernorDashboardFreshness(
            updated_at_utc=None if missing else datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
            scan_order=None if missing else 456,
            source=None if missing else "KingdomScanData4",
        ),
        inventory=GovernorDashboardInventoryHighlights(
            total_resources=None if missing else 100_700_000_000,
            total_speedup_days=None if missing else 4_372,
            total_legendary_materials=None if missing else 177,
        ),
        available_actions=(
            "accounts",
            "reminders",
            "preferences",
            "exports",
            "resources",
            "materials",
            "speedups",
        ),
        missing_fields=("vip_level_label",) if missing else (),
        self_view=GovernorDashboardSelfView(
            account_type=context.account_type_for_self_view,
            vip_level_label=None if missing else "VIP 19",
        ),
    )


def _ctx() -> SimpleNamespace:
    interaction = _Interaction(component=False)
    return SimpleNamespace(user=interaction.user, interaction=interaction)


def _custom_ids(view: discord.ui.View) -> set[str]:
    return {str(child.custom_id) for child in view.children if child.custom_id}


@pytest.mark.asyncio
async def test_no_governors_opens_private_setup_shell_with_accounts_primary() -> None:
    ctx = _ctx()

    async def resolver(user_id: int, **kwargs):
        assert user_id == 42
        assert kwargs == {"viewer_mode": "self"}
        return GovernorDashboardResolution(state="requires_setup", options=())

    async def payload_loader(_context):
        raise AssertionError("setup state must not fetch dashboard data")

    await views.send_governor_dashboard(
        ctx,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    interaction = ctx.interaction
    assert interaction.response.deferred == [{"ephemeral": True}]
    edited = interaction.original_edits[-1]
    assert edited["embed"].title == "Set up your Governor Dashboard"
    assert "me:dashboard:navigate:accounts" in _custom_ids(edited["view"])
    accounts = next(
        child
        for child in edited["view"].children
        if child.custom_id == "me:dashboard:navigate:accounts"
    )
    assert accounts.style is discord.ButtonStyle.success


@pytest.mark.asyncio
async def test_one_governor_opens_dashboard_directly_after_access_resolution() -> None:
    option = _option(111, name="Main Gov", is_default=True)
    resolution = _selected_resolution(option)
    ctx = _ctx()
    order: list[str] = []

    async def resolver(_user_id: int, **_kwargs):
        order.append("access")
        return resolution

    async def payload_loader(context):
        order.append("payload")
        assert context.access_allowed is True
        return _payload(context)

    await views.send_governor_dashboard(
        ctx,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    edited = ctx.interaction.original_edits[-1]
    assert order == ["access", "payload"]
    assert edited["embed"] is None
    assert edited["attachments"] == []
    assert [item.filename for item in edited["files"]] == ["governor_dashboard.png"]
    assert edited["files"][0].fp.closed is True
    assert "me:dashboard:change" not in _custom_ids(edited["view"])


@pytest.mark.asyncio
async def test_selected_card_uses_invoking_players_discord_avatar(monkeypatch) -> None:
    option = _option(111, name="Main Gov", is_default=True)
    ctx = _ctx()
    captured: dict[str, object] = {}

    class Avatar:
        def with_size(self, size):
            captured["size"] = size
            return self

        async def read(self):
            return b"discord-avatar"

    ctx.user.display_avatar = Avatar()

    def fake_render(payload, *, avatar_bytes=None):
        captured["avatar_bytes"] = avatar_bytes
        return SimpleNamespace(filename="governor_dashboard.png", image_bytes=b"card")

    monkeypatch.setattr(views, "render_governor_dashboard", fake_render)

    async def resolver(_user_id: int, **_kwargs):
        return _selected_resolution(option)

    async def payload_loader(context):
        return _payload(context)

    await views.send_governor_dashboard(
        ctx, context_resolver=resolver, payload_loader=payload_loader
    )

    assert captured == {"size": 256, "avatar_bytes": b"discord-avatar"}


@pytest.mark.asyncio
async def test_avatar_reader_rejects_a_different_discord_user() -> None:
    foreign = _User(99)

    class Avatar:
        async def read(self):
            raise AssertionError("foreign avatar must not be read")

    foreign.display_avatar = Avatar()
    assert await views._read_avatar_bytes(foreign, expected_user_id=42) is None


@pytest.mark.asyncio
async def test_render_failure_uses_same_payload_fallback_without_second_fetch(monkeypatch) -> None:
    option = _option(111, name="Main Gov", is_default=True)
    ctx = _ctx()
    payload_calls = 0

    def broken_render(payload, *, avatar_bytes=None):
        raise RuntimeError("render failed")

    monkeypatch.setattr(views, "render_governor_dashboard", broken_render)

    async def resolver(_user_id: int, **_kwargs):
        return _selected_resolution(option)

    async def payload_loader(context):
        nonlocal payload_calls
        payload_calls += 1
        return _payload(context)

    await views.send_governor_dashboard(
        ctx, context_resolver=resolver, payload_loader=payload_loader
    )

    edited = ctx.interaction.original_edits[-1]
    assert payload_calls == 1
    assert edited["embed"].title == "Governor Dashboard — Main Gov"
    assert edited["attachments"] == []
    assert "files" not in edited


@pytest.mark.asyncio
async def test_image_delivery_failure_retries_embed_and_closes_file() -> None:
    option = _option(111, name="Main Gov", is_default=True)
    ctx = _ctx()
    payload_calls = 0
    attempts: list[dict] = []

    async def resolver(_user_id: int, **_kwargs):
        return _selected_resolution(option)

    async def payload_loader(context):
        nonlocal payload_calls
        payload_calls += 1
        return _payload(context)

    async def flaky_edit(**kwargs):
        attempts.append(kwargs)
        if kwargs.get("files"):
            raise RuntimeError("attachment rejected")
        return SimpleNamespace(id=456)

    ctx.interaction.edit_original_response = flaky_edit
    await views.send_governor_dashboard(
        ctx, context_resolver=resolver, payload_loader=payload_loader
    )

    assert payload_calls == 1
    assert len(attempts) == 2
    assert attempts[0]["files"][0].fp.closed is True
    assert attempts[1]["embed"].title == "Governor Dashboard — Main Gov"
    assert attempts[1]["attachments"] == []


@pytest.mark.asyncio
async def test_multiple_governors_show_selector_before_payload_fetch() -> None:
    options = (
        _option(111, name="  Main\r\n  Gov  ", is_default=True),
        _option(222, name="Alt Gov", account_type="Alt 1"),
    )
    ctx = _ctx()

    async def resolver(_user_id: int, **_kwargs):
        return GovernorDashboardResolution(
            state="requires_selection",
            options=options,
            default_option=options[0],
        )

    async def payload_loader(_context):
        raise AssertionError("selector state must not fetch dashboard data")

    await views.send_governor_dashboard(
        ctx,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    edited = ctx.interaction.original_edits[-1]
    assert edited["embed"].title == "Choose a Governor"
    selector = next(
        child for child in edited["view"].children if isinstance(child, discord.ui.Select)
    )
    assert [choice.label for choice in selector.options] == ["Main Gov", "Alt Gov"]
    assert [choice.value for choice in selector.options] == ["111", "222"]
    assert edited["embed"].fields[0].value == "Main Gov (`111`)"
    assert len(edited["view"].children) == 1


def test_governor_option_label_falls_back_to_id_after_whitespace_sanitization() -> None:
    option = _option(111, name=" \r\n\t ")

    assert views._option_label(option) == "111"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("state", "title"),
    [
        ("unavailable", "Governor Dashboard Temporarily Unavailable"),
        ("denied", "Governor Access Denied"),
    ],
)
async def test_unavailable_and_denied_states_do_not_fetch_payload(state: str, title: str) -> None:
    ctx = _ctx()

    async def resolver(_user_id: int, **_kwargs):
        return GovernorDashboardResolution(state=state, options=(), reason=state)

    async def payload_loader(_context):
        raise AssertionError("failure states must not fetch dashboard data")

    await views.send_governor_dashboard(
        ctx,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    assert ctx.interaction.original_edits[-1]["embed"].title == title


@pytest.mark.asyncio
async def test_forged_selection_is_rechecked_and_denied_before_payload_fetch() -> None:
    linked = _option(111, name="Main Gov", is_default=True)
    initial = GovernorDashboardResolution(
        state="requires_selection",
        options=(linked, _option(222, account_type="Alt 1")),
    )
    calls: list[tuple] = []

    async def resolver(user_id: int, governor_id: str, **kwargs):
        calls.append((user_id, governor_id, kwargs))
        return GovernorDashboardResolution(
            state="denied",
            options=(linked,),
            reason="governor is not linked",
        )

    async def payload_loader(_context):
        raise AssertionError("denied forged selection must not fetch dashboard data")

    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    interaction = _Interaction()

    await view.select_governor(interaction, "999")

    assert calls == [(42, "999", {"viewer_mode": "self"})]
    assert interaction.original_edits[-1]["embed"].title == "Governor Access Denied"
    assert interaction.response.deferred == [{}]


@pytest.mark.asyncio
async def test_selected_resolution_must_be_linked_self_context_for_same_author() -> None:
    option = _option(111, name="Main Gov")
    unsafe_context = GovernorDashboardContext(
        viewer_discord_id=99,
        viewer_mode="inspect",
        selected_governor_id=111,
        selected_governor_name="Main Gov",
        is_linked_to_viewer=False,
        account_type_for_self_view=None,
        access_decision=GovernorDashboardAccessDecision(allowed=True, reason="inspect mode"),
        privacy_profile="inspect_safe",
    )
    ctx = _ctx()

    async def resolver(_user_id: int, **_kwargs):
        return GovernorDashboardResolution(
            state="selected",
            options=(option,),
            context=unsafe_context,
        )

    async def payload_loader(_context):
        raise AssertionError("non-self or wrong-author context must not fetch dashboard data")

    await views.send_governor_dashboard(
        ctx,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    assert ctx.interaction.original_edits[-1]["embed"].title == "Governor Access Denied"


@pytest.mark.asyncio
async def test_valid_selection_rechecks_access_before_payload_and_edits_in_place() -> None:
    main = _option(111, name="Main Gov", is_default=True)
    alt = _option(222, name="Alt Gov", account_type="Alt 1")
    initial = GovernorDashboardResolution(state="requires_selection", options=(main, alt))
    selected = _selected_resolution(alt, options=(main, alt))
    order: list[str] = []

    async def resolver(_user_id: int, governor_id: str, **_kwargs):
        assert governor_id == "222"
        order.append("access")
        return selected

    async def payload_loader(context):
        order.append("payload")
        assert context.selected_governor_id == 222
        return _payload(context)

    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    interaction = _Interaction()

    await view.select_governor(interaction, "222")

    assert order == ["access", "payload"]
    edited = interaction.original_edits[-1]
    assert edited["embed"] is None
    assert [item.filename for item in edited["files"]] == ["governor_dashboard.png"]
    assert edited["files"][0].fp.closed is True
    assert "me:dashboard:governor" in _custom_ids(edited["view"])
    assert interaction.followup.sent == []

    raced_stale_interaction = _Interaction()
    assert await view.interaction_check(raced_stale_interaction) is False
    assert "expired" in raced_stale_interaction.response.sent[-1][0][0]


@pytest.mark.asyncio
async def test_change_governor_is_multi_only_dropdown_below_blue_navigation() -> None:
    main = _option(111, name="Main Gov", is_default=True)
    alt = _option(222, name="Alt Gov", account_type="Alt 1")
    single_view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(main),
    )
    assert "me:dashboard:governor" not in _custom_ids(single_view)

    multi_resolution = _selected_resolution(main, options=(main, alt))

    selected_alt = _selected_resolution(alt, options=(main, alt))
    order: list[str] = []

    async def resolver(_user_id: int, governor_id: str, **_kwargs):
        assert governor_id == "222"
        order.append("access")
        return selected_alt

    async def payload_loader(context):
        order.append("payload")
        return _payload(context)

    multi_view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=multi_resolution,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    assert "me:dashboard:change" not in _custom_ids(multi_view)
    assert "me:dashboard:governor" in _custom_ids(multi_view)
    change_select = next(
        child for child in multi_view.children if isinstance(child, discord.ui.Select)
    )
    assert change_select.placeholder == "Change Governor"
    assert change_select.row == 3
    top_buttons = [
        child
        for child in multi_view.children
        if isinstance(child, discord.ui.Button) and child.row == 0
    ]
    assert [button.label for button in top_buttons] == ["Accounts", "Reminders", "Preferences"]
    assert all(button.style is discord.ButtonStyle.primary for button in top_buttons)
    report_buttons = [
        child
        for child in multi_view.children
        if isinstance(child, discord.ui.Button) and child.row == 2
    ]
    assert [button.label for button in report_buttons] == ["RSS", "Speedups", "Materials"]
    assert all(button.style is discord.ButtonStyle.success for button in report_buttons)
    assert "me:dashboard:navigate:inventory" not in _custom_ids(multi_view)
    interaction = _Interaction()

    await multi_view.select_governor(interaction, "222")

    assert order == ["access", "payload"]
    edited = interaction.original_edits[-1]
    assert edited["embed"] is None
    assert edited["attachments"] == []
    assert [item.filename for item in edited["files"]] == ["governor_dashboard.png"]


@pytest.mark.asyncio
async def test_navigation_preserves_selected_governor_and_edits_component_message(
    monkeypatch,
) -> None:
    from ui.views import player_self_service_views as page_views

    option = _option(111, name="Main Gov")

    async def summary_loader(_user_id: int):
        return SimpleNamespace()

    async def fake_page_response(*_args, **_kwargs):
        return discord.Embed(title="Accounts"), []

    monkeypatch.setattr(page_views, "_build_page_response", fake_page_response)
    dashboard_view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(option),
        summary_loader=summary_loader,
    )
    interaction = _Interaction()

    await dashboard_view.open_page(interaction, page_views.PAGE_ACCOUNTS)

    assert interaction.response.deferred == [{}]
    edited = interaction.original_edits[-1]
    assert edited["attachments"] == []
    page_view = edited["view"]
    assert page_view.dashboard_governor_id == 111

    dashboard_calls = []

    async def fake_dashboard(target, **kwargs):
        dashboard_calls.append((target, kwargs))

    monkeypatch.setattr(views, "show_governor_dashboard_for_interaction", fake_dashboard)
    return_interaction = _Interaction()

    await page_view._show_page(return_interaction, page_views.PAGE_DASHBOARD)

    assert dashboard_calls[0][0] is return_interaction
    assert dashboard_calls[0][1]["governor_id"] == 111


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("report_view", "expected"),
    (
        ("RESOURCES", "resources"),
        ("MATERIALS", "materials"),
        ("SPEEDUPS", "speedups"),
    ),
)
async def test_dashboard_report_actions_preserve_selected_governor(
    monkeypatch,
    report_view,
    expected,
) -> None:
    from inventory.models import InventoryReportView
    from ui.views import player_self_service_inventory_report_views as report_views

    calls = []

    async def fake_report(interaction, **kwargs):
        calls.append((interaction, kwargs))

    monkeypatch.setattr(
        report_views,
        "show_player_inventory_report_for_interaction",
        fake_report,
    )
    option = _option(111, name="Main Gov")
    dashboard = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(option),
    )
    interaction = _Interaction()

    await dashboard.open_inventory_report(
        interaction,
        getattr(InventoryReportView, report_view),
    )

    assert calls[0][0] is interaction
    assert calls[0][1]["author_id"] == 42
    assert calls[0][1]["governor_id"] == 111
    assert calls[0][1]["report_view"].value == expected


@pytest.mark.asyncio
async def test_dashboard_report_action_reports_unexpected_failure_privately(monkeypatch) -> None:
    from inventory.models import InventoryReportView
    from ui.views import player_self_service_inventory_report_views as report_views

    async def failed_report(*_args, **_kwargs):
        raise RuntimeError("discord edit failed")

    monkeypatch.setattr(
        report_views,
        "show_player_inventory_report_for_interaction",
        failed_report,
    )
    option = _option(111, name="Main Gov")
    dashboard = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(option),
    )
    interaction = _Interaction()

    await dashboard.open_inventory_report(interaction, InventoryReportView.RESOURCES)

    assert interaction.response.sent[-1][1]["ephemeral"] is True
    assert "could not be opened" in interaction.response.sent[-1][0][0]


def test_short_number_format_matches_existing_dashboard_style() -> None:
    assert views._format_short_number(182_200_000) == "182.2M"
    assert views._format_short_number(74_000) == "74K"


def test_vip_label_does_not_repeat_vip_prefix() -> None:
    option = _option(111, name="Main Gov")
    payload = _payload(_context(option))
    payload = replace(
        payload,
        self_view=GovernorDashboardSelfView(
            account_type="Alt 1",
            vip_level_label="VIP 14 or less",
        ),
    )

    embed = views.build_governor_dashboard_embed(payload)

    assert "VIP 14 or less" in embed.fields[0].value
    assert "VIP: VIP" not in embed.fields[0].value


@pytest.mark.asyncio
async def test_author_gate_and_expired_view_fail_privately() -> None:
    option = _option(111)
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(option),
    )

    foreign = _Interaction(user_id=99)
    assert await view.interaction_check(foreign) is False
    assert foreign.response.sent[-1][1]["ephemeral"] is True
    assert "not for you" in foreign.response.sent[-1][0][0]

    message = _EditableMessage()
    view.set_message_ref(message)
    await view.on_timeout()
    assert all(child.disabled for child in view.children)
    assert "expired" in message.edits[-1]["content"]

    stale = _Interaction()
    assert await view.interaction_check(stale) is False
    assert stale.response.sent[-1][1]["ephemeral"] is True
    assert "expired" in stale.response.sent[-1][0][0]


@pytest.mark.asyncio
async def test_timeout_edits_original_ephemeral_response_gracefully() -> None:
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(_option(111)),
    )
    interaction = _Interaction()
    view.set_timeout_target(interaction)

    await view.on_timeout()

    edited = interaction.original_edits[-1]
    assert "expired" in edited["content"]
    assert edited["view"] is view
    assert all(child.disabled for child in view.children)


def test_missing_values_missing_vip_and_zero_ark_are_safe_and_no_olympia_text() -> None:
    option = _option(111, name="Main Gov", is_default=True)
    payload = _payload(_context(option), missing=True)

    embed = views.build_governor_dashboard_embed(payload)
    rendered = " ".join(
        [embed.title or "", embed.description or ""]
        + [f"{field.name} {field.value}" for field in embed.fields]
    ).casefold()

    assert "vip: not set" in rendered
    assert "ark win ratio: n/a" in rendered
    assert "power: n/a" in rendered
    assert "location: n/a" in rendered
    assert "times autarch participated: n/a" in rendered
    assert "no recent scan available" in rendered
    assert "olympia" not in rendered


def test_dashboard_titles_sanitize_untrusted_names_and_respect_discord_limit() -> None:
    unsafe_name = "  @everyone <@123>  " + ("x" * 300)
    option = _option(111, name=unsafe_name)
    context = _context(option)

    dashboard_title = views.build_governor_dashboard_embed(_payload(context)).title or ""
    error_title = views.build_governor_payload_error_embed(context).title or ""

    for title in (dashboard_title, error_title):
        assert len(title) <= 256
        assert "@everyone" not in title
        assert "<" not in title
        assert ">" not in title
        assert "\n" not in title
        assert "@\u200beveryone ‹@\u200b123›" in title


@pytest.mark.asyncio
async def test_payload_failure_renders_safe_missing_data_shell() -> None:
    option = _option(111, name="Main Gov")
    ctx = _ctx()

    async def resolver(_user_id: int, **_kwargs):
        return _selected_resolution(option)

    async def payload_loader(_context):
        raise RuntimeError("SQL unavailable")

    await views.send_governor_dashboard(
        ctx,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    embed = ctx.interaction.original_edits[-1]["embed"]
    assert embed.title == "Governor Dashboard — Main Gov"
    assert "temporarily unavailable" in embed.description
    assert embed.fields[1].value == "Dashboard metrics: N/A"


@pytest.mark.asyncio
async def test_inflight_selection_rejects_concurrent_navigation(monkeypatch) -> None:
    main = _option(111, name="Main Gov", is_default=True)
    alt = _option(222, name="Alt Gov", account_type="Alt 1")
    initial = GovernorDashboardResolution(state="requires_selection", options=(main, alt))
    selected = _selected_resolution(alt, options=(main, alt))
    resolver_started = asyncio.Event()
    release_resolver = asyncio.Event()
    navigation_calls = []

    async def resolver(_user_id: int, _governor_id: str, **_kwargs):
        resolver_started.set()
        await release_resolver.wait()
        return selected

    async def payload_loader(context):
        return _payload(context)

    async def fake_navigation(*args, **kwargs):
        navigation_calls.append((args, kwargs))

    from ui.views import player_self_service_views as legacy_views

    monkeypatch.setattr(
        legacy_views,
        "show_player_self_service_page_for_interaction",
        fake_navigation,
    )
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    selection_interaction = _Interaction()
    navigation_interaction = _Interaction()

    selection_task = asyncio.create_task(view.select_governor(selection_interaction, "222"))
    await resolver_started.wait()
    await view.open_page(navigation_interaction, "accounts")
    release_resolver.set()
    await selection_task

    assert navigation_calls == []
    assert "stale" in navigation_interaction.response.sent[-1][0][0]
    assert selection_interaction.original_edits[-1]["embed"] is None


@pytest.mark.asyncio
async def test_duplicate_pagination_is_serialized() -> None:
    options = tuple(_option(100 + index, account_type=f"Farm {index}") for index in range(26))
    resolution = GovernorDashboardResolution(state="requires_selection", options=options)
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=resolution,
    )
    first = _Interaction()
    second = _Interaction()
    edit_started = asyncio.Event()
    release_edit = asyncio.Event()
    original_edit = first.response.edit_message

    async def slow_edit(**kwargs):
        edit_started.set()
        await release_edit.wait()
        return await original_edit(**kwargs)

    first.response.edit_message = slow_edit
    first_task = asyncio.create_task(view.next_selector_page(first))
    await edit_started.wait()
    await view.previous_selector_page(second)
    release_edit.set()
    await first_task

    assert len(first.response.edited) == 1
    assert "stale" in second.response.sent[-1][0][0]


@pytest.mark.asyncio
async def test_real_timeout_during_payload_suppresses_late_dashboard_edit() -> None:
    main = _option(111, name="Main Gov", is_default=True)
    alt = _option(222, name="Alt Gov", account_type="Alt 1")
    initial = GovernorDashboardResolution(state="requires_selection", options=(main, alt))
    selected = _selected_resolution(alt, options=(main, alt))
    payload_started = asyncio.Event()
    release_payload = asyncio.Event()

    async def resolver(_user_id: int, _governor_id: str, **_kwargs):
        return selected

    async def payload_loader(context):
        payload_started.set()
        await release_payload.wait()
        return _payload(context)

    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        context_resolver=resolver,
        payload_loader=payload_loader,
        timeout=0.01,
    )
    interaction = _Interaction()
    message = _EditableMessage()
    view.set_message_ref(message)
    view._start_listening_from_store(SimpleNamespace(remove_view=lambda _view: None))

    selection_task = asyncio.create_task(view.select_governor(interaction, "222"))
    await payload_started.wait()
    await asyncio.sleep(0.05)
    assert view._timed_out is True
    release_payload.set()
    await selection_task

    assert interaction.original_edits == []
    assert "expired" in message.edits[-1]["content"]


@pytest.mark.asyncio
async def test_real_timeout_cancels_slow_page_navigation_before_edit() -> None:
    option = _option(111, name="Main Gov")
    accounts_started = asyncio.Event()
    release_accounts = asyncio.Event()

    async def accounts_loader(_user_id: int):
        accounts_started.set()
        await release_accounts.wait()
        raise AssertionError("timed-out navigation must cancel the Accounts load")

    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=_selected_resolution(option),
        accounts_loader=accounts_loader,
        timeout=0.01,
    )
    interaction = _Interaction()
    message = _EditableMessage()
    view.set_message_ref(message)
    view._start_listening_from_store(SimpleNamespace(remove_view=lambda _view: None))

    navigation_task = asyncio.create_task(view.open_page(interaction, "accounts"))
    await accounts_started.wait()
    await asyncio.sleep(0.05)
    release_accounts.set()
    await navigation_task

    assert view._timed_out is True
    assert interaction.original_edits == []
    assert "expired" in message.edits[-1]["content"]


@pytest.mark.asyncio
async def test_real_timeout_cancels_slow_pagination_before_replacement() -> None:
    options = tuple(_option(100 + index, account_type=f"Farm {index}") for index in range(26))
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=GovernorDashboardResolution(state="requires_selection", options=options),
        timeout=0.01,
    )
    interaction = _Interaction()
    message = _EditableMessage()
    view.set_message_ref(message)
    view._start_listening_from_store(SimpleNamespace(remove_view=lambda _view: None))
    edit_started = asyncio.Event()

    async def slow_edit(**_kwargs):
        edit_started.set()
        await asyncio.Event().wait()

    interaction.response.edit_message = slow_edit
    pagination_task = asyncio.create_task(view.next_selector_page(interaction))
    await edit_started.wait()
    await asyncio.sleep(0.05)
    await pagination_task

    assert view._timed_out is True
    assert interaction.response.edited == []
    assert interaction.followup.sent == []
    assert "expired" in message.edits[-1]["content"]


@pytest.mark.asyncio
async def test_real_timeout_cancels_blocked_terminal_dashboard_edit() -> None:
    main = _option(111, name="Main Gov", is_default=True)
    alt = _option(222, name="Alt Gov", account_type="Alt 1")
    selected = _selected_resolution(alt, options=(main, alt))
    edit_started = asyncio.Event()

    async def resolver(_user_id: int, _governor_id: str, **_kwargs):
        return selected

    async def payload_loader(context):
        return _payload(context)

    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=GovernorDashboardResolution(state="requires_selection", options=(main, alt)),
        context_resolver=resolver,
        payload_loader=payload_loader,
        timeout=0.01,
    )
    interaction = _Interaction()
    message = _EditableMessage()
    view.set_message_ref(message)
    view._start_listening_from_store(SimpleNamespace(remove_view=lambda _view: None))

    async def slow_edit(**_kwargs):
        edit_started.set()
        await asyncio.Event().wait()

    interaction.edit_original_response = slow_edit
    selection_task = asyncio.create_task(view.select_governor(interaction, "222"))
    await edit_started.wait()
    await asyncio.sleep(0.05)
    await selection_task

    assert view._timed_out is True
    assert interaction.original_edits == []
    assert interaction.followup.sent == []
    assert "expired" in message.edits[-1]["content"]


@pytest.mark.asyncio
async def test_real_timeout_cancels_blocked_dashboard_fallback_send() -> None:
    main = _option(111, name="Main Gov", is_default=True)
    alt = _option(222, name="Alt Gov", account_type="Alt 1")
    selected = _selected_resolution(alt, options=(main, alt))
    fallback_started = asyncio.Event()

    async def resolver(_user_id: int, _governor_id: str, **_kwargs):
        return selected

    async def payload_loader(context):
        return _payload(context)

    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=GovernorDashboardResolution(state="requires_selection", options=(main, alt)),
        context_resolver=resolver,
        payload_loader=payload_loader,
        timeout=0.01,
    )
    interaction = _Interaction()
    message = _EditableMessage()
    view.set_message_ref(message)
    view._start_listening_from_store(SimpleNamespace(remove_view=lambda _view: None))

    async def broken_edit(**_kwargs):
        raise RuntimeError("original response missing")

    async def slow_fallback(*_args, **_kwargs):
        fallback_started.set()
        await asyncio.Event().wait()

    interaction.edit_original_response = broken_edit
    interaction.followup.send = slow_fallback
    selection_task = asyncio.create_task(view.select_governor(interaction, "222"))
    await fallback_started.wait()
    await asyncio.sleep(0.05)
    await selection_task

    assert view._timed_out is True
    assert interaction.original_edits == []
    assert interaction.followup.sent == []
    assert "expired" in message.edits[-1]["content"]


@pytest.mark.asyncio
async def test_real_timeout_cancels_blocked_pagination_fallback_send() -> None:
    options = tuple(_option(100 + index, account_type=f"Farm {index}") for index in range(26))
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=GovernorDashboardResolution(state="requires_selection", options=options),
        timeout=0.01,
    )
    interaction = _Interaction()
    message = _EditableMessage()
    view.set_message_ref(message)
    view._start_listening_from_store(SimpleNamespace(remove_view=lambda _view: None))
    fallback_started = asyncio.Event()

    async def broken_edit(**_kwargs):
        raise RuntimeError("component message missing")

    async def slow_fallback(*_args, **_kwargs):
        fallback_started.set()
        await asyncio.Event().wait()

    interaction.response.edit_message = broken_edit
    interaction.followup.send = slow_fallback
    pagination_task = asyncio.create_task(view.next_selector_page(interaction))
    await fallback_started.wait()
    await asyncio.sleep(0.05)
    await pagination_task

    assert view._timed_out is True
    assert interaction.response.edited == []
    assert interaction.followup.sent == []
    assert "expired" in message.edits[-1]["content"]


@pytest.mark.asyncio
async def test_selector_supports_more_than_twenty_five_linked_governors() -> None:
    options = tuple(
        _option(
            100 + index,
            account_type="Main" if index == 0 else f"Farm {index}",
            is_default=index == 0,
        )
        for index in range(26)
    )
    resolution = GovernorDashboardResolution(state="requires_selection", options=options)

    first = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=resolution,
    )
    selector = next(child for child in first.children if isinstance(child, discord.ui.Select))

    assert len(selector.options) == 25
    assert "me:dashboard:selector:next" in _custom_ids(first)


@pytest.mark.asyncio
async def test_selected_change_dropdown_pages_without_replacing_card_attachment() -> None:
    options = tuple(
        _option(100 + index, account_type="Main" if index == 0 else f"Farm {index}")
        for index in range(26)
    )
    resolution = _selected_resolution(options[25], options=options)
    view = views.GovernorDashboardView(
        author_id=42,
        display_name="Tester",
        resolution=resolution,
    )
    selector = next(child for child in view.children if isinstance(child, discord.ui.Select))

    assert view.selector_page == 1
    assert [option.value for option in selector.options] == ["125"]
    assert "me:dashboard:change:previous" in _custom_ids(view)

    interaction = _Interaction()
    await view.previous_selector_page(interaction)

    assert interaction.response.edited
    edit_kwargs = interaction.response.edited[-1]
    assert set(edit_kwargs) == {"view"}
    replacement = edit_kwargs["view"]
    replacement_selector = next(
        child for child in replacement.children if isinstance(child, discord.ui.Select)
    )
    assert replacement.selector_page == 0
    assert len(replacement_selector.options) == 25
