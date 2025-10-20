# crystaltech_ui.py
from __future__ import annotations

import os

import discord

from crystaltech_service import NextSteps

# --- formatting helpers ---


def _fmt_crystals(n: int) -> str:
    """Human readable crystal amounts: 1.7m / 900k / 950."""
    if n >= 1_000_000:
        whole = n // 1_000_000
        rem = n % 1_000_000
        if rem == 0:
            return f"{whole}m"
        val = n / 1_000_000
        return f"{val:.1f}m".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n // 1_000}k"  # thousands: no decimal
    return str(n)


def _path_label(service, path_id: str, locale: str = "en-GB") -> str:
    """Fetch the pretty display name for a path_id from config; fallback to path_id."""
    try:
        cfg = service.cfg()
        for p in cfg.get("paths", []):
            if p.get("path_id") == path_id:
                disp = p.get("display") or {}
                return disp.get(locale) or next(iter(disp.values()), path_id)
    except Exception:
        pass
    return path_id


def _with_default(options: list[discord.SelectOption], selected: str) -> list[discord.SelectOption]:
    """Clone options and mark the selected value as default=True so it renders picked."""
    return [
        discord.SelectOption(
            label=o.label,
            value=o.value,
            description=o.description,
            emoji=o.emoji,
            default=(o.value == selected),
        )
        for o in options
    ]


# ---------- Setup (first-time) ----------


class SetupView(discord.ui.View):
    def __init__(
        self,
        author_id: int,
        accounts: list[tuple[str, str]],
        timeout: int = 300,
        on_release: callable | None = None,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.selected_governor_id: str | None = None
        self.selected_path_id: str | None = None  # real path_id from config
        self.selected_troop: str | None = None  # derived from chosen path.troop_type
        self.accounts = accounts
        self._account_label = {gid: lbl for gid, lbl in accounts}
        self._on_release = on_release
        self._path_map: dict[str, dict] = {}  # path_id -> path dict from cfg

        # Account select (only show if multiple)
        if len(accounts) > 1:
            self.account_select = discord.ui.Select(
                placeholder="Choose account",
                min_values=1,
                max_values=1,
                options=[discord.SelectOption(label=lbl, value=gid) for gid, lbl in accounts],
            )
            self.account_select.callback = self._on_account
            self.add_item(self.account_select)
        else:
            # Auto-pick the only account
            self.selected_governor_id = accounts[0][0]

        # Single "Path" select — built directly from config
        from crystaltech_di import get_crystaltech_service  # late import avoids circulars

        service = get_crystaltech_service()
        cfg = service.cfg()
        paths = cfg.get("paths", [])
        self._path_map = {p.get("path_id"): p for p in paths if p.get("path_id")}

        def _disp(p: dict, locale: str = "en-GB") -> str:
            disp = p.get("display") or {}
            return disp.get(locale) or next(iter(disp.values()), p["path_id"])

        path_options = [
            discord.SelectOption(
                label=_disp(p),
                value=p["path_id"],
                description=(p.get("troop_type") or "").title() or None,
            )
            for p in paths
        ]
        self.path_select = discord.ui.Select(
            placeholder="Select investment path and primary troop type",
            min_values=1,
            max_values=1,
            options=path_options,
        )
        self.path_select.callback = self._on_path
        self.add_item(self.path_select)

        # Continue / Cancel
        self.next_btn = discord.ui.Button(
            label="Continue", style=discord.ButtonStyle.primary, disabled=True
        )
        self.next_btn.callback = self._on_continue
        self.add_item(self.next_btn)

        self.cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        self.cancel_btn.callback = self._on_cancel
        self.add_item(self.cancel_btn)

    def make_embed(self) -> discord.Embed:
        """Live summary of current selections."""
        troop_map = {
            "infantry": "Infantry",
            "cavalry": "Cavalry",
            "archer": "Archers",
            "siege": "Siege",
        }
        acc_txt = self._account_label.get(
            self.selected_governor_id,
            "—" if len(self.accounts) > 1 else self._account_label[self.accounts[0][0]],
        )
        # Resolve the nice path label via the service (or fall back to path_id)
        from crystaltech_di import get_crystaltech_service

        service = get_crystaltech_service()
        path_txt = _path_label(service, self.selected_path_id) if self.selected_path_id else "—"
        troop_txt = troop_map.get(self.selected_troop or "", "—")

        emb = discord.Embed(
            title="Crystal Tech — Setup",
            description="Pick your **investment path** and **primary troop** to begin.",
            color=discord.Color.blurple(),
        )
        emb.add_field(name="Account", value=acc_txt, inline=False)
        emb.add_field(name="Investment path", value=path_txt, inline=True)
        emb.add_field(name="Primary troop", value=troop_txt, inline=True)
        return emb

    async def _on_account(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("This isn’t your setup.", ephemeral=True)
        self.selected_governor_id = self.account_select.values[0]

        old_opts = [
            discord.SelectOption(label=o.label, value=o.value) for o in self.account_select.options
        ]
        self.remove_item(self.account_select)
        self.account_select = discord.ui.Select(
            placeholder="Choose account",
            min_values=1,
            max_values=1,
            options=_with_default(old_opts, self.selected_governor_id),
        )
        self.account_select.callback = self._on_account
        self.add_item(self.account_select)

        await interaction.response.edit_message(view=self, embed=self.make_embed())
        await self._update_next_state(interaction)

    async def _on_path(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("This isn’t your setup.", ephemeral=True)
        self.selected_path_id = self.path_select.values[0]
        # derive troop from config path (kept for progress stats/display)
        p = self._path_map.get(self.selected_path_id) or {}
        self.selected_troop = (p.get("troop_type") or "").lower() or None

        # Rebuild select to show default
        base_opts = [
            discord.SelectOption(label=o.label, value=o.value, description=o.description)
            for o in self.path_select.options
        ]
        self.remove_item(self.path_select)
        self.path_select = discord.ui.Select(
            placeholder="Choose exact investment path",
            min_values=1,
            max_values=1,
            options=_with_default(base_opts, self.selected_path_id),
        )
        self.path_select.callback = self._on_path
        self.add_item(self.path_select)

        await interaction.response.edit_message(view=self, embed=self.make_embed())
        await self._update_next_state(interaction)

    async def _on_continue(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("This isn’t your setup.", ephemeral=True)

        from crystaltech_di import get_crystaltech_service  # late import avoids circulars

        service = get_crystaltech_service()

        # Use the real config path_id; troop already derived
        path_id = self.selected_path_id

        # Persist/ensure the entry (and validate path_id). If invalid, show a friendly hint.
        try:
            service.ensure_user_entry(
                governor_id=self.selected_governor_id,
                selected_path_id=path_id,
                selected_troop_type=self.selected_troop,
            )
        except ValueError as ve:
            return await interaction.response.send_message(
                f"⚠️ {ve}\nPlease adjust your selection and try again.", ephemeral=True
            )

        # 1) Ack by disabling the setup view (no files on edit!)
        self.disable_all_items()
        try:
            await interaction.response.edit_message(
                content="Opening progress…", view=self, embed=None, attachments=[]
            )
        except Exception:
            # If we somehow already responded, just continue
            pass

        # 2) Send a **new** ephemeral message with the progress view + files
        view = ProgressView(
            author_id=self.author_id,
            governor_id=self.selected_governor_id,
            path_id=path_id,
            troop=self.selected_troop,
            timeout=300,
            on_release=self._on_release,  # <-- keep the session lock hook
        )
        try:
            embed, files = await view.render_embed()
        except ValueError as ve:
            # Surface config/validation hints gracefully
            return await interaction.followup.send(f"⚠️ {ve}", ephemeral=True)

        try:
            sent = await interaction.followup.send(
                embed=embed, files=files, ephemeral=True, view=view
            )
            view.message = sent
        except Exception:
            # Fallback: send without files if the client rejects attachments
            sent = await interaction.followup.send(embed=embed, ephemeral=True, view=view)
            view.message = sent

    async def _on_cancel(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("This isn’t your setup.", ephemeral=True)
        self.disable_all_items()
        await interaction.response.edit_message(content="Cancelled.", view=self)

    async def _update_next_state(self, interaction: discord.Interaction):
        ready = self.selected_governor_id and self.selected_path_id and self.selected_troop
        self.next_btn.disabled = not bool(ready)
        # If we already responded in the callback above, use edit only for the button state
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self, embed=self.make_embed())
        else:
            try:
                await interaction.edit_original_response(view=self)
            except Exception:
                pass

    def disable_all_items(self):
        for c in self.children:
            c.disabled = True

    # SetupView.on_timeout
    async def on_timeout(self):
        self.disable_all_items()
        try:
            if getattr(self, "message", None):
                await self.message.edit(
                    content="Session timed out. Run /my_kvkcrystaltech again.",
                    view=self,
                    embed=None,
                    attachments=[],
                )
        except Exception:
            pass
        if self._on_release:
            try:
                maybe_coro = self._on_release()
                if hasattr(maybe_coro, "__await__"):  # supports async callbacks
                    await maybe_coro
            except Exception:
                pass


# ---------- Progress (update & next two) ----------


class StepSelect(discord.ui.Select):
    def __init__(self, *, options: list[discord.SelectOption]):
        super().__init__(
            placeholder="Tick steps you've just completed",
            min_values=0,
            max_values=len(options) if options else 1,
            options=options,
            disabled=(len(options) == 0),
        )


class ProgressView(discord.ui.View):
    MAX_OPTIONS = 25  # Discord select max; we show the first 25 incomplete steps

    def __init__(
        self,
        author_id: int,
        governor_id: str,
        path_id: str,
        troop: str,
        timeout: int = 300,
        on_release: callable | None = None,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.governor_id = governor_id
        self.path_id = path_id
        self.troop = troop
        self._selected_to_save: list[str] = []
        self._on_release = on_release

        # Keep it simple: only Save + Reset
        self.save_btn = discord.ui.Button(label="Save Progress", style=discord.ButtonStyle.success)
        self.reset_btn = discord.ui.Button(label="Reset Account", style=discord.ButtonStyle.danger)

        self.save_btn.callback = self._on_save
        self.reset_btn.callback = self._on_reset

        self.add_item(self.save_btn)
        self.add_item(self.reset_btn)

    async def render_embed(self) -> tuple[discord.Embed, list[discord.File]]:
        from crystaltech_di import get_crystaltech_service

        service = get_crystaltech_service()
        # Compute next steps; let ValueError bubble to caller to show a friendly hint
        ns: NextSteps = service.compute_next_steps(self.path_id, self.governor_id)

        title = "Crystal Tech — Progress"
        last_step = service.get_last_completed(self.path_id, self.governor_id)
        path_pretty = _path_label(service, self.path_id)

        desc = (
            f"**Path:** {path_pretty} • **Troop:** `{self.troop}`\n"
            f"**Last completed:** "
            f"{(last_step.display_name() + f' (#{last_step.order})') if last_step else 'none yet'}\n"
            f"**Your progress:** {ns.user_progress_pct}% • **Kingdom avg:** {ns.path_avg_pct}%"
        )

        embed = discord.Embed(title=title, description=desc, color=discord.Color.blurple())

        if ns.next_two:
            labels = ["Next step", "Following step"]
            for i, step in enumerate(ns.next_two):
                embed.add_field(
                    name=f"{labels[i]}: {step.display_name()} → Lv {step.target_level}",
                    value=f"Cost: {_fmt_crystals(step.crystal_cost)} crystals",
                    inline=False,
                )
        else:
            embed.add_field(
                name="All done!", value="No remaining steps on this path 🎉", inline=False
            )

        # rebuild the select (first 25 incomplete steps)
        for child in list(self.children):
            if isinstance(child, discord.ui.Select):
                self.remove_item(child)

        incomplete = service.list_incomplete_steps(self.path_id, self.governor_id)
        chunk = incomplete[: self.MAX_OPTIONS]

        opts = [
            discord.SelectOption(
                label=f"{s.display_name()} → Lv{s.target_level}",
                value=s.step_uid,
                description=f"Cost {_fmt_crystals(s.crystal_cost)}",
            )
            for s in chunk
        ]

        if opts:
            self.step_select = StepSelect(options=opts)
            self.step_select.callback = self._on_select
            self.add_item(self.step_select)
            self.save_btn.disabled = False
        else:
            self.save_btn.disabled = True

        # footer note (always show the hint; it's how the flow works)
        note = f"Remaining steps: {ns.remaining_count} • Save your progress to view more steps"
        embed.set_footer(text=note)

        # small thumbnail for Next 1
        files: list[discord.File] = []
        if ns.next_two:
            img_path = os.path.join("assets", "crystaltech", ns.next_two[0].image)
            if os.path.isfile(img_path):
                f = discord.File(img_path, filename=ns.next_two[0].image)
                files.append(f)
                embed.set_thumbnail(url=f"attachment://{f.filename}")

        return embed, files

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "This isn’t your session.", ephemeral=True
            )
        self._selected_to_save = list(self.step_select.values)
        await interaction.response.defer()

    async def _on_save(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "This isn’t your session.", ephemeral=True
            )
        if not self._selected_to_save:
            return await interaction.response.send_message(
                "Select at least one step to save.", ephemeral=True
            )

        from crystaltech_di import get_crystaltech_service

        service = get_crystaltech_service()

        # Guard: if the account was reset after this panel opened, entry will be missing.
        current_entry = service.get_user_entry(self.governor_id)
        if current_entry is None:
            return await interaction.response.send_message(
                "This panel is no longer active (account was reset). Run `/my_kvkcrystaltech` to set up again.",
                ephemeral=True,
            )

        await service.save_progress(
            governor_id=self.governor_id,
            path_id=self.path_id,
            troop_type=self.troop,
            newly_completed_uids=self._selected_to_save,
        )
        self._selected_to_save = []

        # Ack + freeze old view (clear attachments to avoid stray large images)
        self.disable_all_items()
        try:
            await interaction.response.edit_message(
                content="✅ Progress saved. Opening updated panel…",
                view=self,
                embed=None,
                attachments=[],
            )
        except Exception:
            pass

        # Send a fresh panel
        new_view = ProgressView(
            self.author_id,
            self.governor_id,
            self.path_id,
            self.troop,
            timeout=300,
            on_release=self._on_release,
        )
        embed, files = await new_view.render_embed()
        sent = await interaction.followup.send(
            embed=embed, files=files, ephemeral=True, view=new_view
        )
        new_view.message = sent

        # Tidy the old one
        try:
            await self.message.delete()
        except Exception:
            pass

    async def _on_reset(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "This isn’t your session.", ephemeral=True
            )

        # Open a confirmation pop-out
        confirm_view = ResetConfirmView(
            author_id=self.author_id,
            governor_id=self.governor_id,
            parent_message=self.message,  # so we can delete it on confirm
            on_release=self._on_release,
        )
        embed = discord.Embed(
            title="Confirm reset?",
            description=(
                "This will **clear all saved progress** for this account.\n\n"
                "Are you sure you want to continue?"
            ),
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, view=confirm_view)

    def disable_all_items(self):
        for c in self.children:
            c.disabled = True

    # ProgressView.on_timeout
    async def on_timeout(self):
        self.disable_all_items()
        try:
            if getattr(self, "message", None):
                await self.message.edit(
                    content="Session timed out. Run /my_kvkcrystaltech again.",
                    view=self,
                    embed=None,
                    attachments=[],
                )
        except Exception:
            pass
        if self._on_release:
            try:
                maybe_coro = self._on_release()
                if hasattr(maybe_coro, "__await__"):
                    await maybe_coro
            except Exception:
                pass


class ResetConfirmView(discord.ui.View):
    def __init__(
        self,
        author_id: int,
        governor_id: str,
        parent_message: discord.Message | None,
        timeout: int = 60,
        on_release: callable | None = None,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.governor_id = governor_id
        self.parent_message = parent_message
        self._on_release = on_release  # for the session lock

    @discord.ui.button(label="Yes, reset", style=discord.ButtonStyle.danger)
    async def confirm_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "This isn’t your confirmation.", ephemeral=True
            )

        from crystaltech_di import get_crystaltech_service

        service = get_crystaltech_service()
        await service.reset_account_progress(self.governor_id)

        # 1) Immediately invalidate the old progress panel (remove all controls)
        try:
            if self.parent_message:
                await self.parent_message.edit(view=None)
        except Exception:
            pass

        # 2) (Optional) also try to delete the panel; if it fails for ephemeral, the view is already removed
        try:
            if self.parent_message:
                await self.parent_message.delete()
        except Exception:
            pass

        # 3) Acknowledge reset in this confirmation message
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Progress reset",
                description="Your progress has been cleared. Run `/my_kvkcrystaltech` to set up again.",
                color=discord.Color.green(),
            ),
            view=None,
        )

        # 4) Release the session lock
        if self._on_release:
            try:
                maybe_coro = self._on_release()
                if hasattr(maybe_coro, "__await__"):
                    await maybe_coro
            except Exception:
                pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "This isn’t your confirmation.", ephemeral=True
            )
        await interaction.response.edit_message(content="Reset cancelled.", embed=None, view=None)

    async def on_timeout(self):
        try:
            await self.message.edit(content="Reset prompt expired.", view=None)
        except Exception:
            pass
