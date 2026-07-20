"""Canonical pure KVK combat metrics shared by every bot consumer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CombatMetrics:
    kp_loss: int | None
    tanking_score: Decimal | None
    engaged: bool


def calculate_combat_metrics(
    *,
    kill_points: int | None,
    healed: int | None,
    deads: int | None,
    t4_t5_kills: int | None,
) -> CombatMetrics:
    """Return KP Loss, higher-is-better Tanking Score, and rank engagement."""
    kp_loss = int(healed) * 20 if healed is not None else None
    engaged = bool(
        kill_points is not None
        and int(kill_points) > 0
        and (
            (t4_t5_kills is not None and int(t4_t5_kills) > 0)
            or (deads is not None and int(deads) > 0)
            or (healed is not None and int(healed) > 0)
        )
    )
    if kill_points is None or kp_loss is None or deads is None:
        return CombatMetrics(kp_loss=kp_loss, tanking_score=None, engaged=engaged)
    denominator = kp_loss + int(deads)
    score = None
    if denominator > 0:
        score = Decimal(int(kill_points)) * Decimal(100) / Decimal(denominator)
    return CombatMetrics(kp_loss=kp_loss, tanking_score=score, engaged=engaged)
