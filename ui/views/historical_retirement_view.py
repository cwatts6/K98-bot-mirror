"""Concise shared review and explicit per-import selection, with durable approval."""

import discord

from core.interaction_safety import safe_defer
from services.historical_import_recovery_service import ACTION
from ui.views.recovery_view import (
    RecoveryIncidentView,
    actor_for,
    call,
    incident_embed,
    report_error,
)


async def show_batches(interaction, after=None):
    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        result = await call("review_historical_groups", actor, after)
        if len(result["groups"]) == 1:
            await show_group(interaction, result["groups"][0], result["next_after"], deferred=True)
            return
        await interaction.followup.send(
            (
                "Choose a group with identical original and installed configuration. Only exports you select will be retired."
                if result["groups"]
                else "No eligible historical exports on this page. Existing approvals continue in the background; other incidents keep their own checks."
            ),
            view=HistoricalBatchPicker(result),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class HistoricalBatchPicker(discord.ui.View):
    def __init__(self, result):
        super().__init__(timeout=300)
        if result["groups"]:
            selector = discord.ui.Select(
                placeholder="Choose shared configuration",
                options=[
                    discord.SelectOption(
                        label=f"{len(g['members'])} exports · original settings {g['configuration']['original'][:8]}",
                        value=str(index),
                        description=(
                            "Settings match installed configuration"
                            if g["configuration"]["original"] == g["configuration"]["current"]
                            else "Original settings differ from installed configuration"
                        ),
                    )
                    for index, g in enumerate(result["groups"])
                ],
            )

            async def choose(interaction):
                await show_group(
                    interaction, result["groups"][int(selector.values[0])], result["next_after"]
                )

            selector.callback = choose
            self.add_item(selector)
        add_next(self, result["next_after"])


def add_next(view, after):
    if after:
        button = discord.ui.Button(
            label="Next historical batch", style=discord.ButtonStyle.secondary
        )

        async def next_batch(interaction):
            await show_batches(interaction, after)

        button.callback = next_batch
        view.add_item(button)


async def show_group(interaction, group, after=None, *, deferred=False):
    try:
        actor = actor_for(interaction)
        if not deferred and not await safe_defer(interaction, ephemeral=True):
            return
        result = await call("review_historical_group", actor, group)
        embed = discord.Embed(
            title=f"Review {len(group['members'])} historical exports together",
            description="Shared configuration is reviewed once. Select only obsolete exports using their original date, procedure and input below. Leave anything still needed or unidentified unselected.",
            color=0xF1C40F,
        )
        for field in result["fields"]:
            embed.add_field(
                name=field["label"],
                value=discord.utils.escape_markdown(field["text"]),
                inline=False,
            )
        embed.set_footer(text="Up to 25 per batch · Full technical details are optional")
        await interaction.followup.send(
            embed=embed,
            view=HistoricalMemberView(result, after),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class HistoricalMemberView(discord.ui.View):
    def __init__(self, result, after):
        super().__init__(timeout=300)
        self.result = result
        members = result["group"]["members"]
        selector = discord.ui.Select(
            placeholder="Select obsolete exports to retire",
            min_values=1,
            max_values=len(members),
            options=[
                discord.SelectOption(
                    label=f"{m['created'][:19]} UTC · {m['procedure'] or 'procedure unknown'}"[
                        :100
                    ],
                    description=f"{m['input'] or 'Input not recorded'} · ID {m['id'][-12:]}"[:100],
                    value=m["id"],
                )
                for m in members
            ],
        )

        async def select(interaction):
            try:
                actor = actor_for(interaction)
                if not await safe_defer(interaction, ephemeral=True):
                    return
                selected = list(selector.values)
                group = result["group"]
                # A changed unselected member must not prevent this decision.
                await call("review_historical_group", actor, group, selected)
                chosen = [m for m in members if m["id"] in selected]
                embed = discord.Embed(
                    title=f"Retire {len(chosen)} selected old exports?",
                    description="Confirm these outputs are no longer needed. SQL outcomes remain unknown. The bot preserves captured bytes and verifies each retirement separately; no import or provider write is replayed.",
                    color=0xF1C40F,
                )
                for offset in range(0, len(chosen), 5):
                    text = "\n".join(
                        f"{m['created'][:19]} · {m['input'] or 'input not recorded'} · ID {m['id'][-12:]}"
                        for m in chosen[offset : offset + 5]
                    )
                    embed.add_field(
                        name="Selected inputs",
                        value=discord.utils.escape_markdown(text),
                        inline=False,
                    )
                await interaction.followup.send(
                    embed=embed,
                    view=HistoricalConfirmView(group, selected),
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except Exception as exc:
                await report_error(interaction, exc)

        selector.callback = select
        self.add_item(selector)
        add_next(self, after)

    @discord.ui.button(label="View shared technical details", style=discord.ButtonStyle.secondary)
    async def technical(self, button, interaction):
        from ui.views.recovery_review_view import show_review_page

        await show_review_page(interaction, self.result["technical_row"], ACTION, 0, read_only=True)


class HistoricalConfirmView(discord.ui.View):
    def __init__(self, group, selected):
        super().__init__(timeout=300)
        self.group, self.selected = group, selected

    @discord.ui.button(label="Confirm selected retirements", style=discord.ButtonStyle.primary)
    async def confirm(self, button, interaction):
        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await call("approve_historical_group", actor, self.group, self.selected)
            await interaction.followup.send(
                embed=incident_embed(row),
                view=RecoveryIncidentView(row),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            button.disabled = True
            self.stop()
        except Exception as exc:
            await report_error(interaction, exc)
