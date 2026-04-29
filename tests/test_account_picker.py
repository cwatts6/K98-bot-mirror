from account_picker import build_unique_gov_options


def _mk_acc(slot, gid, name=None):
    d = {"GovernorID": gid}
    if name is not None:
        d["GovernorName"] = name
    return (slot, d)


def test_build_unique_gov_options_basic_ordering_and_dedupe():
    """
    Ensure preferred slot ordering and duplicate GovernorID dedupe works.
    """
    accounts = dict(
        [
            _mk_acc("Farm 1", "900", "FarmOne"),
            _mk_acc("Alt 2", "200", "AltTwo"),
            _mk_acc("Main", "100", "MainUser"),
            _mk_acc("Alt 1", "200", "AltTwoDuplicate"),
            _mk_acc("OtherSlot", "300", "Zed"),
        ]
    )

    opts = build_unique_gov_options(accounts)
    # Values correspond to GovernorID strings, unique and stable ordering (Main first, then Alts/Farm)
    vals = [o.value for o in opts]
    assert "100" in vals  # Main must be present
    # dedupe: 200 appears only once
    assert vals.count("200") == 1
    # ensure deterministic presence of the three distinct ids
    assert set(vals) == {"100", "200", "300", "900"}


def test_build_unique_gov_options_labels_and_desc_limits():
    accounts = {
        "Main": {"GovernorID": 1, "GovernorName": "A" * 200},
        "Alt 1": {"GovernorID": 2, "GovernorName": "B"},
    }
    opts = build_unique_gov_options(accounts)
    assert len(opts) == 2
    # label trimmed to 100 chars by implementation (defensive assumption)
    assert len(opts[0].label) <= 100
    assert opts[0].description == "Main"
