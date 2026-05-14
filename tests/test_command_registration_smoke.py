import datetime
import os
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

    fake_bot = types.SimpleNamespace()
    fake_bot.tree = types.SimpleNamespace(command=lambda **kw: (lambda fn: fn))
    fake_bot.add_listener = lambda *args, **kwargs: None

    def slash_command(**kwargs):
        def deco(fn):
            return fn

        return deco

    fake_bot.slash_command = slash_command

    Commands.register_commands(fake_bot)
