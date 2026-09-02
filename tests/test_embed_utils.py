import types

import pytest

from core.discord_embed_limits import require_valid_embed_payload

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


@pytest.mark.asyncio
async def test_send_embed_safe_falls_back_for_invalid_log_limit():
    import embed_utils

    class Dest:
        async def send(self, **kwargs):
            self.kwargs = kwargs
            return types.SimpleNamespace(id=1)

    dest = Dest()

    assert await embed_utils.send_embed_safe(
        dest,
        "Invalid log limit",
        {"Status": "ok"},
        color=0x123456,
        max_log_embed_chars="not-an-integer",
    )
    require_valid_embed_payload(dest.kwargs["embed"])


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [0, 1])
async def test_send_embed_safe_enforces_exact_and_one_over_component_boundaries(extra):
    import embed_utils

    class Dest:
        async def send(self, **kwargs):
            self.kwargs = kwargs
            return types.SimpleNamespace(id=1)

    dest = Dest()
    title = "T" * (256 + extra)
    field_name = "N" * (256 + extra)
    field_value = "V" * (1024 + extra)

    assert await embed_utils.send_embed_safe(
        dest,
        title,
        {field_name: field_value},
        color=0x123456,
        mention="@ops",
        max_field_length=5000,
        total_cap=9000,
    )

    embed = dest.kwargs["embed"]
    require_valid_embed_payload(embed)
    assert len(embed.title) == 256
    assert len(embed.fields[0].name) == 256
    assert len(embed.fields[0].value) == 1024
    assert dest.kwargs["content"] == "@ops"
    if extra:
        assert embed.title.endswith("…")
        assert embed.fields[0].name.endswith("…")
        assert embed.fields[0].value.endswith("…")


@pytest.mark.asyncio
async def test_send_embed_safe_replaces_aggregate_overflow_without_duplicate_fields(monkeypatch):
    import embed_utils

    class FakeFile:
        def __init__(self, bio, filename):
            bio.seek(0)
            self.filename = filename
            self.content = bio.read()

    class Dest:
        async def send(self, **kwargs):
            self.kwargs = kwargs
            return types.SimpleNamespace(id=1)

    monkeypatch.setattr(embed_utils.discord, "File", FakeFile)
    fields = {f"Field {index}": chr(65 + index) * 1024 for index in range(7)}
    dest = Dest()

    assert await embed_utils.send_embed_safe(dest, "Aggregate", fields, color=0x123456)

    embed = dest.kwargs["embed"]
    usage = require_valid_embed_payload(embed)
    names = [field.name for field in embed.fields]
    assert len(embed.fields) == len(fields)
    assert len(names) == len(set(names))
    assert usage.total_characters <= 6000
    assert any(name.startswith("Attached field") for name in names)
    assert dest.kwargs.get("files")


@pytest.mark.asyncio
async def test_send_embed_safe_attaches_fields_over_field_count_limit(monkeypatch):
    import embed_utils

    class FakeFile:
        def __init__(self, bio, filename):
            bio.seek(0)
            self.filename = filename
            self.content = bio.read()

    class Dest:
        async def send(self, **kwargs):
            self.kwargs = kwargs
            return types.SimpleNamespace(id=1)

    monkeypatch.setattr(embed_utils.discord, "File", FakeFile)
    dest = Dest()
    fields = {f"Field {index}": f"Value {index}" for index in range(30)}

    assert await embed_utils.send_embed_safe(dest, "Many fields", fields, color=0x123456)

    embed = dest.kwargs["embed"]
    require_valid_embed_payload(embed)
    assert len(embed.fields) == 25
    assert embed.fields[-1].name == "Additional fields"
    assert "6 additional fields attached" in embed.fields[-1].value
    assert len(dest.kwargs["files"]) == 1


@pytest.mark.asyncio
async def test_send_embed_safe_never_exceeds_ten_attachments(monkeypatch):
    import embed_utils

    class FakeFile:
        def __init__(self, bio, filename):
            bio.seek(0)
            self.filename = filename
            self.content = bio.read()

    class Dest:
        async def send(self, **kwargs):
            self.kwargs = kwargs
            return types.SimpleNamespace(id=1)

    monkeypatch.setattr(embed_utils.discord, "File", FakeFile)
    dest = Dest()
    fields = {f"Log {index}": "X" * 2000 for index in range(25)}

    assert await embed_utils.send_embed_safe(
        dest,
        "Attachment cap",
        fields,
        color=0x123456,
        max_log_embed_chars=10,
    )

    require_valid_embed_payload(dest.kwargs["embed"])
    assert len(dest.kwargs["files"]) == 10
    assert any(field.value.endswith("…") for field in dest.kwargs["embed"].fields)


@pytest.mark.asyncio
async def test_send_embed_safe_compacts_with_marker_if_attachment_creation_fails(monkeypatch):
    import embed_utils

    class Dest:
        async def send(self, **kwargs):
            self.kwargs = kwargs
            return types.SimpleNamespace(id=1)

    def fail_file(*_args, **_kwargs):
        raise OSError("attachment unavailable")

    monkeypatch.setattr(embed_utils.discord, "File", fail_file)
    dest = Dest()
    fields = {f"Field {index}": "X" * 1024 for index in range(7)}

    assert await embed_utils.send_embed_safe(dest, "Aggregate", fields, color=0x123456)

    embed = dest.kwargs["embed"]
    require_valid_embed_payload(embed)
    assert any(field.value.endswith("…") for field in embed.fields)
    assert "files" not in dest.kwargs


@pytest.mark.asyncio
async def test_send_embed_safe_preserves_forbidden_fallback_behavior(monkeypatch):
    import embed_utils

    class FakeForbidden(Exception):
        pass

    class FailingDest:
        async def send(self, **_kwargs):
            raise FakeForbidden("forbidden")

    class Fallback:
        def __init__(self):
            self.calls = []

        async def send(self, **kwargs):
            self.calls.append(kwargs)

    monkeypatch.setattr(embed_utils.discord, "Forbidden", FakeForbidden)
    monkeypatch.setattr(embed_utils, "VIEW_PRUNE_ON_FORBIDDEN", False)
    fallback = Fallback()

    ok = await embed_utils.send_embed_safe(
        FailingDest(),
        "Fallback title",
        {"Status": "value"},
        color=0x123456,
        fallback_channel=fallback,
        bot=object(),
    )

    assert ok is False
    assert len(fallback.calls) == 1
    assert fallback.calls[0]["embed"].title == "Embed Delivery Failed (Forbidden)"
    assert fallback.calls[0]["embed"].description.endswith("Fallback title")


@pytest.mark.asyncio
async def test_send_embed_safe_bounds_fallback_description_for_long_title(monkeypatch):
    import embed_utils

    class FakeHTTPException(Exception):
        pass

    class FailingDest:
        async def send(self, **_kwargs):
            raise FakeHTTPException("rejected")

    class Fallback:
        async def send(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(embed_utils.discord, "HTTPException", FakeHTTPException)
    fallback = Fallback()

    ok = await embed_utils.send_embed_safe(
        FailingDest(),
        "T" * 5000,
        {"Status": "value"},
        color=0x123456,
        fallback_channel=fallback,
        bot=object(),
    )

    assert ok is False
    require_valid_embed_payload(fallback.kwargs["embed"])
    assert fallback.kwargs["embed"].description.endswith("…")


@pytest.mark.asyncio
async def test_history_and_failure_views_bound_dynamic_names_and_values():
    import embed_utils

    history = embed_utils.HistoryView(
        None,
        [
            {
                "Filename": "F" * 400,
                "Author": "A" * 400,
                "Timestamp": "T" * 400,
                "Channel": "C" * 400,
                "SavedPath": "P" * 2000,
            }
        ],
        1,
        1,
    ).get_embed()
    failures = embed_utils.FailuresView(
        None,
        [
            {
                "Filename": "F" * 400,
                "User": "U" * 400,
                "Timestamp": "T" * 400,
                "Rank": "R" * 400,
                "Seed": "S" * 400,
            }
        ],
        1,
        1,
    ).get_embed()

    require_valid_embed_payload(history)
    require_valid_embed_payload(failures)
    assert history.fields[0].name.endswith("…")
    assert history.fields[0].value.endswith("…")
    assert failures.fields[0].name.endswith("…")
    assert failures.fields[0].value.endswith("…")
