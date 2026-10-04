"""Deterministic 1702x924 renderer for Accounts and Account Summary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from core import visual_contract, visual_text
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
    AccountSummaryPage,
)

WIDTH = 1702
HEIGHT = 924
_BACKGROUND = Path(__file__).resolve().parent.parent / "assets" / "me" / "cards" / "me_accounts.png"
_TEXT = visual_contract.TEXT
_MUTED = visual_contract.MUTED
_BLUE = visual_contract.BLUE
_GOLD = visual_contract.GOLD
_GREEN = visual_contract.GREEN
_AMBER = visual_contract.AMBER
_RED = visual_contract.RED
_PANEL = visual_contract.PANEL


@dataclass(frozen=True, slots=True)
class RenderedAccountsCard:
    filename: str
    image_bytes: bytes
    width: int = WIDTH
    height: int = HEIGHT


def _clean(value: Any, *, missing: str = "—") -> str:
    if value is None:
        return missing
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text or missing


def _compact(value: int | None) -> str:
    return visual_contract.format_compact_number(value)


def _compact_detail(value: int | None) -> str:
    return visual_contract.format_compact_number(value)


def _number(value: Any) -> str:
    if value is None:
        return "—"
    try:
        numeric = int(value)
        return f"{numeric:,}"
    except (TypeError, ValueError):
        return _clean(value)


def _date(value: datetime | None, *, include_time: bool = False) -> str:
    if value is None:
        return "—"
    stamp = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return (
        visual_contract.format_utc_datetime(stamp) if include_time else stamp.strftime("%d %b %Y")
    )


def format_whole_number(value: Any) -> str:
    if value is None:
        return "—"
    try:
        rounded = Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return str(rounded)
    except (InvalidOperation, TypeError, ValueError):
        return _clean(value)


def _score(value: Decimal | None) -> str:
    if value is None:
        return "—"
    rendered = f"{value:.1f}"
    return rendered.removesuffix(".0")


def format_tanking_score(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{_score(value)}%"


def format_discord_heading(display_name: str, *, kingdom_id: int = 1198) -> str:
    """Return the shared /me identity without duplicating a saved kingdom suffix."""
    cleaned = _clean(display_name)
    suffix = f"({int(kingdom_id)})"
    if cleaned.casefold().endswith(suffix.casefold()):
        return cleaned
    return f"{cleaned} {suffix}"


def _discord_heading(display_name: str) -> str:
    return format_discord_heading(display_name)


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    *,
    width: int,
    size: int = 22,
    min_size: int = 13,
    fill: tuple[int, int, int, int] = _TEXT,
    bold: bool = False,
    right_align: bool = False,
) -> None:
    fitted = visual_text.fit_font(
        draw,
        _clean(value),
        max_width=max(1, width),
        size=size,
        min_size=min_size,
        bold=bold,
    )
    fitted_value = visual_text.fit_text_to_width(
        draw, _clean(value), width=max(1, width), base_font=fitted, bold=bold
    )
    draw_x = xy[0]
    if right_align:
        draw_x += width - visual_text.text_width(draw, fitted_value, font=fitted, bold=bold)
    visual_text.draw_text(
        draw,
        (draw_x, xy[1]),
        fitted_value,
        font=fitted,
        fill=fill,
        bold=bold,
        embedded_color=True,
    )


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 16) -> None:
    visual_contract.draw_panel(draw, box, radius=radius)


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    with Image.open(_BACKGROUND) as source:
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"Accounts backdrop must be {WIDTH}x{HEIGHT}; got {source.size}")
        canvas = source.convert("RGBA")
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", canvas.size, (0, 5, 17, 76)))
    return canvas, ImageDraw.Draw(canvas, "RGBA")


def paste_discord_avatar(canvas: Image.Image, avatar_bytes: bytes | None) -> bool:
    """Paste a real or fallback /me avatar.

    Return True only when readable avatar bytes supplied the real avatar.
    """
    return visual_contract.paste_core_avatar(canvas, avatar_bytes)


def _avatar(canvas: Image.Image, avatar_bytes: bytes | None) -> bool:
    return paste_discord_avatar(canvas, avatar_bytes)


def _encode(canvas: Image.Image, filename: str) -> RenderedAccountsCard:
    stream = BytesIO()
    try:
        canvas.convert("RGB").save(stream, format="PNG", optimize=True)
        return RenderedAccountsCard(filename=filename, image_bytes=stream.getvalue())
    finally:
        stream.close()
        canvas.close()


def _coverage(metric: AccountMetricTotal) -> str:
    return f"{metric.reporting_count}/{metric.expected_count} reporting"


def _metric_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    helper: str,
    *,
    large: bool = False,
) -> None:
    _panel(draw, box, 13)
    x0, y0, x1, _ = box
    label_y = y0 + (18 if large else 13)
    value_y = y0 + (52 if large else 42)
    helper_y = y0 + (112 if large else 84)
    _text(
        draw,
        (x0 + 18, label_y),
        label,
        width=x1 - x0 - 36,
        size=19 if large else 17,
        fill=_BLUE,
        bold=True,
    )
    _text(
        draw,
        (x0 + 18, value_y),
        value,
        width=x1 - x0 - 36,
        size=40 if large else 34,
        min_size=27 if large else 24,
        bold=True,
    )
    _text(
        draw,
        (x0 + 18, helper_y),
        helper,
        width=x1 - x0 - 36,
        size=17 if large else 15,
        min_size=13 if large else 12,
        fill=_MUTED,
        right_align=True,
    )


def _state_colour(state: str) -> tuple[int, int, int, int]:
    return visual_contract.state_colour(state)


def _data_colour(state: str) -> tuple[int, int, int, int]:
    if state == "UNRESOLVED":
        return _RED
    return visual_contract.state_colour(state)


def _role_helper(payload: AccountsPortfolioPayload) -> str:
    parts = [f"{count} {role}" for role, count in payload.role_counts if count]
    return " • ".join(parts) or "No linked roles"


def format_governor_count(count: int) -> str:
    """Return a compact linked-governor count with correct grammar."""
    return f"{count} {'governor' if count == 1 else 'governors'}"


def _linked_governor_entries(
    payload: AccountsPortfolioPayload,
) -> tuple[tuple[str, str, str, str, str], ...]:
    if len(payload.rows) <= 8:
        source_rows = payload.rows
        overflow = 0
    else:
        source_rows = payload.rows[:7]
        overflow = len(payload.rows) - 7
    entries = [
        (
            row.slot,
            row.display_name,
            str(row.governor_id) if row.governor_id is not None else "—",
            _compact(row.power),
            row.data_state,
        )
        for row in source_rows
    ]
    if overflow:
        entries.append(("", f"+ {overflow} more — open Account Summary", "", "", ""))
    if not entries:
        entries.append(("—", "No linked governors", "—", "—", "UNRESOLVED"))
    return tuple(entries)


def render_accounts_card(
    payload: AccountsPortfolioPayload,
    *,
    display_name: str,
    avatar_bytes: bytes | None = None,
) -> RenderedAccountsCard:
    canvas, draw = _canvas()
    _avatar(canvas, avatar_bytes)
    draw = ImageDraw.Draw(canvas, "RGBA")
    _text(draw, (270, 48), "ACCOUNT CENTRE", width=730, size=42, min_size=30, bold=True)
    _text(
        draw,
        (270, 103),
        _discord_heading(display_name),
        width=730,
        size=31,
        min_size=20,
        fill=_GOLD,
        bold=True,
    )
    _text(
        draw,
        (270, 149),
        f"{format_governor_count(payload.linked_count)} • {_role_helper(payload)}",
        width=730,
        size=27,
        min_size=18,
        bold=True,
    )
    visual_contract.draw_state_pill(draw, payload.state)
    _text(
        draw,
        (1010, 127),
        "LATEST SNAPSHOTS",
        width=595,
        size=24,
        min_size=17,
        fill=_BLUE,
        bold=True,
        right_align=True,
    )
    _text(
        draw,
        (1010, 165),
        f"Data refreshed {_date(payload.latest_scan_date, include_time=True)}",
        width=595,
        size=14,
        min_size=10,
        fill=_MUTED,
        right_align=True,
    )
    boxes = [(95 + index * 385, 230, 450 + index * 385, 388) for index in range(4)]
    _metric_box(
        draw,
        boxes[0],
        "LINKED",
        str(payload.linked_count),
        _role_helper(payload),
        large=True,
    )
    _metric_box(
        draw,
        boxes[1],
        "PORTFOLIO POWER",
        _compact(payload.power.value),
        _coverage(payload.power),
        large=True,
    )
    _metric_box(
        draw,
        boxes[2],
        "T4+T5 KILLS",
        _compact(payload.t4_t5_kills.value),
        _coverage(payload.t4_t5_kills),
        large=True,
    )
    _metric_box(
        draw,
        boxes[3],
        "RSS TOTAL",
        _compact(payload.rss_total.value),
        _coverage(payload.rss_total),
        large=True,
    )

    _panel(draw, (95, 414, 1605, 705))
    _text(draw, (119, 432), "LINKED GOVERNORS", width=600, size=20, fill=_BLUE, bold=True)
    tile_width = 725
    for index, (slot, governor, governor_id, power, data_state) in enumerate(
        _linked_governor_entries(payload)
    ):
        column = index % 2
        row_index = index // 2
        x = 115 + column * 750
        y = 455 + row_index * 60
        draw.rounded_rectangle(
            (x, y, x + tile_width, y + 57),
            radius=8,
            fill=(5, 18, 35, 205),
            outline=(76, 150, 212, 92),
            width=1,
        )
        if not slot:
            _text(draw, (x + 16, y + 17), governor, width=720, size=21, min_size=16, fill=_BLUE)
            continue
        _text(draw, (x + 14, y + 7), slot, width=105, size=20, min_size=16, bold=True)
        _text(draw, (x + 122, y + 5), governor, width=405, size=23, min_size=17)
        _text(
            draw,
            (x + 592, y + 8),
            data_state,
            width=145,
            size=17,
            min_size=13,
            fill=_data_colour(data_state),
            bold=True,
        )
        _text(
            draw,
            (x + 14, y + 34),
            f"ID  {governor_id}",
            width=245,
            size=16,
            min_size=13,
            fill=_MUTED,
        )
        _text(
            draw,
            (x + 285, y + 35),
            "POWER",
            width=75,
            size=14,
            min_size=12,
            fill=_MUTED,
            bold=True,
        )
        _text(
            draw,
            (x + 365, y + 29),
            power,
            width=190,
            size=23,
            min_size=17,
            bold=True,
        )

    _panel(draw, (95, 722, 1605, 803), 18)
    _text(draw, (119, 738), "PORTFOLIO INSIGHT", width=285, size=16, fill=_GOLD, bold=True)
    _text(draw, (407, 734), payload.insight, width=1174, size=20, min_size=15)
    _text(draw, (95, 816), "Manage", width=330, size=20, fill=_BLUE, bold=True)
    _text(
        draw,
        (95, 849),
        "Find an ID, add, replace or remove a linked governor.",
        width=950,
        size=18,
        fill=_MUTED,
    )
    _text(
        draw,
        (1325, 845),
        f"Generated {visual_contract.format_utc_datetime(payload.refreshed_at_utc)}",
        width=280,
        size=15,
        min_size=11,
        fill=_MUTED,
    )
    return _encode(canvas, f"me_accounts_{payload.discord_user_id}.png")


def _summary_columns(page: AccountSummaryPage) -> tuple[tuple[str, int], ...]:
    if page.section == "combat":
        return (
            ("SLOT", 100),
            ("GOVERNOR", 250),
            ("KILL POINTS", 180),
            ("T4+T5", 155),
            ("DEADS", 145),
            ("HEALED", 160),
            ("ACCLAIM", 150),
            ("KP LOSS", 160),
            ("TANKING", 170),
        )
    if page.section == "economy":
        return (
            ("SLOT", 100),
            ("GOVERNOR", 240),
            ("RSS GATHERED", 200),
            ("RSS ASSISTANCE", 210),
            ("RSS TOTAL", 170),
            ("HELPS", 145),
            ("CONDUCT", 130),
            ("INVENTORY AS OF", 280),
        )
    return (
        ("SLOT", 100),
        ("GOVERNOR", 220),
        ("CIVILISATION", 170),
        ("CH", 70),
        ("VIP", 145),
        ("POWER", 165),
        ("TROOP POWER", 175),
        ("LOCATION", 135),
        ("LAST SCAN", 275),
    )


def _summary_values(page: AccountSummaryPage, row: AccountPortfolioRow) -> tuple[str, ...]:
    if page.section == "combat":
        return (
            row.slot,
            row.display_name,
            _compact_detail(row.kill_points),
            _compact_detail(row.t4_t5_kills),
            _compact_detail(row.deads),
            _compact_detail(row.healed_troops),
            _compact_detail(row.highest_acclaim),
            _compact_detail(row.kp_loss),
            format_tanking_score(row.tanking_score),
        )
    if page.section == "economy":
        return (
            row.slot,
            row.display_name,
            _compact_detail(row.rss_gathered),
            _compact_detail(row.rss_assistance),
            _compact_detail(row.rss_total),
            _compact_detail(row.helps),
            format_whole_number(row.conduct),
            _date(row.inventory_as_of),
        )
    location = (
        f"{row.location_x}:{row.location_y}"
        if row.location_x is not None and row.location_y is not None
        else "—"
    )
    return (
        row.slot,
        row.display_name,
        _clean(row.civilisation),
        _number(row.city_hall),
        _clean(row.vip_level),
        _compact_detail(row.power),
        _compact_detail(row.troop_power),
        location,
        _date(row.last_governor_scan, include_time=True),
    )


def _summary_section_label(section: str) -> str:
    return {
        "overview": "OVERVIEW",
        "combat": "COMBAT",
        "economy": "ECONOMY & ACTIVITY",
    }[section]


def _summary_footer_label(section: str) -> str:
    if section == "combat":
        return "Combat all linked governors (Tanking: Higher = Better)"
    return f"{_summary_section_label(section).title()} • all linked governors"


def render_account_summary_card(
    page: AccountSummaryPage,
    *,
    display_name: str,
    avatar_bytes: bytes | None = None,
) -> RenderedAccountsCard:
    payload = page.payload
    canvas, draw = _canvas()
    _avatar(canvas, avatar_bytes)
    draw = ImageDraw.Draw(canvas, "RGBA")
    _text(draw, (270, 48), "ACCOUNT SUMMARY", width=730, size=42, min_size=30, bold=True)
    _text(
        draw,
        (270, 103),
        _discord_heading(display_name),
        width=730,
        size=31,
        min_size=20,
        fill=_GOLD,
        bold=True,
    )
    _text(
        draw,
        (270, 149),
        f"{format_governor_count(payload.linked_count)} • {_summary_section_label(page.section)}",
        width=730,
        size=27,
        min_size=18,
        bold=True,
    )
    visual_contract.draw_state_pill(draw, payload.state)
    _text(
        draw,
        (1010, 127),
        f"{_summary_section_label(page.section).title()} • Page {page.page} / {page.page_count}",
        width=595,
        size=24,
        min_size=17,
        fill=_BLUE,
        bold=True,
    )
    _text(
        draw,
        (1010, 165),
        f"Data refreshed {_date(payload.latest_scan_date, include_time=True)}",
        width=595,
        size=14,
        min_size=10,
        fill=_MUTED,
    )

    labels = (
        ("TOTAL POWER", payload.power),
        ("TROOP POWER", payload.troop_power),
        ("T4+T5 KILLS", payload.t4_t5_kills),
        ("RSS TOTAL", payload.rss_total),
    )
    for index, (label, metric) in enumerate(labels):
        x0 = 95 + index * 385
        _metric_box(
            draw, (x0, 230, x0 + 355, 343), label, _compact(metric.value), _coverage(metric)
        )

    section_label = _summary_section_label(page.section)
    _text(draw, (95, 370), section_label, width=850, size=23, fill=_BLUE, bold=True)
    _text(
        draw, (1380, 373), f"Page {page.page} / {page.page_count}", width=225, size=18, fill=_MUTED
    )
    _panel(draw, (95, 413, 1605, 803))
    columns = _summary_columns(page)
    x_positions: list[int] = []
    x = 115
    for label, width in columns:
        x_positions.append(x)
        _text(draw, (x, 435), label, width=width - 10, size=17, min_size=11, fill=_MUTED, bold=True)
        x += width
    draw.line((115, 467, 1585, 467), fill=visual_contract.PANEL_EDGE, width=2)
    if not page.rows:
        _text(draw, (115, 500), "No linked governors to show.", width=1450, size=22, fill=_MUTED)
    for row_index, row in enumerate(page.rows):
        y = 488 + row_index * 38
        values = _summary_values(page, row)
        if row_index % 2:
            draw.rounded_rectangle((107, y - 5, 1593, y + 30), radius=7, fill=(35, 64, 96, 58))
        for value, (label, width), x in zip(values, columns, x_positions, strict=True):
            colour = _data_colour(value) if label == "DATA" else _TEXT
            _text(
                draw,
                (x, y),
                value,
                width=width - 10,
                size=21,
                min_size=13,
                fill=colour,
                bold=label == "SLOT",
            )

    footer_label = _summary_footer_label(page.section)
    _text(
        draw,
        (95, 845),
        footer_label,
        width=1050,
        size=17,
        fill=_MUTED,
    )
    _text(
        draw,
        (1325, 845),
        f"Generated {visual_contract.format_utc_datetime(payload.refreshed_at_utc)}",
        width=280,
        size=15,
        min_size=10,
        fill=_MUTED,
    )
    return _encode(canvas, f"me_account_summary_{payload.discord_user_id}.png")
