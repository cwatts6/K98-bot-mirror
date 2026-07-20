from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from kvk.models.kvk_stats_card import KvkStatsCardPayload, RenderedKvkStatsCard
from kvk.theme import normalize_kvk_mode

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets" / "kvk" / "cards"
DEFAULT_BACKGROUND = ASSET_DIR / "Default_card.jpg"
TIDES_BACKGROUND = ASSET_DIR / "Tides_Stats_Card.png"
MODE_BACKGROUNDS = {
    "tides of war": TIDES_BACKGROUND,
    "heroic anthem": ASSET_DIR / "Heroic_Anthem_Stats_Card.jpg",
    "storm of stratagems": ASSET_DIR / "Storm_of_Stratagems_Stats_card.png",
    "songs of troy": ASSET_DIR / "Songs_of_Troy_Stats_card.jpg",
}

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
    return visual_text.font(size, bold=bold)


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
            out = f"{val / limit:.1f}".rstrip("0").rstrip(".")
            return f"{out}{suffix}"
    return f"{int(val):,}"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    number = f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{number}%"


def _progress_scale(percent: float | None) -> list[int]:
    value = max(0.0, float(percent or 0.0))
    if value <= 100:
        return list(range(0, 101, 25))
    if value <= 150:
        upper = int(((value + 24.999) // 25) * 25)
        return list(range(0, max(125, upper) + 1, 25))
    upper = int(((value + 49.999) // 50) * 50)
    ticks = list(range(0, 151, 25))
    ticks.extend(range(200, max(200, upper) + 1, 50))
    return ticks


def _background_for_mode(kvk_name: str | None) -> Path | None:
    mode_path = MODE_BACKGROUNDS.get(normalize_kvk_mode(kvk_name))
    for path in (mode_path, DEFAULT_BACKGROUND, TIDES_BACKGROUND):
        if path is not None and path.exists():
            return path
    return None


def _load_background(path: Path) -> Image.Image:
    background = Image.open(path).convert("RGBA")
    return background.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    *,
    bold: bool = False,
) -> int:
    return visual_text.text_width(draw, text, font=font, bold=bold)


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    font = visual_text.font_for_text(text, size, bold=bold)
    while size > min_size and _text_width(draw, text, font, bold=bold) > max_width:
        size -= 1
        font = visual_text.font_for_text(text, size, bold=bold)
    return font


def _fit_shared_font(
    draw: ImageDraw.ImageDraw,
    values: list[str],
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    text = max(values or [""], key=len)
    font = visual_text.font_for_text(text, size, bold=bold)
    while size > min_size and any(
        _text_width(draw, value, font, bold=bold) > max_width for value in values
    ):
        size -= 1
        font = visual_text.font_for_text(text, size, bold=bold)
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
    visual_text.draw_text(draw, xy, text, fill=fill, font=font, bold=bold)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    *,
    center_x: int,
    y: int,
    text: str,
    fill=TEXT,
    font: ImageFont.ImageFont | None = None,
    bold: bool = False,
) -> None:
    font = font or _font(20, bold=bold)
    x = center_x - (_text_width(draw, text, font, bold=bold) // 2)
    _draw_text(draw, (x, y), text, fill=fill, font=font, bold=bold)


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
    value_font: ImageFont.ImageFont | None = None,
) -> None:
    _draw_text(draw, (x, y), title.upper(), fill=TEXT, font=_font(21, bold=True), bold=True)
    value_font = value_font or _fit_font(draw, value, max_width=w, size=44, min_size=29, bold=True)
    _draw_text(draw, (x, y + 34), value, fill=color, font=value_font, bold=True)
    if sub:
        sub_font = _fit_font(draw, sub, max_width=w, size=18, min_size=13, bold=True)
        _draw_text(draw, (x, y + 82), sub, fill=MUTED, font=sub_font, bold=True)


def _panel(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int, int] = (10, 18, 32, 155),
) -> None:
    draw.rounded_rectangle(xy, radius=14, fill=fill, outline=(255, 255, 255, 45), width=1)


def _section_title(draw: ImageDraw.ImageDraw, xy: tuple[int, int], title: str) -> None:
    _draw_text(draw, xy, title.upper(), fill=GOLD, font=_font(22, bold=True), bold=True)


def _draw_kv_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[tuple[str, str]],
    *,
    x: int,
    y: int,
    width: int,
    row_gap: int = 31,
) -> None:
    label_font = _font(18, bold=True)
    for idx, (label, value) in enumerate(lines):
        row_y = y + idx * row_gap
        label_text = f"{label}:"
        _draw_text(draw, (x, row_y), label_text, fill=MUTED, font=label_font, bold=True)
        value_text = str(value)
        fit_value_font = _fit_font(
            draw, value_text, max_width=width - 150, size=20, min_size=15, bold=True
        )
        value_x = x + width - _text_width(draw, value_text, fit_value_font, bold=True)
        _draw_text(draw, (value_x, row_y), value_text, fill=TEXT, font=fit_value_font, bold=True)


def _nonzero_items(values: dict) -> list[tuple[str, int | float | str]]:
    return [(label, value) for label, value in values.items() if value not in (None, "", 0, 0.0)]


def _draw_card_header(
    draw: ImageDraw.ImageDraw,
    payload: KvkStatsCardPayload,
    *,
    title: str,
    accent: tuple[int, int, int] = GOLD,
) -> None:
    _draw_text(draw, (42, 38), title.upper(), fill=accent, font=_font(34, bold=True), bold=True)
    name_font = _fit_font(
        draw, payload.governor_name, max_width=520, size=34, min_size=23, bold=True
    )
    _draw_text(draw, (42, 84), payload.governor_name, fill=TEXT, font=name_font, bold=True)
    context = [payload.display_kvk_label, payload.display_mode]
    if payload.display_camp:
        context.append(payload.display_camp)
    if payload.kingdom:
        context.append(f"Kingdom {payload.kingdom}")
    context_text = "  |  ".join(context)
    font = _fit_font(draw, context_text, max_width=820, size=20, min_size=15, bold=True)
    _draw_text(draw, (42, 126), context_text, fill=MUTED, font=font, bold=True)


def _draw_small_progress(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    percent: float | None,
    color: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle((x, y, x + w, y + 15), radius=7, fill=(57, 65, 81, 220))
    pct = max(0.0, min(float(percent or 0.0), 100.0))
    fill_w = int(w * pct / 100.0)
    if fill_w:
        draw.rounded_rectangle((x, y, x + fill_w, y + 15), radius=7, fill=color)


def _rank_value(value: int | str | None) -> str:
    if value in (None, ""):
        return "N/A"
    return f"#{value}"


def _main_rank_value(payload: KvkStatsCardPayload) -> str:
    return _rank_value(payload.kvk_rank)


def _overall_kvk_rank_value(payload: KvkStatsCardPayload) -> str:
    if payload.overall_kvk_rank in (None, 0):
        return "TBC"
    return _rank_value(payload.overall_kvk_rank)


def _overall_kvk_rank_context(payload: KvkStatsCardPayload) -> str | None:
    if payload.overall_kvk_rank in (None, 0):
        return None
    parts: list[str] = []
    if payload.overall_kvk_total_governors:
        parts.append(f"Total {_compact(payload.overall_kvk_total_governors).lower()}")
    if payload.overall_kvk_top_percent is not None:
        parts.append(f"Top {_pct(payload.overall_kvk_top_percent)}")
    if not parts:
        return None
    return " / ".join(parts)


def _pass_window(payload: KvkStatsCardPayload, pass_no: int) -> tuple[int, int]:
    return (
        int(payload.pass_stats.get(f"Pass {pass_no} Kills", 0) or 0),
        int(payload.pass_stats.get(f"Pass {pass_no} Deads", 0) or 0),
    )


def _draw_scaled_progress(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    title: str,
    value_text: str,
    percent: float | None,
    color: tuple[int, int, int],
) -> None:
    ticks = _progress_scale(percent)
    scale_max = ticks[-1]
    label = f"{title}  {value_text}"
    font = _fit_font(draw, label, max_width=w, size=23, min_size=16, bold=True)
    _draw_text(draw, (x, y), label, fill=color, font=font, bold=True)
    bar_y = y + 40
    draw.rounded_rectangle((x, bar_y, x + w, bar_y + 18), radius=8, fill=(66, 58, 48))
    pct = max(0.0, min(float(percent or 0.0), float(scale_max)))
    fill_w = int(w * pct / scale_max)
    if fill_w:
        draw.rounded_rectangle((x, bar_y, x + fill_w, bar_y + 18), radius=8, fill=color)
    tick_font = _font(15, bold=True)
    for tick in ticks:
        tick_x = x + int(w * tick / scale_max)
        draw.line((tick_x, bar_y - 4, tick_x, bar_y + 22), fill=(255, 255, 255, 150), width=2)
        tick_label = f"{tick}%"
        label_width = _text_width(draw, tick_label, tick_font, bold=True)
        label_x = max(x, min(x + w - label_width, tick_x - label_width // 2))
        _draw_text(draw, (label_x, bar_y + 27), tick_label, fill=MUTED, font=tick_font, bold=True)


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
        label_width = _text_width(draw, tick_label, tick_font, bold=True)
        label_x = max(x, min(x + w - label_width, tick_x - label_width // 2))
        _draw_text(draw, (label_x, y + 26), tick_label, fill=MUTED, font=tick_font, bold=True)
    label = f"Kills Target Progress  {_pct(payload.kill_progress.percent)} - {payload.kill_progress.quote}"
    font = _fit_font(draw, label, max_width=780, size=23, min_size=16, bold=True)
    _draw_text(draw, (40, 504), label, fill=color, font=font, bold=True)


def render_kvk_stats_card(
    payload: KvkStatsCardPayload, *, avatar_bytes: bytes | None = None
) -> RenderedKvkStatsCard | None:
    background_path = _background_for_mode(payload.kvk_name)
    if background_path is None:
        return None

    background = _load_background(background_path)
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

    rank_center_x = 995
    _draw_centered_text(
        draw,
        center_x=rank_center_x,
        y=56,
        text="\U0001f3c6 RANK",
        fill=TEXT,
        font=_font(25, bold=True),
        bold=True,
    )
    rank_value = _main_rank_value(payload)
    _draw_centered_text(
        draw,
        center_x=rank_center_x,
        y=88,
        text=rank_value,
        fill=TEXT,
        font=_font(50, bold=True),
        bold=True,
    )

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
        sub="Higher is better" if payload.tanking_score_percent is not None else "Not enough data",
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


def render_kvk_more_stats_card(payload: KvkStatsCardPayload) -> RenderedKvkStatsCard | None:
    background_path = _background_for_mode(payload.kvk_name)
    if background_path is None:
        return None

    background = _load_background(background_path)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    odraw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=22, fill=(0, 0, 0, 95))
    odraw.rectangle((0, 0, WIDTH, 168), fill=(0, 0, 0, 95))
    canvas = Image.alpha_composite(background, overlay)
    draw = ImageDraw.Draw(canvas, "RGBA")

    _draw_card_header(draw, payload, title="More KVK Stats")

    rank_center_x = 1008
    rank_label = "KVK OVERALL RANK"
    rank_font = _fit_font(draw, rank_label, max_width=265, size=22, min_size=16, bold=True)
    _draw_centered_text(
        draw,
        center_x=rank_center_x,
        y=50,
        text=rank_label,
        fill=TEXT,
        font=rank_font,
        bold=True,
    )
    _draw_centered_text(
        draw,
        center_x=rank_center_x,
        y=82,
        text=_overall_kvk_rank_value(payload),
        fill=TEXT,
        font=_fit_font(
            draw,
            _overall_kvk_rank_value(payload),
            max_width=160,
            size=46,
            min_size=30,
            bold=True,
        ),
        bold=True,
    )
    rank_context = _overall_kvk_rank_context(payload)
    if rank_context:
        _draw_centered_text(
            draw,
            center_x=rank_center_x,
            y=128,
            text=rank_context,
            fill=GOLD,
            font=_fit_font(draw, rank_context, max_width=280, size=20, min_size=15, bold=True),
            bold=True,
        )

    col_w = 230
    col_x = (45, 315, 585, 855)
    pass_y = 205
    pass_values = [
        f"{_compact(kills)} / {_compact(deads)}"
        for pass_no in (4, 6, 7, 8)
        for kills, deads in [_pass_window(payload, pass_no)]
    ]
    pass_value_font = _fit_shared_font(
        draw, pass_values, max_width=col_w, size=44, min_size=29, bold=True
    )
    for idx, pass_no in enumerate((4, 6, 7, 8)):
        kills, deads = _pass_window(payload, pass_no)
        _metric(
            draw,
            x=col_x[idx],
            y=pass_y,
            w=col_w,
            title=f"Pass {pass_no}",
            value=f"{_compact(kills)} / {_compact(deads)}",
            color=GREEN if kills else MUTED,
            sub="Kills / Deads",
            value_font=pass_value_font,
        )

    row2_y = 345
    _metric(
        draw,
        x=col_x[0],
        y=row2_y,
        w=col_w,
        title="Pre-KVK",
        value=(
            f"{payload.prekvk_rank} / {_compact(payload.prekvk_points)}"
            if payload.prekvk_rank
            else f"N/A / {_compact(payload.prekvk_points)}"
        ),
        color=BLUE if payload.prekvk_rank else MUTED,
        sub="Rank / Points",
    )
    _metric(
        draw,
        x=col_x[1],
        y=row2_y,
        w=col_w,
        title="Honor",
        value=(
            f"{payload.honor_rank} / {_compact(payload.honor_points)}"
            if payload.honor_rank
            else f"N/A / {_compact(payload.honor_points)}"
        ),
        color=GOLD if payload.honor_rank else MUTED,
        sub="Rank / Points",
    )

    dkp_label = f"{_compact(payload.dkp)} / {_compact(payload.dkp_target)} | {_pct(payload.dkp_target_percent)}"
    _draw_scaled_progress(
        draw,
        x=40,
        y=498,
        w=760,
        title="DKP Progress",
        value_text=dkp_label,
        percent=payload.dkp_target_percent,
        color=GOLD,
    )

    updated = f"Last updated {payload.last_refresh or 'unknown'}"
    footer_font = _fit_font(draw, updated, max_width=365, size=20, min_size=15, bold=True)
    _draw_text(draw, (775, 596), updated, fill=MUTED, font=footer_font, bold=True)
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedKvkStatsCard(
        filename=f"kvk_more_stats_{payload.governor_id}.png", image_bytes=buf
    )
