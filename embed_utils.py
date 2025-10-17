# embed_utils.py
from __future__ import annotations  # 🔒 avoid runtime eval of type hints

from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)
import math
import os

# NEW
import aiofiles
import discord
from discord.ui import View
from discord.utils import format_dt

from constants import (
    CUSTOM_AVATAR_URL,
    DOWN_ARROW_EMOJI,
    UP_ARROW_EMOJI,
    VIEW_TRACKING_FILE,
)
from file_utils import read_summary_log_rows
from generate_progress_image import generate_exempt_dial, generate_progress_dial
from utils import format_countdown, utcnow

# --- Emoji & color fallbacks ---
try:
    from constants import (
        DANGER_COLOR,
        INFO_COLOR,
        SUCCESS_COLOR,
        WARN_COLOR,
    )
except Exception:
    INFO_COLOR, SUCCESS_COLOR, WARN_COLOR, DANGER_COLOR = 0x3B82F6, 0x22C55E, 0xF59E0B, 0xEF4444


AUTO_REGENERATE = False  # Optional toggle to regenerate expired embeds


def fmt_short(n: float | None) -> str:
    if n is None:
        return "—"
    try:
        x = float(n)
        if math.isnan(x) or math.isinf(x):
            return "—"
    except Exception:
        return "—"
    sign = "-" if x < 0 else ""
    ax = abs(x)
    if ax >= 1_000_000_000:
        s = f"{ax/1_000_000_000:.2f}B"
    elif ax >= 1_000_000:
        s = f"{ax/1_000_000:.2f}M"
    elif ax >= 1_000:
        s = f"{ax/1_000:.2f}K"
    else:
        s = f"{ax:.0f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return f"{sign}{s}"


def fmt_pct(p: float | None, *, decimals: int = 0) -> str:
    if p is None:
        return "—"
    try:
        v = float(p)
    except Exception:
        return "—"
    out = f"{v:.{decimals}f}%"
    if decimals and out.endswith(".0%"):
        out = out.replace(".0%", "%")
    return out


def fmt_delta(n: float | None) -> str:
    if n is None:
        return "—"
    try:
        v = float(n)
    except Exception:
        return "—"
    if v > 0:
        return f"{UP_ARROW_EMOJI} {fmt_short(v)}"
    if v < 0:
        return f"{DOWN_ARROW_EMOJI} {fmt_short(abs(v))}"
    return "—"


def md_escape(s: str | None) -> str:
    if not s:
        return ""
    for ch in ("*", "_", "`", "~", "|", ">"):
        s = s.replace(ch, f"\\{ch}")
    return s


class LocalTimeButton(discord.ui.Button):
    def __init__(self, custom_id: str = "local_time_toggle"):
        super().__init__(
            label="🕒 Show in My Local Time", style=discord.ButtonStyle.success, custom_id=custom_id
        )
        self.prefix = custom_id.removesuffix("_local_time_toggle")  # ← Extract prefix from ID

    async def callback(self, interaction: discord.Interaction):
        logger.info(f"[BUTTON] {self.custom_id} clicked (prefix: {self.prefix})")
        try:
            embed = self.view.build_local_time_embed()

            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.edit_original_response(embed=embed)
            except discord.NotFound:
                logger.warning("[WARN] Interaction expired — trying followup...")
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception(f"[ERROR] Failed to respond to local time toggle: {e}")
            try:
                await interaction.followup.send("Failed to build local time view.", ephemeral=True)
            except Exception as inner:
                logger.exception(
                    f"[ERROR] Failed to fallback after local time toggle failure: {inner}"
                )


class TargetLookupView(View):
    def __init__(self, matches: list[dict], timeout: float = 60):
        super().__init__(timeout=timeout)
        self.matches = matches

        for entry in matches[:5]:  # Limit to 5 buttons
            label = str(entry.get("GovernorName", ""))[:75]
            custom_id = str(entry.get("GovernorID", ""))
            button = discord.ui.Button(
                label=label,
                custom_id=custom_id,
                style=discord.ButtonStyle.primary,
            )
            button.callback = self.make_callback(custom_id)
            self.add_item(button)

    def make_callback(self, governor_id: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            # Trigger the /mykvktargets command by editing the interaction message
            # This is simulated behavior since buttons can't invoke slash commands directly
            await interaction.followup.send(
                f"📊 Looking up targets for Governor ID `{governor_id}`...", ephemeral=True
            )
            # If your /mykvktargets command is callable as a function:
            from Commands import mykvktargets

            await mykvktargets(interaction, governorid=governor_id)

            # Disable all buttons after click
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)

        return callback


class LocalTimeToggleView(View):
    def __init__(self, events, prefix="default", timeout=None):
        super().__init__(timeout=timeout)
        self.events = events
        self.prefix = prefix  # ✅ Store prefix
        # Defensive: prevent duplicate "_local_time_toggle"
        if not self.prefix.endswith("_local_time_toggle"):
            custom_id = f"{self.prefix}_local_time_toggle"
        else:
            custom_id = self.prefix

        self.add_item(LocalTimeButton(custom_id=custom_id))

    def build_local_time_embed(self):
        if not self.events:
            logger.warning(
                f"[LOCAL TIME EMBED] No events found in view with prefix '{self.prefix}'"
            )
            return discord.Embed(
                title="No events found",
                description="Unable to build local time view. This might be a stale or expired button.",
                color=discord.Color.red(),
            )

        is_single_event = len(self.events) == 1
        if is_single_event:
            embed_title = (
                f"📅 {self.events[0].get('name') or self.events[0].get('title')} – Local Time View"
            )
        else:
            # If all events are altar-type, call it fights; otherwise events.
            types = {(e.get("type") or "").lower() for e in self.events}
            embed_title = (
                "⚔️ Upcoming Fights – Local Time View"
                if types and types.issubset({"altar", "altars"})
                else "📊 Upcoming Events – Local Time View"
            )

        embed = discord.Embed(
            title=embed_title,
            description="These times are shown in **your local time**.",
            color=discord.Color.orange(),
            timestamp=utcnow(),
        )

        if is_single_event:
            # Just show the single event directly
            e = self.events[0]
            label = e.get("name") or e.get("title")
            time_str = format_dt(e["start_time"], style="F")
            embed.add_field(name=label, value=time_str, inline=False)
        else:
            # Group by type
            TYPE_MAP = {
                "ruins": "ruins",
                "next ruins": "ruins",
                "altar": "altars",
                "altars": "altars",
                "next altar fight": "altars",
                "chronicle": "chronicle",
                "major": "major",
            }

            grouped = {"ruins": [], "altars": [], "chronicle": [], "major": []}

            for e in self.events:
                raw_type = e.get("type", "").lower()
                normalized = TYPE_MAP.get(raw_type, raw_type)
                if normalized in grouped:
                    grouped[normalized].append(e)

            for key, items in grouped.items():
                if not items:
                    continue
                items.sort(key=lambda e: e["start_time"])

                lines = [
                    f"• **{e.get('name') or e.get('title')}**\n{format_dt(e['start_time'], style='F')}"
                    for e in items
                ]
                value = "\n".join(lines)
                if len(value) > 1024:
                    trimmed = []
                    total = 0
                    for line in lines:
                        ln = len(line) + 1
                        if total + ln > 1010:
                            break
                        trimmed.append(line)
                        total += ln
                    value = "\n".join(trimmed) + "\n…"
                embed.add_field(name=key.capitalize(), value=value, inline=False)

        embed.set_footer(text="K98 Bot – Local Time View")
        logger.info(
            f"[LOCAL TIME EMBED] Built embed for prefix '{self.prefix}' with {len(self.events)} event(s)."
        )
        return embed


def format_event_time(dt):
    """Formats a datetime object into a UTC string."""
    return dt.strftime("%A, %d %B %Y at %H:%M UTC")


async def log_embed_to_file(embed: discord.Embed, log_path="embed_audit.log"):
    async with aiofiles.open(log_path, "a", encoding="utf-8") as f:
        await f.write(
            f"[{discord.utils.utcnow().isoformat()}] {embed.title} - {embed.description}\n"
        )


async def send_embed(
    destination, title, fields: dict, color: int, mention=None, fallback_channel=None, bot=None
):
    embed = discord.Embed(title=title, color=color)
    for name, value in fields.items():
        value = str(value)
        if len(value) > 1024:
            value = value[:1021] + "..."
        embed.add_field(name=name, value=value, inline=False)
    embed.timestamp = discord.utils.utcnow()

    try:
        await destination.send(content=mention if mention else None, embed=embed)
    except discord.HTTPException as e:
        logger.warning(
            f"Failed to send embed to {getattr(destination, 'name', str(destination))} ({getattr(destination, 'id', 'N/A')}): {e}"
        )
        if fallback_channel and bot:
            fallback_embed = discord.Embed(
                title="📬 Embed Delivery Failed",
                description="Sent fallback to notify channel.",
                color=0xE67E22,
            )
            fallback_embed.add_field(name="Original Title", value=title, inline=False)
            fallback_embed.timestamp = discord.utils.utcnow()
            await fallback_channel.send(embed=fallback_embed)
    await log_embed_to_file(embed)


async def generate_summary_embed(days=1, summary_log_path="summary_log.csv"):
    start_date = discord.utils.utcnow().date() - timedelta(days=days - 1)
    total = 0
    failures = 0
    durations = []
    rows_to_show = []

    if not os.path.exists(summary_log_path):
        return None

    rows = await read_summary_log_rows(summary_log_path)

    for row in rows:
        timestamp_str = row.get("Timestamp")
        if not timestamp_str:
            continue
        try:
            ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        if ts.date() >= start_date:
            total += 1
            try:
                duration = float(row.get("Duration (sec)", 0))
                durations.append(duration)
            except Exception:
                duration = 0.0

            excel = "✅" if row.get("Excel Success") == "True" else "❌"
            archive = "✅" if row.get("Archive Success") == "True" else "❌"
            sql = "✅" if row.get("SQL Success") == "True" else "❌"
            export = "✅" if row.get("Export Success") == "True" else "❌"

            if sql != "✅" or export != "✅":
                failures += 1

            rows_to_show.append(
                f"🕒 {ts.strftime('%Y-%m-%d %H:%M')} – **{row.get('Filename', 'N/A')}** – {duration:.0f}s – Excel:{excel} Archive:{archive} SQL:{sql} Export:{export}"
            )

    if total == 0:
        return None

    avg_duration_str = f"{(sum(durations) / len(durations)):.1f} sec" if durations else "N/A"

    embed = discord.Embed(
        title=f"📊 {'Weekly' if days > 1 else 'Daily'} Processing Summary", color=INFO_COLOR
    )
    today = discord.utils.utcnow().date()
    embed.add_field(name="Date Range", value=f"{start_date} to {today}", inline=False)
    embed.add_field(name="Files Processed", value=fmt_short(total), inline=True)
    embed.add_field(name="Failures", value=str(failures), inline=True)
    embed.add_field(name="Average Duration", value=avg_duration_str, inline=True)
    details_text = "\n".join(rows_to_show[-10:]) or "No recent files"
    if len(details_text) > 1024:
        details_text = details_text[:1021] + "…"
    embed.add_field(name="File Details", value=details_text, inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


async def send_summary_embed(channel: discord.TextChannel, days: int = 1) -> discord.Message | None:
    """Build and send a summary embed to a Discord channel."""
    try:
        embed = await generate_summary_embed(days=days)
    except Exception as e:
        logger.warning(f"[SUMMARY] Failed to generate summary embed: {e}")
        embed = None

    if not embed:
        await channel.send("No recent processing activity to summarise.")
        return
    await channel.send(embed=embed)


class HistoryView(discord.ui.View):
    def __init__(
        self, interaction, rows, page, total_pages, *, entries_per_page: int = 5, timeout: int = 60
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction  # original interaction (optional fallback)
        self.rows = rows
        self.page = max(1, int(page))
        self.total_pages = max(1, int(total_pages))
        self.entries_per_page = entries_per_page
        self.message: discord.Message | None = None  # set by the command after send
        self._apply_nav_state()

    def _get_nav_buttons(self):
        prev_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "previous" in (c.label or "").lower()
            ),
            None,
        )
        next_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "next" in (c.label or "").lower()
            ),
            None,
        )
        return prev_btn, next_btn

    def _apply_nav_state(self):
        prev_btn, next_btn = self._get_nav_buttons()
        if prev_btn:
            prev_btn.disabled = self.page <= 1
        if next_btn:
            next_btn.disabled = self.page >= self.total_pages

    async def _refresh_message(self, interaction: discord.Interaction):
        self._apply_nav_state()
        try:
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        except discord.InteractionResponded:
            # Fallback if already acked
            try:
                if self.message:
                    await self.message.edit(embed=self.get_embed(), view=self)
                elif self.interaction:
                    msg = await self.interaction.original_response()
                    await msg.edit(embed=self.get_embed(), view=self)
            except Exception:
                pass

    def get_embed(self):
        start = (self.page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        page_rows = self.rows[::-1][start:end]

        embed = discord.Embed(
            title=f"📜 File Processing History (Page {self.page}/{self.total_pages})",
            color=INFO_COLOR,
        )
        for row in page_rows:
            embed.add_field(
                name=f"📄 {row.get('Filename', 'Unknown')}",
                value=(
                    f"👤 Uploaded by: `{row.get('Author', 'Unknown')}`\n"
                    f"🕒 Time: `{row.get('Timestamp', 'Unknown')}`\n"
                    f"#️⃣ Channel: `{row.get('Channel', 'Unknown')}`\n"
                    f"📂 Path: `{row.get('SavedPath', 'Unknown')}`"
                ),
                inline=False,
            )
        embed.timestamp = discord.utils.utcnow()
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page <= 1:
            # Ack silently so Discord doesn't show an error
            await interaction.response.defer()
            return
        self.page -= 1
        await self._refresh_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page >= self.total_pages:
            await interaction.response.defer()
            return
        self.page += 1
        await self._refresh_message(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
            elif self.interaction:
                msg = await self.interaction.original_response()
                await msg.edit(view=self)
        except Exception as e:
            logger.warning(f"[HistoryView] Failed to disable buttons after timeout: {e}")


class FailuresView(discord.ui.View):
    def __init__(
        self, interaction, rows, page, total_pages, *, entries_per_page: int = 5, timeout: int = 60
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.rows = rows
        self.page = max(1, int(page))
        self.total_pages = max(1, int(total_pages))
        self.entries_per_page = entries_per_page
        self.message: discord.Message | None = None  # set by the command after send
        self._apply_nav_state()

    def _get_nav_buttons(self):
        prev_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "previous" in (c.label or "").lower()
            ),
            None,
        )
        next_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "next" in (c.label or "").lower()
            ),
            None,
        )
        return prev_btn, next_btn

    def _apply_nav_state(self):
        prev_btn, next_btn = self._get_nav_buttons()
        if prev_btn:
            prev_btn.disabled = self.page <= 1
        if next_btn:
            next_btn.disabled = self.page >= self.total_pages

    async def _refresh_message(self, interaction: discord.Interaction):
        self._apply_nav_state()
        try:
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        except discord.InteractionResponded:
            try:
                if self.message:
                    await self.message.edit(embed=self.get_embed(), view=self)
                elif self.interaction:
                    msg = await self.interaction.original_response()
                    await msg.edit(embed=self.get_embed(), view=self)
            except Exception:
                pass

    def get_embed(self):
        start = (self.page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        page_rows = self.rows[::-1][start:end]

        embed = discord.Embed(
            title=f"❌ Failed Jobs (Page {self.page}/{self.total_pages})", color=DANGER_COLOR
        )
        for row in page_rows:
            embed.add_field(
                name=f"📄 {row.get('Filename', 'Unknown')}",
                value=(
                    f"👤 Author: `{row.get('User', 'Unknown')}`\n"
                    f"🕒 Time: `{row.get('Timestamp', 'Unknown')}`\n"
                    f"📊 Rank/Seed: `{row.get('Rank', '?')}` / `{row.get('Seed', '?')}`\n"
                    f"**Excel:** `{row.get('Excel Success', '?')}`, Archive: `{row.get('Archive Success', '?')}`\n"
                    f"🧠 SQL: `{row.get('SQL Success', '?')}` | 📤 Export: `{row.get('Export Success', '?')}`\n"
                    f"⏱ Duration: `{row.get('Duration (sec)', '?')}`"
                ),
                inline=False,
            )
        embed.timestamp = discord.utils.utcnow()
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page <= 1:
            await interaction.response.defer()
            return
        self.page -= 1
        await self._refresh_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page >= self.total_pages:
            await interaction.response.defer()
            return
        self.page += 1
        await self._refresh_message(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
            elif self.interaction:
                msg = await self.interaction.original_response()
                await msg.edit(view=self)
        except Exception as e:
            logger.warning(f"[FailuresView] Failed to disable buttons after timeout: {e}")


def build_target_embed(data):
    gov_name = md_escape(str(data.get("GovernorName", "Unknown")))
    embed = discord.Embed(title=f"🎯 KVK Targets for {gov_name}", color=INFO_COLOR)
    embed.add_field(name="Governor ID", value=str(data.get("GovernorID", "—")), inline=False)
    embed.add_field(name="Kill Target", value=fmt_short(data.get("KillTarget", 0)), inline=True)
    embed.add_field(name="Dead Target", value=fmt_short(data.get("DeadTarget", 0)), inline=True)
    embed.add_field(name="DKP Target", value=fmt_short(data.get("DKPTarget", 0)), inline=True)
    embed.set_footer(text="K98 Discord bot • KVK Targets")
    embed.timestamp = discord.utils.utcnow()
    return embed


def format_fight_embed(fights):
    embed = discord.Embed(
        title="🔥 Upcoming Fights",
        color=DANGER_COLOR,
    )
    embed.set_thumbnail(url="https://i.ibb.co/FLPsD22x/FIGHTS.jpg")

    for event in fights:
        name = md_escape(event.get("name", "(Unnamed Event)"))
        start = event.get("start_time")
        if not start:
            continue
        countdown = format_countdown(start, short=True)
        value = f"{format_event_time(start)}  ({countdown})"  # UTC
        if len(value) > 1024:
            value = value[:1021] + "…"
        embed.add_field(name=f"⚔️ {name}", value=value, inline=False)

    embed.set_footer(
        text="Times shown in UTC — use the button to view in your local time & switch between 1 or 3 upcoming fights."
    )
    embed.timestamp = discord.utils.utcnow()
    return embed


def format_event_embed(events):
    embed = discord.Embed(
        title="📅 Upcoming Event(s)",
        color=INFO_COLOR,
    )

    for event in events:
        name = md_escape(event.get("name", "(Unnamed Event)"))
        start = event.get("start_time")
        if not start:
            continue
        countdown = format_countdown(start, short=True)
        value = f"{format_event_time(start)}  ({countdown})"  # UTC
        description = event.get("description")
        if description:
            value += f"\n\n📖 {md_escape(description)}"
        if len(value) > 1024:
            value = value[:1021] + "…"
        embed.add_field(name=name, value=value, inline=False)

    embed.set_footer(text="Times shown in UTC — use the local-time button to convert.")
    embed.timestamp = discord.utils.utcnow()
    return embed


async def expire_old_event_embeds(bot: discord.Client):
    try:
        with open(VIEW_TRACKING_FILE, encoding="utf-8") as f:
            views = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[expire_embeds] View tracker file not found or invalid.")
        return

    now = discord.utils.utcnow()
    today = now.date()
    yesterday = today - timedelta(days=1)

    views_to_update = views.copy()

    for key in ("nextevent", "nextfight"):
        data = views.get(key)
        if not data:
            continue

        created_at_str = data.get("created_at")
        if not created_at_str:
            continue

        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except ValueError:
            print(f"[expire_embeds] Invalid timestamp for {key}: {created_at_str}")
            continue

        if created_at.date() != yesterday:
            continue  # Not expired yet

        channel_id = data.get("channel_id")
        message_id = data.get("message_id")

        try:
            channel = await bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
            print(f"[expire_embeds] Deleted outdated `{key}` embed.")
        except Exception as e:
            print(f"[expire_embeds] Failed to delete `{key}` message: {e}")
            continue  # Skip regeneration if delete failed

        if AUTO_REGENERATE:
            try:
                from command_regenerate import regenerate_embed

                new_embed_data = await regenerate_embed(key, channel)
                if new_embed_data:
                    views_to_update[key] = new_embed_data
                    print(f"[expire_embeds] Regenerated `{key}` embed and updated tracker.")
                else:
                    print(
                        f"[expire_embeds] Regeneration returned no data for `{key}` — keeping old."
                    )
                    continue  # Keep old entry
            except Exception as e:
                print(f"[expire_embeds] Regeneration failed for `{key}`: {e}")
                continue  # Keep old entry
        else:
            del views_to_update[key]  # Only remove if not regenerating

    with open(VIEW_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(views_to_update, f, indent=2, ensure_ascii=False)
        print("[expire_embeds] View tracker file updated.")


def build_stats_embed(governor_data, discord_user) -> tuple[discord.Embed, discord.File]:
    def clamp(v, lo=0.0, hi=100.0):
        try:
            return max(lo, min(hi, float(v)))
        except Exception:
            return 0.0

    governor_name = md_escape(governor_data.get("GovernorName", "Unknown"))
    KVK_NO = int(governor_data.get("KVK_NO", 0) or 0)
    governor_id = str(governor_data.get("GovernorID", "Unknown"))
    power_int = int(governor_data.get("Power", 0) or 0)
    power = fmt_short(power_int)
    kvk_rank = governor_data.get("KVK_RANK", "—")
    status_raw = str(governor_data.get("STATUS", "") or "").strip().upper()
    is_exempt = status_raw == "EXEMPT"

    # Targets
    kill_target = int(governor_data.get("Kill Target", 0) or 0)
    dead_target = int(governor_data.get("Dead Target", 0) or 0)
    dkp_target = int(governor_data.get("DKP Target", 0) or 0)
    no_targets_set = kill_target == 0 and dead_target == 0 and dkp_target == 0

    # Stats
    T4_kills = int(governor_data.get("T4_Kills", 0) or 0)
    T5_kills = int(governor_data.get("T5_Kills", 0) or 0)
    Total_kills = int(governor_data.get("T4&T5_Kills", 0) or 0)
    T4_deads = int(governor_data.get("T4_Deads", 0) or 0)
    T5_deads = int(governor_data.get("T5_Deads", 0) or 0)
    deads = int(governor_data.get("Deads", 0) or 0)
    dkp = float(governor_data.get("DKP Score", 0) or 0.0)

    # Percent calculations (only when targets exist)
    if is_exempt:
        # use Nones to hide % text + avoid drawing a progress dial with numbers
        kills_pct_raw = deads_pct_raw = dkp_pct_raw = None
    else:
        # compute RAW (unclamped) values so text can show >100%
        kills_pct_raw = (Total_kills / kill_target * 100.0) if kill_target else None
        deads_pct_raw = (deads / dead_target * 100.0) if dead_target else None
        dkp_pct_raw = (dkp / dkp_target * 100.0) if dkp_target else None
        # (optional) If you want clamped values handy for anything else:
        # kills_pct = clamp(kills_pct_raw or 0.0)
        # deads_pct = clamp(deads_pct_raw or 0.0)
        # dkp_pct   = clamp(dkp_pct_raw   or 0.0)

    # Last refresh
    last_refresh = governor_data.get("LAST_REFRESH", "—")

    def _fmt_last_refresh(val):
        if isinstance(val, datetime):
            return val.strftime("%d %B %Y")
        try:
            s = str(val)
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s).strftime("%d %B %Y")
        except Exception:
            return "—"

    last_refresh_str = _fmt_last_refresh(last_refresh)

    # Build embed
    title = f"🧾 KVK {KVK_NO} • {governor_name} — ID {governor_id}"
    embed = discord.Embed(title=title[:256], color=INFO_COLOR, timestamp=discord.utils.utcnow())
    # Always use the global custom avatar for consistency
    thumb_url = CUSTOM_AVATAR_URL
    try:
        if not thumb_url and getattr(discord_user, "display_avatar", None):
            thumb_url = discord_user.display_avatar.url
    except Exception:
        pass
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)

    embed.add_field(name="🏅 KVK Rank", value=f"**{kvk_rank}**", inline=True)
    embed.add_field(name="MM Power", value=power, inline=True)

    # Targets block with new logic
    if is_exempt:
        targets_text = "📛 This player is **exempt** from all targets."
    else:
        if no_targets_set:
            if power_int < 40_000_000:
                targets_text = "🍼 Power below **40M** — no targets set. Just do what you can!"
            else:
                targets_text = "⏳ Targets not yet assigned. Please check back soon."
        else:
            targets_text = (
                f"🗡 Kills: **{fmt_short(kill_target)}**\n"
                f"💀 Deads: **{fmt_short(dead_target)}**\n"
                f"🧮 DKP: **{fmt_short(dkp_target)}**"
            )
    embed.add_field(name="🎯 Targets", value=targets_text, inline=False)

    # Per-metric % visibility flags
    show_kill_pct = (not is_exempt) and (kill_target > 0) and (kills_pct_raw is not None)
    show_dead_pct = (not is_exempt) and (dead_target > 0) and (deads_pct_raw is not None)
    show_dkp_pct = (not is_exempt) and (dkp_target > 0) and (dkp_pct_raw is not None)

    # Kills
    kills_val = (
        f"T4: **{fmt_short(T4_kills)}**\n"
        f"T5: **{fmt_short(T5_kills)}**\n"
        f"T4&T5: **{fmt_short(Total_kills)}**"
        + (f" **({fmt_pct(kills_pct_raw)})**" if show_kill_pct else "")
    )
    embed.add_field(name="🗡 KILLS", value=kills_val, inline=False)

    # Deads
    deads_val = (
        f"T4: **{fmt_short(T4_deads)}**\n"
        f"T5: **{fmt_short(T5_deads)}**\n"
        f"Total: **{fmt_short(deads)}**"
        + (f" **({fmt_pct(deads_pct_raw)})**" if show_dead_pct else "")
    )
    embed.add_field(name="💀 DEADS", value=deads_val, inline=False)

    # DKP
    dkp_val = (
        "📛 Exempt from DKP target."
        if is_exempt
        else f"**{fmt_short(int(dkp))}**"
        + (f" **({fmt_pct(dkp_pct_raw)})**" if show_dkp_pct else "")
    )
    embed.add_field(name="🧮 DKP", value=dkp_val, inline=False)

    embed.add_field(
        name="🕒 Last Updated",
        value=f"{last_refresh_str} — Requested: {discord_user.mention}",
        inline=False,
    )
    embed.set_footer(text="K98 Stats Bot")

    # Dial image
    if is_exempt:
        img_bytes = generate_exempt_dial()
    else:
        # Dial clamped to [0,100], label shows RAW (can be >100)
        dial_pct = clamp(kills_pct_raw if kills_pct_raw is not None else 0.0)
        img_bytes = generate_progress_dial(dial_pct, display_percent=kills_pct_raw)
    file = discord.File(img_bytes, filename="progress.png")
    embed.set_image(url="attachment://progress.png")

    return embed, file
