from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging

import discord

from account_picker import build_unique_gov_options
from core.interaction_safety import send_ephemeral
from mge import mge_dm_followup, mge_signup_service
from mge.dal import mge_signup_dal
from mge.mge_cache import get_commanders_for_variant
from mge.mge_signup_service import ServiceResult
from ui.views.mge_admin_view import ConfirmSwitchOpenView, MGEAdminViewDeps
from ui.views.mge_signup_modal import MgeSignupModalPayload, MgeSignupPrimaryModal

logger = logging.getLogger(__name__)


def _member_role_ids(interaction: discord.Interaction) -> set[int]:
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if not member and interaction.guild:
        member = interaction.guild.get_member(interaction.user.id)
    if not member:
        return set()
    return {int(r.id) for r in getattr(member, "roles", []) if getattr(r, "id", None)}


class MGESignupView(discord.ui.View):
    def __init__(self, event_id: int, admin_deps: MGEAdminViewDeps, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)
        self.admin_deps = admin_deps

    def _admin_role_ids(self) -> set[int]:
        role_ids = set()
        for attr in ("admin_role_ids", "leadership_role_ids"):
            vals = getattr(self.admin_deps, attr, None)
            if isinstance(vals, (list, set, tuple)):
                role_ids.update(int(v) for v in vals)
        return role_ids

    async def _open_signup_modal(
        self,
        interaction: discord.Interaction,
        *,
        governor_id: int,
        governor_name: str,
        signup_id: int | None = None,
    ) -> None:
        event = mge_signup_dal.fetch_event_signup_context(self.event_id)
        if not event:
            await send_ephemeral(interaction, "❌ Event not found.")
            return

        variant_name = str(event.get("VariantName") or "").strip()
        commander_rows = get_commanders_for_variant(variant_name)
        commander_options: dict[int, str] = {}
        for row in commander_rows:
            try:
                cid = int(row["CommanderId"])
                cname = str(row.get("CommanderName") or "").strip()
                if cname:
                    commander_options[cid] = cname
            except Exception:
                continue

        if not commander_options:
            await send_ephemeral(
                interaction,
                "❌ Commander cache is unavailable for this variant. Please try again later.",
            )
            return

        payload = MgeSignupModalPayload(
            event_id=self.event_id,
            governor_id=int(governor_id),
            governor_name=governor_name,
            actor_role_ids=_member_role_ids(interaction),
            admin_role_ids=self._admin_role_ids(),
            signup_id=signup_id,
        )
        modal = MgeSignupPrimaryModal(
            payload=payload,
            commander_options=commander_options,
            title="Edit MGE Signup" if signup_id else "Create MGE Signup",
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Sign Up", style=discord.ButtonStyle.primary, custom_id="mge_signup")
    async def sign_up(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        linked = await asyncio.to_thread(
            mge_signup_service.get_linked_governors_for_user, interaction.user.id
        )
        if not linked:
            await send_ephemeral(
                interaction,
                "❌ No linked governors found. Please register first.",
            )
            return

        if len(linked) == 1:
            gov = linked[0]
            await self._open_signup_modal(
                interaction,
                governor_id=int(gov["GovernorID"]),
                governor_name=str(gov["GovernorName"]),
            )
            return

        accounts = {
            f"Account {idx + 1}": {"GovernorID": g["GovernorID"], "GovernorName": g["GovernorName"]}
            for idx, g in enumerate(linked)
        }
        options = build_unique_gov_options(accounts)

        class _GovSelect(discord.ui.Select):
            def __init__(self, parent_view: MGESignupView):
                super().__init__(
                    placeholder="Select governor to sign up",
                    min_values=1,
                    max_values=1,
                    options=options[:25],
                )
                self.parent_view = parent_view

            async def callback(self, select_interaction: discord.Interaction):
                gid = int(self.values[0])
                gov = next((g for g in linked if int(g["GovernorID"]) == gid), None)
                if not gov:
                    await send_ephemeral(select_interaction, "❌ Governor selection failed.")
                    return
                await self.parent_view._open_signup_modal(
                    select_interaction,
                    governor_id=gid,
                    governor_name=str(gov["GovernorName"]),
                )

        picker = discord.ui.View(timeout=180)
        picker.add_item(_GovSelect(self))
        await send_ephemeral(interaction, "Select a governor for signup:", view=picker)

    @discord.ui.button(
        label="Withdraw", style=discord.ButtonStyle.secondary, custom_id="mge_withdraw"
    )
    async def withdraw(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        rows = mge_signup_dal.fetch_active_signups_by_event_discord(
            self.event_id, interaction.user.id
        )
        if not rows:
            await send_ephemeral(interaction, "❌ No active signup found for this event.")
            return

        if len(rows) == 1:
            row = rows[0]
            result = mge_signup_service.withdraw_signup(
                signup_id=int(row["SignupId"]),
                event_id=int(row["EventId"]),
                governor_id=int(row["GovernorId"]),
                actor_discord_id=interaction.user.id,
                actor_role_ids=_member_role_ids(interaction),
                admin_role_ids=self._admin_role_ids(),
                now_utc=datetime.now(UTC),
            )
            await send_ephemeral(
                interaction, "✅ " + result.message if result.success else "❌ " + result.message
            )
            return

        class _WithdrawSelect(discord.ui.Select):
            def __init__(self, parent_view: MGESignupView):
                options: list[discord.SelectOption] = []
                for r in rows[:25]:
                    gov_name = str(r.get("GovernorNameSnapshot") or f"Governor {r['GovernorId']}")
                    value = f"{int(r['SignupId'])}|{int(r['GovernorId'])}|{int(r['EventId'])}"
                    options.append(
                        discord.SelectOption(
                            label=gov_name[:100],
                            description=f"Signup ID {int(r['SignupId'])}",
                            value=value,
                        )
                    )
                super().__init__(
                    placeholder="Select signup to withdraw",
                    min_values=1,
                    max_values=1,
                    options=options,
                )
                self.parent_view = parent_view

            async def callback(self, select_interaction: discord.Interaction) -> None:
                try:
                    signup_id_s, governor_id_s, event_id_s = self.values[0].split("|", 2)
                    signup_id = int(signup_id_s)
                    governor_id = int(governor_id_s)
                    event_id = int(event_id_s)
                except Exception:
                    await send_ephemeral(select_interaction, "❌ Failed to parse selection.")
                    return

                result = mge_signup_service.withdraw_signup(
                    signup_id=signup_id,
                    event_id=event_id,
                    governor_id=governor_id,
                    actor_discord_id=select_interaction.user.id,
                    actor_role_ids=_member_role_ids(select_interaction),
                    admin_role_ids=self.parent_view._admin_role_ids(),
                    now_utc=datetime.now(UTC),
                )
                await send_ephemeral(
                    select_interaction,
                    "✅ " + result.message if result.success else "❌ " + result.message,
                )

        picker = discord.ui.View(timeout=180)
        picker.add_item(_WithdrawSelect(self))
        await send_ephemeral(
            interaction,
            "You have multiple active signups. Select one to withdraw:",
            view=picker,
        )

    @discord.ui.button(
        label="View / Edit My Request",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_edit",
    )
    async def edit(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        rows = mge_signup_dal.fetch_active_signups_by_event_discord(
            self.event_id, interaction.user.id
        )
        if not rows:
            await send_ephemeral(interaction, "❌ No active signup found for this event.")
            return

        if len(rows) == 1:
            row = rows[0]
            await self._open_signup_modal(
                interaction,
                governor_id=int(row["GovernorId"]),
                governor_name=str(row.get("GovernorNameSnapshot") or "Unknown"),
                signup_id=int(row["SignupId"]),
            )
            return

        class _EditSelect(discord.ui.Select):
            def __init__(self, parent_view: MGESignupView):
                options: list[discord.SelectOption] = []
                for r in rows[:25]:
                    gov_name = str(r.get("GovernorNameSnapshot") or f"Governor {r['GovernorId']}")
                    value = f"{int(r['SignupId'])}|{int(r['GovernorId'])}"
                    options.append(
                        discord.SelectOption(
                            label=gov_name[:100],
                            description=f"Signup ID {int(r['SignupId'])}",
                            value=value,
                        )
                    )
                super().__init__(
                    placeholder="Select signup to edit",
                    min_values=1,
                    max_values=1,
                    options=options,
                )
                self.parent_view = parent_view

            async def callback(self, select_interaction: discord.Interaction) -> None:
                try:
                    signup_id_s, governor_id_s = self.values[0].split("|", 1)
                    signup_id = int(signup_id_s)
                    governor_id = int(governor_id_s)
                except Exception:
                    await send_ephemeral(select_interaction, "❌ Failed to parse selection.")
                    return

                row = next((r for r in rows if int(r["SignupId"]) == signup_id), None)
                governor_name = (
                    str(row.get("GovernorNameSnapshot") or "Unknown") if row else "Unknown"
                )

                await self.parent_view._open_signup_modal(
                    select_interaction,
                    governor_id=governor_id,
                    governor_name=governor_name,
                    signup_id=signup_id,
                )

        picker = discord.ui.View(timeout=180)
        picker.add_item(_EditSelect(self))
        await send_ephemeral(
            interaction,
            "You have multiple active signups. Select one to edit:",
            view=picker,
        )

    @discord.ui.button(
        label="Switch to Open",
        style=discord.ButtonStyle.danger,
        custom_id="mge_switch_open",
        row=1,
    )
    async def switch_to_open(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not self.admin_deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return

        confirm_view = ConfirmSwitchOpenView(event_id=self.event_id, deps=self.admin_deps)
        await send_ephemeral(
            interaction,
            "⚠️ This will delete all existing signups for this event. Confirm?",
            view=confirm_view,
        )

    @discord.ui.button(
        label="Edit Rules",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="mge_edit_rules",
    )
    async def edit_rules(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if not self.admin_deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return
        await send_ephemeral(interaction, "Rules editor hook.")

    @discord.ui.button(
        label="Refresh Embed",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="mge_refresh_embed",
    )
    async def refresh(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if not self.admin_deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return
        self.admin_deps.refresh_embed(self.event_id)
        await send_ephemeral(interaction, "Embed refresh requested.")

    @discord.ui.button(
        label="Open Leadership Board",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="mge_open_leadership_board",
    )
    async def leadership(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        if not self.admin_deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return
        await send_ephemeral(interaction, "Leadership board hook.")

    async def maybe_offer_dm_followup(
        self,
        *,
        interaction: discord.Interaction,
        result: ServiceResult,
        event_id: int,
        event_name: str,
    ) -> None:
        """
        Offer and initiate optional DM follow-up after successful signup create/edit.
        """
        if not result.success or result.signup_id is None:
            return

        user = interaction.user
        if not isinstance(user, (discord.Member, discord.User)):
            return

        ok, msg = await mge_dm_followup.open_dm_followup(
            user=user,
            event_id=event_id,
            signup_id=int(result.signup_id),
            event_name=event_name,
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            logger.exception(
                "mge_signup_view_dm_followup_notice_failed event_id=%s signup_id=%s dm_open_ok=%s",
                event_id,
                result.signup_id,
                ok,
            )
