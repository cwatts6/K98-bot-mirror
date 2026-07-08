from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import discord
import pytest

from ui.views.vote_admin_dashboard_view import VoteAdminDashboardView, eligible_users_from_guild
from voting import dashboard_presentation
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingContract,
    DashboardReportingSummary,
    EngagementReportingContract,
)


def _contract(*, title: str = "Planning vote") -> DashboardReportingContract:
    now = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    return DashboardReportingContract(
        generated_at_utc=now,
        privacy_profile=REPORT_PRIVACY_PROFILE,
        summaries=(
            DashboardReportingSummary(
                content_kind=REPORT_CONTENT_VOTE,
                content_id=42,
                title=title,
                status="Open",
                result_visibility="PublicLive",
                created_at_utc=now,
                closes_at_utc=now,
                closed_at_utc=None,
                total_participants=3,
                total_selections=3,
                option_count=2,
                question_count=1,
                required_question_count=1,
                optional_question_count=0,
                vote_mode="OneChoice",
                top_summary="Top selection: A (2)",
            ),
        ),
        question_aggregates=(),
        option_aggregates=(),
    )


class _Response:
    def __init__(self) -> None:
        self.done = False
        self.edits: list[dict[str, object]] = []
        self.deferred = False

    def is_done(self) -> bool:
        return self.done

    async def edit_message(self, **kwargs) -> None:
        self.done = True
        self.edits.append(kwargs)

    async def defer(self, **_kwargs) -> None:
        self.done = True
        self.deferred = True


class _Interaction:
    def __init__(self, user_id: int = 123, guild=None) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.guild = guild
        self.response = _Response()
        self.original_edits: list[dict[str, object]] = []
        self.followup = SimpleNamespace(send=self._followup_send)
        self.followups: list[dict[str, object]] = []

    async def edit_original_response(self, **kwargs) -> None:
        self.original_edits.append(kwargs)

    async def _followup_send(self, *args, **kwargs) -> None:
        self.followups.append({"args": args, "kwargs": kwargs})


class _FailingDeferResponse(_Response):
    async def defer(self, **_kwargs) -> None:
        raise RuntimeError("defer failed")


class _FailingDeferInteraction(_Interaction):
    def __init__(self, user_id: int = 123) -> None:
        super().__init__(user_id=user_id)
        self.response = _FailingDeferResponse()


class _FailingOriginalEditInteraction(_Interaction):
    async def edit_original_response(self, **_kwargs) -> None:
        raise discord.NotFound(SimpleNamespace(status=404, reason="missing"), "missing")


class _Role:
    def __init__(self, role_id: int, name: str) -> None:
        self.id = role_id
        self.name = name


class _Member:
    def __init__(
        self,
        user_id: int,
        display_name: str,
        roles: list[_Role] | None = None,
        *,
        bot: bool = False,
    ) -> None:
        self.id = user_id
        self.display_name = display_name
        self.roles = roles or []
        self.bot = bot


class _Guild:
    def __init__(self, members: list[_Member]) -> None:
        self.members = members


@pytest.mark.asyncio
async def test_dashboard_view_starts_with_single_page_controls() -> None:
    view = VoteAdminDashboardView(_contract(), owner_user_id=123)

    assert len(view.pages) == 1
    assert view.prev_btn.disabled is True
    assert view.next_btn.disabled is True
    assert "Planning vote" in str(view.current_embed().to_dict())


@pytest.mark.asyncio
async def test_dashboard_view_rejects_other_admin(monkeypatch) -> None:
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.vote_admin_dashboard_view.send_ephemeral", fake_send_ephemeral)
    view = VoteAdminDashboardView(_contract(), owner_user_id=123)

    assert await view.interaction_check(SimpleNamespace(user=SimpleNamespace(id=456))) is False
    assert sent == ["This dashboard belongs to another admin."]


@pytest.mark.asyncio
async def test_dashboard_refresh_reloads_contract() -> None:
    async def loader():
        return _contract(title="Refreshed vote")

    view = VoteAdminDashboardView(_contract(), owner_user_id=123, report_loader=loader)
    interaction = _Interaction(user_id=123)

    await view._on_refresh(interaction)

    assert interaction.response.deferred is True
    assert interaction.original_edits
    assert "Refreshed vote" in str(interaction.original_edits[-1]["embed"].to_dict())


@pytest.mark.asyncio
async def test_dashboard_refresh_uses_response_edit_when_defer_fails() -> None:
    async def loader():
        return _contract(title="Refreshed without defer")

    view = VoteAdminDashboardView(_contract(), owner_user_id=123, report_loader=loader)
    interaction = _FailingDeferInteraction(user_id=123)

    await view._on_refresh(interaction)

    assert interaction.original_edits == []
    assert interaction.response.edits
    assert "Refreshed without defer" in str(interaction.response.edits[-1]["embed"].to_dict())


@pytest.mark.asyncio
async def test_dashboard_edit_failure_sends_retry_guidance(monkeypatch) -> None:
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.vote_admin_dashboard_view.send_ephemeral", fake_send_ephemeral)
    view = VoteAdminDashboardView(_contract(), owner_user_id=123)
    interaction = _FailingOriginalEditInteraction(user_id=123)
    interaction.response.done = True

    await view.edit_current(interaction)

    assert sent == ["Dashboard update took too long for Discord to accept. Please press Refresh."]


def test_eligible_users_from_guild_includes_roles_and_excludes_bots() -> None:
    guild = _Guild(
        [
            _Member(100, "Alice", [_Role(1, "@everyone"), _Role(10, "Kingdom Leadership")]),
            _Member(200, "NoRole", [_Role(1, "@everyone")]),
            _Member(300, "Bot", [_Role(10, "Kingdom Leadership")], bot=True),
        ]
    )

    users = eligible_users_from_guild(guild)

    assert [user.discord_user_id for user in users] == [100, 200]
    assert users[0].role_ids == (10,)
    assert users[0].role_names == ("Kingdom Leadership",)
    assert users[1].role_ids == ()


@pytest.mark.asyncio
async def test_dashboard_engagement_mode_loads_private_role_filtered_summary() -> None:
    guild = _Guild(
        [
            _Member(100, "Alice", [_Role(10, "Kingdom Leadership")]),
            _Member(200, "NoRole", []),
        ]
    )
    loaded: list[tuple[int, str, str]] = []

    async def engagement_loader(*, eligible_users, window_key, role_filter_value):
        loaded.append((len(eligible_users), window_key, role_filter_value))
        now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
        return EngagementReportingContract(
            generated_at_utc=now,
            privacy_profile=ENGAGEMENT_PRIVACY_PROFILE,
            window_key=window_key,
            window_label="Last 3 months",
            window_start_utc=now,
            window_end_utc=now,
            role_filter_value=role_filter_value,
            role_filter_label="Kingdom Leadership",
            eligible_user_count=1,
            vote_post_count=1,
            survey_post_count=0,
            possible_participations=1,
            actual_participations=1,
            engagement_rate=1.0,
            user_summaries=(),
            monthly_buckets=(),
        )

    view = VoteAdminDashboardView(
        _contract(),
        owner_user_id=123,
        engagement_report_loader=engagement_loader,
        eligible_users=eligible_users_from_guild(guild),
        role_filter_value="role:10",
    )
    view.mode_value = dashboard_presentation.DASHBOARD_MODE_ENGAGEMENT
    interaction = _Interaction(user_id=123, guild=guild)

    assert await view.ensure_engagement_contract(interaction) is True
    view.rebuild_pages()
    await view.edit_current(interaction)

    assert loaded == [(2, "last_3_months", "role:10")]
    assert interaction.response.deferred is True
    assert interaction.original_edits
    rendered = str(interaction.original_edits[-1]["embed"].to_dict())
    assert "Kingdom Leadership" in rendered
    assert "1/1" in rendered
