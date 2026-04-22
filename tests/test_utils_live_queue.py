import asyncio

import pytest

import utils

pytestmark = pytest.mark.asyncio


async def test_save_and_load_structure(tmp_path, monkeypatch):
    """
    Unit test: verify save_live_queue writes the expected shape and load_live_queue
    repopulates live_queue['jobs'] and live_queue['message_meta'].
    """
    temp_file = tmp_path / "queue_cache.json"
    monkeypatch.setattr(utils, "QUEUE_CACHE_FILE", str(temp_file))

    # Prepare live_queue with jobs and a fake message_meta
    async with utils.live_queue_lock:
        utils.live_queue["jobs"] = [{"filename": "a.txt", "status": "ok"}]
        utils.live_queue["message"] = None
        utils.live_queue["message_meta"] = {
            "channel_id": 111,
            "message_id": 222,
            "message_created": None,
        }

    # Save to disk
    utils.save_live_queue()
    assert temp_file.exists()

    # Clear in-memory and call load_live_queue
    async with utils.live_queue_lock:
        utils.live_queue["jobs"] = []
        utils.live_queue["message"] = None
        utils.live_queue["message_meta"] = None

    # Call load_live_queue (it schedules the apply into the running loop)
    utils.load_live_queue()
    # allow scheduled apply() to run
    await asyncio.sleep(0.1)

    # Validate
    async with utils.live_queue_lock:
        assert utils.live_queue["jobs"] == [{"filename": "a.txt", "status": "ok"}]
        assert utils.live_queue["message_meta"] == {
            "channel_id": 111,
            "message_id": 222,
            "message_created": None,
        }


async def test_update_live_queue_embed_rehydrate(monkeypatch):
    """
    Integration-style test that simulates rehydration:
    - live_queue has message_meta but message is None.
    - bot.get_channel returns a fake channel whose fetch_message returns a fake message.
    - After calling update_live_queue_embed, live_queue['message'] should be set to the fake message.
    """

    class FakeMessage:
        def __init__(self, mid, created_at=None):
            self.id = mid
            self.created_at = created_at

        async def edit(self, *, embed=None):
            # simulate edit success
            self._edited = True
            return self

    class FakeChannel:
        def __init__(self, cid, fake_message):
            self.id = cid
            self._fake_message = fake_message

        async def fetch_message(self, mid):
            if mid == self._fake_message.id:
                return self._fake_message
            raise Exception("NotFound")

        async def send(self, embed=None):
            # simulate send returning a message
            return self._fake_message

    class FakeBot:
        def __init__(self, channel):
            self._channel = channel

        def get_channel(self, cid):
            # return cached object only if same id
            if cid == self._channel.id:
                return self._channel
            return None

        async def fetch_channel(self, cid):
            if cid == self._channel.id:
                return self._channel
            raise Exception("NotFound")

    fake_msg = FakeMessage(mid=999)
    fake_chan = FakeChannel(cid=123, fake_message=fake_msg)
    fake_bot = FakeBot(channel=fake_chan)

    # Prepare live_queue state
    async with utils.live_queue_lock:
        utils.live_queue["jobs"] = []
        utils.live_queue["message"] = None
        utils.live_queue["message_meta"] = {
            "channel_id": 123,
            "message_id": 999,
            "message_created": None,
        }

    # Call update_live_queue_embed (this will try to rehydrate)
    await utils.update_live_queue_embed(fake_bot, notify_channel_id=123)

    # Validate that message was rehydrated
    async with utils.live_queue_lock:
        assert utils.live_queue["message"] is fake_msg
        assert utils.live_queue["message_meta"]["channel_id"] == 123
        assert utils.live_queue["message_meta"]["message_id"] == 999
