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
def recovery_execution(incident_id):
    """Never block the monitor behind a long-running admin action."""
    with _registry_lock:
        entry = _active.setdefault(str(incident_id), [Lock(), 0, monotonic()])
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
                del _active[str(incident_id)]


def execution_progress(incident_id):
    """Transient progress only; durable receipts still decide the outcome."""
    with _registry_lock:
        entry = _active.get(str(incident_id))
        if entry is None or not entry[0].locked():
            return None
        return dict(
            state="in_progress",
            elapsed_seconds=max(0, int(monotonic() - entry[2])),
            verification="Local call is active; final durable verification is still required.",
        )
