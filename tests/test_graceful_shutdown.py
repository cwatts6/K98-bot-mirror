from __future__ import annotations

import importlib
import sys
import types


def _load_graceful_shutdown(monkeypatch, tmp_path, timeout_value: str | None):
    bot_config = types.ModuleType("bot_config")
    bot_config.DISCORD_BOT_TOKEN = "token"
    bot_config.NOTIFY_CHANNEL_ID = 1
    monkeypatch.setitem(sys.modules, "bot_config", bot_config)

    constants = types.ModuleType("constants")
    constants.EXIT_CODE_FILE = str(tmp_path / ".exit_code")
    constants.LAST_SHUTDOWN_INFO = str(tmp_path / "last_shutdown_info.json")
    constants.SHUTDOWN_LOG_PATH = str(tmp_path / "shutdown.log")
    constants.SHUTDOWN_MARKER_FILE = str(tmp_path / ".shutdown_marker")
    monkeypatch.setitem(sys.modules, "constants", constants)

    discord = types.ModuleType("discord")
    discord.Intents = types.SimpleNamespace(none=lambda: object())
    discord.Client = lambda intents=None: object()
    discord.Embed = object
    monkeypatch.setitem(sys.modules, "discord", discord)

    if timeout_value is None:
        monkeypatch.delenv("GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS", timeout_value)

    sys.modules.pop("graceful_shutdown", None)
    return importlib.import_module("graceful_shutdown")


def test_graceful_shutdown_timeout_env_defaults_when_missing(monkeypatch, tmp_path):
    module = _load_graceful_shutdown(monkeypatch, tmp_path, None)

    assert module.COOPERATIVE_SHUTDOWN_TIMEOUT_SECONDS == 15.0


def test_graceful_shutdown_timeout_env_falls_back_on_invalid_value(monkeypatch, tmp_path, capsys):
    module = _load_graceful_shutdown(monkeypatch, tmp_path, "abc")

    assert module.COOPERATIVE_SHUTDOWN_TIMEOUT_SECONDS == 15.0
    assert "Invalid GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS='abc'" in capsys.readouterr().out


def test_graceful_shutdown_timeout_env_accepts_positive_value(monkeypatch, tmp_path):
    module = _load_graceful_shutdown(monkeypatch, tmp_path, "22.5")

    assert module.COOPERATIVE_SHUTDOWN_TIMEOUT_SECONDS == 22.5
