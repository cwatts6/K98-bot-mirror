from math import ceil
import os

from discord.ext import commands

# Admin constant (pick the right source)
from constants import ADMIN_USER_ID  # or: from bot_config import ADMIN_USER_ID

# Soft imports with fallbacks (avoid hard failures on import order)
try:
    from stats_alert_utils import generate_summary_embed
except Exception:

    async def generate_summary_embed(*args, **kwargs):  # type: ignore
        return None


try:
    from logging_setup import read_summary_log_rows
except Exception:

    async def read_summary_log_rows(*args, **kwargs):  # type: ignore
        return []


try:
    from embed_utils import FailuresView, HistoryView
except Exception:
    HistoryView = None  # type: ignore
    FailuresView = None  # type: ignore


class SummaryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="summary", description="View today's file processing summary")
    async def summary_command(self, ctx):
        await ctx.defer()
        embed = await generate_summary_embed(days=1)
        await ctx.respond(
            embed=embed or "âš ï¸ No summary log available or no files processed today."
        )

    @commands.slash_command(name="weeksummary", description="View 7-day file processing summary")
    async def weeksummary_command(self, ctx):
        await ctx.defer()
        embed = await generate_summary_embed(days=7)
        await ctx.respond(
            embed=embed
            or "âš ï¸ No summary log available or no files processed in the last 7 days."
        )

    @commands.slash_command(name="history", description="View recently processed files")
    async def history_command(self, ctx, page: int = 1):
        await ctx.defer()
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.respond("âŒ This command is restricted to admins.", ephemeral=True)
            return
        log_file = "download_log.csv"
        if not os.path.exists(log_file):
            await ctx.respond("âš ï¸ No download log found.")
            return
        rows = await read_summary_log_rows(log_file)
        total_pages = max(1, ceil(len(rows) / 5))
        page = max(1, min(page, total_pages))
        view = HistoryView(ctx, rows, page, total_pages) if HistoryView else None
        await ctx.respond(embed=view.get_embed(), view=view)

    @commands.slash_command(name="failures", description="View recently failed jobs")
    async def failures_command(self, ctx, page: int = 1):
        await ctx.defer()
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.respond("âŒ This command is restricted to admins.", ephemeral=True)
            return
        log_file = "failed_log.csv"
        if not os.path.exists(log_file):
            await ctx.respond("âš ï¸ No failure log found.")
            return
        rows = await read_summary_log_rows(log_file)
        if not rows:
            await ctx.respond("âœ… No failed jobs found.")
            return
        total_pages = max(1, ceil(len(rows) / 5))
        page = max(1, min(page, total_pages))
        view = FailuresView(ctx, rows, page, total_pages)
        await ctx.respond(embed=view.get_embed(), view=view)

    @commands.slash_command(name="ping", description="Test command")
    async def ping_command(self, ctx):
        await ctx.respond("Pong! ðŸ“")


async def setup(bot):
    await bot.add_cog(SummaryCommands(bot))
