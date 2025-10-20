# embed_kvk_history.py
from __future__ import annotations

import discord

from constants import CUSTOM_AVATAR_URL

# Optional styling constants (safe fallbacks if missing)
try:
    from constants import INFO_COLOR
except Exception:
    INFO_COLOR = 0x2B6CB0  # calm blue fallback


def make_history_embed(
    user: discord.User | discord.Member,
    overlay_labels: dict[int, str],  # Gov_ID -> label
    left_metrics: list[str],
    right_metric: str | None,
    table_preview_rows: list[dict],
    title_suffix: str = "",
) -> tuple[discord.Embed, discord.File | None, discord.File | None]:
    """
    Returns (embed, chart_file, csv_file) where the files are placeholders (None).
    The actual image/CSV files are created and attached by the View.

    table_preview_rows: list of dicts with keys [KVK_NO, label, metric, value].
    """
    title = "KVK History"
    if title_suffix:
        title += f" — {title_suffix}"

    emb = discord.Embed(title=title, color=INFO_COLOR)

    # Author & styling to match your other embeds
    try:
        emb.set_author(
            name=getattr(user, "display_name", str(user)),
            icon_url=getattr(getattr(user, "display_avatar", None), "url", discord.Embed.Empty),
        )
    except Exception:
        pass

    if CUSTOM_AVATAR_URL:
        try:
            emb.set_thumbnail(url=CUSTOM_AVATAR_URL)
        except Exception:
            pass

    # Table preview (first ~10 lines, trimmed to fit field length limits)
    if table_preview_rows:
        lines = []
        for row in table_preview_rows[:10]:
            lines.append(f"KVK {row['KVK_NO']}: {row['label']} — {row['metric']}: {row['value']}")
        preview_text = "\n".join(lines)

        # Field value should stay under ~1024 chars (leave headroom for code fences)
        max_inner = 980
        if len(preview_text) > max_inner:
            preview_text = preview_text[: max_inner - 3] + "..."

        emb.add_field(name="Preview", value=f"```\n{preview_text}\n```", inline=False)

    # Files are provided by the caller (the View)
    chart_file: discord.File | None = None
    csv_file: discord.File | None = None

    # Helpful footer
    emb.set_footer(
        text="Tip: use the buttons to change metrics, accounts, or open the custom picker."
    )

    return emb, chart_file, csv_file
