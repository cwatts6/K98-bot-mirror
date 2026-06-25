"""Generated dashboard card renderer for the /me command centre."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from player_self_service.service import PlayerSelfServiceSummary
from . import page_cards

WIDTH = page_cards.WIDTH
HEIGHT = page_cards.HEIGHT


@dataclass(frozen=True, slots=True)
class RenderedDashboardCard:
    filename: str
    image_bytes: BytesIO


def _status_label(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"set", "single", "multiple"}:
        return "READY"
    if normalized == "on":
        return "ON"
    if normalized == "public":
        return "PUBLIC"
    if normalized == "private":
        return "PRIVATE"
    if normalized in {"not set", "none"}:
        return "SETUP"
    if normalized in {"off", "not subscribed"}:
        return "OFF"
    if normalized == "incomplete":
        return "SETUP"
    if normalized == "unknown":
        return "CHECK"
    return str(value or "STATUS").strip().upper() or "STATUS"


def _linked_display(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.endswith(" linked"):
        normalized = normalized.removesuffix(" linked")
    return normalized or "unknown"


def _account_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    accounts = summary.accounts
    return (
        f"Main: {accounts.main_label}",
        f"Linked: {_linked_display(accounts.linked_label)}",
        f"Accounts: {accounts.linked_count}",
    )


def _reminder_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    reminders = summary.reminders
    return (
        f"KVK: {reminders.event_summary}",
        f"Calendar: {reminders.calendar.event_summary}",
        f"Times: {reminders.time_summary}",
        f"Lead times: {reminders.calendar.time_summary}",
    )


def _preference_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    preferences = summary.preferences
    return (
        f"Inventory: {preferences.inventory_visibility}",
        "Exports: private",
    )


def render_dashboard_card(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
    generated_at_utc: datetime | None = None,
) -> RenderedDashboardCard:
    rendered = page_cards.render_page_card(
        "dashboard",
        summary,
        display_name=display_name,
        generated_at_utc=generated_at_utc,
    )
    return RenderedDashboardCard(
        filename=rendered.filename,
        image_bytes=rendered.image_bytes,
    )
