# governor_registry.py
import json
import os

import discord

from constants import REGISTRY_FILE
from embed_utils import build_stats_embed
from utils import load_stat_row, normalize_governor_id


def load_registry():
    data = {}
    try:
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            data = json.load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        # log and return empty
        pass

    # Migrate/normalize stored GovernorIDs in-place for uniformity
    changed = False
    for user_id, block in data.items():
        accounts = block.get("accounts", {}) or {}
        for slot, details in accounts.items():
            gid = details.get("GovernorID") or details.get("governor_id")
            if gid:
                norm = normalize_governor_id(gid)
                if norm and norm != str(gid):
                    details["GovernorID"] = norm
                    changed = True

    if changed:
        try:
            save_registry(data)
        except Exception:
            pass

    return data


def save_registry(data):
    # Ensure folder exists and write atomically
    os.makedirs(os.path.dirname(REGISTRY_FILE) or ".", exist_ok=True)
    tmp = f"{REGISTRY_FILE}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, REGISTRY_FILE)


def _is_claimed_by_other(registry: dict, governor_id: str, owner_discord_id: str) -> bool:
    gid = str(governor_id).strip()
    for did, payload in (registry or {}).items():
        if did == owner_discord_id:
            continue
        for _label, acct in (payload.get("accounts") or {}).items():
            if str(acct.get("GovernorID", "")).strip() == gid:
                return True
    return False


def register_account(
    discord_id: str, discord_name: str, account_type: str, governor_id: str, governor_name: str
) -> tuple[bool, str | None]:
    # Normalize governor_id before any checks/storage
    normalized_gid = normalize_governor_id(governor_id)
    if not normalized_gid:
        return False, "Invalid Governor ID provided."

    data = load_registry()

    if discord_id not in data:
        data[discord_id] = {"discord_name": discord_name, "accounts": {}}

    # Prevent duplicate GovernorID claimed by another user (normalize check)
    if _is_claimed_by_other(data, normalized_gid, discord_id):
        return False, "This Governor ID is already registered to another Discord user."

    data[discord_id]["accounts"][account_type] = {
        "GovernorID": normalized_gid,
        "GovernorName": governor_name,
    }

    save_registry(data)
    return True, None


def get_discord_name_for_governor(governor_id: str) -> str | None:
    """Return the registered Discord name for this GovernorID, or None if not found."""
    data = load_registry()  # uses REGISTRY_FILE underneath
    gid = str(governor_id).strip()
    for _discord_user_id, payload in (data or {}).items():
        accounts = (payload or {}).get("accounts", {})
        for _label, acct in (accounts or {}).items():
            if str(acct.get("GovernorID", "")).strip() == gid:
                # payload has the display name we want to show on the card
                name = (payload.get("discord_name") or "").strip()
                return name or None
    return None


class RegisterGovernorView(discord.ui.View):
    def __init__(self, user, account_type, governor_id, governor_name):
        super().__init__(timeout=60)
        self.user = user
        self.account_type = account_type
        self.governor_id = governor_id
        self.governor_name = governor_name

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your registration to confirm!", ephemeral=True
            )
            return

        ok, err = register_account(
            discord_id=str(self.user.id),
            discord_name=str(self.user),
            account_type=self.account_type,
            governor_id=self.governor_id,
            governor_name=self.governor_name,
        )

        if not ok:
            await interaction.response.edit_message(
                content=f"❌ Registration failed: {err or 'Unknown error.'}", view=None
            )
            return
        else:
            await interaction.response.edit_message(
                content=f"✅ Registered `{self.account_type}` as **{self.governor_name}** (ID: `{self.governor_id}`)",
                view=None,
            )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.edit_message(content="❌ Registration cancelled.", view=None)


class ModifyGovernorView(discord.ui.View):
    def __init__(self, user, account_type, new_gov_id, new_gov_name):
        super().__init__(timeout=60)
        self.user = user
        self.account_type = account_type
        self.new_gov_id = new_gov_id
        self.new_gov_name = new_gov_name

    @discord.ui.button(label="✅ Confirm Change", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your registration to change!", ephemeral=True
            )
            return

        ok, err = register_account(
            discord_id=str(self.user.id),
            discord_name=str(self.user),
            account_type=self.account_type,
            governor_id=self.new_gov_id,
            governor_name=self.new_gov_name,
        )

        if not ok:
            await interaction.response.edit_message(
                content=f"❌ Update failed: {err or 'Unknown error.'}", view=None
            )
            return
        else:
            await interaction.response.edit_message(
                content=f"✅ `{self.account_type}` updated to **{self.new_gov_name}** (ID: `{self.new_gov_id}`)",
                view=None,
            )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.edit_message(content="❌ Modification cancelled.", view=None)


class KVKStatsView(discord.ui.View):
    def __init__(
        self, user: discord.User, accounts: dict, *, ephemeral: bool = False, timeout: float = 120
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.author_id = user.id
        self.accounts = accounts
        self.ephemeral = ephemeral

        # Stable ordering: Main, Alt N, Farm N, then alphabetical fallbacks
        def _sort_key(item):
            label, _info = item
            label_lc = label.lower().strip()
            if label_lc == "main":
                return (0, 0, label_lc)
            if label_lc.startswith("alt"):
                try:
                    n = int("".join(ch for ch in label_lc if ch.isdigit()) or 0)
                except Exception:
                    n = 0
                return (1, n, label_lc)
            if label_lc.startswith("farm"):
                try:
                    n = int("".join(ch for ch in label_lc if ch.isdigit()) or 0)
                except Exception:
                    n = 0
                return (2, n, label_lc)
            return (3, 0, label_lc)

        ordered = sorted(accounts.items(), key=_sort_key)
        # Add buttons (5 per row max, Discord hard limit 25 total)
        for idx, (label, info) in enumerate(ordered[:25]):
            gov_id = str(info.get("GovernorID", "")).strip()
            if not gov_id:
                # Skip entries with no GovernorID to avoid a broken button
                continue
            btn = KVKAccountButton(
                label=label, governor_id=gov_id, author_id=self.author_id, ephemeral=self.ephemeral
            )
            try:
                btn.row = min(idx // 5, 4)
            except Exception:
                pass
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message(
                    "❌ This selector isn’t for you.", ephemeral=True
                )
            except Exception:
                pass
            return False
        return True

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        # If you keep a handle to the message elsewhere, you can edit the view to show disabled state.


class KVKAccountButton(discord.ui.Button):
    def __init__(self, *, label: str, governor_id: str, author_id: int, ephemeral: bool):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self._label = label  # store separately to avoid shadowing .label internals
        self.governor_id = str(governor_id)
        self.author_id = author_id
        self.ephemeral = ephemeral

    async def callback(self, interaction: discord.Interaction):
        # Double guard (view.interaction_check runs too)
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This selector isn’t for you.", ephemeral=True
            )
            return

        # Acknowledge quickly; ephemeral/public as requested
        try:
            await interaction.response.defer(ephemeral=self.ephemeral)
        except Exception:
            pass

        # Load single governor row (fast, mtime-guarded)
        gov_data = load_stat_row(self.governor_id)
        if not gov_data:
            await interaction.followup.send(
                "❌ Stats not found for that Governor ID.", ephemeral=True
            )
            return

        # Build and send
        try:
            result = build_stats_embed(gov_data, interaction.user)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to build stats: `{type(e).__name__}: {e}`", ephemeral=True
            )
            return

        # New long-term return shape: ([Embed,...], File|None)
        # But tolerate older single-embed returns for backwards compatibility.
        embeds = None
        file = None
        try:
            if isinstance(result, tuple) and isinstance(result[0], list):
                embeds, file = result
            elif isinstance(result, list):
                # returned a list only (unlikely) -> treat as embeds; no file
                embeds, file = result, None
            else:
                # older shape: (embed, file) or embed alone
                try:
                    possible_embed, possible_file = result
                    # if we got here and possible_embed is an Embed, convert to single-item list
                    if isinstance(possible_embed, discord.Embed):
                        embeds, file = [possible_embed], possible_file
                    else:
                        # fallback: wrap whatever was returned
                        embeds, file = [possible_embed], possible_file
                except Exception:
                    # single embed returned directly
                    if isinstance(result, discord.Embed):
                        embeds, file = [result], None
                    else:
                        # last-resort wrap
                        embeds, file = [result], None
        except Exception:
            embeds, file = [result], None

        # Send combined embeds (with file when present)
        try:
            if file is not None:
                await interaction.followup.send(
                    content=f"📊 Showing stats for `{self._label}`:",
                    embeds=embeds,
                    files=[file],
                    ephemeral=self.ephemeral,
                )
            else:
                await interaction.followup.send(
                    content=f"📊 Showing stats for `{self._label}`:",
                    embeds=embeds,
                    ephemeral=self.ephemeral,
                )
        except Exception as e:
            logger = globals().get("logger")
            if logger:
                logger.exception("[KVKAccountButton] failed to send embeds: %s", e)
            try:
                # fallback single-embed send if something about multi-embed failed
                if embeds and isinstance(embeds, list) and embeds:
                    await interaction.followup.send(
                        content=f"📊 Showing stats for `{self._label}`:",
                        embed=embeds[0],
                        file=file,
                        ephemeral=self.ephemeral,
                    )
            except Exception:
                pass


class ConfirmRemoveView(discord.ui.View):
    def __init__(self, user, account_type):
        super().__init__(timeout=60)
        self.user = user
        self.account_type = account_type

    @discord.ui.button(label="✅ Confirm Remove", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You cannot modify someone else's registration.", ephemeral=True
            )
            return

        registry = load_registry()
        user_id = str(interaction.user.id)
        accounts = registry.get(user_id, {}).get("accounts", {})
        if self.account_type not in accounts:
            await interaction.response.send_message(
                "❌ That account type is no longer registered.", ephemeral=True
            )
            return

        del accounts[self.account_type]
        # If user has no accounts left, prune the user node to keep registry small
        try:
            if not accounts:
                # rebuild the user block without empty 'accounts'
                registry.pop(user_id, None)
        except Exception:
            pass

        save_registry(registry)

        await interaction.response.send_message(
            f"✅ `{self.account_type}` has been removed from your registered accounts.",
            ephemeral=True,
        )
        self.stop()


def get_user_main_governor_id(registry: dict, user_id: str | int) -> str | None:
    rec = registry.get(str(user_id)) or registry.get(user_id)
    if not rec:
        return None
    main = (rec.get("accounts") or {}).get("Main")
    gid = (main or {}).get("GovernorID")
    return str(gid) if gid else None


def get_user_main_governor_name(registry: dict, user_id: str | int) -> str | None:
    rec = registry.get(str(user_id)) or registry.get(user_id)
    if not rec:
        return None
    main = (rec.get("accounts") or {}).get("Main")
    name = (main or {}).get("GovernorName")
    return str(name) if name else None
