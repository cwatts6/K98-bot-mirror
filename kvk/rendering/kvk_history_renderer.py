from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from kvk.models.kvk_history_payload import (
    KvkHistoryPayload,
    KvkHistoryRow,
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
    _draw_centered_text,
    _draw_text,
    _fit_font,
    _font,
    _load_background,
    _metric,
    _pct,
)

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets" / "kvk" / "cards"
HISTORY_LAST3_BACKGROUND = ASSET_DIR / "history_card1.PNG"
HISTORY_SUMMARY_BACKGROUND = ASSET_DIR / "history_card2.PNG"
DEFAULT_BACKGROUND = ASSET_DIR / "Default_card.jpg"
TIDES_BACKGROUND = ASSET_DIR / "Tides_Stats_Card.png"

PANEL_FILL = (6, 11, 22, 178)
PANEL_OUTLINE = (255, 255, 255, 48)


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
    odraw.rectangle((0, 182, WIDTH, HEIGHT), fill=(0, 0, 0, 64))
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


def _latest_present_row(payload: KvkHistoryPayload) -> KvkHistoryRow | None:
    for row in reversed(payload.rows):
        if row.row_present:
            return row
    return None


def _average(values: list[int | float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _trend_label(payload: KvkHistoryPayload) -> tuple[str, tuple[int, int, int]]:
    trend = payload.trends.get("kills")
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


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    radius: int = 16,
    fill: tuple[int, int, int, int] = PANEL_FILL,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=PANEL_OUTLINE, width=1)


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
        x0 = 760 + idx * 130
        _draw_panel(draw, (x0, 40, x0 + 116, 138), radius=12, fill=(9, 15, 26, 174))
        _draw_centered_text(
            draw,
            center_x=x0 + 58,
            y=58,
            text=label,
            fill=MUTED,
            font=_fit_font(draw, label, max_width=102, size=15, min_size=12, bold=True),
            bold=True,
        )
        _draw_centered_text(
            draw,
            center_x=x0 + 58,
            y=86,
            text=value,
            fill=color,
            font=_fit_font(draw, value, max_width=104, size=28, min_size=18, bold=True),
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
    value_font = _fit_font(draw, value, max_width=width, size=28, min_size=18, bold=True)
    _draw_text(draw, (x, y), label.upper(), fill=MUTED, font=label_font, bold=True)
    _draw_text(draw, (x, y + 23), value, fill=color, font=value_font, bold=True)
    if sub:
        sub_font = _fit_font(draw, sub, max_width=width, size=16, min_size=12, bold=True)
        _draw_text(draw, (x, y + 57), sub, fill=MUTED, font=sub_font, bold=True)


def _draw_last3_rows(draw: ImageDraw.ImageDraw, payload: KvkHistoryPayload) -> None:
    y0 = 212
    row_h = 118
    columns = [
        ("KVK", 58, 74),
        ("Rank", 150, 100),
        ("Kills", 275, 150),
        ("Deads", 455, 140),
        ("DKP", 625, 145),
        ("Acclaim", 800, 145),
    ]
    _draw_text(
        draw,
        (46, 184),
        "Last 3 started KVKs",
        fill=GOLD,
        font=_font(22, bold=True),
        bold=True,
    )
    _draw_text(
        draw,
        (800, 184),
        "Missing metrics stay missing",
        fill=MUTED,
        font=_font(17, bold=True),
        bold=True,
    )
    for idx, row in enumerate(payload.last3_rows):
        y = y0 + idx * row_h
        fill = (6, 11, 22, 184) if idx % 2 == 0 else (8, 15, 28, 166)
        _draw_panel(draw, (40, y, 1118, y + row_h - 14), radius=14, fill=fill)
        if not row.row_present:
            _draw_cell(
                draw,
                x=columns[0][1],
                y=y + 24,
                width=columns[0][2],
                label="KVK",
                value=str(row.kvk_no),
                color=BLUE,
            )
            _draw_text(
                draw,
                (170, y + 42),
                "No row found for this governor in this started KVK.",
                fill=MUTED,
                font=_font(23, bold=True),
                bold=True,
            )
            continue
        _draw_cell(
            draw,
            x=columns[0][1],
            y=y + 23,
            width=columns[0][2],
            label="KVK",
            value=str(row.kvk_no),
            color=BLUE,
        )
        _draw_cell(
            draw,
            x=columns[1][1],
            y=y + 23,
            width=columns[1][2],
            label="Rank",
            value=_rank(row.kvk_rank),
            color=GOLD,
        )
        _draw_cell(
            draw,
            x=columns[2][1],
            y=y + 23,
            width=columns[2][2],
            label="Kills",
            value=_value(row.kills),
            color=GREEN,
            sub=f"Target {_pct_value(row.kill_target_percent)}",
        )
        _draw_cell(
            draw,
            x=columns[3][1],
            y=y + 23,
            width=columns[3][2],
            label="Deads",
            value=_value(row.deads),
            color=RED,
            sub=f"Target {_pct_value(row.dead_target_percent)}",
        )
        _draw_cell(
            draw,
            x=columns[4][1],
            y=y + 23,
            width=columns[4][2],
            label="DKP",
            value=_value(row.dkp),
            color=PURPLE,
            sub=f"Target {_pct_value(row.dkp_target_percent)}",
        )
        _draw_cell(
            draw,
            x=columns[5][1],
            y=y + 23,
            width=columns[5][2],
            label="Acclaim",
            value=_value(row.acclaim, missing="Missing"),
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


def _summary_value(payload: KvkHistoryPayload, label: str) -> int | None:
    return payload.history_summary.get(label)


def _draw_latest_comparison(draw: ImageDraw.ImageDraw, row: KvkHistoryRow | None) -> None:
    _draw_text(
        draw, (46, 418), "LAST KVK COMPARISON", fill=GOLD, font=_font(22, bold=True), bold=True
    )
    if row is None:
        _draw_text(
            draw,
            (46, 465),
            "No history data available.",
            fill=MUTED,
            font=_font(26, bold=True),
            bold=True,
        )
        return
    label = f"KVK {row.kvk_no}"
    _draw_text(draw, (48, 456), label, fill=BLUE, font=_font(30, bold=True), bold=True)
    items = [
        ("Kills", _value(row.kills), _pct_value(row.kill_target_percent), GREEN),
        ("Deads", _value(row.deads), _pct_value(row.dead_target_percent), RED),
        ("DKP", _value(row.dkp), _pct_value(row.dkp_target_percent), PURPLE),
        (
            "Acclaim",
            _value(row.acclaim, missing="Missing"),
            None,
            GOLD if row.acclaim is not None else MUTED,
        ),
    ]
    for idx, (title, value, pct, color) in enumerate(items):
        x = 205 + idx * 230
        _draw_cell(
            draw,
            x=x,
            y=445,
            width=190,
            label=title,
            value=value,
            color=color,
            sub=f"Target {pct}" if pct is not None else None,
        )


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
    _metric(
        draw,
        x=col_x[0],
        y=205,
        w=col_w,
        title="KVK Played",
        value=_value(_summary_value(payload, "KVK Played")),
        color=BLUE,
    )
    _metric(
        draw,
        x=col_x[1],
        y=205,
        w=col_w,
        title="Highest Acclaim",
        value=_value(_summary_value(payload, "Highest Acclaim")),
        color=GOLD,
    )
    _metric(
        draw,
        x=col_x[2],
        y=205,
        w=col_w,
        title="Most Kills",
        value=_value(_summary_value(payload, "Most Kills")),
        color=GREEN,
    )
    _metric(
        draw,
        x=col_x[3],
        y=205,
        w=col_w,
        title="Most Deads",
        value=_value(_summary_value(payload, "Most Deads")),
        color=RED,
    )
    if _summary_value(payload, "Most Heal") not in (None, 0):
        _metric(
            draw,
            x=col_x[0],
            y=320,
            w=col_w,
            title="Most Heal",
            value=_value(_summary_value(payload, "Most Heal")),
            color=BLUE,
        )

    _draw_latest_comparison(draw, _latest_present_row(payload))
    footer = f"Generated {payload.generated_at_utc:%Y-%m-%d %H:%M UTC}"
    footer_font = _fit_font(draw, footer, max_width=430, size=18, min_size=14, bold=True)
    _draw_text(draw, (705, 594), footer, fill=MUTED, font=footer_font, bold=True)
    return _save(canvas, f"kvk_history_summary_{payload.governor_id}.png")


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
                    f"DKP {_value(row.dkp)} ({_pct_value(row.dkp_target_percent)})",
                    f"Acclaim {_value(row.acclaim, missing='Missing')}",
                ]
            )
        )
    return "\n".join(lines)
