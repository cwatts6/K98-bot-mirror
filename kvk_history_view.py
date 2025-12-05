# kvk_history_view.py
from __future__ import annotations

import io

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

MAX_OVERLAY = 3


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

        # Build initial controls
        self.add_item(self._make_account_select())
        self._make_presets_row()  # adds buttons directly
        self.add_item(self._make_custom_button())
        self.add_item(self._make_export_csv_button())
        self._make_table_cols_row()  # adds range buttons directly

    # ---------- Data & rendering ----------

    def _build_chart_embed_only(self, df, overlay_labels) -> discord.Embed:
        """Rebuild just the chart embed (fields + image URL), no chart plotting."""
        # Highlights over all graph data
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
                    default=(gov_id in sel_selected),  # <- pre-select our default
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
        # Determine which preset (if any) matches the current selection
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

        # Add to the view
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
            # Show a temporary modal-like selection via followup selects
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

            df = fetch_history_for_governors(overlay_labels.keys())
            csv_name, csv_bytes = build_history_csv(df, filename="kvk_history.csv")
            await interaction.response.send_message(
                content="Here’s your CSV export.",
                file=discord.File(fp=io.BytesIO(csv_bytes), filename=csv_name),
                ephemeral=True,
            )

        btn.callback = on_export
        return btn

    def _make_table_cols_row(self):
        # Helper to create a button with selected style
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
                await self._redraw_table(interaction)  # only update table embed + controls

            b.callback = _cb
            return b

        self.add_item(_mk("Last 3", 3))
        self.add_item(_mk("Last 6", 6))
        self.add_item(_mk("Last 10", 10))

    # ---------- Lifecycle ----------
    async def initial_send(self, ctx):
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

        await self._msg.edit(embeds=payload["embeds"], files=payload["files"], view=self)

    async def _redraw_table(self, interaction: discord.Interaction):
        """Re-render ONLY the Data (table) embed and controls."""
        if not self._msg:
            if not interaction.response.is_done():
                await interaction.response.defer()
            return
        # Build fresh table (chart unchanged)
        table_payload = await self._build_table_only()

        # Rebuild controls so the selected range button highlights correctly
        self.clear_items()
        self.add_item(self._make_account_select())
        self._make_presets_row()
        self.add_item(self._make_custom_button())
        self.add_item(self._make_export_csv_button())
        self._make_table_cols_row()

        # Rebuild the chart embed so its image points to attachment://kvk_history.png
        # Prepare overlay map and df (same selection)
        overlay_labels: dict[int, str] = {}
        for label, meta in self.account_map.items():
            gid = int(meta.get("GovernorID"))
            if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                overlay_labels[gid] = str(meta.get("GovernorName") or label)
        df = fetch_history_for_governors(overlay_labels.keys())
        if not df.empty and "KVK_NO" in df.columns:
            df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")
        chart_embed = self._build_chart_embed_only(df, overlay_labels)
        new_embeds = [chart_embed, table_payload["embed_table"]]

        if not interaction.response.is_done():
            await interaction.response.defer()
        # Replace attachments cleanly: re-upload cached chart + new table (no attachments=)
        files = []
        if self._chart_image:
            fname, raw = self._chart_image
            files.append(discord.File(fp=io.BytesIO(raw), filename=fname))
        files.append(table_payload["file"])
        await self._msg.edit(embeds=new_embeds, files=files, view=self)

    # ---------- Data & rendering ----------

    async def _build_payload(self) -> dict:
        # Prepare data
        overlay_labels: dict[int, str] = {}
        for label, meta in self.account_map.items():
            gid = int(meta.get("GovernorID"))
            if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                overlay_labels[gid] = str(meta.get("GovernorName") or label)

        df = fetch_history_for_governors(overlay_labels.keys())
        # Ensure KVK_NO is numeric for ordering/filters
        if not df.empty and "KVK_NO" in df.columns:
            df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")

        # Chart
        buf = build_dual_axis_chart(
            df=df,
            overlay=overlay_labels,
            left_metrics=self.left_metrics,
            right_metric=self.right_metric,
            title="KVK History",
            show_point_labels="all",  # "none" | "latest" | "all"
        )
        # cache chart bytes so we can reattach it during table-only edits
        chart_bytes = buf.getvalue()
        self._chart_image = ("kvk_history.png", chart_bytes)
        chart_file = discord.File(fp=io.BytesIO(chart_bytes), filename="kvk_history.png")

        # Highlights (averages over *all data shown on the graph*)
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

        # Chart embed
        emb_chart, _, _ = make_history_embed(
            user=self.user,
            overlay_labels=overlay_labels,
            left_metrics=self.left_metrics,
            right_metric=self.right_metric,
            table_preview_rows=[],
        )
        emb_chart.set_image(url="attachment://kvk_history.png")

        # --- Right-axis clarity in title ---
        right_suffix = f" • Right axis: {self.right_metric}" if self.right_metric else ""
        try:
            emb_chart.title = f"KVK History{right_suffix}"
        except Exception:
            pass

        # Field order: Highlights → Legend → Axes
        if highlights:
            emb_chart.add_field(name="Highlights", value="\n".join(highlights), inline=False)

        # --- Legend chips (match overlay order, emoji-coded) ---
        # We use a stable emoji palette for up to 3 overlays.
        legend_palette = ["🔵", "🟠", "🟢"]
        if overlay_labels:
            legend_lines = []
            for idx, (gid, label) in enumerate(
                sorted(overlay_labels.items(), key=lambda x: x[0])[:3]
            ):
                emoji = legend_palette[idx] if idx < len(legend_palette) else "▪️"
                legend_lines.append(f"{emoji} {label}")
            emb_chart.add_field(name="Legend", value="\n".join(legend_lines), inline=True)

        # Axes field last
        axes_left = ", ".join(self.left_metrics[:2]) if self.left_metrics else "—"
        axes_right = f"{self.right_metric}" if self.right_metric else "—"
        emb_chart.add_field(
            name="Axes:", value=f"**Left:** {axes_left}\n**Right:** {axes_right}", inline=True
        )

        # Table image + embed (toggle: last 3/6/10 KVKs)
        table_name, table_buf = build_history_table_image(
            df=df,
            overlay=overlay_labels,
            left_metrics=self.left_metrics,
            right_metric=self.right_metric,
            cols=self.table_cols,
            title=f"Data • Last {self.table_cols} KVKs",
        )
        table_file = discord.File(fp=table_buf, filename=table_name)
        emb_table = discord.Embed(
            color=emb_chart.color, title=f"Data • Last {self.table_cols} KVKs"
        )
        emb_table.set_image(url=f"attachment://{table_name}")

        return {
            "embeds": [emb_chart, emb_table],  # <- two stacked embeds
            "files": [chart_file, table_file],  # <- both images
        }

    async def _build_table_only(self) -> dict:
        """Build just the table embed & file for fast updates."""
        # Prepare overlay map (reuse current selection)
        overlay_labels: dict[int, str] = {}
        for label, meta in self.account_map.items():
            gid = int(meta.get("GovernorID"))
            if gid in self.selected_ids and len(overlay_labels) < MAX_OVERLAY:
                overlay_labels[gid] = str(meta.get("GovernorName") or label)

        df = fetch_history_for_governors(overlay_labels.keys())
        if not df.empty and "KVK_NO" in df.columns:
            df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")

        table_name, table_buf = build_history_table_image(
            df=df,
            overlay=overlay_labels,
            left_metrics=self.left_metrics,
            right_metric=self.right_metric,
            cols=self.table_cols,
            title=f"Data • Last {self.table_cols} KVKs",
        )
        table_file = discord.File(fp=table_buf, filename=table_name)
        # Match the chart embed color for a cohesive look
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
                # Add an explicit "none" so users can remove the right axis
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
