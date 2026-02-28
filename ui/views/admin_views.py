# ui/views/admin_views.py
"""Administrative UI views extracted from command module."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from datetime import datetime
import io
import os
import re

import discord

from bot_config import ADMIN_USER_ID

try:
    from constants import RESTART_EXIT_CODE, RESTART_FLAG_PATH
except Exception:
    RESTART_EXIT_CODE = 1
    RESTART_FLAG_PATH = ".restart_flag.json"


class LogTailView(discord.ui.View):
    def __init__(self, ctx, src_path, title, level=None, contains=None, page=1, page_size=50):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.src_path = src_path
        self.title = title
        self.level = (level or "").upper().strip() or None
        self.contains = contains.strip() if contains else None
        self.page = max(1, int(page or 1))
        self.page_size = max(10, min(int(page_size or 50), 200))

        self.prev.disabled = self.page <= 1

    def _match(self, line: str) -> bool:
        if self.level:
            # naive level check (works with standard logging format)
            # e.g., "INFO", "WARNING", "ERROR", "CRITICAL"
            if self.level not in line:
                return False
        if self.contains:
            try:
                if re.search(self.contains, line, re.IGNORECASE) is None:
                    return False
            except re.error:
                if self.contains.lower() not in line.lower():
                    return False
        return True

    def _tail_filtered(self):
        if not os.path.exists(self.src_path):
            return [], 0, 0, 0

        total_lines = 0
        dq = deque(maxlen=50000)
        with open(self.src_path, encoding="utf-8", errors="replace", newline="") as f:
            for ln in f:
                total_lines += 1
                dq.append(ln.rstrip("\n"))

        # NEW: newest-first by iterating reversed(dq)
        matched = []
        for ln in reversed(dq):
            if self._match(ln):
                matched.append(ln)

        total_matches = len(matched)
        total_pages = max(1, (total_matches + self.page_size - 1) // self.page_size)
        self.page = min(self.page, total_pages)

        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        return matched[start:end], total_lines, total_matches, total_pages

    def _color(self):
        name = os.path.basename(self.src_path).lower()
        if "error" in name:
            return 0xE74C3C
        if "crash" in name:
            return 0xFF6347
        return 0x3498DB

    async def render(self, interaction: discord.Interaction):
        # 1) Compute page slice
        lines, total_lines, total_matches, total_pages = self._tail_filtered()
        body = "\n".join(lines).strip() or "(no matching lines)"
        body = body.replace("```", "`\u200b``")  # fence safety

        # 2) Budget + description
        BUDGET = 3800
        needs_file = len(body) > BUDGET
        desc_body = body[:BUDGET]
        if needs_file:
            desc_body += "\n…(truncated)"
        desc = f"```{desc_body}```"

        # 3) File stats for footer
        try:
            mtime = os.path.getmtime(self.src_path)
            mtime_dt = datetime.utcfromtimestamp(mtime)
            size_kb = os.path.getsize(self.src_path) // 1024
        except Exception:
            mtime_dt, size_kb = datetime.utcnow(), 0

        # 4) Build the embed (DEFINE IT BEFORE kwargs)
        filters = []
        if self.level:
            filters.append(f"level={self.level}")
        if self.contains:
            filters.append(f"contains=/{self.contains}/")
        filter_text = " • ".join(filters) if filters else "none"

        embed = discord.Embed(
            title=self.title,
            description=desc,
            color=self._color(),
        )
        embed.add_field(name="Page", value=f"{self.page}/{total_pages}", inline=True)
        embed.add_field(name="Matches", value=str(total_matches), inline=True)
        embed.add_field(
            name="File Stats",
            value=f"{os.path.basename(self.src_path)} • {size_kb} KB",
            inline=True,
        )
        embed.set_footer(text=f"Modified {mtime_dt:%Y-%m-%d %H:%M:%S} UTC • Filters: {filter_text}")
        embed.timestamp = datetime.utcnow()

        # 5) Prepare kwargs correctly
        kwargs = {"embed": embed, "view": self}

        if needs_file:
            # Upload a fresh file for this page
            buf = io.BytesIO(("\n".join(lines)).encode("utf-8", "replace"))
            buf.seek(0)
            file = discord.File(buf, filename=f"log_page_{self.page}.txt")
            kwargs["files"] = [file]
        else:
            # If a previous page attached a file, clear it now
            kwargs["attachments"] = []

        # 6) Edit depending on interaction state
        if interaction.response.is_done():
            await interaction.edit_original_response(**kwargs)
        else:
            await interaction.response.edit_message(**kwargs)

    @discord.ui.button(label="◀️ Newer", style=discord.ButtonStyle.secondary)
    async def prev(self, _, interaction: discord.Interaction):
        if self.page > 1:
            self.page -= 1
        self.prev.disabled = self.page <= 1
        await self.render(interaction)

    @discord.ui.button(label="Older ▶️", style=discord.ButtonStyle.secondary)
    async def next(self, _, interaction: discord.Interaction):
        self.page += 1
        self.prev.disabled = self.page <= 1
        await self.render(interaction)

    @discord.ui.button(label="🔎 Toggle Filter", style=discord.ButtonStyle.primary)
    async def show_filters(self, _, interaction: discord.Interaction):
        txt = (
            f"**Current filters**\n"
            f"- level: `{self.level or 'none'}`\n"
            f"- contains: `{self.contains or 'none'}`\n"
            f"- page_size: `{self.page_size}`\n\n"
            f"Tip: Use command options to set filters, e.g.:\n"
            f'`/logs source:error level:ERROR contains:"sql" page_size:100`'
        )
        await interaction.response.send_message(txt, ephemeral=True)


class ConfirmRestartView(discord.ui.View):
    def __init__(self, ctx, *, bot, notify_channel_id: int, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.notify_channel_id = notify_channel_id
        self.confirmed = asyncio.Event()
        self.cancelled = False
        self.message: discord.Message | None = None

    def _disable_all(self):
        for c in self.children:
            c.disabled = True

    async def _try_disable_ui(self):
        try:
            if self.message is None:
                self.message = await self.ctx.interaction.original_response()
            self._disable_all()
            await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="✅ Confirm Restart", style=discord.ButtonStyle.danger)
    async def confirm(self, _button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message(
                "❌ Only the admin can confirm this action.", ephemeral=True
            )
            return

        embed_user = discord.Embed(
            title="🔄 Bot Restart Initiated",
            description="Attempting to restart the bot now. If it doesn't come back online, check your host.",
            color=0xF39C12,
        )
        embed_user.set_footer(text="Restart requested by admin")
        embed_user.timestamp = datetime.utcnow()
        await interaction.response.send_message(embed=embed_user, ephemeral=True)

        try:
            notify_channel = self.bot.get_channel(self.notify_channel_id)
            if notify_channel:
                embed_broadcast = discord.Embed(
                    title="🛠️ Bot Restart Requested",
                    description=f"Admin <@{interaction.user.id}> initiated a restart via slash command.",
                    color=0xF39C12,
                )
                embed_broadcast.timestamp = datetime.utcnow()
                await notify_channel.send(embed=embed_broadcast)
        except Exception:
            pass

        await self._try_disable_ui()
        self.confirmed.set()
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, _button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message(
                "❌ Only the admin can cancel this action.", ephemeral=True
            )
            return
        await interaction.response.send_message("❎ Bot restart cancelled.", ephemeral=True)
        self.cancelled = True
        await self._try_disable_ui()
        self.confirmed.set()
        self.stop()


class ConfirmImportView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        ephemeral: bool = True,
        timeout: int = 120,
        on_confirm_apply: Callable[[discord.Interaction], Awaitable[None]] | None = None,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.ephemeral = ephemeral
        self.on_confirm_apply = on_confirm_apply

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message(
                    "❌ This confirmation is not for you.", ephemeral=True
                )
            except Exception:
                pass
            return False
        return True

    @discord.ui.button(label="Apply import", style=discord.ButtonStyle.success)
    async def on_confirm(self, _button: discord.ui.Button, interaction: discord.Interaction):
        for c in self.children:
            c.disabled = True
        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            pass

        if self.on_confirm_apply is not None:
            await self.on_confirm_apply(interaction)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def on_cancel(self, _button: discord.ui.Button, interaction: discord.Interaction):
        for c in self.children:
            c.disabled = True
        try:
            await interaction.response.edit_message(
                content="❌ Import cancelled by user.", view=self
            )
        except Exception:
            pass
        self.stop()

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True


__all__ = [
    "ConfirmImportView",
    "ConfirmRestartView",
    "LogTailView",
]
