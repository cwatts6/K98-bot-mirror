from __future__ import annotations

import os
import sys
import types

sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
os.environ.setdefault("OUR_KINGDOM", "0")
if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

from datetime import UTC, datetime

import pytest

from mge import mge_simplified_flow_service as svc


def test_sort_review_rows_orders_by_priority_then_kvk_rank_then_signup_identity() -> None:
    rows = [
        {
            "SignupId": 30,
            "RequestPriority": "Medium",
            "LatestKVKRank": 5,
            "SignupCreatedUtc": datetime(2026, 3, 12, tzinfo=UTC),
        },
        {
            "SignupId": 10,
            "RequestPriority": "High",
            "LatestKVKRank": 8,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        },
        {
            "SignupId": 11,
            "RequestPriority": "High",
            "LatestKVKRank": 3,
            "SignupCreatedUtc": datetime(2026, 3, 11, tzinfo=UTC),
        },
        {
            "SignupId": 31,
            "RequestPriority": "Low",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 3, 9, tzinfo=UTC),
        },
    ]

    ordered = svc.sort_review_rows(rows)

    assert [row["SignupId"] for row in ordered] == [11, 10, 30, 31]


def test_sort_review_rows_places_missing_kvk_rank_last_in_priority_bucket() -> None:
    rows = [
        {
            "SignupId": 1,
            "RequestPriority": "High",
            "LatestKVKRank": None,
            "LastKVKRank": None,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        },
        {
            "SignupId": 2,
            "RequestPriority": "High",
            "LatestKVKRank": 6,
            "SignupCreatedUtc": datetime(2026, 3, 9, tzinfo=UTC),
        },
    ]

    ordered = svc.sort_review_rows(rows)

    assert [row["SignupId"] for row in ordered] == [2, 1]


def test_build_leadership_dataset_keeps_missing_awards_unassigned_and_excludes_rejected_from_active_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_rows = [
        {
            "EventId": 77,
            "SignupId": 1,
            "GovernorId": 101,
            "GovernorNameSnapshot": "G101",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Cmdr",
            "RequestPriority": "High",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 3, 9, tzinfo=UTC),
        },
        {
            "EventId": 77,
            "SignupId": 2,
            "GovernorId": 102,
            "GovernorNameSnapshot": "G102",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Cmdr",
            "RequestPriority": "Medium",
            "LatestKVKRank": 2,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        },
        {
            "EventId": 77,
            "SignupId": 3,
            "GovernorId": 103,
            "GovernorNameSnapshot": "G103",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Cmdr",
            "RequestPriority": "Low",
            "LatestKVKRank": 3,
            "SignupCreatedUtc": datetime(2026, 3, 11, tzinfo=UTC),
        },
    ]
    award_rows = [
        {"SignupId": 2, "AwardId": 22, "AwardStatus": "waitlist", "WaitlistOrder": 1},
        {"SignupId": 3, "AwardId": 33, "AwardStatus": "rejected"},
    ]

    # in-memory DAL stubs so self-heal cannot hit real I/O
    store = list(award_rows)

    def _insert_award(**kwargs):
        new_id = 100 + len(store)
        store.append(
            {
                "SignupId": kwargs["signup_id"],
                "AwardId": new_id,
                "AwardStatus": kwargs["award_status"],
                "AwardedRank": kwargs.get("awarded_rank"),
                "WaitlistOrder": kwargs.get("waitlist_order"),
                "ManualOrderOverride": kwargs.get("manual_order_override", False),
            }
        )
        return new_id

    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.insert_award", _insert_award
    )
    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.fetch_event_awards",
        lambda event_id: list(store),
    )

    dataset = svc.build_leadership_ordered_dataset(review_rows, award_rows)

    # signup 1 should now self-heal into roster (not remain unassigned)
    assert [row["SignupId"] for row in dataset["roster_rows"]] == [1]
    assert [row["SignupId"] for row in dataset["waitlist_rows"]] == [2]
    assert [row["SignupId"] for row in dataset["rejected_rows"]] == [3]
    assert dataset["counts"]["unassigned_count"] == 0


def test_build_leadership_dataset_preserves_manual_roster_override_positions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_rows = [
        {
            "EventId": 77,
            "SignupId": 1,
            "GovernorId": 101,
            "GovernorNameSnapshot": "G101",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Cmdr",
            "RequestPriority": "High",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 3, 9, tzinfo=UTC),
        },
        {
            "EventId": 77,
            "SignupId": 2,
            "GovernorId": 102,
            "GovernorNameSnapshot": "G102",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Cmdr",
            "RequestPriority": "High",
            "LatestKVKRank": 2,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        },
        {
            "EventId": 77,
            "SignupId": 3,
            "GovernorId": 103,
            "GovernorNameSnapshot": "G103",
            "RequestedCommanderId": 1,
            "RequestedCommanderName": "Cmdr",
            "RequestPriority": "High",
            "LatestKVKRank": 3,
            "SignupCreatedUtc": datetime(2026, 3, 11, tzinfo=UTC),
        },
    ]
    award_rows = [
        {
            "SignupId": 2,
            "AwardId": 22,
            "AwardStatus": "awarded",
            "AwardedRank": 1,
            "ManualOrderOverride": 1,
        },
    ]

    store = list(award_rows)

    def _insert_award(**kwargs):
        new_id = 100 + len(store)
        store.append(
            {
                "SignupId": kwargs["signup_id"],
                "AwardId": new_id,
                "AwardStatus": kwargs["award_status"],
                "AwardedRank": kwargs.get("awarded_rank"),
                "WaitlistOrder": kwargs.get("waitlist_order"),
                "ManualOrderOverride": kwargs.get("manual_order_override", False),
            }
        )
        return new_id

    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.insert_award", _insert_award
    )
    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.fetch_event_awards",
        lambda event_id: list(store),
    )

    dataset = svc.build_leadership_ordered_dataset(review_rows, award_rows)

    roster = dataset["roster_rows"]
    # manual override row remains first/pinned
    assert roster[0]["SignupId"] == 2
    assert roster[0]["ComputedAwardedRank"] == 1

    # self-heal adds the other active signups into roster when space exists
    assert set(row["SignupId"] for row in roster) == {1, 2, 3}
    assert dataset["counts"]["unassigned_count"] == 0


def test_evaluate_publish_readiness_blocked_when_roster_exceeds_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "counts": {
                "total_signups": 16,
                "roster_count": 16,
                "waitlist_count": 0,
                "rejected_count": 0,
            },
            "rows": [{"AwardStatus": "awarded", "TargetScore": 1}] * 16,
            "roster_rows": [{"TargetScore": 1}] * 16,
        },
    )

    readiness = svc.evaluate_publish_readiness(1)

    assert readiness["publish_ready"] is False
    assert "roster_count_exceeds_limit" in readiness["publish_block_reason_codes"]


def test_evaluate_publish_readiness_blocked_when_roster_targets_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "counts": {
                "total_signups": 3,
                "roster_count": 2,
                "waitlist_count": 1,
                "rejected_count": 0,
            },
            "rows": [
                {"AwardStatus": "awarded", "TargetScore": 8_000_000},
                {"AwardStatus": "awarded", "TargetScore": None},
                {"AwardStatus": "waitlist", "TargetScore": None},
            ],
            "roster_rows": [{"TargetScore": 8_000_000}, {"TargetScore": None}],
        },
    )

    readiness = svc.evaluate_publish_readiness(1)

    assert readiness["publish_ready"] is False
    assert readiness["missing_roster_target_count"] == 1
    assert "missing_roster_targets" in readiness["publish_block_reason_codes"]


def test_evaluate_publish_readiness_ready_when_roster_constraints_met(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "counts": {
                "total_signups": 4,
                "roster_count": 2,
                "waitlist_count": 1,
                "rejected_count": 1,
            },
            "rows": [
                {"AwardStatus": "awarded", "TargetScore": 8_000_000},
                {"AwardStatus": "roster", "TargetScore": 7_000_000},
                {"AwardStatus": "waitlist", "TargetScore": None},
                {"AwardStatus": "rejected", "TargetScore": None},
            ],
            "roster_rows": [{"TargetScore": 8_000_000}, {"TargetScore": 7_000_000}],
        },
    )

    readiness = svc.evaluate_publish_readiness(1)

    assert readiness["publish_ready"] is True
    assert readiness["publish_block_reason_codes"] == []
    assert readiness["publish_status_text"] == "Ready to publish."


def test_evaluate_publish_readiness_ignores_unassigned_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        svc,
        "get_ordered_leadership_rows",
        lambda event_id: {
            "rows": [
                {"SignupId": 1, "AwardStatus": "awarded", "TargetScore": 8_000_000},
                {"SignupId": 2, "AwardStatus": "waitlist", "TargetScore": None},
                {"SignupId": 3, "AwardStatus": "unassigned", "TargetScore": None},
            ],
            "counts": {
                "total_signups": 3,
                "roster_count": 1,
                "waitlist_count": 1,
                "unassigned_count": 1,
                "rejected_count": 0,
            },
        },
    )

    readiness = svc.evaluate_publish_readiness(1)
    assert readiness["publish_ready"] is True


# ---- Appended Phase 1 tests (auto-placement + self-heal) ----


def _review(signup_id: int, governor_id: int, priority: str = "medium", kvk: int = 100) -> dict:
    return {
        "EventId": 77,
        "SignupId": signup_id,
        "GovernorId": governor_id,
        "GovernorNameSnapshot": f"G{governor_id}",
        "RequestedCommanderId": 1,
        "RequestedCommanderName": "Cmdr",
        "RequestPriority": priority,
        "LatestKVKRank": kvk,
        "SignupCreatedUtc": datetime.now(UTC),
    }


def test_build_dataset_self_heals_unassigned_to_roster_when_space(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_rows = [_review(1, 101), _review(2, 102), _review(3, 103), _review(4, 104)]
    existing_awards = [
        {"SignupId": 1, "AwardId": 11, "AwardStatus": "awarded", "AwardedRank": 1},
        {"SignupId": 2, "AwardId": 12, "AwardStatus": "awarded", "AwardedRank": 2},
        {"SignupId": 3, "AwardId": 13, "AwardStatus": "awarded", "AwardedRank": 3},
    ]

    inserted: list[dict] = []
    store = list(existing_awards)

    def _insert_award(**kwargs):
        aid = 100 + len(inserted) + 1
        inserted.append(dict(kwargs))
        store.append(
            {
                "SignupId": kwargs["signup_id"],
                "AwardId": aid,
                "AwardStatus": kwargs["award_status"],
                "AwardedRank": kwargs.get("awarded_rank"),
                "WaitlistOrder": kwargs.get("waitlist_order"),
                "ManualOrderOverride": kwargs.get("manual_order_override", False),
            }
        )
        return aid

    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.insert_award", _insert_award
    )
    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.fetch_event_awards",
        lambda event_id: list(store),
    )

    dataset = svc.build_leadership_ordered_dataset(review_rows, existing_awards)

    assert dataset["counts"]["roster_count"] == 4
    assert dataset["counts"]["waitlist_count"] == 0
    assert dataset["counts"]["unassigned_count"] == 0
    assert inserted and inserted[0]["award_status"] == "awarded"


def test_build_dataset_self_heals_16th_to_waitlist(monkeypatch: pytest.MonkeyPatch) -> None:
    review_rows = [_review(i, 1000 + i, kvk=i) for i in range(1, 17)]
    existing_awards = [
        {"SignupId": i, "AwardId": 200 + i, "AwardStatus": "awarded", "AwardedRank": i}
        for i in range(1, 16)
    ]

    inserted: list[dict] = []
    store = list(existing_awards)

    def _insert_award(**kwargs):
        aid = 500 + len(inserted) + 1
        inserted.append(dict(kwargs))
        store.append(
            {
                "SignupId": kwargs["signup_id"],
                "AwardId": aid,
                "AwardStatus": kwargs["award_status"],
                "AwardedRank": kwargs.get("awarded_rank"),
                "WaitlistOrder": kwargs.get("waitlist_order"),
                "ManualOrderOverride": kwargs.get("manual_order_override", False),
            }
        )
        return aid

    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.insert_award", _insert_award
    )
    monkeypatch.setattr(
        "mge.mge_simplified_flow_service.mge_roster_dal.fetch_event_awards",
        lambda event_id: list(store),
    )

    dataset = svc.build_leadership_ordered_dataset(review_rows, existing_awards)

    assert dataset["counts"]["roster_count"] == 15
    assert dataset["counts"]["waitlist_count"] == 1
    assert dataset["counts"]["unassigned_count"] == 0
    assert inserted and inserted[0]["award_status"] == "waitlist"
