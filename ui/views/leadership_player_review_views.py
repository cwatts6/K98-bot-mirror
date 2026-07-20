"""Private, author-gated interaction lifecycle for /stats player."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from io import BytesIO
import logging
from typing import Any
from uuid import UUID, uuid4

import discord

from core.interaction_safety import safe_defer
from core.leadership_player_permissions import (
    LeadershipPlayerAuthorization,
    actor_guild_channel_ids,
    authorize_leadership_player_interaction,
    reauthorize_leadership_player_interaction,
)
from leadership_player_review import renderer, service
from leadership_player_review.models import LeadershipPlayerPayload, LookupCandidate, ReviewPage

logger = logging.getLogger(__name__)

_PAGE_LABELS: dict[ReviewPage, str] = {
    "overview": "Overview",
    "activity": "Kingdom Activity",
    "kvk": "KVK Performance",
    "record": "Player Record",
}


def _close_file(file: discord.File | None) -> None:
    if file is None:
        return
    try:
        file.close()
    except Exception:
        fp = getattr(file, "fp", None)
        try:
            if fp is not None:
                fp.close()
        except Exception:
            pass


def _card_file(payload: LeadershipPlayerPayload) -> discord.File:
    rendered = renderer.render_leadership_player(payload)
    return discord.File(BytesIO(rendered.image_bytes), filename=rendered.filename)


def build_fallback_embed(payload: LeadershipPlayerPayload) -> discord.Embed:
    header = payload.header
    colour = {
        "CURRENT": discord.Color.green(),
        "STALE": discord.Color.orange(),
        "PARTIAL": discord.Color.orange(),
        "NO DATA": discord.Color.red(),
    }[payload.freshness]
    embed = discord.Embed(
        title=f"{header.governor_name or 'Governor'} ({header.governor_id})",
        description=(
            f"**{_PAGE_LABELS[payload.page]} · {payload.period_days} days · {payload.freshness}**\n"
            "Private leadership review. Image rendering was unavailable; these values use the same payload."
        ),
        color=colour,
    )
    embed.add_field(
        name="Header",
        value=(
            f"Alliance: {header.current_alliance or 'Unallied'}\n"
            f"Power: {header.current_power if header.current_power is not None else '—'}\n"
            f"City Hall: {header.city_hall if header.city_hall is not None else '—'}"
        ),
        inline=True,
    )
    current = payload.current_presence
    embed.add_field(
        name="Presence",
        value=(
            f"Scans: {current.present_scans}/{current.complete_scans}\n"
            f"Scanned days: {current.present_scanned_days}/{current.scanned_days}"
            if current
            else "NO DATA"
        ),
        inline=True,
    )
    if payload.page in {"overview", "activity"}:
        lines = []
        for metric in payload.metrics:
            total = metric.current_total if metric.current_total is not None else "—"
            rank = (
                f"#{metric.kingdom_rank}/{metric.cohort_count}"
                if metric.kingdom_rank
                else "rank unavailable"
            )
            lines.append(f"{metric.code.replace('_', ' ').title()}: {total} · {rank}")
        embed.add_field(name="Activity", value="\n".join(lines) or "NO DATA", inline=False)
    elif payload.page == "kvk":

        def number(value: int | None) -> str:
            return f"{value:,}" if value is not None else "—"

        lines = [
            f"KVK {row.kvk_no}: KP {number(row.kill_points)} · Tanking {row.tanking_score if row.tanking_score is not None else '—'} · DKP {number(row.dkp)}"
            for row in payload.kvk_rows
        ]
        embed.add_field(
            name="Ended/finalized KVKs", value="\n".join(lines) or "NO DATA", inline=False
        )
    else:
        linked = [f"{row.governor_name} ({row.governor_id})" for row in payload.linked_governors]
        embed.add_field(
            name="Active linked governors", value="\n".join(linked) or "None found", inline=False
        )
    embed.set_footer(
        text="Source freshness and Generated time remain separate on the primary card."
    )
    return embed


async def _audit(
    interaction: Any,
    authorization: LeadershipPlayerAuthorization,
    *,
    target_id: int | None,
    action: str,
    outcome: str,
    correlation_id: UUID,
    error_code: str | None = None,
) -> None:
    try:
        actor_id, guild_id, channel_id = actor_guild_channel_ids(interaction)
    except ValueError:
        return
    await service.write_audit(
        actor_id=actor_id,
        target_governor_id=target_id,
        guild_id=guild_id,
        channel_id=channel_id,
        authorization_basis=authorization.basis,
        authorization_role_id=authorization.role_id,
        action=action,
        outcome=outcome,
        error_code=error_code,
        correlation_id=correlation_id,
    )


async def _deny(interaction: discord.Interaction, message: str) -> None:
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception:
        logger.debug("leadership_player_denial_send_failed", exc_info=True)


async def _final_delivery_authorization(
    interaction: discord.Interaction,
    *,
    author_id: int,
    target_id: int | None,
    action: str,
    correlation_id: UUID,
) -> LeadershipPlayerAuthorization | None:
    authorization = await reauthorize_leadership_player_interaction(interaction)
    if int(getattr(interaction.user, "id", 0) or 0) != int(author_id):
        error_code = "AUTHOR_MISMATCH"
    elif not authorization.allowed:
        error_code = authorization.error_code or "REVALIDATION_FAILED"
    else:
        return authorization
    await _audit(
        interaction,
        authorization,
        target_id=target_id,
        action=action,
        outcome="DENIED",
        correlation_id=correlation_id,
        error_code=error_code,
    )
    await _deny(
        interaction,
        "Your current identity, role, guild membership, or channel no longer permits this review.",
    )
    return None


class LeadershipPlayerView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        payload: LeadershipPlayerPayload,
        authorization: LeadershipPlayerAuthorization,
        correlation_id: UUID,
        timeout: float = 14 * 60,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.payload = payload
        self.authorization = authorization
        self.correlation_id = correlation_id
        self.message: Any | None = None
        self._transition_id = 0
        self._expired = False
        if self._record_page_count() <= 1:
            self.remove_item(self.record_previous)
            self.remove_item(self.record_next)
        self.add_item(
            discord.ui.Button(
                label=(
                    f"Current: {payload.header.governor_name or 'Governor'} "
                    f"({payload.header.governor_id})"
                )[:80],
                custom_id="leadership:player:current",
                style=discord.ButtonStyle.primary,
                disabled=True,
                row=4,
            )
        )
        self._sync_controls()

    def _record_page_count(self) -> int:
        return max(
            1,
            (
                max(
                    len(self.payload.linked_governors),
                    len(self.payload.aliases),
                    len(self.payload.alliance_episodes),
                )
                + 9
            )
            // 10,
        )

    def _sync_controls(self) -> None:
        for child in self.children:
            custom_id = getattr(child, "custom_id", "") or ""
            if custom_id.startswith("leadership:player:page:"):
                page = custom_id.rsplit(":", 1)[-1]
                child.disabled = page == self.payload.page
                child.style = (
                    discord.ButtonStyle.primary if child.disabled else discord.ButtonStyle.secondary
                )
            if custom_id == "leadership:player:period":
                child.options = [
                    discord.SelectOption(
                        label=f"{days} days",
                        value=str(days),
                        default=days == self.payload.period_days,
                    )
                    for days in service.SUPPORTED_PERIODS
                ]
            if custom_id == "leadership:player:linked":
                other = [row for row in self.payload.linked_governors if not row.current]
                child.disabled = not other
                child.placeholder = (
                    f"Current: {self.payload.header.governor_name or self.payload.header.governor_id}"
                    if other
                    else "No other linked governors"
                )
                child.options = [
                    discord.SelectOption(
                        label=row.governor_name[:100],
                        description=f"Governor ID {row.governor_id}",
                        value=f"g:{row.governor_id}",
                    )
                    for row in other[:25]
                ] or [discord.SelectOption(label="No linked governors", value="none")]
            if custom_id == "leadership:player:record:previous":
                child.disabled = self.payload.record_page <= 0
            if custom_id == "leadership:player:record:next":
                child.disabled = self.payload.record_page + 1 >= self._record_page_count()

    @staticmethod
    def _interaction_action(interaction: discord.Interaction) -> str:
        data = getattr(interaction, "data", None) or {}
        custom_id = str(data.get("custom_id") or "")
        if custom_id.endswith(":period"):
            return "period_change"
        if custom_id.endswith(":linked"):
            return "linked_governor_change"
        if custom_id.endswith(":change"):
            return "change_player"
        if custom_id.endswith(":definitions"):
            return "definitions"
        if custom_id.endswith(":refresh"):
            return "refresh"
        return "page_change"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        authorization = authorize_leadership_player_interaction(interaction)
        action = self._interaction_action(interaction)
        if int(getattr(interaction.user, "id", 0) or 0) != self.author_id:
            await _audit(
                interaction,
                authorization,
                target_id=self.payload.header.governor_id,
                action=action,
                outcome="DENIED",
                correlation_id=self.correlation_id,
                error_code="AUTHOR_MISMATCH",
            )
            await _deny(interaction, "This private leadership review belongs to another user.")
            return False
        if not authorization.allowed:
            await _audit(
                interaction,
                authorization,
                target_id=self.payload.header.governor_id,
                action=action,
                outcome="DENIED",
                correlation_id=self.correlation_id,
                error_code=authorization.error_code,
            )
            await _deny(interaction, "Your current role or channel no longer permits this review.")
            return False
        self.authorization = authorization
        return True

    async def _begin(self, interaction: discord.Interaction) -> int:
        self._transition_id += 1
        transition_id = self._transition_id
        if not interaction.response.is_done():
            await interaction.response.defer()
        return transition_id

    async def _replace(
        self,
        interaction: discord.Interaction,
        payload: LeadershipPlayerPayload,
        *,
        action: str,
        transition_id: int,
    ) -> None:
        if transition_id != self._transition_id:
            await _audit(
                interaction,
                self.authorization,
                target_id=payload.header.governor_id,
                action=action,
                outcome="STALE_SUPPRESSED",
                correlation_id=self.correlation_id,
                error_code="NEWER_TRANSITION",
            )
            return
        next_view = LeadershipPlayerView(
            author_id=self.author_id,
            payload=payload,
            authorization=self.authorization,
            correlation_id=self.correlation_id,
            timeout=self.timeout or 14 * 60,
        )
        file: discord.File | None = None
        try:
            try:
                file = await asyncio.to_thread(_card_file, payload)
                if transition_id != self._transition_id:
                    await _audit(
                        interaction,
                        self.authorization,
                        target_id=payload.header.governor_id,
                        action=action,
                        outcome="STALE_SUPPRESSED",
                        correlation_id=self.correlation_id,
                        error_code="NEWER_TRANSITION",
                    )
                    return
                authorization = await _final_delivery_authorization(
                    interaction,
                    author_id=self.author_id,
                    target_id=payload.header.governor_id,
                    action=action,
                    correlation_id=self.correlation_id,
                )
                if authorization is None:
                    return
                self.authorization = authorization
                next_view.authorization = authorization
                edited = await interaction.edit_original_response(
                    content=None,
                    embed=None,
                    attachments=[],
                    files=[file],
                    view=next_view,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "leadership_player_render_or_delivery_failed target_id=%s page=%s",
                    payload.header.governor_id,
                    payload.page,
                )
                if transition_id != self._transition_id:
                    await _audit(
                        interaction,
                        self.authorization,
                        target_id=payload.header.governor_id,
                        action=action,
                        outcome="STALE_SUPPRESSED",
                        correlation_id=self.correlation_id,
                        error_code="NEWER_TRANSITION",
                    )
                    return
                authorization = await _final_delivery_authorization(
                    interaction,
                    author_id=self.author_id,
                    target_id=payload.header.governor_id,
                    action=action,
                    correlation_id=self.correlation_id,
                )
                if authorization is None:
                    return
                self.authorization = authorization
                next_view.authorization = authorization
                edited = await interaction.edit_original_response(
                    content=None,
                    embed=build_fallback_embed(payload),
                    attachments=[],
                    view=next_view,
                )
            next_view.message = edited
            await _audit(
                interaction,
                self.authorization,
                target_id=payload.header.governor_id,
                action=action,
                outcome="SUCCEEDED",
                correlation_id=self.correlation_id,
            )
        finally:
            _close_file(file)

    async def _page(self, interaction: discord.Interaction, page: ReviewPage) -> None:
        transition = await self._begin(interaction)
        await self._replace(
            interaction,
            replace(self.payload, page=page),
            action="page_change",
            transition_id=transition,
        )

    @discord.ui.button(label="Overview", custom_id="leadership:player:page:overview", row=0)
    async def overview(self, _button, interaction):
        await self._page(interaction, "overview")

    @discord.ui.button(label="Kingdom Activity", custom_id="leadership:player:page:activity", row=0)
    async def activity(self, _button, interaction):
        await self._page(interaction, "activity")

    @discord.ui.button(label="KVK Performance", custom_id="leadership:player:page:kvk", row=0)
    async def kvk(self, _button, interaction):
        await self._page(interaction, "kvk")

    @discord.ui.button(label="Player Record", custom_id="leadership:player:page:record", row=0)
    async def record(self, _button, interaction):
        await self._page(interaction, "record")

    @discord.ui.select(
        placeholder="Period",
        custom_id="leadership:player:period",
        options=[discord.SelectOption(label="90 days", value="90")],
        row=1,
    )
    async def period(self, select, interaction):
        transition = await self._begin(interaction)
        try:
            period_days = int(select.values[0])
            payload = await service.load_payload(
                self.payload.header.governor_id,
                period_days,
                page=self.payload.page,
            )
        except Exception:
            logger.exception("leadership_player_period_change_failed")
            await _audit(
                interaction,
                self.authorization,
                target_id=self.payload.header.governor_id,
                action="period_change",
                outcome="FAILED",
                correlation_id=self.correlation_id,
                error_code="LOAD_FAILED",
            )
            await interaction.followup.send(
                "Could not load that period. Please try again.", ephemeral=True
            )
            return
        await self._replace(interaction, payload, action="period_change", transition_id=transition)

    @discord.ui.button(label="Change Player", custom_id="leadership:player:change", row=2)
    async def change_player(self, _button, interaction):
        await interaction.response.send_modal(
            LeadershipChangePlayerModal(
                parent=self,
            )
        )

    @discord.ui.button(
        label="Definitions / Method", custom_id="leadership:player:definitions", row=2
    )
    async def definitions(self, _button, interaction):
        embed = discord.Embed(
            title="Leadership player review · definitions",
            description=(
                "Exact periods use anchor − days + 1. Presence is distinct complete scans containing the Governor ID. "
                "Coverage keeps Stats scans, Alliance Activity snapshots, and completed Rally report dates separate.\n\n"
                "Activity Index v1 weights: Forts 30%, Helps 22%, Tech 18%, RSS 14%, Building 10%, Power 6%. "
                "Components use average-rank percentile; missing one component makes the index unavailable.\n\n"
                "KP Loss = Healed × 20. Tanking Score = Kill Points ÷ (KP Loss + Deads) × 100; higher is better."
            ),
            color=discord.Color.blue(),
        )
        depth_lines = [
            (
                f"{row.source_code}: {row.earliest or '—'} to {row.latest or '—'} · "
                f"{row.observation_count} {row.history_kind.lower()} · "
                f"gaps {row.gap_count if row.gap_count is not None else '—'} · {row.evidence_basis}"
            )
            for row in self.payload.history_depth
        ]
        embed.add_field(
            name="History depth",
            value=("\n".join(depth_lines) or "No history-depth evidence is available.")[:1024],
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await _audit(
            interaction,
            self.authorization,
            target_id=self.payload.header.governor_id,
            action="definitions",
            outcome="SUCCEEDED",
            correlation_id=self.correlation_id,
        )

    @discord.ui.button(label="Refresh", custom_id="leadership:player:refresh", row=2)
    async def refresh(self, _button, interaction):
        transition = await self._begin(interaction)
        try:
            payload = await service.load_payload(
                self.payload.header.governor_id,
                self.payload.period_days,
                page=self.payload.page,
                refresh=True,
            )
        except Exception:
            logger.exception("leadership_player_refresh_failed")
            await _audit(
                interaction,
                self.authorization,
                target_id=self.payload.header.governor_id,
                action="refresh",
                outcome="FAILED",
                correlation_id=self.correlation_id,
                error_code="LOAD_FAILED",
            )
            await interaction.followup.send(
                "Refresh failed. The existing report has been preserved.", ephemeral=True
            )
            return
        await self._replace(interaction, payload, action="refresh", transition_id=transition)

    @discord.ui.select(
        placeholder="Linked governors",
        custom_id="leadership:player:linked",
        options=[discord.SelectOption(label="No linked governors", value="none")],
        row=3,
    )
    async def linked(self, select, interaction):
        value = select.values[0]
        if not value.startswith("g:"):
            await interaction.response.send_message(
                "No linked governor is available.", ephemeral=True
            )
            return
        transition = await self._begin(interaction)
        target_id = int(value.split(":", 1)[1])
        if target_id not in {row.governor_id for row in self.payload.linked_governors}:
            await _audit(
                interaction,
                self.authorization,
                target_id=target_id,
                action="linked_governor_change",
                outcome="DENIED",
                correlation_id=self.correlation_id,
                error_code="TARGET_NOT_LINKED",
            )
            await interaction.followup.send("That linked-governor choice is stale.", ephemeral=True)
            return
        try:
            payload = await service.load_payload(
                target_id, self.payload.period_days, page=self.payload.page
            )
        except Exception:
            logger.exception("leadership_player_linked_change_failed target_id=%s", target_id)
            await _audit(
                interaction,
                self.authorization,
                target_id=target_id,
                action="linked_governor_change",
                outcome="FAILED",
                correlation_id=self.correlation_id,
                error_code="LOAD_FAILED",
            )
            await interaction.followup.send("Could not load that linked governor.", ephemeral=True)
            return
        await self._replace(
            interaction, payload, action="linked_governor_change", transition_id=transition
        )

    async def _record_page(self, interaction: discord.Interaction, delta: int) -> None:
        transition = await self._begin(interaction)
        page = min(
            max(0, self.payload.record_page + delta),
            self._record_page_count() - 1,
        )
        await self._replace(
            interaction,
            replace(self.payload, page="record", record_page=page),
            action="page_change",
            transition_id=transition,
        )

    @discord.ui.button(
        label="Previous Record Page",
        custom_id="leadership:player:record:previous",
        row=4,
    )
    async def record_previous(self, _button, interaction):
        await self._record_page(interaction, -1)

    @discord.ui.button(
        label="Next Record Page",
        custom_id="leadership:player:record:next",
        row=4,
    )
    async def record_next(self, _button, interaction):
        await self._record_page(interaction, 1)

    async def on_timeout(self) -> None:
        self._expired = True
        for child in self.children:
            child.disabled = True
        try:
            if self.message is not None:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("leadership_player_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


class LeadershipChangePlayerModal(discord.ui.Modal):
    def __init__(self, *, parent: LeadershipPlayerView) -> None:
        super().__init__(title="Change player")
        self.parent = parent
        self.query = discord.ui.InputText(
            label="Exact Governor ID or governor name",
            placeholder="Governor ID or name",
            min_length=1,
            max_length=100,
        )
        self.add_item(self.query)

    async def callback(self, interaction: discord.Interaction) -> None:
        authorization = authorize_leadership_player_interaction(interaction)
        if (
            int(getattr(interaction.user, "id", 0) or 0) != self.parent.author_id
            or not authorization.allowed
        ):
            await _audit(
                interaction,
                authorization,
                target_id=self.parent.payload.header.governor_id,
                action="change_player",
                outcome="DENIED",
                correlation_id=self.parent.correlation_id,
                error_code="REVALIDATION_FAILED",
            )
            await _deny(
                interaction, "Your current identity, role, or channel cannot change this review."
            )
            return
        raw = str(self.query.value or "").strip()
        target_id: int | None = None
        matches: tuple[LookupCandidate, ...] = ()
        lookup_error: str | None = None
        if raw.isdecimal():
            target_id = int(raw)
            lookup_error = service.validate_command_inputs(target_id, None)
            if lookup_error:
                target_id = None
        else:
            try:
                result = await service.resolve_name(raw)
            except Exception:
                logger.exception("leadership_player_change_lookup_failed")
                await _audit(
                    interaction,
                    authorization,
                    target_id=None,
                    action="change_player",
                    outcome="FAILED",
                    correlation_id=self.parent.correlation_id,
                    error_code="LOOKUP_FAILED",
                )
                await interaction.response.send_message(
                    "Player lookup is temporarily unavailable.", ephemeral=True
                )
                return
            if result.status == "found" and result.candidate:
                target_id = result.candidate.governor_id
            elif result.status == "matches":
                matches = result.candidates
            else:
                lookup_error = result.error
        if matches:
            current_authorization = await _final_delivery_authorization(
                interaction,
                author_id=self.parent.author_id,
                target_id=None,
                action="change_player",
                correlation_id=self.parent.correlation_id,
            )
            if current_authorization is None:
                return
            authorization = current_authorization
            view = LeadershipPlayerAmbiguityView(
                author_id=self.parent.author_id,
                candidates=matches,
                period_days=self.parent.payload.period_days,
                page=self.parent.payload.page,
                authorization=authorization,
                correlation_id=self.parent.correlation_id,
            )
            await interaction.response.send_message(
                "Multiple governors match. Select one exact Governor ID.",
                view=view,
                ephemeral=True,
            )
            try:
                view.message = await interaction.original_response()
            except Exception:
                logger.debug("leadership_player_ambiguity_message_capture_failed", exc_info=True)
            return
        if target_id is None:
            await _audit(
                interaction,
                authorization,
                target_id=None,
                action="change_player",
                outcome="FAILED",
                correlation_id=self.parent.correlation_id,
                error_code="INVALID_LOOKUP",
            )
            await interaction.response.send_message(
                lookup_error or "No matching governor was found.",
                ephemeral=True,
            )
            return
        await interaction.response.defer()
        try:
            payload = await service.load_payload(
                target_id, self.parent.payload.period_days, page=self.parent.payload.page
            )
        except Exception:
            logger.exception("leadership_player_change_load_failed target_id=%s", target_id)
            await _audit(
                interaction,
                authorization,
                target_id=target_id,
                action="change_player",
                outcome="FAILED",
                correlation_id=self.parent.correlation_id,
                error_code="LOAD_FAILED",
            )
            await interaction.followup.send("Could not load that governor.", ephemeral=True)
            return
        transition = self.parent._transition_id + 1
        self.parent._transition_id = transition
        await self.parent._replace(
            interaction, payload, action="change_player", transition_id=transition
        )


class LeadershipPlayerAmbiguityView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        candidates: tuple[LookupCandidate, ...],
        period_days: int,
        page: ReviewPage,
        authorization: LeadershipPlayerAuthorization,
        correlation_id: UUID,
        selector_page: int = 0,
        timeout: float = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.candidates = tuple(candidates)
        self.period_days = int(period_days)
        self.page = page
        self.selector_page = max(0, int(selector_page))
        self.authorization = authorization
        self.correlation_id = correlation_id
        self.message: Any | None = None
        self._sync_selector_page()

    def _sync_selector_page(self) -> None:
        page_count = max(1, (len(self.candidates) + 24) // 25)
        self.selector_page = min(self.selector_page, page_count - 1)
        start = self.selector_page * 25
        self.selector.options = [
            discord.SelectOption(
                label=(row.current_name or row.governor_name)[:100],
                description=(
                    f"ID {row.governor_id} · {row.current_alliance or 'Unallied'} · scan {row.last_scan_at_utc.date().isoformat() if row.last_scan_at_utc else 'unknown'}"
                )[:100],
                value=f"candidate:{index}",
            )
            for index, row in enumerate(self.candidates[start : start + 25], start=start)
        ]
        self.selector.placeholder = f"Select governor · page {self.selector_page + 1}/{page_count}"
        self.ambiguity_previous.disabled = self.selector_page <= 0
        self.ambiguity_next.disabled = self.selector_page + 1 >= page_count

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        authorization = authorize_leadership_player_interaction(interaction)
        if (
            int(getattr(interaction.user, "id", 0) or 0) != self.author_id
            or not authorization.allowed
        ):
            await _audit(
                interaction,
                authorization,
                target_id=None,
                action="ambiguity_select",
                outcome="DENIED",
                correlation_id=self.correlation_id,
                error_code="REVALIDATION_FAILED",
            )
            await _deny(interaction, "This private selector is unavailable to you here.")
            return False
        self.authorization = authorization
        return True

    @discord.ui.select(
        placeholder="Select governor",
        custom_id="leadership:player:ambiguity",
        options=[discord.SelectOption(label="Loading", value="loading")],
    )
    async def selector(self, select, interaction):
        try:
            candidate_index = int(select.values[0].split(":", 1)[1])
            candidate = self.candidates[candidate_index]
        except (IndexError, TypeError, ValueError):
            await interaction.response.send_message("That selection expired.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            payload = await service.load_payload(
                candidate.governor_id,
                self.period_days,
                page=self.page,
            )
            view = LeadershipPlayerView(
                author_id=self.author_id,
                payload=payload,
                authorization=self.authorization,
                correlation_id=self.correlation_id,
            )
            file: discord.File | None = None
            try:
                file = await asyncio.to_thread(_card_file, payload)
                current_authorization = await _final_delivery_authorization(
                    interaction,
                    author_id=self.author_id,
                    target_id=candidate.governor_id,
                    action="ambiguity_select",
                    correlation_id=self.correlation_id,
                )
                if current_authorization is None:
                    return
                self.authorization = current_authorization
                view.authorization = current_authorization
                message = await interaction.edit_original_response(
                    content=None, embed=None, attachments=[], files=[file], view=view
                )
            except Exception:
                logger.exception("leadership_player_ambiguity_render_failed")
                current_authorization = await _final_delivery_authorization(
                    interaction,
                    author_id=self.author_id,
                    target_id=candidate.governor_id,
                    action="ambiguity_select",
                    correlation_id=self.correlation_id,
                )
                if current_authorization is None:
                    return
                self.authorization = current_authorization
                view.authorization = current_authorization
                message = await interaction.edit_original_response(
                    content=None, embed=build_fallback_embed(payload), attachments=[], view=view
                )
            finally:
                _close_file(file)
            view.message = message
            await _audit(
                interaction,
                self.authorization,
                target_id=candidate.governor_id,
                action="ambiguity_select",
                outcome="SUCCEEDED",
                correlation_id=self.correlation_id,
            )
        except Exception:
            logger.exception("leadership_player_ambiguity_load_failed")
            await _audit(
                interaction,
                self.authorization,
                target_id=candidate.governor_id,
                action="ambiguity_select",
                outcome="FAILED",
                correlation_id=self.correlation_id,
                error_code="LOAD_FAILED",
            )
            await interaction.followup.send("Could not load that governor.", ephemeral=True)

    async def _change_selector_page(
        self,
        interaction: discord.Interaction,
        delta: int,
    ) -> None:
        self.selector_page += delta
        self._sync_selector_page()
        current_authorization = await _final_delivery_authorization(
            interaction,
            author_id=self.author_id,
            target_id=None,
            action="page_change",
            correlation_id=self.correlation_id,
        )
        if current_authorization is None:
            return
        self.authorization = current_authorization
        await interaction.response.edit_message(view=self)
        await _audit(
            interaction,
            self.authorization,
            target_id=None,
            action="page_change",
            outcome="SUCCEEDED",
            correlation_id=self.correlation_id,
        )

    @discord.ui.button(
        label="Previous Matches",
        custom_id="leadership:player:ambiguity:previous",
        row=1,
    )
    async def ambiguity_previous(self, _button, interaction):
        await self._change_selector_page(interaction, -1)

    @discord.ui.button(
        label="Next Matches",
        custom_id="leadership:player:ambiguity:next",
        row=1,
    )
    async def ambiguity_next(self, _button, interaction):
        await self._change_selector_page(interaction, 1)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            if self.message is not None:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("leadership_player_ambiguity_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


async def send_leadership_player_review(
    ctx: discord.ApplicationContext,
    *,
    governor_id: int | None,
    name: str | None,
) -> None:
    interaction = ctx.interaction
    correlation_id = uuid4()
    authorization = authorize_leadership_player_interaction(interaction)
    if not authorization.allowed:
        await _audit(
            interaction,
            authorization,
            target_id=governor_id,
            action="open",
            outcome="DENIED",
            correlation_id=correlation_id,
            error_code=authorization.error_code,
        )
        await ctx.respond(
            "This command is not available for your current role and channel.", ephemeral=True
        )
        return
    error = service.validate_command_inputs(governor_id, name)
    if error:
        await _audit(
            interaction,
            authorization,
            target_id=governor_id,
            action="open",
            outcome="FAILED",
            correlation_id=correlation_id,
            error_code="INVALID_LOOKUP_SHAPE",
        )
        await ctx.respond(error, ephemeral=True)
        return
    await _audit(
        interaction,
        authorization,
        target_id=governor_id,
        action="open",
        outcome="ALLOWED",
        correlation_id=correlation_id,
    )
    await safe_defer(ctx, ephemeral=True)
    target_id = int(governor_id or 0) or None
    if target_id is None:
        try:
            result = await service.resolve_name(name or "")
        except Exception:
            logger.exception("leadership_player_lookup_failed")
            await _audit(
                interaction,
                authorization,
                target_id=None,
                action="open",
                outcome="FAILED",
                correlation_id=correlation_id,
                error_code="LOOKUP_FAILED",
            )
            await ctx.followup.send("Player lookup is temporarily unavailable.", ephemeral=True)
            return
        if result.status == "matches":
            current_authorization = await _final_delivery_authorization(
                interaction,
                author_id=ctx.user.id,
                target_id=None,
                action="open",
                correlation_id=correlation_id,
            )
            if current_authorization is None:
                return
            authorization = current_authorization
            view = LeadershipPlayerAmbiguityView(
                author_id=ctx.user.id,
                candidates=result.candidates,
                period_days=service.DEFAULT_PERIOD,
                page="overview",
                authorization=authorization,
                correlation_id=correlation_id,
            )
            message = await ctx.followup.send(
                "Multiple governors match. Select one exact Governor ID.", view=view, ephemeral=True
            )
            view.message = message
            return
        if result.status != "found" or result.candidate is None:
            await _audit(
                interaction,
                authorization,
                target_id=None,
                action="open",
                outcome="FAILED",
                correlation_id=correlation_id,
                error_code="NOT_FOUND",
            )
            await ctx.followup.send(
                result.error or "No matching governor was found.", ephemeral=True
            )
            return
        target_id = result.candidate.governor_id
    try:
        payload = await service.load_payload(target_id, service.DEFAULT_PERIOD)
    except Exception:
        logger.exception("leadership_player_open_failed target_id=%s", target_id)
        await _audit(
            interaction,
            authorization,
            target_id=target_id,
            action="open",
            outcome="FAILED",
            correlation_id=correlation_id,
            error_code="LOAD_FAILED",
        )
        await ctx.followup.send("Player review is temporarily unavailable.", ephemeral=True)
        return
    view = LeadershipPlayerView(
        author_id=ctx.user.id,
        payload=payload,
        authorization=authorization,
        correlation_id=correlation_id,
    )
    file: discord.File | None = None
    try:
        try:
            file = await asyncio.to_thread(_card_file, payload)
            current_authorization = await _final_delivery_authorization(
                interaction,
                author_id=ctx.user.id,
                target_id=target_id,
                action="open",
                correlation_id=correlation_id,
            )
            if current_authorization is None:
                return
            authorization = current_authorization
            view.authorization = current_authorization
            message = await ctx.followup.send(file=file, view=view, ephemeral=True)
        except Exception:
            logger.exception("leadership_player_initial_render_failed target_id=%s", target_id)
            current_authorization = await _final_delivery_authorization(
                interaction,
                author_id=ctx.user.id,
                target_id=target_id,
                action="open",
                correlation_id=correlation_id,
            )
            if current_authorization is None:
                return
            authorization = current_authorization
            view.authorization = current_authorization
            message = await ctx.followup.send(
                embed=build_fallback_embed(payload), view=view, ephemeral=True
            )
        view.message = message
        await _audit(
            interaction,
            authorization,
            target_id=target_id,
            action="open",
            outcome="SUCCEEDED",
            correlation_id=correlation_id,
        )
    finally:
        _close_file(file)
