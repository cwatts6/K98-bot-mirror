from __future__ import annotations

from types import SimpleNamespace

import pytest

from player_self_service.service import (
    AccountStatus,
    ExportStatus,
    PlayerSelfServiceSummary,
    PreferenceStatus,
    ReminderStatus,
)
from ui.views import player_self_service_views as views


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

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)


class _Followup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, *args, **kwargs):
        message = SimpleNamespace(edits=[])
        self.sent.append((args, kwargs, message))
        return message


class _Interaction:
    def __init__(self, user_id: int = 42) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.response = _Response()
        self.followup = _Followup()


def test_dashboard_embed_is_status_first_and_compact() -> None:
    embed = views.build_dashboard_embed(_summary(), display_name="Tester")

    assert embed.title == "K98 Personal Command Centre"
    assert len(embed.fields) == 3
    assert [field.name for field in embed.fields] == ["Accounts", "Reminders", "Preferences"]
    assert "Next action: Review" in embed.fields[0].value
    assert "/register_governor" not in embed.fields[0].value


@pytest.mark.asyncio
async def test_dashboard_view_has_three_primary_buttons_and_quick_launch() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")

    labels = [getattr(child, "label", None) for child in view.children]
    assert labels[:3] == ["Accounts", "Reminders", "Preferences"]
    assert "Dashboard" not in labels
    assert any(isinstance(child, views.PlayerSelfServiceQuickLaunchSelect) for child in view.children)


@pytest.mark.asyncio
async def test_view_rejects_non_owner() -> None:
    view = views.PlayerSelfServiceView(author_id=42, display_name="Tester")
    interaction = _Interaction(user_id=99)

    assert await view.interaction_check(interaction) is False
    assert interaction.response.sent[-1][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_view_navigation_loads_summary_and_edits_message() -> None:
    async def loader(user_id: int):
        assert user_id == 42
        return _summary()

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        summary_loader=loader,
    )
    interaction = _Interaction()

    await view._show_page(interaction, views.PAGE_REMINDERS)

    edited = interaction.response.edited[-1]
    assert edited["embed"].title == "Reminder Centre"
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


def test_exports_embed_warns_file_exports_are_private() -> None:
    embed = views.build_exports_embed(_summary(), display_name="Tester")

    assert embed.title == "Exports"
    assert "file exports are delivered privately" in embed.fields[1].value
