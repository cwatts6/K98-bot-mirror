"""Discord-free orchestration helpers for registry admin commands."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import csv
import io
import logging
import re
from typing import Any

from registry.registry_io import (
    apply_import_plan,
    build_error_csv_bytes,
    build_error_xlsx_bytes,
    export_registration_audit_files,
    export_registration_audit_xlsx_bytes,
    parse_csv_bytes,
    parse_xlsx_bytes,
    prepare_import_plan,
    rows_to_xlsx_bytes,
)

logger = logging.getLogger(__name__)

EXPORT_REGISTRATION_HEADERS = [
    "discord_id",
    "discord_id_excel",
    "discord_user",
    "account_type",
    "governor_id",
    "governor_id_excel",
    "governor_name",
    "roles",
    "top_role",
]


@dataclass(frozen=True, slots=True)
class RegistryAuditPayload:
    files: dict[str, io.BytesIO]
    xlsx_bytes: io.BytesIO | None
    registered_accounts_total: int
    unregistered_current_governors_count: int
    members_without_registration_count: int


@dataclass(frozen=True, slots=True)
class RegistryExportPayload:
    rows: list[dict[str, object]]
    csv_bytes: io.BytesIO
    xlsx_bytes: io.BytesIO | None

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True, slots=True)
class RegistryImportPreview:
    changes: list[dict[str, Any]]
    errors: list[str]
    warnings: list[str]
    error_rows: list[dict[str, str]]
    error_csv_bytes: io.BytesIO | None
    error_xlsx_bytes: io.BytesIO | None
    preview_lines: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class RegistryImportApplyResult:
    summary: list[str]
    errors: list[str]

    @property
    def applied_count(self) -> int:
        return len(self.summary)


def excel_safe_formula(value: object) -> str:
    v = str(value or "").strip()
    return f'="{v}"' if v else ""


def normalize_registry_governor_id(value: object) -> str:
    """Normalize GovernorID-like values used in registry audit/export comparisons."""
    if value is None:
        return ""
    if isinstance(value, int):
        text = str(value)
    elif isinstance(value, float):
        try:
            text = str(Decimal(str(value)).to_integral_value(rounding=ROUND_HALF_UP))
        except Exception:
            text = str(int(value))
    elif isinstance(value, Decimal):
        text = str(value.to_integral_value(rounding=ROUND_HALF_UP))
    else:
        text = str(value).strip()
        if text.startswith('="') and text.endswith('"') and len(text) >= 3:
            text = text[2:-1]
        text = text.replace(",", "")
        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
            try:
                text = str(Decimal(text).to_integral_value(rounding=ROUND_HALF_UP))
            except (InvalidOperation, ValueError):
                pass
    digits = re.findall(r"\d+", text)
    if digits:
        text = "".join(digits)
    return text.lstrip("0") or ("0" if text else "")


def extract_governor_id(details: dict[str, Any] | None) -> str:
    """Pull a GovernorID out of a registry account dict with legacy key tolerance."""
    if not isinstance(details, dict):
        return ""
    for key in (
        "GovernorID",
        "Governor Id",
        "GovernorId",
        "gov_id",
        "govid",
        "GovID",
        "Gov Id",
    ):
        if details.get(key):
            return str(details[key])
    for key, value in details.items():
        normalized_key = re.sub(r"[^a-z0-9]", "", str(key).lower())
        if (
            ("governor" in normalized_key and "id" in normalized_key)
            or normalized_key in ("govid", "govidnumber", "governorid")
        ) and value:
            return str(value)
    return ""


def parse_attachment_bytes(raw: bytes, file_type: str) -> list[dict[str, str]]:
    """Parse CSV/XLSX import bytes. Unknown files try CSV first, then XLSX."""
    if file_type == "csv":
        return parse_csv_bytes(raw)
    if file_type == "xlsx":
        try:
            return parse_xlsx_bytes(raw)
        except Exception:
            logger.exception("[IMPORT] XLSX parse failed, attempting CSV fallback")
            return parse_csv_bytes(raw)

    rows = parse_csv_bytes(raw)
    if rows:
        return rows
    try:
        return parse_xlsx_bytes(raw)
    except Exception:
        return []


def _registered_governor_ids(registry: dict[str, Any]) -> set[str]:
    registered_ids: set[str] = set()
    for data in (registry or {}).values():
        accounts = data.get("accounts") or {}
        if not isinstance(accounts, dict):
            continue
        for details in accounts.values():
            governor_id = normalize_registry_governor_id(extract_governor_id(details))
            if governor_id:
                registered_ids.add(governor_id)
    return registered_ids


def _current_governor_ids(sql_rows: list[dict[str, object]]) -> set[str]:
    current_ids: set[str] = set()
    for row in sql_rows or []:
        governor_id = normalize_registry_governor_id(row.get("GovernorID"))
        if governor_id:
            current_ids.add(governor_id)
    return current_ids


def build_registration_audit_payload(
    registry: dict[str, Any],
    members_info: dict[str, dict[str, str]],
    sql_rows: list[dict[str, object]],
) -> RegistryAuditPayload:
    files = export_registration_audit_files(registry, members_info, sql_rows)
    try:
        xlsx_bytes = export_registration_audit_xlsx_bytes(registry, members_info, sql_rows)
    except Exception:
        logger.exception("Failed to produce XLSX audit workbook")
        xlsx_bytes = None

    registered_accounts_total = 0
    for data in (registry or {}).values():
        accounts = data.get("accounts") or {}
        if isinstance(accounts, dict):
            registered_accounts_total += len(accounts)

    registered_ids = _registered_governor_ids(registry)
    current_ids = _current_governor_ids(sql_rows)
    registered_user_ids = {str(key).strip() for key in (registry or {}).keys()}
    members_without_registration_count = sum(
        1 for uid in (members_info or {}) if str(uid).strip() not in registered_user_ids
    )

    return RegistryAuditPayload(
        files=files,
        xlsx_bytes=xlsx_bytes,
        registered_accounts_total=registered_accounts_total,
        unregistered_current_governors_count=len(sorted(current_ids - registered_ids)),
        members_without_registration_count=members_without_registration_count,
    )


def build_registration_export_payload(
    registry: dict[str, Any],
    members_info: dict[str, dict[str, str]],
) -> RegistryExportPayload:
    rows: list[dict[str, object]] = []
    for uid, data in (registry or {}).items():
        uid_str = str(uid).strip()
        member_info = members_info.get(uid_str, {})
        accounts = data.get("accounts", {}) or {}
        if not isinstance(accounts, dict):
            continue
        for account_type, details in accounts.items():
            if not isinstance(details, dict):
                continue
            governor_id = str(details.get("GovernorID") or "").strip()
            rows.append(
                {
                    "discord_id": uid_str,
                    "discord_id_excel": excel_safe_formula(uid_str),
                    "discord_user": data.get("discord_name", uid_str),
                    "account_type": str(account_type).strip(),
                    "governor_id": governor_id,
                    "governor_id_excel": excel_safe_formula(governor_id),
                    "governor_name": details.get("GovernorName", ""),
                    "roles": member_info.get("roles", ""),
                    "top_role": member_info.get("top_role", ""),
                }
            )

    rows.sort(
        key=lambda row: (
            str(row.get("discord_user", "")).casefold(),
            str(row.get("account_type", "")).casefold(),
        )
    )

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_REGISTRATION_HEADERS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: row.get(header, "") for header in EXPORT_REGISTRATION_HEADERS})
    csv_bytes = io.BytesIO(buf.getvalue().encode("utf-8-sig"))

    try:
        xlsx_bytes = rows_to_xlsx_bytes(
            rows,
            EXPORT_REGISTRATION_HEADERS,
            sheet_name="registrations",
        )
    except Exception:
        logger.exception("Failed to produce XLSX export for registrations")
        xlsx_bytes = None

    return RegistryExportPayload(rows=rows, csv_bytes=csv_bytes, xlsx_bytes=xlsx_bytes)


def build_import_preview(
    rows: list[dict[str, str]],
    existing_registry: dict[str, Any],
) -> RegistryImportPreview:
    changes, errors, warnings, error_rows = prepare_import_plan(rows, existing_registry)
    error_csv_bytes = None
    error_xlsx_bytes = None
    if errors:
        error_csv_bytes = build_error_csv_bytes(error_rows)
        try:
            error_xlsx_bytes = build_error_xlsx_bytes(error_rows)
        except Exception:
            logger.exception("[IMPORT] failed to build XLSX error workbook")

    preview_lines = [
        f"Row {change.get('source_row')}: {change['discord_id']} | "
        f"{change['account_type']} -> {change['governor_id']}"
        for change in changes[:20]
    ]
    return RegistryImportPreview(
        changes=changes,
        errors=errors,
        warnings=warnings,
        error_rows=error_rows,
        error_csv_bytes=error_csv_bytes,
        error_xlsx_bytes=error_xlsx_bytes,
        preview_lines=preview_lines,
    )


def apply_import_changes(changes: list[dict[str, Any]]) -> RegistryImportApplyResult:
    _new_registry, summary, errors = apply_import_plan(changes, None, dry_run=False)
    return RegistryImportApplyResult(summary=summary, errors=errors)


def build_import_summary_text(
    result: RegistryImportApplyResult,
    warnings: list[str] | None = None,
    *,
    include_apply_errors: bool = True,
) -> str:
    text = f"Import applied: {result.applied_count} change(s) made.\n" + "\n".join(
        result.summary[:50]
    )
    if include_apply_errors and result.errors:
        text += f"\n\n{len(result.errors)} row(s) failed:\n" + "\n".join(
            f"- {error}" for error in result.errors[:20]
        )
    if warnings:
        text += "\n\nWarnings:\n" + "\n".join(f"- {warning}" for warning in warnings[:20])
    return text


def build_import_summary_file_bytes(
    result: RegistryImportApplyResult,
    warnings: list[str] | None = None,
) -> io.BytesIO:
    full = "\n".join(result.summary)
    if result.errors:
        full += "\n\nApply errors:\n" + "\n".join(result.errors)
    if warnings:
        full += "\n\nWarnings:\n" + "\n".join(warnings)
    return io.BytesIO(full.encode("utf-8"))
