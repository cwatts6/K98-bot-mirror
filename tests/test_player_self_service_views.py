from __future__ import annotations

from types import SimpleNamespace

import pytest

from player_self_service.account_service import AccountCentreState
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

    async def send(self, *args, **kwargs):
        message = SimpleNamespace(edits=[])
        self.sent.append((args, kwargs, message))
        return message


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


def test_accounts_embed_invites_service_backed_controls() -> None:
    embed = views.build_accounts_embed(_summary(), display_name="Tester")

    assert embed.title == "Account Centre"
    assert "Use the controls below" in embed.fields[1].value
    assert "/modify_registration" not in embed.fields[1].value


def test_reminders_embed_invites_service_backed_controls() -> None:
    embed = views.build_reminders_embed(_summary(), display_name="Tester")

    assert embed.title == "Reminder Centre"
    assert "Use the controls below" in embed.fields[1].value
    assert "/modify_subscription" not in embed.fields[1].value


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
    assert {"Find ID", "Register", "Replace", "Remove"}.issubset(set(labels))
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
    assert {"Manage", "Unsubscribe"}.issubset(set(labels))
    assert "Register" not in labels
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
async def test_register_button_opens_free_slot_selector(monkeypatch) -> None:
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
        child
        for child in view.children
        if getattr(child, "custom_id", None) == "me:account:register"
    )

    await button.callback(interaction)

    _args, kwargs, _message = interaction.followup.sent[-1]
    slot_view = kwargs["view"]
    assert kwargs["ephemeral"] is True
    assert isinstance(slot_view, account_views.AccountSlotSelectView)
    select = next(
        child for child in slot_view.children if isinstance(child, account_views.AccountSlotSelect)
    )
    assert [option.value for option in select.options] == ["Main", "Alt 1"]


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


@pytest.mark.asyncio
async def test_reminder_event_select_refreshes_fights_as_exclusive_choice() -> None:
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

    assert view.selected_types == ["fights"]
    assert interaction.response.edited[-1]["view"] is view
    defaults = {option.value: option.default for option in select.options}
    assert defaults == {
        "ruins": False,
        "altars": False,
        "major": False,
        "fights": True,
        "all": False,
    }


@pytest.mark.asyncio
async def test_reminder_unsubscribe_button_requires_active_subscription(monkeypatch) -> None:
    async def fake_state(_user_id: int):
        return ReminderCentreState(
            ok=True,
            subscribed=False,
            event_types=(),
            reminder_times=(),
            event_summary="not subscribed",
            time_summary="not set",
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
        if getattr(child, "custom_id", None) == "me:reminder:unsubscribe"
    )

    await button.callback(interaction)

    args, kwargs, _message = interaction.followup.sent[-1]
    assert "not currently subscribed" in args[0]
    assert kwargs["ephemeral"] is True


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
async def test_reminder_setup_save_calls_service_and_sends_dm(monkeypatch) -> None:
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
    button = next(
        child for child in view.children if getattr(child, "custom_id", None) == "me:reminder:save"
    )

    await button.callback(interaction)

    assert calls == [(42, "Tester", ("ruins",), ("24h",))]
    assert interaction.user.sent
    edited = interaction.original_edits[-1]
    assert "confirmation DM was sent" in edited["content"]
    assert isinstance(edited["view"], reminder_views.ReminderCompletionView)


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
    assert edited["embed"].title == "Reminder Centre"
    assert isinstance(edited["view"], views.PlayerSelfServiceView)
    assert edited["view"].message is interaction.message


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
    assert interaction.original_edits[-1]["embed"].title == "Account Centre"


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

    new_view = interaction.original_edits[-1]["view"]
    assert isinstance(new_view, views.PlayerSelfServiceView)
    assert new_view.message is interaction.message


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
