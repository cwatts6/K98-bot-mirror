from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime

import pytest

from voting import reporting_service
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingOptionAggregate,
    DashboardReportingQuestionAggregate,
    DashboardReportingSummary,
    EngagementEligibleUser,
    EngagementItemSummary,
    EngagementParticipant,
)
from voting.service import VoteValidationError
from voting.survey_models import SurveyReportingOptionRow, SurveyReportingQuestionRow


def _summary(kind: str, content_id: int, closes_at: datetime) -> DashboardReportingSummary:
    return DashboardReportingSummary(
        content_kind=kind,
        content_id=content_id,
        title=f"{kind} {content_id}",
        status="Closed",
        result_visibility="HiddenUntilClose",
        created_at_utc=closes_at,
        closes_at_utc=closes_at,
        closed_at_utc=closes_at,
        total_participants=3,
        total_selections=4,
        option_count=2,
        question_count=1,
        required_question_count=1,
        optional_question_count=0,
        vote_mode="MultiSelect" if kind == REPORT_CONTENT_VOTE else None,
        answer_type_summary="1 choice" if kind == REPORT_CONTENT_SURVEY else "",
        message_link="https://discord" + ".com/channels/1/2/3",
    )


@pytest.mark.asyncio
async def test_admin_leadership_dashboard_report_is_aggregate_only(monkeypatch):
    now = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)

    async def fake_vote_summaries(*, limit):
        assert limit == 10
        return (_summary(REPORT_CONTENT_VOTE, 42, now),)

    async def fake_survey_summaries(*, limit):
        assert limit == 10
        return (
            _summary(REPORT_CONTENT_SURVEY, 77, now),
            _summary(REPORT_CONTENT_SURVEY, 78, now),
        )

    async def fake_vote_options(vote_post_ids):
        assert vote_post_ids == (42,)
        return (
            DashboardReportingOptionAggregate(
                content_kind=REPORT_CONTENT_VOTE,
                content_id=42,
                option_id=10,
                option_key="opt1",
                option_label="A",
                option_sort_order=1,
                total_participants=3,
                selection_count=2,
                is_top_selection=True,
            ),
            DashboardReportingOptionAggregate(
                content_kind=REPORT_CONTENT_VOTE,
                content_id=42,
                option_id=11,
                option_key="opt2",
                option_label="B",
                option_sort_order=2,
                total_participants=3,
                selection_count=1,
                is_top_selection=False,
            ),
        )

    async def fake_question_rows(survey_ids):
        assert survey_ids == (78, 77)
        return (
            SurveyReportingQuestionRow(
                survey_id=77,
                title="Planning",
                status="Closed",
                result_visibility="HiddenUntilClose",
                question_id=100,
                question_key="q1",
                question_prompt="Pick?",
                question_type="SingleChoice",
                question_sort_order=1,
                is_required=True,
                min_selections=1,
                max_selections=1,
                allow_details=False,
                total_responses=3,
                option_count=2,
                answered_responses=3,
                skipped_responses=0,
                choice_selection_count=3,
                ranked_option_count=0,
                ranking_first_place_count=0,
                average_rating=None,
                minimum_rating=None,
                maximum_rating=None,
                rating1_count=0,
                rating2_count=0,
                rating3_count=0,
                rating4_count=0,
                rating5_count=0,
            ),
        )

    async def fake_option_rows(survey_ids):
        assert survey_ids == (78, 77)
        return (
            SurveyReportingOptionRow(
                survey_id=77,
                title="Planning",
                status="Closed",
                result_visibility="HiddenUntilClose",
                question_id=100,
                question_key="q1",
                question_prompt="Pick?",
                question_type="SingleChoice",
                question_sort_order=1,
                is_required=True,
                option_id=101,
                option_key="opt1",
                option_label="A",
                option_sort_order=1,
                total_responses=3,
                selection_count=3,
                is_top_selection=True,
                ranked_count=0,
                average_rank=None,
                rank1_count=0,
                rank2_count=0,
                rank3_count=0,
                rank4_count=0,
                rank5_count=0,
                rank6_count=0,
            ),
        )

    async def forbidden_answer_audit(_survey_id):
        raise AssertionError("dashboard contract must not read raw response-detail rows")

    async def forbidden_per_survey_reporting(_survey_id):
        raise AssertionError("dashboard contract must use batch survey reporting rows")

    monkeypatch.setattr(
        reporting_service.reporting_dal, "list_vote_dashboard_summaries", fake_vote_summaries
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_dashboard_summaries",
        fake_survey_summaries,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_vote_dashboard_option_aggregates",
        fake_vote_options,
    )
    monkeypatch.setattr(
        reporting_service.survey_dal,
        "list_reporting_question_rows_for_surveys",
        fake_question_rows,
    )
    monkeypatch.setattr(
        reporting_service.survey_dal,
        "list_reporting_option_rows_for_surveys",
        fake_option_rows,
    )
    monkeypatch.setattr(
        reporting_service.survey_dal,
        "list_reporting_question_rows",
        forbidden_per_survey_reporting,
    )
    monkeypatch.setattr(
        reporting_service.survey_dal,
        "list_reporting_option_rows",
        forbidden_per_survey_reporting,
    )
    monkeypatch.setattr(
        reporting_service.survey_dal, "list_answer_audit_rows", forbidden_answer_audit
    )

    report = await reporting_service.build_admin_leadership_dashboard_report(limit=10)

    assert report.privacy_profile == REPORT_PRIVACY_PROFILE
    assert report.dashboard_safe is True
    assert report.contains_raw_text_or_detail is False
    assert report.contains_discord_identity is False
    assert report.raw_detail_access_profile == "private_exports_only"
    assert len(report.summaries) == 3
    assert report.summaries[0].top_summary == "Top selection: A (2)"
    assert report.question_aggregates[0].question_type == "SingleChoice"
    assert report.option_aggregates[-1].content_kind == REPORT_CONTENT_SURVEY


def test_dashboard_reporting_contract_models_do_not_expose_discord_identity_fields():
    checked = (
        DashboardReportingSummary,
        DashboardReportingQuestionAggregate,
        DashboardReportingOptionAggregate,
    )

    for model in checked:
        field_names = {field.name.lower() for field in fields(model)}
        assert not any("discord_user" in name for name in field_names)
        assert "discord_name" not in field_names


@pytest.mark.asyncio
async def test_dashboard_report_limit_must_be_positive():
    with pytest.raises(VoteValidationError, match="limit"):
        await reporting_service.build_admin_leadership_dashboard_report(limit=0)


@pytest.mark.asyncio
async def test_engagement_report_dedupes_discord_users_and_excludes_no_role_members(
    monkeypatch,
):
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    items = (
        EngagementItemSummary(REPORT_CONTENT_VOTE, 1, now, "Closed"),
        EngagementItemSummary(REPORT_CONTENT_SURVEY, 2, now, "Closed"),
    )
    participants = (
        EngagementParticipant(REPORT_CONTENT_VOTE, 1, 100, now),
        EngagementParticipant(REPORT_CONTENT_SURVEY, 2, 100, now),
        EngagementParticipant(REPORT_CONTENT_VOTE, 1, 200, now),
        EngagementParticipant(REPORT_CONTENT_SURVEY, 2, 300, now),
    )

    async def fake_vote_items(**_kwargs):
        return (items[0],)

    async def fake_survey_items(**_kwargs):
        return (items[1],)

    async def fake_vote_participants(**_kwargs):
        return participants[:2:2] + participants[2:3]

    async def fake_survey_participants(**_kwargs):
        return participants[1:2] + participants[3:]

    monkeypatch.setattr(
        reporting_service.reporting_dal, "list_vote_engagement_items", fake_vote_items
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_items",
        fake_survey_items,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_vote_engagement_participants",
        fake_vote_participants,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_participants",
        fake_survey_participants,
    )

    report = await reporting_service.build_admin_leadership_engagement_report(
        eligible_users=(
            EngagementEligibleUser(100, "Alice", (10,), ("Kingdom Leadership",)),
            EngagementEligibleUser(100, "Alice Alt Governor", (10,), ("Kingdom Leadership",)),
            EngagementEligibleUser(200, "NoRole"),
            EngagementEligibleUser(300, "Cara", (20,), ("R4",)),
        ),
        window_key=reporting_service.ENGAGEMENT_WINDOW_LAST_3_MONTHS,
        role_filter_value=reporting_service.ENGAGEMENT_ROLE_FILTER_EXPECTED,
        now=now,
    )

    assert report.privacy_profile == ENGAGEMENT_PRIVACY_PROFILE
    assert report.contains_discord_identity is True
    assert report.contains_raw_text_or_detail is False
    assert report.eligible_user_count == 2
    assert report.vote_post_count == 1
    assert report.survey_post_count == 1
    assert report.possible_participations == 4
    assert report.actual_participations == 3
    assert report.engagement_rate == pytest.approx(0.75)
    assert [row.discord_user_id for row in report.user_summaries] == [300, 100]
    assert report.user_summaries[0].vote_participation_count == 0
    assert report.user_summaries[0].survey_participation_count == 1
    assert report.user_summaries[1].vote_participation_count == 1
    assert report.user_summaries[1].survey_participation_count == 1


@pytest.mark.asyncio
async def test_engagement_report_keeps_duplicate_role_names_paired_with_role_ids(monkeypatch):
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)

    async def fake_empty_rows(**_kwargs):
        return ()

    monkeypatch.setattr(
        reporting_service.reporting_dal, "list_vote_engagement_items", fake_empty_rows
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_items",
        fake_empty_rows,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_vote_engagement_participants",
        fake_empty_rows,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_participants",
        fake_empty_rows,
    )

    report = await reporting_service.build_admin_leadership_engagement_report(
        eligible_users=(EngagementEligibleUser(400, "Dana", (30, 40), ("Shared", "Shared")),),
        role_filter_value="role:40",
        now=now,
    )

    assert report.role_filter_label == "Shared"
    assert report.eligible_user_count == 1
    assert report.user_summaries[0].role_names == ("Shared", "Shared")


@pytest.mark.asyncio
async def test_engagement_report_can_filter_to_specific_discord_role(monkeypatch):
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)

    async def fake_vote_items(**_kwargs):
        return (EngagementItemSummary(REPORT_CONTENT_VOTE, 1, now, "Closed"),)

    async def fake_survey_items(**_kwargs):
        return (EngagementItemSummary(REPORT_CONTENT_SURVEY, 2, now, "Closed"),)

    async def fake_vote_participants(**_kwargs):
        return (EngagementParticipant(REPORT_CONTENT_VOTE, 1, 100, now),)

    async def fake_survey_participants(**_kwargs):
        return (
            EngagementParticipant(REPORT_CONTENT_SURVEY, 2, 100, now),
            EngagementParticipant(REPORT_CONTENT_SURVEY, 2, 300, now),
        )

    monkeypatch.setattr(
        reporting_service.reporting_dal, "list_vote_engagement_items", fake_vote_items
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_items",
        fake_survey_items,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_vote_engagement_participants",
        fake_vote_participants,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_participants",
        fake_survey_participants,
    )

    report = await reporting_service.build_admin_leadership_engagement_report(
        eligible_users=(
            EngagementEligibleUser(100, "Alice", (10,), ("Kingdom Leadership",)),
            EngagementEligibleUser(300, "Cara", (20,), ("R4",)),
        ),
        role_filter_value="role:10",
        now=now,
    )

    assert report.role_filter_label == "Kingdom Leadership"
    assert report.eligible_user_count == 1
    assert report.possible_participations == 2
    assert report.actual_participations == 2
    assert report.user_summaries[0].discord_user_id == 100


@pytest.mark.asyncio
async def test_engagement_report_includes_best_and_worst_poll_with_newest_tie_breaker(
    monkeypatch,
):
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    older = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    newer = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    items = (
        EngagementItemSummary(REPORT_CONTENT_VOTE, 1, older, "Closed", "Old low poll"),
        EngagementItemSummary(REPORT_CONTENT_VOTE, 2, newer, "Closed", "New low poll"),
        EngagementItemSummary(REPORT_CONTENT_SURVEY, 3, now, "Closed", "Best poll"),
    )

    async def fake_vote_items(**_kwargs):
        return items[:2]

    async def fake_survey_items(**_kwargs):
        return items[2:]

    async def fake_vote_participants(**_kwargs):
        return ()

    async def fake_survey_participants(**_kwargs):
        return (
            EngagementParticipant(REPORT_CONTENT_SURVEY, 3, 100, now),
            EngagementParticipant(REPORT_CONTENT_SURVEY, 3, 200, now),
        )

    monkeypatch.setattr(
        reporting_service.reporting_dal, "list_vote_engagement_items", fake_vote_items
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_items",
        fake_survey_items,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_vote_engagement_participants",
        fake_vote_participants,
    )
    monkeypatch.setattr(
        reporting_service.reporting_dal,
        "list_survey_engagement_participants",
        fake_survey_participants,
    )

    report = await reporting_service.build_admin_leadership_engagement_report(
        eligible_users=(
            EngagementEligibleUser(100, "Alice", (10,), ("Kingdom Leadership",)),
            EngagementEligibleUser(200, "Bob", (10,), ("Kingdom Leadership",)),
        ),
        role_filter_value=reporting_service.ENGAGEMENT_ROLE_FILTER_EXPECTED,
        now=now,
    )

    assert report.best_item is not None
    assert report.best_item.title == "Best poll"
    assert report.best_item.actual_participations == 2
    assert report.best_item.possible_participations == 2
    assert report.worst_item is not None
    assert report.worst_item.title == "New low poll"
    assert report.worst_item.engagement_rate == pytest.approx(0.0)
