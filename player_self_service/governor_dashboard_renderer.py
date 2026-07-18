"""Deterministic premium PNG renderer for the private governor dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

from core import visual_text
from player_self_service.governor_dashboard_models import GovernorDashboardPayload
from utils import fmt_short

WIDTH = 1180
HEIGHT = 760
FILENAME = "governor_dashboard.png"

_BACKGROUND = Path(__file__).resolve().parent.parent / "assets" / "me" / "cards" / "me.png"
_TEXT = (246, 247, 252, 255)
_MUTED = (180, 184, 201, 255)
_GOLD = (238, 190, 92, 255)
_BLUE = (105, 171, 255, 255)
_PANEL = (8, 10, 20, 185)


@dataclass(frozen=True, slots=True)
class RenderedGovernorDashboard:
    filename: str
    image_bytes: bytes
    width: int = WIDTH
    height: int = HEIGHT


def _clean(value: Any, *, missing: str = "N/A") -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    return text or missing


def _compact(value: int | float | None) -> str:
    if value is None or isinstance(value, bool):
        return "N/A"
    try:
        numeric = float(value)
        if abs(numeric) >= 1_000_000_000_000_000:
            return f"{numeric:.2E}".replace("E+", "E")
        value_text = fmt_short(value)
    except (TypeError, ValueError):
        return "N/A"
    value_text = value_text.replace("k", "K")
    if len(value_text) >= 3 and value_text[-1:] in "KMB" and value_text[-3:-1] == ".0":
        value_text = value_text[:-3] + value_text[-1]
    return value_text


def _number(value: int | float | None) -> str:
    if value is None or isinstance(value, bool):
        return "N/A"
    if isinstance(value, int):
        return f"{value:,}"
    try:
        return f"{float(value):,.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "N/A"


def _days(value: float | None) -> str:
    if value is None:
        return "Not recorded"
    return f"{int(round(value)):,}d"


def _legendary(value: float | None) -> str:
    if value is None:
        return "Not recorded"
    return f"{value:,.0f}"


def _location(x: int | None, y: int | None) -> str:
    return f"{x}:{y}" if x is not None and y is not None else "N/A"


def _freshness(value: Any) -> str:
    if value is None:
        return "No recent scan available"
    if isinstance(value, datetime):
        timestamp = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return f"Updated {timestamp:%d %b %Y, %H:%M UTC}"
    return f"Updated {_clean(value, missing='time unavailable')}"


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    *,
    size: int,
    min_size: int,
    width: int,
    fill: tuple[int, int, int, int] = _TEXT,
    bold: bool = False,
) -> None:
    fitted = visual_text.fit_font(
        draw, value, max_width=width, size=size, min_size=min_size, bold=bold
    )
    fitted_value = visual_text.fit_text_to_width(
        draw, value, width=width, base_font=fitted, bold=bold
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


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, radius: int = 16) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=_PANEL, outline=(111, 89, 145, 150), width=1)


def _avatar(canvas: Image.Image, avatar_bytes: bytes | None) -> None:
    box = (67, 61, 302, 296)
    size = box[2] - box[0]
    if avatar_bytes:
        try:
            with Image.open(BytesIO(avatar_bytes)) as source:
                avatar = ImageOps.fit(
                    ImageOps.exif_transpose(source).convert("RGBA"),
                    (size, size),
                    method=Image.Resampling.LANCZOS,
                )
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
            canvas.paste(avatar, (box[0], box[1]), mask)
            return
        except Exception:
            pass
    draw = ImageDraw.Draw(canvas)
    draw.ellipse(box, fill=(10, 12, 24, 235))
    _text(draw, (105, 145), "KD98", size=47, min_size=32, width=160, fill=_GOLD, bold=True)


def _metric(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    *,
    subtle: bool = False,
) -> None:
    _panel(draw, box, radius=13)
    x0, y0, x1, _ = box
    _text(
        draw,
        (x0 + 14, y0 + (20 if subtle else 12)),
        value,
        size=20 if subtle else 35,
        min_size=16 if subtle else 24,
        width=x1 - x0 - 28,
        fill=_MUTED if subtle else _TEXT,
        bold=not subtle,
    )
    _text(draw, (x0 + 14, y0 + 53), label, size=17, min_size=14, width=x1 - x0 - 28, fill=_MUTED)


def render_governor_dashboard(
    payload: GovernorDashboardPayload, *, avatar_bytes: bytes | None = None
) -> RenderedGovernorDashboard:
    """Render the approved self-view payload without Discord, SQL, or network IO."""
    with Image.open(_BACKGROUND) as source:
        canvas = source.convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", canvas.size, (2, 4, 12, 70)))
    _avatar(canvas, avatar_bytes)
    draw = ImageDraw.Draw(canvas, "RGBA")

    identity = payload.identity
    metrics = payload.latest_metrics
    history = payload.historical_highlights
    honours = payload.activity_honours
    inventory = payload.inventory
    self_view = payload.self_view

    _panel(draw, (315, 35, 885, 145), radius=18)
    name = _clean(identity.governor_name, missing=f"Governor {identity.governor_id}")
    _text(draw, (337, 48), name, size=49, min_size=27, width=535, bold=True)
    _text(
        draw,
        (338, 103),
        f"Alliance  {_clean(identity.alliance)}",
        size=22,
        min_size=16,
        width=345,
        fill=_MUTED,
    )
    account = _clean(getattr(self_view, "account_type", None))
    vip = _clean(getattr(self_view, "vip_level_label", None), missing="VIP not set")
    _text(draw, (685, 105), f"{account}  •  {vip}", size=18, min_size=14, width=190, fill=_GOLD)

    _panel(draw, (64, 314, 305, 430), radius=18)
    _text(draw, (91, 328), "GOVERNOR ID", size=18, min_size=15, width=190, fill=_MUTED, bold=True)
    _text(
        draw,
        (87, 359),
        str(identity.governor_id),
        size=37,
        min_size=25,
        width=195,
        fill=_GOLD,
        bold=True,
    )

    profile_box = (920, 65, 1150, 420)
    _panel(draw, profile_box, radius=20)
    profile_rows = (
        ("CIVILISATION", _clean(identity.civilisation)),
        ("LOCATION", _location(identity.location_x, identity.location_y)),
        ("CONDUCT SCORE", _number(payload.profile_status.conduct_score)),
    )
    y = 94
    for label, value in profile_rows:
        _text(draw, (944, y), label, size=16, min_size=13, width=182, fill=_MUTED, bold=True)
        _text(draw, (944, y + 27), value, size=29, min_size=19, width=182, bold=True)
        y += 92
    _text(draw, (944, 366), "LAST LOGIN", size=15, min_size=12, width=182, fill=_MUTED, bold=True)
    _text(draw, (944, 390), "TBC", size=19, min_size=15, width=182, fill=_BLUE, bold=True)

    metric_values = (
        ("POWER", _compact(metrics.power)),
        ("KILL POINTS", _compact(metrics.kill_points)),
        ("HIGHEST ACCLAIM", _compact(history.highest_acclaim)),
        ("DEAD", _compact(metrics.dead)),
        ("HELPS", _compact(metrics.helps)),
        ("HEALED", _compact(metrics.healed)),
    )
    for index, (label, value) in enumerate(metric_values):
        column = index % 3
        row = index // 3
        x0 = 315 + column * 195
        y0 = 164 + row * 112
        _metric(draw, (x0, y0, x0 + 180, y0 + 96), label, value)

    inventory_values = (
        (
            "TOTAL RSS",
            (
                _compact(inventory.total_resources)
                if inventory.total_resources is not None
                else "Not recorded"
            ),
            inventory.total_resources is None,
        ),
        (
            "SPEEDUPS",
            _days(inventory.total_speedup_days),
            inventory.total_speedup_days is None,
        ),
        (
            "MATERIALS",
            _legendary(inventory.total_legendary_materials),
            inventory.total_legendary_materials is None,
        ),
    )
    for index, (label, value, subtle) in enumerate(inventory_values):
        x0 = 315 + index * 195
        _metric(draw, (x0, 388, x0 + 180, 484), label, value, subtle=subtle)

    honour_values = (
        ("ARK JOINED", _number(honours.ark_joined)),
        ("ARK WON", _number(honours.ark_won)),
        ("WIN RATIO", _clean(honours.ark_win_ratio_label)),
        ("NAMED AUTARCH", _number(history.times_named_autarch)),
        ("AUTARCH PARTICIPATED", _number(history.times_autarch_participated)),
    )
    for index, (label, value) in enumerate(honour_values):
        x0 = 88 + index * 207
        _text(draw, (x0, 618), value, size=31, min_size=21, width=175, bold=True)
        _text(draw, (x0, 658), label, size=15, min_size=11, width=175, fill=_MUTED, bold=True)

    _text(
        draw,
        (88, 718),
        _freshness(payload.freshness.updated_at_utc),
        size=15,
        min_size=12,
        width=520,
        fill=_MUTED,
    )
    _text(
        draw,
        (870, 718),
        "KD98 GOVERNOR DASHBOARD",
        size=15,
        min_size=12,
        width=270,
        fill=_GOLD,
        bold=True,
    )

    output = BytesIO()
    try:
        with canvas.convert("RGB") as rendered_canvas:
            rendered_canvas.save(output, format="PNG", optimize=True)
        image_bytes = output.getvalue()
    finally:
        output.close()
        canvas.close()
    return RenderedGovernorDashboard(filename=FILENAME, image_bytes=image_bytes)
