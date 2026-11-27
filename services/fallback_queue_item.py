"""One immutable attachment selection per admitted Discord message."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FallbackQueueItem:
    message: Any
    attachments: tuple[Any, ...]


def selected_attachments(item):
    if isinstance(item, FallbackQueueItem):
        return item.message, item.attachments
    # Compatibility for an in-memory item queued before this route was used.
    return item, tuple(
        a for a in item.attachments if a.filename.lower().endswith((".xlsx", ".xls", ".csv"))
    )
