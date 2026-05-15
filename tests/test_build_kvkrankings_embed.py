# tests/test_build_kvkrankings_embed.py
"""
Unit tests for build_KVKrankings_embed.py

Updated to match new behavior:
- Medal emojis removed; top-3 highlighted as "*1", "*2", "*3"
- Embed builder filters by STATUS == "INCLUDED" and Starting Power >= 40_000_000 by default
- Column header "% K/T" used for percent kill target
"""

from build_KVKrankings_embed import (
    _safe_get_deads,
    _safe_get_dkp,
    _safe_get_kills,
    _safe_get_pct_kill_target,
    _safe_get_power,
    _to_float,
    _to_int,
    _value_getter,
    build_kvkrankings_embed,
)

# === Test helpers (_to_int, _to_float) ===


def test_to_int_handles_valid_int():
    assert _to_int(123) == 123
    assert _to_int("456") == 456
    assert _to_int(789.0) == 789


def test_to_int_handles_float_string():
    assert _to_int("123.0") == 123
    assert _to_int("456.7") == 456  # Truncates


def test_to_int_handles_none():
    assert _to_int(None) == 0
    assert _to_int(None, default=99) == 99


def test_to_int_handles_empty_string():
    assert _to_int("") == 0
    assert _to_int("", default=42) == 42


def test_to_int_handles_invalid():
    assert _to_int("abc") == 0
    assert _to_int("abc", default=100) == 100


def test_to_float_handles_valid():
    assert _to_float(123.45) == 123.45
    assert _to_float("678.9") == 678.9
    assert _to_float(100) == 100.0


def test_to_float_handles_none():
    assert _to_float(None) == 0.0
    assert _to_float(None, default=99.9) == 99.9


def test_to_float_handles_empty_string():
    assert _to_float("") == 0.0


def test_to_float_handles_invalid():
    assert _to_float("not_a_number") == 0.0


# === Test safe getters ===


def test_safe_get_power_uses_starting_power():
    """Primary field is 'Starting Power'."""
    row = {"Starting Power": 132395931}
    assert _safe_get_power(row) == 132395931


def test_safe_get_power_fallback_to_power():
    """Falls back to 'Power' if 'Starting Power' missing."""
    row = {"Power": 100000000}
    assert _safe_get_power(row) == 100000000


def test_safe_get_power_handles_missing():
    """Returns 0 if both fields missing."""
    assert _safe_get_power({}) == 0
    assert _safe_get_power({"Starting Power": None}) == 0


def test_safe_get_power_prefers_starting_power():
    """'Starting Power' takes precedence when both present."""
    row = {"Starting Power": 200000000, "Power": 100000000}
    assert _safe_get_power(row) == 200000000


def test_safe_get_kills_uses_combined_field():
    """Primary field is 'T4&T5_Kills'."""
    row = {"T4&T5_Kills": 18475861}
    assert _safe_get_kills(row) == 18475861


def test_safe_get_kills_fallback_to_sum():
    """Falls back to T4_Kills + T5_Kills if combined field is 0."""
    row = {"T4&T5_Kills": 0, "T4_Kills": 1373491, "T5_Kills": 17102370}
    assert _safe_get_kills(row) == 18475861


def test_safe_get_kills_sum_when_combined_missing():
    """Uses sum when combined field is missing entirely."""
    row = {"T4_Kills": 1000000, "T5_Kills": 2000000}
    assert _safe_get_kills(row) == 3000000


def test_safe_get_kills_handles_missing():
    """Returns 0 if all fields missing."""
    assert _safe_get_kills({}) == 0


def test_safe_get_deads_uses_delta():
    """Primary field is 'Deads_Delta'."""
    row = {"Deads_Delta": 905708}
    assert _safe_get_deads(row) == 905708


def test_safe_get_deads_fallback_to_deads():
    """Falls back to 'Deads' if 'Deads_Delta' missing."""
    row = {"Deads": 500000}
    assert _safe_get_deads(row) == 500000


def test_safe_get_deads_handles_missing():
    """Returns 0 if both fields missing."""
    assert _safe_get_deads({}) == 0


def test_safe_get_dkp_uses_dkp_score():
    """Primary field is 'DKP_SCORE'."""
    row = {"DKP_SCORE": 62673247}
    assert _safe_get_dkp(row) == 62673247.0


def test_safe_get_dkp_fallback_to_dkp_space():
    """Falls back to 'DKP Score' (with space)."""
    row = {"DKP Score": 12345678}
    assert _safe_get_dkp(row) == 12345678.0


def test_safe_get_dkp_handles_missing():
    """Returns 0.0 if both fields missing."""
    assert _safe_get_dkp({}) == 0.0


def test_safe_get_pct_kill_target():
    """Uses '% of Kill Target' field (already calculated in cache)."""
    row = {"% of Kill Target": 123.17}
    assert _safe_get_pct_kill_target(row) == 123.17


def test_safe_get_pct_kill_target_handles_missing():
    """Returns 0.0 if field missing."""
    assert _safe_get_pct_kill_target({}) == 0.0


# === Test _value_getter ===


def test_value_getter_power():
    """Power metric returns correct getter and uses fmt_short."""
    label, getter, formatter = _value_getter("power")
    assert label == "Power"

    row = {"Starting Power": 100000000}
    assert getter(row) == 100000000

    # formatter should be fmt_short (produces "100M")
    formatted = formatter(100000000)
    assert "M" in formatted  # Should be "100M" or "100.0M"


def test_value_getter_kills():
    """Kills metric returns correct getter and uses fmt_short."""
    label, getter, formatter = _value_getter("kills")
    assert label == "Kills (T4+T5)"

    row = {"T4&T5_Kills": 5000000}
    assert getter(row) == 5000000

    formatted = formatter(5000000)
    assert "M" in formatted  # Should be "5M" or "5.0M"


def test_value_getter_pct_kill_target():
    """% Kill Target returns correct getter and percentage formatter."""
    label, getter, formatter = _value_getter("pct_kill_target")
    assert label == "% Kill Target"

    row = {"% of Kill Target": 85.67}
    assert getter(row) == 85.67

    # Formatter should produce percentage string
    formatted = formatter(85.67)
    assert formatted == "86%"  # Rounds to nearest int


def test_value_getter_deads():
    """Deads metric returns correct getter and uses fmt_short."""
    label, getter, formatter = _value_getter("deads")
    assert label == "Deads"

    row = {"Deads_Delta": 905708}
    assert getter(row) == 905708

    formatted = formatter(905708)
    assert "k" in formatted.lower()  # Should be "905k" or "905.7k"


def test_value_getter_dkp():
    """DKP metric returns correct getter and uses fmt_short."""
    label, getter, formatter = _value_getter("dkp")
    assert label == "DKP"

    row = {"DKP_SCORE": 62673247}
    assert getter(row) == 62673247.0

    formatted = formatter(62673247)
    assert "M" in formatted  # Should be "62M" or "62.7M"


def test_value_getter_default_to_kills():
    """Invalid metric defaults to power (changed in PR2)."""
    label, getter, _ = _value_getter("invalid_metric")
    assert label == "Power"  # CHANGED: now defaults to power, not kills


def test_value_getter_none_defaults_to_kills():
    """None metric defaults to power (changed in PR2)."""
    label, getter, _ = _value_getter(None)
    assert label == "Power"  # CHANGED: now defaults to power, not kills


# === Test build_kvkrankings_embed ===


def test_build_embed_basic():
    """Basic embed building with valid data."""
    rows = [
        {
            "GovernorID": "123",
            "GovernorName": "TestPlayer",
            "Starting Power": 100_000_000,
            "T4&T5_Kills": 5_000_000,
            "Deads_Delta": 500_000,
            "DKP_SCORE": 12345678,
            "% of Kill Target": 33.33,
            "LAST_REFRESH": "2026-02-08",
            "STATUS": "INCLUDED",
        }
    ]
    embed = build_kvkrankings_embed(rows, "kills", 10)

    # Check basic structure
    assert embed.title == "🏆 Top Kills — Current KVK"
    assert "TestPlayer" in embed.description
    # Top player is now indicated with "*1"
    assert "*1" in embed.description

    # CHANGED: Multi-column format uses footer instead of fields
    # Check footer exists and has content
    assert embed.footer.text is not None
    assert "Sorted by:" in embed.footer.text
    assert "2026-02-08" in embed.footer.text


def test_build_embed_uses_fmt_short():
    """Embed uses fmt_short for number formatting."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "Test",
            "Starting Power": 123_456_789,
            "T4&T5_Kills": 18_475_861,
            "STATUS": "INCLUDED",
        }
    ]
    embed = build_kvkrankings_embed(rows, "kills", 1)
    desc = embed.description

    # Should use k/M notation, not comma-separated
    assert "18.5M" in desc or "18.4M" in desc
    assert "18,475,861" not in desc  # Full number should NOT appear


def test_build_embed_sort_by_power():
    """Sorting by power works correctly."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "Low",
            "Starting Power": 1_000_000_000,
            "T4&T5_Kills": 10_000_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "GovernorName": "High",
            "Starting Power": 2_000_000_000,
            "T4&T5_Kills": 1_000_000,
            "STATUS": "INCLUDED",
        },
    ]
    embed = build_kvkrankings_embed(rows, "power", 10)

    # "High" should be ranked #1 (higher power)
    lines = embed.description.split("\n")
    assert any("High" in line and "*1" in line for line in lines)


def test_build_embed_sort_by_pct_kill_target():
    """Sorting by % kill target works correctly."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "Over",
            "% of Kill Target": 150.0,
            "Starting Power": 1_000_000_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "GovernorName": "Under",
            "% of Kill Target": 50.0,
            "Starting Power": 2_000_000_000,
            "STATUS": "INCLUDED",
        },
    ]
    embed = build_kvkrankings_embed(rows, "pct_kill_target", 10)

    # "Over" should be ranked #1 (150% > 50%)
    lines = embed.description.split("\n")
    assert any("Over" in line and "*1" in line for line in lines)


def test_build_embed_tiebreaker_by_power():
    """When metric ties, power is used as tiebreaker."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "LowPower",
            "T4&T5_Kills": 5_000_000,
            "Starting Power": 1_000_000_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "GovernorName": "HighPower",
            "T4&T5_Kills": 5_000_000,
            "Starting Power": 100_000_000_000,
            "STATUS": "INCLUDED",
        },
    ]
    embed = build_kvkrankings_embed(rows, "kills", 10)

    # "HighPower" should be ranked #1 (same kills, higher power)
    lines = embed.description.split("\n")
    data_lines = [line for line in lines if "HighPower" in line or "LowPower" in line]

    assert len(data_lines) >= 2
    assert "HighPower" in data_lines[0]
    assert "*1" in data_lines[0]


def test_build_embed_medals_for_top_3():
    """Top 3 players are highlighted with *1/*2/*3 markers."""
    rows = [
        {
            "GovernorID": str(i),
            "GovernorName": f"Player{i}",
            "Starting Power": 100_000_000 + (1000 - i),
            "STATUS": "INCLUDED",
        }
        for i in range(5)
    ]
    embed = build_kvkrankings_embed(rows, "power", 10)
    desc = embed.description

    assert "*1" in desc  # 1st place
    assert "*2" in desc  # 2nd place
    assert "*3" in desc  # 3rd place


def test_build_embed_limit_respected():
    """Limit parameter controls number of players shown."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(100)
    ]
    embed = build_kvkrankings_embed(rows, "power", 25)

    # Count data lines (exclude code block markers, header, separator)
    lines = [line for line in embed.description.split("\n") if line.strip()]
    data_lines = [
        line
        for line in lines
        if any(char.isdigit() for char in line) and "Rank" not in line and "─" not in line
    ]
    assert len(data_lines) == 25


def test_build_embed_empty_rows():
    """Empty rows list produces valid embed (shows header even with no data)."""
    embed = build_kvkrankings_embed([], "power", 10)

    assert embed is not None
    assert embed.description is not None
    assert "```" in embed.description  # Still in code block
    assert "Rank" in embed.description  # Header still shown


def test_build_embed_single_player():
    """Single player produces valid embed."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "Solo",
            "Starting Power": 100_000_000,
            "STATUS": "INCLUDED",
        }
    ]
    embed = build_kvkrankings_embed(rows, "power", 10)

    assert "Solo" in embed.description
    assert "*1" in embed.description


def test_build_embed_missing_all_fields():
    """Row with only GovernorID doesn't crash (filtering may exclude it)."""
    rows = [{"GovernorID": "1"}]
    embed = build_kvkrankings_embed(rows, "power", 10)

    assert embed is not None
    assert len(embed.description) > 0


def test_build_embed_missing_governor_name():
    """Missing GovernorName falls back to GovernorID when included."""
    rows = [{"GovernorID": "12345", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]
    embed = build_kvkrankings_embed(rows, "power", 10)

    assert "12345" in embed.description


def test_build_embed_title_map():
    """Different metrics produce different titles."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]

    assert "Top Power" in build_kvkrankings_embed(rows, "power", 10).title
    assert "Top Kills" in build_kvkrankings_embed(rows, "kills", 10).title
    assert "Top % Kill Target" in build_kvkrankings_embed(rows, "pct_kill_target", 10).title
    assert "Top Deads" in build_kvkrankings_embed(rows, "deads", 10).title
    assert "Top DKP" in build_kvkrankings_embed(rows, "dkp", 10).title


def test_build_embed_last_refresh_from_rows():
    """Last refresh uses max value from rows."""
    rows = [
        {
            "GovernorID": "1",
            "Starting Power": 100_000_000,
            "LAST_REFRESH": "2026-02-07",
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "Starting Power": 200_000_000,
            "LAST_REFRESH": "2026-02-08",
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "3",
            "Starting Power": 300_000_000,
            "LAST_REFRESH": "2026-02-06",
            "STATUS": "INCLUDED",
        },
    ]
    embed = build_kvkrankings_embed(rows, "power", 10)

    assert embed.footer.text is not None
    assert "2026-02-08" in embed.footer.text  # Max date


def test_build_embed_no_last_refresh():
    """Missing LAST_REFRESH doesn't crash (footer still set)."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]
    embed = build_kvkrankings_embed(rows, "power", 10)

    assert embed is not None


# === PR2: Multi-column format tests ===


def test_multicolumn_format_shows_all_six_columns():
    """Multi-column format displays all 6 data columns."""
    rows = [
        {
            "GovernorID": "123",
            "GovernorName": "TestPlayer",
            "Starting Power": 100_000_000,
            "T4&T5_Kills": 5_000_000,
            "Deads_Delta": 500_000,
            "DKP_SCORE": 12345678,
            "% of Kill Target": 33.0,
            "STATUS": "INCLUDED",
        }
    ]
    embed = build_kvkrankings_embed(rows, "power", 10)
    desc = embed.description

    # Should be in code block
    assert "```" in desc

    # Check all columns present
    assert "TestPlayer" in desc
    assert "100M" in desc or "100.0M" in desc  # Power
    assert "5M" in desc or "5.0M" in desc  # Kills
    assert "33%" in desc  # % Target
    assert "500k" in desc or "500.0k" in desc  # Deads
    assert "12.3M" in desc or "12.4M" in desc  # DKP


def test_multicolumn_header_shows_column_names():
    """Header row shows all column names."""
    rows = [{"GovernorID": "1", "Starting Power": 1_000_000, "STATUS": "INCLUDED"}]
    embed = build_kvkrankings_embed(rows, "power", 10)
    desc = embed.description

    # Header should contain column names
    assert "Rank" in desc
    assert "Name" in desc
    assert "Power" in desc
    assert "Kills" in desc
    assert "% K/T" in desc
    assert "Dead" in desc
    assert "DKP" in desc


def test_sort_indicator_shows_on_active_column():
    """Excel-style sort indicator (▼) appears on active sort column."""
    rows = [
        {
            "GovernorID": "1",
            "Starting Power": 1_000_000_000,
            "T4&T5_Kills": 5_000_000,
            "STATUS": "INCLUDED",
        }
    ]

    # Test Power sort
    embed = build_kvkrankings_embed(rows, "power", 10)
    assert "Power" in embed.description and "▼" in embed.description

    # Test Kills sort
    embed = build_kvkrankings_embed(rows, "kills", 10)
    assert "Kills" in embed.description and "▼" in embed.description


def test_sort_indicator_moves_with_metric():
    """Sort indicator moves when changing metric."""
    rows = [
        {
            "GovernorID": "1",
            "Starting Power": 1_000_000_000,
            "Deads_Delta": 100_000,
            "STATUS": "INCLUDED",
        }
    ]

    for metric in ["power", "kills", "pct_kill_target", "deads", "dkp"]:
        embed = build_kvkrankings_embed(rows, metric, 10)
        # Should contain exactly one ▼ indicator
        assert embed.description.count("▼") == 1


def test_pagination_page_1_of_2():
    """Top 100 limit creates 2 pages, page 1 shows first 50."""
    rows = [
        {
            "GovernorID": str(i),
            "GovernorName": f"Player{i:03d}",
            "Starting Power": 1_000_000_000 - i,
            "STATUS": "INCLUDED",
        }
        for i in range(100)
    ]

    # Page 1: rows 1-50
    embed = build_kvkrankings_embed(rows, "power", 100, page=1)

    # Check title shows page indicator
    assert "Page 1/2" in embed.title

    # Check description contains first 50 players
    desc = embed.description
    assert "Player000" in desc  # 1st player
    assert "Player049" in desc  # 50th player
    assert "Player050" not in desc  # 51st player (not on page 1)

    # Check footer shows range
    assert "1-50 of 100" in embed.footer.text


def test_pagination_page_2_of_2():
    """Page 2 shows players 51-100."""
    rows = [
        {
            "GovernorID": str(i),
            "GovernorName": f"Player{i:03d}",
            "Starting Power": 1_000_000_000 - i,
            "STATUS": "INCLUDED",
        }
        for i in range(100)
    ]

    # Page 2: rows 51-100
    embed = build_kvkrankings_embed(rows, "power", 100, page=2)

    # Check title shows page 2
    assert "Page 2/2" in embed.title

    # Check description contains last 50 players
    desc = embed.description
    assert "Player050" in desc  # 51st player
    assert "Player099" in desc  # 100th player
    assert "Player000" not in desc  # 1st player (not on page 2)

    # Check footer shows range
    assert "51-100 of 100" in embed.footer.text


def test_pagination_no_indicator_for_single_page():
    """Single page views don't show page indicator in title."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]

    # Top 10, 25, 50 should not show page indicator
    for limit in [10, 25, 50]:
        embed = build_kvkrankings_embed(rows, "power", limit)
        assert "Page" not in embed.title


def test_pagination_page_clamping_low():
    """Page 0 or negative clamps to page 1."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(100)
    ]

    embed = build_kvkrankings_embed(rows, "power", 100, page=0)
    assert "Page 1/2" in embed.title

    embed = build_kvkrankings_embed(rows, "power", 100, page=-5)
    assert "Page 1/2" in embed.title


def test_pagination_page_clamping_high():
    """Page > max_pages clamps to max."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(100)
    ]

    # Max pages is 2 for 100 players
    embed = build_kvkrankings_embed(rows, "power", 100, page=999)
    assert "Page 2/2" in embed.title


def test_long_name_truncation():
    """Names longer than width are truncated with ellipsis."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "VeryLongPlayerNameThatExceeds16Characters",
            "Starting Power": 41_000_000,
            "STATUS": "INCLUDED",
        }
    ]
    embed = build_kvkrankings_embed(rows, "power", 10)

    # Name should be truncated and show an ellipsis; full name must not appear
    assert "…" in embed.description
    assert "VeryLongPlayerNameThatExceeds16Characters" not in embed.description


def test_code_block_formatting():
    """Description uses code block for monospace alignment."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]
    embed = build_kvkrankings_embed(rows, "power", 10)

    # Should start and end with ```
    assert embed.description.startswith("```")
    assert embed.description.endswith("```")


def test_separator_line_in_header():
    """Header includes separator line (dashes) after column names."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]
    embed = build_kvkrankings_embed(rows, "power", 10)

    # Should contain a line of dashes as separator
    assert "─" in embed.description or "-" in embed.description


def test_footer_sorted_by_info():
    """Footer shows 'Sorted by: {metric} (Descending)'."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]

    embed = build_kvkrankings_embed(rows, "power", 10)
    assert "Sorted by: Power (Descending)" in embed.footer.text

    embed = build_kvkrankings_embed(rows, "kills", 10)
    assert "Sorted by: Kills (T4+T5) (Descending)" in embed.footer.text


def test_footer_showing_info_single_page():
    """Footer shows 'Showing: Top {limit}' for single-page views."""
    rows = [{"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"}]

    embed = build_kvkrankings_embed(rows, "power", 25)
    assert "Showing: Top 25" in embed.footer.text


def test_footer_showing_info_multi_page():
    """Footer shows 'Showing: X-Y of Z' for multi-page views."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(100)
    ]

    embed = build_kvkrankings_embed(rows, "power", 100, page=1)
    assert "Showing: 1-50 of 100" in embed.footer.text

    embed = build_kvkrankings_embed(rows, "power", 100, page=2)
    assert "Showing: 51-100 of 100" in embed.footer.text


def test_all_metrics_produce_valid_embeds():
    """All 5 metrics produce valid multi-column embeds."""
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "Test",
            "Starting Power": 100_000_000,
            "T4&T5_Kills": 5_000_000,
            "% of Kill Target": 75.5,
            "Deads_Delta": 500_000,
            "DKP_SCORE": 12_000_000,
            "STATUS": "INCLUDED",
        }
    ]

    metrics = ["power", "kills", "pct_kill_target", "deads", "dkp"]

    for metric in metrics:
        embed = build_kvkrankings_embed(rows, metric, 10)

        # Basic validity checks
        assert embed.title is not None
        assert embed.description is not None
        assert len(embed.description) > 0
        assert "```" in embed.description  # Code block
        assert embed.footer.text is not None
        assert "Sorted by:" in embed.footer.text


def test_empty_rows_multicolumn():
    """Empty rows produces valid embed with no-data message."""
    embed = build_kvkrankings_embed([], "power", 10)

    assert embed is not None
    assert embed.title is not None
    assert embed.description is not None


def test_default_metric_changed_to_power():
    """Default metric is now 'power' (changed from 'kills' in PR1)."""
    rows = [
        {
            "GovernorID": "1",
            "Starting Power": 100_000_000,
            "T4&T5_Kills": 1_000_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "Starting Power": 50_000_000,
            "T4&T5_Kills": 10_000_000,
            "STATUS": "INCLUDED",
        },
    ]

    # Call without metric parameter (uses default)
    embed = build_kvkrankings_embed(rows, limit=10)

    # Should be sorted by power (GovernorID "1" first, higher power)
    assert "Top Power" in embed.title
    lines = embed.description.split("\n")
    assert any("*1" in line for line in lines)


def test_page_parameter_default_is_1():
    """page parameter defaults to 1."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(100)
    ]

    # Call without page parameter
    embed = build_kvkrankings_embed(rows, "power", 100)

    # Should show page 1
    assert "Page 1/2" in embed.title
    assert "1-50 of 100" in embed.footer.text


def test_exact_50_players_no_pagination():
    """Exactly 50 players (page boundary) doesn't trigger pagination."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(50)
    ]

    embed = build_kvkrankings_embed(rows, "power", 50)

    # Should NOT show page indicator
    assert "Page" not in embed.title
    assert "Showing: Top 50" in embed.footer.text


def test_51_players_triggers_pagination():
    """51 players triggers pagination (2 pages)."""
    rows = [
        {"GovernorID": str(i), "Starting Power": 100_000_000 + i, "STATUS": "INCLUDED"}
        for i in range(51)
    ]

    embed = build_kvkrankings_embed(rows, "power", 51, page=1)

    # Should show pagination (51 players = 2 pages)
    assert "Page 1/2" in embed.title
