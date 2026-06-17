from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from kvk.models.kvk_history_payload import (
    KvkHistoryPayload,
    KvkHistoryRow,
    KvkHistorySummaryMetric,
    KvkHistoryTrend,
    RenderedKvkHistoryCard,
)
from kvk.rendering.kvk_stats_card_renderer import (
    BLUE,
    GOLD,
    GREEN,
    HEIGHT,
    MUTED,
    PURPLE,
    RED,
    TEXT,
    WIDTH,
    _compact,
    _draw_avatar,
    _draw_text,
    _fit_font,
    _font,
    _load_background,
    _pct,
)

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets" / "kvk" / "cards"
HISTORY_LAST3_BACKGROUND = ASSET_DIR / "history_card1.PNG"
HISTORY_SUMMARY_BACKGROUND = ASSET_DIR / "history_card2.PNG"
HISTORY_TRENDS_BACKGROUND = ASSET_DIR / "history_card3.PNG"
DEFAULT_BACKGROUND = ASSET_DIR / "Default_card.jpg"
TIDES_BACKGROUND = ASSET_DIR / "Tides_Stats_Card.png"


def _background_path(primary: Path) -> Path | None:
    for path in (primary, DEFAULT_BACKGROUND, TIDES_BACKGROUND):
        if path.exists():
            return path
    return None


def _card_canvas(path: Path) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    background = _load_background(path)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    odraw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=22, fill=(0, 0, 0, 78))
    odraw.rectangle((0, 0, WIDTH, 166), fill=(0, 0, 0, 104))
    odraw.rectangle((0, 182, WIDTH, HEIGHT), fill=(0, 0, 0, 96))
    canvas = Image.alpha_composite(background, overlay)
    return canvas, ImageDraw.Draw(canvas, "RGBA")


def _save(canvas: Image.Image, filename: str) -> RenderedKvkHistoryCard:
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedKvkHistoryCard(filename=filename, image_bytes=buf)


def _value(value: int | float | None, *, missing: str = "N/A") -> str:
    if value is None:
        return missing
    return _compact(value)


def _pct_value(value: float | None) -> str:
    return "N/A" if value is None else _pct(value)


def _rank(value: int | None) -> str:
    return "N/A" if value is None else f"#{value}"


def _last3_display_rows(payload: KvkHistoryPayload) -> tuple[KvkHistoryRow, ...]:
    return tuple(sorted(payload.last3_rows, key=lambda item: item.kvk_no, reverse=True))


def _average(values: list[int | float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _trend_label(payload: KvkHistoryPayload) -> tuple[str, tuple[int, int, int]]:
    trend = payload.trends.get("last3_kills") or payload.trends.get("kills")
    direction = getattr(trend, "direction", "missing")
    if direction == "up":
        return "Up", GREEN
    if direction == "down":
        return "Down", RED
    if direction == "flat":
        return "Flat", GOLD
    if direction == "insufficient":
        return "New", BLUE
    return "N/A", MUTED


def _trend_direction(payload: KvkHistoryPayload) -> str:
    trend = payload.trends.get("last3_kills") or payload.trends.get("kills")
    return getattr(trend, "direction", "missing")


def _trend_text(direction: str) -> str:
    if direction == "up":
        return "Improved"
    if direction == "down":
        return "Declined"
    if direction == "flat":
        return "Flat"
    if direction == "insufficient":
        return "New"
    return "Missing"


def _trend_color(direction: str) -> tuple[int, int, int]:
    if direction == "up":
        return GREEN
    if direction == "down":
        return RED
    if direction == "flat":
        return GOLD
    if direction == "insufficient":
        return BLUE
    return MUTED


def _draw_trend_indicator(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    direction: str,
    color: tuple[int, int, int],
) -> None:
    if direction == "up":
        draw.line((x, y + 34, x + 26, y + 8, x + 52, y + 8), fill=color, width=6)
        draw.polygon(
            [(x + 52, y + 8), (x + 38, y), (x + 42, y + 17)],
            fill=color,
        )
        return
    if direction == "down":
        draw.line((x, y + 8, x + 26, y + 34, x + 52, y + 34), fill=color, width=6)
        draw.polygon(
            [(x + 52, y + 34), (x + 38, y + 42), (x + 42, y + 25)],
            fill=color,
        )
        return
    if direction == "flat":
        draw.line((x, y + 22, x + 54, y + 22), fill=color, width=6)
        return
    draw.ellipse((x + 17, y + 12, x + 37, y + 32), fill=color)


def _trend_value(value: float | None, kind: str) -> str:
    if value is None:
        return "N/A"
    if kind == "rank":
        return f"#{int(round(value))}"
    if kind in {"percent", "score"}:
        return _pct(float(value) * 100 if kind == "score" else float(value))
    return _compact(value)


def _trend_detail(trend: KvkHistoryTrend, kind: str) -> str:
    if trend.value_count <= 0:
        return "No collected values"
    if trend.value_count < 2:
        return f"Only {_trend_value(trend.last_value, kind)} collected"
    first = _trend_value(trend.first_value, kind)
    last = _trend_value(trend.last_value, kind)
    avg = _trend_value(trend.average, kind)
    return f"{first} to {last} | Avg {avg}"


def _draw_header(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    payload: KvkHistoryPayload,
    *,
    title: str,
    accent: tuple[int, int, int],
    avatar_bytes: bytes | None,
) -> None:
    _draw_text(draw, (42, 34), title.upper(), fill=accent, font=_font(32, bold=True), bold=True)
    _draw_avatar(
        canvas,
        draw,
        (45, 86, 125, 166),
        governor_name=payload.governor_name,
        avatar_bytes=avatar_bytes,
    )
    name_font = _fit_font(
        draw, payload.governor_name, max_width=520, size=36, min_size=24, bold=True
    )
    _draw_text(draw, (148, 88), payload.governor_name, fill=TEXT, font=name_font, bold=True)
    subtitle = f"Governor ID {payload.governor_id}"
    _draw_text(draw, (150, 130), subtitle, fill=MUTED, font=_font(21, bold=True), bold=True)


def _draw_summary_stats(draw: ImageDraw.ImageDraw, payload: KvkHistoryPayload) -> None:
    avg_kills = _average([row.kills for row in payload.last3_rows if row.row_present])
    avg_kill_pct = _average(
        [row.kill_target_percent for row in payload.last3_rows if row.row_present]
    )
    trend_text, trend_color = _trend_label(payload)
    boxes = [
        ("AVG KILLS", _value(avg_kills), GREEN),
        ("AVG KILL %", _pct_value(avg_kill_pct), GOLD),
        ("KILLS TREND", trend_text, trend_color),
    ]
    for idx, (label, value, color) in enumerate(boxes):
        x0 = 750 + idx * 138
        _draw_text(
            draw,
            (x0, 54),
            label,
            fill=TEXT,
            font=_fit_font(draw, label, max_width=128, size=18, min_size=14, bold=True),
            bold=True,
        )
        if label == "KILLS TREND":
            _draw_trend_indicator(
                draw,
                x=x0 + 4,
                y=84,
                direction=_trend_direction(payload),
                color=color,
            )
            trend_font = _fit_font(draw, value, max_width=64, size=24, min_size=17, bold=True)
            _draw_text(draw, (x0 + 70, 92), value, fill=color, font=trend_font, bold=True)
            continue
        _draw_text(
            draw,
            (x0, 86),
            value,
            fill=color,
            font=_fit_font(draw, value, max_width=128, size=30, min_size=20, bold=True),
            bold=True,
        )


def _draw_cell(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    width: int,
    label: str,
    value: str,
    color: tuple[int, int, int] = TEXT,
    sub: str | None = None,
) -> None:
    label_font = _font(16, bold=True)
    _draw_text(draw, (x, y), label.upper(), fill=MUTED, font=label_font, bold=True)
    if value:
        value_font = _fit_font(draw, value, max_width=width, size=28, min_size=18, bold=True)
        _draw_text(draw, (x, y + 23), value, fill=color, font=value_font, bold=True)
    if sub:
        sub_font = _fit_font(draw, sub, max_width=width, size=16, min_size=12, bold=True)
        _draw_text(draw, (x, y + 57), sub, fill=MUTED, font=sub_font, bold=True)


def _draw_last3_rows(draw: ImageDraw.ImageDraw, payload: KvkHistoryPayload) -> None:
    y0 = 226
    row_h = 118
    columns = [
        ("KVK", 46, 68),
        ("Rank", 128, 82),
        ("Kills", 230, 130),
        ("Deads", 382, 122),
        ("Healed", 522, 128),
        ("DKP", 680, 135),
        ("Acclaim", 855, 145),
    ]
    _draw_text(
        draw,
        (46, 184),
        "Last 3 KVKs",
        fill=GOLD,
        font=_font(24, bold=True),
        bold=True,
    )
    for idx, row in enumerate(_last3_display_rows(payload)):
        y = y0 + idx * row_h
        if not row.row_present:
            _draw_cell(
                draw,
                x=columns[0][1],
                y=y,
                width=columns[0][2],
                label="KVK",
                value=str(row.kvk_no),
                color=BLUE,
            )
            _draw_text(
                draw,
                (170, y + 18),
                "No row found for this governor in this started KVK.",
                fill=MUTED,
                font=_font(23, bold=True),
                bold=True,
            )
            continue
        _draw_cell(
            draw,
            x=columns[0][1],
            y=y,
            width=columns[0][2],
            label="KVK",
            value=str(row.kvk_no),
            color=BLUE,
        )
        _draw_cell(
            draw,
            x=columns[1][1],
            y=y,
            width=columns[1][2],
            label="Rank",
            value=_rank(row.kvk_rank),
            color=GOLD,
        )
        _draw_cell(
            draw,
            x=columns[2][1],
            y=y,
            width=columns[2][2],
            label="Kills",
            value=_value(row.kills),
            color=GREEN,
            sub=f"Target {_pct_value(row.kill_target_percent)}",
        )
        _draw_cell(
            draw,
            x=columns[3][1],
            y=y,
            width=columns[3][2],
            label="Deads",
            value=_value(row.deads),
            color=RED,
            sub=f"Target {_pct_value(row.dead_target_percent)}",
        )
        _draw_cell(
            draw,
            x=columns[4][1],
            y=y,
            width=columns[4][2],
            label="Healed",
            value=_value(row.heals, missing=""),
            color=BLUE if row.heals is not None else MUTED,
        )
        _draw_cell(
            draw,
            x=columns[5][1],
            y=y,
            width=columns[5][2],
            label="DKP",
            value=_value(row.dkp),
            color=PURPLE,
            sub=f"Target {_pct_value(row.dkp_target_percent)}",
        )
        _draw_cell(
            draw,
            x=columns[6][1],
            y=y,
            width=columns[6][2],
            label="Acclaim",
            value=_value(row.acclaim, missing=""),
            color=GOLD if row.acclaim is not None else MUTED,
        )


def render_kvk_history_last3_card(
    payload: KvkHistoryPayload, *, avatar_bytes: bytes | None = None
) -> RenderedKvkHistoryCard | None:
    background = _background_path(HISTORY_LAST3_BACKGROUND)
    if background is None:
        return None
    canvas, draw = _card_canvas(background)
    _draw_header(
        canvas,
        draw,
        payload,
        title="KVK History",
        accent=GOLD,
        avatar_bytes=avatar_bytes,
    )
    _draw_summary_stats(draw, payload)
    _draw_last3_rows(draw, payload)
    footer = f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}"
    _draw_text(draw, (770, 594), footer, fill=MUTED, font=_font(18, bold=True), bold=True)
    return _save(canvas, f"kvk_history_last3_{payload.governor_id}.png")


def _summary_metric_record(payload: KvkHistoryPayload, label: str) -> KvkHistorySummaryMetric:
    metric = payload.history_summary_metrics.get(label)
    if metric is not None:
        return metric
    return KvkHistorySummaryMetric(value=payload.history_summary.get(label))


SUMMARY_METRIC_LAYOUT = (
    (
        ("Highest Rank", "Highest Rank", GOLD, "rank"),
        ("Autarchs", "Autarchs", GOLD, "number"),
        ("KVK Played", "KVK Played", BLUE, "number"),
        ("Highest Acclaim", "Highest Acclaim", GOLD, "number"),
    ),
    (
        ("Most Kills", "Most Kills", GREEN, "number"),
        ("Most KillPoints", "Most KillPoints", GREEN, "number"),
        ("Most Deads", "Most Deads", RED, "number"),
        ("Most Heals", "Most Heals", BLUE, "number"),
    ),
    (
        ("Most DKP", "Most DKP", PURPLE, "number"),
        ("Lowest Tanking Score", "Lowest Tanking Score", BLUE, "score"),
        ("Most Pre-KVK", "Most Pre-KVK", BLUE, "number"),
        ("Most Honor", "Most Honor", GOLD, "number"),
    ),
)


def _summary_display_value(value: int | float | None, kind: str) -> str:
    if value is None:
        return "N/A"
    if kind == "rank":
        return f"#{int(value)}"
    if kind == "score":
        return f"{float(value) * 100:.0f}%"
    return _compact(value)


def _summary_subtitle(metric: KvkHistorySummaryMetric) -> str:
    if metric.value is None:
        return ""
    kvk = f"KVK {metric.kvk_no}" if metric.kvk_no is not None else ""
    rank = f"#{metric.overall_rank} overall" if metric.overall_rank is not None else ""
    if rank and kvk:
        return f"{rank} • {kvk}"
    return rank or kvk


def _draw_summary_metric(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    title: str,
    metric: KvkHistorySummaryMetric,
    color: tuple[int, int, int],
    kind: str,
) -> None:
    title_font = _fit_font(draw, title.upper(), max_width=w, size=20, min_size=14, bold=True)
    value = _summary_display_value(metric.value, kind)
    value_font = _fit_font(draw, value, max_width=w, size=38, min_size=24, bold=True)
    sub = _summary_subtitle(metric)

    _draw_text(draw, (x, y), title.upper(), fill=TEXT, font=title_font, bold=True)
    _draw_text(draw, (x, y + 31), value, fill=color, font=value_font, bold=True)
    if sub:
        sub_font = _fit_font(draw, sub, max_width=w, size=16, min_size=12, bold=True)
        _draw_text(draw, (x, y + 75), sub, fill=MUTED, font=sub_font, bold=True)


def render_kvk_history_summary_card(
    payload: KvkHistoryPayload, *, avatar_bytes: bytes | None = None
) -> RenderedKvkHistoryCard | None:
    background = _background_path(HISTORY_SUMMARY_BACKGROUND)
    if background is None:
        return None
    canvas, draw = _card_canvas(background)
    _draw_header(
        canvas,
        draw,
        payload,
        title="KVK Summary",
        accent=BLUE,
        avatar_bytes=avatar_bytes,
    )

    col_w = 230
    col_x = (45, 315, 585, 855)
    row_y = (190, 325, 460)
    for row_index, metrics in enumerate(SUMMARY_METRIC_LAYOUT):
        for col_index, (title, key, color, kind) in enumerate(metrics):
            _draw_summary_metric(
                draw,
                x=col_x[col_index],
                y=row_y[row_index],
                w=col_w,
                title=title,
                metric=_summary_metric_record(payload, key),
                color=color,
                kind=kind,
            )

    footer = f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}"
    footer_font = _fit_font(draw, footer, max_width=430, size=18, min_size=14, bold=True)
    _draw_text(draw, (705, 594), footer, fill=MUTED, font=footer_font, bold=True)
    return _save(canvas, f"kvk_history_summary_{payload.governor_id}.png")


TREND_METRIC_LAYOUT = (
    ("Rank", "rank", GOLD, "rank"),
    ("Kills", "kills", GREEN, "number"),
    ("Kill Target", "kill_target_percent", GOLD, "percent"),
    ("Deads", "deads", RED, "number"),
    ("Dead Target", "dead_target_percent", RED, "percent"),
    ("Healed", "heals", BLUE, "number"),
    ("DKP", "dkp", PURPLE, "number"),
    ("DKP Target", "dkp_target_percent", PURPLE, "percent"),
    ("Acclaim", "acclaim", GOLD, "number"),
    ("KillPoints", "kill_points", GREEN, "number"),
    ("Tanking Score", "tanking_score", BLUE, "score"),
)


def _draw_trend_metric(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    title: str,
    trend: KvkHistoryTrend,
    accent: tuple[int, int, int],
    kind: str,
) -> None:
    direction = trend.direction
    color = _trend_color(direction)
    title_font = _fit_font(draw, title.upper(), max_width=w - 68, size=18, min_size=13, bold=True)
    value = _trend_text(direction)
    value_font = _fit_font(draw, value, max_width=124, size=21, min_size=15, bold=True)
    detail = _trend_detail(trend, kind)
    detail_font = _fit_font(draw, detail, max_width=w - 206, size=14, min_size=10, bold=True)

    draw.rounded_rectangle((x, y, x + w, y + 56), radius=8, fill=(0, 0, 0, 72))
    _draw_trend_indicator(draw, x=x + 11, y=y + 7, direction=direction, color=color)
    _draw_text(draw, (x + 76, y + 7), title.upper(), fill=TEXT, font=title_font, bold=True)
    _draw_text(draw, (x + 76, y + 28), value, fill=color, font=value_font, bold=True)
    _draw_text(draw, (x + 196, y + 33), detail, fill=accent, font=detail_font, bold=True)


def render_kvk_history_trends_card(
    payload: KvkHistoryPayload, *, avatar_bytes: bytes | None = None
) -> RenderedKvkHistoryCard | None:
    background = _background_path(HISTORY_TRENDS_BACKGROUND)
    if background is None:
        return None
    canvas, draw = _card_canvas(background)
    _draw_header(
        canvas,
        draw,
        payload,
        title="KVK Trends",
        accent=PURPLE,
        avatar_bytes=avatar_bytes,
    )

    _draw_text(
        draw,
        (46, 184),
        "Performance movement across collected KVK history",
        fill=GOLD,
        font=_font(23, bold=True),
        bold=True,
    )
    left_x = 46
    right_x = 612
    y0 = 218
    row_gap = 61
    for idx, (title, key, accent, kind) in enumerate(TREND_METRIC_LAYOUT):
        col = idx % 2
        row = idx // 2
        x = left_x if col == 0 else right_x
        y = y0 + row * row_gap
        trend = payload.trends.get(key) or KvkHistoryTrend(
            metric=key,
            average=None,
            direction="missing",
        )
        _draw_trend_metric(
            draw,
            x=x,
            y=y,
            w=520,
            title=title,
            trend=trend,
            accent=accent,
            kind=kind,
        )

    footer = f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}"
    footer_font = _fit_font(draw, footer, max_width=430, size=18, min_size=14, bold=True)
    _draw_text(draw, (705, 594), footer, fill=MUTED, font=footer_font, bold=True)
    return _save(canvas, f"kvk_history_trends_{payload.governor_id}.png")


def build_last3_text_fallback(payload: KvkHistoryPayload) -> str:
    lines = [f"KVK History - {payload.governor_name} ({payload.governor_id})"]
    for row in payload.last3_rows:
        if not row.row_present:
            lines.append(f"KVK {row.kvk_no}: no row found")
            continue
        lines.append(
            " | ".join(
                [
                    f"KVK {row.kvk_no}",
                    f"Rank {_rank(row.kvk_rank)}",
                    f"Kills {_value(row.kills)} ({_pct_value(row.kill_target_percent)})",
                    f"Deads {_value(row.deads)} ({_pct_value(row.dead_target_percent)})",
                    f"Healed {_value(row.heals, missing='Missing')}",
                    f"DKP {_value(row.dkp)} ({_pct_value(row.dkp_target_percent)})",
                    f"Acclaim {_value(row.acclaim, missing='Missing')}",
                ]
            )
        )
    return "\n".join(lines)
