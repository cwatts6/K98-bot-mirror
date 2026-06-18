from decimal import Decimal

import pytest

from kvk.models.kvk_rankings import HallOfFameMetric
from kvk.services import kvk_rankings_service


def test_normalize_ranking_limit_allows_primary_limits_only():
    assert kvk_rankings_service.normalize_ranking_limit(10) == 10
    assert kvk_rankings_service.normalize_ranking_limit(25) == 25
    assert kvk_rankings_service.normalize_ranking_limit(50) == 50
    assert kvk_rankings_service.normalize_ranking_limit(100) == 10


def test_normalize_hall_of_fame_limit_is_top_10_only():
    assert kvk_rankings_service.normalize_hall_of_fame_limit(None) == 10
    assert kvk_rankings_service.normalize_hall_of_fame_limit(10) == 10
    assert kvk_rankings_service.normalize_hall_of_fame_limit(25) == 10
    assert kvk_rankings_service.normalize_hall_of_fame_limit(50) == 10


def test_parse_hall_of_fame_metric_accepts_aliases():
    assert kvk_rankings_service.parse_hall_of_fame_metric("kp") == HallOfFameMetric.KILL_POINTS
    assert (
        kvk_rankings_service.parse_hall_of_fame_metric("PreKvK Points") == HallOfFameMetric.PREKVK
    )


def test_build_hall_of_fame_payload_from_rows_preserves_single_kvk_records():
    rows = [
        {
            "RecordRank": 1,
            "GovernorID": 123,
            "GovernorName": "Alice",
            "KVK_NO": 17,
            "KVK_NAME": "Light vs Dark",
            "MetricValue": Decimal("1234567.00"),
        },
        {
            "RecordRank": 2,
            "GovernorID": 123,
            "GovernorName": "Alice",
            "KVK_NO": 16,
            "KVK_NAME": "Strife",
            "MetricValue": Decimal("999999.00"),
        },
    ]

    payload = kvk_rankings_service.build_hall_of_fame_payload_from_rows(
        HallOfFameMetric.KILLS,
        rows,
        limit=10,
    )

    assert payload.mode == "records"
    assert payload.metric == "kills"
    assert payload.metric_label == "Kills"
    assert [row.governor_id for row in payload.rows] == [123, 123]
    assert payload.rows[0].kvk_name == "Light vs Dark"
    assert payload.rows[0].value == 1_234_567


@pytest.mark.asyncio
async def test_build_hall_of_fame_payload_fetches_dal_rows(monkeypatch):
    calls = {}

    def fake_fetch(metric, *, limit):
        calls["metric"] = metric
        calls["limit"] = limit
        return [
            {
                "RecordRank": 1,
                "GovernorID": 456,
                "GovernorName": "Bob",
                "KVK_NO": 15,
                "MetricValue": 5000,
            }
        ]

    monkeypatch.setattr(
        kvk_rankings_service.kvk_rankings_dal, "fetch_hall_of_fame_records", fake_fetch
    )

    payload = await kvk_rankings_service.build_hall_of_fame_payload(
        metric="honor",
        limit=25,
    )

    assert calls == {"metric": HallOfFameMetric.HONOR, "limit": 10}
    assert payload.rows[0].governor_name == "Bob"
    assert payload.metric_label == "Honor"
    assert payload.limit == 10
