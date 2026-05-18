# Updated test file to monkeypatch discord.NotFound to a simple Exception subclass so we can
# simulate a NotFound without invoking discord.py's HTTPException constructor.
from datetime import timedelta
import json
import os

import discord  # used only as module namespace to be monkeypatched in the test
import pytest

# Import the module under test and allow test to override module-level file paths.
import rehydrate_views

# Ensure we can operate in the test environment even if discord package is missing.
# The code under test tolerates missing discord and falls back to pruning on fetch errors.
# We'll create lightweight fakes for Bot/Channel/Message as needed.
import utils


@pytest.fixture(autouse=True)
def isolate_view_tracking_file(tmp_path, monkeypatch):
    """
    Ensure each test uses its own VIEW_TRACKING_FILE and associated lock path.
    Monkeypatch the module-global variables so functions use the test file.
    """
    tracker_path = tmp_path / "view_tracker_test.json"
    monkeypatch.setattr(rehydrate_views, "VIEW_TRACKING_FILE", str(tracker_path))
    # if module defines a derived lock path, update it too
    if hasattr(rehydrate_views, "_LOCK_PATH"):
        monkeypatch.setattr(rehydrate_views, "_LOCK_PATH", f"{tracker_path!s}.lock")
    # ensure file does not exist at test start
    try:
        os.remove(str(tracker_path))
    except Exception:
        pass
    yield
    # cleanup
    try:
        os.remove(str(tracker_path))
    except Exception:
        pass
    try:
        os.remove(f"{tracker_path!s}.lock")
    except Exception:
        pass


def make_event(name="Test Event", typ="ruins", offset_minutes=60):
    """
    Helper to create a simple event dict with timezone-aware start_time (UTC).
    """
    start = utils.utcnow() + timedelta(minutes=offset_minutes)
    return {"name": name, "type": typ, "start_time": start, "description": "desc"}


def read_tracker_file():
    path = rehydrate_views.VIEW_TRACKING_FILE
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_serialize_and_save_and_load_roundtrip():
    """
    - Verify serialize_event converts datetimes to ISO strings with timezone info.
    - Verify save_view_tracker writes an entry that load_view_tracker (via load helper) can read back.
    """
    key = "nextevent_test_roundtrip"
    ev = make_event(offset_minutes=30)
    # serialize / ensure format
    ser = rehydrate_views.serialize_event(ev)
    assert isinstance(ser, dict)
    # start_time should be an ISO string (tz-aware -> include +00:00 or Z)
    assert isinstance(ser.get("start_time"), str)
    assert "+" in ser["start_time"] or ser["start_time"].endswith("Z")

    # Build entry as the persisted shape would be
    entry = {
        "channel_id": 111222,
        "message_id": 333444,
        "events": [ser],
        "created_at": utils.utcnow().isoformat(),
    }
    # Save to disk
    await rehydrate_views.save_view_tracker_async(key, entry)

    # Read raw file and assert content present
    raw = read_tracker_file()
    assert key in raw
    loaded = raw[key]
    assert loaded["channel_id"] == entry["channel_id"]
    assert loaded["message_id"] == entry["message_id"]
    assert isinstance(loaded["events"], list)
    assert loaded["events"][0]["start_time"] == ser["start_time"]


@pytest.mark.asyncio
async def test_rehydrate_tracked_views_attaches_view_to_bot():
    """
    Create a tracker entry on disk, simulate a bot that can fetch a channel & message,
    and assert rehydrate_tracked_views registers a LocalTimeToggleView and attaches it
    for the correct message_id (via bot.add_view(..., message_id=...)).
    """

    # Prepare persisted tracker entry
    key = "rehyd_test_attach"
    event = make_event(offset_minutes=45)
    ser = rehydrate_views.serialize_event(event)
    entry = {
        "channel_id": 12345,
        "message_id": 98765,
        "events": [ser],
        "created_at": utils.utcnow().isoformat(),
    }
    rehydrate_views.save_view_tracker(key, entry)

    # Create fake message/channel/bot
    attached_views = []

    class FakeMessage:
        def __init__(self, mid):
            self.id = mid

        async def edit(self, view=None):
            # emulate message.edit attaching the view (fallback path)
            attached_views.append(("edited", view, self.id))
            return self

    class FakeChannel:
        def __init__(self, cid, message):
            self.id = cid
            self._msg = message

        async def fetch_message(self, message_id):
            if int(message_id) != self._msg.id:
                raise Exception("message not found")
            return self._msg

    class FakeBot:
        def __init__(self, channel):
            self._channel = channel
            self.added = []

        async def fetch_channel(self, channel_id):
            # verify requested id matches
            if int(channel_id) != self._channel.id:
                raise Exception("channel not found")
            return self._channel

        # Emulate modern discord.py add_view(signature) which accepts message_id
        def add_view(self, view, message_id=None):
            # Record the view object type & message_id for assertions
            self.added.append({"view": view, "message_id": message_id})

    fake_msg = FakeMessage(entry["message_id"])
    fake_chan = FakeChannel(entry["channel_id"], fake_msg)
    bot = FakeBot(fake_chan)

    # Run rehydration
    summary = await rehydrate_views.rehydrate_tracked_views(bot)

    # Verify summary and that bot.add_view was called attaching the message id
    assert isinstance(summary, dict)
    assert summary.get("rehydrated", 0) == 1
    assert len(bot.added) == 1
    assert bot.added[0]["message_id"] == entry["message_id"]
    # ensure the attached view holds the events we persisted
    attached_view = bot.added[0]["view"]
    assert hasattr(attached_view, "events")
    assert len(attached_view.events) == 1
    assert attached_view.events[0]["name"] == event["name"]


@pytest.mark.asyncio
async def test_rehydrate_prunes_missing_channel_or_message(monkeypatch):
    """
    When the bot cannot fetch the channel/message (simulated by raising a NotFound),
    rehydrate_tracked_views should prune the stale tracker entry from disk.

    discord.NotFound from discord.py inherits from HTTPException and its constructor
    expects internal args; to avoid constructing the real discord.NotFound we monkeypatch
    discord.NotFound to a simple Exception subclass for the duration of this test so we
    can simulate the exact type-check the module performs.
    """
    key = "rehyd_test_prune"
    event = make_event(offset_minutes=10)
    ser = rehydrate_views.serialize_event(event)
    entry = {
        "channel_id": 111222,
        "message_id": 333444,
        "events": [ser],
        "created_at": utils.utcnow().isoformat(),
    }
    # Save to disk (async wrapper)
    await rehydrate_views.save_view_tracker_async(key, entry)

    # Create a minimal dummy NotFound class and patch discord.NotFound to it
    class DummyNotFound(Exception):
        pass

    monkeypatch.setattr(discord, "NotFound", DummyNotFound, raising=False)

    # Fake bot that raises DummyNotFound when fetching channel
    class BadBot:
        async def fetch_channel(self, channel_id):
            raise DummyNotFound("simulated fetch failure")

    bad = BadBot()
    summary = await rehydrate_views.rehydrate_tracked_views(bad)

    # The rehydrate logic should have pruned the broken entry
    raw = read_tracker_file()
    assert key not in raw
    # summary should reflect pruning
    assert summary.get("pruned", 0) >= 1


@pytest.mark.asyncio
async def test_save_view_tracker_uses_lock_and_atomic_write(tmp_path, monkeypatch):
    """
    Smoke test that save_view_tracker can be called repeatedly without raising and
    that the file is valid JSON after multiple updates.
    (This indirectly exercises the locking + atomic_write behaviour.)
    """
    # Use the module-level file path (already redirected by fixture)
    key_base = "concurrent_key"
    event = make_event(offset_minutes=5)
    ser = rehydrate_views.serialize_event(event)

    # call save_view_tracker multiple times
    for i in range(5):
        key = f"{key_base}_{i}"
        entry = {"channel_id": i, "message_id": i * 10, "events": [ser]}
        # Should not raise
        rehydrate_views.save_view_tracker(key, entry)

    # File should parse as JSON and contain all keys
    raw = read_tracker_file()
    for i in range(5):
        assert f"{key_base}_{i}" in raw


@pytest.mark.asyncio
async def test_rehydrate_nextfight_uses_specialized_view():
    key = "nextfight"
    event = make_event(offset_minutes=20)
    ser = rehydrate_views.serialize_event(event)
    entry = {
        "channel_id": 4242,
        "message_id": 5252,
        "events": [ser],
        "prefix": "nextfight",
        "initial_limit": 1,
        "created_at": utils.utcnow().isoformat(),
    }
    rehydrate_views.save_view_tracker(key, entry)

    class FakeMessage:
        def __init__(self, mid):
            self.id = mid

    class FakeChannel:
        def __init__(self, cid, message):
            self.id = cid
            self._msg = message

        async def fetch_message(self, message_id):
            assert int(message_id) == self._msg.id
            return self._msg

    class FakeBot:
        def __init__(self, channel):
            self._channel = channel
            self.added = []

        async def fetch_channel(self, channel_id):
            assert int(channel_id) == self._channel.id
            return self._channel

        def add_view(self, view, message_id=None):
            self.added.append({"view": view, "message_id": message_id})

    bot = FakeBot(FakeChannel(entry["channel_id"], FakeMessage(entry["message_id"])))
    summary = await rehydrate_views.rehydrate_tracked_views(bot)

    assert summary.get("rehydrated", 0) == 1
    assert len(bot.added) == 1
    attached_view = bot.added[0]["view"]
    assert attached_view.__class__.__name__ == "NextFightView"
    custom_ids = [
        getattr(child, "custom_id", None)
        for child in getattr(attached_view, "children", [])
        if getattr(child, "custom_id", None)
    ]
    assert any(
        cid.startswith("nextfight") and cid.endswith("_local_time_toggle") for cid in custom_ids
    )


@pytest.mark.asyncio
async def test_rehydrate_nextevent_uses_specialized_view_and_limit():
    key = "nextevent"
    event1 = make_event(name="Event 1", offset_minutes=20)
    event2 = make_event(name="Event 2", offset_minutes=40)
    event3 = make_event(name="Event 3", offset_minutes=60)
    entry = {
        "channel_id": 6262,
        "message_id": 7272,
        "events": [
            rehydrate_views.serialize_event(event1),
            rehydrate_views.serialize_event(event2),
            rehydrate_views.serialize_event(event3),
        ],
        "prefix": "nextevent",
        "initial_limit": 3,
        "created_at": utils.utcnow().isoformat(),
    }
    rehydrate_views.save_view_tracker(key, entry)

    class FakeMessage:
        def __init__(self, mid):
            self.id = mid

    class FakeChannel:
        def __init__(self, cid, message):
            self.id = cid
            self._msg = message

        async def fetch_message(self, message_id):
            assert int(message_id) == self._msg.id
            return self._msg

    class FakeBot:
        def __init__(self, channel):
            self._channel = channel
            self.added = []

        async def fetch_channel(self, channel_id):
            assert int(channel_id) == self._channel.id
            return self._channel

        def add_view(self, view, message_id=None):
            self.added.append({"view": view, "message_id": message_id})

    bot = FakeBot(FakeChannel(entry["channel_id"], FakeMessage(entry["message_id"])))
    summary = await rehydrate_views.rehydrate_tracked_views(bot)

    assert summary.get("rehydrated", 0) == 1
    assert len(bot.added) == 1
    attached_view = bot.added[0]["view"]
    assert attached_view.__class__.__name__ == "NextEventView"
    assert getattr(attached_view, "limit", None) == 3
    custom_ids = [
        getattr(child, "custom_id", None)
        for child in getattr(attached_view, "children", [])
        if getattr(child, "custom_id", None)
    ]
    assert any(
        cid.startswith("nextevent") and cid.endswith("_local_time_toggle") for cid in custom_ids
    )
