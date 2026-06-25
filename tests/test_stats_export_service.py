from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from services import stats_export_service


def _daily_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "GovernorID": 123,
                "GovernorName": "Player",
                "Alliance": "K98",
                "AsOfDate": "2026-05-01",
                "Power": 100,
            }
        ]
    )


@pytest.mark.asyncio
async def test_build_personal_stats_export_no_registered_accounts(monkeypatch) -> None:
    async def fake_summary(_discord_user_id: int):
        return stats_export_service.governor_account_service.summarize_accounts({})

    monkeypatch.setattr(
        stats_export_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )

    outcome = await stats_export_service.build_personal_stats_export(
        discord_user_id=1,
        display_name="User",
        requested_format="Excel",
        days=90,
    )

    assert outcome.status == "no_accounts"
    assert outcome.export_file is None


@pytest.mark.asyncio
async def test_build_personal_stats_export_empty_data(monkeypatch) -> None:
    async def fake_summary(_discord_user_id: int):
        return stats_export_service.governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "Player"}}
        )

    async def fake_fetch_daily(_governor_ids: list[int]):
        return pd.DataFrame()

    monkeypatch.setattr(
        stats_export_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )
    monkeypatch.setattr(stats_export_service, "_fetch_daily", fake_fetch_daily)

    outcome = await stats_export_service.build_personal_stats_export(
        discord_user_id=1,
        display_name="User",
        requested_format="CSV",
        days=90,
    )

    assert outcome.status == "no_data"


@pytest.mark.asyncio
async def test_build_personal_stats_export_selects_csv_builder(monkeypatch, tmp_path) -> None:
    async def fake_summary(_discord_user_id: int):
        return stats_export_service.governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "Player"}}
        )

    async def fake_fetch_daily(_governor_ids: list[int]):
        return _daily_frame()

    def fake_mkdtemp():
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        return str(export_dir)

    def fake_csv_builder(_df_daily, _df_targets, *, out_path: str, days_for_daily_table: int):
        Path(out_path).write_text("csv", encoding="utf-8")
        assert days_for_daily_table == 30

    monkeypatch.setattr(
        stats_export_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )
    monkeypatch.setattr(stats_export_service, "_fetch_daily", fake_fetch_daily)
    monkeypatch.setattr(stats_export_service.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(stats_export_service, "build_user_stats_csv", fake_csv_builder)

    outcome = await stats_export_service.build_personal_stats_export(
        discord_user_id=1,
        display_name="Test User",
        requested_format="CSV",
        days=30,
    )

    assert outcome.status == "ok"
    assert outcome.export_file is not None
    assert outcome.export_file.filename.endswith(".csv")
    assert outcome.export_file.telemetry["format"] == "CSV"

    stats_export_service.cleanup_export_file(outcome.export_file)
    assert not Path(outcome.export_file.temp_dir).exists()


@pytest.mark.asyncio
async def test_build_personal_stats_export_cleans_partial_file_on_builder_failure(
    monkeypatch, tmp_path
) -> None:
    async def fake_summary(_discord_user_id: int):
        return stats_export_service.governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "Player"}}
        )

    async def fake_fetch_daily(_governor_ids: list[int]):
        return _daily_frame()

    def fake_mkdtemp():
        export_dir = tmp_path / "failed_export"
        export_dir.mkdir()
        return str(export_dir)

    def fake_csv_builder(_df_daily, _df_targets, *, out_path: str, days_for_daily_table: int):
        Path(out_path).write_text("partial", encoding="utf-8")
        raise RuntimeError("writer failed")

    monkeypatch.setattr(
        stats_export_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )
    monkeypatch.setattr(stats_export_service, "_fetch_daily", fake_fetch_daily)
    monkeypatch.setattr(stats_export_service.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(stats_export_service, "build_user_stats_csv", fake_csv_builder)

    with pytest.raises(RuntimeError, match="writer failed"):
        await stats_export_service.build_personal_stats_export(
            discord_user_id=1,
            display_name="Test User",
            requested_format="CSV",
            days=30,
        )

    assert not (tmp_path / "failed_export").exists()
