import discord

import honor_rankings_view as hrv


def test_build_honor_rankings_embed_no_rows():
    embed = hrv.build_honor_rankings_embed(rows=None, limit=10)
    assert isinstance(embed, discord.Embed)
    assert embed.description == "No matching players found."
    assert "Top Honor" in embed.title
    # timestamp should be present (set to utcnow)
    assert getattr(embed, "timestamp", None) is not None


def test_build_honor_rankings_embed_formats_rows_and_normalizes_name():
    rows = [
        {"GovernorName": None, "GovernorID": 123, "HonorPoints": 1000},
        {"GovernorName": "Alice", "GovernorID": 456, "HonorPoints": 2000},
    ]
    embed = hrv.build_honor_rankings_embed(rows, limit=2)
    # description should have two lines
    desc = embed.description or ""
    lines = desc.splitlines()
    assert len(lines) == 2
    # check first line uses the numeric id for missing name and has thousand separator
    assert "**123**" in lines[0] or "123" in lines[0]
    assert "1,000" in lines[0]
    # check second line contains Alice
    assert "**Alice**" in lines[1]
    # field "Shown" must reflect limit
    shown_field = next((f for f in embed.fields if f.name == "Shown"), None)
    assert shown_field is not None
    assert "Top 2" in shown_field.value
