"""Discord-independent diagnostic orchestration and truthful durable outcomes."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from stats_alerts.diagnostic_sessions import DiagnosticSession, SessionRepository
from stats_alerts.dispatch_reservations import DispatchGuarded, DispatchUnavailable, _io

logger = logging.getLogger(__name__)


@dataclass
class PublicationReceipt:
    message_id: int | None = None


@dataclass
class DiagnosticResult:
    outcome: str
    session: str
    detail: str
    snapshot: dict | None = None
    receipt: int | None = None


def validate_destination(
    *,
    guild_id: int,
    expected_guild_id: int,
    channel_guild_id: int,
    channel_id: int,
    forbidden_channels: set[int],
    is_text: bool,
    requester_can_send: bool,
    bot_can_publish: bool,
) -> None:
    if (
        guild_id != expected_guild_id
        or channel_guild_id != guild_id
        or not is_text
        or channel_id in forbidden_channels
        or not requester_can_send
        or not bot_can_publish
    ):
        raise ValueError(
            "Choose an accessible guild text channel outside production stats channels"
        )


class DiagnosticRunner:
    def __init__(self):
        self.stopping = False
        self.active: asyncio.Task | None = None

    async def shutdown(self) -> None:
        self.stopping = True
        task = self.active
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            # Drain the operation, including the existing shielded filesystem finalizers.
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break

    async def execute(
        self,
        *,
        guild_id: int,
        channel_id: int,
        owner_id: int,
        token: str | None,
        action: str,
        publish: Callable[[DiagnosticSession, PublicationReceipt], Awaitable[str]],
        repository: SessionRepository | None = None,
    ) -> DiagnosticResult:
        if action not in {"run", "status"} or (action == "status" and token is None):
            raise ValueError("Status requires an existing session token")
        if self.stopping or (action == "run" and self.active is not None):
            raise DispatchUnavailable("Diagnostics are busy or shutting down")
        if action == "run":
            self.active = asyncio.current_task()
        session = None
        operation = None
        receipt = PublicationReceipt()
        result = None
        repository = repository or SessionRepository()

        def outcome(*args):
            nonlocal result
            result = DiagnosticResult(*args)
            return result

        def open_session():
            nonlocal session
            session = repository.open(guild_id, channel_id, owner_id, token)
            logger.info(
                "[PREKVK DIAGNOSTIC] session=%s owner=%s channel=%s action=%s",
                session.token,
                owner_id,
                channel_id,
                action,
            )

        def begin():
            nonlocal operation
            operation = session.begin()

        try:
            await _io(open_session)
            if action == "status":
                snapshot = await _io(session.snapshot)
                return outcome(
                    "status", session.token, "Read-only observation; no dispatch", snapshot
                )
            await _io(begin)
            await _io(session.store.recover)
            before = await _io(session.snapshot)
            if before["pending"]:
                return outcome(
                    "guarded", session.token, "Unresolved or owned attempt; no publication", before
                )
            publication = await publish(session, receipt)
            snapshot = await _io(session.snapshot)
            attempt = snapshot["attempt"]
            if publication == "edited" and receipt.message_id == snapshot["message_id"]:
                return outcome(
                    "edited",
                    session.token,
                    "Existing message edited; this is not fresh-admission proof",
                    snapshot,
                    receipt.message_id,
                )
            committed = (
                attempt
                and attempt["phase"] == "committed"
                and attempt["message_id"] == receipt.message_id
                and any(
                    row
                    == [attempt["accepted_at"][:10], attempt["accepted_at"][11:19], "prekvk_daily"]
                    for row in snapshot["rows"]
                )
            )
            # Crossing midnight can intentionally suppress the legacy message projection.
            if committed and snapshot["message_id"] == receipt.message_id:
                return outcome(
                    "sent",
                    session.token,
                    "Receipt and projections committed",
                    snapshot,
                    receipt.message_id,
                )
            return outcome(
                "uncertain",
                session.token,
                "Positive receipt; projections require inspection. Do not resend",
                snapshot,
                receipt.message_id,
            )
        except asyncio.CancelledError:
            logger.warning(
                "[PREKVK DIAGNOSTIC] Cancelled session=%s receipt=%s; inspect durable state",
                session.token if session else token,
                receipt.message_id,
            )
            raise
        except Exception as exc:
            logger.exception(
                "[PREKVK DIAGNOSTIC] Failed session=%s receipt=%s",
                session.token if session else token,
                receipt.message_id,
            )
            if session is None:
                raise
            snapshot = None
            try:
                snapshot = await _io(session.snapshot)
            except Exception:
                logger.exception("[PREKVK DIAGNOSTIC] Could not inspect durable outcome")
            attempt = snapshot["attempt"] if snapshot else None
            unknown = receipt.message_id is not None or (
                attempt and attempt["phase"] in {"sending", "uncertain", "accepted"}
            )
            guarded = isinstance(exc, DispatchGuarded) and not unknown
            return outcome(
                "uncertain" if unknown else "guarded" if guarded else "failed",
                session.token,
                "Inspect durable state; no automatic retry",
                snapshot,
                receipt.message_id,
            )
        finally:
            try:
                if operation is not None:
                    try:
                        await _io(session.finish, operation)
                    except Exception:
                        logger.exception(
                            "[PREKVK DIAGNOSTIC] Operation finalization failed session=%s receipt=%s",
                            session.token,
                            receipt.message_id,
                        )
                        if result is not None:
                            result.outcome = "uncertain" if receipt.message_id else "failed"
                            result.detail = (
                                "Operation finalization failed; preserve evidence and do not retry"
                            )
            finally:
                if action == "run":
                    self.active = None


runner = DiagnosticRunner()
