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


def test_source_preview_renders_twelve_blocks_and_explicit_unavailable(monkeypatch):
    from core.discord_embed_limits import require_valid_embed_payload
    from stats_alerts.embeds.kvk import build_source_preview
    from tests.test_kvk_source_reporting import load_synthetic

    report, _, _, _ = load_synthetic(monkeypatch, desired_end=14)
    preview = build_source_preview(report)
    assert len(preview.payload[0].fields) == 12
    assert "configuration pending" in preview.payload[0].description
    assert "13" in preview.payload[0].description and "14" in preview.payload[0].description
    assert "unsupported" in str(preview.payload[0].to_dict())
    require_valid_embed_payload(preview.payload)


def test_source_preview_maximum_names_and_numbers_pack_complete_rows(monkeypatch):
    from decimal import Decimal

    from core.discord_embed_limits import require_valid_embed_payload
    from stats_alerts.embeds.kvk import build_source_preview
    from tests.test_kvk_source_reporting import load_synthetic

    report, _, _, _ = load_synthetic(monkeypatch)
    for rows in report["blocks"].values():
        if rows:
            row = dict(rows[0], name="@everyone **" * 25, dkp=Decimal("9" * 32 + ".123456"))
            rows[:] = [row] * 500
    preview = build_source_preview(report)
    assert "not shown" in str(preview.payload[0].to_dict())
    assert "@everyone" not in str(preview.payload[0].to_dict())
    require_valid_embed_payload(preview.payload)
