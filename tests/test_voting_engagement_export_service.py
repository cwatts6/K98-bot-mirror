from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from voting.engagement_export_service import (
    build_engagement_csv_bytes,
    build_engagement_csv_export,
    engagement_csv_rows,
)
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    EngagementReportingContract,
    EngagementUserSummary,
)


def _contract() -> EngagementReportingContract:
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    return EngagementReportingContract(
        generated_at_utc=now,
        privacy_profile=ENGAGEMENT_PRIVACY_PROFILE,
        window_key="last_3_months",
        window_label="Last 3 months",
        window_start_utc=now,
        window_end_utc=now,
        role_filter_value="role:10",
        role_filter_label="=Kingdom Leadership",
        eligible_user_count=2,
        vote_post_count=2,
        survey_post_count=1,
        possible_participations=6,
        actual_participations=4,
        engagement_rate=4 / 6,
        user_summaries=(
            EngagementUserSummary(
                discord_user_id=100,
                display_name="=Alice",
                role_names=("@Lead",),
                participation_count=1,
                possible_count=3,
                engagement_rate=1 / 3,
                last_participated_at_utc=now,
                vote_participation_count=1,
                survey_participation_count=0,
            ),
            EngagementUserSummary(
                discord_user_id=200,
                display_name="Bob",
                role_names=("R4",),
                participation_count=3,
                possible_count=3,
                engagement_rate=1.0,
                last_participated_at_utc=now,
                vote_participation_count=2,
                survey_participation_count=1,
            ),
        ),
        monthly_buckets=(),
    )


def test_engagement_csv_rows_sort_highest_engagement_first_and_include_split_counts() -> None:
    rows = engagement_csv_rows(_contract())

    assert [row["DiscordUserID"] for row in rows] == ["'200", "'100"]
    assert rows[0]["VoteParticipationCount"] == 2
    assert rows[0]["SurveyParticipationCount"] == 1
    assert rows[0]["MissedCount"] == 0
    assert rows[1]["MissedCount"] == 2


def test_engagement_csv_bytes_are_spreadsheet_safe() -> None:
    text = build_engagement_csv_bytes(_contract()).getvalue().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))

    assert rows[0]["DiscordUserID"] == "'200"
    assert rows[1]["DiscordUserID"] == "'100"
    assert rows[1]["DiscordDisplayName"] == "'=Alice"
    assert rows[1]["RoleNames"] == "'@Lead"
    assert rows[0]["RoleFilter"] == "'=Kingdom Leadership"
    assert "AnswerText" not in text
    assert "DetailText" not in text


def test_build_engagement_csv_export_names_file_and_rewinds_bytes() -> None:
    export = build_engagement_csv_export(_contract(), requested_by_discord_user_id=999)

    assert export.filename.startswith("vote_engagement_last_3_months_kingdom_leadership_")
    assert export.filename.endswith(".csv")
    assert export.row_count == 2
    assert export.csv_bytes.tell() == 0
    assert export.is_oversized() is False

