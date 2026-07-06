from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime

import pytest

from voting import reporting_service
from voting.reporting_models import (
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingOptionAggregate,
    DashboardReportingQuestionAggregate,
    DashboardReportingSummary,
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
