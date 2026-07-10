from __future__ import annotations

import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest

from inventory.models import InventoryReportVisibility
from player_self_service.account_service import (
    AccountCentreState,
    AccountConfirmation,
    AccountMutationResult,
)
from player_self_service.preference_service import PreferenceMutationResult
from player_self_service.profile_preference_service import (
    UserProfilePreference,
    UserProfilePreferenceMutationResult,
    UserProfilePreferenceRead,
)
from player_self_service.reminder_service import (
    ReminderCentreState,
    ReminderMessage,
    ReminderMutationResult,
    ReminderUnsubscribeConfirmation,
)
from player_self_service.service import (
    AccountStatus,
    ExportStatus,
    InventoryCategoryStatus,
    InventoryStatus,
    PlayerSelfServiceSummary,
    PreferenceStatus,
    ReminderStatus,
)
from ui.views import (
    player_self_service_account_views as account_views,
    player_self_service_governor_dashboard_views as governor_dashboard_views,
    player_self_service_preference_views as preference_views,
    player_self_service_reminder_views as reminder_views,
    player_self_service_views as views,
)


def _summary() -> PlayerSelfServiceSummary:
    return PlayerSelfServiceSummary(
        discord_user_id=42,
        accounts=AccountStatus(
            state="single",
            linked_count=1,
            linked_label="1 linked",
            main_state="set",
            main_label="Main Gov (111)",
            next_action="Review",
            account_names=("Main Gov",),
        ),
        reminders=ReminderStatus(
            state="on",
            event_summary="all KVK events",
            time_summary="24h, 4h, 1h",
            next_action="Manage",
        ),
        preferences=PreferenceStatus(
            inventory_visibility="private",
            exports_summary="available through private export tools",
            next_action="Review preferences",
            timezone="Europe/London",
            location_country="United Kingdom (GB)",
            preferred_language="English (en-GB)",
        ),
        exports=ExportStatus(
            stats_export="Excel / CSV / Google Sheets",
            inventory_export="Excel / CSV / Google Sheets",
            privacy_note="Private",
        ),
        inventory=InventoryStatus(
            state="available",
            account_summary="1 registered governor(s) with complete approved inventory data.",
            resources=InventoryCategoryStatus(
                state="available",
                value="1.2B RSS",
                detail="1/1 governors | latest 2026-06-25",
                governor_count=1,
                latest_scan_label="2026-06-25",
            ),
            speedups=InventoryCategoryStatus(
                state="available",
                value="365d total",
                detail="1/1 governors | latest 2026-06-25",
                governor_count=1,
                latest_scan_label="2026-06-25",
            ),
            materials=InventoryCategoryStatus(
                state="available",
                value="42 legendary",
                detail="1/1 governors | latest 2026-06-25",
                governor_count=1,
                latest_scan_label="2026-06-25",
            ),
            upload_guidance="Use `/inventory import` in the inventory upload channel.",
        ),
    )


def _no_account_summary() -> PlayerSelfServiceSummary:
    summary = _summary()
    return PlayerSelfServiceSummary(
        discord_user_id=summary.discord_user_id,
        accounts=AccountStatus(
            state="none",
            linked_count=0,
            linked_label="0 linked",
            main_state="not set",
            main_label="not set",
            next_action="Register",
        ),
        reminders=summary.reminders,
        preferences=summary.preferences,
        exports=ExportStatus(
            stats_export="Unavailable",
            inventory_export="Unavailable",
            privacy_note="Private",
            action_state="unavailable",
            action_summary="Register an account first.",
        ),
    )


class _Response:
    def __init__(self) -> None:
        self.sent = []
        self.edited = []
        self.deferred = []
        self.modals = []
        self._done = False

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        self._done = True

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)
        self._done = True

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True

    async def send_modal(self, modal):
        self.modals.append(modal)
        self._done = True

    def is_done(self):
        return self._done


class _Followup:
    def __init__(self) -> None:
        self.sent = []
        self.edited = []

    async def send(self, *args, **kwargs):
        message = SimpleNamespace(edits=[])
        self.sent.append((args, kwargs, message))
        return message

    async def edit_message(self, message_id, **kwargs):
        self.edited.append((message_id, kwargs))
        return SimpleNamespace(id=message_id)


class _Interaction:
    def __init__(self, user_id: int = 42) -> None:
        self.user = _User(user_id)
        self.response = _Response()
        self.followup = _Followup()
        self.message = SimpleNamespace(id=123, edits=[])
        self.original_edits = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return SimpleNamespace(id=456)


class _EditableMessage:
    def __init__(self) -> None:
        self.id = 789
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)
        return self


class _User:
    def __init__(self, user_id: int = 42) -> None:
        self.id = user_id
        self.sent = []

    def __str__(self) -> str:
        return f"user-{self.id}"

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        return None


def test_dashboard_embed_is_status_first_and_compact() -> None:
    embed = views.build_dashboard_embed(_summary(), display_name="Tester")

    assert embed.title == "K98 Personal Command Centre"
    assert len(embed.fields) == 3
    assert [field.name for field in embed.fields] == ["Accounts", "Reminders", "Preferences"]
    assert "Next action: Review" in embed.fields[0].value
    assert "/register_governor" not in embed.fields[0].value


@pytest.mark.asyncio
async def test_dashboard_page_response_includes_generated_card(monkeypatch) -> None:
    calls = []

    def fake_render(summary, *, display_name):
        calls.append((summary.discord_user_id, display_name))
        return views.dashboard_card.RenderedDashboardCard(
            filename="me_dashboard_42.png",
            image_bytes=BytesIO(b"png"),
        )

    monkeypatch.setattr(views.dashboard_card, "render_dashboard_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_DASHBOARD,
        _summary(),
        display_name="Tester",
    )

    assert calls == [(42, "Tester")]
    assert embed.title is None
    assert embed.fields == []
    assert embed.image.url == "attachment://me_dashboard_42.png"
    assert [file.filename for file in files] == ["me_dashboard_42.png"]


@pytest.mark.asyncio
async def test_dashboard_page_response_falls_back_to_embed_when_card_render_fails(
    monkeypatch,
) -> None:
    def fake_render(*_args, **_kwargs):
        raise RuntimeError("no pillow today")

    monkeypatch.setattr(views.dashboard_card, "render_dashboard_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_DASHBOARD,
        _summary(),
        display_name="Tester",
    )

    assert embed.title == "K98 Personal Command Centre"
    assert files == []
    assert getattr(embed.image, "url", None) is None


@pytest.mark.asyncio
async def test_subpage_response_includes_generated_card(monkeypatch) -> None:
    calls = []

    def fake_render(page, summary, *, display_name):
        calls.append((page, summary.discord_user_id, display_name))
        return views.page_cards.RenderedPageCard(
            filename="me_accounts_42.png",
            image_bytes=BytesIO(b"png"),
        )

    monkeypatch.setattr(views.page_cards, "render_page_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_ACCOUNTS,
        _summary(),
        display_name="Tester",
    )

    assert calls == [(views.PAGE_ACCOUNTS, 42, "Tester")]
    assert embed.title is None
    assert embed.fields == []
    assert embed.image.url == "attachment://me_accounts_42.png"
    assert [file.filename for file in files] == ["me_accounts_42.png"]


@pytest.mark.asyncio
async def test_subpage_response_falls_back_to_embed_when_card_render_fails(monkeypatch) -> None:
    def fake_render(*_args, **_kwargs):
        raise RuntimeError("asset unavailable")

    monkeypatch.setattr(views.page_cards, "render_page_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_REMINDERS,
        _summary(),
        display_name="Tester",
    )

    assert embed.title == "Reminder Centre"
    assert files == []
    assert getattr(embed.image, "url", None) is None


@pytest.mark.asyncio
async def test_dashboard_page_response_propagates_card_render_cancellation(
    monkeypatch,
) -> None:
    def fake_render(*_args, **_kwargs):
        raise asyncio.CancelledError()

    monkeypatch.setattr(views.dashboard_card, "render_dashboard_card", fake_render)

    with pytest.raises(asyncio.CancelledError):
        await views._build_page_response(
            views.PAGE_DASHBOARD,
            _summary(),
            display_name="Tester",
        )


@pytest.mark.asyncio
async def test_dashboard_image_send_failure_retries_embed_only() -> None:
    class Target:
        def __init__(self) -> None:
            self.calls = []

        async def edit_original_response(self, **kwargs):
            self.calls.append(kwargs)
            if kwargs.get("files"):
                raise RuntimeError("attachment rejected")
            return SimpleNamespace(id=999)

    embed = views.build_dashboard_embed(_summary(), display_name="Tester")
    embed.set_image(url="attachment://me_dashboard_42.png")
    target = Target()

    message = await views._edit_original_with_image_fallback(
        target,
        page=views.PAGE_DASHBOARD,
        summary=_summary(),
        display_name="Tester",
        view=views.PlayerSelfServiceView(author_id=42, display_name="Tester"),
        embed=embed,
        files=[SimpleNamespace(filename="me_dashboard_42.png")],
    )

    assert message.id == 999
    assert len(target.calls) == 2
    assert target.calls[0]["files"]
    assert "files" not in target.calls[1]
    assert getattr(target.calls[1]["embed"].image, "url", None) is None


@pytest.mark.asyncio
async def test_dashboard_image_send_cancellation_is_not_retried() -> None:
    class Target:
        async def edit_original_response(self, **_kwargs):
            raise asyncio.CancelledError()

    embed = views.build_dashboard_embed(_summary(), display_name="Tester")

    with pytest.raises(asyncio.CancelledError):
        await views._edit_original_with_image_fallback(
            Target(),
            page=views.PAGE_DASHBOARD,
            summary=_summary(),
            display_name="Tester",
            view=views.PlayerSelfServiceView(author_id=42, display_name="Tester"),
            embed=embed,
            files=[SimpleNamespace(filename="me_dashboard_42.png")],
        )


def test_accounts_embed_invites_service_backed_controls() -> None:
    embed = views.build_accounts_embed(_summary(), display_name="Tester")

    assert embed.title == "Account Centre"
    assert "Use Manage" in embed.fields[1].value
    assert "/modify_registration" not in embed.fields[1].value


def test_reminders_embed_invites_service_backed_controls() -> None:
    embed = views.build_reminders_embed(_summary(), display_name="Tester")

    assert embed.title == "Reminder Centre"
    assert "Manage auto-saves" in embed.fields[1].value
    assert "Manage Calendar Reminders" in embed.fields[1].value
    assert "/modify_subscription" not in embed.fields[1].value


def test_preferences_embed_invites_service_backed_visibility_controls() -> None:
    embed = views.build_preferences_embed(_summary(), display_name="Tester")

    assert embed.title == "Preferences"
    assert "VIP level" in embed.fields[0].value
    assert "Location: United Kingdom (GB)" in embed.fields[0].value
    assert "inventory reports are posted" in embed.fields[1].value
    assert "Manage Profile" in embed.fields[1].value
    assert "/inventory_preferences" not in embed.fields[1].value


def test_inventory_embed_summarizes_latest_approved_data() -> None:
    embed = views.build_inventory_embed(_summary(), display_name="Tester")

    assert embed.title == "Inventory"
    assert "Resources: 1.2B RSS" in embed.fields[0].value
    assert "Speedups: 365d total" in embed.fields[0].value
    assert "Materials: 42 legendary" in embed.fields[0].value
    assert "`/inventory import`" in embed.fields[1].value
    assert "Open Report" in embed.fields[2].value


@pytest.mark.asyncio
async def test_account_slot_select_view_preserves_twenty_sixth_slot() -> None:
    slots = tuple(f"Slot {index}" for index in range(1, 27))

    view = account_views.AccountSlotSelectView(
        author_id=42,
        display_name="Tester",
        action="replace",
        slots=slots,
    )

    selects = [
        child for child in view.children if isinstance(child, account_views.AccountSlotSelect)
    ]
    assert [len(select.options) for select in selects] == [25, 1]
    assert selects[-1].options[-1].value == "Slot 26"


@pytest.mark.asyncio
async def test_dashboard_view_has_primary_buttons_and_inventory_exports() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")

    labels = [getattr(child, "label", None) for child in view.children]
    assert labels[:3] == ["Accounts", "Reminders", "Preferences"]
    assert "Inventory" in labels
    assert "Exports" in labels
    assert "Dashboard" in labels
    assert "Quick launch" not in [getattr(child, "placeholder", None) for child in view.children]


def _style_name(child: object) -> str:
    style = getattr(child, "style", None)
    return str(getattr(style, "name", style))


def _button_layout(view: views.PlayerSelfServiceView) -> list[tuple[str, int, str, bool]]:
    return [
        (
            str(getattr(child, "label", "")),
            int(getattr(child, "row", 0) or 0),
            _style_name(child),
            bool(getattr(child, "disabled", False)),
        )
        for child in view.children
        if getattr(child, "custom_id", None)
    ]


def _assert_button_layout(
    page: str,
    expected: list[tuple[str, int, str, bool]],
) -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=page,
        summary=_summary(),
    )

    assert _button_layout(view) == expected


@pytest.mark.asyncio
async def test_player_self_service_button_layout_is_consistent() -> None:
    primary = "primary"
    secondary = "secondary"
    success = "success"

    top_row = [
        ("Accounts", 0, primary, False),
        ("Reminders", 0, primary, False),
        ("Preferences", 0, primary, False),
    ]
    nav_row = [
        ("Dashboard", 1, secondary, False),
        ("Inventory", 1, secondary, False),
        ("Exports", 1, secondary, False),
    ]

    _assert_button_layout(
        views.PAGE_DASHBOARD,
        [
            *top_row,
            ("Dashboard", 1, secondary, True),
            ("Inventory", 1, secondary, False),
            ("Exports", 1, secondary, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_ACCOUNTS,
        [
            ("Accounts", 0, primary, True),
            ("Reminders", 0, primary, False),
            ("Preferences", 0, primary, False),
            *nav_row,
            ("Manage", 2, success, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_REMINDERS,
        [
            ("Accounts", 0, primary, False),
            ("Reminders", 0, primary, True),
            ("Preferences", 0, primary, False),
            *nav_row,
            ("Manage", 2, success, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_PREFERENCES,
        [
            ("Accounts", 0, primary, False),
            ("Reminders", 0, primary, False),
            ("Preferences", 0, primary, True),
            *nav_row,
            ("Set Public", 2, success, False),
            ("Update VIP", 2, success, False),
            ("Manage Profile", 2, success, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_INVENTORY,
        [
            *top_row,
            ("Dashboard", 1, secondary, False),
            ("Inventory", 1, secondary, True),
            ("Exports", 1, secondary, False),
            ("Open Report", 2, success, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_EXPORTS,
        [
            *top_row,
            ("Dashboard", 1, secondary, False),
            ("Inventory", 1, secondary, False),
            ("Exports", 1, secondary, True),
            ("Export Stats", 2, success, False),
            ("Export Inventory", 2, success, False),
        ],
    )


@pytest.mark.asyncio
async def test_accounts_view_keeps_inventory_and_exports_navigation() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_ACCOUNTS,
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage" in labels
    assert not {"Find ID", "Register", "Replace", "Remove"}.intersection(set(labels))
    assert "Inventory" in labels
    assert "Exports" in labels


@pytest.mark.asyncio
async def test_reminders_view_keeps_inventory_and_exports_navigation() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_REMINDERS,
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage" in labels
    assert "Unsubscribe" not in labels
    assert "Register" not in labels
    assert "Inventory" in labels
    assert "Exports" in labels


@pytest.mark.asyncio
async def test_exports_view_has_inventory_navigation_and_option_entry_actions() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_EXPORTS,
        summary=_summary(),
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Export Stats" in labels
    assert "Export Inventory" in labels
    assert "Inventory" in labels
    assert "Exports" in labels
    exports_nav = next(
        child for child in view.children if getattr(child, "custom_id", None) == "me:exports"
    )
    assert exports_nav.disabled is True


@pytest.mark.asyncio
async def test_exports_view_disables_export_actions_when_unavailable() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_EXPORTS,
        summary=_no_account_summary(),
    )

    export_buttons = [
        child
        for child in view.children
        if str(getattr(child, "custom_id", "") or "").startswith("me:export:")
    ]
    assert export_buttons
    assert all(child.disabled for child in export_buttons)


@pytest.mark.asyncio
async def test_exports_stats_button_opens_options(monkeypatch) -> None:
    calls = []

    async def fake_send_stats_export_options(interaction, *, display_name):
        calls.append((interaction.user.id, display_name))

    monkeypatch.setattr(
        views.export_views,
        "send_stats_export_options",
        fake_send_stats_export_options,
    )
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_EXPORTS,
        summary=_summary(),
    )
    interaction = _Interaction()
    button = next(
        child for child in view.children if getattr(child, "custom_id", None) == "me:export:stats"
    )

    await button.callback(interaction)

    assert calls == [(42, "Tester")]


@pytest.mark.asyncio
async def test_exports_inventory_button_opens_options(monkeypatch) -> None:
    calls = []

    async def fake_send_inventory_export_options(interaction, *, display_name):
        calls.append((interaction.user.id, display_name))

    monkeypatch.setattr(
        views.export_views,
        "send_inventory_export_options",
        fake_send_inventory_export_options,
    )
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_EXPORTS,
        summary=_summary(),
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:export:inventory"
    )

    await button.callback(interaction)

    assert calls == [(42, "Tester")]


@pytest.mark.asyncio
async def test_dashboard_inventory_button_opens_inventory_page() -> None:
    async def loader(_user_id: int):
        return _summary()

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()
    button = next(
        child for child in view.children if getattr(child, "custom_id", None) == "me:inventory"
    )

    await button.callback(interaction)

    edited = interaction.original_edits[-1]
    assert interaction.response.deferred == [{"ephemeral": True}]
    assert edited["embed"].image.url.startswith("attachment://me_inventory_")
    assert [file.filename for file in edited["files"]] == ["me_inventory_42.png"]
    assert isinstance(edited["view"], views.PlayerSelfServiceView)


@pytest.mark.asyncio
async def test_inventory_report_button_uses_existing_inventory_selector(monkeypatch) -> None:
    calls = []

    async def fake_visibility(user_id):
        calls.append(("visibility", user_id))
        return InventoryReportVisibility.ONLY_ME

    async def fake_start_myinventory_command(*, ctx, visibility):
        calls.append(("inventory", ctx.user.id, visibility))

    monkeypatch.setattr(
        views.reporting_service,
        "get_visibility_preference_or_none",
        fake_visibility,
    )
    monkeypatch.setattr(
        views,
        "start_myinventory_command",
        fake_start_myinventory_command,
    )
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_INVENTORY,
        summary=_summary(),
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:inventory:report"
    )

    await button.callback(interaction)

    assert interaction.response.deferred == [{"ephemeral": True}]
    assert calls == [
        ("visibility", 42),
        ("inventory", 42, InventoryReportVisibility.ONLY_ME),
    ]


@pytest.mark.asyncio
async def test_reminder_setup_view_includes_calendar_management() -> None:
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )

    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage Calendar Reminders" in labels
    assert "Remove All" in labels
    manage_calendar = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:manage_calendar"
    )
    remove_all = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:remove_all"
    )
    assert manage_calendar.row == 2
    assert remove_all.row == 2


@pytest.mark.asyncio
async def test_reminder_setup_switches_to_calendar_management(monkeypatch) -> None:
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )

    monkeypatch.setattr(
        reminder_views.reminder_config_service,
        "known_calendar_event_types",
        lambda: ("raid",),
    )
    monkeypatch.setattr(
        reminder_views,
        "get_user_prefs",
        lambda _user_id: {"enabled": True, "by_event_type": {"raid": ["24h"]}},
    )

    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:manage_calendar"
    )

    await button.callback(interaction)

    edited = interaction.original_edits[-1]
    assert isinstance(edited["view"], reminder_views.CalendarReminderSetupView)
    assert "calendar reminder" in edited["content"]
    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_calendar_management_autosaves_and_can_switch_back(monkeypatch) -> None:
    calls = []

    def fake_save(user_id, **kwargs):
        calls.append((user_id, kwargs))
        return reminder_views.reminder_config_service.CalendarReminderMutationResult(
            ok=True,
            message="saved",
            state=reminder_views.reminder_config_service.CalendarReminderConfigState(
                enabled=True,
                selected_types=("raid",),
                selected_offsets=("24h",),
            ),
        )

    async def fake_state(_user_id):
        return ReminderCentreState(
            ok=True,
            subscribed=True,
            event_types=("ruins",),
            reminder_times=("24h",),
            event_summary="ruins",
            time_summary="24h",
        )

    monkeypatch.setattr(
        reminder_views.reminder_config_service,
        "save_user_calendar_reminder_preferences",
        fake_save,
    )
    monkeypatch.setattr(reminder_views.reminder_service, "build_reminder_centre_state", fake_state)
    view = reminder_views.CalendarReminderSetupView(
        author_id=42,
        username="Tester",
        display_name="Tester",
        state=reminder_views.reminder_config_service.CalendarReminderConfigState(
            enabled=False,
            selected_types=(),
            selected_offsets=(),
        ),
        known_event_types=("raid",),
    )
    select = next(
        child
        for child in view.children
        if isinstance(child, reminder_views.CalendarReminderEventSelect)
    )
    select._selected_values = ["raid"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    assert calls[0][0] == 42
    assert calls[0][1]["enabled"] is True
    assert calls[0][1]["selected_types"] == ["raid"]
    assert tuple(calls[0][1]["selected_offsets"]) == ("7d", "3d", "24h", "1h", "start")
    assert interaction.original_edits[-1]["view"] is view

    switch_button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:manage_kvk"
    )
    switch_interaction = _Interaction()

    await switch_button.callback(switch_interaction)

    assert isinstance(
        switch_interaction.original_edits[-1]["view"], reminder_views.ReminderSetupView
    )


@pytest.mark.asyncio
async def test_calendar_management_remove_all_uses_service(monkeypatch) -> None:
    calls = []

    def fake_clear(user_id):
        calls.append(user_id)
        return reminder_views.reminder_config_service.CalendarReminderMutationResult(
            ok=True,
            message="removed",
            state=reminder_views.reminder_config_service.CalendarReminderConfigState(
                enabled=False,
                selected_types=(),
                selected_offsets=(),
            ),
        )

    monkeypatch.setattr(
        reminder_views.reminder_config_service,
        "clear_user_calendar_reminder_preferences",
        fake_clear,
    )
    view = reminder_views.CalendarReminderSetupView(
        author_id=42,
        username="Tester",
        display_name="Tester",
        state=reminder_views.reminder_config_service.CalendarReminderConfigState(
            enabled=True,
            selected_types=("all",),
            selected_offsets=("24h",),
        ),
        known_event_types=("raid",),
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:calendar_remove_all"
    )

    await button.callback(interaction)

    assert calls == [42]
    assert view.selected_types == []
    assert interaction.original_edits[-1]["content"] == "Calendar reminders removed."
    assert interaction.original_edits[-1]["view"] is view


@pytest.mark.asyncio
async def test_preferences_view_keeps_inventory_and_exports_navigation() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        summary=_summary(),
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert {"Set Public", "Update VIP", "Manage Profile"}.issubset(set(labels))
    assert "Set Private" not in labels
    assert "Inventory" in labels
    assert "Exports" in labels


@pytest.mark.asyncio
async def test_view_rejects_non_owner() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")
    interaction = _Interaction(user_id=99)

    assert await view.interaction_check(interaction) is False
    assert interaction.response.sent[-1][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_account_manage_button_opens_guided_menu(monkeypatch) -> None:
    async def fake_state(_user_id: int):
        return AccountCentreState(
            ok=True,
            linked_count=0,
            main_label="not set",
            registered_slots=(),
            free_slots=("Main", "Alt 1"),
        )

    monkeypatch.setattr(views.account_service, "build_account_centre_state", fake_state)

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_ACCOUNTS,
    )
    interaction = _Interaction()
    button = next(
        child for child in view.children if getattr(child, "custom_id", None) == "me:account:manage"
    )

    await button.callback(interaction)

    _args, kwargs, _message = interaction.followup.sent[-1]
    manage_view = kwargs["view"]
    assert kwargs["ephemeral"] is True
    assert isinstance(manage_view, account_views.AccountManageView)
    select = next(
        child
        for child in manage_view.children
        if isinstance(child, account_views.AccountManageActionSelect)
    )
    assert [option.value for option in select.options] == ["lookup", "register"]


@pytest.mark.asyncio
async def test_account_manage_register_selection_opens_free_slot_selector() -> None:
    state = AccountCentreState(
        ok=True,
        linked_count=0,
        main_label="not set",
        registered_slots=(),
        free_slots=("Main", "Alt 1"),
    )
    view = account_views.AccountManageView(author_id=42, display_name="Tester", state=state)
    select = next(
        child
        for child in view.children
        if isinstance(child, account_views.AccountManageActionSelect)
    )
    select._selected_values = ["register"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    _args, kwargs, _message = interaction.followup.sent[-1]
    slot_view = kwargs["view"]
    assert isinstance(slot_view, account_views.AccountSlotSelectView)
    slot_select = next(
        child for child in slot_view.children if isinstance(child, account_views.AccountSlotSelect)
    )
    assert [option.value for option in slot_select.options] == ["Main", "Alt 1"]


@pytest.mark.asyncio
async def test_account_lookup_result_register_carries_governor_id(monkeypatch) -> None:
    async def fake_state(_user_id: int):
        return AccountCentreState(
            ok=True,
            linked_count=0,
            main_label="not set",
            registered_slots=(),
            free_slots=("Main",),
        )

    async def fake_prepare(_user_id, _slot, _governor_query):
        return (
            AccountConfirmation(
                action="register",
                account_type="Main",
                governor_id="123456789",
                governor_name="FoundGov",
            ),
            None,
        )

    monkeypatch.setattr(account_views.account_service, "build_account_centre_state", fake_state)
    monkeypatch.setattr(
        account_views.account_service,
        "prepare_register_confirmation",
        fake_prepare,
    )
    view = account_views.AccountLookupResultActionView(
        author_id=42,
        display_name="Tester",
        governor_id="123456789",
        governor_name="FoundGov",
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:account:lookup:register"
    )

    await button.callback(interaction)

    _args, kwargs, _message = interaction.followup.sent[-1]
    slot_view = kwargs["view"]
    assert isinstance(slot_view, account_views.AccountSlotSelectView)
    assert slot_view.governor_query == "123456789"


@pytest.mark.asyncio
async def test_account_lookup_result_register_rejects_duplicate_before_slot_picker(
    monkeypatch,
) -> None:
    async def fake_state(_user_id: int):
        return AccountCentreState(
            ok=True,
            linked_count=1,
            main_label="Main Gov (123456789)",
            registered_slots=(),
            free_slots=("Alt 1",),
        )

    async def fake_prepare(_user_id, _slot, _governor_query):
        return None, (
            "That Governor ID is already linked to your account centre as "
            "Main: Main Gov (123456789)."
        )

    monkeypatch.setattr(account_views.account_service, "build_account_centre_state", fake_state)
    monkeypatch.setattr(
        account_views.account_service,
        "prepare_register_confirmation",
        fake_prepare,
    )
    view = account_views.AccountLookupResultActionView(
        author_id=42,
        display_name="Tester",
        governor_id="123456789",
        governor_name="Main Gov",
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:account:lookup:register"
    )

    await button.callback(interaction)

    args, kwargs, _message = interaction.followup.sent[-1]
    assert "already linked" in args[0]
    assert "Main Gov" in args[0]
    assert "view" not in kwargs


@pytest.mark.asyncio
async def test_account_confirmation_refreshes_visible_account_card(monkeypatch) -> None:
    async def fake_confirm(_user_id, _discord_name, _confirmation):
        return AccountMutationResult(ok=True, message="Registered Main as FoundGov (123456789).")

    async def loader(_user_id: int):
        return _summary()

    monkeypatch.setattr(account_views.account_service, "confirm_register", fake_confirm)
    host_message = _EditableMessage()
    view = account_views.AccountConfirmationView(
        author_id=42,
        display_name="Tester",
        confirmation=AccountConfirmation(
            action="register",
            account_type="Main",
            governor_id="123456789",
            governor_name="FoundGov",
        ),
        host_message=host_message,
        summary_loader=loader,
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:account:confirm"
    )

    await button.callback(interaction)

    assert host_message.edits[-1]["embed"].image.url.startswith("attachment://me_accounts_")
    assert [file.filename for file in host_message.edits[-1]["files"]] == ["me_accounts_42.png"]


@pytest.mark.asyncio
async def test_reminder_manage_button_opens_selector_with_existing_state(monkeypatch) -> None:
    async def fake_state(_user_id: int):
        return ReminderCentreState(
            ok=True,
            subscribed=True,
            event_types=("all",),
            reminder_times=("24h", "1h"),
            event_summary="all KVK events",
            time_summary="24h, 1h",
        )

    monkeypatch.setattr(views.reminder_service, "build_reminder_centre_state", fake_state)

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_REMINDERS,
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:manage"
    )

    await button.callback(interaction)

    _args, kwargs, _message = interaction.followup.sent[-1]
    setup_view = kwargs["view"]
    assert kwargs["ephemeral"] is True
    assert isinstance(setup_view, reminder_views.ReminderSetupView)
    assert setup_view.selected_types == ["all"]
    assert setup_view.selected_reminders == ["24h", "1h"]
    assert any(
        getattr(child, "custom_id", None) == "me:reminder:remove_all"
        for child in setup_view.children
    )


@pytest.mark.asyncio
async def test_preference_visibility_toggle_saves_opposite_visibility_and_refreshes(
    monkeypatch,
) -> None:
    calls = []

    async def fake_save(user_id: int, visibility: InventoryReportVisibility):
        calls.append((user_id, visibility))
        return PreferenceMutationResult(
            ok=True,
            message="Inventory report visibility saved as public.",
            inventory_visibility="public",
        )

    async def loader(user_id: int):
        assert user_id == 42
        return _summary()

    monkeypatch.setattr(views.preference_service, "save_inventory_visibility", fake_save)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        summary=_summary(),
        summary_loader=loader,
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:preference:visibility"
    )

    await button.callback(interaction)

    assert calls == [(42, InventoryReportVisibility.PUBLIC)]
    args, kwargs, _message = interaction.followup.sent[-1]
    assert "saved as public" in args[0]
    assert kwargs["ephemeral"] is True
    assert interaction.original_edits[-1]["embed"].image.url.startswith(
        "attachment://me_preferences_"
    )
    assert isinstance(interaction.original_edits[-1]["view"], views.PlayerSelfServiceView)


@pytest.mark.asyncio
async def test_preference_vip_button_reuses_inventory_vip_prompt(monkeypatch) -> None:
    calls = []

    async def fake_prompt(*, interaction, requester_id):
        calls.append((interaction, requester_id))
        await interaction.followup.send("Choose a governor and VIP level:", ephemeral=True)

    monkeypatch.setattr(views, "send_inventory_vip_preference_prompt", fake_prompt)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
    )
    interaction = _Interaction()
    button = next(
        child for child in view.children if getattr(child, "custom_id", None) == "me:preference:vip"
    )

    await button.callback(interaction)

    assert calls == [(interaction, 42)]
    assert interaction.followup.sent[-1][0][0] == "Choose a governor and VIP level:"


@pytest.mark.asyncio
async def test_preference_profile_button_opens_private_profile_manager(monkeypatch) -> None:
    async def fake_read(user_id: int):
        assert user_id == 42
        return UserProfilePreferenceRead(
            ok=True,
            profile=UserProfilePreference(
                timezone_name="Europe/London",
                location_country_code="GB",
                preferred_language_tag="en-GB",
            ),
        )

    monkeypatch.setattr(
        views.profile_preference_service,
        "read_user_profile_preference",
        fake_read,
    )
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        summary=_summary(),
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:preference:profile"
    )

    await button.callback(interaction)

    args, kwargs, _message = interaction.followup.sent[-1]
    assert "United Kingdom (GB)" in args[0]
    assert kwargs["ephemeral"] is True
    assert isinstance(kwargs["view"], preference_views.ProfilePreferenceManageView)


@pytest.mark.asyncio
async def test_profile_preference_select_rejects_invalid_country(monkeypatch) -> None:
    async def fake_set(*_args, **_kwargs):
        return UserProfilePreferenceMutationResult(
            ok=False,
            message="Location country was not recognised.",
        )

    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "set_profile_preference",
        fake_set,
    )
    view = preference_views.ProfilePreferenceManageView(
        author_id=42,
        display_name="Tester",
        profile=UserProfilePreference(),
    )
    select = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:preference:profile:select_country"
    )
    select._selected_values = ["Atlantis"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    assert interaction.followup.sent == []
    assert interaction.original_edits[-1]["content"] == "Location country was not recognised."
    assert isinstance(
        interaction.original_edits[-1]["view"],
        preference_views.ProfilePreferenceManageView,
    )


@pytest.mark.asyncio
async def test_profile_preference_manager_rejects_missing_user(monkeypatch) -> None:
    async def fake_set(*_args, **_kwargs):
        raise AssertionError("profile mutation should not run without an interaction user")

    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "set_profile_preference",
        fake_set,
    )
    view = preference_views.ProfilePreferenceManageView(
        author_id=42,
        display_name="Tester",
        profile=UserProfilePreference(),
    )
    interaction = _Interaction()
    interaction.user = None

    assert await view.interaction_check(interaction) is False

    args, kwargs = interaction.response.sent[-1]
    assert args[0] == "This private profile preference menu is not for you."
    assert kwargs["ephemeral"] is True
    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_profile_preference_select_saves_canonical_country(monkeypatch) -> None:
    calls = []

    async def fake_set(user_id: int, field: str, value: str):
        calls.append((user_id, field, value))
        return UserProfilePreferenceMutationResult(
            ok=True,
            message="Location country saved as Germany (DE).",
            profile=UserProfilePreference(location_country_code="DE"),
        )

    async def loader(_user_id: int):
        return _summary()

    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "set_profile_preference",
        fake_set,
    )
    host_message = _EditableMessage()
    view = preference_views.ProfilePreferenceManageView(
        author_id=42,
        display_name="Tester",
        profile=UserProfilePreference(),
        host_message=host_message,
        summary_loader=loader,
    )
    select = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:preference:profile:select_country"
    )
    select._selected_values = ["DE"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    assert calls == [(42, "country", "DE")]
    assert interaction.followup.sent == []
    assert interaction.original_edits[-1]["content"] == "Location country saved as Germany (DE)."
    assert isinstance(
        interaction.original_edits[-1]["view"],
        preference_views.ProfilePreferenceManageView,
    )
    assert interaction.followup.edited[-1][0] == host_message.id


@pytest.mark.asyncio
async def test_profile_preference_manager_uses_dropdowns_for_profile_values() -> None:
    view = preference_views.ProfilePreferenceManageView(
        author_id=42,
        display_name="Tester",
        profile=UserProfilePreference(
            timezone_name="Europe/London",
            location_country_code="GB",
            preferred_language_tag="en-GB",
        ),
    )

    selects = [
        child
        for child in view.children
        if isinstance(child, preference_views.ProfilePreferenceSelect)
    ]
    assert [select.field for select in selects] == ["timezone", "country", "language"]
    assert all(len(select.options) <= 25 for select in selects)
    assert {
        getattr(child, "custom_id", None)
        for child in view.children
        if getattr(child, "custom_id", None)
    }.isdisjoint(
        {
            "me:preference:profile:set_timezone",
            "me:preference:profile:set_country",
            "me:preference:profile:set_language",
        }
    )


@pytest.mark.asyncio
async def test_profile_preference_dropdown_keeps_current_value_outside_common_list() -> None:
    view = preference_views.ProfilePreferenceManageView(
        author_id=42,
        display_name="Tester",
        profile=UserProfilePreference(timezone_name="Pacific/Honolulu"),
    )
    select = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:preference:profile:select_timezone"
    )

    assert select.options[0].value == "Pacific/Honolulu"
    assert select.options[0].default is True
    assert len(select.options) <= 25


@pytest.mark.asyncio
async def test_profile_preference_clear_refreshes_host_card(monkeypatch) -> None:
    async def fake_clear(_user_id: int, field: str):
        assert field == "country"
        return UserProfilePreferenceMutationResult(
            ok=True,
            message="Location country removed.",
            profile=UserProfilePreference(timezone_name="Europe/London"),
        )

    async def loader(_user_id: int):
        return _summary()

    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "clear_profile_preference",
        fake_clear,
    )
    host_message = _EditableMessage()
    view = preference_views.ProfilePreferenceManageView(
        author_id=42,
        display_name="Tester",
        profile=UserProfilePreference(location_country_code="GB"),
        host_message=host_message,
        summary_loader=loader,
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:preference:profile:clear_country"
    )

    await button.callback(interaction)

    assert interaction.followup.sent == []
    assert interaction.original_edits[-1]["content"] == "Location country removed."
    assert isinstance(
        interaction.original_edits[-1]["view"],
        preference_views.ProfilePreferenceManageView,
    )
    assert interaction.followup.edited[-1][0] == host_message.id


@pytest.mark.asyncio
async def test_preference_visibility_defer_cancellation_propagates(monkeypatch) -> None:
    async def fake_save(*_args, **_kwargs):
        raise AssertionError("save should not run after cancelled defer")

    monkeypatch.setattr(views.preference_service, "save_inventory_visibility", fake_save)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
    )
    interaction = _Interaction()

    async def defer(**_kwargs):
        raise asyncio.CancelledError()

    interaction.response.defer = defer

    with pytest.raises(asyncio.CancelledError):
        await view._save_inventory_visibility(
            interaction,
            InventoryReportVisibility.PUBLIC,
        )

    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_preference_visibility_defer_fallback_cancellation_propagates(
    monkeypatch,
) -> None:
    async def fake_save(*_args, **_kwargs):
        raise AssertionError("save should not run after cancelled defer fallback")

    monkeypatch.setattr(views.preference_service, "save_inventory_visibility", fake_save)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
    )
    interaction = _Interaction()

    async def defer(**kwargs):
        if "ephemeral" in kwargs:
            raise TypeError("ephemeral is not supported")
        raise asyncio.CancelledError()

    interaction.response.defer = defer

    with pytest.raises(asyncio.CancelledError):
        await view._save_inventory_visibility(
            interaction,
            InventoryReportVisibility.PUBLIC,
        )

    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_preference_visibility_refresh_cancellation_propagates(monkeypatch) -> None:
    async def fake_save(_user_id: int, _visibility: InventoryReportVisibility):
        return PreferenceMutationResult(
            ok=True,
            message="Inventory report visibility saved as public.",
            inventory_visibility="public",
        )

    async def loader(_user_id: int):
        raise asyncio.CancelledError()

    monkeypatch.setattr(views.preference_service, "save_inventory_visibility", fake_save)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        summary_loader=loader,
    )
    interaction = _Interaction()

    with pytest.raises(asyncio.CancelledError):
        await view._save_inventory_visibility(
            interaction,
            InventoryReportVisibility.PUBLIC,
        )

    args, kwargs, _message = interaction.followup.sent[-1]
    assert "saved as public" in args[0]
    assert kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_preference_visibility_refresh_edit_cancellation_propagates(
    monkeypatch,
) -> None:
    async def fake_save(_user_id: int, _visibility: InventoryReportVisibility):
        return PreferenceMutationResult(
            ok=True,
            message="Inventory report visibility saved as public.",
            inventory_visibility="public",
        )

    async def loader(_user_id: int):
        return _summary()

    monkeypatch.setattr(views.preference_service, "save_inventory_visibility", fake_save)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        summary_loader=loader,
    )
    interaction = _Interaction()

    async def edit_original_response(**_kwargs):
        raise asyncio.CancelledError()

    interaction.edit_original_response = edit_original_response

    with pytest.raises(asyncio.CancelledError):
        await view._save_inventory_visibility(
            interaction,
            InventoryReportVisibility.PUBLIC,
        )


@pytest.mark.asyncio
async def test_reminder_event_select_refreshes_full_coverage_as_all(monkeypatch) -> None:
    async def fake_save(_user_id, _username, _selected_types, _selected_times):
        return ReminderMutationResult(
            ok=True,
            action="update",
            message="Updated reminders.",
            event_types=("all",),
            reminder_times=("24h",),
            dm_message=None,
        )

    monkeypatch.setattr(reminder_views.reminder_service, "save_reminder_preferences", fake_save)
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )
    select = next(
        child for child in view.children if isinstance(child, reminder_views.ReminderEventSelect)
    )
    select._selected_values = ["ruins", "altars", "major", "fights"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    assert view.selected_types == ["all"]
    assert interaction.original_edits[-1]["view"] is view
    defaults = {option.value: option.default for option in select.options}
    assert defaults == {
        "ruins": False,
        "altars": False,
        "major": False,
        "fights": False,
        "all": True,
    }


@pytest.mark.asyncio
async def test_reminder_event_select_keeps_major_with_fights(monkeypatch) -> None:
    async def fake_save(_user_id, _username, _selected_types, _selected_times):
        return ReminderMutationResult(
            ok=True,
            action="update",
            message="Updated reminders.",
            event_types=("major", "fights"),
            reminder_times=("24h",),
            dm_message=None,
        )

    monkeypatch.setattr(reminder_views.reminder_service, "save_reminder_preferences", fake_save)
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )
    select = next(
        child for child in view.children if isinstance(child, reminder_views.ReminderEventSelect)
    )
    select._selected_values = ["major", "fights"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    assert view.selected_types == ["major", "fights"]
    assert interaction.original_edits[-1]["view"] is view
    defaults = {option.value: option.default for option in select.options}
    assert defaults["major"] is True
    assert defaults["fights"] is True


@pytest.mark.asyncio
async def test_reminder_event_select_refreshes_altars_into_fights(monkeypatch) -> None:
    async def fake_save(_user_id, _username, _selected_types, _selected_times):
        return ReminderMutationResult(
            ok=True,
            action="update",
            message="Updated reminders.",
            event_types=("fights",),
            reminder_times=("24h",),
            dm_message=None,
        )

    monkeypatch.setattr(reminder_views.reminder_service, "save_reminder_preferences", fake_save)
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )
    select = next(
        child for child in view.children if isinstance(child, reminder_views.ReminderEventSelect)
    )
    select._selected_values = ["altars", "fights"]
    select._interaction = SimpleNamespace(data={})
    interaction = _Interaction()

    await select.callback(interaction)

    assert view.selected_types == ["fights"]
    assert interaction.original_edits[-1]["view"] is view
    defaults = {option.value: option.default for option in select.options}
    assert defaults["altars"] is False
    assert defaults["fights"] is True


@pytest.mark.asyncio
async def test_reminder_setup_disables_remove_all_when_unsubscribed() -> None:
    state = ReminderCentreState(
        ok=True,
        subscribed=False,
        event_types=(),
        reminder_times=(),
        event_summary="not subscribed",
        time_summary="not set",
    )
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )

    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:remove_all"
    )

    assert button.disabled is True


@pytest.mark.asyncio
async def test_reminder_setup_timeout_disables_child_controls() -> None:
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )
    edits = []

    class Message:
        async def edit(self, **kwargs):
            edits.append(kwargs)

    view.set_message_ref(Message())

    await view.on_timeout()

    assert all(child.disabled for child in view.children)
    assert "expired" in edits[-1]["content"]
    assert edits[-1]["view"] is view


@pytest.mark.asyncio
async def test_account_slot_select_rejects_non_owner() -> None:
    view = account_views.AccountSlotSelectView(
        author_id=42,
        display_name="Tester",
        action="register",
        slots=("Main",),
    )
    interaction = _Interaction(user_id=99)

    assert await view.interaction_check(interaction) is False
    assert interaction.response.sent[-1][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_reminder_setup_event_select_autosaves_and_sends_dm(monkeypatch) -> None:
    calls = []

    async def fake_save(user_id, username, selected_types, selected_times):
        calls.append((user_id, username, tuple(selected_types), tuple(selected_times)))
        return ReminderMutationResult(
            ok=True,
            action="update",
            message="Updated reminders.",
            event_types=("ruins",),
            reminder_times=("24h",),
            dm_message=ReminderMessage(
                title="Updated",
                description="Saved.",
                color=1,
                fields=(("Event Types", "ruins"),),
                footer="Done.",
            ),
        )

    monkeypatch.setattr(reminder_views.reminder_service, "save_reminder_preferences", fake_save)
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
    )
    interaction = _Interaction()
    select = next(
        child for child in view.children if isinstance(child, reminder_views.ReminderEventSelect)
    )
    select._selected_values = ["ruins"]
    select._interaction = SimpleNamespace(data={})

    await select.callback(interaction)

    assert calls == [(42, "Tester", ("ruins",), ("24h",))]
    assert interaction.user.sent
    edited = interaction.original_edits[-1]
    assert "Saved automatically" in edited["content"]
    assert "confirmation DM was sent" in edited["content"]
    assert isinstance(edited["view"], reminder_views.ReminderSetupView)
    assert all(getattr(child, "custom_id", None) != "me:reminder:save" for child in view.children)


@pytest.mark.asyncio
async def test_reminder_autosave_refreshes_visible_reminder_card(monkeypatch) -> None:
    async def fake_save(_user_id, _username, _selected_types, _selected_times):
        return ReminderMutationResult(
            ok=True,
            action="update",
            message="Updated reminders.",
            event_types=("ruins",),
            reminder_times=("24h",),
            dm_message=None,
        )

    async def loader(_user_id: int):
        return _summary()

    monkeypatch.setattr(reminder_views.reminder_service, "save_reminder_preferences", fake_save)
    state = ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=("ruins",),
        reminder_times=("24h",),
        event_summary="ruins",
        time_summary="24h",
    )
    host_message = _EditableMessage()
    view = reminder_views.ReminderSetupView(
        author_id=42,
        username="Tester",
        state=state,
        display_name="Tester",
        host_message=host_message,
        summary_loader=loader,
    )
    interaction = _Interaction()
    select = next(
        child for child in view.children if isinstance(child, reminder_views.ReminderTimeSelect)
    )
    select._selected_values = ["24h"]
    select._interaction = SimpleNamespace(data={})

    await select.callback(interaction)

    message_id, edit = interaction.followup.edited[-1]
    assert message_id == host_message.id
    assert edit["embed"].image.url.startswith("attachment://me_reminders_")
    assert [file.filename for file in edit["files"]] == ["me_reminders_42.png"]


@pytest.mark.asyncio
async def test_reminder_unsubscribe_failure_allows_confirm_retry(monkeypatch) -> None:
    calls = []

    async def fake_confirm(user_id, confirmation):
        calls.append((user_id, confirmation))
        return ReminderMutationResult(
            ok=False,
            action="unsubscribe",
            message="Failed to unsubscribe. Please try again in a moment.",
        )

    monkeypatch.setattr(reminder_views.reminder_service, "confirm_unsubscribe", fake_confirm)
    confirmation = ReminderUnsubscribeConfirmation(
        event_types=("ruins",),
        reminder_times=("24h",),
    )
    view = reminder_views.ReminderUnsubscribeConfirmView(
        author_id=42,
        display_name="Tester",
        confirmation=confirmation,
    )
    interaction = _Interaction()
    button = next(
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:reminder:unsubscribe:confirm"
    )

    await button.callback(interaction)
    await button.callback(interaction)

    assert calls == [(42, confirmation), (42, confirmation)]
    assert view._confirmed is False
    assert len(interaction.followup.sent) == 2


@pytest.mark.asyncio
async def test_view_navigation_loads_summary_and_edits_message() -> None:
    order = []

    async def loader(user_id: int):
        assert user_id == 42
        order.append("loader")
        return _summary()

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()
    original_defer = interaction.response.defer

    async def defer(**kwargs):
        order.append("defer")
        await original_defer(**kwargs)

    interaction.response.defer = defer

    await view._show_page(interaction, views.PAGE_REMINDERS)

    edited = interaction.original_edits[-1]
    assert order == ["defer", "loader"]
    assert interaction.response.deferred[-1]["ephemeral"] is True
    assert edited["content"] is None
    assert edited["embed"].image.url.startswith("attachment://me_reminders_")
    assert edited["attachments"] == []
    assert [file.filename for file in edited["files"]] == ["me_reminders_42.png"]
    assert isinstance(edited["view"], views.PlayerSelfServiceView)
    assert edited["view"]._message_ref is interaction.message


@pytest.mark.asyncio
async def test_view_navigation_propagates_edit_cancellation(monkeypatch) -> None:
    async def loader(_user_id: int):
        return _summary()

    async def fake_edit(*_args, **_kwargs):
        raise asyncio.CancelledError()

    monkeypatch.setattr(views, "_edit_original_with_image_fallback", fake_edit)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()

    with pytest.raises(asyncio.CancelledError):
        await view._show_page(interaction, views.PAGE_REMINDERS)

    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_view_navigation_defer_type_error_falls_back_without_logging(caplog) -> None:
    order = []

    async def loader(_user_id: int):
        order.append("loader")
        return _summary()

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()
    original_defer = interaction.response.defer

    async def defer(**kwargs):
        if "ephemeral" in kwargs:
            order.append("defer-ephemeral")
            raise TypeError("ephemeral is not supported")
        order.append("defer-fallback")
        await original_defer(**kwargs)

    caplog.set_level("DEBUG")
    interaction.response.defer = defer

    await view._show_page(interaction, views.PAGE_REMINDERS)

    assert order == ["defer-ephemeral", "defer-fallback", "loader"]
    assert interaction.response.deferred[-1] == {}
    assert "player_self_service_navigation_defer_failed" not in caplog.text


@pytest.mark.asyncio
async def test_view_navigation_failure_after_defer_uses_private_followup() -> None:
    async def loader(_user_id: int):
        raise RuntimeError("registry down")

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()

    await view._show_page(interaction, views.PAGE_ACCOUNTS)

    assert interaction.response.deferred[-1]["ephemeral"] is True
    args, kwargs, _message = interaction.followup.sent[-1]
    assert "temporarily unavailable" in args[0]
    assert kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_account_completion_navigation_defer_type_error_falls_back() -> None:
    order = []

    async def loader(_user_id: int):
        order.append("loader")
        return _summary()

    view = account_views.AccountCompletionView(
        author_id=42,
        display_name="Tester",
        message="Done",
        summary_loader=loader,
    )
    interaction = _Interaction()
    original_defer = interaction.response.defer

    async def defer(**kwargs):
        if "ephemeral" in kwargs:
            order.append("defer-ephemeral")
            raise TypeError("ephemeral is not supported")
        order.append("defer-fallback")
        await original_defer(**kwargs)

    interaction.response.defer = defer

    await view._show_page(interaction, views.PAGE_ACCOUNTS)

    assert order == ["defer-ephemeral", "defer-fallback", "loader"]
    assert interaction.response.deferred[-1] == {}
    assert interaction.original_edits[-1]["embed"].image.url.startswith("attachment://me_accounts_")


@pytest.mark.asyncio
async def test_account_completion_navigation_opens_governor_dashboard(monkeypatch) -> None:
    async def loader(_user_id: int):
        return _summary()

    view = account_views.AccountCompletionView(
        author_id=42,
        display_name="Tester",
        message="Done",
        summary_loader=loader,
    )
    interaction = _Interaction()
    calls = []

    async def fake_show(target, **kwargs):
        calls.append((target, kwargs))

    monkeypatch.setattr(
        governor_dashboard_views,
        "show_governor_dashboard_for_interaction",
        fake_show,
    )

    await view._show_page(interaction, views.PAGE_DASHBOARD)

    assert calls[0][0] is interaction
    assert calls[0][1]["author_id"] == 42
    assert calls[0][1]["display_name"] == "Tester"
    assert calls[0][1]["summary_loader"] is loader


@pytest.mark.asyncio
async def test_reminder_completion_dashboard_navigation_uses_governor_journey(
    monkeypatch,
) -> None:
    async def loader(_user_id: int):
        return _summary()

    view = reminder_views.ReminderCompletionView(
        author_id=42,
        display_name="Tester",
        message="Done",
        summary_loader=loader,
    )
    interaction = _Interaction()
    calls = []

    async def fake_show(target, **kwargs):
        calls.append((target, kwargs))

    monkeypatch.setattr(
        governor_dashboard_views,
        "show_governor_dashboard_for_interaction",
        fake_show,
    )

    await view._show_page(interaction, views.PAGE_DASHBOARD)

    assert calls[0][0] is interaction
    assert calls[0][1]["author_id"] == 42
    assert calls[0][1]["display_name"] == "Tester"
    assert calls[0][1]["summary_loader"] is loader


@pytest.mark.asyncio
async def test_view_timeout_disables_controls() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")
    edits = []

    class Message:
        async def edit(self, **kwargs):
            edits.append(kwargs)

    view.set_message_ref(Message())

    await view.on_timeout()

    assert all(child.disabled for child in view.children)
    assert edits[-1]["view"] is view
    assert "expired" in edits[-1]["content"]


@pytest.mark.asyncio
async def test_exports_view_timeout_disables_controls() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_EXPORTS,
        summary=_summary(),
    )
    edits = []

    class Message:
        async def edit(self, **kwargs):
            edits.append(kwargs)

    view.set_message_ref(Message())

    await view.on_timeout()

    assert all(child.disabled for child in view.children)
    assert edits[-1]["view"] is view
    assert "expired" in edits[-1]["content"]


@pytest.mark.asyncio
async def test_expired_view_rejects_click_with_private_message() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")
    await view.on_timeout()
    interaction = _Interaction()

    assert await view.interaction_check(interaction) is False
    assert "expired" in interaction.response.sent[-1][0][0]
    assert interaction.response.sent[-1][1]["ephemeral"] is True


def test_exports_embed_is_compact_and_action_first() -> None:
    embed = views.build_exports_embed(_summary(), display_name="Tester")

    assert embed.title == "Exports"
    assert embed.description == "Private exports for Tester"
    assert [field.name for field in embed.fields] == ["Status", "Actions"]
    assert "Delivery: Private" in embed.fields[0].value
    assert "Export Stats" in embed.fields[1].value
    assert "Export Inventory" in embed.fields[1].value
    assert "Legacy" not in embed.fields[1].value


@pytest.mark.asyncio
async def test_initial_page_summary_failure_edits_deferred_response(monkeypatch) -> None:
    async def fake_safe_defer(_ctx, *, ephemeral=False):
        calls.append(("defer", ephemeral))

    async def loader(_user_id: int):
        calls.append(("loader", None))
        raise RuntimeError("inventory down")

    class Interaction:
        def __init__(self):
            self.edits = []

        async def edit_original_response(self, **kwargs):
            self.edits.append(kwargs)

    class Followup:
        def __init__(self):
            self.sent = []

        async def send(self, *args, **kwargs):
            self.sent.append((args, kwargs))

    calls = []
    ctx = SimpleNamespace(
        user=SimpleNamespace(id=42, display_name="Tester"),
        interaction=Interaction(),
        followup=Followup(),
    )

    monkeypatch.setattr(views, "safe_defer", fake_safe_defer)

    await views.send_player_self_service_page(ctx, summary_loader=loader)

    assert calls == [("defer", True), ("loader", None)]
    assert "temporarily unavailable" in ctx.interaction.edits[-1]["content"]
    assert ctx.interaction.edits[-1]["embed"] is None
    assert ctx.interaction.edits[-1]["view"] is None
    assert ctx.followup.sent == []
