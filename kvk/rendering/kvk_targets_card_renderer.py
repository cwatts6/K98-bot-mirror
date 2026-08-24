from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core import visual_text
from kvk.models.kvk_targets_card import KvkTargetsCardPayload, RenderedKvkTargetsCard
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
GOLD = (255, 211, 87)
GREEN = (52, 211, 153)
AMBER = (255, 183, 77)
RED = (255, 87, 118)
BLUE = (164, 220, 255)
GRAY = (148, 163, 184)
PURPLE = (168, 85, 247)


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    return visual_text.font(size, bold=bold)


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


def _fit_common_font(
    draw: ImageDraw.ImageDraw,
    values: list[str],
    *,
    max_width: int,
    size: int,
    min_size: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    font = _font(size, bold=bold)
    while size > min_size and any(
        _text_width(draw, value, font, bold=bold) > max_width for value in values
    ):
        size -= 1
        font = _font(size, bold=bold)
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


def _compact(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    val = float(value)
    abs_val = abs(val)
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs_val >= limit:
            return f"{val / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{int(val):,}"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def _metric_color(percent: float | None, has_target: bool) -> tuple[int, int, int]:
    if not has_target or percent is None:
        return GRAY
    if percent >= 100:
        return GOLD
    if percent >= 75:
        return GREEN
    if percent >= 50:
        return AMBER
    return RED


def _metric_type_color(label: str) -> tuple[int, int, int]:
    lowered = label.lower()
    if "kill" in lowered:
        return GREEN
    if "dead" in lowered:
        return RED
    if "dkp" in lowered:
        return PURPLE
    if "acclaim" in lowered:
        return GOLD
    return TEXT


def _note_color(payload: KvkTargetsCardPayload) -> tuple[int, int, int]:
    percent = payload.completion_percent
    if percent is None:
        return TEXT
    if percent >= 100:
        return GOLD
    if percent >= 70:
        return GREEN
    if percent >= 40:
        return AMBER
    return RED


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

    draw.ellipse(box, fill=(38, 44, 58, 215), outline=(188, 196, 216), width=3)
    initials = "".join(part[:1] for part in governor_name.split()[:2]).upper() or "K"
    initials_font = _fit_font(draw, initials, max_width=52, size=30, min_size=18, bold=True)
    draw.text((x0 + size / 2, y0 + size / 2), initials, anchor="mm", fill=GOLD, font=initials_font)


def _draw_stat_block(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    title: str,
    value: str,
    color: tuple[int, int, int],
    subtext: str | None = None,
    value_font: ImageFont.ImageFont | None = None,
) -> None:
    title_font = _fit_font(draw, title.upper(), max_width=w, size=21, min_size=15, bold=True)
    _draw_text(draw, (x, y), title.upper(), fill=TEXT, font=title_font, bold=True)
    value_font = value_font or _fit_font(draw, value, max_width=w, size=38, min_size=24, bold=True)
    _draw_text(draw, (x, y + 33), value, fill=color, font=value_font, bold=True)
    if subtext:
        sub_font = _fit_font(draw, subtext, max_width=w, size=18, min_size=13, bold=True)
        _draw_text(draw, (x, y + 76), subtext, fill=MUTED, font=sub_font, bold=True)


def _draw_metric_grid(draw: ImageDraw.ImageDraw, payload: KvkTargetsCardPayload) -> None:
    metrics = list(payload.metrics[:4])
    col_x = (74, 335, 596, 857)
    col_w = 205
    target_values: list[str] = []
    comparison_values: list[str] = []

    for metric in metrics:
        target_value = _compact(metric.target) if metric.has_target else "TBC"
        target_values.append(target_value)

        comparison_value = _compact(metric.current)
        if metric.has_target:
            comparison_value = (
                f"{_compact(metric.current)} / {_compact(metric.target)} / {_pct(metric.percent)}"
            )
        comparison_values.append(comparison_value)

    target_value_font = _fit_common_font(
        draw, target_values, max_width=col_w, size=38, min_size=24, bold=True
    )
    comparison_value_font = _fit_common_font(
        draw, comparison_values, max_width=col_w, size=27, min_size=18, bold=True
    )

    for idx, metric in enumerate(metrics):
        _draw_stat_block(
            draw,
            x=col_x[idx],
            y=238,
            w=col_w,
            title=metric.label,
            value=target_values[idx],
            color=_metric_type_color(metric.label) if metric.has_target else GRAY,
            subtext="Coming next KVK" if metric.note and not metric.has_target else None,
            value_font=target_value_font,
        )

    for idx, metric in enumerate(metrics):
        color = _metric_type_color(metric.label)
        if metric.has_target:
            subtext = "actual / target / %"
        elif metric.note:
            subtext = metric.note
        else:
            subtext = "last KVK value"

        _draw_stat_block(
            draw,
            x=col_x[idx],
            y=374,
            w=col_w,
            title=f"Last KVK {metric.label.replace(' Target', '')}",
            value=comparison_values[idx],
            color=color,
            subtext=subtext,
            value_font=comparison_value_font,
        )


def _draw_empty_state(draw: ImageDraw.ImageDraw, payload: KvkTargetsCardPayload) -> None:
    status_font = _fit_font(
        draw, payload.status_label, max_width=1020, size=44, min_size=28, bold=True
    )
    _draw_text(draw, (82, 277), payload.status_label, fill=GOLD, font=status_font, bold=True)
    detail_font = _fit_font(
        draw, payload.status_detail, max_width=970, size=28, min_size=19, bold=True
    )
    _draw_text(draw, (82, 340), payload.status_detail, fill=TEXT, font=detail_font, bold=True)


def render_kvk_targets_card(
    payload: KvkTargetsCardPayload, *, avatar_bytes: bytes | None = None
) -> RenderedKvkTargetsCard | None:
    background_path = _background_for_mode(payload.kvk_name)
    if background_path is None:
        return None

    background = _load_background(background_path)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    odraw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=22, fill=(0, 0, 0, 82))
    odraw.rectangle((0, 0, WIDTH, 190), fill=(0, 0, 0, 78))
    odraw.rectangle((0, 505, WIDTH, HEIGHT), fill=(0, 0, 0, 96))
    canvas = Image.alpha_composite(background, overlay)
    draw = ImageDraw.Draw(canvas, "RGBA")

    _draw_text(draw, (46, 38), "KVK TARGETS", fill=GOLD, font=_font(36, bold=True), bold=True)
    context_bits = [payload.display_kvk_label, payload.display_mode]
    if payload.display_camp:
        context_bits.append(payload.display_camp)
    if payload.power:
        context_bits.append(f"MM Power {_compact(payload.power)}")
    context = "  |  ".join(context_bits)
    context_font = _fit_font(draw, context, max_width=850, size=21, min_size=15, bold=True)
    _draw_text(draw, (46, 86), context, fill=MUTED, font=context_font, bold=True)

    _draw_avatar(
        canvas,
        draw,
        (50, 125, 130, 205),
        governor_name=payload.governor_name,
        avatar_bytes=avatar_bytes,
    )
    name_font = _fit_font(
        draw, payload.governor_name, max_width=640, size=36, min_size=23, bold=True
    )
    _draw_text(draw, (155, 123), payload.governor_name, fill=TEXT, font=name_font, bold=True)
    _draw_text(draw, (155, 167), str(payload.governor_id), fill=TEXT, font=_font(23, bold=True))

    if payload.metrics:
        _draw_metric_grid(draw, payload)
    else:
        _draw_empty_state(draw, payload)

    action_label = "LAST KVK NOTE"
    _draw_text(draw, (74, 524), action_label, fill=TEXT, font=_font(22, bold=True), bold=True)
    action_font = _fit_font(
        draw, payload.next_action, max_width=970, size=27, min_size=18, bold=True
    )
    _draw_text(
        draw, (74, 558), payload.next_action, fill=_note_color(payload), font=action_font, bold=True
    )

    footer_parts = []
    if payload.last_refreshed:
        footer_parts.append(f"Targets refreshed {payload.last_refreshed}")
    if payload.source_state:
        footer_parts.append(f"State {payload.source_state}")
    footer = "  |  ".join(footer_parts)
    footer_font = _fit_font(draw, footer, max_width=1040, size=17, min_size=13, bold=True)
    footer_x = WIDTH - 52 - _text_width(draw, footer, footer_font, bold=True)
    _draw_text(draw, (footer_x, 610), footer, fill=MUTED, font=footer_font, bold=True)

    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RenderedKvkTargetsCard(
        filename=f"kvk_targets_{payload.governor_id}.png",
        image_bytes=buf,
    )
