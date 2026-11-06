from prekvk.models import (
    PreKvkScheduledSummary,
    PreKvkScheduledTopBlocks,
    PreKvkScheduledTopEntry,
)
from stats_alerts import prekvk_stats


def test_load_prekvk_top3_delegates_to_scheduled_summary(monkeypatch):
    calls = []

    def fake_summary(**kwargs):
        calls.append(kwargs)
        return PreKvkScheduledSummary(
            kvk_no=15,
            current=PreKvkScheduledTopBlocks(
                overall=[
                    PreKvkScheduledTopEntry("Alice", 150),
                    PreKvkScheduledTopEntry("Bob", 120),
                ],
                p1=[PreKvkScheduledTopEntry("Charlie", 40)],
                p2=[PreKvkScheduledTopEntry("Delta", 30)],
                p3=[PreKvkScheduledTopEntry("Echo", 20)],
            ),
        )

    monkeypatch.setattr(
        prekvk_stats.report_service,
        "build_prekvk_scheduled_summary_sync",
        fake_summary,
    )

    out = prekvk_stats.load_prekvk_top3(15, limit=3)

    assert calls == [{"kvk_no": 15, "current_limit": 3}]
    assert set(out.keys()) == {"overall", "p1", "p2", "p3"}
    assert out["overall"][0] == {"Name": "Alice", "Points": 150}
    assert out["p1"][0] == {"Name": "Charlie", "Points": 40}


def test_load_prekvk_top3_preserves_empty_shape_for_invalid_kvk(monkeypatch):
    def fail_summary(**_kwargs):
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        prekvk_stats.report_service,
        "build_prekvk_scheduled_summary_sync",
        fail_summary,
    )

    assert prekvk_stats.load_prekvk_top3(0) == {"overall": [], "p1": [], "p2": [], "p3": []}


def test_load_prekvk_top3_returns_empty_shape_on_service_failure(monkeypatch):
    def fail_summary(**_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        prekvk_stats.report_service,
        "build_prekvk_scheduled_summary_sync",
        fail_summary,
    )

    assert prekvk_stats.load_prekvk_top3(15) == {"overall": [], "p1": [], "p2": [], "p3": []}
