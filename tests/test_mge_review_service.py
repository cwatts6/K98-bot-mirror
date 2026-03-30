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

from mge import mge_review_service


def test_get_signup_review_pool_sorts_as_required(monkeypatch):
    rows = [
        {
            "SignupId": 3,
            "RequestPriority": "Low",
            "LatestKVKRank": 1,
            "SignupCreatedUtc": datetime(2026, 3, 10, tzinfo=UTC),
        },
        {
            "SignupId": 2,
            "RequestPriority": "High",
            "LatestKVKRank": 5,
            "SignupCreatedUtc": datetime(2026, 3, 9, tzinfo=UTC),
        },
        {
            "SignupId": 4,
            "RequestPriority": "High",
            "LatestKVKRank": None,
            "LastKVKRank": None,
            "SignupCreatedUtc": datetime(2026, 3, 8, tzinfo=UTC),
        },
        {
            "SignupId": 1,
            "RequestPriority": "High",
            "LatestKVKRank": 2,
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
    assert [row["SignupId"] for row in out] == [1, 2, 4, 3]


def test_get_signup_review_pool_null_safe(monkeypatch):
    rows = [
        {
            "RequestPriority": None,
            "RequestedCommanderName": None,
            "LatestKVKRank": None,
            "LastKVKRank": None,
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
            "SignupId": 1,
            "RequestPriority": "High",
            "RequestedCommanderName": "Scipio",
            "KingdomRole": "R4",
            "WarningMissingKVKData": 1,
            "WarningHeadsOutOfRange": 0,
            "WarningNoAttachments": 1,
            "WarningNoGearOrArmamentText": 0,
            "LatestKVKRank": 1,
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
