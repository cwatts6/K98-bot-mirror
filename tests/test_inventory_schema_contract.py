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


def test_inventory_phase1b_schema_defines_visibility_preference_contract():
    sql = Path("sql/inventory_phase1b_schema.sql").read_text(encoding="utf-8")

    required_tokens = [
        "SET ANSI_NULLS ON",
        "SET QUOTED_IDENTIFIER ON",
        "CREATE TABLE dbo.InventoryReportPreference",
        "DiscordUserID BIGINT NOT NULL",
        "Visibility NVARCHAR(32) NOT NULL",
        "CreatedAtUtc DATETIME2(3) NOT NULL",
        "UpdatedAtUtc DATETIME2(3) NOT NULL",
        "CK_InventoryReportPreference_Visibility",
        "N'only_me'",
        "N'public'",
    ]

    for token in required_tokens:
        assert token in sql


def test_inventory_phase1f_schema_defines_governor_profile_contract():
    sql = Path("sql/inventory_phase1f_schema.sql").read_text(encoding="utf-8")

    required_tokens = [
        "SET ANSI_NULLS ON",
        "SET QUOTED_IDENTIFIER ON",
        "CREATE TABLE dbo.GovernorInventoryProfile",
        "GovernorID BIGINT NOT NULL",
        "VipLevelCode NVARCHAR(32) NULL",
        "VipLevelLabel NVARCHAR(64) NULL",
        "UpdatedByDiscordUserID BIGINT NULL",
        "CreatedAtUtc DATETIME2(3) NOT NULL",
        "UpdatedAtUtc DATETIME2(3) NOT NULL",
        "CK_GovernorInventoryProfile_VipLevelCode",
        "N'VIP_14_OR_LESS'",
        "N'VIP_15'",
        "N'VIP_16'",
        "N'VIP_17'",
        "N'VIP_18'",
        "N'VIP_19'",
        "N'SVIP'",
    ]

    for token in required_tokens:
        assert token in sql


def test_inventory_phase2_materials_schema_defines_material_contract():
    sql = Path("sql/inventory_phase2_materials_schema.sql").read_text(encoding="utf-8")

    required_tokens = [
        "SET ANSI_NULLS ON",
        "SET QUOTED_IDENTIFIER ON",
        "CREATE TABLE dbo.GovernorMaterialInventory",
        "MaterialKind NVARCHAR(32) NOT NULL",
        "Rarity NVARCHAR(32) NOT NULL",
        "Quantity BIGINT NOT NULL",
        "LegendaryEquivalent DECIMAL(18,4) NOT NULL",
        "FK_GovernorMaterialInventory_ImportBatch",
        "CK_GovernorMaterialInventory_MaterialKind",
        "CK_GovernorMaterialInventory_Rarity",
        "IX_GovernorMaterialInventory_Governor_ScanUtc",
        "IX_GovernorMaterialInventory_Governor_Kind_Rarity_ScanUtc",
        "UX_GovernorMaterialInventory_Batch_Kind_Rarity",
    ]

    for token in required_tokens:
        assert token in sql


def test_inventory_phase2_materials_status_schema_adds_awaiting_more_material():
    sql = Path("sql/inventory_phase2_materials_status_schema.sql").read_text(encoding="utf-8")

    required_tokens = [
        "SET ANSI_NULLS ON",
        "SET QUOTED_IDENTIFIER ON",
        "CK_InventoryImportBatch_Status",
        "N'awaiting_more_material'",
        "UX_InventoryImportBatch_ActiveGovernor",
        "awaiting_more_material",
    ]

    for token in required_tokens:
        assert token in sql
