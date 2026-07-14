from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import StringIO

from player_self_service import accounts_export
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
)


def test_accounts_csv_has_locked_columns_exact_values_unicode_and_formula_protection() -> None:
    now = datetime(2026, 7, 14, 8, 30, tzinfo=UTC)
    row = AccountPortfolioRow(
        slot="Main",
        role="Main",
        registered_name='=HYPERLINK("bad")',
        current_governor_name="Gövérnor 東京",
        governor_id=123456789,
        civilisation="Rome",
        city_hall=25,
        power=1_234_567_890,
        troop_power=987_654_321,
        kill_points=111,
        t4_kills=22,
        t5_kills=33,
        t4_t5_kills=55,
        deads=44,
        healed_troops=66,
        highest_acclaim=77,
        helps=88,
        rss_gathered=99,
        rss_assistance=100,
        rss_total=101,
        conduct=98.5,
        location_x=123,
        location_y=456,
        data_state="CURRENT",
        last_governor_scan=now,
        inventory_as_of=now,
    )
    metric = AccountMetricTotal(1, 1, 1)
    payload = AccountsPortfolioPayload(
        discord_user_id=42,
        state="READY",
        rows=(row,),
        linked_count=1,
        main_row=row,
        role_counts=(("Main", 1), ("Alt", 0), ("Farm", 0)),
        power=metric,
        troop_power=metric,
        t4_t5_kills=metric,
        rss_total=metric,
        insight="Current.",
        refreshed_at_utc=now,
    )

    export = accounts_export.build_accounts_csv(payload)
    decoded = export.data.decode("utf-8-sig")
    rows = list(csv.reader(StringIO(decoded)))

    assert tuple(rows[0]) == accounts_export.CSV_COLUMNS
    assert len(rows[1]) == len(accounts_export.CSV_COLUMNS)
    assert rows[1][2].startswith("'=")
    assert rows[1][3] == "Gövérnor 東京"
    assert rows[1][7] == "1234567890"
    assert rows[1][12] == "55"
    assert rows[1][16] == "88"
    assert rows[1][21:23] == ["123", "456"]
    assert export.filename == "me_account_summary_42_20260714_083000.csv"
