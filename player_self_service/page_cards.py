"""Generated subpage card renderer for the /me command centre."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from player_self_service.service import PlayerSelfServiceSummary
from prekvk import report_image_renderer as text_renderer

WIDTH = 1702
HEIGHT = 924

TEXT = (246, 250, 255)
MUTED = (190, 206, 226)
PANEL = (13, 22, 36, 186)
LINE = (115, 139, 176, 170)
BLUE = (96, 165, 250)
GREEN = (74, 222, 128)
GOLD = (250, 204, 21)
RED = (248, 113, 113)

_CARD_DIR = Path(__file__).resolve().parent.parent / "assets" / "me" / "cards"
_BACKGROUND_BY_PAGE = {
    "accounts": "me accounts.png",
    "reminders": "me reminders.png",
    "preferences": "me preferences.png",
    "exports": "me exports.png",
}


@dataclass(frozen=True, slots=True)
class RenderedPageCard:
    filename: str
    image_bytes: BytesIO


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return text_renderer._font(size, bold=bold)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    return text_renderer._text_width(draw, text, font=font)


def _fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    size: int,
    min_size: int = 18,
    bold: bool = False,
) -> ImageFont.ImageFont:
    font = text_renderer._font_for_text(text, size, bold=bold)
    while size > min_size and _text_width(draw, text, font) > width:
        size -= 1
        font = text_renderer._font_for_text(text, size, bold=bold)
    return font


def _clean(value: object, *, fallback: str = "Unknown") -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return text or fallback


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, int, int] = TEXT,
    font: ImageFont.ImageFont | None = None,
    bold: bool = False,
) -> None:
    font = font or _font(28, bold=bold)
    text_renderer._draw_text(draw, xy, text, fill=fill, font=font, bold=bold)


def _status_color(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lower()
    if normalized in {"set", "single", "multiple", "on", "public", "private"}:
        return GREEN
    if normalized in {"none", "not set", "off", "not subscribed"}:
        return GOLD
    if normalized == "unknown":
        return RED
    return BLUE


def _status_label(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"set", "single", "multiple"}:
        return "READY"
    if normalized == "on":
        return "ON"
    if normalized == "off":
        return "OFF"
    if normalized == "public":
        return "PUBLIC"
    if normalized == "private":
        return "PRIVATE"
    if normalized in {"none", "not set", "not subscribed"}:
        return "SETUP"
    if normalized == "unknown":
        return "CHECK"
    return _clean(value, fallback="STATUS").upper()


def _load_background(page: str) -> Image.Image:
    filename = _BACKGROUND_BY_PAGE[page]
    with Image.open(_CARD_DIR / filename) as source:
        background = source.convert("RGBA")
    if background.size != (WIDTH, HEIGHT):
        background = background.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (4, 8, 16, 84))
    return Image.alpha_composite(background, overlay)


def _panel(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(xy, radius=18, fill=PANEL, outline=LINE, width=2)


def _badge(draw: ImageDraw.ImageDraw, *, x: int, y: int, text: str) -> None:
    color = _status_color(text)
    label = _status_label(text)
    width = 210
    font = _fit(draw, label, width=width - 44, size=30, min_size=18, bold=True)
    label_width = _text_width(draw, label, font)
    draw.rounded_rectangle((x, y, x + width, y + 50), radius=25, fill=color + (125,))
    _draw_text(
        draw,
        (x + (width - label_width) // 2, y + 10),
        label,
        font=font,
        bold=True,
    )


def _draw_wrapped_lines(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    width: int,
    lines: tuple[str, ...],
    size: int = 34,
    gap: int = 52,
) -> None:
    cursor_y = y
    for line in lines:
        text = _clean(line, fallback="-")
        font = _fit(draw, text, width=width, size=size, min_size=20, bold=True)
        _draw_text(draw, (x, cursor_y), text, font=font, bold=True)
        cursor_y += gap


def _account_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    accounts = summary.accounts
    names = ", ".join(accounts.account_names[:4]) if accounts.account_names else "None shown"
    return (
        f"Main: {accounts.main_label}",
        f"Linked accounts: {accounts.linked_count}",
        f"Known names: {names}",
        "Manage guides add, replace, remove, and ID lookup.",
    )


def _reminder_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    reminders = summary.reminders
    return (
        f"KVK reminders: {reminders.state}",
        f"Events: {reminders.event_summary}",
        f"Times: {reminders.time_summary}",
        "Calendar reminders are separate and planned for a later pass.",
    )


def _preference_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    preferences = summary.preferences
    return (
        f"Inventory visibility: {preferences.inventory_visibility}",
        "VIP level: available through Update VIP",
        f"Exports: {preferences.exports_summary}",
        "Preferences reuse existing inventory service storage.",
    )


def _export_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    exports = summary.exports
    return (
        f"Stats: {exports.stats_export}",
        f"Inventory: {exports.inventory_export}",
        exports.privacy_note,
        "Dashboard Quick Launch stays dashboard-only.",
    )


def _page_copy(
    page: str, summary: PlayerSelfServiceSummary
) -> tuple[str, str, str, tuple[str, ...]]:
    if page == "accounts":
        return (
            "Account Centre",
            summary.accounts.main_state,
            f"Next: {summary.accounts.next_action}",
            _account_lines(summary),
        )
    if page == "reminders":
        return (
            "Reminder Centre",
            summary.reminders.state,
            f"Next: {summary.reminders.next_action}",
            _reminder_lines(summary),
        )
    if page == "preferences":
        return (
            "Preferences",
            summary.preferences.inventory_visibility,
            f"Next: {summary.preferences.next_action}",
            _preference_lines(summary),
        )
    if page == "exports":
        return "Exports", "private", "Private export paths", _export_lines(summary)
    raise ValueError(f"Unsupported /me page card: {page}")


def render_page_card(
    page: str,
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
    generated_at_utc: datetime | None = None,
) -> RenderedPageCard:
    generated_at_utc = generated_at_utc or datetime.now(UTC)
    canvas = _load_background(page)
    draw = ImageDraw.Draw(canvas, "RGBA")
    title, status, action, lines = _page_copy(page, summary)

    _panel(draw, (72, 66, WIDTH - 72, 858))
    _draw_text(draw, (118, 110), title.upper(), fill=MUTED, font=_font(36, bold=True), bold=True)
    _badge(draw, x=WIDTH - 340, y=104, text=status)

    player = _clean(display_name, fallback="player")
    player_font = _fit(draw, player, width=900, size=64, min_size=32, bold=True)
    _draw_text(draw, (116, 176), player, font=player_font, bold=True)

    updated = generated_at_utc.strftime("%Y-%m-%d %H:%M UTC")
    _draw_text(draw, (118, 258), updated, fill=MUTED, font=_font(28))

    draw.line((118, 326, WIDTH - 118, 326), fill=LINE, width=2)
    _draw_wrapped_lines(draw, x=118, y=374, width=WIDTH - 236, lines=lines)

    draw.line((118, 756, WIDTH - 118, 756), fill=LINE, width=2)
    action_font = _fit(draw, action, width=WIDTH - 236, size=44, min_size=26, bold=True)
    _draw_text(draw, (118, 786), action, fill=BLUE, font=action_font, bold=True)

    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return RenderedPageCard(
        filename=f"me_{page}_{summary.discord_user_id}.png",
        image_bytes=output,
    )
