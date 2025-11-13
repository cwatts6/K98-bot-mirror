# embed_player_profile.py
from __future__ import annotations

import io
import os
from typing import Any

import discord

try:
    from governor_registry import (
        get_discord_name_for_governor,  # used in build_player_profile_embed
    )
except Exception:

    def get_discord_name_for_governor(_):
        return None


try:
    from constants import CUSTOM_AVATAR_PATH, CUSTOM_AVATAR_URL
except Exception:
    CUSTOM_AVATAR_PATH = None  # type: ignore
    CUSTOM_AVATAR_URL = None  # type: ignore


# Optional deps
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

try:
    import matplotlib.pyplot as plt

    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

try:
    import aiohttp

    HAVE_AIOHTTP = True
except Exception:
    HAVE_AIOHTTP = False

# Optional header banner (MUST be a direct image URL: e.g., https://i.ibb.co/.../banner.png)
try:
    from constants import PROFILE_HEADER_BANNER_PATH  # type: ignore
except Exception:
    PROFILE_HEADER_BANNER_PATH = None

try:
    from constants import PROFILE_HEADER_BANNER_URL  # type: ignore
except Exception:
    PROFILE_HEADER_BANNER_URL = None

try:
    from constants import CUSTOM_AVATAR_PATH, CUSTOM_AVATAR_URL
except Exception:
    CUSTOM_AVATAR_PATH = None  # type: ignore
    CUSTOM_AVATAR_URL = None  # type: ignore


# ----------------- small helpers -----------------


def _fmt_short(n: Any) -> str:
    try:
        x = float(n)
    except Exception:
        return "—" if n in (None, "", []) else str(n)
    neg = x < 0
    x = abs(x)
    for unit in ("", "K", "M", "B", "T"):
        if x < 1000:
            s = f"{x:.1f}".rstrip("0").rstrip(".")
            return f"{'-' if neg else ''}{s}{unit}"
        x /= 1000.0
    return f"{'-' if neg else ''}{x:.1f}P"


def _kvk_color_hex(pct: float | None) -> str:
    pct = pct or 0.0
    if pct < 50:
        return "#D9534F"  # red
    if pct < 75:
        return "#F0AD4E"  # amber
    return "#5CB85C"  # green


def _hex_to_rgba(hex_str: str, a: int = 255) -> tuple[int, int, int, int]:
    h = hex_str.strip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def _fmt(n: Any) -> str:
    try:
        if isinstance(n, (int, float)) and n is not None:
            return f"{int(n):,}"
        if isinstance(n, str) and n.strip().isdigit():
            return f"{int(n):,}"
    except Exception:
        pass
    return "—" if n in (None, "", []) else str(n)


def _kvk_summary_lines(kvk_slices: list[dict[str, Any]]) -> str:
    if not kvk_slices:
        return "No recent KVK history."
    items = sorted(kvk_slices, key=lambda x: x.get("KVK") or 0, reverse=True)[:3]
    lines = []
    for d in items:
        kvk = d.get("KVK")
        rank = d.get("Rank")
        pct = d.get("Percent")
        rank_s = f"#{rank}" if rank is not None else "–"
        pct_s = "–" if pct is None else f"{pct:.0f}%"
        lines.append(f"KVK {kvk}: Kill Rank {rank_s} • {pct_s}")
    return "\n".join(lines)


def _nice_ylim(values: list[float]) -> int:
    import math

    if not values:
        return 100
    y_max = max(values + [100.0])
    step = 25
    return max(100, int(math.ceil((y_max * 1.10) / step)) * step)


# ------------- text fitting (shrink + wrap/ellipsis) -------------


def _wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int = 2):
    words = (str(text) or "").split()
    if not words:
        return [""]

    lines, cur = [], ""
    i, n = 0, len(words)
    truncated = False

    while i < n:
        w = words[i]
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
            i += 1
        else:
            if cur:
                lines.append(cur)
            else:
                # very long single token: hard trim
                chunk = w
                while draw.textlength(chunk, font=font) > max_width and len(chunk) > 1:
                    chunk = chunk[:-1]
                lines.append(chunk)
                w = w[len(chunk) :]
                if w:
                    words[i] = w
                    continue
                i += 1
            cur = ""
            if len(lines) >= max_lines - 1:
                truncated = True
                break

    if cur:
        lines.append(cur)

    # If we exited early (truncated) or still have leftover words, ellipsize the last line.
    if lines:
        leftover = truncated or (i < n)
        last = lines[-1]
        if leftover:
            last += "…"
        while draw.textlength(last, font=font) > max_width and len(last) > 1:
            last = last[:-2] + "…" if last.endswith("…") else last[:-1] + "…"
        lines[-1] = last

    return lines[:max_lines]


def _fit_text(
    draw, text, font_loader, *, start_size: int, min_size: int, max_width: int, bold: bool = True
):
    """Shrink single-line text until it fits width."""
    size = start_size
    while size >= min_size:
        f = font_loader(size, bold=bold)
        if draw.textlength(str(text), font=f) <= max_width:
            return f, str(text)
        size -= 1
    f = font_loader(min_size, bold=bold)
    # ellipsize if still too wide
    t, ell = str(text), "…"
    while draw.textlength(t + ell, font=f) > max_width and len(t) > 1:
        t = t[:-1]
    return f, (t + ell)


def _fit_multiline(
    draw,
    text,
    font_loader,
    *,
    start_size: int,
    min_size: int,
    max_width: int,
    max_lines: int,
    bold: bool = True,
    prefer_two_lines: bool = True,  # NEW: prefer wrapping over extreme shrink
):
    txt = str(text or "")
    # Heuristic: if the text starts wider than a line and we have spaces + max_lines>1,
    # prefer a 2-line layout instead of shrinking to a tiny single line.
    want_two = prefer_two_lines and (max_lines > 1) and (" " in txt)

    size = start_size
    # Precompute whether it overflows at the starting size
    try_font = font_loader(start_size, bold=bold)
    started_overflow = draw.textlength(txt, font=try_font) > max_width

    while size >= min_size:
        f = font_loader(size, bold=bold)
        lines = _wrap_to_width(draw, txt, f, max_width, max_lines=max_lines)

        # If we wanted 2 lines and it came back as 1 line while it *did* overflow at start,
        # nudge it to wrap (keeps the font larger and the text more readable).
        if want_two and started_overflow and len(lines) == 1:
            # Greedy split: push as many words as fit into line 1, rest in line 2
            words = txt.split()
            l1, i = [], 0
            while i < len(words):
                probe = (" ".join(l1 + [words[i]])).strip()
                if draw.textlength(probe, font=f) <= max_width:
                    l1.append(words[i])
                    i += 1
                else:
                    break
            l2 = " ".join(words[i:]).strip()
            if l2:
                lines = [" ".join(l1).strip(), l2]

        if len(lines) <= max_lines and all(
            draw.textlength(ln, font=f) <= max_width for ln in lines
        ):
            return f, lines

        size -= 1

    # Fallback at min size
    f = font_loader(min_size, bold=bold)
    return f, _wrap_to_width(draw, txt, f, max_width, max_lines=max_lines)


# ----------------- chart (natural size; font sizes match card) -----------------


async def _make_kvk_chart_file(kvk_slices: list[dict[str, Any]]) -> discord.File | None:
    if not HAVE_MPL or not kvk_slices:
        return None

    data = sorted(kvk_slices[:4], key=lambda x: x.get("KVK") or 0)  # left→right old→new
    labels = [f"KVK {d.get('KVK')}" for d in data]
    perc = [float(d.get("Percent") or 0.0) for d in data]
    ranks = [d.get("Rank") for d in data]
    colors = [_kvk_color_hex(p) for p in perc]

    # Slightly larger so typography matches card labels/values (~20px)
    fig, ax = plt.subplots(figsize=(7.6, 4.0), dpi=200)
    bars = ax.bar(labels, perc, color=colors)

    ax.set_ylim(0, _nice_ylim(perc))
    ax.set_ylabel("Kill target achieved (%)", fontsize=18)
    ax.set_title("Kill % by KVK (rank • %)", pad=10, fontsize=20)
    ax.tick_params(axis="both", labelsize=16)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # in-bar labels (match card value size ~18)
    y_top = ax.get_ylim()[1]
    for rect, p, r in zip(bars, perc, ranks, strict=False):
        lbl = f"{(str(r) if r is not None else '–')} • {int(round(p))}%"
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            min(p, y_top) - (y_top * 0.05),
            lbl,
            ha="center",
            va="top",
            fontsize=18,
            color="white",
            fontweight="bold",
        )

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return discord.File(buf, filename="kvk_chart.png")


# ----------------- main entry -----------------


async def build_player_profile_embed(
    interaction: discord.Interaction,
    data: dict[str, Any],
    *,
    card_scale: float = 1.35,  # affects file quality, not preview size
) -> tuple[discord.File | None, discord.Embed, discord.File | None]:

    avatar_url = CUSTOM_AVATAR_URL or None

    gov_id = data.get("GovernorID")
    gov_name = (data.get("GovernorName") or str(gov_id)).strip()
    alliance = (data.get("Alliance") or "—").strip()
    status = data.get("Status") or "—"

    # NEW: look up the player's Discord name from the registry (fallback to Unknown)
    player_discord_name = get_discord_name_for_governor(str(gov_id)) or "Unknown"

    kvk_slices = data.get("KVK") or []

    # Render the card (chart is pasted inside)
    card_file = await _render_hero_card(
        data, player_discord_name, avatar_url, scale=card_scale, kvk_slices=kvk_slices
    )
    chart_file = None  # chart lives inside the card now

    # ===== Title with Governor ID =====
    embed = discord.Embed(
        title=f"{gov_name} ** ID:** {gov_id}]",  # ID in heading
        description=f"**Discord:** {player_discord_name}\n**Alliance:** {alliance}\n**Status:** {status}",
        colour=discord.Colour.blurple(),
    )
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    # --- Compact fields, but easier to read (multi-line) ---

    # Location string (two lines)
    xy = "—"
    if data.get("X") is not None and data.get("Y") is not None:
        xy = f"X: {_fmt(data['X'])} Y: {_fmt(data['Y'])}"

    # Power label: rank first, then value; add CH on the next line
    power_val = _fmt_short(data.get("Power"))
    power_rank = data.get("PowerRank")
    power_first_line = f"Rank:{power_rank} Power:{power_val}" if power_rank else power_val
    power_block = f"{power_first_line}\nCH {_fmt(data.get('CityHallLevel'))}"

    # Row 1 (two columns)
    embed.add_field(name="Power / CH", value=power_block, inline=True)
    embed.add_field(name="Location", value=xy, inline=True)

    # Row 2 (stacked list, easier to scan)
    totals_block = "\n".join(
        [
            f"Kills {_fmt_short(data.get('Kills'))} : Deads {_fmt_short(data.get('Deads'))}",
            # f"Deads {_fmt_short(data.get('Deads'))}",
            f"RSS {_fmt_short(data.get('RSS_Gathered'))} : Helps {_fmt_short(data.get('Helps'))}",
            # f"Helps {_fmt_short(data.get('Helps'))}",
        ]
    )
    embed.add_field(name="Totals", value=totals_block, inline=False)

    # Row 3 (two columns again)
    forts_total = data.get("FortsTotal") or (
        (data.get("FortsStarted") or 0) + (data.get("FortsJoined") or 0)
    )
    forts_block = f"Rank: {_fmt(data.get('FortsRank'))} Total: {_fmt(forts_total)}"

    first_scan = (str(data.get("FirstScanDate") or "—"))[:10]
    last_scan = (str(data.get("LastScanDate") or "—"))[:10]
    offline_days = int(data.get("OfflineDaysOver30") or 0)
    scans_lines = [f"First {first_scan}", f"Last {last_scan}"]
    if offline_days > 0:
        scans_lines.append(f"Offline: {_fmt(offline_days)}d")
    scans_block = "\n".join(scans_lines)

    embed.add_field(name="Forts Rank / Total", value=forts_block, inline=True)
    embed.add_field(name="Scans", value=scans_block, inline=True)

    # KVK stays multi-line
    embed.add_field(
        name="KVK Performance (last 3)", value=_kvk_summary_lines(kvk_slices), inline=False
    )

    if card_file:
        embed.set_image(url=f"attachment://{card_file.filename}")

        return card_file, embed, chart_file


# ----------------- hero card (PIL) -----------------


async def _render_hero_card(
    data: dict[str, Any],
    player_discord_name: str,
    avatar_url: str | None,
    *,
    scale: float = 1.0,
    kvk_slices: list[dict[str, Any]] | None = None,
) -> discord.File | None:
    if not HAVE_PIL:
        return None

    S = lambda x: int(round(x * scale))

    # Canvas + card
    W, H = S(1200), S(1560)
    bg = Image.new("RGBA", (W, H), (32, 35, 42, 255))
    card_w, card_h = W - S(80), H - S(120)
    card = Image.new("RGBA", (card_w, card_h), (242, 243, 245, 255))
    draw = ImageDraw.Draw(card)

    # Soft shadow
    shadow = Image.new("RGBA", (card_w + S(40), card_h + S(40)), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (0, 0, shadow.width - 1, shadow.height - 1), radius=S(28), fill=(0, 0, 0, 60)
    )
    bg.paste(shadow, (S(20), S(40)), shadow)

    # Header
    header_h = S(300)
    header = Image.new("RGBA", (card.width - S(60), header_h), (60, 64, 90, 255))
    try:
        header = header.filter(ImageFilter.GaussianBlur(radius=0))
    except Exception:
        pass
    mask = Image.new("L", header.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, header.size[0], header.size[1]), radius=S(24), fill=255
    )
    header.putalpha(mask)
    card.paste(header, (S(30), S(30)), header)

    # === Full-bleed header banner (cover fit) ===
    def _cover_fit(img: Image.Image, tw: int, th: int) -> Image.Image:
        """Resize img to cover target (tw x th) and center-crop the overflow."""
        iw, ih = img.width, img.height
        if iw == 0 or ih == 0:
            return img
        scale = max(tw / iw, th / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        img = img.resize((nw, nh), resample=Image.BICUBIC)
        # center crop
        left = (nw - tw) // 2
        top = (nh - th) // 2
        return img.crop((left, top, left + tw, top + th))

    banner_img = None
    try:
        if PROFILE_HEADER_BANNER_PATH and os.path.exists(PROFILE_HEADER_BANNER_PATH):
            banner_img = Image.open(PROFILE_HEADER_BANNER_PATH).convert("RGBA")
        elif PROFILE_HEADER_BANNER_URL and HAVE_AIOHTTP:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as sess:
                async with sess.get(PROFILE_HEADER_BANNER_URL, allow_redirects=True) as resp:
                    if resp.status == 200:
                        raw = await resp.read()
                        try:
                            banner_img = Image.open(io.BytesIO(raw)).convert("RGBA")
                        except Exception:
                            banner_img = None
    except Exception:
        banner_img = None

    if banner_img is not None:
        # Size of the header panel (already created above)
        header_w = card.width - S(60)
        # Fit + crop to cover
        banner_cover = _cover_fit(banner_img, header_w, header_h)
        # Optional: subtle dark overlay for text contrast
        overlay = Image.new("RGBA", (header_w, header_h), (0, 0, 0, 70))
        banner_cover = Image.alpha_composite(banner_cover, overlay)

        # Apply same rounded mask as header
        mask_full = Image.new("L", (header_w, header_h), 0)
        ImageDraw.Draw(mask_full).rounded_rectangle(
            (0, 0, header_w, header_h), radius=S(24), fill=255
        )
        # Paste the image into the header region
        card.paste(banner_cover, (S(30), S(30)), mask_full)

    # Fonts
    def load_font(size, bold=False):
        candidates = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
        ]
        for name in candidates:
            try:
                return ImageFont.truetype(name, S(size))
            except Exception:
                continue
        return ImageFont.load_default()

    f_title = load_font(44, bold=True)
    f_body = load_font(22)
    f_label = load_font(20)
    f_val = load_font(32, bold=True)

    # ===== Title on banner (bottom-left) =====
    gov_name = (data.get("GovernorName") or str(data.get("GovernorID"))).strip()
    tb = draw.textbbox((0, 0), gov_name, font=f_title)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]

    # header area starts at (S(30), S(30)) with size (card.width - S(60), header_h)
    title_x = S(30) + S(24)  # left padding inside banner
    title_y = S(30) + header_h - th - S(22)  # bottom padding inside banner
    draw.text(
        (title_x, title_y),
        gov_name,
        font=f_title,
        fill=(255, 255, 255, 255),
        stroke_width=S(2),  # subtle outline for contrast
        stroke_fill=(0, 0, 0, 140),
    )

    # ===== Status pill (pin to top-right of banner) =====
    status = data.get("Status") or "—"
    pill_w, pill_h = S(260), S(48)
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(pill)
    pdraw.rounded_rectangle((0, 0, pill_w, pill_h), radius=S(24), fill=(230, 220, 255, 230))
    bb = pdraw.textbbox((0, 0), f"Status: {status}", font=f_label)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pdraw.text(
        ((pill_w - tw) // 2, (pill_h - th) // 2 - S(1)),
        f"Status: {status}",
        font=f_label,
        fill=(60, 20, 100, 255),
    )

    # position inside the banner with padding
    pill_x = S(30) + (card.width - S(60)) - pill_w - S(24)
    pill_y = S(30) + header_h - pill_h - S(16)  # bottom-right inside banner
    card.paste(pill, (pill_x, pill_y), pill)

    # ===== Avatar (disabled by default) =====
    SHOW_AVATAR = globals().get("SHOW_PROFILE_AVATAR_IN_CARD", False)
    if SHOW_AVATAR:
        av = None
        try:
            if CUSTOM_AVATAR_PATH and os.path.exists(CUSTOM_AVATAR_PATH):
                av = Image.open(CUSTOM_AVATAR_PATH).convert("RGBA")
            elif CUSTOM_AVATAR_URL and HAVE_AIOHTTP:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(CUSTOM_AVATAR_URL) as resp:
                        if resp.status == 200:
                            av = Image.open(io.BytesIO(await resp.read())).convert("RGBA")
        except Exception:
            av = None

        if av is not None:
            av = av.resize((S(120), S(120)))
            m = Image.new("L", (S(120), S(120)), 0)
            ImageDraw.Draw(m).ellipse((0, 0, S(120), S(120)), fill=255)
            av.putalpha(m)
            # place it below the banner if you ever enable it
            card.paste(av, (S(50), S(350)), av)

    # ---- Stats grid (Discord Name shrinks, Forts wraps+shrinks) ----
    BOX_W = S(320)
    BOX_H = S(118)
    COL_GAP = S(24)
    STEP_Y = S(124)

    def box(x, y, label, value, shrink=False, wrap_lines=1):
        draw.rounded_rectangle(
            (x, y, x + BOX_W, y + BOX_H),
            radius=S(16),
            fill=(255, 255, 255, 255),
            outline=(225, 228, 234, 255),
            width=S(1),
        )
        draw.text((x + S(16), y + S(12)), label, font=f_label, fill=(90, 95, 110, 255))

        max_w = BOX_W - S(32)
        y_val = y + S(54)

        if shrink and wrap_lines > 1:
            f_fit, lines = _fit_multiline(
                draw,
                value,
                lambda s, bold=True: load_font(s, bold=bold),
                start_size=34,
                min_size=12,
                max_width=max_w,
                max_lines=wrap_lines,
                bold=True,
                prefer_two_lines=True,
            )
            lh = f_fit.size + S(2)
            for i, ln in enumerate(lines[:wrap_lines]):
                draw.text((x + S(16), y_val + i * lh), ln, font=f_fit, fill=(22, 25, 28, 255))

        elif shrink:
            f_fit, txt = _fit_text(
                draw,
                value,
                lambda s, bold=True: load_font(s, bold=bold),
                start_size=34,
                min_size=12,
                max_width=max_w,
                bold=True,
            )
            draw.text((x + S(16), y_val), txt, font=f_fit, fill=(22, 25, 28, 255))

        elif wrap_lines > 1:
            lines = _wrap_to_width(draw, value, f_val, max_w, max_lines=wrap_lines)
            lh = f_val.size + S(2)
            for i, ln in enumerate(lines):
                draw.text((x + S(16), y_val + i * lh), ln, font=f_val, fill=(22, 25, 28, 255))

        else:
            draw.text((x + S(16), y_val), value, font=f_val, fill=(22, 25, 28, 255))

    start_x, row_y = S(40), S(360)

    box(start_x, row_y, "Governor Name", gov_name)
    box(
        start_x + BOX_W + COL_GAP,
        row_y,
        "Discord Name",
        player_discord_name,
        shrink=True,
        wrap_lines=2,
    )
    box(start_x + (BOX_W + COL_GAP) * 2, row_y, "Governor ID", str(data.get("GovernorID")))

    row_y += STEP_Y
    xy = "—"
    if data.get("X") is not None and data.get("Y") is not None:
        xy = f"X: {_fmt(data['X'])} • Y: {_fmt(data['Y'])}"
    box(start_x, row_y, "Location", xy)
    box(start_x + BOX_W + COL_GAP, row_y, "Power", _fmt_short(data.get("Power")))
    box(start_x + (BOX_W + COL_GAP) * 2, row_y, "City Hall", _fmt(data.get("CityHallLevel")))

    row_y += STEP_Y
    box(start_x, row_y, "Kills", _fmt_short(data.get("Kills")))
    box(start_x + BOX_W + COL_GAP, row_y, "Deads", _fmt_short(data.get("Deads")))
    box(start_x + (BOX_W + COL_GAP) * 2, row_y, "Helps", _fmt(data.get("Helps")))

    row_y += STEP_Y
    forts_total = data.get("FortsTotal") or (
        (data.get("FortsStarted") or 0) + (data.get("FortsJoined") or 0)
    )
    forts = f"Rank: {_fmt(data.get('FortsRank'))} • Total: {_fmt(forts_total)} (all-time)"
    box(start_x, row_y, "Forts", forts, shrink=True)
    box(start_x + BOX_W + COL_GAP, row_y, "RSS Gathered", _fmt_short(data.get("RSS_Gathered")))
    box(start_x + (BOX_W + COL_GAP) * 2, row_y, "Alliance", (data.get("Alliance") or "—").strip())

    # move below last row
    last_row_bottom = row_y + BOX_H
    row_y = last_row_bottom + S(28)

    # ---- KVK chart panel (align with 3-column grid, natural size, scale down only) ----
    if HAVE_MPL and kvk_slices:
        try:
            chart_file = await _make_kvk_chart_file(kvk_slices)
            if chart_file:
                chart_img = Image.open(chart_file.fp).convert("RGBA")

                # Panel aligned to boxes (same left/right edges)
                panel_left = start_x
                panel_w = BOX_W * 3 + COL_GAP * 2
                panel_pad = S(18)

                # room for caption below
                max_panel_h = card.height - row_y - S(80)
                panel_h = min(max_panel_h, S(360))
                panel_h = max(panel_h, S(260))

                panel = Image.new("RGBA", (panel_w, panel_h), (255, 255, 255, 255))
                pdraw = ImageDraw.Draw(panel)
                pdraw.rounded_rectangle(
                    (0, 0, panel.width - 1, panel.height - 1),
                    radius=S(16),
                    outline=(225, 228, 234, 255),
                    fill=(255, 255, 255, 255),
                    width=S(1),
                )

                # Natural chart size — only scale DOWN to fit
                avail_w = panel.width - panel_pad * 2
                avail_h = panel.height - panel_pad * 2
                ratio = min(1.0, min(avail_w / chart_img.width, avail_h / chart_img.height))
                new_w = int(chart_img.width * ratio)
                new_h = int(chart_img.height * ratio)
                if ratio < 1.0:
                    chart_img = chart_img.resize((new_w, new_h), resample=Image.BICUBIC)

                # Center inside panel
                cx = (panel.width - chart_img.width) // 2
                cy = (panel.height - chart_img.height) // 2
                panel.paste(chart_img, (cx, cy), chart_img)

                card.paste(panel, (panel_left, row_y), panel)
                row_y += panel_h  # advance cursor after panel
        except Exception:
            pass

    # caption (always under graph)
    row_y += S(16)
    draw.text(
        (start_x, row_y), "Profile generated from latest scan", font=f_body, fill=(90, 95, 110, 255)
    )
    row_y += f_body.size + S(20)  # bottom padding

    # Compose & crop bottom whitespace dynamically
    used_card_height = min(card.height, row_y + S(10))
    base_h = S(60) + used_card_height + S(30)  # top margin + content + bottom margin
    base = Image.new("RGBA", (W, base_h), (32, 35, 42, 255))
    # Re-use shadow & card
    base.paste(shadow, (S(20), S(40)), shadow)
    base.paste(card.crop((0, 0, card.width, used_card_height)), (S(40), S(60)))

    out = io.BytesIO()
    base.save(out, format="PNG")
    out.seek(0)
    return discord.File(out, filename="profile_card.png")
