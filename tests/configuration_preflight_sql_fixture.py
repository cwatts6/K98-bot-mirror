"""Session-local, typed projections of the authoritative preflight SQL columns.

These compile read queries against SQL Server; they do not validate deployment
permissions or replace the independent authoritative schema/migration checks.
"""

import re

from tests import test_export_target_containment_sql as fixture_module

TABLE_COLUMNS = {
    "dbo.KVK_Details": "KVK_NO int NOT NULL",
    "dbo.ProcConfig": "KVKVersion int NOT NULL,ConfigKey varchar(50) NOT NULL,ConfigValue float NULL",
    "dbo.KingdomScanData4": "ScanOrder int NULL",
    "dbo.KVK_Target_Publication": "KVK_NO int NOT NULL,PublicationState nvarchar(16) NOT NULL,SourceScanOrder int NOT NULL,ConfiguredMatchmakingScan int NULL,IsCurrent bit NOT NULL",
    "KVK.SeasonSource": "KVK_NO int NOT NULL,SourceKey varchar(32) NOT NULL,SeasonState varchar(16) NOT NULL",
    "KVK.SourcePeriod": "PeriodID uniqueidentifier NOT NULL,SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,PeriodKey nvarchar(64) NOT NULL,PeriodKind varchar(32) NOT NULL",
    "KVK.SourceWindowConfig": "ConfigVersionID uniqueidentifier NOT NULL,SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,PeriodKey nvarchar(64) NOT NULL,WindowName nvarchar(40) NOT NULL,StartScanID int NULL,EndScanID int NULL",
    "KVK.SourceConfigVersion": "ConfigVersionID uniqueidentifier NOT NULL,SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,ConfigVersion int NOT NULL",
    "KVK.SourceSelection": "SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,PeriodID uniqueidentifier NOT NULL,PublicationID uniqueidentifier NOT NULL",
    "KVK.SourcePublication": "PublicationID uniqueidentifier NOT NULL,ConfigVersionID uniqueidentifier NOT NULL",
    "KVK.SourceConfigRequest": "RequestID uniqueidentifier NOT NULL,SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,PeriodID uniqueidentifier NOT NULL,DesiredConfigVersionID uniqueidentifier NOT NULL,RequestState varchar(32) NOT NULL",
    "KVK.SourceLogicalScan": "SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,LogicalScanID int NOT NULL,ObservationID uniqueidentifier NOT NULL",
    "KVK.SourceObservation": "ObservationID uniqueidentifier NOT NULL,ScanStartUTC datetime2(0) NOT NULL",
    "KVK.SourceWeightConfig": "ConfigVersionID uniqueidentifier NOT NULL,WeightT4X decimal(38,12) NOT NULL,WeightT5Y decimal(38,12) NOT NULL,WeightDeadsZ decimal(38,12) NOT NULL",
    "KVK.SourceCompleteSelection": "SourceKey varchar(32) NOT NULL,KVK_NO int NOT NULL,PeriodID uniqueidentifier NOT NULL,UpdateID uniqueidentifier NOT NULL",
    "KVK.SourceUpdate": "UpdateID uniqueidentifier NOT NULL,ConfigVersionID uniqueidentifier NOT NULL",
}


def install_preflight_tables(monkeypatch, fixture):
    previous = fixture_module.local_sql

    def rewrite(text):
        for name in sorted(TABLE_COLUMNS, key=len, reverse=True):
            text = re.sub(r"\b" + re.escape(name) + r"\b", "#" + name.split(".")[1], text)
        return previous(text)

    monkeypatch.setattr(fixture_module, "local_sql", rewrite)
    for name, columns in TABLE_COLUMNS.items():
        fixture.sql.execute(f"CREATE TABLE #{name.split('.')[1]} ({columns})")
    fixture.sql.execute("INSERT #KingdomScanData4 (ScanOrder) VALUES (101),(107)")
    fixture.sql.commit()
