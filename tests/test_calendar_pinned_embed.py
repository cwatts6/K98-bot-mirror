import pytest

from event_calendar import pinned_embed as pe


class DummyMsg:
    def __init__(self, mid=1):
        self.id = mid
        self.pinned = False
        self.edits = 0

    async def edit(self, **kwargs):
        self.edits += 1

    async def pin(self, **kwargs):
        self.pinned = True


class DummyChannel:
    def __init__(self):
        self.msg = DummyMsg(10)
        self.sent = []

    async def fetch_message(self, mid):
        if mid != self.msg.id:
            raise RuntimeError("missing")
        return self.msg

    async def send(self, **kwargs):
        m = DummyMsg(11)
        self.sent.append(m)
        return m


class DummyBot:
    def __init__(self):
        self.ch = DummyChannel()

    def get_channel(self, _):
        return self.ch


@pytest.mark.asyncio
async def test_update_calendar_embed_creates_when_missing(monkeypatch):
    monkeypatch.setattr(pe, "_load_tracker", lambda: {})
    monkeypatch.setattr(pe, "_save_tracker", lambda data: None)
    monkeypatch.setattr(pe, "load_runtime_cache", lambda: {"ok": True, "events": [], "payload": {}})
    monkeypatch.setattr(pe, "filter_events", lambda *a, **k: [])
    b = DummyBot()
    out = await pe.update_calendar_embed(b, 123)
    assert out["ok"] is True
    assert out["status"] == "created"
