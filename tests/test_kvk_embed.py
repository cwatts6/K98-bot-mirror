from __future__ import annotations

import logging

from stats_alerts.embeds.kvk import _fmt_top_list, _truncate_and_log


def test_kvk_top_list_ignores_structured_contribution_fields() -> None:
    text = _fmt_top_list(
        [
            {
                "name": "Alice",
                "kills_gain": 1234,
                "kp_gain": 5678,
                "deads": 9,
                "dkp": 42,
                "healed_troops": 100,
                "acclaim_gain": 888,
            }
        ],
        name_key="name",
        kp_key="kp_gain",
        healed_key="healed_troops",
    )

    assert "Alice" in text
    assert "Kills:" in text
    assert "KP:" in text
    assert "deads:" in text
    assert "dkp:" in text
    assert "healed:" in text
    assert "contribute" not in text.lower()
    assert "acclaim" not in text.lower()
    assert "999" not in text
    assert "888" not in text


def test_kvk_truncation_stability_logs_and_limits(caplog) -> None:
    caplog.set_level(logging.WARNING)
    result = _truncate_and_log("All Players — Top Kills", "x" * 1100, max_len=32)

    assert len(result) == 32
    assert result.endswith("…")
    assert "truncated from 1100 to 32" in caplog.text
