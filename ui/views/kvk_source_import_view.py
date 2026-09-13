"""Short-lived owner controls; metadata and outcomes live in durable source receipts."""

import asyncio
import logging
import time

import discord

from core.interaction_safety import safe_defer, send_ephemeral
from kvk.schemas.new_source_schema import SourceValidationError
from kvk.services.new_source_admin_service import CONFIRM_SECONDS, SourceActor, SourceConflict

logger = logging.getLogger(__name__)


async def current_actor(subject, access):
    """Fetch membership on every handler/callback; cached roles are not authority."""
    guild = getattr(subject, "guild", None)
    user = getattr(subject, "user", None) or getattr(subject, "author", None)
    channel = getattr(subject, "channel", None)
    if not guild or guild.id != access.guild_id or not user or getattr(user, "bot", False):
        raise PermissionError("Use the configured guild with an authorized member account.")
    member = await guild.fetch_member(user.id)
    return SourceActor(member.id, guild.id, channel.id, frozenset(r.id for r in member.roles))


async def report_failure(interaction, exc):
    # Parser/SQL messages can contain private fields: return only controlled guidance.
    logger.info("KVK source interaction failed type=%s", type(exc).__name__)
    guidance = "Check permissions, metadata and current receipt version, then resume."
    if isinstance(exc, SourceValidationError):
        guidance = f"Workbook validation rejected the input ({exc.code}). Review its structure and metadata."
    elif type(exc) in (ValueError, PermissionError, SourceConflict):
        guidance = str(exc)[:900]
    await send_ephemeral(
        interaction,
        f"Source action could not complete. {guidance} No publication or delivery is implied.",
        allowed_mentions=discord.AllowedMentions.none(),
    )


async def send_receipt(interaction, service, row, view=None):
    """Retain every complete review line across bounded private messages."""
    pages, page = [], ""
    for line in service.summary(row).splitlines():
        if len(line) > 1800:
            raise ValueError("Receipt review line exceeds its display contract.")
        if len(page) + len(line) + 1 > 1800:
            pages.append(page)
            page = ""
        page += ("\n" if page else "") + line
    pages.append(page)
    for index, content in enumerate(pages):
        await send_ephemeral(
            interaction,
            content,
            view=view if index == len(pages) - 1 else None,
            allowed_mentions=discord.AllowedMentions.none(),
        )


class SourceMetadataModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Source workbook metadata", timeout=CONFIRM_SECONDS)
        self.source_view = view
        candidate = (
            view.row["payload"]
            .get("proposal", {})
            .get("candidate", view.row["payload"].get("candidate", {}))
        )
        self.identity = discord.ui.InputText(
            label="Kind | period | precision",
            placeholder="players | fight:pass4 | minute",
            value=f"{candidate.get('kind') or 'players'} | {candidate.get('period_key') or ''} | {candidate.get('time_precision') or 'minute'}",
            max_length=200,
        )
        self.scan = discord.ui.InputText(
            label="Scan START in UTC (not upload time)",
            placeholder="2000-01-01T12:00Z",
            value=candidate.get("scan_start_utc") or "",
            max_length=40,
        )
        self.kingdoms = discord.ui.InputText(
            label="All approved kingdom IDs, comma separated", max_length=2000
        )
        self.coverage = discord.ui.InputText(
            label="Aggregate only: start | end | as-of | state",
            placeholder="UTC timestamps | live, final or corrected_final",
            required=False,
            max_length=200,
        )
        self.reason = discord.ui.InputText(
            label="Audit reason (including metadata overrides)", max_length=512
        )
        for item in (self.identity, self.scan, self.kingdoms, self.coverage, self.reason):
            self.add_item(item)

    async def callback(self, interaction):
        try:
            actor = await self.source_view.authorized(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            kind, period, precision = (x.strip() for x in self.identity.value.split("|"))
            fields = {
                "kind": kind,
                "period": period,
                "precision": precision,
                "scan_start": self.scan.value,
                "kingdoms": self.kingdoms.value,
            }
            if self.coverage.value:
                fields.update(
                    zip(
                        ("coverage_start", "coverage_end", "as_of", "state"),
                        (x.strip() for x in self.coverage.value.split("|")),
                        strict=True,
                    )
                )
            row = await asyncio.to_thread(
                self.source_view.service.prepare_metadata,
                actor,
                self.source_view.receipt_id,
                self.source_view.version,
                fields,
                action=self.source_view.action,
                reason=self.reason.value,
                expected_revision=self.source_view.expected_revision,
                expected_revision_version=self.source_view.expected_revision_version,
            )
            view = KvkSourceImportView(
                self.source_view.service, row, action=self.source_view.action
            )
            await send_receipt(interaction, self.source_view.service, row, view)
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceConfigurationModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Approve source configuration", timeout=CONFIRM_SECONDS)
        self.source_view = view
        self.window = discord.ui.InputText(
            label="Period | label | StartScanID | EndScanID",
            placeholder="fight:pass4 | Pass 4 | 10 | 13",
            max_length=200,
        )
        self.coverage = discord.ui.InputText(
            label="Initial only: coverage start UTC | end UTC", required=False, max_length=100
        )
        self.mapping = discord.ui.InputText(
            label="Initial only: kingdom | camp ID | camp name",
            style=discord.InputTextStyle.long,
            required=False,
            max_length=4000,
        )
        self.weights = discord.ui.InputText(
            label="Initial only: X | Y | Z | effective UTC", required=False, max_length=450
        )
        self.reason = discord.ui.InputText(label="Configuration approval reason", max_length=512)
        for item in (self.window, self.coverage, self.mapping, self.weights, self.reason):
            self.add_item(item)

    async def callback(self, interaction):
        try:
            actor = await self.source_view.authorized(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.source_view.service.prepare_configuration,
                actor,
                self.source_view.receipt_id,
                self.source_view.version,
                window=self.window.value,
                coverage=self.coverage.value or "",
                mapping=self.mapping.value or "",
                weights=self.weights.value or "",
                reason=self.reason.value,
            )
            view = KvkSourceImportView(self.source_view.service, row, action="configure")
            await send_receipt(interaction, self.source_view.service, row, view)
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceRosterModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Review B0 roster correction", timeout=CONFIRM_SECONDS)
        self.source_view = view
        self.plan = discord.ui.InputText(
            label="Each publication UUID | retain",
            style=discord.InputTextStyle.long,
            required=False,
            max_length=4000,
        )
        self.reason = discord.ui.InputText(label="Roster correction reason", max_length=512)
        self.add_item(self.plan)
        self.add_item(self.reason)

    async def callback(self, interaction):
        try:
            actor = await self.source_view.authorized(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.source_view.service.prepare_roster_correction,
                actor,
                self.source_view.receipt_id,
                self.source_view.version,
                reason=self.reason.value,
                publication_plan=self.plan.value or "",
            )
            await send_receipt(
                interaction,
                self.source_view.service,
                row,
                KvkSourceImportView(
                    self.source_view.service, row, action="configure", roster_correction=True
                ),
            )
        except Exception as exc:
            await report_failure(interaction, exc)


class KvkSourceImportView(discord.ui.View):
    def __init__(
        self,
        service,
        row,
        *,
        action="accept",
        expected_revision=None,
        expected_revision_version=None,
        roster_correction=False,
    ):
        super().__init__(timeout=CONFIRM_SECONDS)
        self.service, self.row, self.action = service, row, action
        self.receipt_id, self.version = row["AttemptID"], row["payload"]["version"]
        self.owner_id = int(row["ActorID"])
        self.expires_at = time.monotonic() + CONFIRM_SECONDS
        proposal = row["payload"].get("proposal", {})
        self.roster_correction = roster_correction or proposal.get("mode") == "roster"
        self.expected_revision, self.expected_revision_version = (
            (
                expected_revision
                if expected_revision is not None
                else proposal.get("expected_revision")
            ),
            (
                expected_revision_version
                if expected_revision_version is not None
                else proposal.get("expected_revision_version")
            ),
        )
        self.confirm_button.disabled = (
            row["Status"] != "validated"
            or row["payload"].get("proposal", {}).get("action") != action
            or (self.roster_correction and proposal.get("mode") != "roster")
        )

    async def authorized(self, interaction):
        if time.monotonic() >= self.expires_at or interaction.user.id != self.owner_id:
            raise PermissionError("Owner-only confirmation expired or belongs to another member.")
        actor = await current_actor(interaction, self.service.access)
        self.service.access.authorize(actor, self.action)
        return actor

    async def interaction_check(self, interaction):
        try:
            await self.authorized(interaction)
            return True
        except Exception as exc:
            await report_failure(interaction, exc)
            return False

    @discord.ui.button(label="Prepare / review metadata", style=discord.ButtonStyle.secondary)
    async def prepare_button(self, button, interaction):
        try:
            await self.authorized(interaction)
            modal = (
                (
                    SourceRosterModal(self)
                    if self.roster_correction
                    else SourceConfigurationModal(self)
                )
                if self.action == "configure"
                else SourceMetadataModal(self)
            )
            await interaction.response.send_modal(modal)
        except Exception as exc:
            await report_failure(interaction, exc)

    @discord.ui.button(label="Confirm reviewed action", style=discord.ButtonStyle.primary)
    async def confirm_button(self, button, interaction):
        try:
            actor = await self.authorized(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.service.confirm, actor, self.receipt_id, self.version
            )
            await send_receipt(interaction, self.service, row)
            self.disable_all_items()
            self.stop()
        except Exception as exc:
            await report_failure(interaction, exc)

    async def on_timeout(self):
        self.disable_all_items()
        self.stop()
