from pathlib import Path


def test_inventory_phase1a_schema_defines_required_tables_and_indexes():
    sql = Path("sql/inventory_phase1a_schema.sql").read_text(encoding="utf-8")

    required_tokens = [
        "SET ANSI_NULLS ON",
        "SET QUOTED_IDENTIFIER ON",
        "CREATE TABLE dbo.InventoryImportBatch",
        "CREATE TABLE dbo.GovernorResourceInventory",
        "CREATE TABLE dbo.GovernorSpeedupInventory",
        "UX_InventoryImportBatch_ActiveGovernor",
        "UX_InventoryImportBatch_ApprovedDaily",
        "IX_InventoryImportBatch_Governor_Status_Expires",
        "IX_InventoryImportBatch_DiscordUser_Status",
        "IX_InventoryImportBatch_Audit",
        "IX_GovernorResourceInventory_Governor_ScanUtc",
        "UX_GovernorResourceInventory_Batch_Type",
        "IX_GovernorSpeedupInventory_Governor_ScanUtc",
        "UX_GovernorSpeedupInventory_Batch_Type",
    ]

    for token in required_tokens:
        assert token in sql


def test_inventory_phase1a_schema_captures_upload_and_debug_contract():
    sql = Path("sql/inventory_phase1a_schema.sql").read_text(encoding="utf-8")

    for column in (
        "FlowType",
        "SourceMessageID",
        "SourceChannelID",
        "ImageAttachmentURL",
        "AdminDebugChannelID",
        "AdminDebugMessageID",
        "OriginalUploadDeletedAtUtc",
        "ExpiresAtUtc",
        "ApprovedDateUtc",
    ):
        assert column in sql
