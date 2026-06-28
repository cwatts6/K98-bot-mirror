import types

import pytest

# Use pytest-asyncio for async tests
pytest_plugins = ("pytest_asyncio",)


def test_build_stats_embed_formats_last_refresh_with_utc_time(monkeypatch):
    import io

    import embed_utils

    monkeypatch.setattr(embed_utils, "_load_last_kvk_for_governor", lambda _governor_id: None)
    monkeypatch.setattr(embed_utils, "generate_progress_dial", lambda *_a, **_k: io.BytesIO(b"png"))

    user = types.SimpleNamespace(mention="@Tester", display_avatar=None)
    embeds, _file = embed_utils.build_stats_embed(
        {
            "GovernorID": "123",
            "GovernorName": "Tester",
            "KVK_NO": 54,
            "KVK_RANK": 1,
            "Starting Power": 100_000_000,
            "T4&T5_Kills": 50_000_000,
            "Kill Target": 100_000_000,
            "LAST_REFRESH": "2026-06-03T07:53:12+00:00",
            "STATUS": "INCLUDED",
        },
        user,
    )

    last_updated = next(field.value for field in embeds[1].fields if "Last Updated" in field.name)
    assert "03 June 2026 07:53 UTC" in last_updated


@pytest.mark.asyncio
async def test_send_embed_safe_attaches_large_log(monkeypatch):
    """
    Validate that send_embed_safe will attach a file for a large 'Log' field
    and place a note in the embed field instead of the full content.
    """
    import embed_utils

    _sent = {}

    class FakeFile:
        def __init__(self, bio, filename):
            # capture content for assertions
            bio.seek(0)
            self.filename = filename
            self.content = bio.read()

    # Monkeypatch discord.File to our FakeFile so we can inspect it
    monkeypatch.setattr(embed_utils.discord, "File", FakeFile)

    # Fake destination with async send method
    class Dest:
        def __init__(self):
            self.called = False
            self.kw = None

        async def send(self, *args, **kwargs):
            self.called = True
            self.kw = kwargs
            # emulate returning a discord.Message-like object
            return types.SimpleNamespace(id=12345)

    dest = Dest()

    # Build a large log string
    large_log = "X" * (embed_utils._DEFAULT_MAX_LOG_EMBED_CHARS + 200)

    fields = {"Filename": "test.xlsx", "Log": large_log, "Context": "ctx"}
    # Call send_embed_safe
    ok = await embed_utils.send_embed_safe(dest, "Test Title", fields, color=0xFF0000)
    assert ok is True
    # Ensure send called
    assert dest.called is True
    # Files should be present and contain our log
    files = dest.kw.get("files") or []
    assert len(files) >= 1
    # find our attached file by filename containing 'Log' or fallback
    found = False
    for f in files:
        assert hasattr(f, "filename")
        if "Log" in f.filename or "log" in f.filename.lower():
            found = True
            # content length should be large
            assert len(f.content) >= len(large_log)
    assert found, "Expected attached file for Log field"

    # Embedded field 'Log' should contain a note, not the full log
    embed = dest.kw.get("embed")
    assert embed is not None
    # find the 'Log' field inside embed, confirm value is a note
    log_field_values = [fld.value for fld in embed.fields if fld.name.lower().startswith("log")]
    assert log_field_values, "Log field missing in embed"
    assert "attached as" in log_field_values[0] or "attached" in log_field_values[0]


@pytest.mark.asyncio
async def test_send_embed_safe_keeps_small_log_inline(monkeypatch):
    import embed_utils

    class Dest:
        def __init__(self):
            self.called = False
            self.kw = None

        async def send(self, *args, **kwargs):
            self.called = True
            self.kw = kwargs
            return types.SimpleNamespace(id=12345)

    dest = Dest()
    small_log = "short log"
    fields = {"Filename": "test.xlsx", "Log": small_log}
    ok = await embed_utils.send_embed_safe(dest, "Test Small Log", fields, color=0x00FF00)
    assert ok is True
    assert dest.called
    embed = dest.kw.get("embed")
    assert embed is not None
    log_field_values = [fld.value for fld in embed.fields if fld.name.lower().startswith("log")]
    assert log_field_values
    assert "short log" in log_field_values[0]
