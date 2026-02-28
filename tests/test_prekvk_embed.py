from types import SimpleNamespace

import pytest

import stats_alerts.embeds.prekvk as prekvk_mod

pytestmark = pytest.mark.asyncio


class DummyChannel:
    def __init__(self):
        self.sent = None

    async def send(self, embed=None, content=None, view=None, allowed_mentions=None):
        # emulate discord.Message with id attribute
        m = SimpleNamespace(id=9999, embed=embed, content=content, view=view)
        self.sent = m
        return m

    async def fetch_message(self, mid):
        raise Exception("no message")


async def test_send_prekvk_embed_uses_prekvk_stats(monkeypatch):
    # Prepare fake metadata
    monkeypatch.setattr(
        prekvk_mod, "get_latest_kvk_metadata_sql", lambda: {"kvk_no": 42, "kvk_name": "KVK42"}
    )

    # Fake prekvk top helper: current (3) and prev (1)
    fake_tops = {
        "overall": [{"Name": "Alice", "Points": 200}, {"Name": "Bob", "Points": 180}],
        "p1": [{"Name": "P1A", "Points": 50}],
        "p2": [{"Name": "P2A", "Points": 40}],
        "p3": [{"Name": "P3A", "Points": 30}],
    }
    fake_prev = {
        "overall": [{"Name": "LastTop", "Points": 210}],
        "p1": [{"Name": "LastP1", "Points": 60}],
        "p2": [{"Name": "LastP2", "Points": 55}],
        "p3": [{"Name": "LastP3", "Points": 45}],
    }

    # monkeypatch load_prekvk_top3 to return fake_tops / fake_prev depending on args
    def fake_load(kvk_no, limit):
        return fake_prev if (limit == 1 and kvk_no == 41) else fake_tops

    monkeypatch.setattr(prekvk_mod, "load_prekvk_top3", fake_load)

    # stub other dependencies to keep embed small
    monkeypatch.setattr(
        prekvk_mod,
        "load_kingdom_summary",
        lambda: {
            "KINGDOM_POWER": 123456,
            "Governors": 12,
            "KP": 98765,
            "DEAD": 1234,
            "KINGDOM_RANK": 2,
            "KINGDOM_SEED": 3,
        },
    )
    monkeypatch.setattr(prekvk_mod, "get_all_upcoming_events", lambda: [])
    monkeypatch.setattr(prekvk_mod, "get_latest_honor_top", lambda n: [])

    ch = DummyChannel()
    res = await prekvk_mod.send_prekvk_embed(None, ch, "2026-01-05 00:00 UTC", is_test=True)
    assert res == "sent"
    assert ch.sent is not None
    embed = ch.sent.embed
    # Verify embed fields contain the previous overall top1 field and phase last-kvk fields
    names = [f.name for f in embed.fields]
    assert any("Overall — Top (last kvk)" in n for n in names)
    assert any("Phase 1 — Marauders (last kvk)" in n for n in names)
