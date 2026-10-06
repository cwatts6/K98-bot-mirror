from ark.team_balancer import auto_balance_team_ids


def _row(gid, name):
    return {
        "GovernorId": gid,
        "GovernorNameSnapshot": name,
        "Status": "Active",
        "SlotType": "Player",
    }


def test_auto_balance_even():
    rows = [_row(i, f"P{i}") for i in range(1, 11)]
    t1, t2 = auto_balance_team_ids(rows)
    assert len(t1) == 5
    assert len(t2) == 5
    assert set(t1).isdisjoint(set(t2))


def test_auto_balance_odd():
    rows = [_row(i, f"P{i}") for i in range(1, 10)]
    t1, t2 = auto_balance_team_ids(rows)
    assert len(t1) == 4
    assert len(t2) == 5
    assert set(t1).isdisjoint(set(t2))


def test_auto_balance_stable():
    rows = [_row(3, "C"), _row(1, "A"), _row(2, "B")]
    t1a, t2a = auto_balance_team_ids(rows)
    t1b, t2b = auto_balance_team_ids(rows)
    assert (t1a, t2a) == (t1b, t2b)
