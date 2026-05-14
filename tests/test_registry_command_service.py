from __future__ import annotations

import csv
import io

from registry import registry_command_service as svc


def _sample_registry() -> dict:
    return {
        "200": {
            "discord_name": "BetaUser",
            "accounts": {"Main": {"GovernorID": "200100", "GovernorName": "Beta"}},
        },
        "100": {
            "discord_name": "AlphaUser",
            "accounts": {
                "Main": {"GovernorID": '="100001"', "GovernorName": "Alpha"},
                "Alt 1": {"GovernorID": "100002", "GovernorName": "AlphaAlt"},
            },
        },
    }


def test_build_registration_audit_payload_counts_and_files() -> None:
    registry = _sample_registry()
    members_info = {
        "100": {"discord_user": "AlphaUser", "roles": "R1", "top_role": "R1"},
        "300": {"discord_user": "NoReg", "roles": "", "top_role": ""},
    }
    sql_rows = [
        {"GovernorID": 100001, "GovernorName": "Alpha"},
        {"GovernorID": 300300, "GovernorName": "Unregistered"},
    ]

    payload = svc.build_registration_audit_payload(registry, members_info, sql_rows)

    assert payload.registered_accounts_total == 3
    assert payload.unregistered_current_governors_count == 1
    assert payload.members_without_registration_count == 1
    assert set(payload.files) == {
        "registered_accounts.csv",
        "unregistered_current_governors.csv",
        "members_without_registration.csv",
    }


def test_build_registration_export_payload_sorts_and_preserves_excel_safe_columns() -> None:
    payload = svc.build_registration_export_payload(
        _sample_registry(),
        {
            "100": {"roles": "R1;R2", "top_role": "R2"},
            "200": {"roles": "R3", "top_role": "R3"},
        },
    )

    text = payload.csv_bytes.getvalue().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))

    assert payload.row_count == 3
    assert [row["discord_user"] for row in rows] == ["AlphaUser", "AlphaUser", "BetaUser"]
    assert rows[0]["discord_id_excel"] == '="100"'
    assert rows[0]["governor_id_excel"] == '="100002"'
    assert rows[0]["roles"] == "R1;R2"


def test_build_import_preview_creates_error_files_for_invalid_rows() -> None:
    rows = [{"discord_id": "123", "account_type": "Main", "governor_id": "not-a-number"}]

    preview = svc.build_import_preview(rows, {})

    assert not preview.ok
    assert preview.errors
    assert preview.error_csv_bytes is not None
    assert "Invalid GovernorID" in preview.errors[0]


def test_build_import_preview_shapes_success_preview_lines() -> None:
    rows = [
        {
            "discord_id": "123",
            "account_type": "Main",
            "governor_id": "100001",
            "governor_name": "Alpha",
        }
    ]

    preview = svc.build_import_preview(rows, {})

    assert preview.ok
    assert preview.preview_lines == ["Row 2: 123 | Main -> 100001"]
    assert preview.changes[0]["governor_name"] == "Alpha"


def test_build_import_summary_text_includes_apply_errors_and_warnings() -> None:
    result = svc.RegistryImportApplyResult(
        summary=["123: Main -> 100001 (Alpha)"],
        errors=["Row 3: duplicate"],
    )

    text = svc.build_import_summary_text(result, ["Row 2: formula"])

    assert "1 change(s) made" in text
    assert "1 row(s) failed" in text
    assert "Row 2: formula" in text
