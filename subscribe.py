# commands/subscribe.py
import discord
from discord import app_commands
from discord.ext import commands

from constants import DEFAULT_REMINDER_TIMES, VALID_TYPES
from subscription_tracker import (
    get_user_config,
    load_subscriptions,
    set_user_config,
)

# Tooltips (user-facing)
TYPE_HELP = "Pick what you want alerts for. Tip: 'fights' includes altars + major; 'all' includes everything."
TIME_HELP = "Choose when to be reminded. If you skip this, defaults will be used."


class SubscribeView(discord.ui.View):
    def __init__(
        self, user: discord.User, *, existing: dict | None = None, timeout: float | None = 180
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.saved = False

        existing_types = (existing or {}).get("subscriptions", [])
        existing_times = (existing or {}).get("reminder_times", [])

        # --- Event types select (multi)
        type_options = [
            discord.SelectOption(label=t, value=t, default=(t in existing_types))
            for t in sorted(VALID_TYPES)
        ]
        self.types = discord.ui.Select(
            placeholder="Select event types…",
            min_values=1,
            max_values=len(type_options),
            options=type_options,
        )
        self.types.callback = self.on_types_changed  # bind handler
        self.add_item(self.types)

        # --- Reminder times select (multi)
        time_options = [
            discord.SelectOption(label=t, value=t, default=(t in existing_times))
            for t in DEFAULT_REMINDER_TIMES
        ]
        self.times = discord.ui.Select(
            placeholder="Select reminder times (or skip for defaults)…",
            min_values=0,  # allow empty -> we’ll use defaults
            max_values=len(time_options),
            options=time_options,
        )
        self.times.callback = self.on_times_changed
        self.add_item(self.times)

        # --- Labels (help text)
        self.add_item(
            discord.ui.Button(
                label="Event types help", style=discord.ButtonStyle.secondary, disabled=True
            )
        )
        self.children[-1].label = TYPE_HELP  # shows as a disabled hint row

        self.add_item(
            discord.ui.Button(
                label="Reminder times help", style=discord.ButtonStyle.secondary, disabled=True
            )
        )
        self.children[-1].label = TIME_HELP

        # --- Action buttons
        self.save_btn = discord.ui.Button(label="Save", style=discord.ButtonStyle.success)
        self.save_btn.callback = self.on_save
        self.add_item(self.save_btn)

        self.cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        self.cancel_btn.callback = self.on_cancel
        self.add_item(self.cancel_btn)

        self._apply_state()

    def _apply_state(self):
        # Save disabled if no event types selected
        selected_types = set(self.types.values or [])
        self.save_btn.disabled = len(selected_types) == 0

    async def on_types_changed(self, interaction: discord.Interaction):
        self._apply_state()
        await interaction.response.edit_message(view=self)

    async def on_times_changed(self, interaction: discord.Interaction):
        # nothing to validate; keep UX snappy
        await interaction.response.defer()

    async def on_cancel(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content="❌ Subscription cancelled.", embed=None, view=None
        )

    async def on_save(self, interaction: discord.Interaction):
        # Collect selections
        selected_types = [v for v in (self.types.values or []) if v in VALID_TYPES]
        selected_times = [v for v in (self.times.values or []) if v in DEFAULT_REMINDER_TIMES]
        if not selected_types:
            await interaction.response.send_message(
                "❌ Please select at least one event type.", ephemeral=True
            )
            return

        if not selected_times:
            selected_times = DEFAULT_REMINDER_TIMES

        # Persist -- store a stable username (username#discriminator) to help identify users
        username_repr = f"{self.user.name}#{getattr(self.user, 'discriminator', '')}"
        set_user_config(self.user.id, username_repr, selected_types, selected_times)
        self.saved = True

        # DM welcome (non-fatal)
        welcome = discord.Embed(
            title="👋 Welcome to Event Reminders!",
            description=f"Hi {self.user.mention}, you're now subscribed to event alerts!",
            color=0x2ECC71,
        )
        welcome.add_field(name="Subscribed Types", value=", ".join(selected_types), inline=False)
        welcome.add_field(name="Reminder Intervals", value=", ".join(selected_times), inline=False)
        welcome.set_footer(
            text="You can update these anytime with /modify_subscription or /unsubscribe"
        )

        dm_note = "Welcome message sent via DM."
        try:
            await self.user.send(embed=welcome)
        except discord.Forbidden:
            dm_note = (
                "⚠️ I couldn't DM you. Please enable DMs from this server to receive reminders "
                "(your subscription is still saved)."
            )

        await interaction.response.edit_message(
            content=f"✅ Subscription saved! {dm_note}", embed=None, view=None
        )


class Subscribe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_subscriptions()

    @app_commands.command(name="subscribe", description="Subscribe to event reminders via DM")
    async def subscribe(self, interaction: discord.Interaction):
        user = interaction.user
        existing = get_user_config(user.id)

        if existing:
            # Let them update in place (same UI), rather than blocking.
            note = (
                "You’re already subscribed. Update your preferences below, or use "
                "`/modify_subscription` or `/unsubscribe`."
            )
        else:
            note = "Pick your event types and reminder times below."

        view = SubscribeView(user, existing=existing, timeout=180)
        await interaction.response.send_message(note, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Subscribe(bot))
