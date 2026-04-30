# tests/test_save_view_tracker_async.py
"""
Test that save_view_tracker_async delegates to the synchronous save_view_tracker via asyncio.to_thread.
We monkeypatch the synchronous function to a lightweight sync stub and assert it was invoked.
"""

import asyncio

import rehydrate_views


def test_save_view_tracker_async_calls_sync(monkeypatch):
    called = {}

    def fake_save(key, entry):
        # mimic synchronous function being called in thread
        called["key"] = key
        called["entry"] = entry

    monkeypatch.setattr(rehydrate_views, "save_view_tracker", fake_save)

    # Run the async wrapper via asyncio.run to exercise the to_thread delegation
    asyncio.run(rehydrate_views.save_view_tracker_async("testkey", {"events": [1, 2, 3]}))

    assert called.get("key") == "testkey"
    assert isinstance(called.get("entry"), dict)
    assert called["entry"]["events"] == [1, 2, 3]
