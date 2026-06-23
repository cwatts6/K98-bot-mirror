from __future__ import annotations

import copy
from pathlib import Path
import threading

import pytest

from player_self_service import reminder_service
import subscription_tracker


@pytest.mark.asyncio
async def test_build_reminder_centre_state_for_unsubscribed_player() -> None:
    state = await reminder_service.build_reminder_centre_state(
        42,
        config_loader=lambda _uid: None,
    )

    assert state.ok is True
    assert state.subscribed is False
    assert state.event_summary == "not subscribed"
    assert state.can_unsubscribe is False


@pytest.mark.asyncio
async def test_build_reminder_centre_state_reports_invalid_shape() -> None:
    state = await reminder_service.build_reminder_centre_state(
        42,
        config_loader=lambda _uid: {"subscriptions": "all", "reminder_times": []},
    )

    assert state.ok is False
    assert state.error == "invalid reminder config shape"


@pytest.mark.asyncio
async def test_build_reminder_centre_state_uses_event_loop_thread() -> None:
    loop_thread = threading.get_ident()
    loader_threads = []

    def config_loader(_uid):
        loader_threads.append(threading.get_ident())
        return None

    state = await reminder_service.build_reminder_centre_state(
        42,
        config_loader=config_loader,
    )

    assert state.ok is True
    assert loader_threads == [loop_thread]


def test_normalize_event_types_prevents_duplicate_reminders() -> None:
    all_types, all_adjusted = reminder_service.normalize_event_types(("ruins", "all", "major"))
    fight_types, fight_adjusted = reminder_service.normalize_event_types(
        ("ruins", "altars", "major", "fights")
    )

    assert all_types == ("all",)
    assert all_adjusted is True
    assert fight_types == ("fights",)
    assert fight_adjusted is True


def test_subscription_tracker_save_failure_propagates(monkeypatch, tmp_path) -> None:
    subscription_path = tmp_path / "subscription_tracker.json"
    monkeypatch.setattr(subscription_tracker, "SUBSCRIPTION_FILE", str(subscription_path))
    monkeypatch.setattr(subscription_tracker, "subscriptions", {}, raising=False)

    def fail_replace(_src, _dst):
        raise OSError("disk full")

    monkeypatch.setattr(subscription_tracker.os, "replace", fail_replace)

    with pytest.raises(OSError):
        subscription_tracker.set_user_config(42, "Tester", ["ruins"], ["24h"])

    assert subscription_tracker.subscriptions == {}


def test_subscription_tracker_update_failure_restores_existing_config(
    monkeypatch,
    tmp_path,
) -> None:
    subscription_path = tmp_path / "subscription_tracker.json"
    original = {
        "42": {
            "username": "Tester",
            "subscriptions": ["ruins"],
            "reminder_times": ["24h"],
        }
    }
    monkeypatch.setattr(subscription_tracker, "SUBSCRIPTION_FILE", str(subscription_path))
    monkeypatch.setattr(
        subscription_tracker,
        "subscriptions",
        copy.deepcopy(original),
        raising=False,
    )

    def fail_replace(_src, _dst):
        raise OSError("disk full")

    monkeypatch.setattr(subscription_tracker.os, "replace", fail_replace)

    with pytest.raises(OSError):
        subscription_tracker.update_user_event_types(42, ["all"])
    assert subscription_tracker.subscriptions == original

    with pytest.raises(OSError):
        subscription_tracker.update_user_reminder_times(42, ["1h"])
    assert subscription_tracker.subscriptions == original


def test_subscription_tracker_remove_failure_restores_existing_config(
    monkeypatch,
    tmp_path,
) -> None:
    subscription_path = tmp_path / "subscription_tracker.json"
    original = {
        "42": {
            "username": "Tester",
            "subscriptions": ["ruins"],
            "reminder_times": ["24h"],
        }
    }
    monkeypatch.setattr(subscription_tracker, "SUBSCRIPTION_FILE", str(subscription_path))
    monkeypatch.setattr(
        subscription_tracker,
        "subscriptions",
        copy.deepcopy(original),
        raising=False,
    )

    def fail_replace(_src, _dst):
        raise OSError("disk full")

    monkeypatch.setattr(subscription_tracker.os, "replace", fail_replace)

    with pytest.raises(OSError):
        subscription_tracker.remove_user(42)

    assert subscription_tracker.subscriptions == original


@pytest.mark.asyncio
async def test_save_reminder_preferences_subscribes_with_existing_writer_path() -> None:
    calls = []

    def writer(*args):
        calls.append(args)

    result = await reminder_service.save_reminder_preferences(
        42,
        "Tester",
        ("ruins", "altars"),
        ("24h", "1h"),
        config_loader=lambda _uid: None,
        writer=writer,
    )

    assert result.ok is True
    assert result.action == "subscribe"
    assert result.event_types == ("ruins", "altars")
    assert result.reminder_times == ("24h", "1h")
    assert calls == [(42, "Tester", ["ruins", "altars"], ["24h", "1h"])]
    assert result.dm_message is not None


@pytest.mark.asyncio
async def test_save_reminder_preferences_keeps_tracker_access_on_event_loop_thread() -> None:
    loop_thread = threading.get_ident()
    call_threads = []

    def config_loader(_uid):
        call_threads.append(("loader", threading.get_ident()))
        return None

    def writer(*_args):
        call_threads.append(("writer", threading.get_ident()))

    result = await reminder_service.save_reminder_preferences(
        42,
        "Tester",
        ("ruins",),
        ("24h",),
        config_loader=config_loader,
        writer=writer,
    )

    assert result.ok is True
    assert call_threads == [
        ("loader", loop_thread),
        ("writer", loop_thread),
    ]


@pytest.mark.asyncio
async def test_save_reminder_preferences_updates_and_defaults_empty_times() -> None:
    calls = []

    def writer(*args):
        calls.append(args)

    result = await reminder_service.save_reminder_preferences(
        42,
        "Tester",
        ("all", "major"),
        (),
        config_loader=lambda _uid: {"subscriptions": ["ruins"], "reminder_times": ["24h"]},
        writer=writer,
    )

    assert result.ok is True
    assert result.action == "update"
    assert result.event_types == ("all",)
    assert result.adjusted is True
    assert result.reminder_times == tuple(reminder_service.DEFAULT_REMINDER_TIMES)
    assert calls == [(42, "Tester", ["all"], list(reminder_service.DEFAULT_REMINDER_TIMES))]


@pytest.mark.asyncio
async def test_save_reminder_preferences_rejects_missing_event_types() -> None:
    calls = []

    result = await reminder_service.save_reminder_preferences(
        42,
        "Tester",
        (),
        ("24h",),
        config_loader=lambda _uid: None,
        writer=lambda *args: calls.append(args),
    )

    assert result.ok is False
    assert "event type" in result.message
    assert calls == []


@pytest.mark.asyncio
async def test_save_reminder_preferences_reports_writer_failure() -> None:
    def writer(*_args):
        raise OSError("disk full")

    result = await reminder_service.save_reminder_preferences(
        42,
        "Tester",
        ("ruins",),
        ("24h",),
        config_loader=lambda _uid: None,
        writer=writer,
    )

    assert result.ok is False
    assert "Failed to save" in result.message


@pytest.mark.asyncio
async def test_prepare_unsubscribe_confirmation_requires_subscription() -> None:
    confirmation, error = await reminder_service.prepare_unsubscribe_confirmation(
        42,
        config_loader=lambda _uid: None,
    )

    assert confirmation is None
    assert "not currently subscribed" in error


@pytest.mark.asyncio
async def test_confirm_unsubscribe_revalidates_stale_confirmation() -> None:
    confirmation = reminder_service.ReminderUnsubscribeConfirmation(
        event_types=("ruins",),
        reminder_times=("24h",),
    )

    result = await reminder_service.confirm_unsubscribe(
        42,
        confirmation,
        config_loader=lambda _uid: {"subscriptions": ["all"], "reminder_times": ["24h"]},
    )

    assert result.ok is False
    assert "stale" in result.message


@pytest.mark.asyncio
async def test_confirm_unsubscribe_cleans_trackers_before_removing_config() -> None:
    calls = []
    confirmation = reminder_service.ReminderUnsubscribeConfirmation(
        event_types=("ruins",),
        reminder_times=("24h", "1h"),
    )

    async def task_canceller(uid):
        calls.append(("cancel", uid))
        return 2

    result = await reminder_service.confirm_unsubscribe(
        42,
        confirmation,
        config_loader=lambda _uid: {"subscriptions": ["ruins"], "reminder_times": ["24h", "1h"]},
        remover=lambda uid: calls.append(("remove", uid)) or True,
        task_canceller=task_canceller,
        scheduled_purger=lambda uid: calls.append(("scheduled", uid)) or 3,
        sent_purger=lambda uid: calls.append(("sent", uid)) or 4,
    )

    assert result.ok is True
    assert result.action == "unsubscribe"
    assert calls == [
        ("cancel", 42),
        ("scheduled", 42),
        ("sent", 42),
        ("remove", 42),
    ]
    assert result.dm_message is not None


@pytest.mark.asyncio
async def test_confirm_unsubscribe_keeps_tracker_access_on_event_loop_thread() -> None:
    loop_thread = threading.get_ident()
    calls = []
    confirmation = reminder_service.ReminderUnsubscribeConfirmation(
        event_types=("ruins",),
        reminder_times=("24h",),
    )

    def config_loader(_uid):
        calls.append(("loader", threading.get_ident()))
        return {"subscriptions": ["ruins"], "reminder_times": ["24h"]}

    async def task_canceller(_uid):
        calls.append(("cancel", threading.get_ident()))
        return 1

    result = await reminder_service.confirm_unsubscribe(
        42,
        confirmation,
        config_loader=config_loader,
        remover=lambda _uid: calls.append(("remove", threading.get_ident())) or True,
        task_canceller=task_canceller,
        scheduled_purger=lambda _uid: calls.append(("scheduled", threading.get_ident())) or 2,
        sent_purger=lambda _uid: calls.append(("sent", threading.get_ident())) or 3,
    )

    assert result.ok is True
    assert calls == [
        ("loader", loop_thread),
        ("cancel", loop_thread),
        ("scheduled", loop_thread),
        ("sent", loop_thread),
        ("remove", loop_thread),
    ]


@pytest.mark.asyncio
async def test_confirm_unsubscribe_reports_tracker_failure() -> None:
    confirmation = reminder_service.ReminderUnsubscribeConfirmation(
        event_types=("ruins",),
        reminder_times=("24h",),
    )

    async def task_canceller(_uid):
        return 0

    def scheduled_purger(_uid):
        raise OSError("tracker locked")

    result = await reminder_service.confirm_unsubscribe(
        42,
        confirmation,
        config_loader=lambda _uid: {"subscriptions": ["ruins"], "reminder_times": ["24h"]},
        remover=lambda _uid: True,
        task_canceller=task_canceller,
        scheduled_purger=scheduled_purger,
        sent_purger=lambda _uid: 0,
    )

    assert result.ok is False
    assert "Failed to unsubscribe" in result.message


def test_reminder_service_has_no_ui_framework_dependency() -> None:
    source = Path("player_self_service/reminder_service.py").read_text(encoding="utf-8")
    framework_name = "dis" + "cord"

    assert f"import {framework_name}" not in source
    assert f"{framework_name}." not in source
