from ark.team_state import ArkTeamStateStore


def test_team_state_create_reset(tmp_path):
    p = tmp_path / "ark_team_state.json"
    store = ArkTeamStateStore.load(path=p)
    a = store.get_or_create(match_id=77, roster_player_ids=[1, 2, 3], actor_discord_id=9)
    a.team1_player_ids = [1]
    a.team2_player_ids = [2]
    store.save()

    loaded = ArkTeamStateStore.load(path=p)
    assert 77 in loaded.assignments
    assert loaded.assignments[77].team1_player_ids == [1]

    loaded.reset(match_id=77, actor_discord_id=10)
    loaded.save()

    loaded2 = ArkTeamStateStore.load(path=p)
    assert loaded2.assignments[77].team1_player_ids == []
    assert loaded2.assignments[77].team2_player_ids == []
