# kvk_history_view.py
from __future__ import annotations

import asyncio
import io
from typing import Any

import discord
from discord import ButtonStyle
import matplotlib

matplotlib.use("Agg")
import pandas as pd

from embed_kvk_history import make_history_embed
from kvk_history_utils import (
    DEFAULT_LEFT,
    DEFAULT_RIGHT,
    LEFT_METRICS,
    RIGHT_METRICS,
    build_dual_axis_chart,
    build_history_csv,
    build_history_table_image,
    fetch_history_for_governors,
)

# Prefer the project's offload primitives where available for better isolation.
try:
    from file_utils import (
        run_blocking_in_thread,
        run_maintenance_with_isolation,
        start_callable_offload,
    )
except Exception:
    start_callable_offload = None
    run_maintenance_with_isolation = None
    run_blocking_in_thread = None

MAX_OVERLAY = 3


async def _offload_callable(
    fn, *args, name: str | None = None, meta: dict | None = None, **kwargs
) -> Any:
    """
    Offload a blocking callable using the project's helpers when available.

    Preference order:
      1) run_blocking_in_thread (lightweight thread runner)
      2) start_callable_offload (process offload wrapper)
      3) run_maintenance_with_isolation (maintenance isolation)
      4) asyncio.to_thread (fallback)

    This returns whatever the underlying runner returns; callers should extract
    the correct result for their expected type.
    """
    # 1) thread runner if present
    if run_blocking_in_thread is not None:
        try:
            return await run_blocking_in_thread(
                fn, *args, name=name or getattr(fn, "__name__", None), meta=meta
            )
        except Exception:
            # Fall through to next option
            pass

    # 2) start_callable_offload (prefer process isolation) - best-effort
    if start_callable_offload is not None:
        try:
            return await start_callable_offload(
                fn,
                *args,
                name=name or getattr(fn, "__name__", None),
                prefer_process=True,
                meta=meta,
            )
        except Exception:
            pass

    # 3) run_maintenance_with_isolation (best-effort)
    if run_maintenance_with_isolation is not None:
        try:
            return await run_maintenance_with_isolation(
                fn,
                *args,
                name=name or getattr(fn, "__name__", None),
                prefer_process=True,
                meta=meta,
            )
        except Exception:
            pass

    # 4) fallback: asyncio.to_thread
    return await asyncio.to_thread(fn, *args, **kwargs)


def _extract_dataframe(maybe: Any) -> pd.DataFrame:
    """
    Given `maybe` which may be a DataFrame, or a wrapper tuple containing a DataFrame
    (e.g., (df, meta)), attempt to return a DataFrame instance.
    Fallback: if not found, attempt to coerce the first element into a DataFrame.
    """
    if isinstance(maybe, pd.DataFrame):
        return maybe
    if isinstance(maybe, tuple) or isinstance(maybe, list):
        for item in maybe:
            if isinstance(item, pd.DataFrame):
                return item
            # duck-type: has .empty and .columns
            if hasattr(item, "empty") and hasattr(item, "columns"):
                return item
        # fallback: try to coerce first element
        first = maybe[0] if maybe else pd.DataFrame()
        if isinstance(first, pd.DataFrame):
            return first
    # Last resort: return an empty frame
    return pd.DataFrame()


def _extract_bytesio(maybe: Any) -> io.BytesIO:
    """
    Extract a BytesIO-like object from an offload result wrapper.
    """
    if isinstance(maybe, io.BytesIO):
        return maybe
    if isinstance(maybe, (bytes, bytearray)):
        return io.BytesIO(maybe)
    if isinstance(maybe, tuple) or isinstance(maybe, list):
        for item in maybe:
            if isinstance(item, io.BytesIO):
                return item
            if hasattr(item, "getvalue"):
                return item
            if isinstance(item, (bytes, bytearray)):
                return io.BytesIO(item)
        # fallback: coerce first
        first = maybe[0] if maybe else None
        if isinstance(first, io.BytesIO):
            return first
        if isinstance(first, (bytes, bytearray)):
            return io.BytesIO(first)
    # fallback empty buffer
    return io.BytesIO(b"")


def _extract_table_tuple(maybe: Any) -> tuple[str, io.BytesIO]:
    """
    Extract expected (filename, BytesIO) tuple from offload result.
    If not found, return a sensible default.
    """
    if isinstance(maybe, tuple) and len(maybe) >= 2 and isinstance(maybe[0], str):
        # Accept (name, buffer, ...) forms
        buf = maybe[1]
        if not isinstance(buf, io.BytesIO):
            buf = _extract_bytesio(buf)
        return (maybe[0], buf)
    if isinstance(maybe, list) and len(maybe) >= 2 and isinstance(maybe[0], str):
        return (maybe[0], _extract_bytesio(maybe[1]))
    # If it's a wrapped tuple containing a tuple, search for a (str, buffer)
    if isinstance(maybe, (tuple, list)):
        for item in maybe:
            if isinstance(item, (tuple, list)) and len(item) >= 2 and isinstance(item[0], str):
                return (item[0], _extract_bytesio(item[1]))
    # fallback
    return ("kvk_table.png", io.BytesIO(b""))


class KVKHistoryView(discord.ui.View):
    def __init__(
        self,
        user: discord.User | discord.Member,
        account_map: dict[str, dict],  # label -> {GovernorID, GovernorName}
        selected_ids: list[str],
        allow_all: bool = True,
        ephemeral: bool = False,
    ):
        super().__init__(timeout=300)
        self.user = user
        self.account_map = account_map
        self.allow_all = allow_all
        self.ephemeral = ephemeral

        # State
        self.selected_ids = self._pick_default_selected(selected_ids)
        self.left_metrics: list[str] = DEFAULT_LEFT[:]  # display names
        self.right_metric: str | None = DEFAULT_RIGHT  # display name
        self.table_cols: int = 3  # default Data range
        self._chart_image: tuple[str, bytes] | None = None  # (filename, raw bytes)

        # Will hold the last message to edit in-place
        self._msg: discord.Message | None = None

        # Lock to serialize redraws so concurrent interactions cannot corrupt view state
        self._redraw_lock: asyncio.Lock = asyncio.Lock()

        # Build initial controls
        self.add_item(self._make_account_select())
        self._make_presets_row()  # adds buttons directly
        self.add_item(self._make_custom_button())
        self.add_item(self._make_export_csv_button())
        self._make_table_cols_row()  # adds range buttons directly

    # ---------- Data & rendering ----------

    def _build_chart_embed_only(
        self, df: pd.DataFrame, overlay_labels: dict[int, str]
    ) -> discord.Embed:
        """Rebuild just the chart embed (fields + image URL), no chart plotting."""
        highlights = []
        if not df.empty:
            graph_subset = df[df["Gov_ID"].isin(overlay_labels.keys())]
            for lm in self.left_metrics[:2] or []:
                lcol = LEFT_METRICS.get(lm)
                if lcol and lcol in graph_subset.columns:
                    avg_left = graph_subset[lcol].astype(float).dropna()
                    avg_left_val = int(float(avg_left.mean())) if not avg_left.empty else 0
                    highlights.append(f"Avg {lm}: `{avg_left_val:,}`")
            if self.right_metric:
                rcol = RIGHT_METRICS.get(self.right_metric)
                if rcol and rcol in graph_subset.columns:
                    avg_right = graph_subset[rcol].astype(float).dropna()
                    pct = float(avg_right.mean()) if not avg_right.empty else 0.0
                    highlights.append(f"Avg {self.right_metric}: `{pct:.1f}%`")

        emb_chart, _, _ = make_history_embed(
            user=self.user,
            overlay_labels=overlay_labels,
            left_metrics=self.left_metrics,
            right_metric=self.right_metric,
            table_preview_rows=[],
        )
        emb_chart.set_image(url="attachment://kvk_history.png")
        right_suffix = f" • Right axis: {self.right_metric}" if self.right_metric else ""
        try:
            emb_chart.title = f"KVK History{right_suffix}"
        except Exception:
            pass
        if highlights:
            emb_chart.add_field(name="Highlights", value="\n".join(highlights), inline=False)
        legend_palette = ["🔵", "🟠", "🟢"]
        if overlay_labels:
            legend_lines = []
            for idx, (gid, label) in enumerate(
                sorted(overlay_labels.items(), key=lambda x: x[0])[:3]
            ):
                emoji = legend_palette[idx] if idx < len(legend_palette) else "▪️"
                legend_lines.append(f"{emoji} {label}")
            emb_chart.add_field(name="Legend", value="\n".join(legend_lines), inline=True)
        axes_left = ", ".join(self.left_metrics[:2]) if self.left_metrics else "—"
        axes_right = f"{self.right_metric}" if self.right_metric else "—"
        emb_chart.add_field(
            name="Axes:", value=f"**Left:** {axes_left}\n**Right:** {axes_right}", inline=True
        )
        return emb_chart

    # ---------- UI builders ----------

    def _pick_default_selected(self, selected_ids: list[str]) -> list[int]:
        # If caller provided a single id, honor it
        if selected_ids:
            ids = [int(x) for x in selected_ids if x]
            if ids:
                return ids[:1]

        # Prefer label starting with 'Main'
        for label, meta in self.account_map.items():
            if str(label).lower().startswith("main"):
                try:
                    return [int(meta.get("GovernorID"))]
                except Exception:
                    pass

        # Fallback: first account in the mapping
        try:
            first_meta = next(iter(self.account_map.values()))
            return [int(first_meta.get("GovernorID"))]
        except Exception:
            return []

    def _make_account_select(self):
        # Which IDs should appear pre-selected?
        sel_selected = {str(i) for i in self.selected_ids}

        # Build options with defaults
        options: list[discord.SelectOption] = []
        if self.allow_all:
            options.append(
                discord.SelectOption(
                    label="All Accounts (pick up to 3)",
                    value="__ALL__",
                    description="Overlay view",
                    default=False,
                )
            )

        for label, meta in self.account_map.items():
            gov_id = str(meta.get("GovernorID"))
            gname = str(meta.get("GovernorName") or label)
            options.append(
                discord.SelectOption(
                    label=f"{label} • {gname}",
                    value=gov_id,
                    default=(gov_id in sel_selected),
                )
            )

        class AccountSelect(discord.ui.Select):
            view: KVKHistoryView

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.view.user.id:
                    await interaction.response.send_message(
                        "This control isn't for you.", ephemeral=True
                    )
                    return
                vals = list(self.values)
                # Expand __ALL__ to first 3 accounts
                if "__ALL__" in vals:
                    vals = []
                    for _label, meta in list(self.view.account_map.items())[:MAX_OVERLAY]:
                        vals.append(str(meta.get("GovernorID")))
                # Limit 3
                vals = vals[:MAX_OVERLAY]
                self.view.selected_ids = [int(v) for v in vals]
                await self.view._redraw(interaction)

        sel = AccountSelect(
            placeholder="Select accounts (max 3)",
            min_values=1,
            max_values=min(
                MAX_OVERLAY,
                (
                    len(self.account_map)
                    if not self.allow_all
                    else min(MAX_OVERLAY, len(self.account_map) + 1)
                ),
            ),
            options=options[:25],
            row=0,
        )
        return sel

    def _make_presets_row(self):
        is_kills = self.left_metrics == ["T4&T5 Kills"] and self.right_metric == "% of Kill target"
        is_deads = self.left_metrics == ["Deads"] and self.right_metric == "% of Dead_Target"
        is_dkp = self.left_metrics == ["DKP Score"] and self.right_metric == "% of DKP Target"

        btn_kills = discord.ui.Button(
            label="Kills vs %",
            style=ButtonStyle.primary if is_kills else ButtonStyle.secondary,
            row=1,
        )
        btn_deads = discord.ui.Button(
            label="Deads vs %",
            style=ButtonStyle.primary if is_deads else ButtonStyle.secondary,
            row=1,
        )
        btn_dkp = discord.ui.Button(
            label="DKP vs %", style=ButtonStyle.primary if is_dkp else ButtonStyle.secondary, row=1
        )

        async def on_kills(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message(
                    "This control isn't for you.", ephemeral=True
                )
                return
            self.left_metrics = ["T4&T5 Kills"]
            self.right_metric = "% of Kill target"
            await self._redraw(interaction)

        async def on_deads(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message(
                    "This control isn't for you.", ephemeral=True
                )
                return
            self.left_metrics = ["Deads"]
            self.right_metric = "% of Dead_Target"
            await self._redraw(interaction)

        async def on_dkp(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message(
                    "This control isn't for you.", ephemeral=True
                )
                return
            self.left_metrics = ["DKP Score"]
            self.right_metric = "% of DKP Target"
            await self._redraw(interaction)

        btn_kills.callback = on_kills
        btn_deads.callback = on_deads
        btn_dkp.callback = on_dkp

        self.add_item(btn_kills)
        self.add_item(btn_deads)
        self.add_item(btn_dkp)

    def _make_custom_button(self):
        btn = discord.ui.Button(label="Custom…", style=discord.ButtonStyle.success, row=1)

        async def on_custom(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message(
                    "This control isn't for you.", ephemeral=True
                )
                return
            view = CustomMetricView(self)
            await interaction.response.send_message("Choose metrics:", view=view, ephemeral=True)

        btn.callback = on_custom
        return btn

    def _make_export_csv_button(self):
        btn = discord.ui.Button(label="Export CSV", style=ButtonStyle.secondary, row=2, emoji="📄")

        async def on_export(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message(
                    "This control isn't for you.", ephemeral=True
                )
                return

            # Build current overlay labels (same logic as _build_payload)
            overlay_labels: dict[int, str] = {}
            for label, meta in self.account_map.items():
                gid = int(meta.get("GovernorID"))
                if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                    overlay_labels[gid] = str(meta.get("GovernorName") or label)

            # Offload CSV build to avoid blocking the event loop
            df_raw = await _offload_callable(
                fetch_history_for_governors, overlay_labels.keys(), name="fetch_history"
            )
            df = _extract_dataframe(df_raw)
            csv_raw = await _offload_callable(
                build_history_csv, df, "kvk_history.csv", name="build_csv"
            )
            csv_name, csv_buf = _extract_table_tuple(
                csv_raw
            )  # reuse table extractor for (name, buffer)
            await interaction.response.send_message(
                content="Here’s your CSV export.",
                file=discord.File(
                    fp=io.BytesIO(csv_buf.getvalue() if hasattr(csv_buf, "getvalue") else csv_buf),
                    filename=csv_name,
                ),
                ephemeral=True,
            )

        btn.callback = on_export
        return btn

    def _make_table_cols_row(self):
        def _mk(label: str, value: int, row: int = 2):
            style = ButtonStyle.primary if self.table_cols == value else ButtonStyle.secondary
            b = discord.ui.Button(label=label, style=style, row=row)

            async def _cb(interaction: discord.Interaction):
                if interaction.user.id != self.user.id:
                    await interaction.response.send_message(
                        "This control isn't for you.", ephemeral=True
                    )
                    return
                self.table_cols = value
                await self._redraw_table(interaction)

            b.callback = _cb
            return b

        self.add_item(_mk("Last 3", 3))
        self.add_item(_mk("Last 6", 6))
        self.add_item(_mk("Last 10", 10))

    # ---------- Lifecycle ----------
    async def initial_send(self, ctx):
        # Build payload off the event loop and send the initial message
        payload = await self._build_payload()
        self._msg = await ctx.followup.send(
            embeds=payload["embeds"],
            files=payload["files"],
            view=self,
            ephemeral=self.ephemeral,
        )

    async def _redraw(self, interaction: discord.Interaction):
        if not self._msg:
            if not interaction.response.is_done():
                await interaction.response.defer()
            return

        # Serialize redraws to avoid concurrent mutations of the view
        async with self._redraw_lock:
            payload = await self._build_payload()

            # --- REBUILD CONTROLS SO DEFAULTS UPDATE ---
            self.clear_items()
            self.add_item(self._make_account_select())
            self._make_presets_row()
            self.add_item(self._make_custom_button())
            self.add_item(self._make_export_csv_button())
            self._make_table_cols_row()
            # --------------------------------------------

            if not interaction.response.is_done():
                await interaction.response.defer()

            # Guard: message may have been cleared by timeout; avoid editing in that case
            if not self._msg:
                return

            try:
                await self._msg.edit(embeds=payload["embeds"], files=payload["files"], view=self)
            except Exception:
                # Swallow edit exceptions to avoid breaking user interaction flow
                pass

    async def _redraw_table(self, interaction: discord.Interaction):
        """Re-render ONLY the Data (table) embed and controls."""
        if not self._msg:
            if not interaction.response.is_done():
                await interaction.response.defer()
            return

        async with self._redraw_lock:
            table_payload = await self._build_table_only()

            # Rebuild controls so the selected range button highlights correctly
            self.clear_items()
            self.add_item(self._make_account_select())
            self._make_presets_row()
            self.add_item(self._make_custom_button())
            self.add_item(self._make_export_csv_button())
            self._make_table_cols_row()

            # Prepare overlay map and df (same selection)
            overlay_labels: dict[int, str] = {}
            for label, meta in self.account_map.items():
                gid = int(meta.get("GovernorID"))
                if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                    overlay_labels[gid] = str(meta.get("GovernorName") or label)

            df_raw = await _offload_callable(
                fetch_history_for_governors, overlay_labels.keys(), name="fetch_history"
            )
            df = _extract_dataframe(df_raw)
            if not df.empty and "KVK_NO" in df.columns:
                df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")
            chart_embed = self._build_chart_embed_only(df, overlay_labels)
            new_embeds = [chart_embed, table_payload["embed_table"]]

            if not interaction.response.is_done():
                await interaction.response.defer()

            files = []
            if self._chart_image:
                fname, raw = self._chart_image
                files.append(discord.File(fp=io.BytesIO(raw), filename=fname))
            files.append(table_payload["file"])

            if not self._msg:
                return

            try:
                await self._msg.edit(embeds=new_embeds, files=files, view=self)
            except Exception:
                pass

    # ---------- Data & rendering ----------

    async def _build_payload(self) -> dict:
        # Prepare overlay labels
        overlay_labels: dict[int, str] = {}
        for label, meta in self.account_map.items():
            gid = int(meta.get("GovernorID"))
            if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                overlay_labels[gid] = str(meta.get("GovernorName") or label)

        # Offload DB query to preserve responsiveness
        df_raw = await _offload_callable(
            fetch_history_for_governors, overlay_labels.keys(), name="fetch_history"
        )
        df = _extract_dataframe(df_raw)
        # Ensure KVK_NO is numeric for ordering/filters
        if not df.empty and "KVK_NO" in df.columns:
            df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")

        # Chart (offloaded)
        buf_raw = await _offload_callable(
            build_dual_axis_chart,
            df,
            overlay_labels,
            self.left_metrics,
            self.right_metric,
            "KVK History",
            "all",
            name="build_chart",
        )
        buf = _extract_bytesio(buf_raw)
        chart_bytes = buf.getvalue()
        self._chart_image = ("kvk_history.png", chart_bytes)
        chart_file = discord.File(fp=io.BytesIO(chart_bytes), filename="kvk_history.png")

        # Highlights
        highlights = []
        if not df.empty:
            graph_subset = df[df["Gov_ID"].isin(overlay_labels.keys())]
            for lm in self.left_metrics[:2] or []:
                lcol = LEFT_METRICS.get(lm)
                if lcol and lcol in graph_subset.columns:
                    avg_left = graph_subset[lcol].astype(float).dropna()
                    avg_left_val = int(float(avg_left.mean())) if not avg_left.empty else 0
                    highlights.append(f"Avg {lm}: `{avg_left_val:,}`")
            if self.right_metric:
                rcol = RIGHT_METRICS.get(self.right_metric)
                if rcol and rcol in graph_subset.columns:
                    avg_right = graph_subset[rcol].astype(float).dropna()
                    pct = float(avg_right.mean()) if not avg_right.empty else 0.0
                    highlights.append(f"Avg {self.right_metric}: `{pct:.1f}%`")

        # Chart embed (uses embed_kvk_history)
        emb_chart, _, _ = make_history_embed(
            user=self.user,
            overlay_labels=overlay_labels,
            left_metrics=self.left_metrics,
            right_metric=self.right_metric,
            table_preview_rows=[],
        )
        emb_chart.set_image(url="attachment://kvk_history.png")

        right_suffix = f" • Right axis: {self.right_metric}" if self.right_metric else ""
        try:
            emb_chart.title = f"KVK History{right_suffix}"
        except Exception:
            pass

        if highlights:
            emb_chart.add_field(name="Highlights", value="\n".join(highlights), inline=False)

        legend_palette = ["🔵", "🟠", "🟢"]
        if overlay_labels:
            legend_lines = []
            for idx, (gid, label) in enumerate(
                sorted(overlay_labels.items(), key=lambda x: x[0])[:3]
            ):
                emoji = legend_palette[idx] if idx < len(legend_palette) else "▪️"
                legend_lines.append(f"{emoji} {label}")
            emb_chart.add_field(name="Legend", value="\n".join(legend_lines), inline=True)

        axes_left = ", ".join(self.left_metrics[:2]) if self.left_metrics else "—"
        axes_right = f"{self.right_metric}" if self.right_metric else "—"
        emb_chart.add_field(
            name="Axes:", value=f"**Left:** {axes_left}\n**Right:** {axes_right}", inline=True
        )

        # Table image + embed (offloaded)
        table_raw = await _offload_callable(
            build_history_table_image,
            df,
            overlay_labels,
            self.left_metrics,
            self.right_metric,
            self.table_cols,
            f"Data • Last {self.table_cols} KVKs",
            name="build_table",
        )
        table_name, table_buf = _extract_table_tuple(table_raw)
        table_file = discord.File(fp=table_buf, filename=table_name)
        emb_table = discord.Embed(
            color=emb_chart.color, title=f"Data • Last {self.table_cols} KVKs"
        )
        emb_table.set_image(url=f"attachment://{table_name}")

        return {
            "embeds": [emb_chart, emb_table],
            "files": [chart_file, table_file],
        }

    async def _build_table_only(self) -> dict:
        """Build just the table embed & file for fast updates."""
        overlay_labels: dict[int, str] = {}
        for label, meta in self.account_map.items():
            gid = int(meta.get("GovernorID"))
            if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                overlay_labels[gid] = str(meta.get("GovernorName") or label)

        df_raw = await _offload_callable(
            fetch_history_for_governors, overlay_labels.keys(), name="fetch_history"
        )
        df = _extract_dataframe(df_raw)
        if not df.empty and "KVK_NO" in df.columns:
            df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")

        table_raw = await _offload_callable(
            build_history_table_image,
            df,
            overlay_labels,
            self.left_metrics,
            self.right_metric,
            self.table_cols,
            f"Data • Last {self.table_cols} KVKs",
            name="build_table",
        )
        table_name, table_buf = _extract_table_tuple(table_raw)
        table_file = discord.File(fp=table_buf, filename=table_name)

        chart_color = None
        try:
            if self._msg and self._msg.embeds:
                chart_color = self._msg.embeds[0].color
        except Exception:
            chart_color = None

        emb_table = discord.Embed(title=f"Data • Last {self.table_cols} KVKs", color=chart_color)
        emb_table.set_image(url=f"attachment://{table_name}")
        return {"embed_table": emb_table, "file": table_file}

    async def on_timeout(self):
        # disable controls and update the view gracefully
        try:
            for item in self.children:
                item.disabled = True
            if self._msg:
                await self._msg.edit(view=self)
        except Exception:
            pass


# ---------- Custom metric selector (pop-up view) ----------


class CustomMetricView(discord.ui.View):
    def __init__(self, parent: KVKHistoryView):
        super().__init__(timeout=120)
        self.host = parent  # <— rename to avoid collisions

        class LeftMetricSelect(discord.ui.Select):
            view: CustomMetricView

            def __init__(self):
                left_opts = [discord.SelectOption(label=k) for k in LEFT_METRICS.keys()]
                super().__init__(
                    placeholder="Left-axis metrics (max 2)",
                    min_values=1,
                    max_values=2,
                    options=left_opts[:25],
                )

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.view.host.user.id:
                    await interaction.response.send_message(
                        "This control isn't for you.", ephemeral=True
                    )
                    return
                vals = list(self.values)[:2]
                self.view.host.left_metrics = vals
                await interaction.response.defer()

        class RightMetricSelect(discord.ui.Select):
            view: CustomMetricView

            def __init__(self):
                right_opts = [discord.SelectOption(label="none")] + [
                    discord.SelectOption(label=k) for k in RIGHT_METRICS.keys()
                ]
                super().__init__(
                    placeholder="Right-axis metric",
                    min_values=1,
                    max_values=1,
                    options=right_opts[:25],
                )

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.view.host.user.id:
                    await interaction.response.send_message(
                        "This control isn't for you.", ephemeral=True
                    )
                    return
                choice = (self.values[0] or "").strip().lower()
                self.view.host.right_metric = None if choice == "none" else self.values[0]
                await interaction.response.defer()

        self.add_item(LeftMetricSelect())
        self.add_item(RightMetricSelect())

        apply_btn = discord.ui.Button(label="Apply", style=discord.ButtonStyle.primary)

        async def on_apply(interaction: discord.Interaction):
            if interaction.user.id != self.host.user.id:
                await interaction.response.send_message(
                    "This control isn't for you.", ephemeral=True
                )
                return
            await interaction.response.edit_message(content="Updated metrics.", view=None)
            await self.host._redraw(interaction)

        apply_btn.callback = on_apply
        self.add_item(apply_btn)
