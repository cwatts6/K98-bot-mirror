"""Read-only, existing-message reconciliation independent of the calendar window."""

import asyncio
from collections import Counter
import logging

from core.owned_work import drain_thread
from mge.dal import mge_recovery_dal
from mge.mge_board_preparation import BOARD_FIELDS
from services import event_delivery_service as delivery
from services.event_delivery_store import delivery_key

logger = logging.getLogger(__name__)


class RecoverySweep:
    def __init__(self, *, include_completed):
        self.include_completed = include_completed
        self.high_water = None
        self.cursor = 0
        self.complete = False
        self.counts = Counter(scanned=0, eligible=0, refreshed=0, held=0, failed=0, outstanding=0)

    def report(self):
        return {
            **self.counts,
            "cursor": self.cursor,
            "high_water": self.high_water,
            "complete": self.complete,
            "include_completed": self.include_completed,
        }

    async def _target(self, bot, event_id, kind, channel_id, receipt=None):
        from mge import mge_embed_manager as manager

        self.counts["eligible"] += 1
        self.counts["outstanding"] += 1
        try:
            if not isinstance(channel_id, int) or isinstance(channel_id, bool) or channel_id <= 0:
                self.counts["held"] += 1
                return
            kwargs = dict(bot=bot, event_id=event_id, existing_only=True, recovery_receipt=receipt)
            if kind == "signup":
                factory = lambda: manager.sync_event_signup_embed(
                    **kwargs,
                    signup_channel_id=channel_id,
                    announce_everyone=False,
                    is_rehydrate=True,
                )
            elif kind == "leadership":
                factory = lambda: manager.sync_event_leadership_embed(
                    **kwargs, channel_id=channel_id
                )
            else:
                factory = lambda: manager.sync_event_awards_embed(**kwargs, channel_id=channel_id)
            handle = manager._refreshes.request(
                (id(bot), event_id, kind, channel_id, "recovery", True), factory
            )
            result = await handle.observe()
            self.counts["refreshed" if result else "failed"] += 1
        except Exception as exc:
            self.counts["failed"] += 1
            logger.warning(
                "mge_recovery_target_failed event_id=%s kind=%s error_type=%s",
                event_id,
                kind,
                type(exc).__name__,
            )
        finally:
            self.counts["outstanding"] -= 1

    async def advance(self, bot):
        """One bounded page; a failed page retains its exact cursor for the next tick."""
        if self.complete:
            return
        try:
            if self.high_water is None:
                self.high_water = await drain_thread(mge_recovery_dal.recovery_high_water)
            rows = await drain_thread(
                mge_recovery_dal.recovery_page,
                self.cursor,
                self.high_water,
                include_completed=self.include_completed,
            )
            ids = [row["EventId"] for row in rows]
            if ids != sorted(set(ids)) or any(
                not self.cursor < eid <= self.high_water for eid in ids
            ):
                raise ValueError("Invalid recovery cursor page")
        except Exception as exc:
            self.counts["failed"] += 1
            logger.warning(
                "mge_recovery_page_held error_type=%s progress=%s",
                type(exc).__name__,
                self.report(),
            )
            return

        async def event(row):
            self.counts["scanned"] += 1
            for kind, (channel, message) in BOARD_FIELDS.items():
                if row.get(message) is not None:
                    await self._target(bot, row["EventId"], kind, row.get(channel))

        # At most two event tasks, not one task per inventory entry.
        for offset in range(0, len(rows), 2):
            await asyncio.gather(*(event(row) for row in rows[offset : offset + 2]))
        if rows:
            self.cursor = ids[-1]
        self.complete = len(rows) < 50 or self.cursor == self.high_water
        logger.info("mge_recovery_progress state=%s", self.report())

    async def receipts(self, bot):
        """Inspect retained evidence once at startup; ambiguous receipts remain held."""
        try:
            rows = await delivery.receipt_rows()
        except Exception as exc:
            self.counts["failed"] += 1
            logger.warning("mge_recovery_receipts_unavailable error_type=%s", type(exc).__name__)
            return
        from mge.dal.mge_event_dal import fetch_event_for_embed
        from mge.mge_board_preparation import recovered_identity, validate_event

        for receipt in rows:
            kind = next(
                (kind for kind in BOARD_FIELDS if receipt.get("kind") == f"mge_{kind}_board"), None
            )
            if kind is None:
                continue
            try:
                event_id, channel_id = int(receipt["event"]), int(receipt["target"])
                if receipt.get("key") != delivery_key("mge_board", kind, event_id, channel_id):
                    raise ValueError("Receipt key mismatch")
                row = await drain_thread(fetch_event_for_embed, event_id, strict=True)
                validate_event(row, event_id)
                if (
                    row[BOARD_FIELDS[kind][1]] == receipt.get("message_id")
                    and row[BOARD_FIELDS[kind][0]] == channel_id
                ):
                    continue  # Persisted identity is already covered by the page inventory.
                recovered_identity(row, kind, channel_id, receipt)
            except Exception:
                self.counts["held"] += 1
                continue
            await self._target(bot, event_id, kind, channel_id, receipt)
        logger.info("mge_recovery_receipt_progress state=%s", self.report())
