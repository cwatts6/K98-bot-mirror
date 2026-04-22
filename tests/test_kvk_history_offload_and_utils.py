import asyncio
import io

import pandas as pd
import pytest

import kvk_history_utils as khu
import kvk_history_view as khv


def test_builders_do_not_mutate_and_csv_defensive(tmp_path):
    # Prepare a DataFrame with minimal columns
    df = pd.DataFrame(
        [
            {"Gov_ID": 1, "Governor_Name": "A", "KVK_NO": 10, "T4_KILLS": 5},
            {"Gov_ID": 1, "Governor_Name": "A", "KVK_NO": 11, "T4_KILLS": 8},
        ]
    )
    df_copy = df.copy(deep=True)

    # Call build_dual_axis_chart — should not mutate caller df
    buf = khu.build_dual_axis_chart(
        df=df,
        overlay={1: "A"},
        left_metrics=["T4 Kills"],
        right_metric=None,
        title="t",
        show_point_labels="none",
    )
    assert isinstance(buf, io.BytesIO)
    # original DataFrame should be unchanged
    pd.testing.assert_frame_equal(df, df_copy)

    # Call build_history_table_image — should not mutate caller df
    name, table_buf = khu.build_history_table_image(
        df=df, overlay={1: "A"}, left_metrics=["T4 Kills"], right_metric=None, cols=2, title="t"
    )
    assert isinstance(name, str)
    assert hasattr(table_buf, "read")

    # Defensive CSV: empty df should return header-only CSV
    empty = pd.DataFrame()
    fname, csv_bytes = khu.build_history_csv(empty, "out.csv")
    assert fname == "out.csv"
    assert isinstance(csv_bytes, (bytes, bytearray))
    csv_text = csv_bytes.decode("utf-8")
    # header should include the primary column names
    assert "Gov_ID" in csv_text
    assert "KVK_NO" in csv_text


@pytest.mark.asyncio
async def test_kvk_view_uses_offload_runner_and_has_lock(monkeypatch):
    # Record calls to run_blocking_in_thread
    calls = []

    async def fake_runner(fn, *args, **kwargs):
        # record the function object identity and allow execution
        calls.append((getattr(fn, "__name__", str(fn)), args, kwargs))
        # Call the function synchronously for test speed
        return fn(*args, **kwargs)

    # Monkeypatch the module-level run_blocking_in_thread used by kvk_history_view
    monkeypatch.setattr(khv, "run_blocking_in_thread", fake_runner)

    # Monkeypatch heavy functions to be lightweight and fast
    def fake_fetch(ids):
        # return empty dataframe
        return pd.DataFrame(columns=["Gov_ID", "KVK_NO"])

    def fake_chart(df, overlay, left_metrics, right_metric, title, show_point_labels):
        return io.BytesIO(b"img")

    def fake_table(df, overlay, left_metrics, right_metric, cols, title):
        return ("kvk_table.png", io.BytesIO(b"table"))

    # Simple stub embed maker (lightweight)
    class SimpleEmbed:
        def __init__(self):
            self.fields = []
            self.color = None
            self.title = "stub"

        def set_image(self, url=None):
            self._img = url

        def add_field(self, name, value, inline=True):
            self.fields.append((name, value, inline))

    def fake_make_history_embed(
        user, overlay_labels, left_metrics, right_metric, table_preview_rows
    ):
        return SimpleEmbed(), None, None

    monkeypatch.setattr(khv, "fetch_history_for_governors", fake_fetch)
    monkeypatch.setattr(khv, "build_dual_axis_chart", fake_chart)
    monkeypatch.setattr(khv, "build_history_table_image", fake_table)
    monkeypatch.setattr(khv, "make_history_embed", fake_make_history_embed)

    # Simplified discord.File used by the view — avoid importing real discord.File
    class DummyFile:
        def __init__(self, fp=None, filename=None):
            self.fp = fp
            self.filename = filename

    monkeypatch.setattr(khv, "discord", khv.discord)  # keep existing module, but override File
    monkeypatch.setattr(khv.discord, "File", DummyFile)

    # Build view with minimal inputs
    user = type("U", (), {"display_name": "u", "display_avatar": None})()
    account_map = {"Main": {"GovernorID": 123, "GovernorName": "Me"}}
    view = khv.KVKHistoryView(
        user=user, account_map=account_map, selected_ids=["123"], allow_all=True, ephemeral=True
    )

    # Ensure the redraw lock exists and is an asyncio.Lock
    assert hasattr(view, "_redraw_lock")
    assert isinstance(view._redraw_lock, asyncio.Lock)

    # Calling _build_payload should call the module-level run_blocking_in_thread (our fake_runner)
    payload = await view._build_payload()

    # Validate recorded calls include the three heavy-call targets (fetch, chart, table)
    called_names = [c[0] for c in calls]
    assert any("fetch" in n for n in called_names)
    assert any("chart" in n for n in called_names) or any(
        "build_dual_axis_chart" in n for n in called_names
    )
    assert any("table" in n for n in called_names) or any(
        "build_history_table_image" in n for n in called_names
    )

    # payload structure
    assert "embeds" in payload and "files" in payload
