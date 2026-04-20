from __future__ import annotations

import asyncio
import logging

import discord

from core.interaction_safety import send_ephemeral
from mge.dal import mge_signup_dal
from mge.mge_cache import get_commanders_for_variant
from ui.views.mge_simplified_signup_form_view import build_simplified_signup_form_view
from ui.views.mge_signup_modal import MgeSignupModalPayload
from ui.views.mge_signup_view import MGESignupView, _member_role_ids

logger = logging.getLogger(__name__)


class MGESimplifiedSignupView(MGESignupView):
    """
    Simplified public-facing MGE signup view for player/data channel use.

    Extends MGESignupView but:
      - hides admin-only buttons
      - overrides _open_signup_modal to launch the simplified no-modal form view
        (MgeSimplifiedSignupFormView) instead of the old MgeSignupPrimaryModal
    """

    def __init__(self, event_id: int, admin_deps, timeout: float | None = None):
        super().__init__(event_id=event_id, admin_deps=admin_deps, timeout=timeout)
        for item in list(self.children):
            if getattr(item, "custom_id", "") in {
                "mge_switch_open",
                "mge_switch_fixed",
                "mge_edit_rules",
                "mge_refresh_embed",
                "mge_open_leadership_board",
                "mge_admin_completion_controls",
            }:
                self.remove_item(item)

        edit_button = next(
            (child for child in self.children if getattr(child, "custom_id", "") == "mge_edit"),
            None,
        )
        if edit_button is not None:
            edit_button.label = "Edit Sign Up"

    async def _open_signup_modal(
        self,
        interaction: discord.Interaction,
        *,
        governor_id: int,
        governor_name: str,
        signup_id: int | None = None,
    ) -> None:
        """
        Override: launch the simplified signup form view (no modal, no DM).

        For edit flows, fetches the existing signup row and pre-fills the combined
        Priority (Rank) dropdown using get_option_by_priority_rank().
        """
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
                    "Use **Edit Sign Up**.",
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

        existing_signup_row: dict | None = None
        if signup_id is not None:
            existing_signup_row = await asyncio.to_thread(
                mge_signup_dal.fetch_signup_by_id, int(signup_id)
            )

        form_view = build_simplified_signup_form_view(
            payload=payload,
            commander_options=commander_options,
            is_edit=signup_id is not None,
            existing_signup_row=existing_signup_row,
            timeout=300,
        )

        await send_ephemeral(
            interaction,
            (
                "✏️ Edit your signup: update selections and click **Sign Up**."
                if signup_id is not None
                else "🆕 Sign up: choose Priority (Rank) and Commander, then click **Sign Up**."
            ),
            view=form_view,
        )
