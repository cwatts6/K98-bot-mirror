"""Short-lived owner controls; metadata and outcomes live in durable source receipts."""

import asyncio
import logging
import time

import discord

from core.interaction_safety import safe_defer, send_ephemeral, send_or_followup
from kvk.models.source_receipt_state import unexpired
from kvk.schemas.new_source_schema import SourceValidationError
from kvk.services.new_source_admin_service import (
    CONFIRM_SECONDS,
    SourceActor,
    SourceConflict,
    UncertainCommit,
)

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
    if isinstance(exc, UncertainCommit):
        await send_ephemeral(
            interaction,
            "The action's commit outcome is uncertain. Read the durable receipt/review with "
            "/kvk_admin source action:status before any retry. Do not repeat the mutation.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return
    if isinstance(exc, SourceValidationError):
        guidance = f"Workbook validation rejected the input ({exc.code}). Review its structure and metadata."
    elif type(exc) in (ValueError, PermissionError, SourceConflict):
        guidance = str(exc)[:900]
    await send_ephemeral(
        interaction,
        f"Source action could not complete. {guidance} No publication or delivery is implied.",
        allowed_mentions=discord.AllowedMentions.none(),
    )


def _receipt_delivery_recovery(row):
    """Keep each receipt family's identity and recovery route in delivery failures."""
    data = row if isinstance(row, dict) else {}
    for field, key in (("AttemptID", "receipt"), ("ReviewID", "review")):
        if data.get(field):
            identity = data[field]
            return (
                key,
                identity,
                (
                    f"Resume with /kvk_admin source action:resume {key}:{identity}. "
                    "Inspect the retained outcome before another action. "
                ),
            )
    identities = [
        (label, value)
        for label, value in (
            ("operation", data.get("OperationID") or data.get("operation_id")),
            ("job", data.get("job_id")),
            ("repair", data.get("repair_id")),
            ("pool", data.get("pool_id")),
        )
        if value
    ]
    if identities:
        key, identity = identities[0]
        return (
            key,
            identity,
            (
                "Export identities: "
                + "; ".join(f"{label}:{value}" for label, value in identities)
                + ". Inspect /kvk_admin source action:export_status for the original season/index "
                "before another action; retain these identities for reconciliation. "
            ),
        )
    token = getattr(row, "token", None)
    if token:
        return (
            "preview",
            token,
            (
                f"Preview token:{token}. This preview is process-local; no export action was "
                "confirmed. Reopen and review a fresh preview if its controls are unavailable. "
            ),
        )
    return "receipt", None, "Inspect the retained outcome before another action. "


async def send_receipt(interaction, service, row, view=None, *, saved=False):
    """Retain every complete review line across bounded private messages."""
    try:
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
            kwargs = {"allowed_mentions": discord.AllowedMentions.none()}
            if view is not None and index == len(pages) - 1:
                kwargs["view"] = view
            await send_or_followup(interaction, content, ephemeral=True, **kwargs)
        return True
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        data = row if isinstance(row, dict) else {}
        key, identity, recovery = _receipt_delivery_recovery(row)
        version = data.get("payload", {}).get("version", data.get("Version"))
        logger.warning(
            "KVK receipt delivery failed %s=%s version=%s saved=%s state=%s type=%s",
            key,
            identity,
            version,
            saved,
            data.get("Status", data.get("ReviewState", data.get("State", data.get("state")))),
            type(exc).__name__,
        )
        if view is not None:
            view.disable_all_items()
            view.stop()
        await send_ephemeral(
            interaction,
            ("Action saved; receipt delivery failed. " if saved else "Receipt delivery failed. ")
            + recovery
            + "No action was automatically retried.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return False


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
            label="Imported kingdom IDs, comma separated",
            max_length=2000,
            value=",".join(
                str(entry[0])
                for entry in (view.row.get("imported_configuration") or {}).get("mapping", [])
            ),
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
            self.source_view.disable_all_items()
            self.source_view.stop()
            await send_receipt(interaction, self.source_view.service, row, view, saved=True)
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
        self.reason = discord.ui.InputText(label="Configuration approval reason", max_length=512)
        # Kingdoms/camps/weights are read from kvk_list by the service, not retyped here.
        for item in (self.window, self.coverage, self.reason):
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
                mapping="",
                weights="",
                reason=self.reason.value,
            )
            view = KvkSourceImportView(self.source_view.service, row, action="configure")
            self.source_view.disable_all_items()
            self.source_view.stop()
            await send_receipt(interaction, self.source_view.service, row, view, saved=True)
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
            self.source_view.disable_all_items()
            self.source_view.stop()
            await send_receipt(
                interaction,
                self.source_view.service,
                row,
                KvkSourceImportView(
                    self.source_view.service, row, action="configure", roster_correction=True
                ),
                saved=True,
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
        allowed = service.actions(row, action, roster_correction=self.roster_correction)
        self.prepare_button.disabled = not allowed.prepare
        self.confirm_button.disabled = not allowed.confirm
        self.cancel_button.disabled = not allowed.cancel
        self.pair_button.disabled = not allowed.pair or self.owner_id != service.access.admin_id
        self.prepare_button.label = {
            "configure": (
                "Review roster correction" if self.roster_correction else "Review configuration"
            ),
            "correct": "Review explicit correction",
            "finalize": "Review aggregate finalization",
        }.get(action, "Prepare / review metadata")

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
            actor = await self.authorized(interaction)
            await asyncio.to_thread(
                self.service.check_receipt_action,
                actor,
                self.receipt_id,
                self.version,
                self.action,
                "prepare",
            )
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
            self.disable_all_items()
            self.stop()
            next_action = (
                "configure"
                if row["payload"].get("proposal", {}).get("baseline_configuration")
                and row.get("ObservationRevisionID")
                else "accept"
            )
            await send_receipt(
                interaction,
                self.service,
                row,
                KvkSourceImportView(self.service, row, action=next_action),
                saved=True,
            )
        except Exception as exc:
            await report_failure(interaction, exc)

    async def on_timeout(self):
        self.disable_all_items()
        self.stop()

    @discord.ui.button(label="Review matched update", style=discord.ButtonStyle.secondary)
    async def pair_button(self, button, interaction):
        try:
            actor = await self.authorized(interaction)
            self.service.access.authorize(actor, "match_update")
            row = await asyncio.to_thread(
                self.service.check_receipt_action,
                actor,
                self.receipt_id,
                self.version,
                self.action,
                "pair",
            )
            from kvk.services.source_admin_review_service import configured_review_service

            await interaction.response.send_modal(
                SourcePairModal(
                    configured_review_service(),
                    actor,
                    row.get("KVK_NO"),
                    receipt=row,
                    receipt_origin=self,
                )
            )
        except Exception as exc:
            await report_failure(interaction, exc)

    @discord.ui.button(label="Cancel pending work", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button, interaction):
        try:
            actor = await self.authorized(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(self.service.cancel, actor, self.receipt_id, self.version)
            self.disable_all_items()
            self.stop()
            await send_receipt(interaction, self.service, row, saved=True)
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceReviewView(discord.ui.View):
    """Disposable controls for immutable SQL reviews; resume uses the review UUID."""

    def __init__(self, service, row):
        super().__init__(timeout=CONFIRM_SECONDS)
        self.service, self.row = service, row
        self.cancel.disabled = row["ReviewState"] != "pending"
        self.confirm.disabled = self.cancel.disabled or not unexpired(
            row["ExpiresUTC"], service.now()
        )

    async def actor(self, interaction):
        actor = await current_actor(interaction, self.service.access)
        if (str(actor.user_id), str(actor.guild_id), str(actor.channel_id)) != (
            self.row["ActorID"],
            self.row["GuildID"],
            self.row["ChannelID"],
        ):
            raise PermissionError("Use your own review in its original channel.")
        self.service.access.authorize(actor, "status")
        return actor

    @discord.ui.button(label="Confirm reviewed action", style=discord.ButtonStyle.primary)
    async def confirm(self, button, interaction):
        try:
            actor = await self.actor(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.service.confirm, actor, str(self.row["ReviewID"]), self.row["Version"]
            )
            self.disable_all_items()
            self.stop()
            await send_receipt(interaction, self.service, row, saved=True)
        except Exception as exc:
            await report_failure(interaction, exc)

    @discord.ui.button(label="Cancel pending work", style=discord.ButtonStyle.danger)
    async def cancel(self, button, interaction):
        try:
            actor = await self.actor(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.service.cancel, actor, str(self.row["ReviewID"]), self.row["Version"]
            )
            self.disable_all_items()
            self.stop()
            await send_receipt(interaction, self.service, row, saved=True)
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceChoiceModal(discord.ui.Modal):
    def __init__(self, service, owner, season=None, source="snapshot_report_v1"):
        super().__init__(title="Review fixed season source", timeout=CONFIRM_SECONDS)
        self.service, self.owner = service, owner
        self.season = discord.ui.InputText(
            label="KVK season", value=str(season or ""), max_length=10
        )
        self.source = discord.ui.InputText(label="Source", value=source, max_length=32)
        self.reason = discord.ui.InputText(label="Reason for fixed source choice", max_length=512)
        for item in (self.season, self.source, self.reason):
            self.add_item(item)

    async def callback(self, interaction):
        try:
            actor = await current_actor(interaction, self.service.access)
            if actor != self.owner:
                raise PermissionError("Source choice identity or permissions changed; start again.")
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.service.prepare_choice,
                actor,
                self.season.value,
                self.source.value,
                self.reason.value,
            )
            await send_receipt(
                interaction, self.service, row, SourceReviewView(self.service, row), saved=True
            )
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceConfigurationReviewModal(discord.ui.Modal):
    def __init__(self, service, owner, season=None):
        super().__init__(title="Review imported KVK configuration", timeout=CONFIRM_SECONDS)
        self.service, self.owner = service, owner
        self.season = discord.ui.InputText(
            label="KVK season", value=str(season or ""), max_length=10
        )
        self.attest = discord.ui.InputText(
            label="Counterparts valid: VALID or blank",
            required=False,
            max_length=5,
        )
        self.reason = discord.ui.InputText(
            label="Configuration and attestation reason", max_length=512
        )
        for item in (self.season, self.attest, self.reason):
            self.add_item(item)

    async def callback(self, interaction):
        try:
            actor = await current_actor(interaction, self.service.access)
            if actor != self.owner:
                raise PermissionError("Configuration review identity changed; start again.")
            if self.attest.value.strip() not in ("", "VALID"):
                raise ValueError(
                    "Type VALID only if the retained counterparts remain valid; otherwise leave blank."
                )
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await asyncio.to_thread(
                self.service.prepare_configuration,
                actor,
                self.season.value,
                self.reason.value,
                attest_counterparts=self.attest.value.strip() == "VALID",
            )
            await send_receipt(
                interaction, self.service, row, SourceReviewView(self.service, row), saved=True
            )
        except Exception as exc:
            await report_failure(interaction, exc)


class SourcePairModal(discord.ui.Modal):
    def __init__(
        self, service, owner, season=None, receipt=None, update_id=None, receipt_origin=None
    ):
        super().__init__(title="Review matched source update", timeout=CONFIRM_SECONDS)
        self.service, self.owner = service, owner
        self.update_id = update_id
        self.receipt_origin = receipt_origin
        self.scope = discord.ui.InputText(
            label="Season | period key | end scan | action",
            value=f"{season or ''} | fight:pass4 | | publish",
            max_length=200,
        )
        self.aggregate = discord.ui.InputText(
            label="Accepted aggregate revision UUID", required=False, max_length=36
        )
        self.coverage = discord.ui.InputText(
            label="Coverage start UTC | end UTC | as-of UTC", max_length=130
        )
        self.counterpart = discord.ui.InputText(
            label="Counterpart UUID: attest valid for this pair", required=False, max_length=36
        )
        self.reason = discord.ui.InputText(
            label="Reason, including counterpart validity", max_length=512
        )
        if receipt:
            proposal = receipt["payload"].get("proposal", {})
            candidate = proposal.get("candidate", {})
            outcome = receipt["payload"].get("outcome", {})
            self.scope.value = f"{season or ''} | {candidate.get('period_key') or ''} | {outcome.get('scan_id') or ''} | publish"
            self.aggregate.value = receipt.get("AggregateRevisionID") or ""
            if candidate.get("coverage_start_utc"):
                self.coverage.value = " | ".join(
                    candidate[key]
                    for key in ("coverage_start_utc", "coverage_end_utc", "as_of_utc")
                )
        for item in (self.scope, self.aggregate, self.coverage, self.counterpart, self.reason):
            self.add_item(item)

    async def callback(self, interaction):
        try:
            actor = await current_actor(interaction, self.service.access)
            if actor != self.owner:
                raise PermissionError("Pair review identity or permissions changed; start again.")
            season, period, end, action = (v.strip() for v in self.scope.value.split("|"))
            start_utc, end_utc, as_of = (v.strip() for v in self.coverage.value.split("|"))
            if not await safe_defer(interaction, ephemeral=True):
                return
            if self.receipt_origin is not None:
                origin = self.receipt_origin
                await origin.authorized(interaction)
                await asyncio.to_thread(
                    origin.service.check_receipt_action,
                    actor,
                    origin.receipt_id,
                    origin.version,
                    origin.action,
                    "pair",
                )
            row = await asyncio.to_thread(
                self.service.prepare_match,
                actor,
                update_id=self.update_id,
                season=season,
                period=period,
                end_scan_id=end,
                coverage_start=start_utc,
                coverage_end=end_utc,
                as_of=as_of,
                action=action,
                aggregate_revision_id=self.aggregate.value.strip() or None,
                counterpart_revision_id=self.counterpart.value.strip() or None,
                reason=self.reason.value,
            )
            await send_receipt(
                interaction, self.service, row, SourceReviewView(self.service, row), saved=True
            )
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceUploadSeasonModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Confirm upload season", timeout=CONFIRM_SECONDS)
        self.source_view = view
        self.season = discord.ui.InputText(
            label="Season (change before accepting these files)",
            value=str(view.season or ""),
            max_length=10,
        )
        self.add_item(self.season)

    async def callback(self, interaction):
        view = self.source_view
        try:
            actor = await current_actor(interaction, view.access)
            if actor.user_id != view.owner.user_id or actor.channel_id != view.owner.channel_id:
                raise PermissionError("These uploads belong to another owner or channel.")
            view.access.authorize(actor, upload=True)
            if not await safe_defer(interaction, ephemeral=True):
                return
            service = await asyncio.to_thread(view.service_factory)
            for attachment in view.attachments:
                content = await attachment.read()
                if not 0 < len(content) <= 20 * 1024 * 1024:
                    raise ValueError("Attachment exceeds 20 MiB.")
                actor = await current_actor(interaction, view.access)
                view.access.authorize(actor, upload=True)
                row = await asyncio.to_thread(
                    service.stage_upload,
                    actor,
                    filename=attachment.filename,
                    content=content,
                    message_id=view.message_id,
                    attachment_id=attachment.id,
                    season=self.season.value,
                )
                await send_receipt(
                    interaction, service, row, KvkSourceImportView(service, row), saved=True
                )
            await send_ephemeral(
                interaction,
                "Files retained for metadata review. If one side is missing, upload its counterpart here. After acceptance, use /kvk_admin source match_update to review the exact pair, or retain scans without assigning a fight.",
            )
            view.disable_all_items()
            view.stop()
        except Exception as exc:
            await report_failure(interaction, exc)


class SourceUploadStartView(discord.ui.View):
    """Pre-receipt season choice can expire safely; no accepted state lives in this view."""

    def __init__(self, access, owner, attachments, message_id, service_factory, season=None):
        super().__init__(timeout=CONFIRM_SECONDS)
        self.access, self.owner, self.attachments = access, owner, tuple(attachments)
        self.message_id, self.service_factory, self.season = message_id, service_factory, season

    @discord.ui.button(label="Confirm / change season", style=discord.ButtonStyle.primary)
    async def begin(self, button, interaction):
        try:
            actor = await current_actor(interaction, self.access)
            self.access.authorize(actor, upload=True)
            if actor.user_id != self.owner.user_id or actor.channel_id != self.owner.channel_id:
                raise PermissionError("These uploads belong to another owner or channel.")
            await interaction.response.send_modal(SourceUploadSeasonModal(self))
        except Exception as exc:
            await report_failure(interaction, exc)

    @discord.ui.button(label="Cancel upload review", style=discord.ButtonStyle.secondary)
    async def cancel(self, button, interaction):
        try:
            actor = await current_actor(interaction, self.access)
            self.access.authorize(actor, upload=True)
            if actor.user_id != self.owner.user_id or actor.channel_id != self.owner.channel_id:
                raise PermissionError("These uploads belong to another owner or channel.")
            self.disable_all_items()
            self.stop()
            await send_ephemeral(
                interaction,
                "Upload review cancelled. No baseline or scan was accepted; original channel attachments remain.",
            )
        except Exception as exc:
            await report_failure(interaction, exc)
