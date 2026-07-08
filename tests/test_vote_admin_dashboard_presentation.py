from __future__ import annotations

from datetime import UTC, datetime

from voting.dashboard_presentation import (
    DASHBOARD_FILTER_OPEN,
    DASHBOARD_FILTER_SURVEYS,
    build_dashboard_embeds,
    build_engagement_dashboard_embeds,
    filter_dashboard_summaries,
)
from voting.option_emojis import normalize_option_emoji
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingContract,
    DashboardReportingOptionAggregate,
    DashboardReportingQuestionAggregate,
    DashboardReportingSummary,
    EngagementMonthlyBucket,
    EngagementReportingContract,
    EngagementUserSummary,
)


def _summary(kind: str, content_id: int, *, status: str = "Closed") -> DashboardReportingSummary:
    now = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    return DashboardReportingSummary(
        content_kind=kind,
        content_id=content_id,
        title=f"{kind} {content_id}",
        status=status,
        result_visibility="HiddenUntilClose",
        created_at_utc=now,
        closes_at_utc=now,
        closed_at_utc=None if status == "Open" else now,
        total_participants=5,
        total_selections=7,
        option_count=2,
        question_count=2 if kind == REPORT_CONTENT_SURVEY else 1,
        required_question_count=1,
        optional_question_count=1 if kind == REPORT_CONTENT_SURVEY else 0,
        vote_mode="MultiSelect" if kind == REPORT_CONTENT_VOTE else None,
        answer_type_summary="1 text, 1 rating" if kind == REPORT_CONTENT_SURVEY else "",
        top_summary="Top selection: A (4)",
        message_link="https://discord.com/channels/1/2/3",
    )


def _contract() -> DashboardReportingContract:
    now = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    return DashboardReportingContract(
        generated_at_utc=now,
        privacy_profile=REPORT_PRIVACY_PROFILE,
        summaries=(
            _summary(REPORT_CONTENT_VOTE, 42, status="Open"),
            _summary(REPORT_CONTENT_SURVEY, 77, status="Closed"),
        ),
        question_aggregates=(
            DashboardReportingQuestionAggregate(
                content_kind=REPORT_CONTENT_SURVEY,
                content_id=77,
                question_id=100,
                question_key="q1",
                question_prompt="Tell us why",
                question_type="Text",
                question_sort_order=1,
                is_required=False,
                allow_details=False,
                total_responses=5,
                answered_responses=3,
                skipped_responses=2,
                choice_selection_count=0,
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
            DashboardReportingQuestionAggregate(
                content_kind=REPORT_CONTENT_SURVEY,
                content_id=77,
                question_id=101,
                question_key="q2",
                question_prompt="Rate it",
                question_type="Rating",
                question_sort_order=2,
                is_required=True,
                allow_details=False,
                total_responses=5,
                answered_responses=5,
                skipped_responses=0,
                choice_selection_count=0,
                ranked_option_count=0,
                ranking_first_place_count=0,
                average_rating=4.2,
                minimum_rating=3,
                maximum_rating=5,
                rating1_count=0,
                rating2_count=0,
                rating3_count=1,
                rating4_count=2,
                rating5_count=2,
            ),
        ),
        option_aggregates=(
            DashboardReportingOptionAggregate(
                content_kind=REPORT_CONTENT_VOTE,
                content_id=42,
                option_id=1,
                option_key="opt1",
                option_label="A",
                option_sort_order=1,
                total_participants=5,
                selection_count=4,
                is_top_selection=True,
            ),
        ),
    )


def test_dashboard_embeds_are_private_aggregate_only() -> None:
    embeds = build_dashboard_embeds(_contract(), filter_value=DASHBOARD_FILTER_SURVEYS)

    assert len(embeds) == 1
    rendered = str(embeds[0].to_dict())
    assert "private text responses counted only" in rendered
    assert "avg 4.2/5" in rendered
    assert "Aggregate-only private dashboard" in rendered
    assert "DiscordUserID" not in rendered
    assert "DiscordName" not in rendered
    assert "AnswerText" not in rendered
    assert "DetailText" not in rendered


def test_dashboard_filter_can_limit_to_open_items() -> None:
    rows = filter_dashboard_summaries(_contract().summaries, DASHBOARD_FILTER_OPEN)

    assert len(rows) == 1
    assert rows[0].content_kind == REPORT_CONTENT_VOTE
    assert rows[0].status == "Open"


def test_dashboard_embed_fields_are_clipped_to_discord_limit() -> None:
    contract = _contract()
    long_options = tuple(
        DashboardReportingOptionAggregate(
            content_kind=REPORT_CONTENT_VOTE,
            content_id=42,
            option_id=index,
            option_key=f"opt{index}",
            option_label=f"Option {index} " + ("x" * 160),
            option_sort_order=index,
            total_participants=5,
            selection_count=index,
            is_top_selection=index == 1,
        )
        for index in range(1, 13)
    )
    contract = DashboardReportingContract(
        generated_at_utc=contract.generated_at_utc,
        privacy_profile=contract.privacy_profile,
        summaries=contract.summaries,
        question_aggregates=contract.question_aggregates,
        option_aggregates=long_options,
    )

    embed = build_dashboard_embeds(contract)[0]
    option_totals = next(
        field["value"] for field in embed.to_dict()["fields"] if field["name"] == "Option totals"
    )

    assert len(option_totals) <= 1024
    assert option_totals.endswith("...")


def test_dashboard_option_totals_include_display_emoji() -> None:
    contract = _contract()
    contract = DashboardReportingContract(
        generated_at_utc=contract.generated_at_utc,
        privacy_profile=contract.privacy_profile,
        summaries=contract.summaries,
        question_aggregates=contract.question_aggregates,
        option_aggregates=(
            DashboardReportingOptionAggregate(
                content_kind=REPORT_CONTENT_VOTE,
                content_id=42,
                option_id=1,
                option_key="opt1",
                option_label="A",
                option_sort_order=1,
                total_participants=5,
                selection_count=4,
                is_top_selection=True,
                option_emoji=normalize_option_emoji("✅"),
            ),
        ),
    )

    embed = build_dashboard_embeds(contract)[0]
    option_totals = next(
        field["value"] for field in embed.to_dict()["fields"] if field["name"] == "Option totals"
    )

    assert "✅ A" in option_totals


def test_dashboard_refuses_to_render_unsafe_contract() -> None:
    contract = _contract()
    unsafe = DashboardReportingContract(
        generated_at_utc=contract.generated_at_utc,
        privacy_profile=contract.privacy_profile,
        summaries=(_summary(REPORT_CONTENT_SURVEY, 99, status="Open"),),
        question_aggregates=contract.question_aggregates,
        option_aggregates=contract.option_aggregates,
        dashboard_safe=False,
        contains_raw_text_or_detail=True,
        contains_discord_identity=True,
    )

    embed = build_dashboard_embeds(unsafe)[0]
    rendered = str(embed.to_dict())

    assert "Voting dashboard unavailable" in rendered
    assert "failed privacy validation" in rendered
    assert "survey 99" not in rendered
    assert "private text responses counted only" not in rendered
    assert "not dashboard-safe" in rendered


def test_engagement_dashboard_renders_private_identity_summary() -> None:
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    contract = EngagementReportingContract(
        generated_at_utc=now,
        privacy_profile=ENGAGEMENT_PRIVACY_PROFILE,
        window_key="last_3_months",
        window_label="Last 3 months",
        window_start_utc=now,
        window_end_utc=now,
        role_filter_value="role:10",
        role_filter_label="Kingdom Leadership",
        eligible_user_count=2,
        vote_post_count=1,
        survey_post_count=1,
        possible_participations=4,
        actual_participations=3,
        engagement_rate=0.75,
        user_summaries=(
            EngagementUserSummary(
                discord_user_id=100,
                display_name="Alice",
                role_names=("Kingdom Leadership",),
                participation_count=1,
                possible_count=2,
                engagement_rate=0.5,
                last_participated_at_utc=now,
            ),
        ),
        monthly_buckets=(
            EngagementMonthlyBucket(
                month_key="2026-07",
                month_label="July 2026",
                vote_post_count=1,
                survey_post_count=1,
                possible_participations=4,
                actual_participations=3,
                engagement_rate=0.75,
            ),
        ),
    )

    embed = build_engagement_dashboard_embeds(contract)[0]
    rendered = str(embed.to_dict())

    assert "Kingdom Leadership" in rendered
    assert "Alice" in rendered
    assert "3/4" in rendered
    assert "Private leadership engagement" in rendered
    assert "AnswerText" not in rendered
    assert "DetailText" not in rendered


def test_engagement_dashboard_refuses_raw_detail_contract() -> None:
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    contract = EngagementReportingContract(
        generated_at_utc=now,
        privacy_profile=ENGAGEMENT_PRIVACY_PROFILE,
        window_key="last_month",
        window_label="Last month",
        window_start_utc=now,
        window_end_utc=now,
        role_filter_value="expected",
        role_filter_label="Expected roles",
        eligible_user_count=1,
        vote_post_count=1,
        survey_post_count=0,
        possible_participations=1,
        actual_participations=0,
        engagement_rate=0.0,
        user_summaries=(
            EngagementUserSummary(100, "Alice", ("Kingdom Leadership",), 0, 1, 0.0, None),
        ),
        monthly_buckets=(),
        contains_raw_text_or_detail=True,
    )

    rendered = str(build_engagement_dashboard_embeds(contract)[0].to_dict())

    assert "Voting engagement unavailable" in rendered
    assert "Alice" not in rendered
