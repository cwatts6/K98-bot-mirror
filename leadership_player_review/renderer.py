"""Deterministic 1702x924 leadership-specific player-review renderer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from core import visual_contract, visual_text
from leadership_player_review.models import ActivityMetric, LeadershipPlayerPayload
from leadership_player_review.record_paging import (
    RECORD_PAGE_SIZE,
    alias_pages,
    alliance_pages,
    record_page_count,
)

WIDTH = 1702
HEIGHT = 924
_BACKGROUND = (
    Path(__file__).resolve().parent.parent / "assets" / "stats" / "cards" / "stats_player.png"
)
_TEXT = visual_contract.TEXT
_MUTED = visual_contract.MUTED
_BLUE = visual_contract.BLUE
_GREEN = visual_contract.GREEN
_AMBER = visual_contract.AMBER
_RED = visual_contract.RED


@dataclass(frozen=True, slots=True)
class RenderedLeadershipPlayerCard:
    filename: str
    image_bytes: bytes
    width: int = WIDTH
    height: int = HEIGHT


def _clean(value: object, *, missing: str = "—") -> str:
    if value is None:
        return missing
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text or missing


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: object,
    *,
    width: int,
    size: int,
    min_size: int = 12,
    fill=_TEXT,
    bold: bool = False,
    centre: bool = False,
    right_align: bool = False,
) -> None:
    rendered = _clean(value)
    font = visual_text.fit_font(
        draw, rendered, max_width=max(1, width), size=size, min_size=min_size, bold=bold
    )
    rendered = visual_text.fit_text_to_width(
        draw, rendered, width=max(1, width), base_font=font, bold=bold
    )
    x = xy[0]
    if right_align:
        x += width - visual_text.text_width(draw, rendered, font=font, bold=bold)
    elif centre:
        x += (width - visual_text.text_width(draw, rendered, font=font, bold=bold)) // 2
    visual_text.draw_text(
        draw, (x + 2, xy[1] + 2), rendered, font=font, fill=(0, 0, 0, 190), bold=bold
    )
    visual_text.draw_text(
        draw, (x, xy[1]), rendered, font=font, fill=fill, bold=bold, embedded_color=True
    )


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    visual_contract.draw_panel(draw, box, fill=(3, 11, 27, 205))


def _compact(value: int | float | Decimal | None, *, signed: bool = False) -> str:
    return visual_contract.format_compact_number(value, signed=signed)


def _percent(value: Decimal | float | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{float(value):.1f}%"


def _date(value) -> str:
    return value.strftime("%d %b %Y") if value is not None else "—"


def _utc(value) -> str:
    return visual_contract.format_utc_datetime(value) if value is not None else "—"


def _short_date(value) -> str:
    return value.strftime("%d %b %y") if value is not None else "—"


def _metric_label(code: str) -> str:
    return {
        "FORTS_TOTAL": "FORTS TOTAL",
        "HELPS": "HELPS",
        "TECH_DONATIONS": "TECH DONATIONS",
        "RSS_GATHERED": "RSS GATHERED",
        "BUILDING_MINUTES": "BUILDING MINUTES",
        "POWER_CHANGE": "POWER CHANGE",
    }.get(code, code.replace("_", " "))


def current_metric_total(metric: ActivityMetric) -> Decimal | None:
    """Return an observed total, including genuine zeroes from partial coverage."""
    if metric.current_valid_days <= 0:
        return None
    return metric.current_total


def _draw_header(
    draw: ImageDraw.ImageDraw, canvas: Image.Image, payload: LeadershipPlayerPayload
) -> None:
    header = payload.header
    visual_contract.paste_core_avatar(canvas, None, fallback_text="KD98")
    _panel(draw, (260, 38, 1328, 210))
    _text(
        draw,
        (286, 50),
        header.governor_name or f"Governor {header.governor_id}",
        width=730,
        size=44,
        min_size=25,
        bold=True,
    )
    _text(
        draw,
        (286, 103),
        f"Governor ID {header.governor_id}  •  Alliance {_clean(header.current_alliance, missing='Unallied')}",
        width=900,
        size=22,
        min_size=16,
        fill=_BLUE,
    )
    _text(
        draw,
        (286, 139),
        f"Power {_compact(header.current_power)}  •  City Hall {_clean(header.city_hall)}  •  Governor scan {_utc(header.latest_governor_scan_at_utc)}",
        width=970,
        size=18,
        min_size=14,
        fill=_MUTED,
    )
    _text(
        draw,
        (286, 171),
        f"{payload.period_days} days  •  {_date(header.current_start_date)}–{_date(header.current_end_date)}  •  Previous {_date(header.previous_start_date)}–{_date(header.previous_end_date)}",
        width=980,
        size=17,
        min_size=13,
        fill=_MUTED,
    )
    visual_contract.draw_state_pill(draw, payload.freshness)
    page_title = {
        "overview": "OVERVIEW",
        "activity": "KINGDOM ACTIVITY",
        "kvk": "KVK PERFORMANCE",
        "record": "PLAYER RECORD",
    }[payload.page]
    _text(
        draw,
        (1365, 119),
        page_title,
        width=245,
        size=18,
        min_size=14,
        fill=_BLUE,
        bold=True,
        centre=True,
    )
    _text(
        draw,
        (1365, 149),
        f"Period {payload.period_days}d",
        width=245,
        size=16,
        min_size=13,
        fill=_MUTED,
        centre=True,
    )
    current = payload.current_presence
    presence = "No scan presence"
    if current:
        presence = f"Presence {current.present_scans}/{current.complete_scans} scans • {current.present_scanned_days}/{current.scanned_days} days"
    _text(draw, (1365, 176), presence, width=245, size=13, min_size=11, fill=_MUTED, centre=True)


def _draw_context(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    header = payload.header
    _panel(draw, (70, 226, 1632, 304))
    location = (
        f"{header.location_x}:{header.location_y}"
        if header.location_x is not None and header.location_y is not None
        else "—"
    )
    shield = "Not reported"
    if header.shield_ends_at_utc is not None:
        status = "active" if header.shield_ends_at_utc > header.effective_now_utc else "expired"
        shield = f"Reported {status} · ends {_utc(header.shield_ends_at_utc)}"
    coverage = " • ".join(
        f"{item.source_code.replace('_', ' ').title()} {item.valid_units}/{item.expected_units}"
        for item in payload.coverage
        if item.window == "CURRENT"
    )
    _text(
        draw,
        (92, 239),
        f"Latest X:Y {location}  •  Location updated {_utc(header.location_updated_at_utc)}  •  Shield {shield}",
        width=1500,
        size=17,
        min_size=13,
        fill=_BLUE,
    )
    _text(
        draw,
        (92, 271),
        coverage or "Valid source observations: NO DATA",
        width=1500,
        size=15,
        min_size=12,
        fill=_MUTED,
    )


def _presence_percentage(payload: LeadershipPlayerPayload) -> str:
    current = payload.current_presence
    if current is None or current.complete_scans <= 0:
        return "—"
    rounded = (current.present_scans * 100 + current.complete_scans // 2) // current.complete_scans
    return f"{rounded}%"


def _draw_overview(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    index_box = (70, 226, 832, 430)
    presence_box = (854, 226, 1632, 430)
    _panel(draw, index_box)
    _panel(draw, presence_box)

    index = payload.activity_index
    _text(
        draw, (94, 244), "ACTIVITY INDEX v1", width=700, size=25, min_size=18, fill=_BLUE, bold=True
    )
    _text(
        draw,
        (94, 286),
        _percent(index.value),
        width=300,
        size=58,
        min_size=38,
        fill=_TEXT if index.value is not None else _RED,
        bold=True,
    )
    rank = f"Kingdom #{index.rank} of {index.cohort_count}" if index.rank else "Rank unavailable"
    _text(draw, (400, 301), rank, width=390, size=21, min_size=15, fill=_GREEN)
    component_labels = [f"{name} {_percent(value)}" for name, value in index.components]
    _text(
        draw,
        (94, 366),
        "  •  ".join(component_labels[:3]),
        width=700,
        size=15,
        min_size=11,
        fill=_MUTED,
    )
    _text(
        draw,
        (94, 394),
        "  •  ".join(component_labels[3:]),
        width=700,
        size=15,
        min_size=11,
        fill=_MUTED,
    )

    current = payload.current_presence
    scan_ratio = (
        f"{current.present_scans} / {current.complete_scans} scans" if current else "NO DATA"
    )
    scanned_days = (
        f"{current.present_scanned_days}/{current.scanned_days} scanned days"
        if current
        else "Scanned days unavailable"
    )
    _text(draw, (878, 244), "PRESENCE", width=325, size=25, min_size=18, fill=_BLUE, bold=True)
    _text(draw, (878, 284), scan_ratio, width=425, size=39, min_size=25, bold=True)
    _text(
        draw,
        (1320, 276),
        _presence_percentage(payload),
        width=270,
        size=54,
        min_size=34,
        fill=_GREEN if current and current.present_scans else _RED,
        bold=True,
        right_align=True,
    )
    _text(draw, (878, 338), scanned_days, width=420, size=16, min_size=12, fill=_MUTED)
    last_active = payload.last_active
    last_active_text = (
        f"Last Active {_date(last_active.last_active_date)}  •  {last_active.activity_state}"
        if last_active and last_active.last_active_date
        else "Last Active Not recorded"
    )
    state_colour = (
        _GREEN
        if last_active and last_active.activity_state == "ACTIVE"
        else _AMBER if last_active and last_active.activity_state == "INACTIVE" else _MUTED
    )
    _text(
        draw,
        (878, 370),
        last_active_text,
        width=710,
        size=20,
        min_size=14,
        fill=state_colour,
        bold=True,
    )
    coverage = "  •  ".join(
        f"{item.source_code.replace('_', ' ').title()} {item.valid_units}/{item.expected_units}"
        for item in payload.coverage
        if item.window == "CURRENT"
    )
    _text(
        draw,
        (878, 402),
        coverage or "Valid source observations: NO DATA",
        width=710,
        size=12,
        min_size=9,
        fill=_MUTED,
    )

    header = payload.header
    location = (
        f"{header.location_x}:{header.location_y}"
        if header.location_x is not None and header.location_y is not None
        else "Not reported"
    )
    shield = "Not reported"
    if header.shield_ends_at_utc is not None:
        status = "ACTIVE" if header.shield_ends_at_utc > header.effective_now_utc else "EXPIRED"
        shield = f"{status} • ends {_utc(header.shield_ends_at_utc)}"
    location_boxes = (
        ((70, 452, 570, 615), "LATEST X:Y", location),
        ((592, 452, 1092, 615), "LOCATION UPDATED UTC", _utc(header.location_updated_at_utc)),
        ((1114, 452, 1632, 615), "SHIELD STATUS", shield),
    )
    for box, label, value in location_boxes:
        _panel(draw, box)
        _text(
            draw,
            (box[0] + 22, box[1] + 20),
            label,
            width=box[2] - box[0] - 44,
            size=19,
            min_size=14,
            fill=_BLUE,
            bold=True,
        )
        _text(
            draw,
            (box[0] + 22, box[1] + 65),
            value,
            width=box[2] - box[0] - 44,
            size=33,
            min_size=19,
            bold=True,
        )

    _panel(draw, (70, 637, 1632, 810))
    _text(
        draw, (92, 653), "LEADERSHIP REVIEW", width=400, size=22, min_size=17, fill=_BLUE, bold=True
    )
    y = 697
    if payload.prompts:
        for prompt in payload.prompts[:2]:
            colour = _GREEN if prompt.startswith("Strength") else _AMBER
            _text(draw, (102, y), prompt, width=1480, size=19, min_size=14, fill=colour)
            y += 45
    else:
        _text(
            draw,
            (102, y),
            "Prompts suppressed for freshness, coverage, tenure, comparison, or cohort safeguards.",
            width=1480,
            size=18,
            min_size=14,
            fill=_MUTED,
        )
        y += 42
    for warning in payload.warnings[:2]:
        _text(draw, (102, y), warning, width=1480, size=16, min_size=12, fill=_AMBER)
        y += 34


def _draw_activity(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    boxes = (
        (70, 226, 570, 507),
        (592, 226, 1092, 507),
        (1114, 226, 1632, 507),
        (70, 529, 570, 810),
        (592, 529, 1092, 810),
        (1114, 529, 1632, 810),
    )
    for box, metric in zip(boxes, payload.metrics[:6], strict=False):
        display_total = current_metric_total(metric)
        x0, y0, x1, _y1 = box
        width = x1 - x0
        _panel(draw, box)
        _text(
            draw,
            (x0 + 22, y0 + 18),
            _metric_label(metric.code),
            width=width - 44,
            size=23,
            min_size=16,
            fill=_BLUE,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 62),
            _compact(display_total, signed=metric.code == "POWER_CHANGE"),
            width=width - 44,
            size=50,
            min_size=30,
            fill=_TEXT if display_total is not None else _RED,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 127),
            f"Average {_compact(metric.current_average)}/valid day",
            width=width - 44,
            size=19,
            min_size=14,
            fill=_MUTED,
        )
        rank = (
            f"Kingdom #{metric.kingdom_rank} of {metric.cohort_count}"
            if metric.kingdom_rank
            else "Kingdom rank unavailable"
        )
        _text(
            draw,
            (x0 + 22, y0 + 164),
            rank,
            width=width - 44,
            size=20,
            min_size=14,
            fill=_GREEN if metric.kingdom_rank else _MUTED,
            bold=bool(metric.kingdom_rank),
        )
        _text(
            draw,
            (x0 + 22, y0 + 202),
            f"Top {_percent(metric.top_percent)}  •  previous {_percent(metric.comparison_percent, signed=True)}",
            width=width - 44,
            size=17,
            min_size=12,
            fill=_MUTED,
        )
        reset = f"  •  {metric.reset_count} reset(s) excluded" if metric.reset_count else ""
        valid_units = max(0, metric.expected_units - metric.missing_units)
        _text(
            draw,
            (x0 + 22, y0 + 239),
            f"Coverage {valid_units}/{metric.expected_units}{reset}",
            width=width - 44,
            size=15,
            min_size=11,
            fill=_AMBER if metric.missing_units or metric.reset_count else _MUTED,
        )


def _kvk_target_context(value: Decimal | None, *, exempt: bool) -> str:
    target = f"{_percent(value)} target" if value is not None else "Target % not recorded"
    return f"{target}  •  EXEMPT" if exempt else target


def _draw_kvk(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    rows = payload.kvk_rows[:3]
    _text(
        draw,
        (1365, 203),
        f"Valid {len(rows)}/3 finalized KVKs",
        width=245,
        size=15,
        min_size=12,
        fill=_MUTED,
        centre=True,
    )
    boxes = ((70, 226, 570, 810), (592, 226, 1092, 810), (1114, 226, 1632, 810))
    for index, box in enumerate(boxes):
        _panel(draw, box)
        x0, y0, x1, _y1 = box
        width = x1 - x0 - 44
        if index >= len(rows):
            _text(
                draw,
                (x0 + 22, y0 + 258),
                "NO ADDITIONAL ELIGIBLE FINALIZED KVK",
                width=width,
                size=22,
                min_size=15,
                fill=_MUTED,
                centre=True,
                bold=True,
            )
            continue
        row = rows[index]
        _text(
            draw,
            (x0 + 22, y0 + 18),
            f"KVK {row.kvk_no}",
            width=width,
            size=29,
            min_size=20,
            fill=_BLUE,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 57),
            row.kvk_name or "Name not recorded",
            width=width,
            size=18,
            min_size=13,
            fill=_MUTED,
        )
        _text(
            draw,
            (x0 + 22, y0 + 91),
            f"KVK rank {_clean(row.kvk_rank)}",
            width=width,
            size=22,
            min_size=15,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 130),
            f"T4+T5  {_compact(row.t4_t5_kills)}",
            width=width,
            size=20,
            min_size=14,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 160),
            _kvk_target_context(row.kill_target_percent, exempt=row.exempt),
            width=width,
            size=15,
            min_size=11,
            fill=_MUTED,
        )
        _text(
            draw,
            (x0 + 22, y0 + 192),
            f"KP  {_compact(row.kill_points)}",
            width=width,
            size=20,
            min_size=14,
        )
        _text(
            draw,
            (x0 + 22, y0 + 230),
            f"Deads  {_compact(row.deads)}",
            width=width,
            size=20,
            min_size=14,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 260),
            _kvk_target_context(row.dead_target_percent, exempt=row.exempt),
            width=width,
            size=15,
            min_size=11,
            fill=_MUTED,
        )
        _text(
            draw,
            (x0 + 22, y0 + 294),
            f"Healed  {_compact(row.healed)}  •  rank {_clean(row.healed_rank)}",
            width=width,
            size=18,
            min_size=12,
        )
        _text(
            draw,
            (x0 + 22, y0 + 328),
            f"KP Loss  {_compact(row.kp_loss)}",
            width=width,
            size=18,
            min_size=12,
        )
        _text(
            draw,
            (x0 + 22, y0 + 362),
            f"Tanking  {_percent(row.tanking_score)}  •  rank {_clean(row.tanking_rank)}",
            width=width,
            size=18,
            min_size=12,
            fill=_GREEN if row.tanking_score is not None else _RED,
        )
        best_acclaim = row.personal_completed_kvk_best_acclaim
        acclaim_pct = (
            Decimal(row.acclaim) * 100 / Decimal(best_acclaim)
            if row.acclaim is not None and best_acclaim is not None and best_acclaim > 0
            else None
        )
        _text(
            draw,
            (x0 + 22, y0 + 404),
            f"Acclaim  {_compact(row.acclaim)}",
            width=width,
            size=18,
            min_size=12,
            bold=True,
        )
        _text(
            draw,
            (x0 + 22, y0 + 434),
            f"Best {_compact(best_acclaim)}  •  {_percent(acclaim_pct)} of best",
            width=width,
            size=15,
            min_size=11,
            fill=_MUTED,
        )
        _text(
            draw,
            (x0 + 22, y0 + 470),
            f"DKP  {_compact(row.dkp)}  •  {_percent(row.dkp_target_percent)}",
            width=width,
            size=18,
            min_size=12,
        )
        _text(
            draw,
            (x0 + 22, y0 + 506),
            f"Pre-KVK  {_compact(row.prekvk_points)}  •  rank {_clean(row.prekvk_rank)}",
            width=width,
            size=17,
            min_size=11,
        )
        _text(
            draw,
            (x0 + 22, y0 + 540),
            f"Honor  {_compact(row.honor_points)}  •  rank {_clean(row.honor_rank)}",
            width=width,
            size=17,
            min_size=11,
        )


def _draw_record(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    page_size = RECORD_PAGE_SIZE
    page_index = max(0, payload.record_page)
    offset = page_index * page_size
    alias_page_rows = alias_pages(payload.aliases)
    alliance_page_rows = alliance_pages(payload.alliance_episodes)
    total_pages = record_page_count(
        linked_count=len(payload.linked_governors),
        aliases=payload.aliases,
        episodes=payload.alliance_episodes,
    )
    _text(
        draw,
        (1365, 203),
        f"Record page {min(payload.record_page + 1, total_pages)}/{total_pages}",
        width=245,
        size=15,
        min_size=12,
        fill=_MUTED,
        centre=True,
    )
    _panel(draw, (70, 326, 570, 810))
    _text(
        draw,
        (92, 342),
        "ACTIVE LINKED GOVERNORS",
        width=455,
        size=21,
        min_size=16,
        fill=_BLUE,
        bold=True,
    )
    y = 384
    if payload.linked_governors:
        for row in payload.linked_governors[offset : offset + page_size]:
            suffix = " · CURRENT" if row.current else ""
            _text(
                draw,
                (100, y),
                f"{row.governor_name} · {row.governor_id}{suffix}",
                width=430,
                size=17,
                min_size=13,
                fill=_BLUE if row.current else _TEXT,
            )
            y += 37
    else:
        _text(
            draw,
            (100, y),
            "No active linked governors were found for this Governor ID.",
            width=430,
            size=17,
            min_size=13,
            fill=_MUTED,
        )

    _panel(draw, (592, 326, 1095, 810))
    _text(
        draw,
        (614, 342),
        "ALIASES BY GOVERNOR ID",
        width=455,
        size=21,
        min_size=16,
        fill=_BLUE,
        bold=True,
    )
    y = 384
    visible_alias_rows = alias_page_rows[page_index] if page_index < len(alias_page_rows) else ()
    for display_row in visible_alias_rows:
        row = display_row.alias
        if row is None:
            _text(
                draw,
                (622, y),
                f"Governor ID {display_row.governor_id}",
                width=445,
                size=16,
                min_size=13,
                fill=_BLUE,
                bold=True,
            )
        else:
            _text(draw, (630, y), row.governor_name, width=124, size=14, min_size=11)
            _text(
                draw,
                (756, y),
                f"1st {_short_date(row.first_seen.date() if row.first_seen else None)}",
                width=105,
                size=13,
                min_size=10,
                fill=_MUTED,
            )
            _text(
                draw,
                (863, y),
                f"last {_short_date(row.last_seen.date() if row.last_seen else None)}",
                width=111,
                size=13,
                min_size=10,
                fill=_MUTED,
            )
            _text(
                draw,
                (976, y),
                f"{row.seen_scan_count} scans",
                width=97,
                size=13,
                min_size=10,
                right_align=True,
            )
        y += 38
    if not payload.aliases:
        _text(
            draw,
            (622, y),
            "No observed alias history.",
            width=445,
            size=17,
            min_size=13,
            fill=_MUTED,
        )

    _panel(draw, (1117, 326, 1632, 810))
    _text(
        draw,
        (1139, 342),
        "ALLIANCES",
        width=465,
        size=21,
        min_size=16,
        fill=_BLUE,
        bold=True,
    )
    y = 384
    visible_alliance_rows = (
        alliance_page_rows[page_index] if page_index < len(alliance_page_rows) else ()
    )
    for display_row in visible_alliance_rows:
        row = display_row.episode
        if row is None:
            _text(
                draw,
                (1147, y),
                f"Governor ID {display_row.governor_id}",
                width=455,
                size=16,
                min_size=13,
                fill=_BLUE,
                bold=True,
            )
        else:
            current = " • CURRENT" if row.current else ""
            _text(
                draw,
                (1155, y),
                f"{row.alliance}{current}",
                width=165,
                size=14,
                min_size=11,
                fill=_BLUE if row.current else _TEXT,
            )
            _text(
                draw,
                (1322, y),
                f"{_short_date(row.first_observed)}–{_short_date(row.last_observed)}",
                width=164,
                size=13,
                min_size=10,
                fill=_MUTED,
            )
            _text(
                draw,
                (1488, y),
                f"{row.observed_scans} scans",
                width=112,
                size=13,
                min_size=10,
                right_align=True,
            )
        y += 38
    if not payload.alliance_episodes:
        _text(
            draw,
            (1147, y),
            "No observed alliance history.",
            width=455,
            size=17,
            min_size=13,
            fill=_MUTED,
        )


def render_leadership_player(payload: LeadershipPlayerPayload) -> RenderedLeadershipPlayerCard:
    with Image.open(_BACKGROUND) as source:
        canvas = source.convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", canvas.size, (1, 4, 13, 60)))
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_header(draw, canvas, payload)
    if payload.page == "activity":
        _draw_activity(draw, payload)
    elif payload.page == "kvk":
        _draw_kvk(draw, payload)
    elif payload.page == "record":
        _draw_context(draw, payload)
        _draw_record(draw, payload)
    else:
        _draw_overview(draw, payload)
    _text(
        draw,
        (72, 842),
        f"Data refreshed {_utc(payload.header.latest_governor_scan_at_utc)}",
        width=720,
        size=15,
        min_size=12,
        fill=_MUTED,
    )
    _text(
        draw,
        (915, 842),
        f"Generated {_utc(payload.generated_at_utc)}",
        width=715,
        size=15,
        min_size=12,
        fill=_BLUE,
        right_align=True,
    )
    _text(
        draw,
        (72, 876),
        "Private leadership review · no public share or export · times UTC",
        width=1560,
        size=14,
        min_size=11,
        fill=_MUTED,
        centre=True,
    )
    buffer = BytesIO()
    try:
        canvas.convert("RGB").save(buffer, format="PNG", optimize=True)
        return RenderedLeadershipPlayerCard(
            filename=f"leadership_player_{payload.header.governor_id}_{payload.page}_{payload.period_days}d.png",
            image_bytes=buffer.getvalue(),
        )
    finally:
        buffer.close()
        canvas.close()
