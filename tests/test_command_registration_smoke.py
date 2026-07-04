import datetime
import os
from pathlib import Path
import sys
import types


def test_register_commands_smoke(monkeypatch):
    monkeypatch.setenv("OUR_KINGDOM", os.getenv("OUR_KINGDOM", "0") or "0")
    if not hasattr(datetime, "UTC"):
        datetime.UTC = datetime.UTC

    sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
    gspread_mod = types.ModuleType("gspread")
    gspread_exc = types.ModuleType("gspread.exceptions")
    gspread_exc.APIError = Exception
    gspread_exc.SpreadsheetNotFound = Exception
    sys.modules.setdefault("gspread", gspread_mod)
    sys.modules.setdefault("gspread.exceptions", gspread_exc)
    sqlalchemy_mod = types.ModuleType("sqlalchemy")
    sqlalchemy_mod.create_engine = lambda *args, **kwargs: None
    sys.modules.setdefault("sqlalchemy", sqlalchemy_mod)

    import Commands

    registered_top_level = []
    fake_bot = types.SimpleNamespace()
    fake_bot.tree = types.SimpleNamespace(command=lambda **kw: (lambda fn: fn))
    fake_bot.add_listener = lambda *args, **kwargs: None
    fake_bot.add_application_command = lambda command: registered_top_level.append(command.name)

    def slash_command(**kwargs):
        def deco(fn):
            registered_top_level.append(kwargs.get("name"))
            return fn

        return deco

    fake_bot.slash_command = slash_command

    Commands.register_commands(fake_bot)

    assert len([name for name in registered_top_level if name]) <= 100
    assert len([name for name in registered_top_level if name]) < 90
    assert "ark" in registered_top_level
    assert "activity" in registered_top_level
    assert "crystaltech" in registered_top_level
    assert "events" in registered_top_level
    assert "honor" in registered_top_level
    assert "inventory" in registered_top_level
    assert "kvk_admin" in registered_top_level
    assert "kvk" in registered_top_level
    assert "location" in registered_top_level
    assert "me" in registered_top_level
    assert "ops" in registered_top_level
    assert "mge" in registered_top_level
    assert "prekvk" in registered_top_level
    assert "registry" in registered_top_level
    assert "stats" in registered_top_level
    assert "subscriptions" in registered_top_level
    assert "ark_create_match" not in registered_top_level
    assert "ark_force_announce" not in registered_top_level
    assert "ark_amend_match" not in registered_top_level
    assert "ark_cancel_match" not in registered_top_level
    assert "ark_reminder_prefs" not in registered_top_level
    assert "ark_set_preference" not in registered_top_level
    assert "ark_clear_preference" not in registered_top_level
    assert "ark_ban_add" not in registered_top_level
    assert "ark_ban_revoke" not in registered_top_level
    assert "ark_ban_list" not in registered_top_level
    assert "ark_set_result" not in registered_top_level
    assert "ark_report_players" not in registered_top_level
    assert "ark_generate_draft" not in registered_top_level
    assert "create_ark_team" not in registered_top_level
    assert "run_sql_proc" not in registered_top_level
    assert "mge_refresh_award_reminders" not in registered_top_level
    assert "prekvk_report" not in registered_top_level
    assert "prekvk_import_history" not in registered_top_level
    assert "summary" not in registered_top_level
    assert "weeksummary" not in registered_top_level
    assert "history" not in registered_top_level
    assert "failures" not in registered_top_level
    assert "usage" not in registered_top_level
    assert "usage_detail" not in registered_top_level
    assert "test_embed" not in registered_top_level
    assert "remove_registration" not in registered_top_level
    assert "remove_registration_by_id" not in registered_top_level
    assert "admin_register_governor" not in registered_top_level
    assert "registration_audit" not in registered_top_level
    assert "bulk_export_registrations" not in registered_top_level
    assert "bulk_import_registrations_dryrun" not in registered_top_level
    assert "bulk_import_registrations" not in registered_top_level
    assert "test_kvk_export" not in registered_top_level
    assert "refresh_stats_cache" not in registered_top_level
    assert "player_stats" not in registered_top_level
    assert "kvk_export_all" not in registered_top_level
    assert "kvk_recompute" not in registered_top_level
    assert "kvk_list_scans" not in registered_top_level
    assert "test_kvk_embed" not in registered_top_level
    assert "kvk_window_preview" not in registered_top_level
    assert "import_inventory" not in registered_top_level
    assert "inventory_import_audit" not in registered_top_level
    assert "calendar_refresh" not in registered_top_level
    assert "calendar_generate" not in registered_top_level
    assert "calendar_publish_cache" not in registered_top_level
    assert "calendar_status" not in registered_top_level
    assert "refresh_events" not in registered_top_level
    assert "refresh_kvk_overview" not in registered_top_level
    assert "list_subscribers" not in registered_top_level
    assert "migrate_subscriptions_dryrun" not in registered_top_level
    assert "migrate_subscriptions_apply" not in registered_top_level
    assert "crystaltech_validate" not in registered_top_level
    assert "crystaltech_reload" not in registered_top_level
    assert "crystaltech_admin_reset" not in registered_top_level
    assert "honor_purge_last" not in registered_top_level
    assert "import_locations" not in registered_top_level
    assert "player_location" not in registered_top_level
    assert "activity_top" not in registered_top_level
    assert "calendar" in registered_top_level
    assert "honor_rankings" in registered_top_level
    assert "player_profile" in registered_top_level
    assert "ping" in registered_top_level


def test_startup_command_audit_uses_authoritative_inventory():
    source = Path("DL_bot.py").read_text(encoding="utf-8")

    assert "collect_static_primary_inventory" in source
    assert "commands package (authoritative)" in source
    assert "grouped_subcommands_detected" in source
    assert "_collect_declared_command_names_safely" in source
    assert "Failed parsing %s" in source
    assert "Commands.py (authoritative)" not in source
    assert "_collect_declared_slash_commands" not in source
