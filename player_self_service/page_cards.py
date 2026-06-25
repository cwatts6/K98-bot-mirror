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
BLUE = (96, 165, 250)
GREEN = (45, 178, 96)
GOLD = (250, 204, 21)
RED = (248, 113, 113)
SHADOW = (2, 6, 14)
DARK_TEXT = (7, 16, 28)

_CARD_DIR = Path(__file__).resolve().parent.parent / "assets" / "me" / "cards"
_BACKGROUND_BY_PAGE = {
    "dashboard": "me dashboard.png",
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
    shadow_xy = (xy[0] + 3, xy[1] + 3)
    text_renderer._draw_text(draw, shadow_xy, text, fill=SHADOW, font=font, bold=bold)
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


def _badge(draw: ImageDraw.ImageDraw, *, x: int, y: int, text: str) -> None:
    color = _status_color(text)
    label = _status_label(text)
    width = 210
    font = _fit(draw, label, width=width - 44, size=30, min_size=18, bold=True)
    draw.rounded_rectangle((x, y, x + width, y + 54), radius=27, fill=color + (210,))
    bbox = draw.textbbox((0, 0), label, font=font)
    label_width = bbox[2] - bbox[0]
    label_height = bbox[3] - bbox[1]
    text_renderer._draw_text(
        draw,
        (
            x + (width - label_width) // 2 - bbox[0],
            y + (54 - label_height) // 2 - bbox[1],
        ),
        label,
        fill=DARK_TEXT,
        font=font,
        bold=True,
    )


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    width: int,
    font: ImageFont.ImageFont,
) -> tuple[str, ...]:
    words = _clean(text, fallback="-").split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or _text_width(draw, candidate, font) <= width:
            current = candidate
            continue
        lines.append(current)
        current = word
    if current:
        lines.append(current)
    return tuple(lines) or ("-",)


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
        font = text_renderer._font_for_text(text, size, bold=True)
        wrapped = _wrap_text(draw, text, width=width, font=font)
        if len(wrapped) == 1:
            font = _fit(draw, text, width=width, size=size, min_size=28, bold=True)
            wrapped = (text,)
        for wrapped_line in wrapped:
            _draw_text(draw, (x, cursor_y), wrapped_line, font=font, bold=True)
            cursor_y += gap


def _account_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    accounts = summary.accounts
    names = ", ".join(accounts.account_names) if accounts.account_names else "None shown"
    return (
        f"Main: {accounts.main_label}",
        f"Linked accounts: {accounts.linked_count}",
        f"Account Names: {names}",
    )


def _reminder_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    reminders = summary.reminders
    return (
        f"KVK reminders: {reminders.state}",
        f"Calendar reminders: {reminders.calendar.state}",
        f"Events: {reminders.event_summary}",
        f"Calendar events: {reminders.calendar.event_summary}",
        f"KVK times: {reminders.time_summary}",
        f"Calendar lead times: {reminders.calendar.time_summary}",
    )


def _preference_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    preferences = summary.preferences
    return (
        f"Inventory visibility: {preferences.inventory_visibility}",
        f"VIP levels: {preferences.vip_summary}",
    )


def _export_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    exports = summary.exports
    return (
        f"Stats: {exports.stats_export}",
        f"Inventory: {exports.inventory_export}",
        exports.privacy_note,
        "This page is private export guidance; dashboard Quick Launch stays dashboard-only.",
    )


def _account_action_detail(summary: PlayerSelfServiceSummary) -> str:
    if summary.accounts.linked_count <= 0:
        return "Find ID by name, then add a governor to an available account slot."
    return "Find ID, replace, remove, and add governors when a slot is open."


def _reminder_action_detail(summary: PlayerSelfServiceSummary) -> str:
    if summary.reminders.combined_state.strip().lower() == "off":
        return "Choose KVK reminders here or use Calendar Settings for calendar reminders."
    return "Manage KVK autosave choices here; Calendar Settings manages calendar reminder offsets."


def _dashboard_lines(summary: PlayerSelfServiceSummary) -> tuple[str, ...]:
    return (
        f"Main account: {summary.accounts.main_state}",
        f"Linked accounts: {summary.accounts.linked_label}",
        f"KVK reminders: {summary.reminders.state}",
        f"Calendar reminders: {summary.reminders.calendar.state}",
        f"Inventory: {summary.preferences.inventory_visibility}",
        "Exports: private",
    )


def _preference_actions(summary: PlayerSelfServiceSummary) -> str:
    visibility = summary.preferences.inventory_visibility.strip().lower()
    visibility_action = "Set Public" if visibility == "private" else "Set Private"
    return f"Actions available: {visibility_action}, Update VIP"


def _page_copy(
    page: str, summary: PlayerSelfServiceSummary
) -> tuple[str, str, str, str, tuple[str, ...]]:
    if page == "dashboard":
        return (
            "Personal Command Centre",
            summary.accounts.main_state,
            "Actions available: Accounts, Reminders, Preferences, Quick Launch",
            "Quick Launch stays on Dashboard; detailed setup lives on each private page.",
            _dashboard_lines(summary),
        )
    if page == "accounts":
        return (
            "Account Centre",
            summary.accounts.main_state,
            "Actions available: Manage",
            _account_action_detail(summary),
            _account_lines(summary),
        )
    if page == "reminders":
        return (
            "Reminder Centre",
            summary.reminders.combined_state,
            "Actions available: Manage",
            _reminder_action_detail(summary),
            _reminder_lines(summary),
        )
    if page == "preferences":
        return (
            "Preferences",
            summary.preferences.inventory_visibility,
            _preference_actions(summary),
            "Switch inventory visibility or update VIP level.",
            _preference_lines(summary),
        )
    if page == "exports":
        return (
            "Exports",
            "private",
            "Actions available: Dashboard, Accounts, Reminders, Preferences",
            "Export files are still delivered through the existing private export flows.",
            _export_lines(summary),
        )
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
    title, status, action, action_detail, lines = _page_copy(page, summary)

    _draw_text(draw, (108, 92), title.upper(), fill=MUTED, font=_font(42, bold=True), bold=True)
    _badge(draw, x=WIDTH - 330, y=90, text=status)

    player = _clean(display_name, fallback="player")
    player_font = _fit(draw, player, width=980, size=70, min_size=34, bold=True)
    _draw_text(draw, (106, 174), player, font=player_font, bold=True)

    updated = generated_at_utc.strftime("%Y-%m-%d %H:%M UTC")
    timestamp_font = _font(26)
    timestamp_width = _text_width(draw, updated, timestamp_font)
    _draw_text(
        draw,
        (WIDTH - timestamp_width - 104, HEIGHT - 72),
        updated,
        fill=MUTED,
        font=timestamp_font,
    )

    _draw_wrapped_lines(draw, x=108, y=332, width=WIDTH - 216, lines=lines, size=46, gap=66)

    action_font = _fit(draw, action, width=WIDTH - 216, size=44, min_size=26, bold=True)
    _draw_text(draw, (108, 720), action, fill=BLUE, font=action_font, bold=True)
    detail_font = _fit(draw, action_detail, width=WIDTH - 216, size=30, min_size=22, bold=False)
    _draw_text(draw, (108, 778), action_detail, fill=MUTED, font=detail_font)

    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return RenderedPageCard(
        filename=f"me_{page}_{summary.discord_user_id}.png",
        image_bytes=output,
    )
