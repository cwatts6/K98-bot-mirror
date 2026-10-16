"""Persistent recovery entry and disposable evidence-bound confirmation views."""

import logging
from uuid import UUID

import discord

from core.interaction_safety import safe_defer, send_ephemeral
from services.recovery_service import RecoveryActor, SourceConflict

logger = logging.getLogger(__name__)
FOOTER_PREFIX = "Recovery incident: "


def actor_for(interaction):
    import bot_config

    actor = RecoveryActor(
        int(interaction.user.id), int(interaction.guild_id or 0), int(interaction.channel_id or 0)
    )
    if (actor.user_id, actor.guild_id, actor.channel_id) != (
        int(bot_config.ADMIN_USER_ID),
        int(bot_config.GUILD_ID),
        int(bot_config.NOTIFY_CHANNEL_ID),
    ):
        raise SourceConflict(
            "Recovery is restricted to the configured admin in the notification channel."
        )
    return actor


async def call(method, *args):
    from services.legacy_export_snapshot_service import drain_thread
    from services.recovery_runtime import call_recovery

    return await drain_thread(call_recovery, method, *args)


def incident_embed(row):
    evidence = row["evidence"]
    embed = discord.Embed(
        title=evidence["title"],
        description=evidence["explanation"][:3500],
        color=0x2ECC71 if row["State"] == "resolved" else 0xF1C40F,
    )
    embed.add_field(name="Recovery status", value=row["State"], inline=True)
    embed.add_field(
        name="Operation outcome", value=str(evidence.get("outcome", "unproven")), inline=True
    )
    if evidence.get("scan") is not None:
        embed.add_field(name="Committed scan", value=str(evidence["scan"]), inline=True)
    if evidence.get("season") is not None:
        embed.add_field(name="KVK season", value=str(evidence["season"]), inline=True)
    embed.add_field(name="Last checked (UTC)", value=str(row["LastSeenUTC"]), inline=False)
    if evidence.get("evidence_reference"):
        embed.add_field(
            name="Affected evidence", value=evidence["evidence_reference"], inline=False
        )
        embed.add_field(
            name="Used for", value=", ".join(evidence["evidence_kinds"])[:1024], inline=False
        )
        embed.add_field(
            name="Verified copy checks",
            value="\n".join(f"{key.title()}: {value}" for key, value in evidence["copies"].items()),
            inline=False,
        )
    if evidence.get("check_unavailable"):
        embed.add_field(
            name="Verification unavailable",
            value="The latest check failed. The evidence above is the last successful observation. Automatic checks will retry; repair choices are disabled until verification succeeds.",
            inline=False,
        )
    if row.get("pending_action"):
        embed.add_field(
            name="Repair being verified",
            value=f"The accepted repair is {row['pending_action']['state']}. The bot will reconcile its existing receipt on the next monitor cycle. No second repair will be dispatched. Use Recheck for current progress.",
            inline=False,
        )
    if row.get("release_notice"):
        embed.add_field(name="Release coverage", value=row["release_notice"], inline=False)
    elif row["State"] != "resolved" and not evidence["actions"]:
        embed.add_field(
            name="Recovery checks",
            value="No repair is currently authorised by the evidence. Recheck to refresh the diagnosis. This incident remains open.",
            inline=False,
        )
    embed.set_footer(text=FOOTER_PREFIX + row["IncidentID"])
    return embed


async def report_error(interaction, exc):
    logger.warning("recovery_interaction_unavailable error_type=%s", type(exc).__name__)
    text = (
        str(exc)
        if isinstance(exc, SourceConflict)
        else "Recovery is temporarily unavailable. The incident is retained. Reopen Review & fix to recheck; a submitted repair will be verified before any further action."
    )
    await send_ephemeral(interaction, text, allowed_mentions=discord.AllowedMentions.none())


async def show_incident(interaction, incident_id):
    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        row = await call("review", actor, incident_id)
        await interaction.followup.send(
            embed=incident_embed(row),
            view=RecoveryIncidentView(row),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class RecoveryConfirmView(discord.ui.View):
    def __init__(self, row, action):
        super().__init__(timeout=300)
        self.row, self.action = row, action

    @discord.ui.button(label="Confirm & apply repair", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction):
        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await call(
                "execute",
                actor,
                self.row["IncidentID"],
                self.row["Revision"],
                self.row["EvidenceHash"],
                self.action,
                "Admin confirmed the displayed checks and repair consequences",
            )
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


class RecoveryIncidentView(discord.ui.View):
    def __init__(self, row):
        super().__init__(timeout=300)
        self.row = row
        delivery = row["evidence"].get("delivery") or {}
        links_to_jobs = []
        if row["evidence"].get("evidence_recovery_job_id"):
            links_to_jobs.append(
                (
                    row["evidence"].get("evidence_recovery_label", "Recover replacement check"),
                    row["evidence"]["evidence_recovery_job_id"],
                )
            )
        if delivery.get("job_id"):
            links_to_jobs.append(("Review replacement export", delivery["job_id"]))
        blockers = row["evidence"].get("blocking_job_ids", [])
        if blockers:
            links_to_jobs.append(("Review blocking recovery", blockers[0]))
        recovery_links = [(label, "export_job", job) for label, job in links_to_jobs]
        recovery_links.extend(
            (link["label"], link["kind"], link["source_id"])
            for link in row["evidence"].get("recovery_links", [])[:3]
        )
        for label, linked_kind, linked_job in recovery_links:
            # A verified rollback closes the old attempt, but the admin still
            # needs the separate fresh-publication/keep-prior decision. Opening
            # that linked incident rechecks authorization and current evidence.
            if row["State"] == "resolved" and linked_kind != "configuration_continuation":
                continue
            linked = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)

            async def review_replacement(
                interaction, linked_job=linked_job, linked_kind=linked_kind
            ):
                try:
                    actor = actor_for(interaction)
                    if not await safe_defer(interaction, ephemeral=True):
                        return
                    current = await call("review_source", actor, linked_kind, linked_job)
                    await interaction.followup.send(
                        embed=incident_embed(current),
                        view=RecoveryIncidentView(current),
                        ephemeral=True,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except Exception as exc:
                    await report_error(interaction, exc)

            linked.callback = review_replacement
            self.add_item(linked)
        if row["evidence"].get("targets"):
            links = discord.ui.Button(
                label="Review output links", style=discord.ButtonStyle.secondary
            )

            async def review_links(interaction):
                from ui.views.recovery_target_view import show_target_page

                await show_target_page(interaction, row["IncidentID"], 0)

            links.callback = review_links
            self.add_item(links)
        actions = (
            {}
            if row.get("pending_action") or row["evidence"].get("check_unavailable")
            else row["evidence"]["actions"]
        )
        for action, details in actions.items():
            button = discord.ui.Button(label=details["label"], style=discord.ButtonStyle.primary)

            async def preview(interaction, action=action):
                try:
                    actor = actor_for(interaction)
                    if not await safe_defer(interaction, ephemeral=True):
                        return
                    current = await call("review", actor, self.row["IncidentID"])
                    detail = current["evidence"]["actions"].get(action)
                    if not detail:
                        await interaction.followup.send(
                            embed=incident_embed(current),
                            view=RecoveryIncidentView(current),
                            ephemeral=True,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                        return
                    if detail.get("input") is True:
                        from ui.views.recovery_input_view import show_input_page

                        page = await call("input_page", actor, current["IncidentID"], action, 0)
                        await show_input_page(interaction, page)
                        return
                    if detail.get("review_details") is True:
                        from ui.views.recovery_review_view import show_review_page

                        await show_review_page(interaction, current, action, 0, deferred=True)
                        return
                    embed = discord.Embed(title=detail["label"], color=0xF1C40F)
                    embed.add_field(
                        name="Check before confirming", value=detail["check"], inline=False
                    )
                    embed.add_field(
                        name="What the bot will do", value=detail["effect"], inline=False
                    )
                    embed.add_field(
                        name="Verification",
                        value="The bot rechecks ownership and the required execution evidence before applying this repair and verifies settlement afterwards.",
                        inline=False,
                    )
                    await interaction.followup.send(
                        embed=embed,
                        view=RecoveryConfirmView(current, action),
                        ephemeral=True,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except Exception as exc:
                    await report_error(interaction, exc)

            button.callback = preview
            self.add_item(button)

    @discord.ui.button(label="Recheck", style=discord.ButtonStyle.secondary)
    async def recheck(self, button, interaction):
        await show_incident(interaction, self.row["IncidentID"])


class RecoveryListView(discord.ui.View):
    def __init__(self, rows):
        super().__init__(timeout=300)
        select = discord.ui.Select(
            placeholder="Choose an incident",
            options=[
                discord.SelectOption(
                    label=f"{row['evidence']['title']} — {row['evidence'].get('outcome', 'unknown')}"[
                        :100
                    ],
                    value=row["IncidentID"],
                    description=f"First seen {row['FirstSeenUTC']}"[:100],
                )
                for row in rows
            ],
        )

        async def selected(interaction):
            await show_incident(interaction, select.values[0])

        select.callback = selected
        self.add_item(select)
        if len(rows) == 20:
            next_button = discord.ui.Button(
                label="Next incidents", style=discord.ButtonStyle.secondary
            )

            async def next_page(interaction):
                await show_centre(interaction, after=rows[-1]["IncidentID"])

            next_button.callback = next_page
            self.add_item(next_button)


async def show_centre(interaction, after=None):
    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        rows = await call("list_open", actor, after)
        await interaction.followup.send(
            (
                "Choose an incident to review its evidence and available repairs."
                if rows
                else "No further open incidents in the current recovery scope. Coverage is limited to installed recovery adapters."
            ),
            view=RecoveryListView(rows) if rows else RecoveryEntryView(),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class RecoveryEntryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Review & fix", custom_id="k98:recovery:review:v1", style=discord.ButtonStyle.primary
    )
    async def review(self, button, interaction):
        try:
            actor_for(interaction)
            embeds = getattr(interaction.message, "embeds", [])
            footer = embeds[0].footer.text if embeds else None
            if footer and footer.startswith(FOOTER_PREFIX):
                incident_id = str(UUID(footer[len(FOOTER_PREFIX) :]))
                await show_incident(interaction, incident_id)
            else:
                await show_centre(interaction)
        except Exception as exc:
            await report_error(interaction, exc)

    @discord.ui.button(
        label="Open recovery centre",
        custom_id="k98:recovery:centre:v1",
        style=discord.ButtonStyle.secondary,
    )
    async def centre(self, button, interaction):
        await show_centre(interaction)
