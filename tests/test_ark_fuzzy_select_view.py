from __future__ import annotations

import discord

from ark.registration_flow import _build_fuzzy_embed
from ui.views.ark_fuzzy_select_view import ArkFuzzySelectView


def test_build_fuzzy_embed_and_view():
    matches = [
        {"GovernorName": "BlaizeP", "GovernorID": "85574801"},
        {"GovernorName": "BlaccSwan", "GovernorID": "6480196"},
        {"GovernorName": "blackBunny", "GovernorID": "77866768"},
    ]

    embed = _build_fuzzy_embed("bla", matches)
    assert embed.title == "Governor Name Search Results"
    assert "OPTIONS MATCHING" in (embed.description or "")

    view = ArkFuzzySelectView(matches, author_id=123, on_select=lambda *_: None)
    assert isinstance(view.select, discord.ui.Select)
    assert len(view.select.options) == 3
    assert view.select.options[0].label == "BlaizeP"
    assert view.select.options[0].description == "ID: 85574801"
