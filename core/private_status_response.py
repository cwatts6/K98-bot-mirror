"""One private acknowledgement and one final edit for an operator status request.

An invalid webhook cannot be repaired by sending to the same webhook again.
Never fall back to a channel or DM, and never log tokens or exception bodies.
"""

from datetime import UTC, datetime
import logging
import time

import discord

from core.interaction_safety import response_is_done, safe_defer

logger = logging.getLogger(__name__)


class PrivateStatusResponse:
    def __init__(self, ctx):
        self.ctx = ctx
        self.interaction = getattr(ctx, "interaction", None) or ctx
        self.started = time.monotonic()
        self.acknowledged = False

    def age_seconds(self):
        created = getattr(self.interaction, "created_at", None)
        if isinstance(created, datetime) and created.tzinfo is not None:
            return max(0, int((datetime.now(UTC) - created).total_seconds()))
        return None

    async def acknowledge(self):
        if response_is_done(self.interaction):
            logger.warning("[OPS_STATUS] disposition=already_acknowledged owner=unconfirmed")
            return False
        self.acknowledged = await safe_defer(self.ctx, ephemeral=True)
        logger.info(
            "[OPS_STATUS] phase=ack acknowledged=%s interaction_age_seconds=%s elapsed_ms=%d",
            self.acknowledged,
            self.age_seconds(),
            int((time.monotonic() - self.started) * 1000),
        )
        return self.acknowledged

    async def complete(self, **payload):
        if not self.acknowledged:
            return "not_acknowledged"
        try:
            await self.interaction.edit_original_response(**payload)
        except discord.HTTPException as exc:
            logger.warning(
                "[OPS_STATUS] phase=edit disposition=unconfirmed status=%s code=%s interaction_age_seconds=%s elapsed_ms=%d",
                exc.status,
                exc.code,
                self.age_seconds(),
                int((time.monotonic() - self.started) * 1000),
            )
            return "unconfirmed"
        except Exception as exc:
            logger.warning(
                "[OPS_STATUS] phase=edit disposition=unconfirmed error_type=%s elapsed_ms=%d",
                type(exc).__name__,
                int((time.monotonic() - self.started) * 1000),
            )
            return "unconfirmed"
        logger.info(
            "[OPS_STATUS] phase=edit disposition=acknowledged elapsed_ms=%d",
            int((time.monotonic() - self.started) * 1000),
        )
        return "acknowledged"
