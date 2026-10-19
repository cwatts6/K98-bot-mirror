import time

import utils as U
from utils import live_queue, load_live_queue, save_live_queue


def test_save_and_load_live_queue(tmp_path, monkeypatch):
    # redirect QUEUE_CACHE_FILE to temp (utils module constant)
    temp = tmp_path / "live_queue_cache.json"
    U.QUEUE_CACHE_FILE = str(temp)

    # populate live_queue
    live_queue["jobs"] = [
        {"filename": "a", "user": "u", "status": "🕐 uploading", "uploaded": "2025-01-01T00:00:00"}
    ]
    live_queue["message_meta"] = {"channel_id": 1, "message_id": 2, "message_created": None}

    save_live_queue()

    # Clear in-memory job then load
    live_queue["jobs"] = []
    live_queue["message_meta"] = None

    load_live_queue()

    # allow small time for run_coroutine_threadsafe if used
    time.sleep(0.05)

    # After load the job list should be restored
    assert live_queue["jobs"], "Jobs should be restored from disk"
