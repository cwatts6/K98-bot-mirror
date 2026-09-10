from __future__ import annotations

from decimal import Decimal

import pytest

from kvk.combat_metrics import calculate_combat_metrics


@pytest.mark.parametrize(
    ("kill_points", "healed", "deads", "kills", "kp_loss", "score", "engaged"),
    [
        (None, None, None, None, None, None, False),
        (100, 0, 0, 1, 0, None, True),
        (1_000, 0, 100, 1, 0, None, True),
        (1_000, 10, 0, 1, 200, Decimal("500.00000000"), True),
        (5_000, 10, 100, 1, 200, Decimal("1666.66666667"), True),
        (0, 10, 100, 0, 200, Decimal("0.00000000"), False),
    ],
)
def test_python_combat_metrics_match_sql_migration_fixtures(
    kill_points, healed, deads, kills, kp_loss, score, engaged
) -> None:
    result = calculate_combat_metrics(
        kill_points=kill_points,
        healed=healed,
        deads=deads,
        t4_t5_kills=kills,
    )

    assert result.kp_loss == kp_loss
    assert result.engaged is engaged
    if score is None:
        assert result.tanking_score is None
    else:
        assert result.tanking_score is not None
        assert result.tanking_score.quantize(Decimal("0.00000001")) == score


def test_engaged_requires_positive_kp_and_combat_evidence() -> None:
    no_evidence = calculate_combat_metrics(
        kill_points=100,
        healed=0,
        deads=0,
        t4_t5_kills=0,
    )
    deads_evidence = calculate_combat_metrics(
        kill_points=100,
        healed=0,
        deads=10,
        t4_t5_kills=0,
    )

    assert no_evidence.engaged is False
    assert no_evidence.tanking_score is None
    assert deads_evidence.engaged is True
    assert deads_evidence.tanking_score is None
