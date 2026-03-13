from __future__ import annotations

from datetime import UTC, datetime

from mge import mge_review_service


def test_get_signup_review_pool_sorts_as_required(monkeypatch):
    rows = [
        {
            "RequestPriority": "Low",
            "RequestedCommanderName": "Boudica",
            "PriorAwardsRequestedCommanderCount": 5,
            "PriorAwardsOverallLast2YearsCount": 4,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        },
        {
            "RequestPriority": "High",
            "RequestedCommanderName": "Charles",
            "PriorAwardsRequestedCommanderCount": 2,
            "PriorAwardsOverallLast2YearsCount": 3,
            "SignupCreatedUtc": datetime(2026, 3, 9, tzinfo=UTC),
        },
        {
            "RequestPriority": "High",
            "RequestedCommanderName": "Charles",
            "PriorAwardsRequestedCommanderCount": 1,
            "PriorAwardsOverallLast2YearsCount": 3,
            "SignupCreatedUtc": datetime(2026, 3, 11, tzinfo=UTC),
        },
        {
            "RequestPriority": "High",
            "RequestedCommanderName": "Charles",
            "PriorAwardsRequestedCommanderCount": 1,
            "PriorAwardsOverallLast2YearsCount": 2,
            "SignupCreatedUtc": datetime(2026, 3, 12, tzinfo=UTC),
        },
    ]

    monkeypatch.setattr(
        mge_review_service.mge_review_dal,
        "fetch_signup_review_rows",
        lambda event_id: rows,
    )

    out = mge_review_service.get_signup_review_pool(event_id=999)

    assert len(out) == 4
    assert out[0]["PriorAwardsRequestedCommanderCount"] == 1
    assert out[0]["PriorAwardsOverallLast2YearsCount"] == 2
    assert out[1]["PriorAwardsRequestedCommanderCount"] == 1
    assert out[1]["PriorAwardsOverallLast2YearsCount"] == 3
    assert out[2]["PriorAwardsRequestedCommanderCount"] == 2
    assert out[-1]["RequestPriority"] == "Low"


def test_get_signup_review_pool_null_safe(monkeypatch):
    rows = [
        {
            "RequestPriority": None,
            "RequestedCommanderName": None,
            "PriorAwardsRequestedCommanderCount": None,
            "PriorAwardsOverallLast2YearsCount": None,
            "SignupCreatedUtc": None,
        }
    ]
    monkeypatch.setattr(
        mge_review_service.mge_review_dal,
        "fetch_signup_review_rows",
        lambda event_id: rows,
    )

    out = mge_review_service.get_signup_review_pool(event_id=1)
    assert len(out) == 1


def test_get_review_pool_with_summary(monkeypatch):
    rows = [
        {
            "RequestPriority": "High",
            "RequestedCommanderName": "Scipio",
            "KingdomRole": "R4",
            "WarningMissingKVKData": 1,
            "WarningHeadsOutOfRange": 0,
            "WarningNoAttachments": 1,
            "WarningNoGearOrArmamentText": 0,
            "PriorAwardsRequestedCommanderCount": 0,
            "PriorAwardsOverallLast2YearsCount": 0,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        }
    ]

    monkeypatch.setattr(
        mge_review_service.mge_review_dal,
        "fetch_signup_review_rows",
        lambda event_id: rows,
    )

    payload = mge_review_service.get_review_pool_with_summary(event_id=77)
    assert payload["event_id"] == 77
    assert len(payload["rows"]) == 1
    assert payload["summary"]["total_rows"] == 1
    assert payload["summary"]["by_priority"]["High"] == 1
