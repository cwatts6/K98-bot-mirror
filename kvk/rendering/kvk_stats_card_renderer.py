from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from kvk.models.kvk_stats_card import KvkStatsCardPayload, RenderedKvkStatsCard
from prekvk import report_image_renderer as text_renderer

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets" / "kvk" / "cards"
BACKGROUND = ASSET_DIR / "Tides_Stats_Card.png"

WIDTH = 1180
HEIGHT = 640
TEXT = (255, 255, 255)
MUTED = (210, 214, 222)
GREEN = (52, 211, 153)
BLUE = (164, 220, 255)
RED = (255, 87, 118)
PURPLE = (168, 85, 247)
GOLD = (255, 211, 87)


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return text_renderer._font(size, bold=bold)


def _hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return GOLD
    return tuple(int(value[idx : idx + 2], 16) for idx in (0, 2, 4))


def _compact(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    val = float(value)
    abs_val = abs(val)
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs_val >= limit:
            out = f"{val / limit:.3f}".rstrip("0").rstrip(".")
            return f"{out}{suffix}"
    return f"{int(val):,}"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    number = f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{number}%"


def _progress_scale(percent: float | None) -> list[int]:
    value = max(0.0, float(percent or 0.0))
    upper = 100
    if value > 125:
        upper = 150
    elif value > 100:
        upper = 125
    return list(range(0, upper + 1, 25))


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    return int(draw.textbbox((0, 0), text, font=font)[2])


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    font = text_renderer._font_for_text(text, size, bold=bold)
    while size > min_size and _text_width(draw, text, font) > max_width:
        size -= 1
        font = text_renderer._font_for_text(text, size, bold=bold)
    return font


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill=TEXT,
    font: ImageFont.ImageFont | None = None,
    bold: bool = False,
) -> None:
    font = font or _font(20, bold=bold)
    text_renderer._draw_text(draw, xy, text, fill=fill, font=font, bold=bold)


def _metric(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    title: str,
    value: str,
    color: tuple[int, int, int],
    sub: str | None = None,
) -> None:
    _draw_text(draw, (x, y), title.upper(), fill=TEXT, font=_font(21, bold=True), bold=True)
    value_font = _fit_font(draw, value, max_width=w, size=44, min_size=29, bold=True)
    _draw_text(draw, (x, y + 34), value, fill=color, font=value_font, bold=True)
    if sub:
        sub_font = _fit_font(draw, sub, max_width=w, size=18, min_size=13, bold=True)
        _draw_text(draw, (x, y + 82), sub, fill=MUTED, font=sub_font, bold=True)


def _draw_avatar(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    governor_name: str,
    avatar_bytes: bytes | None,
) -> None:
    x0, y0, x1, y1 = box
    size = x1 - x0
    if avatar_bytes:
        try:
            avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((size, size))
            mask = Image.new("L", (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)
            canvas.paste(avatar, (x0, y0), mask)
            draw.ellipse(box, outline=(188, 196, 216), width=3)
            return
        except Exception:
            pass

    draw.ellipse(box, fill=(38, 44, 58, 220), outline=(188, 196, 216), width=3)
    initials = "".join(part[:1] for part in governor_name.split()[:2]).upper() or "K"
    initials_font = _fit_font(draw, initials, max_width=52, size=30, min_size=18, bold=True)
    draw.text((x0 + size / 2, y0 + size / 2), initials, anchor="mm", fill=GOLD, font=initials_font)


def _progress(draw: ImageDraw.ImageDraw, payload: KvkStatsCardPayload) -> None:
    x, y, w, h = 40, 544, 760, 18
    color = _hex_color(payload.kill_progress.color_hex)
    ticks = _progress_scale(payload.kill_progress.percent)
    scale_max = ticks[-1]
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(66, 58, 48))
    pct = max(0.0, min(float(payload.kill_progress.percent or 0.0), float(scale_max)))
    fill_w = int(w * pct / scale_max)
    if fill_w:
        draw.rounded_rectangle((x, y, x + fill_w, y + h), radius=8, fill=color)
    tick_font = _font(15, bold=True)
    for tick in ticks:
        tick_x = x + int(w * tick / scale_max)
        draw.line((tick_x, y - 4, tick_x, y + h + 4), fill=(255, 255, 255, 150), width=2)
        tick_label = f"{tick}%"
        label_width = _text_width(draw, tick_label, tick_font)
        label_x = max(x, min(x + w - label_width, tick_x - label_width // 2))
        _draw_text(draw, (label_x, y + 26), tick_label, fill=MUTED, font=tick_font, bold=True)
    label = f"Kills Target Progress  {_pct(payload.kill_progress.percent)} - {payload.kill_progress.quote}"
    font = _fit_font(draw, label, max_width=780, size=23, min_size=16, bold=True)
    _draw_text(draw, (40, 504), label, fill=color, font=font, bold=True)


def render_kvk_stats_card(
    payload: KvkStatsCardPayload, *, avatar_bytes: bytes | None = None
) -> RenderedKvkStatsCard | None:
    if not BACKGROUND.exists():
        return None

    background = Image.open(BACKGROUND).convert("RGBA")
    background = background.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    odraw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=22, fill=(0, 0, 0, 75))
    odraw.rectangle((0, 0, WIDTH, 190), fill=(0, 0, 0, 72))
    odraw.rectangle((0, 470, WIDTH, HEIGHT), fill=(0, 0, 0, 88))
    canvas = Image.alpha_composite(background, overlay)
    draw = ImageDraw.Draw(canvas, "RGBA")

    title_parts = [payload.display_mode]
    if payload.display_camp:
        title_parts.append(payload.display_camp)
    title = " | ".join(title_parts)
    title_font = _fit_font(draw, title, max_width=650, size=28, min_size=20, bold=True)
    _draw_text(draw, (40, 46), title, fill=GOLD, font=title_font, bold=True)

    context = [payload.display_kvk_label]
    if payload.kingdom:
        context.append(f"Kingdom {payload.kingdom}")
    _draw_text(
        draw,
        (40, 92),
        "  |  ".join(context),
        fill=TEXT,
        font=_font(22),
    )

    avatar_box = (48, 135, 128, 215)
    _draw_avatar(
        canvas, draw, avatar_box, governor_name=payload.governor_name, avatar_bytes=avatar_bytes
    )

    name_font = _fit_font(
        draw, payload.governor_name, max_width=470, size=43, min_size=25, bold=True
    )
    _draw_text(draw, (155, 135), payload.governor_name, fill=TEXT, font=name_font, bold=True)
    _draw_text(draw, (155, 183), str(payload.governor_id), fill=TEXT, font=_font(24, bold=True))

    rank_x = 940
    _draw_text(draw, (rank_x, 56), "RANK", fill=TEXT, font=_font(25, bold=True), bold=True)
    rank_value = f"#{payload.kvk_rank}" if payload.kvk_rank not in (None, "") else "N/A"
    _draw_text(draw, (rank_x, 88), rank_value, fill=TEXT, font=_font(50, bold=True), bold=True)

    col_w = 230
    col_x = (45, 315, 585, 855)
    row_y = (260, 390)
    _metric(
        draw,
        x=col_x[0],
        y=row_y[0],
        w=col_w,
        title="MM Power",
        value=_compact(payload.matchmaking_power),
        color=BLUE,
    )
    _metric(
        draw,
        x=col_x[1],
        y=row_y[0],
        w=col_w,
        title="Kills Gain",
        value=f"{_compact(payload.kills_gain)}",
        sub=f"{_compact(payload.kill_target)} target | {_pct(payload.kill_progress.percent)}",
        color=GREEN,
    )
    _metric(
        draw,
        x=col_x[2],
        y=row_y[0],
        w=col_w,
        title="Deads",
        value=_compact(payload.deads),
        sub=f"{_compact(payload.dead_target)} target | {_pct(payload.dead_target_percent)}",
        color=RED,
    )
    _metric(
        draw,
        x=col_x[3],
        y=row_y[0],
        w=col_w,
        title="Healed",
        value=_compact(payload.healed),
        color=BLUE,
    )
    _metric(
        draw,
        x=col_x[0],
        y=row_y[1],
        w=col_w,
        title="KP Gain",
        value=_compact(payload.kp_gain),
        color=GREEN,
    )
    _metric(
        draw,
        x=col_x[1],
        y=row_y[1],
        w=col_w,
        title="KP Loss",
        value=_compact(payload.kp_loss),
        color=(255, 126, 126),
    )
    _metric(
        draw,
        x=col_x[2],
        y=row_y[1],
        w=col_w,
        title="Tanking Score",
        value=_pct(payload.tanking_score_percent),
        sub=payload.playstyle or "Not enough data",
        color=PURPLE if payload.tanking_score_percent is not None else MUTED,
    )
    _metric(
        draw,
        x=col_x[3],
        y=row_y[1],
        w=col_w,
        title="Acclaim",
        value=_compact(payload.acclaim),
        color=GOLD,
    )

    _progress(draw, payload)
    updated = f"Last updated {payload.last_refresh or 'unknown'}"
    footer_font = _fit_font(draw, updated, max_width=365, size=20, min_size=15, bold=True)
    _draw_text(
        draw,
        (775, 596),
        updated,
        fill=MUTED,
        font=footer_font,
        bold=True,
    )

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    filename = f"kvk_stats_{payload.governor_id}.png"
    return RenderedKvkStatsCard(filename=filename, image_bytes=buf)
