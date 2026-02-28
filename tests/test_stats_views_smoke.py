# tests/test_stats_views_smoke.py
import asyncio
import sys
import types

utils_stub = types.ModuleType("utils")
utils_stub.fmt_short = lambda v: str(v)
sys.modules.setdefault("utils", utils_stub)

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
        assert len(view.children) >= 5

    asyncio.run(_run())
