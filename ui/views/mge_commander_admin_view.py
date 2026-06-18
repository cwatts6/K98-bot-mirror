from __future__ import annotations

import asyncio
from typing import Any

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_interaction
from mge import mge_commander_service


def _to_bool(value: str) -> bool | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "yes", "y", "1", "active"}:
        return True
    if normalized in {"false", "no", "n", "0", "inactive"}:
        return False
    return None


def _row_active(row: dict[str, Any]) -> bool:
    return bool(row.get("CommanderIsActive")) and bool(row.get("VariantCommanderIsActive"))


class _CommanderEditModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        parent: MgeCommanderAdminView,
        commander_id: int | None,
        current_name: str,
        current_active: bool,
    ) -> None:
        super().__init__(title="MGE Commander", timeout=300)
        self.parent_view = parent
        self.commander_id = commander_id
        self.name = discord.ui.InputText(
            label="Commander name",
            value=current_name,
            required=True,
            max_length=100,
        )
        self.active = discord.ui.InputText(
            label="Active? yes/no",
            value="yes" if current_active else "no",
            required=True,
            max_length=8,
        )
        self.variant = discord.ui.InputText(
            label="Linked variant id",
            value=str(parent.variant_id or ""),
            required=True,
            max_length=8,
        )
        self.add_item(self.name)
        self.add_item(self.active)
        self.add_item(self.variant)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view._guard(interaction):
            return
        active = _to_bool(str(self.active.value))
        if active is None:
            await send_ephemeral(interaction, "Active must be yes or no.")
            return
        try:
            variant_id = int(str(self.variant.value).strip())
        except Exception:
            await send_ephemeral(interaction, "Variant id must be numeric.")
            return

        result = await asyncio.to_thread(
            mge_commander_service.save_commander_assignment,
            commander_id=self.commander_id,
            commander_name=str(self.name.value or ""),
            variant_id=variant_id,
            is_active=active,
        )
        prefix = "OK: " if result.success else "Error: "
        await send_ephemeral(interaction, prefix + result.message)


class _VariantSelect(discord.ui.Select):
    def __init__(self, *, variants: list[dict[str, Any]], parent: MgeCommanderAdminView) -> None:
        options = [
            discord.SelectOption(
                label=str(row.get("VariantName") or f"Variant {row.get('VariantId')}")[:100],
                value=str(int(row["VariantId"])),
            )
            for row in variants[:25]
        ]
        super().__init__(
            placeholder="Select variant",
            min_values=1,
            max_values=1,
            options=options or [discord.SelectOption(label="No variants", value="0")],
        )
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view._guard(interaction):
            return
        variant_id = int(self.values[0])
        if variant_id <= 0:
            await send_ephemeral(interaction, "No active MGE variants are configured.")
            return
        self.parent_view.variant_id = variant_id
        rows = await asyncio.to_thread(
            mge_commander_service.list_commanders_by_variant,
            variant_id,
            include_inactive=True,
        )
        await send_ephemeral(
            interaction,
            self.parent_view._format_variant_rows(rows),
            view=_CommanderPickerView(parent=self.parent_view, rows=rows),
        )


class _CommanderSelect(discord.ui.Select):
    def __init__(self, *, parent: MgeCommanderAdminView, rows: list[dict[str, Any]]) -> None:
        options = [discord.SelectOption(label="Add New Commander", value="new")]
        for row in rows[:24]:
            name = str(row.get("CommanderName") or "Unknown")
            state = "active" if _row_active(row) else "inactive"
            options.append(
                discord.SelectOption(
                    label=name[:100],
                    value=str(int(row["CommanderId"])),
                    description=state,
                )
            )
        super().__init__(
            placeholder="Add or edit commander",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.parent_view = parent
        self.rows = rows

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await self.parent_view._guard(interaction):
            return
        value = str(self.values[0])
        if value == "new":
            await interaction.response.send_modal(
                _CommanderEditModal(
                    parent=self.parent_view,
                    commander_id=None,
                    current_name="",
                    current_active=True,
                )
            )
            return

        commander_id = int(value)
        row = next((r for r in self.rows if int(r.get("CommanderId") or 0) == commander_id), None)
        if row is None:
            await send_ephemeral(interaction, "Commander selection is no longer available.")
            return
        await interaction.response.send_modal(
            _CommanderEditModal(
                parent=self.parent_view,
                commander_id=commander_id,
                current_name=str(row.get("CommanderName") or ""),
                current_active=_row_active(row),
            )
        )


class _CommanderPickerView(discord.ui.View):
    def __init__(self, *, parent: MgeCommanderAdminView, rows: list[dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        self.add_item(_CommanderSelect(parent=parent, rows=rows))


class MgeCommanderAdminView(discord.ui.View):
    def __init__(self, *, variants: list[dict[str, Any]], timeout: float | None = 300) -> None:
        super().__init__(timeout=timeout)
        self.variant_id: int | None = None
        self.add_item(_VariantSelect(variants=variants, parent=self))

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if not is_admin_interaction(interaction):
            await send_ephemeral(interaction, "Admin only.")
            return False
        return True

    def _format_variant_rows(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "No commanders are mapped to this variant yet."
        lines = ["Current commanders:"]
        for row in rows[:20]:
            state = "active" if _row_active(row) else "inactive"
            lines.append(f"- {row.get('CommanderName') or 'Unknown'} ({state})")
        if len(rows) > 20:
            lines.append(f"- ...and {len(rows) - 20} more")
        return "\n".join(lines)
