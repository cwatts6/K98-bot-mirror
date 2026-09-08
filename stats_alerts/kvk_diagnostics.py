"""Fighting preview orchestration; no production quota or reservation claims."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from uuid import uuid4

from stats_alerts.diagnostics import DiagnosticResult, DiagnosticRunner
from stats_alerts.dispatch_reservations import DispatchGuarded, DispatchUnavailable, _io
from stats_alerts.kvk_diagnostic_sessions import PreviewRepository

logger = logging.getLogger(__name__)


@dataclass
class PreviewPayload:
    payload: object
    available: bool
    detail: str
    digest: str


class PreviewRunner(DiagnosticRunner):
    """Reuse Phase 2H's cancellation/drain lifecycle, not its session or receipt protocol."""

    async def execute(
        self,
        *,
        guild_id,
        channel_id,
        owner_id,
        token,
        action,
        build,
        publish,
        repository=None,
        kvk_no=None,
    ):
        if action not in {"run", "status"} or (action == "status" and token is None):
            raise ValueError("Status requires a preview session")
        if self.stopping or (action == "run" and self.active is not None):
            raise DispatchGuarded("Previews busy or shutting down")
        if action == "run":
            self.active = asyncio.current_task()
        repository = repository or PreviewRepository()
        session = None
        operation = uuid4().hex
        began = False
        entered = False
        receipt = None
        result = None

        def open_session():
            nonlocal session
            session = repository.open(guild_id, channel_id, owner_id, token, kvk_no=kvk_no)

        def begin():
            nonlocal began
            session.begin(operation)
            began = True

        def outcome(kind, detail, snapshot=None):
            nonlocal result
            selected = session.manifest.get("kvk_no")
            if selected is not None:
                detail = f"Selected KVK {selected}. " + detail
            result = DiagnosticResult(kind, session.token, detail, snapshot, receipt)
            return result

        try:
            await _io(open_session)
            if action == "status":
                return outcome(
                    "status",
                    "Read-only preview observation; no dispatch",
                    await _io(session.snapshot),
                )
            await _io(begin)
            before = await _io(session.snapshot)
            selected = session.manifest.get("kvk_no")
            preview = await build(kvk_no=selected) if selected is not None else await build()
            if not preview.available:
                await _io(session.transition, operation, "unavailable")
                return outcome("unavailable", preview.detail, await _io(session.snapshot))

            async def before_send():
                nonlocal entered

                def start():
                    nonlocal entered
                    session.transition(
                        operation,
                        "editing" if before["message_id"] else "sending",
                        digest=preview.digest,
                    )
                    entered = True

                await _io(start)

            receipt = await publish(preview, before["message_id"], before_send)
            if not entered:
                raise DispatchUnavailable("Publisher did not enter the durable boundary")
            await _io(session.transition, operation, "accepted", receipt=receipt)
            await _io(session.transition, operation, "committed")
            return outcome(
                "edited" if before["message_id"] else "sent",
                "Preview receipt committed; not production admission proof. " + preview.detail,
                await _io(session.snapshot),
            )
        except asyncio.CancelledError:
            logger.warning(
                "[KVK PREVIEW] cancelled session=%s receipt=%s; inspect saved state",
                session.token if session else token,
                receipt,
            )
            raise
        except Exception as exc:
            logger.exception(
                "[KVK PREVIEW] unavailable session=%s receipt=%s",
                session.token if session else token,
                receipt,
            )
            if session is None:
                raise
            return outcome(
                (
                    "uncertain"
                    if entered or receipt
                    else "guarded" if isinstance(exc, DispatchGuarded) else "failed"
                ),
                "Inspect saved state; no automatic retry or replacement",
            )
        finally:
            try:
                if began:
                    try:
                        snapshot = await _io(session.snapshot)
                        if snapshot["operations"][-1]["phase"] == "preparing":
                            await _io(session.transition, operation, "failed")
                    finally:
                        await _io(session.finish, operation)
            except Exception:
                logger.exception("[KVK PREVIEW] finalization failed session=%s", session.token)
                if result is not None:
                    result.outcome = "uncertain" if entered or receipt else "failed"
                    result.detail = "Finalization failed; retain evidence and do not retry"
            finally:
                try:
                    if result is not None and result.snapshot is None:
                        try:
                            result.snapshot = await _io(session.snapshot)
                        except Exception:
                            logger.warning(
                                "[KVK PREVIEW] result snapshot unavailable session=%s",
                                session.token,
                                exc_info=True,
                            )
                            result.detail += "; saved state could not be read"
                finally:
                    if action == "run":
                        self.active = None


runner = PreviewRunner()
