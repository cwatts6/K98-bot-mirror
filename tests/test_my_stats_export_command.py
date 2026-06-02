"""
tests/test_my_stats_export_command.py

Focused tests for /my_stats_export command/service handoff.
"""

import types

import pytest

from services import stats_export_service


class DummyAuthor:
    id = 123
    display_name = "Tester"
    name = "Tester"


class DummyFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="msg")


class DummyCtx:
    def __init__(self):
        self.author = DummyAuthor()
        self.user = self.author
        self.followup = DummyFollowup()


def _get_stats_export_handler():
    import commands.stats_cmds as C

    fake_bot = types.SimpleNamespace(registered={})

    def slash_command(*, name=None, description=None, guild_ids=None):
        def decorator(fn):
            fake_bot.registered[name] = fn
            return fn

        return decorator

    fake_bot.slash_command = slash_command
    fake_bot.add_application_command = lambda _command: None
    C.register_stats(fake_bot)
    fn = fake_bot.registered["my_stats_export"]
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return C, fn


@pytest.mark.asyncio
async def test_my_stats_export_delegates_to_service(monkeypatch, tmp_path):
    C, handler = _get_stats_export_handler()
    export_path = tmp_path / "stats.csv"
    export_path.write_text("data", encoding="utf-8")
    export_file = stats_export_service.StatsExportFile(
        file_path=str(export_path),
        temp_dir=str(tmp_path),
        filename="stats.csv",
        format_name="CSV",
        format_emoji="CSV",
        description="desc",
        instructions="instructions",
        governor_ids=[123],
        row_count=1,
        days=30,
        telemetry={"event": "my_stats_export"},
    )
    called = {}

    async def fake_build_personal_stats_export(**kwargs):
        called.update(kwargs)
        return stats_export_service.StatsExportOutcome(status="ok", export_file=export_file)

    monkeypatch.setattr(C, "safe_defer", lambda ctx, ephemeral=True: C.asyncio.sleep(0))
    monkeypatch.setattr(
        C.stats_export_service,
        "build_personal_stats_export",
        fake_build_personal_stats_export,
    )
    monkeypatch.setattr(C.stats_export_service, "cleanup_export_file", lambda _export: None)

    ctx = DummyCtx()
    await handler(ctx, format="CSV", days=30)

    assert called["discord_user_id"] == 123
    assert called["requested_format"] == "CSV"
    assert ctx.followup.sent
    assert ctx.followup.sent[0]["kwargs"]["ephemeral"] is True


@pytest.mark.asyncio
async def test_my_stats_export_no_registered_accounts(monkeypatch):
    C, handler = _get_stats_export_handler()

    async def fake_build_personal_stats_export(**_kwargs):
        return stats_export_service.StatsExportOutcome(
            status="no_accounts",
            message="You have no registered accounts. Use `/register_governor` first.",
        )

    monkeypatch.setattr(C, "safe_defer", lambda ctx, ephemeral=True: C.asyncio.sleep(0))
    monkeypatch.setattr(
        C.stats_export_service,
        "build_personal_stats_export",
        fake_build_personal_stats_export,
    )

    ctx = DummyCtx()
    await handler(ctx, format="Excel", days=90)

    assert "no registered accounts" in ctx.followup.sent[0]["args"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
