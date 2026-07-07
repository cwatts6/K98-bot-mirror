from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from ui.views.vote_admin_dashboard_view import VoteAdminDashboardView
from voting.reporting_models import (
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingContract,
    DashboardReportingSummary,
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
    def __init__(self, user_id: int = 123) -> None:
        self.user = SimpleNamespace(id=user_id)
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
