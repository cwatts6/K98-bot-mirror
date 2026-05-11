from __future__ import annotations

from kvk.dal import kvk_reporting_dal
from kvk.services import kvk_reporting_service
from stats_alerts import allkingdoms


def test_reporting_service_preserves_block_keys_and_adds_contribution_fields(monkeypatch) -> None:
    raw_blocks = {
        "players_by_kills": [
            {
                "name": "Alice",
                "kills_gain": 100,
                "kp_gain": 200,
                "deads": 3,
                "dkp": 42,
                "healed_troops": 50,
                "max_contribute_gain": 7,
                "cur_contribute_gain": 8,
            }
        ],
        "kingdoms_by_kills": [{"kingdom": 1198, "kills_gain": 1000}],
        "camps_by_kills": [{"camp_name": "Camp A", "kills_gain": 900}],
    }
    captured = {}

    def fake_fetch(kvk_no: int, our_kingdom: int):
        captured["args"] = (kvk_no, our_kingdom)
        return raw_blocks

    monkeypatch.setattr(
        kvk_reporting_service.kvk_reporting_dal,
        "fetch_allkingdom_reporting_rows",
        fake_fetch,
    )

    blocks = kvk_reporting_service.load_allkingdom_reporting_blocks(12, our_kingdom=1198)

    assert captured["args"] == (12, 1198)
    assert tuple(blocks) == kvk_reporting_service.REPORTING_BLOCK_KEYS
    assert blocks["players_by_kills"][0]["max_contribute_gain"] == 7
    assert blocks["players_by_kills"][0]["cur_contribute_gain"] == 8
    assert blocks["kingdoms_by_kills"][0]["max_contribute_gain"] == 0
    assert blocks["camps_by_kills"][0]["cur_contribute_gain"] == 0
    assert blocks["players_by_deads"] == []
    assert blocks["our_camp"] == []


def test_allkingdoms_wrapper_delegates_to_reporting_service(monkeypatch) -> None:
    expected = {"players_by_kills": [{"name": "Alice"}]}

    def fake_load(kvk_no: int):
        assert kvk_no == 99
        return expected

    monkeypatch.setattr(allkingdoms, "load_allkingdom_reporting_blocks", fake_load)

    assert allkingdoms.load_allkingdom_blocks(99) is expected


def test_allkingdoms_wrapper_delegates_to_service_layer() -> None:
    """Verify the wrapper delegates to the service and does not directly import DB helpers."""
    wrapper_module_attrs = set(vars(allkingdoms))
    dal_module_attrs = set(vars(kvk_reporting_dal))

    # Wrapper must not import DB-layer helpers (SQL belongs in the DAL, not the wrapper)
    assert (
        "get_conn_with_retries" not in wrapper_module_attrs
    ), "allkingdoms wrapper must not import get_conn_with_retries (SQL belongs in the DAL)"
    assert (
        "cursor_row_to_dict" not in wrapper_module_attrs
    ), "allkingdoms wrapper must not import cursor_row_to_dict (SQL belongs in the DAL)"

    # Wrapper must delegate to the service function
    assert (
        "load_allkingdom_reporting_blocks" in wrapper_module_attrs
    ), "allkingdoms wrapper must import load_allkingdom_reporting_blocks from the service"

    # DAL must own the DB helpers (confirms SQL lives in the DAL)
    assert (
        "get_conn_with_retries" in dal_module_attrs
    ), "get_conn_with_retries must be imported by the DAL module"
