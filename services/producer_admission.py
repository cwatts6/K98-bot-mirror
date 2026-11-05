"""Fair process-local scheduling before shared-output producers acquire SQL locks.

This queue grants no durable ownership. SQL fences, receipts and session guards
remain mandatory, including for other processes and after restart.
"""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
import logging
from threading import Condition, get_ident
from time import monotonic

from kvk.dal.new_source_import_dal import SourceBusy, SourceConflict

logger = logging.getLogger(__name__)
_condition = Condition()
_queue = deque()
_active = None
_inherited = ContextVar("producer_admission", default=None)


@contextmanager
def producer_turn(*, timeout=900.0):
    """Wait without a SQL connection; nested synchronous helpers reuse the turn."""
    global _active
    inherited = _inherited.get()
    with _condition:
        if inherited is not None:
            if inherited is not _active or inherited[1] != get_ident():
                raise SourceConflict(
                    "A delayed or parallel producer cannot reuse this scheduling turn."
                )
            nested = True
            ticket = inherited
        else:
            nested = False
            ticket = (object(), get_ident())
            started = monotonic()
            _queue.append(ticket)
            try:
                if _active is not None or _queue[0] is not ticket:
                    logger.info("producer_admission_waiting state=waiting_for_shared_outputs")
                if not _condition.wait_for(
                    lambda: _active is None and _queue[0] is ticket, timeout=timeout
                ):
                    raise SourceBusy(
                        "Shared output work is still active; this producer has not started."
                    )
                _active = ticket
            finally:
                _queue.remove(ticket)
                _condition.notify_all()
            logger.info("producer_admission_ready wait_ms=%s", int((monotonic() - started) * 1000))
    token = _inherited.set(ticket)
    try:
        yield
    finally:
        _inherited.reset(token)
        if not nested:
            with _condition:
                _active = None
                _condition.notify_all()
