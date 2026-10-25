"""Read-only prerequisites for importing a replacement configuration workbook.

This never invokes import/publication procedures, takes ownership or releases a
reservation. Results describe current SQL state and must be checked again at
activation; the existing import transaction remains the final concurrency guard.
"""

from decimal import Decimal
import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.new_source_recovery_dal import current_config
from kvk.dal.source_weight_dal import stale_weight_periods, stored_weights
from kvk.models.source_configuration import weight_values
from kvk.schemas.new_source_schema import SOURCE_KEY
from services.export_configuration_values import numeric_value


def integer(row, key):
    value = row.get(key)
    return None if value in (None, "") else int(Decimal(str(value)))


class ConfigurationPreflightDAL:
    def __init__(self, connect):
        self.connect = connect

    def inspect(self, tables, *, source_recovery, source_intake):
        with transaction(self.connect) as cursor:
            result = self._targets(cursor, tables)
            windows = tables["KVK_Windows"] if source_recovery else []
            checked = set()
            for window in windows:
                season = integer(window, "KVK_NO")
                cursor.execute(
                    "SELECT DISTINCT p.PeriodID FROM KVK.SourceWindowConfig w "
                    "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO "
                    "AND p.PeriodKey=w.PeriodKey WHERE w.SourceKey=? AND w.KVK_NO=? AND w.WindowName=?",
                    SOURCE_KEY,
                    season,
                    window["WindowName"],
                )
                periods = rows(cursor)
                if len(periods) > 1:
                    raise SourceConflict(
                        f"KVK_Windows: {window['WindowName']} maps to multiple source periods. "
                        "Restore the intended window name before checking again."
                    )
                if periods:
                    period = str(periods[0]["PeriodID"])
                    self._period(cursor, season, period, window=window)
                    checked.add((season, period))
            if source_intake:
                for weight in tables["KVK_DKPWeights"]:
                    season = integer(weight, "KVK_NO")
                    cursor.execute("SELECT SourceKey FROM KVK.SeasonSource WHERE KVK_NO=?", season)
                    choice = one(cursor)
                    if not choice or choice["SourceKey"] != SOURCE_KEY:
                        continue
                    cursor.execute(
                        "SELECT PeriodID FROM KVK.SourcePeriod WHERE SourceKey=? AND KVK_NO=?",
                        SOURCE_KEY,
                        season,
                    )
                    for period_row in rows(cursor):
                        period = str(period_row["PeriodID"])
                        if (season, period) not in checked:
                            self._period(
                                cursor,
                                season,
                                period,
                                required=False,
                                coefficients=weight_values(
                                    [
                                        weight[key]
                                        for key in ("WeightT4X", "WeightT5Y", "WeightDeadsZ")
                                    ]
                                ),
                            )
                            checked.add((season, period))
            result["source_periods_checked"] = len(checked)
            result["empty_tabs_retain_sql"] = sorted(
                name for name, records in tables.items() if not records
            )
            return result

    @staticmethod
    def _targets(cursor, tables):
        details = tables["KVK_Details"]
        if details:
            season = max(integer(row, "KVK_NO") for row in details)
        else:
            cursor.execute("SELECT MAX(KVK_NO) AS Season FROM dbo.KVK_Details")
            season = one(cursor)["Season"]
        if not season:
            season = max(integer(row, "KVK_NO") for row in tables["ProcConfig"])
        numeric_value("ProcConfig", "KVK_NO", season)
        cursor.execute(
            "SELECT ConfigKey,ConfigValue FROM dbo.ProcConfig WHERE KVKVersion=? "
            "AND ConfigKey IN ('MATCHMAKING_SCAN','DRAFTSCAN')",
            season,
        )
        configured = {r["ConfigKey"]: r["ConfigValue"] for r in rows(cursor)}
        for row in tables["ProcConfig"]:
            if integer(row, "KVK_NO") == season:
                # The authoritative upsert skips NULL cells; it does not clear them.
                for key in ("MATCHMAKING_SCAN", "DRAFTSCAN"):
                    value = integer(row, key)
                    if value is not None:
                        configured[key] = value
        for key, value in configured.items():
            if value is not None:
                configured[key] = int(numeric_value("ProcConfig", key, value))
        cursor.execute("SELECT MAX(ScanOrder) AS Latest FROM dbo.KingdomScanData4")
        latest = one(cursor)["Latest"]
        matchmaking, draft = configured.get("MATCHMAKING_SCAN"), configured.get("DRAFTSCAN")
        selected = (
            matchmaking
            if latest is not None and matchmaking is not None and matchmaking <= latest
            else min(draft, latest) if latest is not None and draft is not None else None
        )
        if selected is not None:
            cursor.execute(
                "SELECT TOP (1) ScanOrder FROM dbo.KingdomScanData4 WHERE ScanOrder=?", selected
            )
            if one(cursor) is None:
                raise SourceConflict(
                    f"ProcConfig: season {season} would select unavailable scan {selected}. "
                    "Verify MATCHMAKING_SCAN and DRAFTSCAN in the replacement workbook."
                )
        cursor.execute(
            "SELECT PublicationState,SourceScanOrder,ConfiguredMatchmakingScan "
            "FROM dbo.KVK_Target_Publication WHERE KVK_NO=? AND IsCurrent=1",
            season,
        )
        publication = one(cursor)
        if (
            publication
            and publication["PublicationState"] == "OFFICIAL"
            and (
                matchmaking is None
                or publication["ConfiguredMatchmakingScan"] != matchmaking
                or publication["SourceScanOrder"] != matchmaking
                or (selected is not None and selected != matchmaking)
            )
        ):
            raise SourceConflict(
                f"ProcConfig: season {season} already has official targets from scan "
                f"{publication['SourceScanOrder']}. Restore that MATCHMAKING_SCAN in the "
                "replacement workbook; replacement recovery cannot republish official targets."
            )
        return dict(season=int(season), selected_scan=selected)

    @staticmethod
    def _period(cursor, season, period, *, window=None, required=True, coefficients=None):
        cursor.execute(
            "SELECT PublicationID FROM KVK.SourceSelection WHERE SourceKey=? AND KVK_NO=? AND PeriodID=?",
            SOURCE_KEY,
            season,
            period,
        )
        selection = one(cursor)
        cursor.execute(
            "SELECT r.*,c.ConfigVersion FROM KVK.SourceConfigRequest r "
            "JOIN KVK.SourceConfigVersion c ON c.ConfigVersionID=r.DesiredConfigVersionID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? AND r.PeriodID=? AND r.RequestState<>'rejected' "
            "ORDER BY c.ConfigVersion DESC",
            SOURCE_KEY,
            season,
            period,
        )
        requests = rows(cursor)
        base_id = current_config(cursor, season, period, selection, requests)
        if base_id is None and not required:
            return
        if coefficients is not None and stored_weights(cursor, base_id) == coefficients:
            stale = {str(key) for key in stale_weight_periods(cursor, season, coefficients)}
            pending = next(
                (r for r in requests if str(r["DesiredConfigVersionID"]) == base_id), None
            )
            if period not in stale or (
                pending and json.loads(pending["ProvenanceJson"]).get("current_weights")
            ):
                return
        cursor.execute(
            "SELECT w.StartScanID,w.EndScanID,p.PeriodKind FROM KVK.SourceConfigVersion c "
            "JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
            "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO "
            "AND p.PeriodKey=w.PeriodKey WHERE c.SourceKey=? AND c.KVK_NO=? "
            "AND c.ConfigVersionID=? AND p.PeriodID=?",
            SOURCE_KEY,
            season,
            base_id,
            period,
        )
        base = one(cursor)
        if base is None:
            raise SourceConflict(f"Season {season}: approved source configuration is unavailable.")
        cursor.execute("SELECT SourceKey,SeasonState FROM KVK.SeasonSource WHERE KVK_NO=?", season)
        choice = one(cursor)
        if not choice or choice["SourceKey"] != SOURCE_KEY or choice["SeasonState"] != "open":
            raise SourceConflict(
                f"Season {season}: source configuration import requires an open season."
            )
        start = integer(window or base, "StartScanID")
        end = integer(window or base, "EndScanID")
        if base["PeriodKind"] == "no_fight" and start != end:
            raise SourceConflict(
                f"KVK_Windows: season {season} baseline window requires identical start/end scans."
            )
        if start is not None and end is not None:
            cursor.execute(
                "SELECT LogicalScanID,ScanStartUTC FROM KVK.SourceLogicalScan s "
                "JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID "
                "WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID IN (?,?)",
                SOURCE_KEY,
                season,
                start,
                end,
            )
            times = {r["LogicalScanID"]: r["ScanStartUTC"] for r in rows(cursor)}
            if start in times and end in times and start != end and times[end] <= times[start]:
                raise SourceConflict(
                    f"KVK_Windows: season {season} end scan must occur after its start scan."
                )
