#!/usr/bin/env python3
"""Static slash-command registration audit helper.

Usage:
  python scripts/validate_command_registration.py
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_COMMAND_INVENTORY_SPEC = importlib.util.spec_from_file_location(
    "_command_inventory", ROOT / "commands" / "command_inventory.py"
)
if _COMMAND_INVENTORY_SPEC is None or _COMMAND_INVENTORY_SPEC.loader is None:
    raise RuntimeError("Could not load commands/command_inventory.py")
_COMMAND_INVENTORY = importlib.util.module_from_spec(_COMMAND_INVENTORY_SPEC)
sys.modules[_COMMAND_INVENTORY_SPEC.name] = _COMMAND_INVENTORY
_COMMAND_INVENTORY_SPEC.loader.exec_module(_COMMAND_INVENTORY)
collect_declared_command_names = _COMMAND_INVENTORY.collect_declared_command_names
collect_static_primary_inventory = _COMMAND_INVENTORY.collect_static_primary_inventory

PRIMARY_COMMAND_LIMIT = 100
PRIMARY_COMMAND_WARNING_THRESHOLD = 90
PRIMARY_COMMAND_SURFACE_LABEL = "commands package (authoritative)"
SECONDARY_COGS_LABEL = "cogs/commands.py (disabled legacy)"
SECONDARY_SUBSCRIBE_LABEL = "subscribe.py (disabled legacy)"
APPROVED_TOP_LEVEL_COMMANDS = frozenset(
    {
        "activity",
        "ark",
        "calendar",
        "calendar_next_event",
        "calendar_reminder_config",
        "crystaltech",
        "events",
        "honor",
        "honor_rankings",
        "inventory",
        "kvk",
        "kvk_admin",
        "kvk_rankings",
        "location",
        "me",
        "mge",
        "modify_registration",
        "modify_subscription",
        "my_registrations",
        "mygovernorid",
        "mykvkcrystaltech",
        "mykvkhistory",
        "mykvkstats",
        "mykvktargets",
        "next_kvk_event",
        "next_kvk_fight",
        "ops",
        "ping",
        "prekvk",
        "register_governor",
        "registry",
        "stats",
        "subscribe",
        "subscriptions",
        "unsubscribe",
        "vote_admin",
    }
)


@dataclass(frozen=True)
class CommandSource:
    label: str
    path: Path


@dataclass(frozen=True)
class CommandRegistrationReport:
    primary_names: set[str]
    grouped: dict[str, set[str]]
    primary_name_sources: dict[str, list[str]]
    paths: dict[str, set[str]]
    active_duplicates: dict[str, list[str]]
    disabled_legacy_duplicates: dict[str, list[str]]
    unexpected_top_level: set[str]
    missing_approved_top_level: set[str]

    @property
    def grouped_subcommand_detected_count(self) -> int:
        return sum(len(commands) for commands in self.grouped.values())

    @property
    def primary_count(self) -> int:
        return len(self.primary_names)

    @property
    def total_unique(self) -> int:
        return len(set().union(*self.paths.values()))

    @property
    def secondary_cogs_count(self) -> int:
        return len(self.paths.get(SECONDARY_COGS_LABEL, set()))

    @property
    def secondary_subscribe_count(self) -> int:
        return len(self.paths.get(SECONDARY_SUBSCRIBE_LABEL, set()))

    @property
    def disabled_legacy_count(self) -> int:
        return sum(
            len(names)
            for label, names in self.paths.items()
            if label != PRIMARY_COMMAND_SURFACE_LABEL
        )

    @property
    def headroom(self) -> int:
        return PRIMARY_COMMAND_LIMIT - self.primary_count


SECONDARY_MODULES = [
    CommandSource(SECONDARY_COGS_LABEL, ROOT / "cogs" / "commands.py"),
    CommandSource(SECONDARY_SUBSCRIBE_LABEL, ROOT / "subscribe.py"),
]


def collect_names(path: Path) -> set[str]:
    return collect_declared_command_names(path)


def _collect_primary_inventory_details() -> (
    tuple[set[str], dict[str, set[str]], dict[str, list[str]]]
):
    inventory = collect_static_primary_inventory(ROOT)
    return inventory.names, inventory.grouped, inventory.name_sources


def collect_primary_inventory() -> tuple[set[str], dict[str, set[str]]]:
    names, grouped, _name_sources = _collect_primary_inventory_details()
    return names, grouped


def collect_primary_names() -> set[str]:
    names, _grouped = collect_primary_inventory()
    return names


def _build_report() -> CommandRegistrationReport:
    primary_names, grouped, primary_name_sources = _collect_primary_inventory_details()
    paths = {PRIMARY_COMMAND_SURFACE_LABEL: primary_names}
    paths.update({source.label: collect_names(source.path) for source in SECONDARY_MODULES})
    owners: dict[str, list[str]] = {}
    for label, names in paths.items():
        for name in names:
            owners.setdefault(name, []).append(label)
    active_duplicates = {
        name: sorted(labels) for name, labels in primary_name_sources.items() if len(labels) > 1
    }
    disabled_legacy_duplicates = {
        name: sorted(labels)
        for name, labels in owners.items()
        if len(labels) > 1 and name not in active_duplicates
    }
    return CommandRegistrationReport(
        primary_names=primary_names,
        grouped=grouped,
        primary_name_sources=primary_name_sources,
        paths=paths,
        active_duplicates=active_duplicates,
        disabled_legacy_duplicates=disabled_legacy_duplicates,
        unexpected_top_level=primary_names - APPROVED_TOP_LEVEL_COMMANDS,
        missing_approved_top_level=APPROVED_TOP_LEVEL_COMMANDS - primary_names,
    )


def _summary_line(report: CommandRegistrationReport) -> str:
    return (
        f"registration summary: primary={report.primary_count} "
        f"grouped_subcommands_detected={report.grouped_subcommand_detected_count} "
        f"disabled_legacy={report.disabled_legacy_count} "
        f"secondary_cogs={report.secondary_cogs_count} "
        f"secondary_subscribe={report.secondary_subscribe_count} "
        f"total_unique={report.total_unique}"
    )


def _report_payload(report: CommandRegistrationReport) -> dict[str, object]:
    return {
        "summary": {
            "primary": report.primary_count,
            "grouped_subcommands_detected": report.grouped_subcommand_detected_count,
            "disabled_legacy": report.disabled_legacy_count,
            "secondary_cogs": report.secondary_cogs_count,
            "secondary_subscribe": report.secondary_subscribe_count,
            "total_unique": report.total_unique,
            "primary_limit": PRIMARY_COMMAND_LIMIT,
            "warning_threshold": PRIMARY_COMMAND_WARNING_THRESHOLD,
            "headroom": report.headroom,
        },
        "top_level_commands": sorted(report.primary_names),
        "approved_top_level_commands": sorted(APPROVED_TOP_LEVEL_COMMANDS),
        "unexpected_top_level_commands": sorted(report.unexpected_top_level),
        "missing_approved_top_level_commands": sorted(report.missing_approved_top_level),
        "grouped_commands": {
            group_name: sorted(commands) for group_name, commands in sorted(report.grouped.items())
        },
        "active_duplicates": report.active_duplicates,
        "disabled_legacy_duplicates": report.disabled_legacy_duplicates,
    }


def _format_text(report: CommandRegistrationReport) -> str:
    lines = [_summary_line(report)]
    lines.append(f"active command surface: {PRIMARY_COMMAND_SURFACE_LABEL}")
    if report.disabled_legacy_count:
        lines.append("disabled legacy command surfaces retained:")
        for source in SECONDARY_MODULES:
            lines.append(
                f"  {source.label}: {len(report.paths.get(source.label, set()))} command(s)"
            )
    else:
        lines.append("disabled legacy command surfaces: none retained")

    if report.grouped:
        lines.append("grouped command summary (statically detected):")
        for group_name in sorted(report.grouped):
            subcommands = report.grouped[group_name]
            lines.append(f"  /{group_name}: {len(subcommands)} subcommand(s)")

    if report.primary_count > PRIMARY_COMMAND_LIMIT:
        lines.append(
            f"primary command limit exceeded: {report.primary_count}/{PRIMARY_COMMAND_LIMIT} "
            "top-level application commands"
        )
    elif report.primary_count >= PRIMARY_COMMAND_WARNING_THRESHOLD:
        lines.append(
            f"primary command limit warning: {report.primary_count}/{PRIMARY_COMMAND_LIMIT} "
            "top-level application commands"
        )

    if report.unexpected_top_level:
        lines.append("unexpected top-level command drift detected:")
        for name in sorted(report.unexpected_top_level):
            lines.append(f"  /{name}")
    else:
        lines.append("no unexpected top-level command drift detected")

    if report.missing_approved_top_level:
        lines.append("approved top-level commands missing from current inventory:")
        for name in sorted(report.missing_approved_top_level):
            lines.append(f"  /{name}")

    if not report.active_duplicates:
        lines.append("no active duplicate risks detected")
    else:
        lines.append("active duplicate risks detected:")
        for name in sorted(report.active_duplicates):
            lines.append(f"  /{name}: {', '.join(report.active_duplicates[name])}")

    if report.disabled_legacy_duplicates:
        lines.append("disabled legacy duplicates detected:")
        for name in sorted(report.disabled_legacy_duplicates):
            lines.append(f"  /{name}: {', '.join(report.disabled_legacy_duplicates[name])}")

    return "\n".join(lines)


def _format_json(report: CommandRegistrationReport) -> str:
    return json.dumps(_report_payload(report), indent=2, sort_keys=True)


def _format_markdown(report: CommandRegistrationReport) -> str:
    lines = [
        "# Command Registration Inventory",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Top-level commands | {report.primary_count} |",
        f"| Grouped subcommands detected | {report.grouped_subcommand_detected_count} |",
        f"| Disabled legacy declarations | {report.disabled_legacy_count} |",
        f"| Unique top-level commands | {report.total_unique} |",
        f"| Discord top-level limit | {PRIMARY_COMMAND_LIMIT} |",
        f"| Remaining headroom | {report.headroom} |",
        "",
        "## Grouped Commands",
        "",
        "| Group | Subcommands |",
        "|---|---:|",
    ]
    for group_name in sorted(report.grouped):
        lines.append(f"| `/{group_name}` | {len(report.grouped[group_name])} |")

    lines.extend(["", "## Top-Level Commands", ""])
    for name in sorted(report.primary_names):
        lines.append(f"- `/{name}`")

    lines.extend(["", "## Drift Checks", ""])
    if report.unexpected_top_level:
        lines.append("Unexpected top-level commands:")
        lines.extend(f"- `/{name}`" for name in sorted(report.unexpected_top_level))
    else:
        lines.append("- No unexpected top-level command drift detected.")
    if report.missing_approved_top_level:
        lines.append("- Approved top-level commands missing from current inventory:")
        lines.extend(f"  - `/{name}`" for name in sorted(report.missing_approved_top_level))
    if report.active_duplicates:
        lines.append("- Active duplicate risks detected:")
        lines.extend(
            f"  - `/{name}`: {', '.join(report.active_duplicates[name])}"
            for name in sorted(report.active_duplicates)
        )
    else:
        lines.append("- No active duplicate risks detected.")
    return "\n".join(lines)


def _is_failed(report: CommandRegistrationReport) -> bool:
    return (
        report.primary_count > PRIMARY_COMMAND_LIMIT
        or bool(report.unexpected_top_level)
        or bool(report.missing_approved_top_level)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="Output format for the command registration inventory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the formatted inventory artifact.",
    )
    args = parser.parse_args([] if argv is None else argv)

    report = _build_report()
    if args.format == "json":
        output = _format_json(report)
    elif args.format == "markdown":
        output = _format_markdown(report)
    else:
        output = _format_text(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)

    return 1 if _is_failed(report) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
