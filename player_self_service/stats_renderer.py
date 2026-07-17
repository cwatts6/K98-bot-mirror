"""Deterministic 1702x924 renderer for private personal period performance."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from core import visual_text
from player_self_service.stats_models import (
    PersonalStatsPayload,
    StatsMetricSummary,
    StatsMode,
)

WIDTH = 1702
HEIGHT = 924
_BACKGROUND = Path(__file__).resolve().parent.parent / "assets" / "me" / "cards" / "me_stats.png"
_TEXT = (245, 248, 255, 255)
_MUTED = (175, 190, 210, 255)
_BLUE = (91, 178, 255, 255)
_GOLD = (242, 195, 98, 255)
_GREEN = (106, 225, 170, 255)
_AMBER = (255, 190, 92, 255)
_RED = (255, 120, 120, 255)
_PANEL = (3, 11, 27, 210)
_SERIES = ((88, 190, 255, 255), (250, 188, 80, 255), (126, 225, 164, 255))


@dataclass(frozen=True, slots=True)
class RenderedStatsCard:
    filename: str
    image_bytes: bytes
    width: int = WIDTH
    height: int = HEIGHT


def _clean(value: object, *, missing: str = "—") -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return text or missing


def _font_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: object,
    *,
    width: int,
    size: int,
    min_size: int = 12,
    fill: tuple[int, int, int, int] = _TEXT,
    bold: bool = False,
) -> None:
    cleaned = _clean(value)
    font = visual_text.fit_font(
        draw, cleaned, max_width=max(1, width), size=size, min_size=min_size, bold=bold
    )
    fitted = visual_text.fit_text_to_width(
        draw, cleaned, width=max(1, width), base_font=font, bold=bold
    )
    visual_text.draw_text(
        draw, xy, fitted, font=font, fill=fill, bold=bold, embedded_color=True
    )


def _compact(value: int | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    sign = "+" if signed and value > 0 else ""
    magnitude = abs(value)
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if magnitude >= divisor:
            rendered = f"{value / divisor:.2f}".rstrip("0").rstrip(".")
            return f"{sign}{rendered}{suffix}"
    return f"{sign}{value:,}"


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=15, fill=_PANEL, outline=(80, 145, 205, 125), width=2)


def _state_colour(state: str) -> tuple[int, int, int, int]:
    return {
        "READY": _GREEN,
        "PARTIAL": _AMBER,
        "NO DATA": _RED,
        "UNAVAILABLE": _RED,
    }.get(state, _MUTED)


def _paste_avatar(canvas: Image.Image, avatar_bytes: bytes | None) -> None:
    size = 144
    position = (96, 60)
    avatar: Image.Image | None = None
    if avatar_bytes:
        try:
            with Image.open(BytesIO(avatar_bytes)) as source:
                avatar = ImageOps.fit(
                    ImageOps.exif_transpose(source).convert("RGBA"),
                    (size, size),
                    method=Image.Resampling.LANCZOS,
                )
        except Exception:
            avatar = None
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    if avatar is not None:
        try:
            canvas.paste(avatar, position, mask)
        finally:
            avatar.close()
    else:
        fallback = Image.new("RGBA", (size, size), (6, 20, 42, 255))
        try:
            fallback_draw = ImageDraw.Draw(fallback, "RGBA")
            fallback_draw.ellipse((2, 2, size - 3, size - 3), outline=_BLUE, width=4)
            _font_text(
                fallback_draw,
                (24, 49),
                "KD98",
                width=96,
                size=30,
                min_size=24,
                fill=_GOLD,
                bold=True,
            )
            canvas.paste(fallback, position, mask)
        finally:
            fallback.close()
    ImageDraw.Draw(canvas, "RGBA").ellipse(
        (position[0] - 2, position[1] - 2, position[0] + size + 1, position[1] + size + 1),
        outline=(92, 174, 255, 210),
        width=3,
    )
    mask.close()


def _metric_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    metric: StatsMetricSummary,
    *,
    context: str | None = None,
    signed: bool = True,
) -> None:
    _panel(draw, box)
    x0, y0, x1, y1 = box
    _font_text(draw, (x0 + 16, y0 + 12), label.upper(), width=x1 - x0 - 32, size=17, fill=_BLUE, bold=True)
    _font_text(
        draw,
        (x0 + 16, y0 + 39),
        _compact(metric.total, signed=signed),
        width=x1 - x0 - 32,
        size=32,
        min_size=22,
        bold=True,
    )
    average = metric.average_per_reporting_day
    helper = context or (
        "No reporting days"
        if average is None
        else f"Avg {average:+,.1f}/reporting day • {metric.reporting_days}/{metric.expected_days} days"
    )
    _font_text(
        draw,
        (x0 + 16, y1 - 31),
        helper,
        width=x1 - x0 - 32,
        size=14,
        min_size=11,
        fill=_MUTED,
    )


def _marker(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    colour: tuple[int, int, int, int],
    marker_index: int,
) -> None:
    if marker_index % 3 == 0:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=colour, outline=_TEXT)
    elif marker_index % 3 == 1:
        draw.rectangle((x - 4, y - 4, x + 4, y + 4), fill=colour, outline=_TEXT)
    else:
        draw.polygon(((x, y - 5), (x - 5, y + 4), (x + 5, y + 4)), fill=colour)


def _chart_summary(metric: StatsMetricSummary) -> str:
    total = _compact(metric.total, signed=True)
    average = metric.average_per_reporting_day
    average_label = "—" if average is None else f"{average:+,.1f}"
    peak = (
        "no exact peak"
        if metric.peak_date is None
        else f"peak {metric.peak_date:%d %b} {_compact(metric.peak_value, signed=True)}"
    )
    return f"total {total} | avg {average_label}/day | {peak} | {metric.reporting_days}/{metric.expected_days} days"


def _draw_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    series: Iterable[tuple[str, StatsMetricSummary]],
) -> None:
    _panel(draw, box)
    x0, y0, x1, y1 = box
    _font_text(draw, (x0 + 16, y0 + 11), title, width=x1 - x0 - 32, size=18, fill=_BLUE, bold=True)
    series_list = list(series)
    all_points = [point for _, metric in series_list for point in metric.daily]
    chart_left, chart_top = x0 + 50, y0 + 52
    chart_right, chart_bottom = x1 - 22, y1 - 82
    if not all_points:
        _font_text(
            draw,
            (chart_left, chart_top + 32),
            "No valid exact-day points for this period.",
            width=chart_right - chart_left,
            size=17,
            fill=_MUTED,
        )
    else:
        dates = sorted({point.reporting_date for point in all_points})
        values = [point.value for point in all_points]
        low, high = min(0, min(values)), max(0, max(values))
        if low == high:
            low -= 1
            high += 1
        span = high - low

        def x_for(reporting_date: object) -> int:
            if len(dates) == 1:
                return (chart_left + chart_right) // 2
            index = dates.index(reporting_date)
            return int(chart_left + index * (chart_right - chart_left) / (len(dates) - 1))

        def y_for(value: int) -> int:
            return int(chart_bottom - (value - low) * (chart_bottom - chart_top) / span)

        zero_y = y_for(0)
        draw.line((chart_left, zero_y, chart_right, zero_y), fill=(220, 230, 245, 155), width=2)
        _font_text(draw, (x0 + 12, zero_y - 9), "0", width=32, size=12, min_size=10, fill=_MUTED)
        for index, (label, metric) in enumerate(series_list):
            colour = _SERIES[index % len(_SERIES)]
            coords = [(x_for(point.reporting_date), y_for(point.value)) for point in metric.daily]
            if len(coords) > 1:
                draw.line(coords, fill=colour, width=3)
            for x, y in coords:
                _marker(draw, x, y, colour, index)
            legend_x = x0 + 17 + index * max(145, (x1 - x0 - 34) // max(1, len(series_list)))
            _marker(draw, legend_x, y0 + 39, colour, index)
            _font_text(draw, (legend_x + 10, y0 + 29), label, width=155, size=13, min_size=10, fill=_TEXT)
        _font_text(draw, (chart_left, chart_bottom + 7), f"{dates[0]:%d %b}", width=90, size=12, min_size=10, fill=_MUTED)
        _font_text(draw, (chart_right - 90, chart_bottom + 7), f"{dates[-1]:%d %b}", width=90, size=12, min_size=10, fill=_MUTED)
    for index, (label, metric) in enumerate(series_list):
        _font_text(
            draw,
            (x0 + 16, y1 - 61 + index * 17),
            f"{label}: {_chart_summary(metric)}",
            width=x1 - x0 - 32,
            size=12,
            min_size=10,
            fill=_MUTED,
        )


def _header(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    payload: PersonalStatsPayload,
    mode: StatsMode,
    display_name: str,
    avatar_bytes: bytes | None,
) -> None:
    _paste_avatar(canvas, avatar_bytes)
    _font_text(draw, (270, 50), "PERIOD PERFORMANCE", width=730, size=38, min_size=28, bold=True)
    _font_text(draw, (270, 100), display_name, width=730, size=27, min_size=18, fill=_GOLD, bold=True)
    _font_text(draw, (270, 141), payload.scope_label, width=730, size=23, min_size=16, fill=_TEXT)
    _font_text(draw, (1040, 49), payload.state.value, width=555, size=29, min_size=21, fill=_state_colour(payload.state.value), bold=True)
    _font_text(draw, (1040, 88), f"{mode.label} • {payload.period.label}", width=555, size=22, min_size=16, fill=_BLUE, bold=True)
    _font_text(
        draw,
        (1040, 122),
        f"{payload.window.start_date:%d %b %Y} — {payload.window.end_date:%d %b %Y}",
        width=555,
        size=19,
        min_size=14,
    )
    coverage = payload.coverage
    if payload.scope_type.value == "all_linked":
        coverage_text = (
            f"Stats {coverage.stats_reporting_governors}/{coverage.requested_governors} governors • "
            f"{coverage.stats_account_days}/{coverage.expected_account_days} account-days"
        )
    else:
        coverage_text = f"Stats coverage {coverage.stats_reporting_dates}/{coverage.expected_dates} dates"
    _font_text(draw, (1040, 158), coverage_text, width=555, size=16, min_size=12, fill=_MUTED)
    generated = payload.generated_at_utc.astimezone(UTC)
    _font_text(
        draw,
        (1040, 188),
        f"Stats anchor {payload.stats_anchor_date:%d %b %Y} • Generated {generated:%d %b %Y %H:%M:%S UTC}",
        width=555,
        size=13,
        min_size=10,
        fill=_MUTED,
    )


def _overview(draw: ImageDraw.ImageDraw, payload: PersonalStatsPayload) -> None:
    metrics = payload.metrics
    end_date = metrics.period_end_date
    power_context = (
        f"End {_compact(metrics.period_end_power)} • {end_date:%d %b}"
        if metrics.period_end_power is not None and end_date
        else "Period-end Power unavailable"
    )
    troop_context = (
        f"End {_compact(metrics.period_end_troop_power)} • {end_date:%d %b}"
        if metrics.period_end_troop_power is not None and end_date
        else "Period-end Troop Power unavailable"
    )
    _metric_box(draw, (95, 230, 820, 392), "Power change", metrics.power_change, context=power_context)
    _metric_box(draw, (850, 230, 1605, 392), "Troop Power change", metrics.troop_power_change, context=troop_context)
    boxes = (
        (95, 420, 575, 575),
        (610, 420, 1090, 575),
        (1125, 420, 1605, 575),
        (95, 603, 575, 758),
        (610, 603, 1090, 758),
        (1125, 603, 1605, 758),
    )
    for box, label, metric in zip(
        boxes,
        ("RSS gathered", "Helps", "Forts total", "Kill Points", "T4+T5 kills", "Deads"),
        (
            metrics.rss_gathered,
            metrics.helps,
            metrics.forts_total,
            metrics.kill_points,
            metrics.t4_t5_kills,
            metrics.deads,
        ),
        strict=True,
    ):
        _metric_box(draw, box, label, metric)


def _activity(draw: ImageDraw.ImageDraw, payload: PersonalStatsPayload) -> None:
    metrics = payload.metrics
    boxes = tuple(
        (95 + column * 382, 230 + row * 136, 455 + column * 382, 350 + row * 136)
        for row in range(2)
        for column in range(4)
    )
    activity = (
        ("RSS gathered", metrics.rss_gathered),
        ("RSS assisted", metrics.rss_assisted),
        ("Helps", metrics.helps),
        ("Build activity", metrics.build_activity),
        ("Tech donations", metrics.tech_donations),
        ("Forts total", metrics.forts_total),
        ("Forts launched", metrics.forts_launched),
        ("Forts joined", metrics.forts_joined),
    )
    for box, (label, metric) in zip(boxes, activity, strict=True):
        _metric_box(draw, box, label, metric)
    _draw_chart(
        draw,
        (95, 514, 825, 792),
        "RSS DAILY TREND",
        (("Gathered", metrics.rss_gathered), ("Assisted", metrics.rss_assisted)),
    )
    _draw_chart(
        draw,
        (850, 514, 1605, 792),
        "FORT DAILY TREND",
        (
            ("Total", metrics.forts_total),
            ("Launched", metrics.forts_launched),
            ("Joined", metrics.forts_joined),
        ),
    )


def _combat(draw: ImageDraw.ImageDraw, payload: PersonalStatsPayload) -> None:
    metrics = payload.metrics
    boxes = tuple(
        (95 + column * 510, 245 + row * 238, 565 + column * 510, 445 + row * 238)
        for row in range(2)
        for column in range(3)
    )
    combat = (
        ("Kill Points gained", metrics.kill_points),
        ("T4 kills gained", metrics.t4_kills),
        ("T5 kills gained", metrics.t5_kills),
        ("T4+T5 combined", metrics.t4_t5_kills),
        ("Deads gained", metrics.deads),
        ("Healed Troops gained", metrics.healed_troops),
    )
    for box, (label, metric) in zip(boxes, combat, strict=True):
        _metric_box(draw, box, label, metric)


def render_personal_stats_card(
    payload: PersonalStatsPayload,
    *,
    mode: StatsMode,
    display_name: str,
    avatar_bytes: bytes | None = None,
) -> RenderedStatsCard:
    with Image.open(_BACKGROUND) as source:
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"Stats backdrop must be {WIDTH}x{HEIGHT}; got {source.size}")
        if source.mode == "RGBA" and source.getextrema()[3] != (255, 255):
            raise ValueError("Stats backdrop must be fully opaque")
        canvas = source.convert("RGBA")
    try:
        overlay = Image.new("RGBA", canvas.size, (0, 4, 14, 76))
        try:
            composited = Image.alpha_composite(canvas, overlay)
        finally:
            overlay.close()
        canvas.close()
        canvas = composited
        draw = ImageDraw.Draw(canvas, "RGBA")
        _header(canvas, draw, payload, mode, display_name, avatar_bytes)
        if mode is StatsMode.OVERVIEW:
            _overview(draw, payload)
        elif mode is StatsMode.ACTIVITY:
            _activity(draw, payload)
        elif mode is StatsMode.COMBAT:
            _combat(draw, payload)
        else:
            raise ValueError(f"Unsupported stats mode: {mode!r}")
        if payload.duplicate_id_warning:
            _font_text(draw, (95, 802), "Review warning: duplicate linked Governor IDs were deduplicated.", width=1120, size=15, min_size=12, fill=_AMBER, bold=True)
        _font_text(draw, (95, 845), "Private period activity • Missing source rows are not treated as zero", width=1050, size=16, min_size=12, fill=_MUTED)
        refreshed = payload.generated_at_utc.astimezone(UTC)
        _font_text(draw, (1325, 845), f"Generated {refreshed:%d %b %Y %H:%M:%S UTC}", width=280, size=14, min_size=10, fill=_MUTED)
        stream = BytesIO()
        try:
            rgb = canvas.convert("RGB")
            try:
                rgb.save(stream, format="PNG", optimize=True)
            finally:
                rgb.close()
            return RenderedStatsCard(
                filename=f"me_stats_{payload.discord_user_id}.png",
                image_bytes=stream.getvalue(),
            )
        finally:
            stream.close()
    finally:
        canvas.close()
