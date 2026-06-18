# tests/test_stats_views_smoke.py
import asyncio

from ui.views.stats_views import KVKRankingView


def test_stats_views_kvkrankingview_instantiates():
    cache = {
        "_meta": {"generated_at": "2026-02-08"},
        "1": {"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"},
        "2": {"GovernorID": "2", "Starting Power": 90_000_000, "STATUS": "INCLUDED"},
    }

    async def _run():
        view = KVKRankingView(cache, metric="power", limit=10)
        assert view.metric == "power"
        assert view.limit == 10
        labels = [
            getattr(child, "label", None)
            for child in view.children
            if getattr(child, "label", None)
        ]
        assert labels == ["Top 10", "Top 25", "Top 50"]

    asyncio.run(_run())
