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
from player_self_service.reminder_service import (
    ReminderCentreState,
    ReminderMessage,
    ReminderMutationResult,
    ReminderUnsubscribeConfirmation,
)
from player_self_service.service import (
    AccountStatus,
    ExportStatus,
    PlayerSelfServiceSummary,
    PreferenceStatus,
    ReminderStatus,
)
from ui.views import (
    player_self_service_account_views as account_views,
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
        ),
        exports=ExportStatus(
            stats_export="stats export available",
            inventory_export="inventory export available for approved records",
            privacy_note="file exports are delivered privately",
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
    assert "/modify_subscription" not in embed.fields[1].value


def test_preferences_embed_invites_service_backed_visibility_controls() -> None:
    embed = views.build_preferences_embed(_summary(), display_name="Tester")

    assert embed.title == "Preferences"
    assert "VIP level" in embed.fields[0].value
    assert "/inventory_preferences" not in embed.fields[1].value


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
async def test_dashboard_view_has_three_primary_buttons_and_quick_launch() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")

    labels = [getattr(child, "label", None) for child in view.children]
    assert labels[:3] == ["Accounts", "Reminders", "Preferences"]
    assert "Dashboard" not in labels
    assert any(
        isinstance(child, views.PlayerSelfServiceQuickLaunchSelect) for child in view.children
    )


@pytest.mark.asyncio
async def test_accounts_view_has_account_actions_without_quick_launch() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_ACCOUNTS,
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage" in labels
    assert not {"Find ID", "Register", "Replace", "Remove"}.intersection(set(labels))
    assert not any(
        isinstance(child, views.PlayerSelfServiceQuickLaunchSelect) for child in view.children
    )


@pytest.mark.asyncio
async def test_reminders_view_has_reminder_actions_without_quick_launch() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_REMINDERS,
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage" in labels
    assert "Unsubscribe" not in labels
    assert "Register" not in labels
    assert not any(
        isinstance(child, views.PlayerSelfServiceQuickLaunchSelect) for child in view.children
    )


@pytest.mark.asyncio
async def test_preferences_view_has_inventory_visibility_actions_without_quick_launch() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        summary=_summary(),
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert {"Set Public", "Update VIP"}.issubset(set(labels))
    assert "Set Private" not in labels
    assert "Manage" not in labels
    assert not any(
        isinstance(child, views.PlayerSelfServiceQuickLaunchSelect) for child in view.children
    )


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
async def test_account_completion_navigation_sets_message_ref() -> None:
    async def loader(_user_id: int):
        return _summary()

    view = account_views.AccountCompletionView(
        author_id=42,
        display_name="Tester",
        message="Done",
        summary_loader=loader,
    )
    interaction = _Interaction()

    await view._show_page(interaction, views.PAGE_DASHBOARD)

    edited = interaction.original_edits[-1]
    assert edited["content"] is None
    assert edited["embed"].image.url.startswith("attachment://me_dashboard_")
    assert [file.filename for file in edited["files"]] == ["me_dashboard_42.png"]
    new_view = interaction.original_edits[-1]["view"]
    assert isinstance(new_view, views.PlayerSelfServiceView)
    assert new_view._message_ref is interaction.message


@pytest.mark.asyncio
async def test_reminder_completion_dashboard_navigation_uses_generated_card() -> None:
    async def loader(_user_id: int):
        return _summary()

    view = reminder_views.ReminderCompletionView(
        author_id=42,
        display_name="Tester",
        message="Done",
        summary_loader=loader,
    )
    interaction = _Interaction()

    await view._show_page(interaction, views.PAGE_DASHBOARD)

    edited = interaction.original_edits[-1]
    assert edited["content"] is None
    assert edited["embed"].image.url.startswith("attachment://me_dashboard_")
    assert [file.filename for file in edited["files"]] == ["me_dashboard_42.png"]
    assert isinstance(edited["view"], views.PlayerSelfServiceView)


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
async def test_expired_view_rejects_click_with_private_message() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")
    await view.on_timeout()
    interaction = _Interaction()

    assert await view.interaction_check(interaction) is False
    assert "expired" in interaction.response.sent[-1][0][0]
    assert interaction.response.sent[-1][1]["ephemeral"] is True


def test_exports_embed_warns_file_exports_are_private() -> None:
    embed = views.build_exports_embed(_summary(), display_name="Tester")

    assert embed.title == "Exports"
    assert "file exports are delivered privately" in embed.fields[1].value


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
