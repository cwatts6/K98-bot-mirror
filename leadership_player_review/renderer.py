"""Deterministic 1702x924 leadership-specific player-review renderer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from core import visual_contract, visual_text
from leadership_player_review.models import LeadershipPlayerPayload

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
) -> None:
    rendered = _clean(value)
    font = visual_text.fit_font(
        draw, rendered, max_width=max(1, width), size=size, min_size=min_size, bold=bold
    )
    rendered = visual_text.fit_text_to_width(
        draw, rendered, width=max(1, width), base_font=font, bold=bold
    )
    x = xy[0]
    if centre:
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


def _target_state(value: Decimal | None, *, exempt: bool) -> str:
    if exempt:
        return "EXEMPT"
    if value is None:
        return "TARGET NOT RECORDED"
    return "MET" if value >= 100 else "NOT MET"


def _trend_delta(current: int | Decimal | None, previous: int | Decimal | None) -> str:
    if current is None or previous is None:
        return "—"
    return _compact(Decimal(current) - Decimal(previous), signed=True)


def _date(value) -> str:
    return value.strftime("%d %b %Y") if value is not None else "—"


def _utc(value) -> str:
    return visual_contract.format_utc_datetime(value) if value is not None else "—"


def _metric_label(code: str) -> str:
    return {
        "FORTS_TOTAL": "FORTS TOTAL",
        "HELPS": "HELPS",
        "TECH_DONATIONS": "TECH DONATIONS",
        "RSS_GATHERED": "RSS GATHERED",
        "BUILDING_MINUTES": "BUILDING MINUTES",
        "POWER_CHANGE": "POWER CHANGE",
    }.get(code, code.replace("_", " "))


def _current_metric_total(metric) -> Decimal | None:
    """Hide SQL aggregate placeholders when source evidence is unavailable."""
    return metric.current_total if metric.available else None


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
    _text(
        draw,
        (1365, 119),
        payload.page.replace("_", " ").upper(),
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


def _draw_overview(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    boxes = (
        (70, 326, 445, 516),
        (468, 326, 843, 516),
        (866, 326, 1241, 516),
        (1264, 326, 1632, 516),
    )
    selected = (payload.metrics[:3] + (None,))[:3]
    for box, metric in zip(boxes[:3], selected, strict=False):
        _panel(draw, box)
        if metric is None:
            continue
        _text(
            draw,
            (box[0] + 18, box[1] + 15),
            _metric_label(metric.code),
            width=box[2] - box[0] - 36,
            size=20,
            min_size=15,
            fill=_BLUE,
            bold=True,
        )
        _text(
            draw,
            (box[0] + 18, box[1] + 54),
            _compact(_current_metric_total(metric), signed=metric.code == "POWER_CHANGE"),
            width=box[2] - box[0] - 36,
            size=43,
            min_size=27,
            fill=_TEXT if metric.available else _RED,
            bold=True,
        )
        rank = (
            f"#{metric.kingdom_rank} of {metric.cohort_count}"
            if metric.kingdom_rank
            else "Rank unavailable"
        )
        _text(
            draw,
            (box[0] + 18, box[1] + 116),
            f"Avg {_compact(metric.current_average)}/day • {rank}",
            width=box[2] - box[0] - 36,
            size=15,
            min_size=12,
            fill=_MUTED,
        )
        valid_units = max(0, metric.expected_units - metric.missing_units)
        _text(
            draw,
            (box[0] + 18, box[1] + 148),
            f"Previous {_percent(metric.comparison_percent, signed=True)} • coverage {valid_units}/{metric.expected_units}",
            width=box[2] - box[0] - 36,
            size=14,
            min_size=11,
            fill=_MUTED,
        )
    box = boxes[3]
    _panel(draw, box)
    index = payload.activity_index
    _text(
        draw,
        (box[0] + 18, box[1] + 15),
        "ACTIVITY INDEX v1",
        width=box[2] - box[0] - 36,
        size=20,
        min_size=15,
        fill=_BLUE,
        bold=True,
    )
    _text(
        draw,
        (box[0] + 18, box[1] + 54),
        _percent(index.value),
        width=box[2] - box[0] - 36,
        size=43,
        min_size=27,
        fill=_TEXT if index.value is not None else _RED,
        bold=True,
    )
    rank = f"#{index.rank} of {index.cohort_count}" if index.rank else "Unavailable"
    _text(
        draw,
        (box[0] + 18, box[1] + 116),
        rank,
        width=box[2] - box[0] - 36,
        size=16,
        min_size=12,
        fill=_MUTED,
    )
    component_labels = [f"{name} {_percent(value)}" for name, value in index.components]
    _text(
        draw,
        (box[0] + 18, box[1] + 145),
        " • ".join(component_labels[:3]),
        width=box[2] - box[0] - 36,
        size=12,
        min_size=10,
        fill=_MUTED,
    )
    _text(
        draw,
        (box[0] + 18, box[1] + 166),
        " • ".join(component_labels[3:]),
        width=box[2] - box[0] - 36,
        size=12,
        min_size=10,
        fill=_MUTED,
    )

    _panel(draw, (70, 538, 1632, 810))
    _text(
        draw, (92, 554), "LEADERSHIP REVIEW", width=400, size=22, min_size=17, fill=_BLUE, bold=True
    )
    y = 598
    if payload.prompts:
        for prompt in payload.prompts[:2]:
            colour = _GREEN if prompt.startswith("Strength") else _AMBER
            _text(draw, (102, y), prompt, width=1480, size=21, min_size=15, fill=colour)
            y += 66
    else:
        _text(
            draw,
            (102, y),
            "Prompts suppressed for freshness, coverage, tenure, comparison, or cohort safeguards.",
            width=1480,
            size=20,
            min_size=15,
            fill=_MUTED,
        )
        y += 60
    for warning in payload.warnings[:3]:
        _text(draw, (102, y), warning, width=1480, size=17, min_size=13, fill=_AMBER)
        y += 42


def _draw_activity(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    for index, metric in enumerate(payload.metrics[:6]):
        column = index % 3
        row = index // 3
        x0 = 70 + column * 520
        y0 = 326 + row * 235
        box = (x0, y0, x0 + 492, y0 + 210)
        _panel(draw, box)
        _text(
            draw,
            (x0 + 18, y0 + 14),
            _metric_label(metric.code),
            width=456,
            size=20,
            min_size=15,
            fill=_BLUE,
            bold=True,
        )
        _text(
            draw,
            (x0 + 18, y0 + 50),
            _compact(_current_metric_total(metric), signed=metric.code == "POWER_CHANGE"),
            width=270,
            size=40,
            min_size=25,
            fill=_TEXT if metric.available else _RED,
            bold=True,
        )
        _text(
            draw,
            (x0 + 298, y0 + 55),
            f"AVG {_compact(metric.current_average)}/day",
            width=170,
            size=18,
            min_size=14,
            fill=_MUTED,
        )
        rank = (
            f"Current kingdom #{metric.kingdom_rank} of {metric.cohort_count}"
            if metric.kingdom_rank
            else "Current kingdom rank unavailable"
        )
        _text(
            draw,
            (x0 + 18, y0 + 108),
            rank,
            width=450,
            size=17,
            min_size=13,
            fill=_GREEN if metric.kingdom_rank else _MUTED,
        )
        _text(
            draw,
            (x0 + 18, y0 + 140),
            f"Top {_percent(metric.top_percent)} • previous {_percent(metric.comparison_percent, signed=True)}",
            width=450,
            size=16,
            min_size=12,
            fill=_MUTED,
        )
        reset = f" • {metric.reset_count} reset(s) excluded" if metric.reset_count else ""
        valid_units = max(0, metric.expected_units - metric.missing_units)
        _text(
            draw,
            (x0 + 18, y0 + 172),
            f"Coverage {valid_units}/{metric.expected_units}{reset}",
            width=450,
            size=14,
            min_size=11,
            fill=_AMBER if metric.missing_units or metric.reset_count else _MUTED,
        )


def _draw_kvk(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    rows = payload.kvk_rows[:3]
    if not rows:
        _panel(draw, (70, 326, 1632, 810))
        _text(
            draw,
            (100, 500),
            "NO DATA · No ended, finalized KVK row is available.",
            width=1500,
            size=30,
            min_size=22,
            fill=_RED,
            centre=True,
        )
        return
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
    for index, row in enumerate(rows):
        y0 = 326 + index * 160
        _panel(draw, (70, y0, 1632, y0 + 138))
        _text(
            draw,
            (92, y0 + 13),
            f"KVK {row.kvk_no} · {row.kvk_name or 'Name not recorded'}",
            width=420,
            size=22,
            min_size=15,
            fill=_BLUE,
            bold=True,
        )
        _text(
            draw,
            (520, y0 + 17),
            f"Rank {_clean(row.kvk_rank)}  •  T4+T5 {_compact(row.t4_t5_kills)} ({_percent(row.kill_target_percent)} · {_target_state(row.kill_target_percent, exempt=row.exempt)})  •  KP {_compact(row.kill_points)}",
            width=520,
            size=18,
            min_size=10,
        )
        _text(
            draw,
            (1060, y0 + 17),
            f"Final {_utc(row.final_data_at_utc)} · {row.final_output_state or 'STATE NOT RECORDED'}",
            width=530,
            size=15,
            min_size=10,
            fill=_MUTED,
        )
        _text(
            draw,
            (92, y0 + 55),
            f"Deads {_compact(row.deads)} ({_percent(row.dead_target_percent)} · {_target_state(row.dead_target_percent, exempt=row.exempt)})  •  Healed {_compact(row.healed)} rank {_clean(row.healed_rank)}  •  KP Loss {_compact(row.kp_loss)}",
            width=900,
            size=18,
            min_size=11,
        )
        _text(
            draw,
            (1030, y0 + 55),
            f"Tanking {_percent(row.tanking_score)} · rank {_clean(row.tanking_rank)} (higher is better)",
            width=560,
            size=17,
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
            (92, y0 + 94),
            f"Acclaim {_compact(row.acclaim)} · best {_compact(best_acclaim)} · {_percent(acclaim_pct)} of personal completed-KVK best  •  DKP {_compact(row.dkp)} ({_percent(row.dkp_target_percent)} · {_target_state(row.dkp_target_percent, exempt=row.exempt)})  •  Pre-KVK {_compact(row.prekvk_points)} rank {_clean(row.prekvk_rank)}  •  Honor {_compact(row.honor_points)} rank {_clean(row.honor_rank)}",
            width=1490,
            size=16,
            min_size=9,
            fill=_MUTED,
        )
    if len(rows) >= 2:
        latest, previous = rows[0], rows[1]
        comparison_rows = rows[1:3]

        def average(attribute: str) -> Decimal | None:
            values = [
                Decimal(value)
                for row in comparison_rows
                if (value := getattr(row, attribute)) is not None
            ]
            return sum(values) / len(values) if values else None

        _text(
            draw,
            (92, 788),
            f"Latest vs previous · Rank {_trend_delta(latest.kvk_rank, previous.kvk_rank)} · KP {_trend_delta(latest.kill_points, previous.kill_points)} · Tanking {_trend_delta(latest.tanking_score, previous.tanking_score)} · Acclaim {_trend_delta(latest.acclaim, previous.acclaim)}",
            width=1495,
            size=13,
            min_size=9,
            fill=_BLUE,
        )
        _text(
            draw,
            (92, 811),
            f"Previous-two averages · Rank {_compact(average('kvk_rank'))} · KP {_compact(average('kill_points'))} · Tanking {_percent(average('tanking_score'))} · Acclaim {_compact(average('acclaim'))}",
            width=1495,
            size=13,
            min_size=9,
            fill=_MUTED,
        )


def _draw_record(draw: ImageDraw.ImageDraw, payload: LeadershipPlayerPayload) -> None:
    page_size = 10
    offset = max(0, payload.record_page) * page_size
    total_pages = max(
        1,
        (
            max(len(payload.linked_governors), len(payload.aliases), len(payload.alliance_episodes))
            + page_size
            - 1
        )
        // page_size,
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
    for row in payload.aliases[offset : offset + page_size]:
        _text(
            draw,
            (622, y),
            f"{row.governor_id} · {row.governor_name} · first {_date(row.first_seen.date() if row.first_seen else None)} · last {_date(row.last_seen.date() if row.last_seen else None)} · {row.seen_scan_count} scans",
            width=445,
            size=15,
            min_size=11,
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
        "ALLIANCE EPISODES",
        width=465,
        size=21,
        min_size=16,
        fill=_BLUE,
        bold=True,
    )
    y = 384
    for row in payload.alliance_episodes[offset : offset + page_size]:
        _text(
            draw,
            (1147, y),
            f"{row.governor_id} · {row.alliance} · {_date(row.first_observed)}–{_date(row.last_observed)} · {row.observed_scans} scans",
            width=455,
            size=15,
            min_size=11,
            fill=_BLUE if row.current else _TEXT,
        )
        y += 38
    if not payload.alliance_episodes:
        _text(
            draw,
            (1147, y),
            "No alliance episodes in the selected history depth.",
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
    _draw_context(draw, payload)
    if payload.page == "activity":
        _draw_activity(draw, payload)
    elif payload.page == "kvk":
        _draw_kvk(draw, payload)
    elif payload.page == "record":
        _draw_record(draw, payload)
    else:
        _draw_overview(draw, payload)
    _text(
        draw,
        (72, 842),
        f"Source freshness {_utc(payload.header.latest_governor_scan_at_utc)}",
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
