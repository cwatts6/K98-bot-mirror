from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
import threading

import pytest

from ark.dal import rehydration_dal
from core import startup_diagnostics
import rehydrate_views as views
from services.tracked_view_rehydration_service import (
    EntryOutcome,
    restoration_completion,
    restore_tracked_views,
)
from services.tracked_view_store import EDIT_RECEIPT, TrackedViewStore, fingerprint


@pytest.fixture
def tracker(tmp_path, monkeypatch):
    path = tmp_path / "views.json"
    monkeypatch.setattr(views, "VIEW_TRACKING_FILE", str(path))
    monkeypatch.setattr(views, "_LOCK_PATH", str(path) + ".lock")
    monkeypatch.setattr(views, "REHYDRATE_MIN_DELAY", 0)
    monkeypatch.setattr(views, "REHYDRATE_FETCH_BACKOFF_BASE", 0)
    monkeypatch.setattr(views, "REHYDRATE_FETCH_TIMEOUT", 0.02)
    monkeypatch.setattr(views, "VIEW_TRACKER_LOCK_TIMEOUT", 0.2)
    monkeypatch.setattr(views, "_build_rehydrated_view", lambda key, entry: (object(), key))
    return path


def entry(mid=2):
    return {
        "channel_id": 1,
        "message_id": mid,
        "prefix": "event",
        "events": [{"name": "Event", "type": "ruins", "start_time": datetime.now(UTC).isoformat()}],
    }


class Bot:
    def __init__(self, *, fallback=False, edit_error=None):
        self.fallback = fallback
        self.edit_error = edit_error
        self.added = []
        self.edits = 0
        self.fetches = 0

    async def fetch_channel(self, cid):
        assert cid == 1
        self.fetches += 1
        return self

    async def fetch_message(self, mid):
        return self

    def add_view(self, view, *, message_id):
        if self.fallback:
            raise TypeError("legacy add_view signature")
        self.added.append(message_id)

    async def edit(self, *, view):
        self.edits += 1
        if self.edit_error:
            raise self.edit_error


@pytest.mark.asyncio
async def test_21_views_finish_after_observation_deadline_without_second_pass(tracker):
    tracker.write_text(json.dumps({str(i): entry(i) for i in range(21)}))
    gate = asyncio.Event()
    started = asyncio.Event()

    class SlowBot(Bot):
        async def fetch_channel(self, cid):
            started.set()
            await gate.wait()
            return await super().fetch_channel(cid)

    bot = SlowBot()
    run = asyncio.create_task(
        startup_diagnostics.run(
            views.rehydrate_tracked_views(bot),
            0.001,
            "tracked-test",
            cancel_on_deadline=False,
            completion_check=restoration_completion,
        )
    )
    await started.wait()
    await asyncio.sleep(0.005)
    assert not run.done()
    duplicate = asyncio.create_task(views.rehydrate_tracked_views(bot))
    gate.set()
    result = await run
    assert result == await duplicate
    assert result["restoration_status"] == "complete"
    assert result["attached"] == result["entries_total"] == 21
    assert bot.added == list(range(21))
    assert await views.rehydrate_tracked_views(bot) == result
    assert bot.fetches == 21
    # Fresh process must register again even though the previous run was complete.
    next_bot = Bot()
    assert (await views.rehydrate_tracked_views(next_bot))["attached"] == 21


@pytest.mark.asyncio
async def test_prune_observes_new_uncertain_receipt_without_claiming_superseded(tracker):
    saved = entry()
    current = dict(saved, **{EDIT_RECEIPT: {"state": "prepared"}})
    tracker.write_text(json.dumps({"k": current}))
    store = views._tracker_store()
    assert await store.prune("k", saved) == "outcome_unconfirmed"
    assert json.loads(tracker.read_text())["k"] == current


@pytest.mark.asyncio
async def test_hung_read_exhausts_budget_and_tail_is_attempted(tracker):
    tracker.write_text(json.dumps({"slow": entry(2), "tail": entry(3)}))

    class SlowMessage(Bot):
        async def fetch_message(self, mid):
            if mid == 2:
                await asyncio.Event().wait()
            return self

    bot = SlowMessage()
    result = await views.rehydrate_tracked_views(bot)
    assert result["failed"] == 1 and result["attached"] == 1
    assert result["restoration_status"] == "partial"
    assert bot.added == [3] and bot.fetches == 4
    assert set(json.loads(tracker.read_text())) == {"slow", "tail"}


@pytest.mark.asyncio
async def test_transient_read_is_retried_without_duplicate_attachment(tracker):
    tracker.write_text(json.dumps({"k": entry()}))

    class RetryBot(Bot):
        async def fetch_channel(self, cid):
            await super().fetch_channel(cid)
            if self.fetches == 1:
                raise OSError("temporary")
            return self

    bot = RetryBot()
    assert (await views.rehydrate_tracked_views(bot))["attached"] == 1
    assert bot.fetches == 2 and bot.added == [2]


@pytest.mark.asyncio
@pytest.mark.parametrize("contents", ["", "{", "[]", "null"])
async def test_unavailable_tracker_is_not_empty_and_bytes_are_preserved(tracker, contents):
    tracker.write_text(contents)
    result = await views.rehydrate_tracked_views(Bot())
    assert result["restoration_status"] == "unavailable"
    assert result["entries_total"] is None
    assert tracker.read_text() == contents
    with pytest.raises((ValueError, json.JSONDecodeError)):
        views.save_view_tracker("k", entry())
    assert not Path(str(tracker) + ".lock").exists()
    assert tracker.read_text() == contents


@pytest.mark.asyncio
@pytest.mark.parametrize("exists", [True, False])
async def test_valid_empty_or_absent_tracker_is_complete_noop(tracker, exists):
    if exists:
        tracker.write_text("{}")
    result = await views.rehydrate_tracked_views(Bot())
    assert result["restoration_status"] == "complete"
    assert result["tracker_state"] == "empty" and result["entries_total"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", [False, True])
async def test_changed_identity_before_attach_or_prune_preserves_new_entry(
    tracker, monkeypatch, missing
):
    original = entry()
    replacement = entry(99)
    tracker.write_text(json.dumps({"k": original}))

    class Missing(Exception):
        pass

    monkeypatch.setattr(views.discord, "NotFound", Missing)

    class ChangingBot(Bot):
        async def fetch_message(self, mid):
            views.save_view_tracker("k", replacement)
            if missing:
                raise Missing()
            return self

    bot = ChangingBot()
    result = await views.rehydrate_tracked_views(bot)
    assert result["superseded"] == 1 and not bot.added
    assert json.loads(tracker.read_text())["k"]["message_id"] == 99


@pytest.mark.asyncio
@pytest.mark.parametrize("prune", [True, False])
async def test_forbidden_policy_is_preserved(tracker, monkeypatch, prune):
    tracker.write_text(json.dumps({"k": entry()}))

    class Forbidden(Exception):
        pass

    monkeypatch.setattr(views.discord, "Forbidden", Forbidden)
    monkeypatch.setattr(views, "VIEW_PRUNE_ON_FORBIDDEN", prune)

    class ForbiddenBot(Bot):
        async def fetch_channel(self, cid):
            raise Forbidden()

    result = await views.rehydrate_tracked_views(ForbiddenBot())
    assert result["pruned" if prune else "failed"] == 1
    assert ("k" in json.loads(tracker.read_text())) is not prune


@pytest.mark.asyncio
async def test_invalid_entry_pruned_but_missing_ark_data_retained(tracker, monkeypatch):
    tracker.write_text(json.dumps({"bad": None, "arkmatch_7": entry()}))

    async def missing(_):
        return None, None

    monkeypatch.setattr(views, "get_registration_rehydration_data", missing)
    bot = Bot()
    result = await views.rehydrate_tracked_views(bot)
    assert result["pruned"] == 1 and result["failed"] == 1 and not bot.added
    assert set(json.loads(tracker.read_text())) == {"arkmatch_7"}


@pytest.mark.asyncio
async def test_uncertain_edit_survives_restart_and_same_message_save(tracker):
    saved = entry()
    tracker.write_text(json.dumps({"k": saved}))
    bot = Bot(fallback=True, edit_error=TimeoutError())
    result = await views.rehydrate_tracked_views(bot)
    assert result["outcome_unconfirmed"] == 1 and bot.edits == 1
    receipt = json.loads(tracker.read_text())["k"][EDIT_RECEIPT]
    assert receipt["state"] == "prepared" and receipt["fingerprint"] == fingerprint(saved)
    saved["events"][0]["name"] = "Updated display"
    await views.save_view_tracker_async("k", saved)
    assert json.loads(tracker.read_text())["k"][EDIT_RECEIPT] == receipt
    next_bot = Bot(fallback=True)
    assert (await views.rehydrate_tracked_views(next_bot))["outcome_unconfirmed"] == 1
    assert next_bot.edits == 0
    # Safe local binding is still allowed and does not erase the uncertain receipt.
    assert (await views.rehydrate_tracked_views(Bot()))["attached"] == 1
    assert json.loads(tracker.read_text())["k"][EDIT_RECEIPT] == receipt
    saved["message_id"] = 99
    views.save_view_tracker("k", saved)
    assert EDIT_RECEIPT not in json.loads(tracker.read_text())["k"]


@pytest.mark.asyncio
async def test_successful_fallback_has_receipt_and_no_reconnect_replay(tracker):
    tracker.write_text(json.dumps({"k": entry()}))
    bot = Bot(fallback=True)
    assert (await views.rehydrate_tracked_views(bot))["attached"] == 1
    assert json.loads(tracker.read_text())["k"][EDIT_RECEIPT]["state"] == "acknowledged"
    await views.rehydrate_tracked_views(bot)
    assert bot.edits == 1


@pytest.mark.asyncio
async def test_cancellation_during_edit_retains_intent_and_releases_lock(tracker):
    tracker.write_text(json.dumps({"k": entry(), "tail": entry(3)}))
    started = asyncio.Event()

    class EditingBot(Bot):
        async def edit(self, *, view):
            started.set()
            await asyncio.Event().wait()

    bot = EditingBot(fallback=True)
    task = asyncio.create_task(views.rehydrate_tracked_views(bot))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not Path(str(tracker) + ".lock").exists()
    assert json.loads(tracker.read_text())["k"][EDIT_RECEIPT]["state"] == "prepared"
    other = Bot(fallback=True)
    result = await views.rehydrate_tracked_views(other)
    assert result["outcome_unconfirmed"] == 1 and result["attached"] == 1
    assert other.edits == 1  # only the previously unattempted tail


@pytest.mark.asyncio
async def test_save_worker_is_drained_and_never_reentered(tracker, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def writer(*args):
        calls.append(args)
        entered.set()
        assert release.wait(2)
        raise OSError("failure after entry")

    monkeypatch.setattr(views, "save_view_tracker", writer)
    task = asyncio.create_task(views.save_view_tracker_async("k", entry()))
    await asyncio.to_thread(entered.wait, 1)
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_cancelled_service_accounts_for_active_and_unattempted_entries():
    started = asyncio.Event()
    summary = {}

    async def load():
        return {"first": {}, "second": {}}

    async def restore(*_):
        started.set()
        await asyncio.Event().wait()
        return EntryOutcome("attached")

    task = asyncio.create_task(restore_tracked_views(load, restore, summary=summary))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert summary["restoration_status"] == "cancelled"
    assert summary["unattempted"] == summary["outcome_unconfirmed"] == 1


def test_ark_read_sets_timeout_parameterizes_and_closes_on_error(monkeypatch):
    calls = []

    class Connection:
        timeout = None

        def cursor(self):
            return self

        def execute(self, sql, *params):
            calls.append((sql, params))
            if params:
                raise OSError("query failed")

        def close(self):
            calls.append("closed")

    conn = Connection()
    monkeypatch.setattr(rehydration_dal, "get_conn_with_retries", lambda **kw: conn)
    monkeypatch.setattr(rehydration_dal, "fetch_one_dict", lambda cursor: {"ConfigId": 1})
    with pytest.raises(OSError):
        rehydration_dal._load_registration(7)
    assert conn.timeout == 5
    assert calls[1][1] == ((7,),)
    assert calls[-2:] == ["closed", "closed"]


@pytest.mark.asyncio
async def test_prune_failure_preserves_entry_and_releases_lock(tracker, monkeypatch):
    saved = entry()
    tracker.write_text(json.dumps({"k": saved}))
    store = TrackedViewStore(tracker, str(tracker) + ".lock")

    async def fail(data):
        raise OSError("atomic writer refused")

    monkeypatch.setattr(store, "write", fail)
    with pytest.raises(OSError):
        await store.prune("k", saved)
    assert json.loads(tracker.read_text())["k"] == saved
    assert not Path(str(tracker) + ".lock").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("fail_at", [1, 2])
async def test_edit_receipt_write_failure_never_repeats_edit(tracker, monkeypatch, fail_at):
    tracker.write_text(json.dumps({"k": entry()}))
    original = TrackedViewStore.write
    writes = 0

    async def writer(self, data):
        nonlocal writes
        writes += 1
        if writes == fail_at:
            raise OSError("persist failure")
        return await original(self, data)

    monkeypatch.setattr(TrackedViewStore, "write", writer)
    bot = Bot(fallback=True)
    result = await views.rehydrate_tracked_views(bot)
    assert bot.edits == fail_at - 1
    assert result["failed" if fail_at == 1 else "outcome_unconfirmed"] == 1
    assert not Path(str(tracker) + ".lock").exists()
    if fail_at == 2:
        next_bot = Bot(fallback=True)
        assert (await views.rehydrate_tracked_views(next_bot))["outcome_unconfirmed"] == 1
        assert next_bot.edits == 0


@pytest.mark.asyncio
async def test_no_prune_of_malformed_entry_with_uncertain_edit(tracker):
    saved = {"channel_id": 1, "message_id": 2, EDIT_RECEIPT: {"state": "prepared"}}
    tracker.write_text(json.dumps({"k": saved}))
    result = await views.rehydrate_tracked_views(Bot())
    assert result["outcome_unconfirmed"] == 1 and result["pruned"] == 0
    assert json.loads(tracker.read_text())["k"] == saved


@pytest.mark.asyncio
async def test_permission_error_is_unavailable_not_empty(tracker, monkeypatch):
    def denied(self):
        raise PermissionError("denied")

    monkeypatch.setattr(TrackedViewStore, "read", denied)
    result = await views.rehydrate_tracked_views(Bot())
    assert result["tracker_error"] == "PermissionError"
    assert result["entries_total"] is None


@pytest.mark.asyncio
async def test_cancelled_lock_acquisition_releases_late_acquired_lock(tracker):
    from file_utils import acquire_lock

    lock_path = str(tracker) + ".lock"
    blocker = acquire_lock(lock_path)
    blocker.__enter__()
    store = TrackedViewStore(tracker, lock_path, timeout=0.3, poll=0.005)

    async def waiting():
        async with store.locked():
            pytest.fail("cancelled owner must not enter protected body")

    task = asyncio.create_task(waiting())
    await asyncio.sleep(0.01)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    blocker.__exit__(None, None, None)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not Path(lock_path).exists()


@pytest.mark.asyncio
async def test_ark_factory_retains_persistent_custom_ids_and_real_callbacks(monkeypatch):
    from datetime import date, time

    from ark.registration_flow import ArkRegistrationController

    async def load(match_id):
        assert match_id == 7
        return {"PlayersCap": 30}, {
            "ArkWeekendDate": date(2026, 10, 24),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(12),
            "Alliance": "Test",
        }

    monkeypatch.setattr(views, "get_registration_rehydration_data", load)
    view = await views._build_ark_registration_view(7)
    assert view.timeout is None
    assert view.events[0]["name"] == "Ark Match — Test"
    assert view.join_player_btn.custom_id.endswith("_join_player")
    assert view.admin_add_btn.custom_id.endswith("_admin_add")
    for name in (
        "join_player",
        "join_sub",
        "leave",
        "switch",
        "admin_add",
        "admin_remove",
        "admin_move",
    ):
        callback = getattr(view, "on_" + name)
        assert isinstance(callback.__self__, ArkRegistrationController)
        assert callback.__self__.match_id == 7


@pytest.mark.asyncio
async def test_partial_feature_outcome_is_visible_in_startup_report():
    async def partial():
        return {"restoration_status": "partial", "failed": 1, "attached": 2}

    await startup_diagnostics.run(
        partial(), 1, "partial-tracked", completion_check=restoration_completion
    )
    record = next(row for row in startup_diagnostics.report() if row["step"] == "partial-tracked")
    assert record["state"] == "completed"
    assert record["completion"]["restoration_status"] == "partial"
