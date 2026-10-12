from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from ui.views.vote_admin_engagement_view import VoteAdminEngagementView, eligible_users_from_guild
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    EngagementEligibleUser,
    EngagementReportingContract,
    EngagementUserSummary,
)


def _contract(*, role_filter_value: str = "role:10") -> EngagementReportingContract:
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    return EngagementReportingContract(
        generated_at_utc=now,
        privacy_profile=ENGAGEMENT_PRIVACY_PROFILE,
        window_key="last_3_months",
        window_label="Last 3 months",
        window_start_utc=now,
        window_end_utc=now,
        role_filter_value=role_filter_value,
        role_filter_label="Kingdom Leadership",
        eligible_user_count=1,
        vote_post_count=1,
        survey_post_count=1,
        possible_participations=2,
        actual_participations=1,
        engagement_rate=0.5,
        user_summaries=(
            EngagementUserSummary(
                discord_user_id=100,
                display_name="Alice",
                role_names=("Kingdom Leadership",),
                participation_count=1,
                possible_count=2,
                engagement_rate=0.5,
                last_participated_at_utc=now,
                vote_participation_count=1,
                survey_participation_count=0,
            ),
        ),
        monthly_buckets=(),
    )


class _Response:
    def __init__(self) -> None:
        self.done = False
        self.deferred = False
        self.edits: list[dict[str, object]] = []

    def is_done(self) -> bool:
        return self.done

    async def defer(self, **_kwargs) -> None:
        self.done = True
        self.deferred = True

    async def edit_message(self, **kwargs) -> None:
        self.done = True
        self.edits.append(kwargs)


class _Interaction:
    def __init__(self, user_id: int = 123, guild=None) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.guild = guild
        self.response = _Response()
        self.original_edits: list[dict[str, object]] = []
        self.followups: list[dict[str, object]] = []
        self.followup = SimpleNamespace(send=self._followup_send)

    async def edit_original_response(self, **kwargs) -> None:
        self.original_edits.append(kwargs)

    async def _followup_send(self, **kwargs) -> None:
        self.followups.append(kwargs)


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
async def test_engagement_view_loads_with_select_driven_filters() -> None:
    loaded: list[tuple[int, str, str]] = []

    async def loader(*, eligible_users, window_key, role_filter_value):
        loaded.append((len(eligible_users), window_key, role_filter_value))
        return _contract(role_filter_value=role_filter_value)

    view = VoteAdminEngagementView(
        owner_user_id=123,
        eligible_users=(EngagementEligibleUser(100, "Alice", (10,), ("Kingdom Leadership",)),),
        report_loader=loader,
        role_filter_value="role:10",
        contract=None,
    )
    interaction = _Interaction(user_id=123)

    assert await view.ensure_contract(interaction) is True
    await view.edit_current(interaction)

    assert loaded == [(1, "last_3_months", "role:10")]
    assert interaction.response.deferred is True
    assert interaction.original_edits
    assert "Kingdom Leadership" in str(interaction.original_edits[-1]["embed"].to_dict())


@pytest.mark.asyncio
async def test_engagement_view_exports_private_csv() -> None:
    view = VoteAdminEngagementView(
        owner_user_id=123,
        eligible_users=(EngagementEligibleUser(100, "Alice", (10,), ("Kingdom Leadership",)),),
        contract=_contract(),
    )
    interaction = _Interaction(user_id=123)

    await view._on_export(interaction)

    assert interaction.response.deferred is True
    assert interaction.followups
    followup = interaction.followups[0]
    assert followup["ephemeral"] is True
    assert followup["file"].filename.startswith("vote_engagement_last_3_months_")
    assert "Voting engagement export" in str(followup["embed"].to_dict())


@pytest.mark.asyncio
async def test_engagement_view_rejects_other_admin(monkeypatch) -> None:
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.vote_admin_engagement_view.send_ephemeral", fake_send_ephemeral)
    view = VoteAdminEngagementView(
        owner_user_id=123,
        eligible_users=(),
        contract=_contract(),
    )

    assert await view.interaction_check(SimpleNamespace(user=SimpleNamespace(id=456))) is False
    assert sent == ["This engagement export belongs to another admin."]


@pytest.mark.asyncio
async def test_engagement_view_allows_owner_with_current_leadership_role() -> None:
    view = VoteAdminEngagementView(
        owner_user_id=123,
        eligible_users=(),
        contract=_contract(),
    )
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=123, roles=[_Role(10, "Kingdom Leadership")])
    )

    assert await view.interaction_check(interaction) is True


@pytest.mark.asyncio
async def test_engagement_view_rejects_owner_without_current_permission(monkeypatch) -> None:
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.vote_admin_engagement_view.send_ephemeral", fake_send_ephemeral)
    view = VoteAdminEngagementView(
        owner_user_id=123,
        eligible_users=(),
        contract=_contract(),
    )

    assert await view.interaction_check(SimpleNamespace(user=SimpleNamespace(id=123))) is False
    assert sent == ["You no longer have permission to use this engagement export."]
