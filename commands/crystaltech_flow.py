"""CrystalTech interaction flow helpers."""

from __future__ import annotations

import logging

import discord

from core.interaction_safety import send_or_followup
from crystaltech_di import get_crystaltech_service
from services.governor_account_service import resolve_governor_label
from services.governor_session_lock_service import (
    claim_governor_session,
    refresh_governor_session,
    release_governor_session,
)

try:
    from crystaltech_ui import ProgressView, SetupView
except Exception:
    ProgressView = None
    SetupView = None
    logging.getLogger(__name__).exception(
        "Optional import failed: crystaltech_ui.ProgressView/SetupView not available"
    )

logger = logging.getLogger(__name__)


async def run_crystaltech_flow(
    interaction: discord.Interaction, governor_id: str, ephemeral: bool
) -> None:
    """Open CrystalTech setup/progress flow for a governor."""

    try:
        claim = await claim_governor_session(governor_id, interaction.user.id)
    except Exception as exc:
        logger.exception("[CrystalTech] lock acquisition failed")
        await send_or_followup(
            interaction,
            f"CrystalTech session locking is unavailable: `{type(exc).__name__}`",
            ephemeral=True,
        )
        return

    if not claim.acquired:
        await send_or_followup(interaction, f"Locked: {claim.message}", ephemeral=True)
        return

    async def _release() -> None:
        try:
            await release_governor_session(governor_id, interaction.user.id)
        except Exception:
            logger.exception("[CrystalTech] _release failed for governor_id=%s", governor_id)

    try:
        if ProgressView is None or SetupView is None:
            await send_or_followup(
                interaction,
                "CrystalTech UI is unavailable in this environment.",
                ephemeral=True,
            )
            await _release()
            return

        try:
            service = get_crystaltech_service()
        except Exception as exc:
            await send_or_followup(
                interaction,
                f"CrystalTech is unavailable: `{exc}`",
                ephemeral=True,
            )
            await _release()
            return

        rep = service.report()
        if not service.is_ready:
            msg = rep.summary() if rep else "Service not initialized."
            await send_or_followup(interaction, msg, ephemeral=True)
            await _release()
            return

        entry = service.get_user_entry(governor_id)
        if entry:
            path_id = entry.get("selected_path_id")
            troop = entry.get("selected_troop_type", "unknown")
            view = ProgressView(
                author_id=interaction.user.id,
                governor_id=governor_id,
                path_id=path_id,
                troop=troop,
                timeout=300,
                on_release=_release,
            )
            embed, files = await view.render_embed()

            try:
                await interaction.response.edit_message(
                    content="Opening progress...", embed=None, view=None, attachments=[]
                )
            except Exception:
                logger.debug("[CrystalTech] picker edit before progress failed", exc_info=True)

            sent = await interaction.followup.send(
                embed=embed, files=files, ephemeral=ephemeral, view=view
            )
            view.message = sent
            await refresh_governor_session(governor_id, interaction.user.id)
            return

        label = await resolve_governor_label(interaction.user.id, governor_id)
        view = SetupView(
            author_id=interaction.user.id,
            accounts=[(governor_id, label)],
            timeout=300,
            on_release=_release,
        )
        embed = view.make_embed()

        try:
            await interaction.response.edit_message(
                content="Opening setup...", embed=None, view=None, attachments=[]
            )
        except Exception:
            logger.debug("[CrystalTech] picker edit before setup failed", exc_info=True)

        sent = await interaction.followup.send(embed=embed, ephemeral=ephemeral, view=view)
        view.message = sent
        await refresh_governor_session(governor_id, interaction.user.id)

    except Exception as exc:
        logger.exception("[CrystalTech] run_crystaltech_flow unhandled")
        await send_or_followup(
            interaction,
            f"Unexpected error: `{type(exc).__name__}: {exc}`",
            ephemeral=True,
        )
        await _release()
