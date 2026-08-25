from __future__ import annotations

from targets_embed import build_kvk_targets_embed


def _targets(**overrides):
    values = {
        "GovernorID": "123",
        "GovernorName": "Governor",
        "KVK_NO": 16,
        "DKP_Target": 100,
        "Kill_Target": 200,
        "Deads_Target": 10,
        "Min_Kill_Target": 50,
        "TargetState": "OFFICIAL",
        "TargetSourceScan": 1059,
        "TargetPublishedAt": "2026-08-25T12:00:00+00:00",
    }
    values.update(overrides)
    return values


def test_legacy_embed_shows_canonical_official_source():
    embed = build_kvk_targets_embed("Governor", 123, _targets(), "Tides of War")

    assert "OFFICIAL" in embed.description
    assert "exact matchmaking scan 1059" in embed.description
    assert "Official targets" in embed.footer.text
    assert "Published 2026-08-25T12:00:00+00:00" in embed.footer.text


def test_legacy_embed_missing_state_defaults_unverified():
    targets = _targets()
    targets.pop("TargetState")
    targets.pop("TargetSourceScan")

    embed = build_kvk_targets_embed("Governor", 123, targets, "Tides of War")

    assert "UNVERIFIED" in embed.description
    assert "could not be verified" in embed.description
    assert "Do not treat this target set as Official" in embed.description


def test_legacy_active_state_is_not_treated_as_official():
    embed = build_kvk_targets_embed(
        "Governor",
        123,
        _targets(TargetState="ACTIVE"),
        "Tides of War",
    )

    assert "UNVERIFIED" in embed.description
