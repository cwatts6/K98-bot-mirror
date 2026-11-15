"""One optional calendar audit context; no backlog, reconnect, replay or rebind."""

import asyncio
from contextvars import Context
from copy import deepcopy
from dataclasses import dataclass

from core.operation_evidence import optional
from core.owned_work import drain_awaitable, drain_thread
from event_calendar import audit_dal
from event_calendar.sql_lifecycle import error_facts
from services.operation_diagnostics import upload_worker_summary

MAX_COUNTER = 2**63 - 1


@dataclass
class AuditTicket:
    reference: str
    terminal: asyncio.Future


class SyncAudit:
    def __init__(self):
        self.closed = False
        self.task = None
        self.retained = None
        self.state = "not_started"
        self.first_error = None
        self.dropped = 0
        self.failures = 0
        self.reference = None

    def _observe(self):
        optional(
            upload_worker_summary,
            "calendar",
            self.state,
            0,
            (self.first_error or {}).get("error_type"),
            self.dropped,
            self.failures,
        )

    def offer(self, reference, started):
        if self.closed or self.retained is not None or (self.task and not self.task.done()):
            self.dropped = min(MAX_COUNTER, self.dropped + 1)
            self._observe()
            return None
        ticket = AuditTicket(reference, asyncio.get_running_loop().create_future())
        self.reference = reference
        self.state = "starting"
        # Audit offloads have no business diagnostic scope; their one summary slot
        # cannot displace retained business history even under an offer storm.
        self.task = asyncio.create_task(self._run(ticket, started), context=Context())
        self._observe()
        return ticket

    def finish(self, ticket, result, completed):
        if ticket is not None and not ticket.terminal.done():
            # Fixed source projection, bounded error classes, no Sheets data.
            fields = (
                "status",
                "rows_read_recurring",
                "rows_read_oneoff",
                "rows_read_overrides",
                "rows_upserted_recurring",
                "rows_upserted_oneoff",
                "rows_upserted_overrides",
                "instances_generated",
                "error_message",
            )
            terminal = {key: result.get(key) for key in fields}
            ticket.terminal.set_result((terminal, completed))

    def _accept(self, result):
        if result.sql.cleanup == "unconfirmed":
            self.retained = result
            self.state = "cleanup_unconfirmed"
        elif result.sql.effect != "committed":
            self.state = "failed"
        else:
            return True
        self.failures = min(MAX_COUNTER, self.failures + 1)
        if self.first_error is None:
            self.first_error = result.sql.error or result.sql.cleanup_error
        return False

    async def _run(self, ticket, started):
        try:
            initial = await drain_thread(audit_dal.start, started)
            if not self._accept(initial) or initial.sync_id is None:
                return
            self.state = "waiting_for_business"
            self._observe()
            result, completed = await ticket.terminal
            self.state = "finishing"
            self._observe()
            terminal = await drain_thread(audit_dal.finish, initial.sync_id, result, completed)
            if self._accept(terminal):
                self.state = "settled"
        except Exception as error:
            self.state = "failed"
            self.failures = min(MAX_COUNTER, self.failures + 1)
            if self.first_error is None:
                self.first_error = error_facts(error)
        finally:
            self._observe()

    def close_admission(self):
        self.closed = True

    async def drain(self):
        if self.task is not None:
            await drain_awaitable(self.task)
        return self.retained is None

    def snapshot(self):
        return deepcopy(
            dict(
                state=self.state,
                reference=self.reference,
                admission_closed=self.closed,
                first_error=self.first_error,
                dropped=self.dropped,
                failures=self.failures,
            )
        )
