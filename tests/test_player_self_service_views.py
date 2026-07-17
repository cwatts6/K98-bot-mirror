from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace

import pytest

from player_self_service.account_service import (
    AccountCentreState,
    AccountConfirmation,
    AccountMutationResult,
)
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
)
from player_self_service.preferences_summary import (
    PreferencesSummaryPayload,
    PreferenceValueSummary,
    RegionalProfileSummary,
    TimeReferenceSummary,
)
from player_self_service.reminder_service import (
    ReminderCentreState,
    ReminderMessage,
    ReminderMutationResult,
    ReminderUnsubscribeConfirmation,
)
from player_self_service.service import (
    AccountStatus,
    PlayerSelfServiceSummary,
    ReminderStatus,
)
from ui.views import (
    player_self_service_account_views as account_views,
    player_self_service_governor_dashboard_views as governor_dashboard_views,
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
    )


def _accounts_payload() -> AccountsPortfolioPayload:
    now = datetime(2026, 7, 14, 8, 30, tzinfo=UTC)
    row = AccountPortfolioRow(
        slot="Main",
        role="Main",
        registered_name="Main Gov",
        current_governor_name="Main Gov",
        governor_id=111,
        power=100,
        troop_power=50,
        t4_kills=10,
        t5_kills=20,
        t4_t5_kills=30,
        rss_total=400,
        data_state="CURRENT",
        last_governor_scan=now,
        inventory_as_of=now,
    )
    metric = AccountMetricTotal(100, 1, 1)
    return AccountsPortfolioPayload(
        discord_user_id=42,
        state="READY",
        rows=(row,),
        linked_count=1,
        main_row=row,
        role_counts=(("Main", 1), ("Alt", 0), ("Farm", 0)),
        power=metric,
        troop_power=metric,
        t4_t5_kills=metric,
        rss_total=metric,
        insight="All linked governors are current.",
        refreshed_at_utc=now,
        latest_scan_date=now,
    )


def _preferences_payload() -> PreferencesSummaryPayload:
    return PreferencesSummaryPayload(
        discord_user_id=42,
        display_name="Tester",
        kingdom_id=1198,
        generated_at_utc=datetime(2026, 7, 14, 8, 30, tzinfo=UTC),
        regional_profile=RegionalProfileSummary(
            timezone=PreferenceValueSummary(True, True, "United Kingdom", "Europe/London"),
            location=PreferenceValueSummary(True, True, "United Kingdom (GB)", "GB"),
            preferred_language=PreferenceValueSummary(True, True, "English (en-GB)", "en-GB"),
        ),
        time_reference=TimeReferenceSummary(
            mode="LOCAL",
            heading="LOCAL TIME REFERENCE",
            display_time="09:30",
            timezone_label="United Kingdom",
            utc_offset_label="UTC+1",
            supporting_line="United Kingdom • UTC+1",
            regional_context="United Kingdom (GB) • English (en-GB)",
        ),
        profile_details_set=3,
        profile_details_total=3,
        profile_supporting_text="3 of 3 profile details set",
        settings_insight="All three regional profile details are available.",
    )


def test_accounts_portfolio_fallback_uses_singular_governor_label() -> None:
    embed = views.build_accounts_portfolio_fallback(
        _accounts_payload(),
        display_name="Tester",
    )

    assert embed.fields[0].name == "READY • 1 governor"


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
    assert len(embed.fields) == 2
    assert [field.name for field in embed.fields] == ["Accounts", "Reminders"]
    assert "Next action: Review" in embed.fields[0].value
    assert "/register_governor" not in embed.fields[0].value


def test_reminders_fallback_identity_and_footer_match_card_contract() -> None:
    embed = views.build_reminders_embed(_summary(), display_name="Chrislos (1198)")

    assert embed.description == "Chrislos (1198)"
    assert embed.footer.text.startswith("Scheduled times shown in UTC • Refreshed ")
    assert embed.footer.text.endswith(" UTC")


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

    def fake_render(payload, *, display_name, avatar_bytes):
        calls.append((payload.discord_user_id, display_name, avatar_bytes))
        return views.accounts_renderer.RenderedAccountsCard(
            filename="me_accounts_42.png",
            image_bytes=b"png",
        )

    monkeypatch.setattr(views.accounts_renderer, "render_accounts_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_ACCOUNTS,
        None,
        display_name="Tester",
        accounts_payload=_accounts_payload(),
        avatar_bytes=b"avatar",
    )

    assert calls == [(42, "Tester", b"avatar")]
    assert embed is None
    assert [file.filename for file in files] == ["me_accounts_42.png"]


@pytest.mark.asyncio
async def test_reminders_response_passes_author_avatar_to_renderer(monkeypatch) -> None:
    calls = []

    def fake_render(payload, *, avatar_bytes):
        calls.append((payload.viewer_discord_id, avatar_bytes))
        return views.reminders_renderer.RenderedRemindersCard(
            filename="me_reminders_42.png",
            image_bytes=BytesIO(b"png"),
        )

    monkeypatch.setattr(views.reminders_renderer, "render_reminders_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_REMINDERS,
        _summary(),
        display_name="Tester",
        avatar_bytes=b"avatar",
    )
    try:
        assert calls == [(42, b"avatar")]
        assert embed is None
        assert [file.filename for file in files] == ["me_reminders_42.png"]
    finally:
        views._close_files(files)


@pytest.mark.asyncio
async def test_accounts_avatar_read_is_author_scoped() -> None:
    class Avatar:
        def __init__(self) -> None:
            self.reads = 0

        def with_size(self, size):
            assert size == 256
            return self

        async def read(self):
            self.reads += 1
            return b"avatar"

    avatar = Avatar()
    owner = SimpleNamespace(id=42, display_avatar=avatar, avatar=None)
    foreign = SimpleNamespace(id=99, display_avatar=avatar, avatar=None)

    assert await views._read_avatar_bytes(owner, expected_user_id=42) == b"avatar"
    assert await views._read_avatar_bytes(foreign, expected_user_id=42) is None
    assert avatar.reads == 1


@pytest.mark.asyncio
async def test_subpage_response_falls_back_to_embed_when_card_render_fails(monkeypatch) -> None:
    def fake_render(*_args, **_kwargs):
        raise RuntimeError("asset unavailable")

    monkeypatch.setattr(views.reminders_renderer, "render_reminders_card", fake_render)

    embed, files = await views._build_page_response(
        views.PAGE_REMINDERS,
        _summary(),
        display_name="Tester",
    )

    assert embed.title == "Reminder Centre"
    assert files == []
    assert getattr(embed.image, "url", None) is None


@pytest.mark.asyncio
async def test_page_response_render_failure_logs_safely_without_payloads(monkeypatch) -> None:
    fallback_embed = object()
    monkeypatch.setattr(
        views,
        "build_page_embed",
        lambda *_args, **_kwargs: fallback_embed,
    )

    embed, files = await views._build_page_response(
        views.PAGE_DASHBOARD,
        None,
        display_name="Tester",
    )

    assert embed is fallback_embed
    assert files == []


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
async def test_reminders_image_send_failure_uses_same_payload_without_refetch(monkeypatch) -> None:
    summary = _summary()
    fallback_calls = []
    real_builder = views.build_page_embed

    def tracked_builder(page, received, **kwargs):
        fallback_calls.append((page, received))
        return real_builder(page, received, **kwargs)

    monkeypatch.setattr(views, "build_page_embed", tracked_builder)

    class Target:
        def __init__(self) -> None:
            self.calls = []

        async def edit_original_response(self, **kwargs):
            self.calls.append(kwargs)
            if kwargs.get("files"):
                raise RuntimeError("attachment rejected")
            return SimpleNamespace(id=999)

    embed, files = await views._build_page_response(
        views.PAGE_REMINDERS,
        summary,
        display_name="Tester",
    )
    try:
        target = Target()
        message = await views._edit_original_with_image_fallback(
            target,
            page=views.PAGE_REMINDERS,
            summary=summary,
            display_name="Tester",
            view=views.PlayerSelfServiceView(author_id=42, display_name="Tester"),
            embed=embed,
            files=files,
        )

        assert message.id == 999
        assert len(target.calls) == 2
        assert target.calls[0]["embed"] is None
        assert target.calls[0]["files"]
        assert target.calls[1]["embed"].title == "Reminder Centre"
        assert fallback_calls[-1] == (views.PAGE_REMINDERS, summary)
    finally:
        views._close_files(files)


@pytest.mark.asyncio
async def test_image_send_failure_logs_safely_without_payloads(monkeypatch) -> None:
    fallback_embed = object()
    monkeypatch.setattr(
        views,
        "build_page_embed",
        lambda *_args, **_kwargs: fallback_embed,
    )

    class Target:
        def __init__(self) -> None:
            self.calls = []

        async def edit_original_response(self, **kwargs):
            self.calls.append(kwargs)
            if kwargs.get("files"):
                raise RuntimeError("attachment rejected")
            return SimpleNamespace(id=999)

    target = Target()
    message = await views._edit_original_with_image_fallback(
        target,
        page=views.PAGE_DASHBOARD,
        summary=None,
        display_name="Tester",
        view=views.PlayerSelfServiceView(author_id=42, display_name="Tester"),
        embed=views.build_dashboard_embed(_summary(), display_name="Tester"),
        files=[SimpleNamespace(filename="me_dashboard_42.png")],
    )

    assert message.id == 999
    assert len(target.calls) == 2
    assert target.calls[1]["embed"] is fallback_embed


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
    assert embed.fields[0].name in {"ACTIVE", "REVIEW", "OFF"}
    assert embed.fields[1].name == "REMINDER COVERAGE"
    assert embed.fields[-1].name == "Manage reminders"
    assert "Choose KVK and calendar events" in embed.fields[-1].value
    assert "/modify_subscription" not in embed.fields[1].value


def test_preferences_embed_uses_same_authorised_payload_without_vip() -> None:
    embed = views.build_preferences_embed(_preferences_payload())

    assert embed.title == "Personal Settings"
    assert "VIP" not in str(embed.to_dict())
    assert "Location: United Kingdom (GB)" in embed.fields[0].value
    assert embed.fields[0].name.startswith("LOCAL")
    assert embed.fields[-1].name == "Manage settings"
    assert "privacy" not in str(embed.to_dict()).casefold()
    assert "inventory visibility" not in str(embed.to_dict()).casefold()


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
async def test_dashboard_view_has_primary_buttons_without_exports() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")

    labels = [getattr(child, "label", None) for child in view.children]
    assert labels[:3] == ["Accounts", "Reminders", "Preferences"]
    assert "Inventory" not in labels
    assert "Exports" not in labels
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
        accounts_payload=_accounts_payload() if page == views.PAGE_ACCOUNTS else None,
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
    _assert_button_layout(
        views.PAGE_DASHBOARD,
        [
            *top_row,
            ("Dashboard", 1, secondary, True),
        ],
    )
    _assert_button_layout(
        views.PAGE_ACCOUNTS,
        [
            ("Accounts", 0, primary, True),
            ("Reminders", 0, primary, False),
            ("Preferences", 0, primary, False),
            ("Dashboard", 1, secondary, False),
            ("Manage Accounts", 2, success, False),
            ("Account Summary", 2, secondary, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_REMINDERS,
        [
            ("Accounts", 0, primary, False),
            ("Reminders", 0, primary, True),
            ("Preferences", 0, primary, False),
            ("Dashboard", 1, secondary, False),
            ("Manage", 2, success, False),
        ],
    )
    _assert_button_layout(
        views.PAGE_PREFERENCES,
        [
            ("Accounts", 0, primary, False),
            ("Reminders", 0, primary, False),
            ("Preferences", 0, primary, True),
            ("Dashboard", 1, secondary, False),
            ("Manage settings", 2, success, False),
        ],
    )


@pytest.mark.asyncio
async def test_accounts_view_has_no_inventory_or_exports_navigation() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_ACCOUNTS,
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage Accounts" in labels
    assert "Account Summary" in labels
    assert not {"Find ID", "Register", "Replace", "Remove"}.intersection(set(labels))
    assert "Inventory" not in labels
    assert "Exports" not in labels


@pytest.mark.asyncio
async def test_reminders_view_has_no_inventory_or_exports_navigation() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_REMINDERS,
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage" in labels
    assert "Unsubscribe" not in labels
    assert "Register" not in labels
    assert "Inventory" not in labels
    assert "Exports" not in labels


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
async def test_preferences_view_removes_inventory_and_old_direct_actions() -> None:
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        preferences_payload=_preferences_payload(),
    )

    labels = [getattr(child, "label", None) for child in view.children]
    assert "Manage settings" in labels
    assert {"Set Public", "Set Private", "Update VIP", "Manage Profile"}.isdisjoint(labels)
    assert "Inventory" not in labels
    assert "Exports" not in labels


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
    assert [option.value for option in select.options] == ["lookup", "update_vip", "register"]


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

    async def accounts_loader(_user_id: int):
        return _accounts_payload()

    monkeypatch.setattr(account_views.account_service, "confirm_register", fake_confirm)
    monkeypatch.setattr(
        account_views.accounts_service,
        "build_accounts_portfolio",
        accounts_loader,
    )
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

    assert host_message.edits[-1]["embed"] is None
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
    rendered_avatars = []

    def fake_render(payload, *, avatar_bytes):
        rendered_avatars.append((payload.viewer_discord_id, avatar_bytes))
        return views.reminders_renderer.RenderedRemindersCard(
            filename="me_reminders_42.png",
            image_bytes=BytesIO(b"png"),
        )

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
    monkeypatch.setattr(views.reminders_renderer, "render_reminders_card", fake_render)
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
        avatar_bytes=b"avatar",
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
    assert edit["embed"] is None
    assert [file.filename for file in edit["files"]] == ["me_reminders_42.png"]
    assert rendered_avatars == [(42, b"avatar")]
    assert edit["view"].avatar_bytes == b"avatar"


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
    assert interaction.response.deferred[-1] == {}
    assert edited["content"] is None
    assert edited["embed"] is None
    assert edited["attachments"] == []
    assert [file.filename for file in edited["files"]] == ["me_reminders_42.png"]
    assert isinstance(edited["view"], views.PlayerSelfServiceView)
    assert edited["view"]._message_ref is interaction.message


@pytest.mark.asyncio
async def test_reminders_navigation_reads_and_retains_author_avatar(monkeypatch) -> None:
    captured = []

    async def loader(_user_id: int):
        return _summary()

    async def fake_read_avatar(user, *, expected_user_id):
        assert user.id == expected_user_id == 42
        return b"avatar"

    async def fake_build(page, summary, **kwargs):
        captured.append((page, summary.discord_user_id, kwargs["avatar_bytes"]))
        return views.build_reminders_embed(summary, display_name="Tester"), []

    monkeypatch.setattr(views, "_read_avatar_bytes", fake_read_avatar)
    monkeypatch.setattr(views, "_build_page_response", fake_build)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()

    await view._show_page(interaction, views.PAGE_REMINDERS)

    refreshed_view = interaction.original_edits[-1]["view"]
    assert captured == [(views.PAGE_REMINDERS, 42, b"avatar")]
    assert refreshed_view.avatar_bytes == b"avatar"


@pytest.mark.asyncio
async def test_stale_navigation_closes_rendered_files(monkeypatch) -> None:
    async def loader(_user_id: int):
        return _summary()

    stream = BytesIO(b"rendered-card")
    rendered_file = SimpleNamespace(fp=stream, close=lambda: None)

    async def fake_build(*_args, **_kwargs):
        return object(), [rendered_file]

    monkeypatch.setattr(views, "_build_page_response", fake_build)
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()
    checks = iter((True, False))

    result = await view._show_page(
        interaction,
        views.PAGE_REMINDERS,
        can_edit=lambda: next(checks),
    )

    assert result is False
    assert stream.closed is True
    assert interaction.original_edits == []


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
    interaction.message = None

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
        accounts_loader=loader,
    )
    interaction = _Interaction()

    await view._show_page(interaction, views.PAGE_ACCOUNTS)

    assert interaction.response.deferred[-1] == {}
    args, kwargs, _message = interaction.followup.sent[-1]
    assert "temporarily unavailable" in args[0]
    assert kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_account_completion_navigation_defer_type_error_falls_back() -> None:
    order = []

    async def accounts_loader(_user_id: int):
        order.append("loader")
        return _accounts_payload()

    view = account_views.AccountCompletionView(
        author_id=42,
        display_name="Tester",
        message="Done",
        accounts_loader=accounts_loader,
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
    interaction.message = None

    await view._show_page(interaction, views.PAGE_ACCOUNTS)

    assert order == ["defer-ephemeral", "defer-fallback", "loader"]
    assert interaction.response.deferred[-1] == {}
    assert interaction.original_edits[-1]["embed"] is None
    assert [file.filename for file in interaction.original_edits[-1]["files"]] == [
        "me_accounts_42.png"
    ]


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
    assert "attachments" not in edits[-1]
    assert "files" not in edits[-1]


@pytest.mark.asyncio
async def test_expired_view_rejects_click_with_private_message() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")
    await view.on_timeout()
    interaction = _Interaction()

    assert await view.interaction_check(interaction) is False
    assert "expired" in interaction.response.sent[-1][0][0]
    assert interaction.response.sent[-1][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_initial_reminders_page_reads_and_retains_author_avatar(monkeypatch) -> None:
    captured = []

    class Avatar:
        def with_size(self, size):
            assert size == 256
            return self

        async def read(self):
            return b"avatar"

    async def fake_safe_defer(_ctx, *, ephemeral=False):
        assert ephemeral is True

    async def loader(user_id: int):
        assert user_id == 42
        return _summary()

    async def fake_build(page, summary, **kwargs):
        captured.append(("build", page, summary.discord_user_id, kwargs["avatar_bytes"]))
        return views.build_reminders_embed(summary, display_name="Tester"), []

    async def fake_edit(_target, **kwargs):
        captured.append(("edit", kwargs["view"].avatar_bytes))
        return SimpleNamespace(id=123)

    user = SimpleNamespace(
        id=42,
        display_name="Tester",
        display_avatar=Avatar(),
        avatar=None,
    )
    ctx = SimpleNamespace(user=user, interaction=SimpleNamespace(), followup=SimpleNamespace())
    monkeypatch.setattr(views, "safe_defer", fake_safe_defer)
    monkeypatch.setattr(views, "_build_page_response", fake_build)
    monkeypatch.setattr(views, "_edit_original_with_image_fallback", fake_edit)

    await views.send_player_self_service_page(
        ctx,
        page=views.PAGE_REMINDERS,
        summary_loader=loader,
    )

    assert captured == [
        ("build", views.PAGE_REMINDERS, 42, b"avatar"),
        ("edit", b"avatar"),
    ]


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
