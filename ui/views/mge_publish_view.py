from __future__ import annotations

import asyncio
from typing import Any

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_or_leadership_interaction
from mge import mge_publish_service
from mge.dal import mge_publish_dal

MAX_REMINDERS_TEXT_LENGTH = 4000


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _fmt_target(value: Any) -> str:
    try:
        if value is None:
            return "—"
        return f"{int(value):,}"
    except Exception:
        return "—"


def _fmt_rank(value: Any) -> str:
    try:
        if value is None:
            return "—"
        return str(int(value))
    except Exception:
        return "—"


class _AwardSelect(discord.ui.Select):
    def __init__(self, *, options: list[discord.SelectOption], on_pick):
        super().__init__(
            placeholder="Select an awarded player",
            options=options[:25],
            min_values=1,
            max_values=1,
        )
        self._on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self._on_pick(interaction, self.values[0])


class _ConfirmUnpublishView(discord.ui.View):
    def __init__(self, *, event_id: int, parent_view: MgePublishView, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)
        self.parent_view = parent_view

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return False
        return True

    @discord.ui.button(
        label="Confirm Unpublish",
        style=discord.ButtonStyle.danger,
        custom_id="mge_confirm_unpublish",
    )
    async def confirm_unpublish(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        res = await mge_publish_service.unpublish_event_awards(
            bot=interaction.client,
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
        )

        msg = ("✅ " if res.success else "❌ ") + res.message
        if res.success:
            msg += f"\n- Embed deleted: `{res.embed_deleted}`"
            msg += f"\n- Status: `{res.old_status}` → `{res.restored_status}`"
            msg += f"\n- PublishVersion: `{res.old_publish_version}` → `0`"
        await interaction.followup.send(msg, ephemeral=True)
        if res.success:
            self.parent_view.stop()
            self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_cancel_unpublish",
    )
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        await send_ephemeral(interaction, "Cancelled.")
        self.stop()


class MgePublishView(discord.ui.View):
    def __init__(self, *, event_id: int, timeout: float | None = 900) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return False
        return True

    async def _load_awarded_rows(self) -> list[dict[str, Any]]:
        """
        Use the same publish-roster source as the published embed flow, then filter to awarded rows.
        This avoids relying on target-generation-only helpers that may not reflect the current roster.
        """
        rows = await asyncio.to_thread(mge_publish_dal.fetch_awards_with_signup_user, self.event_id)
        return [r for r in rows if _status(r.get("AwardStatus")) == "awarded"]

    @discord.ui.button(label="Generate Targets", style=discord.ButtonStyle.primary, row=0)
    async def generate_targets(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        class _GenerateModal(discord.ui.Modal):
            def __init__(self, parent: MgePublishView):
                super().__init__(title="Generate Targets", timeout=300)
                self.parent = parent
                self.rank1 = discord.ui.InputText(
                    label="Rank 1 Target (millions)", required=True, max_length=6
                )
                self.add_item(self.rank1)

            async def callback(self, modal_interaction: discord.Interaction) -> None:
                if not await self.parent._guard(modal_interaction):
                    return
                try:
                    rank1_m = int(str(self.rank1.value).strip())
                except Exception:
                    await send_ephemeral(modal_interaction, "❌ Invalid rank 1 target.")
                    return

                res = await asyncio.to_thread(
                    mge_publish_service.generate_targets_from_rank1,
                    event_id=self.parent.event_id,
                    rank1_target_millions=rank1_m,
                    actor_discord_id=int(modal_interaction.user.id),
                )
                await send_ephemeral(
                    modal_interaction, ("✅ " if res.success else "❌ ") + res.message
                )

        await interaction.response.send_modal(_GenerateModal(self))

    @discord.ui.button(label="Override Target", style=discord.ButtonStyle.secondary, row=0)
    async def override_target(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        awarded = await self._load_awarded_rows()
        if not awarded:
            await send_ephemeral(interaction, "No awarded rows are available.")
            return

        options: list[discord.SelectOption] = []
        for row in awarded[:25]:
            award_id = _to_int(row.get("AwardId"), 0)
            if award_id <= 0:
                continue

            gov = str(row.get("GovernorNameSnapshot") or "Unknown")
            commander = str(row.get("RequestedCommanderName") or "Unknown")
            rank = _fmt_rank(row.get("AwardedRank"))
            current_target = _fmt_target(row.get("TargetScore"))

            label = f"#{rank} • {gov} • {commander} • current target {current_target}"
            options.append(
                discord.SelectOption(
                    label=label[:100],
                    value=str(award_id),
                )
            )

        if not options:
            await send_ephemeral(interaction, "No selectable awarded rows were found.")
            return

        async def _after_pick(inter: discord.Interaction, award_id_value: str) -> None:
            try:
                aid = int(award_id_value)
            except Exception:
                await send_ephemeral(inter, "❌ Invalid award selection.")
                return

            current_row = next((r for r in awarded if _to_int(r.get("AwardId")) == aid), None)
            if not current_row:
                await send_ephemeral(inter, "❌ Selected award row was not found.")
                return

            class _OverrideModal(discord.ui.Modal):
                def __init__(self, parent: MgePublishView, row: dict[str, Any]):
                    current_target = row.get("TargetScore")
                    super().__init__(title="Override Target Score", timeout=300)
                    self.parent = parent
                    self.award_id = int(row["AwardId"])
                    self.target = discord.ui.InputText(
                        label=f"New Target Score (current: {_fmt_target(current_target)})",
                        required=True,
                        max_length=20,
                        placeholder=str(current_target if current_target is not None else "0"),
                    )
                    self.add_item(self.target)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    try:
                        target = int(str(self.target.value).strip())
                    except Exception:
                        await send_ephemeral(modal_interaction, "❌ Invalid target score.")
                        return

                    res = await asyncio.to_thread(
                        mge_publish_service.override_target_score,
                        award_id=self.award_id,
                        target_score=target,
                        actor_discord_id=int(modal_interaction.user.id),
                    )
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                    )

            await inter.response.send_modal(_OverrideModal(self, current_row))

        view = discord.ui.View(timeout=120.0)
        view.add_item(_AwardSelect(options=options, on_pick=_after_pick))
        await interaction.response.send_message(
            "Select the awarded player whose target you want to override:",
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="Publish / Republish", style=discord.ButtonStyle.success, row=1)
    async def publish(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not await self._guard(interaction):
            return
        ctx = await asyncio.to_thread(mge_publish_dal.fetch_event_publish_context, self.event_id)
        if not ctx:
            await send_ephemeral(interaction, "❌ Event not found.")
            return

        reminders_sent = ctx.get("AwardRemindersSentUtc") is not None
        should_prompt_for_reminders = not reminders_sent

        if should_prompt_for_reminders:
            mode = str(ctx.get("RuleMode") or "").strip().lower()
            default_text = await asyncio.to_thread(
                mge_publish_dal.fetch_default_award_reminders_text,
                mode,
            )
            if not default_text:
                await send_ephemeral(
                    interaction,
                    "❌ No active MGE Award Reminders default is configured in SQL "
                    f"for rule mode `{mode or 'unknown'}`. Please add one in `dbo.MGE_DefaultRules`.",
                )
                return
            if len(default_text) > MAX_REMINDERS_TEXT_LENGTH:
                await send_ephemeral(
                    interaction,
                    "⚠️ Default reminder text exceeds 4000 characters and cannot be prefilled safely.\n"
                    "Please shorten the default in SQL and try again.",
                )
                return

            class _PublishWithRemindersModal(discord.ui.Modal):
                def __init__(self, parent: MgePublishView, prefill_text: str):
                    super().__init__(title="MGE Award Reminders", timeout=300)
                    self.parent = parent
                    self.reminders_text = discord.ui.InputText(
                        label="Reminders (plain text, # sections, !warns)",
                        style=discord.InputTextStyle.long,
                        required=True,
                        max_length=MAX_REMINDERS_TEXT_LENGTH,
                        value=prefill_text,
                    )
                    self.add_item(self.reminders_text)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    entered = str(self.reminders_text.value or "").strip()
                    if not entered:
                        await send_ephemeral(
                            modal_interaction,
                            "❌ MGE Award Reminders text cannot be empty.",
                        )
                        return
                    if len(entered) > MAX_REMINDERS_TEXT_LENGTH:
                        await send_ephemeral(
                            modal_interaction,
                            "❌ MGE Award Reminders text is too long "
                            f"(max {MAX_REMINDERS_TEXT_LENGTH} characters).",
                        )
                        return

                    await modal_interaction.response.defer(ephemeral=True)
                    await self.parent._run_publish(
                        interaction=modal_interaction,
                        reminders_text_override=entered,
                    )

            await interaction.response.send_modal(_PublishWithRemindersModal(self, default_text))
            return

        await interaction.response.defer(ephemeral=True)
        await self._run_publish(interaction=interaction, reminders_text_override=None)

    async def _run_publish(
        self,
        *,
        interaction: discord.Interaction,
        reminders_text_override: str | None,
    ) -> None:
        res = await mge_publish_service.publish_event_awards(
            bot=interaction.client,
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
            reminders_text_override=reminders_text_override,
        )
        text = ("✅ " if res.success else "❌ ") + res.message
        if res.publish_version is not None:
            text += f"\nVersion: `{res.publish_version}`"
        if res.change_lines and res.publish_version and res.publish_version > 1:
            text += f"\nChanges: `{len(res.change_lines)}`"
        if res.reminders_embed_status == "sent":
            text += "\nReminders: `sent`"
        elif res.reminders_embed_status:
            label = {
                "send_failed": f"failed ({res.reminders_embed_status})",
                "persist_failed": f"failed ({res.reminders_embed_status})",
                "mark_failed": f"failed ({res.reminders_embed_status})",
            }.get(res.reminders_embed_status, f"skipped ({res.reminders_embed_status})")
            text += f"\nReminders: `{label}`"
        await interaction.followup.send(text, ephemeral=True)

    @discord.ui.button(label="Unpublish", style=discord.ButtonStyle.danger, row=1)
    async def unpublish(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not await self._guard(interaction):
            return

        await interaction.response.send_message(
            "Are you sure you want to unpublish this MGE event? This will remove the published embed "
            "if possible and roll the event back to an editable state.",
            view=_ConfirmUnpublishView(event_id=self.event_id, parent_view=self),
            ephemeral=True,
        )
