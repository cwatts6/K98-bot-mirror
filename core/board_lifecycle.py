"""Small domain-neutral board policy; persistence and completion belong to callers.

An ended event can still await results. Only a domain-final event freezes its
payload. Delivery and retirement are separate facts, never inferred from age.
"""

from dataclasses import dataclass
from enum import StrEnum


class BoardWork(StrEnum):
    REFRESH = "refresh"
    FINAL_EDIT = "final_edit"
    RECONCILE = "reconcile"
    NONE = "none"


@dataclass(frozen=True)
class BoardLifecycle:
    domain_final: bool
    delivery_state: str
    retired: bool = False
    refresh_allowed: bool = True

    def work(self) -> BoardWork:
        if self.retired or self.delivery_state in {"retired", "confirmed", "held", "legacy_frozen"}:
            return BoardWork.NONE
        if not self.domain_final:
            return BoardWork.REFRESH if self.refresh_allowed else BoardWork.NONE
        if self.delivery_state in {"pending", "failed"}:
            return BoardWork.FINAL_EDIT
        if self.delivery_state == "unknown":
            return BoardWork.RECONCILE
        return BoardWork.NONE
