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
DIM = (164, 170, 181)
GREEN = (52, 211, 153)
BLUE = (164, 220, 255)
RED = (255, 87, 118)
PURPLE = (168, 85, 247)
GOLD = (255, 211, 87)
ORANGE = (234, 128, 24)
PANEL = (15, 12, 10, 118)
PANEL_SOFT = (255, 255, 255, 28)


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


def _draw_panel(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(xy, radius=8, fill=PANEL, outline=PANEL_SOFT, width=1)


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
    _draw_text(draw, (x, y), title.upper(), fill=TEXT, font=_font(23, bold=True), bold=True)
    value_font = _fit_font(draw, value, max_width=w, size=50, min_size=31, bold=True)
    _draw_text(draw, (x, y + 38), value, fill=color, font=value_font, bold=True)
    if sub:
        sub_font = _fit_font(draw, sub, max_width=w, size=21, min_size=14, bold=True)
        _draw_text(draw, (x, y + 92), sub, fill=MUTED, font=sub_font, bold=True)


def _progress(draw: ImageDraw.ImageDraw, payload: KvkStatsCardPayload) -> None:
    x, y, w, h = 40, 548, 670, 18
    color = _hex_color(payload.kill_progress.color_hex)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(66, 58, 48))
    pct = max(0.0, min(float(payload.kill_progress.percent or 0.0), 100.0))
    fill_w = int(w * pct / 100.0)
    if fill_w:
        draw.rounded_rectangle((x, y, x + fill_w, y + h), radius=8, fill=color)
    label = f"Kills Target Progress  {_pct(payload.kill_progress.percent)} - {payload.kill_progress.quote}"
    font = _fit_font(draw, label, max_width=900, size=25, min_size=17, bold=True)
    _draw_text(draw, (40, 510), label, fill=color, font=font, bold=True)


def render_kvk_stats_card(payload: KvkStatsCardPayload) -> RenderedKvkStatsCard | None:
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

    _draw_text(draw, (40, 46), "MY KVK", fill=GOLD, font=_font(25, bold=True), bold=True)
    context = [payload.display_kvk_label, payload.display_mode]
    if payload.kingdom:
        context.append(f"Kingdom {payload.kingdom}")
    if payload.display_camp:
        context.append(payload.display_camp)
    updated = f"Last updated {payload.last_refresh or 'unknown'}"
    _draw_text(
        draw,
        (40, 92),
        f"{updated}  |  {'  |  '.join(context)}",
        fill=TEXT,
        font=_font(23),
    )

    avatar_box = (48, 145, 128, 225)
    draw.ellipse(avatar_box, fill=(38, 44, 58, 220), outline=(188, 196, 216), width=3)
    initials = "".join(part[:1] for part in payload.governor_name.split()[:2]).upper() or "K"
    initials_font = _fit_font(draw, initials, max_width=52, size=30, min_size=18, bold=True)
    draw.text((88, 184), initials, anchor="mm", fill=GOLD, font=initials_font)

    name_font = _fit_font(draw, payload.governor_name, max_width=470, size=43, min_size=25, bold=True)
    _draw_text(draw, (155, 142), payload.governor_name, fill=TEXT, font=name_font, bold=True)
    _draw_text(draw, (155, 190), str(payload.governor_id), fill=TEXT, font=_font(24, bold=True))
    if payload.display_camp:
        camp_font = _fit_font(draw, payload.display_camp, max_width=180, size=24, min_size=16, bold=True)
        draw.rounded_rectangle((155, 228, 315, 266), radius=8, fill=(122, 73, 248, 230))
        _draw_text(draw, (170, 234), payload.display_camp, fill=TEXT, font=camp_font, bold=True)

    _draw_panel(draw, (780, 135, 1090, 252))
    _draw_text(draw, (805, 155), "RANK", fill=TEXT, font=_font(28, bold=True), bold=True)
    rank_value = f"#{payload.kvk_rank}" if payload.kvk_rank not in (None, "") else "N/A"
    _draw_text(draw, (805, 188), rank_value, fill=TEXT, font=_font(54, bold=True), bold=True)

    col_w = 300
    _metric(draw, x=45, y=305, w=col_w, title="KP Gain", value=_compact(payload.kp_gain), color=GREEN)
    _metric(
        draw,
        x=350,
        y=305,
        w=col_w,
        title="MM Power",
        value=_compact(payload.matchmaking_power),
        color=BLUE,
    )
    _metric(
        draw,
        x=700,
        y=305,
        w=col_w,
        title="Power Loss",
        value=_compact(abs(payload.power_loss) if payload.power_loss is not None else None),
        color=RED,
    )
    _metric(
        draw,
        x=45,
        y=420,
        w=col_w,
        title="Kills Gain",
        value=f"{_compact(payload.kills_gain)}",
        sub=f"{_compact(payload.kill_target)} target | {_pct(payload.kill_progress.percent)}",
        color=GREEN,
    )
    _metric(
        draw,
        x=350,
        y=420,
        w=col_w,
        title="Deads",
        value=_compact(payload.deads),
        sub=f"{_compact(payload.dead_target)} target | {_pct(payload.dead_target_percent)}",
        color=RED,
    )
    _metric(
        draw,
        x=700,
        y=420,
        w=col_w,
        title="Tanking Score",
        value=_pct(payload.tanking_score_percent),
        sub=payload.playstyle or "Not enough data",
        color=PURPLE if payload.tanking_score_percent is not None else MUTED,
    )

    right_x = 805
    _draw_text(draw, (right_x, 280), "KP LOSS", fill=TEXT, font=_font(22, bold=True), bold=True)
    _draw_text(
        draw,
        (right_x, 310),
        _compact(payload.kp_loss),
        fill=(255, 126, 126),
        font=_font(36, bold=True),
        bold=True,
    )
    _draw_text(draw, (right_x, 365), "HEALED", fill=TEXT, font=_font(22, bold=True), bold=True)
    _draw_text(
        draw,
        (right_x, 395),
        _compact(payload.healed),
        fill=BLUE,
        font=_font(36, bold=True),
        bold=True,
    )
    _draw_text(draw, (right_x, 450), "ACCLAIM", fill=TEXT, font=_font(22, bold=True), bold=True)
    _draw_text(
        draw,
        (right_x, 480),
        _compact(payload.acclaim),
        fill=GOLD,
        font=_font(36, bold=True),
        bold=True,
    )

    _progress(draw, payload)
    _draw_text(
        draw,
        (756, 596),
        "powered by PROKINGDOMS.COM",
        fill=GOLD,
        font=_font(22, bold=True),
        bold=True,
    )

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    filename = f"kvk_stats_{payload.governor_id}.png"
    return RenderedKvkStatsCard(filename=filename, image_bytes=buf)
