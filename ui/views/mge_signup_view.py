from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging

import discord

from account_picker import build_unique_gov_options
from bot_config import MGE_LEADERSHIP_CHANNEL_ID, MGE_SIMPLIFIED_FLOW_ENABLED
from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_interaction, is_admin_or_leadership_interaction
from mge import mge_dm_followup, mge_signup_service
from mge.dal import mge_signup_dal
from mge.mge_cache import get_commanders_for_variant
from mge.mge_signup_service import ServiceResult
from ui.views.mge_admin_completion_view import MgeAdminCompletionView
from ui.views.mge_admin_view import ConfirmSwitchFixedView, ConfirmSwitchOpenView, MGEAdminViewDeps
from ui.views.mge_rules_edit_view import MgeRulesEditView
from ui.views.mge_signup_form_view import MgeSignupFormView
from ui.views.mge_signup_modal import MgeSignupModalPayload

logger = logging.getLogger(__name__)


class MgeSignupPrimaryModal(MgeSignupFormView):
    """Compatibility wrapper for the primary MGE signup selection step."""

    def __init__(self, *, title: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title


_LOCK_MESSAGE = "❌ This MGE is published or completed and is locked. Please contact an admin if a change is required."


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

    async def _event_is_locked(self) -> bool:
        event = await asyncio.to_thread(mge_signup_dal.fetch_event_signup_context, self.event_id)
        if not event:
            return False
        status = str(event.get("Status") or "").strip().lower()
        event_mode = str(event.get("EventMode") or "").strip().lower()
        return status in {"published", "completed"} or event_mode == "published"

    async def _block_if_locked(self, interaction: discord.Interaction) -> bool:
        if await self._event_is_locked():
            await send_ephemeral(interaction, _LOCK_MESSAGE)
            return True
        return False

    async def _is_signup_closed(self) -> bool:
        """Check if signups are closed based on SignupCloseUtc."""
        event = await asyncio.to_thread(mge_signup_dal.fetch_event_signup_context, self.event_id)
        if not event:
            return False
        status = str(event.get("Status") or "").strip().lower()
        if status in {"completed", "finished"}:
            return True
        close_utc = event.get("SignupCloseUtc")
        if close_utc is None:
            return False
        now = datetime.now(UTC)
        if isinstance(close_utc, datetime):
            close_aware = close_utc.replace(tzinfo=UTC) if close_utc.tzinfo is None else close_utc
            return now >= close_aware
        return False

    async def _block_if_signup_closed(self, interaction: discord.Interaction) -> bool:
        """Backend gating layer: reject interactions when signups are closed."""
        if await self._is_signup_closed():
            await send_ephemeral(
                interaction,
                "❌ Signups are now closed. Contact leadership for changes.",
            )
            logger.info(
                "mge_signup_blocked_after_close event_id=%s user_id=%s",
                self.event_id,
                interaction.user.id,
            )
            return True
        return False

    async def _open_signup_modal(
        self,
        interaction: discord.Interaction,
        *,
        governor_id: int,
        governor_name: str,
        signup_id: int | None = None,
    ) -> None:
        if await self._block_if_locked(interaction):
            return

        event = await asyncio.to_thread(mge_signup_dal.fetch_event_signup_context, self.event_id)
        if not event:
            await send_ephemeral(interaction, "❌ Event not found.")
            return

        if signup_id is None:
            existing = await asyncio.to_thread(
                mge_signup_dal.fetch_active_signup_by_event_governor,
                self.event_id,
                int(governor_id),
            )
            if existing:
                await send_ephemeral(
                    interaction,
                    "❌ An active signup already exists for this governor/event. "
                    "Use **View / Edit My Request**.",
                )
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
            on_success_refresh=self.admin_deps.refresh_embed,
        )

        initial_priority = None
        initial_rank_band = None
        initial_commander_id = None
        initial_current_heads = None
        initial_kingdom_role = None
        initial_gear_text = None
        initial_armament_text = None

        if signup_id is not None:
            row = await asyncio.to_thread(mge_signup_dal.fetch_signup_by_id, int(signup_id))
            if row:
                initial_priority = str(row.get("RequestPriority") or "").strip() or None
                initial_rank_band = str(row.get("PreferredRankBand") or "").strip() or None
                try:
                    initial_commander_id = int(row.get("RequestedCommanderId"))
                except Exception:
                    initial_commander_id = None
                try:
                    initial_current_heads = int(row.get("CurrentHeads"))
                except Exception:
                    initial_current_heads = None
                initial_kingdom_role = str(row.get("KingdomRole") or "").strip() or None
                initial_gear_text = str(row.get("GearText") or "").strip() or None
                initial_armament_text = str(row.get("ArmamentText") or "").strip() or None

        title = "Edit MGE Signup" if signup_id is not None else "Create MGE Signup"
        primary_step = MgeSignupPrimaryModal(
            payload=payload,
            commander_options=commander_options,
            is_edit=signup_id is not None,
            initial_priority=initial_priority,
            initial_rank_band=initial_rank_band,
            initial_commander_id=initial_commander_id,
            initial_current_heads=initial_current_heads,
            initial_kingdom_role=initial_kingdom_role,
            initial_gear_text=initial_gear_text,
            initial_armament_text=initial_armament_text,
            timeout=300,
            title=title,
        )

        await send_ephemeral(
            interaction,
            (
                "✏️ Edit existing signup: review selections and click **Continue**."
                if signup_id is not None
                else "🆕 Create signup: choose selections and click **Continue**."
            ),
            view=primary_step,
        )

    async def sync_embed(
        self,
        *,
        bot: discord.Client,
        signup_channel_id: int,
        announce_everyone: bool = False,
        is_rehydrate: bool = False,
        now_utc: datetime | None = None,
    ) -> bool:
        """
        Sync the signup embed for this event.

        announce_everyone=True should be used only when the embed is first posted
        or when the event mode is explicitly switched between fixed/open.
        """
        from mge.mge_embed_manager import sync_event_signup_embed

        return await sync_event_signup_embed(
            bot=bot,
            event_id=self.event_id,
            signup_channel_id=signup_channel_id,
            now_utc=now_utc,
            announce_everyone=announce_everyone,
            is_rehydrate=is_rehydrate,
        )

    @discord.ui.button(label="Sign Up", style=discord.ButtonStyle.primary, custom_id="mge_signup")
    async def sign_up(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if await self._block_if_signup_closed(interaction):
            return
        if await self._block_if_locked(interaction):
            return

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
                if await self.parent_view._block_if_locked(select_interaction):
                    return
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
        del button
        if await self._block_if_signup_closed(interaction):
            return
        if await self._block_if_locked(interaction):
            return

        rows = await asyncio.to_thread(
            mge_signup_dal.fetch_active_signups_by_event_discord,
            self.event_id,
            interaction.user.id,
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
            if result.success:
                self.admin_deps.refresh_embed(self.event_id)
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
                if await self.parent_view._block_if_locked(select_interaction):
                    return
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
                if result.success:
                    self.parent_view.admin_deps.refresh_embed(self.parent_view.event_id)

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
        del button
        if await self._block_if_signup_closed(interaction):
            return
        if await self._block_if_locked(interaction):
            return

        rows = await asyncio.to_thread(
            mge_signup_dal.fetch_active_signups_by_event_discord,
            self.event_id,
            interaction.user.id,
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
                if await self.parent_view._block_if_locked(select_interaction):
                    return
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
        row=2,
    )
    async def switch_to_open(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
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
        label="Switch to Fixed",
        style=discord.ButtonStyle.danger,
        custom_id="mge_switch_fixed",
        row=2,
    )
    async def switch_to_fixed(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not self.admin_deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return

        confirm_view = ConfirmSwitchFixedView(event_id=self.event_id, deps=self.admin_deps)
        await send_ephemeral(
            interaction,
            "⚠️ This will switch the event back to fixed mode without deleting signups. Confirm?",
            view=confirm_view,
        )

    @discord.ui.button(
        label="Edit Rules",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_edit_rules",
        row=1,
    )
    async def edit_rules(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        view = MgeRulesEditView(event_id=self.event_id)
        await send_ephemeral(
            interaction,
            f"📝 Rules editor opened for event `{self.event_id}`.",
            view=view,
        )

    @discord.ui.button(
        label="Refresh Embed",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_refresh_embed",
        row=1,
    )
    async def refresh_embed_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not self.admin_deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return

        try:
            from mge import mge_embed_manager
            from mge.dal import mge_event_dal

            row = mge_event_dal.fetch_event_for_embed(self.event_id)
            if not row:
                await send_ephemeral(interaction, "❌ Event not found.")
                return

            names = mge_event_dal.fetch_public_signup_names(self.event_id)
            embed = mge_embed_manager.build_mge_signup_embed(row, public_signup_names=names)

            await interaction.message.edit(
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            )
            await send_ephemeral(interaction, "✅ Embed refreshed.")
        except Exception:
            logger.exception("mge_refresh_embed_failed event_id=%s", self.event_id)
            await send_ephemeral(interaction, "❌ Failed to refresh embed.")

    @discord.ui.button(
        label="Open Leadership Board",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="mge_open_leadership_board",
    )
    async def leadership(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        if MGE_SIMPLIFIED_FLOW_ENABLED:
            from mge.mge_embed_manager import sync_event_leadership_embed

            refreshed = await sync_event_leadership_embed(
                bot=interaction.client,
                event_id=self.event_id,
                channel_id=MGE_LEADERSHIP_CHANNEL_ID,
            )
            if refreshed:
                await send_ephemeral(
                    interaction,
                    f"✅ Leadership control center refreshed in <#{int(MGE_LEADERSHIP_CHANNEL_ID)}> for event `{self.event_id}`.",
                )
            else:
                await send_ephemeral(interaction, "❌ Failed to refresh leadership control center.")
            return
        from ui.views.mge_leadership_board_view import MgeLeadershipBoardView

        view = MgeLeadershipBoardView(event_id=self.event_id)
        await send_ephemeral(
            interaction,
            f"📋 Leadership board opened for event `{self.event_id}`.",
            view=view,
        )

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

    @discord.ui.button(
        label="Completion Controls",
        style=discord.ButtonStyle.secondary,
        row=2,
        custom_id="mge_admin_completion_controls",
    )
    async def completion_controls_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if not is_admin_interaction(interaction):
            await send_ephemeral(
                interaction, "You do not have permission to access completion controls."
            )
            return

        await send_ephemeral(
            interaction,
            "Opened completion controls.",
            view=MgeAdminCompletionView(
                event_id=self.event_id,
                leadership_channel_id=MGE_LEADERSHIP_CHANNEL_ID,
                timeout=300,
            ),
        )
