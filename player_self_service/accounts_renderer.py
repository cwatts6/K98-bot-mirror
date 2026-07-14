"""Deterministic 1702x924 renderer for Accounts and Account Summary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from core import visual_text
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
    AccountSummaryPage,
)
from utils import fmt_short

WIDTH = 1702
HEIGHT = 924
_BACKGROUND = Path(__file__).resolve().parent.parent / "assets" / "me" / "cards" / "me_accounts.png"
_TEXT = (244, 247, 255, 255)
_MUTED = (170, 185, 205, 255)
_BLUE = (92, 174, 255, 255)
_GOLD = (241, 194, 97, 255)
_GREEN = (104, 221, 170, 255)
_AMBER = (255, 190, 93, 255)
_RED = (255, 125, 125, 255)
_PANEL = (4, 12, 28, 202)


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
    if value is None:
        return "—"
    text = fmt_short(value).replace("k", "K")
    if len(text) >= 3 and text[-1:] in "KMB" and text[-3:-1] == ".0":
        return text[:-3] + text[-1]
    return text


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
    return stamp.strftime("%d %b %Y %H:%M") if include_time else stamp.strftime("%d %b %Y")


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
    visual_text.draw_text(
        draw,
        xy,
        fitted_value,
        font=fitted,
        fill=fill,
        bold=bold,
        embedded_color=True,
    )


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 16) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=_PANEL, outline=(71, 130, 187, 125), width=2)


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    with Image.open(_BACKGROUND) as source:
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"Accounts backdrop must be {WIDTH}x{HEIGHT}; got {source.size}")
        canvas = source.convert("RGBA")
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", canvas.size, (0, 5, 17, 76)))
    return canvas, ImageDraw.Draw(canvas, "RGBA")


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
) -> None:
    _panel(draw, box, 13)
    x0, y0, x1, _ = box
    _text(draw, (x0 + 18, y0 + 13), label, width=x1 - x0 - 36, size=17, fill=_BLUE, bold=True)
    _text(draw, (x0 + 18, y0 + 42), value, width=x1 - x0 - 36, size=34, min_size=24, bold=True)
    _text(draw, (x0 + 18, y0 + 84), helper, width=x1 - x0 - 36, size=15, min_size=12, fill=_MUTED)


def _state_colour(state: str) -> tuple[int, int, int, int]:
    return {"READY": _GREEN, "REVIEW": _AMBER, "SETUP": _BLUE}.get(state, _MUTED)


def _data_colour(state: str) -> tuple[int, int, int, int]:
    return {"CURRENT": _GREEN, "STALE": _AMBER, "NO DATA": _RED}.get(state, _RED)


def _role_helper(payload: AccountsPortfolioPayload) -> str:
    parts = [f"{count} {role}" for role, count in payload.role_counts if count]
    return " • ".join(parts) or "No linked roles"


def render_accounts_card(
    payload: AccountsPortfolioPayload,
    *,
    display_name: str,
) -> RenderedAccountsCard:
    canvas, draw = _canvas()
    _text(draw, (68, 40), "ACCOUNT CENTRE", width=900, size=34, bold=True)
    _text(
        draw,
        (1385, 45),
        payload.state,
        width=245,
        size=27,
        min_size=21,
        fill=_state_colour(payload.state),
        bold=True,
    )
    _text(draw, (68, 91), f"{_clean(display_name)} (1198)", width=1150, size=31, bold=True)
    _text(
        draw,
        (1385, 96),
        f"{payload.linked_count} governors",
        width=245,
        size=21,
        min_size=16,
        fill=_MUTED,
    )
    main = payload.main_row
    main_label = (
        f"{main.display_name} • {main.governor_id or '—'}" if main is not None else "Not configured"
    )
    _text(draw, (68, 143), "MAIN GOVERNOR", width=230, size=17, fill=_GOLD, bold=True)
    _text(draw, (298, 139), main_label, width=1050, size=24, min_size=17, bold=True)

    _text(draw, (68, 194), "LATEST SNAPSHOTS", width=500, size=17, fill=_BLUE, bold=True)
    boxes = [(68 + index * 397, 224, 445 + index * 397, 342) for index in range(4)]
    _metric_box(draw, boxes[0], "LINKED", str(payload.linked_count), _role_helper(payload))
    _metric_box(
        draw, boxes[1], "PORTFOLIO POWER", _compact(payload.power.value), _coverage(payload.power)
    )
    _metric_box(
        draw,
        boxes[2],
        "T4+T5 KILLS",
        _compact(payload.t4_t5_kills.value),
        _coverage(payload.t4_t5_kills),
    )
    _metric_box(
        draw, boxes[3], "RSS TOTAL", _compact(payload.rss_total.value), _coverage(payload.rss_total)
    )

    _panel(draw, (68, 374, 1634, 697))
    _text(draw, (92, 392), "LINKED GOVERNORS", width=600, size=18, fill=_BLUE, bold=True)
    columns = (("SLOT", 92, 170), ("GOVERNOR", 280, 515), ("ID", 815, 230), ("POWER", 1065, 250), ("DATA", 1350, 230))
    for label, x, width in columns:
        _text(draw, (x, 426), label, width=width, size=15, fill=_MUTED, bold=True)
    draw.line((92, 451, 1610, 451), fill=(91, 140, 190, 110), width=1)
    visible_rows: list[tuple[str, str, str, str, str]] = []
    if len(payload.rows) <= 8:
        source_rows = payload.rows
        overflow = 0
    else:
        source_rows = payload.rows[:7]
        overflow = len(payload.rows) - 7
    for row in source_rows:
        visible_rows.append(
            (
                row.slot,
                row.display_name,
                str(row.governor_id) if row.governor_id is not None else "—",
                _compact(row.power),
                row.data_state,
            )
        )
    if overflow:
        visible_rows.append(("", f"+ {overflow} more — open Account Summary", "", "", ""))
    if not visible_rows:
        visible_rows.append(("—", "No linked governors", "—", "—", "UNRESOLVED"))
    for index, values in enumerate(visible_rows):
        y = 464 + index * 27
        for value, (_label, x, width) in zip(values, columns, strict=True):
            colour = _data_colour(value) if _label == "DATA" else _TEXT
            _text(draw, (x, y), value, width=width, size=17, min_size=13, fill=colour, bold=_label == "SLOT")

    _panel(draw, (68, 714, 1634, 795), 13)
    _text(draw, (92, 730), "PORTFOLIO INSIGHT", width=285, size=16, fill=_GOLD, bold=True)
    _text(draw, (380, 726), payload.insight, width=1225, size=20, min_size=15)
    _text(draw, (68, 816), "Manage accounts", width=330, size=20, fill=_BLUE, bold=True)
    _text(
        draw,
        (68, 849),
        "Find an ID, add, replace or remove a linked governor.",
        width=950,
        size=18,
        fill=_MUTED,
    )
    refreshed = payload.refreshed_at_utc.astimezone(UTC)
    _text(draw, (1390, 850), f"Refreshed {refreshed:%H:%M UTC}", width=244, size=16, min_size=13, fill=_MUTED)
    return _encode(canvas, f"me_accounts_{payload.discord_user_id}.png")


def _summary_columns(page: AccountSummaryPage) -> tuple[tuple[str, int], ...]:
    if page.section == "combat":
        return (
            ("SLOT", 105), ("GOVERNOR", 230), ("KILL POINTS", 165), ("T4+T5", 145),
            ("DEADS", 135), ("HEALED", 145), ("ACCLAIM", 130), ("HELPS", 115),
            ("CONDUCT", 125),
        )
    if page.section == "economy":
        return (
            ("SLOT", 125), ("GOVERNOR", 300), ("RSS GATHERED", 225),
            ("RSS ASSISTANCE", 235), ("RSS TOTAL", 210), ("INVENTORY AS OF", 235),
            ("DATA", 150),
        )
    return (
        ("SLOT", 95), ("GOVERNOR", 220), ("GOVERNOR ID", 155), ("CIVILISATION", 165),
        ("CH", 65), ("POWER", 130), ("TROOP POWER", 140), ("LOCATION", 115),
        ("DATA", 105), ("LAST SCAN", 175),
    )


def _summary_values(page: AccountSummaryPage, row: AccountPortfolioRow) -> tuple[str, ...]:
    if page.section == "combat":
        return (
            row.slot, row.display_name, _number(row.kill_points), _number(row.t4_t5_kills),
            _number(row.deads), _number(row.healed_troops), _number(row.highest_acclaim),
            _number(row.helps), _clean(row.conduct),
        )
    if page.section == "economy":
        return (
            row.slot, row.display_name, _number(row.rss_gathered), _number(row.rss_assistance),
            _number(row.rss_total), _date(row.inventory_as_of), row.data_state,
        )
    location = (
        f"{row.location_x}:{row.location_y}"
        if row.location_x is not None and row.location_y is not None
        else "—"
    )
    return (
        row.slot, row.display_name, str(row.governor_id or "—"), _clean(row.civilisation),
        _number(row.city_hall), _number(row.power), _number(row.troop_power), location,
        row.data_state, _date(row.last_governor_scan),
    )


def render_account_summary_card(
    page: AccountSummaryPage,
    *,
    display_name: str,
) -> RenderedAccountsCard:
    payload = page.payload
    canvas, draw = _canvas()
    _text(draw, (68, 38), "ACCOUNT SUMMARY", width=820, size=33, bold=True)
    _text(draw, (68, 86), f"{_clean(display_name)} (1198)", width=1000, size=25, bold=True)
    _text(
        draw, (1375, 43), payload.state, width=255, size=25,
        fill=_state_colour(payload.state), bold=True,
    )
    _text(draw, (1375, 84), f"{payload.linked_count} governors", width=255, size=18, fill=_MUTED)

    labels = (
        ("TOTAL POWER", payload.power),
        ("TROOP POWER", payload.troop_power),
        ("T4+T5 KILLS", payload.t4_t5_kills),
        ("RSS TOTAL", payload.rss_total),
    )
    for index, (label, metric) in enumerate(labels):
        x0 = 68 + index * 397
        _metric_box(draw, (x0, 135, x0 + 377, 248), label, _compact(metric.value), _coverage(metric))

    section_label = {
        "overview": "OVERVIEW",
        "combat": "COMBAT & PARTICIPATION",
        "economy": "ECONOMY & ACTIVITY",
    }[page.section]
    _text(draw, (68, 275), section_label, width=850, size=23, fill=_BLUE, bold=True)
    _text(draw, (1405, 278), f"Page {page.page} / {page.page_count}", width=225, size=18, fill=_MUTED)
    _panel(draw, (68, 318, 1634, 816))
    columns = _summary_columns(page)
    x_positions: list[int] = []
    x = 88
    for label, width in columns:
        x_positions.append(x)
        _text(draw, (x, 340), label, width=width - 10, size=14, min_size=10, fill=_MUTED, bold=True)
        x += width
    draw.line((88, 372, 1614, 372), fill=(91, 140, 190, 120), width=1)
    if not page.rows:
        _text(draw, (88, 405), "No linked governors to show.", width=1450, size=22, fill=_MUTED)
    for row_index, row in enumerate(page.rows):
        y = 393 + row_index * 50
        values = _summary_values(page, row)
        if row_index % 2:
            draw.rounded_rectangle((80, y - 7, 1620, y + 34), radius=7, fill=(35, 64, 96, 58))
        for value, (label, width), x in zip(values, columns, x_positions, strict=True):
            colour = _data_colour(value) if label == "DATA" else _TEXT
            _text(draw, (x, y), value, width=width - 10, size=16, min_size=10, fill=colour, bold=label == "SLOT")

    _text(draw, (68, 842), f"{section_label.title()} • all linked governors", width=900, size=17, fill=_MUTED)
    refreshed = payload.refreshed_at_utc.astimezone(UTC)
    _text(draw, (1388, 842), f"Refreshed {refreshed:%H:%M UTC}", width=245, size=16, min_size=12, fill=_MUTED)
    return _encode(canvas, f"me_account_summary_{payload.discord_user_id}.png")
