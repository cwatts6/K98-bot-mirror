"""Registry-domain UI views."""

from __future__ import annotations

from collections.abc import Callable
import logging

import discord
from discord import Embed

from governor_registry import ConfirmRemoveView, ModifyGovernorView, RegisterGovernorView
from utils import normalize_governor_id

logger = logging.getLogger(__name__)

# Configured by command module (callback injection; no command module import here)
_async_load_registry: Callable[[], object] = lambda: {}
_lookup_governor_id: Callable[[str], object] = lambda _name: {
    "status": "not_found",
    "message": "No results found.",
}
_target_lookup_view_factory: Callable[[list[dict], int], object] | None = None
_name_cache_getter: Callable[[], object] = lambda: {}
_send_profile_to_channel: Callable[[discord.Interaction, int, object], object] = (
    lambda *_a, **_k: None
)
_account_order_getter: Callable[[], list[str]] = lambda: ["Main"]


def configure_registry_views(
    *,
    async_load_registry: Callable[[], object],
    lookup_governor_id: Callable[[str], object],
    target_lookup_view_factory: Callable[[list[dict], int], object] | None,
    name_cache_getter: Callable[[], object],
    send_profile_to_channel: Callable[[discord.Interaction, int, object], object],
    account_order_getter: Callable[[], list[str]],
) -> None:
    global _async_load_registry, _lookup_governor_id, _target_lookup_view_factory
    global _name_cache_getter, _send_profile_to_channel, _account_order_getter
    _async_load_registry = async_load_registry
    _lookup_governor_id = lookup_governor_id
    _target_lookup_view_factory = target_lookup_view_factory
    _name_cache_getter = name_cache_getter
    _send_profile_to_channel = send_profile_to_channel
    _account_order_getter = account_order_getter


class MyRegsActionView(discord.ui.View):
    def __init__(self, *, author_id: int, has_regs: bool, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self._message: discord.Message | None = None

        if not has_regs:
            for child in self.children:
                try:
                    if (
                        isinstance(child, discord.ui.Button)
                        and child.label == "Modify Registration"
                    ):
                        child.disabled = True
                except Exception:
                    pass

    def set_message_ref(self, message: discord.Message):
        self._message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        try:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
        except Exception:
            pass
        return False

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        try:
            if self._message:
                await self._message.edit(view=self)
        except Exception:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[MyRegsActionView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass

    @discord.ui.button(label="Look up Governor ID", style=discord.ButtonStyle.primary, emoji="🔎")
    async def btn_lookup(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        try:
            await interaction.response.send_modal(GovNameModal(author_id=self.author_id))
        except Exception:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Use **/mygovernorid** and start typing your governor name to find your Governor ID.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Use **/mygovernorid** and start typing your governor name to find your Governor ID.",
                    ephemeral=True,
                )

    @discord.ui.button(label="Modify Registration", style=discord.ButtonStyle.secondary, emoji="🛠️")
    async def btn_modify(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
        try:
            registry = await _async_load_registry() or {}
            user_key_str = str(self.author_id)
            user_key_int = self.author_id
            accounts = (registry.get(user_key_str) or registry.get(user_key_int) or {}).get(
                "accounts", {}
            ) or {}
            if not accounts:
                await interaction.followup.send(
                    "You don’t have any accounts to modify. Use **Register New Account** instead.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Select which registered account you want to modify:",
                view=ModifyStartView(author_id=self.author_id, accounts=accounts),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("[MyRegsActionView] btn_modify failed")
            try:
                await interaction.followup.send(
                    f"⚠️ Failed to open modify flow: `{type(e).__name__}: {e}`", ephemeral=True
                )
            except Exception:
                pass

    @discord.ui.button(label="Register New Account", style=discord.ButtonStyle.success, emoji="➕")
    async def btn_register(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
        try:
            registry = await _async_load_registry() or {}
            user_key_str = str(self.author_id)
            user_key_int = self.author_id
            accounts = (registry.get(user_key_str) or registry.get(user_key_int) or {}).get(
                "accounts", {}
            ) or {}
            used_slots = set(accounts.keys())
            free_slots = [slot for slot in _account_order_getter() if slot not in used_slots]
            if not free_slots:
                await interaction.followup.send(
                    "All account slots are registered already. Use **Modify Registration** to change one.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Pick an account slot to register:",
                view=RegisterStartView(author_id=self.author_id, free_slots=free_slots),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("[MyRegsActionView] btn_register failed")
            try:
                await interaction.followup.send(
                    f"⚠️ Failed to open registration flow: `{type(e).__name__}: {e}`",
                    ephemeral=True,
                )
            except Exception:
                pass


class GovNameModal(discord.ui.Modal):
    def __init__(self, author_id: int):
        super().__init__(title="Look up Governor ID")
        self.author_id = author_id
        self.add_item(
            discord.ui.InputText(label="Governor Name", placeholder="Type your governor name")
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return

        governorname = (self.children[0].value or "").strip()
        if not governorname:
            await interaction.response.send_message("Please enter a governor name.", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            result = await _lookup_governor_id(governorname)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Lookup failed: `{type(e).__name__}: {e}`", ephemeral=True
            )
            return

        if result["status"] == "found":
            embed = Embed(
                title="🆔 Governor ID Lookup",
                description=(
                    f"**Governor Name:** {result['data']['GovernorName']}\n"
                    f"**Governor ID:** `{result['data']['GovernorID']}`"
                ),
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        elif result["status"] == "fuzzy_matches":
            embed = Embed(
                title="🔍 Governor Name Search Results",
                description="Pick a governor from the dropdown below.",
                color=discord.Color.blue(),
            )
            for entry in result["matches"]:
                embed.add_field(
                    name=entry["GovernorName"],
                    value=f"`Governor ID: {entry['GovernorID']}`",
                    inline=False,
                )
            view = (
                _target_lookup_view_factory(result["matches"], interaction.user.id)
                if _target_lookup_view_factory
                else None
            )
            if view:
                await view.send_followup(interaction, embed)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                result.get("message", "No results found."), ephemeral=True
            )


class ModifyStartView(discord.ui.View):
    def __init__(self, *, author_id: int, accounts: dict, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        options = []
        for slot in _account_order_getter():
            if slot in accounts:
                info = accounts.get(slot) or {}
                gid = str(info.get("GovernorID", "")).strip()
                gname = str(info.get("GovernorName", "")).strip()
                label = f"{slot} — {gname} ({gid})" if (gname or gid) else f"{slot}"
                options.append(discord.SelectOption(label=label[:100], value=slot))
        select = discord.ui.Select(
            placeholder="Choose an account to modify",
            options=options[:25],
            min_values=1,
            max_values=1,
        )

        async def on_select(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message(
                    "❌ This menu isn't for you.", ephemeral=True
                )
                return
            await interaction.response.send_modal(
                EnterGovernorIDModal(
                    author_id=self.author_id, mode="modify", account_type=select.values[0]
                )
            )

        select.callback = on_select
        self.add_item(select)

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[ModifyStartView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass


class RegisterStartView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        free_slots: list,
        timeout: float = 180,
        prefill_id: str | None = None,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.prefill_id = prefill_id
        options = [discord.SelectOption(label=slot, value=slot) for slot in free_slots[:25]]
        select = discord.ui.Select(
            placeholder="Choose a slot to register", options=options, min_values=1, max_values=1
        )

        async def on_select(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message(
                    "❌ This menu isn't for you.", ephemeral=True
                )
                return
            await interaction.response.send_modal(
                EnterGovernorIDModal(
                    author_id=self.author_id,
                    mode="register",
                    account_type=select.values[0],
                    prefill_id=self.prefill_id,
                )
            )

        select.callback = on_select
        self.add_item(select)

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[RegisterStartView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass


class EnterGovernorIDModal(discord.ui.Modal):
    def __init__(
        self, *, author_id: int, mode: str, account_type: str, prefill_id: str | None = None
    ):
        title = "Modify Registration" if mode == "modify" else "Register New Account"
        super().__init__(title=title)
        self.author_id = author_id
        self.mode = mode
        self.account_type = account_type
        placeholder = (
            "Enter new Governor ID, or type REMOVE"
            if mode == "modify"
            else "Enter Governor ID to register"
        )
        self.add_item(
            discord.ui.InputText(
                label="Governor ID", placeholder=placeholder, value=(prefill_id or "")
            )
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return

        governor_id = normalize_governor_id((self.children[0].value or "").strip())

        if (
            self.mode == "modify"
            and str((self.children[0].value or "").strip()).upper() == "REMOVE"
        ):
            view = ConfirmRemoveView(interaction.user, self.account_type)
            await interaction.response.send_message(
                f"⚠️ Are you sure you want to **remove** `{self.account_type}` from your registration?",
                view=view,
                ephemeral=True,
            )
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if not governor_id.isdigit():
            await interaction.followup.send(
                "❌ Please enter a **numeric** Governor ID (or type `REMOVE` to delete when modifying).",
                ephemeral=True,
            )
            return

        try:
            registry = await _async_load_registry() or {}
        except Exception as e:
            await interaction.followup.send(
                f"❌ Could not load registry: `{type(e).__name__}: {e}`", ephemeral=True
            )
            return

        name_cache = _name_cache_getter()
        all_rows = (name_cache or {}).get("rows", []) if isinstance(name_cache, dict) else []
        matched_row = next(
            (r for r in all_rows if str(r.get("GovernorID", "")).strip() == governor_id), None
        )
        if not matched_row:
            await interaction.followup.send(
                f"❌ Governor ID `{governor_id}` not found in the database. Try **Look up Governor ID** first.",
                ephemeral=True,
            )
            return

        for uid, data in registry.items():
            if self.mode == "modify" and str(uid) == str(self.author_id):
                continue
            for acc_type, details in (data.get("accounts") or {}).items():
                if str(details.get("GovernorID", "")).strip() == governor_id:
                    existing_user = data.get("discord_name", f"<@{uid}>")
                    await interaction.followup.send(
                        f"❌ This Governor ID `{governor_id}` is already registered to **{existing_user}** ({acc_type}).",
                        ephemeral=True,
                    )
                    return

        gov_name = matched_row.get("GovernorName", "Unknown")
        if self.mode == "modify":
            view = ModifyGovernorView(interaction.user, self.account_type, governor_id, gov_name)
            await interaction.followup.send(
                f"⚙️ Update `{self.account_type}` to **{gov_name}** (ID: `{governor_id}`)?",
                view=view,
                ephemeral=True,
            )
        else:
            view = RegisterGovernorView(interaction.user, self.account_type, governor_id, gov_name)
            await interaction.followup.send(
                f"⚙️ Register `{self.account_type}` as **{gov_name}** (ID: `{governor_id}`)?",
                view=view,
                ephemeral=True,
            )


class GovernorSelect(discord.ui.Select):
    def __init__(self, matches: list[tuple[str, int]], *, author_id: int | None = None):
        self.author_id = author_id
        options = [
            discord.SelectOption(label=name, description=str(gid), value=str(gid))
            for name, gid in matches[:25]
        ]
        super().__init__(
            placeholder="Multiple matches — pick one", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the requester can use this menu.", ephemeral=True
            )
            return

        gid = int(normalize_governor_id(self.values[0]))

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            await _send_profile_to_channel(interaction, gid, interaction.channel)
        except Exception as e:
            logger.exception("[GovernorSelect] send_profile_to_channel failed")
            try:
                await interaction.followup.send(
                    f"⚠️ Failed to send profile: `{type(e).__name__}: {e}`", ephemeral=True
                )
            except Exception:
                pass
            return

        text = f"Sent profile for **{self.values[0]}**."
        try:
            await interaction.followup.send(text, ephemeral=True)
        except Exception:
            try:
                await interaction.edit_original_response(content=text, view=None)
            except Exception:
                try:
                    await interaction.message.edit(content=text, view=None)
                except Exception:
                    pass


class GovernorSelectView(discord.ui.View):
    def __init__(
        self, matches: list[tuple[str, int]], *, author_id: int | None = None, timeout: int = 60
    ):
        super().__init__(timeout=timeout)
        self.add_item(GovernorSelect(matches, author_id=author_id))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[GovernorSelectView] handler error", exc_info=error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ Something went wrong. Please try again.", ephemeral=True
                )
        except Exception:
            pass


__all__ = [
    "EnterGovernorIDModal",
    "GovNameModal",
    "GovernorSelect",
    "GovernorSelectView",
    "ModifyStartView",
    "MyRegsActionView",
    "RegisterStartView",
    "configure_registry_views",
]
