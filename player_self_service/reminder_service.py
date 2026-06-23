"""Reminder-centre service logic for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any, Literal

from constants import DEFAULT_REMINDER_TIMES, VALID_TYPES
from dm_tracker_utils import (
    purge_user_from_dm_scheduled_tracker,
    purge_user_from_dm_sent_tracker,
)
from reminder_task_registry import cancel_and_wait_user_tasks
from subscription_tracker import get_user_config, remove_user, set_user_config

logger = logging.getLogger(__name__)

ReminderAction = Literal["subscribe", "update", "unsubscribe"]

ConfigLoader = Callable[[int | str], dict[str, Any] | None]
ConfigWriter = Callable[[int | str, str, list[str], list[str]], None]
ConfigRemover = Callable[[int | str], bool]
TaskCanceller = Callable[[int | str], Awaitable[int]]
TrackerPurger = Callable[[int | str], int]


async def _cancel_user_tasks_for_unsubscribe(user_id: int | str) -> int:
    return await cancel_and_wait_user_tasks(user_id, timeout=2.0)


@dataclass(frozen=True, slots=True)
class ReminderCentreState:
    ok: bool
    subscribed: bool
    event_types: tuple[str, ...]
    reminder_times: tuple[str, ...]
    event_summary: str
    time_summary: str
    error: str | None = None

    @property
    def can_manage(self) -> bool:
        return self.ok

    @property
    def can_unsubscribe(self) -> bool:
        return self.ok and self.subscribed


@dataclass(frozen=True, slots=True)
class ReminderMessage:
    title: str
    description: str
    color: int
    fields: tuple[tuple[str, str], ...]
    footer: str


@dataclass(frozen=True, slots=True)
class ReminderMutationResult:
    ok: bool
    action: ReminderAction
    message: str
    event_types: tuple[str, ...] = ()
    reminder_times: tuple[str, ...] = ()
    adjusted: bool = False
    dm_message: ReminderMessage | None = None


@dataclass(frozen=True, slots=True)
class ReminderUnsubscribeConfirmation:
    event_types: tuple[str, ...]
    reminder_times: tuple[str, ...]

    @property
    def body(self) -> str:
        return (
            "Unsubscribe from all KVK event reminders?\n"
            f"Current events: {_format_list(self.event_types)}\n"
            f"Current times: {_format_list(self.reminder_times)}"
        )


def _ordered_valid(values: list[Any] | tuple[Any, ...], valid: tuple[str, ...]) -> tuple[str, ...]:
    selected = {str(value).strip().lower() for value in values if str(value).strip()}
    return tuple(item for item in valid if item in selected)


def normalize_event_types(values: list[Any] | tuple[Any, ...]) -> tuple[tuple[str, ...], bool]:
    ordered = _ordered_valid(values, tuple(VALID_TYPES))
    adjusted = False
    if "all" in ordered:
        adjusted = ordered != ("all",)
        return ("all",), adjusted
    if "fights" in ordered:
        filtered = tuple(value for value in ordered if value not in {"altars", "major"})
        adjusted = filtered != ordered
        ordered = filtered
    return ordered, adjusted


def normalize_reminder_times(values: list[Any] | tuple[Any, ...]) -> tuple[str, ...]:
    ordered = _ordered_valid(values, tuple(DEFAULT_REMINDER_TIMES))
    if ordered:
        return ordered
    return tuple(DEFAULT_REMINDER_TIMES)


def _state_from_config(config: dict[str, Any] | None) -> ReminderCentreState:
    if config is None:
        return ReminderCentreState(
            ok=True,
            subscribed=False,
            event_types=(),
            reminder_times=(),
            event_summary="not subscribed",
            time_summary="not set",
        )
    if not isinstance(config, dict):
        return ReminderCentreState(
            ok=False,
            subscribed=False,
            event_types=(),
            reminder_times=(),
            event_summary="unknown",
            time_summary="unknown",
            error="invalid reminder config",
        )

    raw_types = config.get("subscriptions") or []
    raw_times = config.get("reminder_times") or []
    if not isinstance(raw_types, list) or not isinstance(raw_times, list):
        return ReminderCentreState(
            ok=False,
            subscribed=False,
            event_types=(),
            reminder_times=(),
            event_summary="unknown",
            time_summary="unknown",
            error="invalid reminder config shape",
        )

    event_types, _adjusted = normalize_event_types(tuple(raw_types))
    reminder_times = _ordered_valid(raw_times, tuple(DEFAULT_REMINDER_TIMES))
    subscribed = bool(event_types or reminder_times)
    if not subscribed:
        return ReminderCentreState(
            ok=True,
            subscribed=False,
            event_types=(),
            reminder_times=(),
            event_summary="not subscribed",
            time_summary="not set",
        )

    return ReminderCentreState(
        ok=True,
        subscribed=True,
        event_types=event_types,
        reminder_times=reminder_times,
        event_summary=_event_summary(event_types),
        time_summary=_format_list(reminder_times) if reminder_times else "times not set",
    )


async def build_reminder_centre_state(
    discord_user_id: int,
    *,
    config_loader: ConfigLoader = get_user_config,
) -> ReminderCentreState:
    config = await asyncio.to_thread(config_loader, int(discord_user_id))
    return _state_from_config(config)


async def save_reminder_preferences(
    discord_user_id: int,
    username: str,
    selected_types: list[Any] | tuple[Any, ...],
    selected_times: list[Any] | tuple[Any, ...],
    *,
    config_loader: ConfigLoader = get_user_config,
    writer: ConfigWriter = set_user_config,
) -> ReminderMutationResult:
    state = await build_reminder_centre_state(
        int(discord_user_id),
        config_loader=config_loader,
    )
    if not state.ok:
        return ReminderMutationResult(
            ok=False,
            action="update",
            message="Reminder data is temporarily unavailable. Please try again in a moment.",
        )

    event_types, adjusted = normalize_event_types(tuple(selected_types))
    reminder_times = normalize_reminder_times(tuple(selected_times))
    if not event_types:
        return ReminderMutationResult(
            ok=False,
            action="update" if state.subscribed else "subscribe",
            message="Choose at least one event type.",
        )

    action: ReminderAction = "update" if state.subscribed else "subscribe"
    try:
        await asyncio.to_thread(
            writer,
            int(discord_user_id),
            str(username),
            list(event_types),
            list(reminder_times),
        )
    except Exception:
        logger.exception(
            "player_self_service_reminders_save_failed user_id=%s action=%s",
            discord_user_id,
            action,
        )
        return ReminderMutationResult(
            ok=False,
            action=action,
            message="Failed to save your reminders. Please try again in a moment.",
        )
    logger.info(
        "player_self_service_reminders_saved user_id=%s action=%s event_types=%s times=%s adjusted=%s",
        discord_user_id,
        action,
        ",".join(event_types),
        ",".join(reminder_times),
        adjusted,
    )
    verb = "Subscribed" if action == "subscribe" else "Updated reminders"
    message = f"{verb}: events {_format_list(event_types)}; times {_format_list(reminder_times)}."
    if adjusted:
        message += " Some selections were adjusted to avoid duplicate reminders."

    return ReminderMutationResult(
        ok=True,
        action=action,
        message=message,
        event_types=event_types,
        reminder_times=reminder_times,
        adjusted=adjusted,
        dm_message=_build_saved_dm_message(
            action=action,
            event_types=event_types,
            reminder_times=reminder_times,
            adjusted=adjusted,
        ),
    )


async def prepare_unsubscribe_confirmation(
    discord_user_id: int,
    *,
    config_loader: ConfigLoader = get_user_config,
) -> tuple[ReminderUnsubscribeConfirmation | None, str | None]:
    state = await build_reminder_centre_state(
        int(discord_user_id),
        config_loader=config_loader,
    )
    if not state.ok:
        return None, "Reminder data is temporarily unavailable. Please try again in a moment."
    if not state.subscribed:
        return None, "You are not currently subscribed to KVK event reminders."
    return (
        ReminderUnsubscribeConfirmation(
            event_types=state.event_types,
            reminder_times=state.reminder_times,
        ),
        None,
    )


async def confirm_unsubscribe(
    discord_user_id: int,
    confirmation: ReminderUnsubscribeConfirmation,
    *,
    config_loader: ConfigLoader = get_user_config,
    remover: ConfigRemover = remove_user,
    task_canceller: TaskCanceller = _cancel_user_tasks_for_unsubscribe,
    scheduled_purger: TrackerPurger = purge_user_from_dm_scheduled_tracker,
    sent_purger: TrackerPurger = purge_user_from_dm_sent_tracker,
) -> ReminderMutationResult:
    state = await build_reminder_centre_state(
        int(discord_user_id),
        config_loader=config_loader,
    )
    if not state.ok:
        return ReminderMutationResult(
            ok=False,
            action="unsubscribe",
            message="Reminder data is temporarily unavailable. Please try again in a moment.",
        )
    if not state.subscribed:
        return ReminderMutationResult(
            ok=False,
            action="unsubscribe",
            message="You are already unsubscribed.",
        )
    if (
        state.event_types != confirmation.event_types
        or state.reminder_times != confirmation.reminder_times
    ):
        return ReminderMutationResult(
            ok=False,
            action="unsubscribe",
            message="This unsubscribe confirmation is stale. Reopen Reminder Centre and try again.",
        )

    try:
        cancelled = await task_canceller(int(discord_user_id))
        scheduled_removed = await asyncio.to_thread(scheduled_purger, int(discord_user_id))
        sent_removed = await asyncio.to_thread(sent_purger, int(discord_user_id))
        removed = await asyncio.to_thread(remover, int(discord_user_id))
    except Exception:
        logger.exception(
            "player_self_service_reminders_unsubscribe_failed user_id=%s",
            discord_user_id,
        )
        return ReminderMutationResult(
            ok=False,
            action="unsubscribe",
            message="Failed to unsubscribe. Please try again in a moment.",
        )
    if not removed:
        return ReminderMutationResult(
            ok=False,
            action="unsubscribe",
            message="You are already unsubscribed.",
        )

    logger.info(
        "player_self_service_reminders_unsubscribed user_id=%s tasks_cancelled=%s scheduled_removed=%s sent_removed=%s",
        discord_user_id,
        cancelled,
        scheduled_removed,
        sent_removed,
    )
    return ReminderMutationResult(
        ok=True,
        action="unsubscribe",
        message="You have been unsubscribed from KVK event reminders.",
        event_types=confirmation.event_types,
        reminder_times=confirmation.reminder_times,
        dm_message=_build_unsubscribed_dm_message(confirmation),
    )


def _event_summary(event_types: tuple[str, ...]) -> str:
    if "all" in event_types:
        return "all KVK events"
    return _format_list(event_types) if event_types else "events not set"


def _format_list(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "None"


def _build_saved_dm_message(
    *,
    action: ReminderAction,
    event_types: tuple[str, ...],
    reminder_times: tuple[str, ...],
    adjusted: bool,
) -> ReminderMessage:
    title = (
        "Subscribed to Event Reminders" if action == "subscribe" else "Reminder Preferences Updated"
    )
    fields = (
        ("Event Types", _format_list(event_types)),
        ("Reminder Times", _format_list(reminder_times)),
    )
    if adjusted:
        fields += (
            (
                "Note",
                "Some selections were adjusted to avoid duplicate reminders.",
            ),
        )
    return ReminderMessage(
        title=title,
        description="Your KVK event reminder preferences are now saved.",
        color=0x2ECC71 if action == "subscribe" else 0xF1C40F,
        fields=fields,
        footer="Manage these anytime from /me reminders.",
    )


def _build_unsubscribed_dm_message(
    confirmation: ReminderUnsubscribeConfirmation,
) -> ReminderMessage:
    return ReminderMessage(
        title="Unsubscribed",
        description="You have been unsubscribed from all KVK event reminders.",
        color=0xE74C3C,
        fields=(
            ("Previous Event Types", _format_list(confirmation.event_types)),
            ("Previous Reminder Times", _format_list(confirmation.reminder_times)),
        ),
        footer="You can re-subscribe anytime from /me reminders.",
    )
