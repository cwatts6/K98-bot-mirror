"""Keep local receipt reconciliation from racing a still-running recovery call.

This guard is scheduling only. Durable action intents, domain ownership checks and
receipt verification remain authoritative after restart or a lost acknowledgement.
"""

from contextlib import contextmanager
from threading import Lock
from time import monotonic

_registry_lock = Lock()
_active = {}


@contextmanager
def recovery_execution(incident_id, *, operation=None):
    """Never block the monitor behind a long-running admin action."""
    key = str(operation if operation is not None else incident_id)
    with _registry_lock:
        entry = _active.setdefault(key, [Lock(), 0, monotonic()])
        entry[1] += 1
    acquired = entry[0].acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            entry[0].release()
        with _registry_lock:
            entry[1] -= 1
            if entry[1] == 0:
                del _active[key]


def execution_progress(incident_id, *, operation=None):
    """Transient progress only; durable receipts still decide the outcome."""
    with _registry_lock:
        entry = _active.get(str(operation if operation is not None else incident_id))
        if entry is None or not entry[0].locked():
            return None
        return dict(
            state="in_progress",
            elapsed_seconds=max(0, int(monotonic() - entry[2])),
            verification="Local call is active; final durable verification is still required.",
        )


def operation_key(scope, source_id):
    """Related cards share an operation; account/storage scope stays separate."""
    return repr((scope, str(source_id).lower()))
