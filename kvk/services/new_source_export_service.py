"""Generation-bound source exports. No legacy sums, credentials or implicit latest reads."""

from dataclasses import dataclass
import hashlib
import json
import logging
import threading
import time
from typing import ClassVar

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.dal.new_source_publication_dal import RESULT_METRICS
from kvk.rendering.new_source_export import ExportTable, table
from kvk.schemas.new_source_schema import SOURCE_KEY
from kvk.services.kvk_export_service import (
    KVK_EXPORT_SECTION_NAMES,
    bind_kvk_export_sections_v2,
)

logger = logging.getLogger(__name__)


class GoogleRequestPacer:
    """Shared process budget leaves quota headroom for other service-account consumers."""

    _lock = threading.Lock()
    _last: ClassVar[dict[str, float]] = {}

    def __init__(self, identity):
        self.identity = identity

    def __call__(self):
        with self._lock:
            time.sleep(max(0, 2.1 - (time.monotonic() - self._last.get(self.identity, 0))))
            self._last[self.identity] = time.monotonic()


def google_error_details(request, error):
    """Never include provider prose, URLs, request bodies, credentials or cell values."""
    allowed = {
        "drive.files.update",
        "drive.permissions.create",
        "drive.permissions.delete",
        "sheets.spreadsheets.batchUpdate",
        "sheets.spreadsheets.values.update",
        "drive.files.get",
        "sheets.spreadsheets.get",
        "sheets.spreadsheets.values.get",
        "sheets.spreadsheets.values.batchGet",
    }
    operation = getattr(request, "methodId", "unknown")
    status = getattr(getattr(error, "resp", None), "status", None)
    reason = {
        400: "invalid_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        429: "rate_limited",
    }.get(status, "outcome_unknown")
    content = getattr(error, "content", b"")
    if isinstance(content, bytes) and len(content) <= 65536:
        try:
            message = json.loads(content).get("error", {}).get("message", "")
            if status == 400 and "delete all non-frozen rows" in message:
                reason = "frozen_rows_shrink"
        except (ValueError, TypeError, AttributeError):
            pass
    return {
        "operation": operation if operation in allowed else "unknown",
        "status": status if type(status) is int else None,
        "reason": reason,
    }


AGGREGATE_METRICS = (
    "t4_kills",
    "t5_kills",
    "kp_t4_t5",
    "dead",
    "t4_t5_dead",
    "healed",
    "acclaim",
    "dkp",
)
CONTEXT = (
    "schema_version",
    "source_key",
    "kvk_no",
    "period_id",
    "period_key",
    "period_label",
    "publication_id",
    "selection_version",
    "generation",
    "selected_config_id",
    "requested_config_id",
    "requested_start_scan_id",
    "requested_end_scan_id",
    "selected_start_scan_id",
    "selected_end_scan_id",
    "player_start_utc",
    "player_end_utc",
    "aggregate_revision_id",
    "aggregate_coverage_start_utc",
    "aggregate_coverage_end_utc",
    "aggregate_as_of_utc",
    "player_state",
    "aggregate_state",
    "current_period_state",
    "is_current",
    "roster_id",
    "calculation_version",
)
FACT_COLUMNS = (
    *CONTEXT,
    "entity_kind",
    "entity_id",
    "name",
    "b0_kingdom",
    "camp_id",
    "metric",
    "value",
    "status",
    "raw",
    "unit",
    "precision",
    "rank",
    "cohort",
)


@dataclass(frozen=True)
class ExportSelection:
    kvk_no: int
    period_id: str
    publication_id: str
    selection_version: int

    def __post_init__(self):
        from uuid import UUID

        if type(self.kvk_no) is not int or not 1 <= self.kvk_no <= 2147483647:
            raise ValueError("Explicit source KVK is required.")
        for value in (self.period_id, self.publication_id):
            if not isinstance(value, str) or str(UUID(value)) != value:
                raise ValueError("Canonical publication/period UUIDs are required.")
        if type(self.selection_version) is not int or self.selection_version < 1:
            raise ValueError("Explicit selection version is required.")


@dataclass(frozen=True)
class ExportGeneration:
    selections: tuple[ExportSelection, ...]
    tables: tuple[ExportTable, ...]
    schema_version: int = 2

    def __post_init__(self):
        if (
            not isinstance(self.selections, tuple)
            or not self.selections
            or any(not isinstance(s, ExportSelection) for s in self.selections)
        ):
            raise ValueError("Generation requires immutable explicit selections.")
        if not isinstance(self.tables, tuple) or {t.name for t in self.tables} != {
            *KVK_EXPORT_SECTION_NAMES,
            "ALL_WINDOWS",
            "COMPARISONS",
        }:
            raise ValueError("Generation requires all twelve intended output tables.")
        bind_kvk_export_sections_v2(
            {t.name: t for t in self.tables}, schema_version=self.schema_version
        )
        if len({t.name for t in self.tables}) != len(self.tables):
            raise ValueError("Duplicate generation table.")

    @property
    def key(self):
        manifest = [
            (s.kvk_no, s.period_id, s.publication_id, s.selection_version) for s in self.selections
        ]
        manifest.extend((t.name, t.sha256) for t in self.tables)
        return hashlib.sha256(json.dumps(manifest, separators=(",", ":")).encode()).hexdigest()

    def manifest(self):
        return {
            t.name: {"sha256": t.sha256, "rows": len(t.rows), "columns": len(t.columns)}
            for t in self.tables
        }


def load_generation(*, connect, selections, snapshot_loader=None):
    """Read exactly the caller's periods/publications; never retarget a stale request."""
    from kvk.dal.new_source_delivery_dal import load_export_snapshot

    chosen = tuple(selections)
    if not chosen or any(not isinstance(s, ExportSelection) for s in chosen):
        raise ValueError("Explicit export selections are required.")
    loader = snapshot_loader or load_export_snapshot
    return build_generation(tuple((s, loader(connect=connect, selection=s)) for s in chosen))


def _facts(envelope, meta, context, kind):
    aggregate = kind != "player"
    items = (
        envelope["players"]
        if not aggregate
        else envelope["aggregates"][
            "SourceKingdomReportRow" if kind == "kingdom" else "SourceCampReportRow"
        ]
    )
    metrics = (
        (*AGGREGATE_METRICS, "total_kill_points", "highest_acclaim")
        if aggregate
        else (*RESULT_METRICS, "t4_t5_dead")
    )
    identities = set()
    output = []
    identity_column = (
        "GovernorID" if kind == "player" else "Kingdom" if kind == "kingdom" else "CampID"
    )
    for item in sorted(items, key=lambda row: row[identity_column]):
        entity = item[
            "GovernorID" if kind == "player" else "Kingdom" if kind == "kingdom" else "CampID"
        ]
        if type(entity) is not int or entity <= 0 or entity in identities:
            raise SourceConflict("Invalid or duplicate export entity identity.")
        identities.add(entity)
        states = {} if aggregate else json.loads(item["FieldStatusJson"])
        for metric in metrics:
            state = (
                ("available" if metric in AGGREGATE_METRICS else "unsupported")
                if aggregate
                else states.get(metric, "unsupported")
            )
            value = item.get(metric) if state == "available" else None
            if (state == "available") != (value is not None):
                raise SourceConflict("Export metric availability mismatch.")
            output.append(
                dict(
                    context,
                    entity_kind=kind,
                    entity_id=entity,
                    name=item.get("CampLabel") if aggregate else item.get("name"),
                    b0_kingdom=item.get("Kingdom") if aggregate else item["b0_kingdom"],
                    camp_id=item["CampID"],
                    metric=metric,
                    value=value,
                    status=state,
                    raw=item.get(metric + "_raw") if aggregate else None,
                    unit=item.get(metric + "_unit") if aggregate else None,
                    precision=(
                        item.get(metric + "_precision") if aggregate else "exact_calculated"
                    ),
                    rank=item.get(metric + "_rank") if not aggregate else None,
                    cohort=item.get(metric + "_cohort") if not aggregate else None,
                )
            )
    if not output:
        output.append(
            dict(
                context,
                entity_kind=kind,
                status=context["aggregate_state" if aggregate else "player_state"],
            )
        )
    return output


def build_generation(inputs):
    """Ten named V2 sections plus long-form ALL_WINDOWS/comparisons keyed by stable IDs.

    Inputs are private S3B envelopes enriched only by their immutable config/revision IDs.
    Full sections contain explicit overall selections; missing overall is a status row.
    Comparisons retain facts side by side and never invent cross-basis ranks/deltas.
    """
    if not inputs:
        raise ValueError("At least one explicit publication is required.")
    sections = {name: [] for name in KVK_EXPORT_SECTION_NAMES}
    all_facts, selections, seen = [], [], set()
    for selection, snapshot in sorted(inputs, key=lambda item: (item[0].kvk_no, item[0].period_id)):
        envelope, meta = snapshot["envelope"], snapshot["metadata"]
        pub = envelope.get("publication")
        if not pub or (
            envelope["source_key"],
            envelope["kvk_no"],
            str(envelope["period_id"]),
            str(pub["PublicationID"]),
            envelope["selection"]["SelectionVersion"],
        ) != (
            SOURCE_KEY,
            selection.kvk_no,
            selection.period_id,
            selection.publication_id,
            selection.selection_version,
        ):
            raise SourceConflict("Export selection changed or belongs to another scope.")
        scope = (selection.kvk_no, selection.period_id)
        if scope in seen:
            raise SourceConflict("Choose exactly one publication per period.")
        seen.add(scope)
        selections.append(selection)
        config, requested = meta["configs"]["selected"], meta["configs"]["requested"]
        for cfg in (config, requested):
            if (cfg["SourceKey"], cfg["KVK_NO"], cfg["PeriodKey"]) != (
                SOURCE_KEY,
                selection.kvk_no,
                pub["PeriodKey"],
            ):
                raise SourceConflict("Export configuration scope mismatch.")
        if (
            config["EndScanID"] is not None
            and config["StartScanID"] is not None
            and config["EndScanID"] < config["StartScanID"]
        ):
            raise SourceConflict("Invalid configured endpoint order.")
        aggregate = meta["aggregate"] or {}
        context = dict(
            schema_version=2,
            source_key=SOURCE_KEY,
            kvk_no=selection.kvk_no,
            period_id=selection.period_id,
            period_key=pub["PeriodKey"],
            period_label=config["WindowName"],
            publication_id=selection.publication_id,
            selection_version=selection.selection_version,
            generation=pub["Generation"],
            selected_config_id=str(pub["ConfigVersionID"]),
            requested_config_id=str(envelope["desired_config_id"]),
            requested_start_scan_id=requested["StartScanID"],
            requested_end_scan_id=requested["EndScanID"],
            selected_start_scan_id=pub["StartScanID"],
            selected_end_scan_id=pub["EndScanID"],
            player_start_utc=(meta["endpoints"]["start"] or {}).get("ScanStartUTC"),
            player_end_utc=(meta["endpoints"]["end"] or {}).get("ScanStartUTC"),
            aggregate_revision_id=pub["AggregateRevisionID"],
            aggregate_coverage_start_utc=aggregate.get("CoverageStartUTC"),
            aggregate_coverage_end_utc=aggregate.get("CoverageEndUTC"),
            aggregate_as_of_utc=aggregate.get("AsOfUTC"),
            player_state=pub["PlayerState"],
            aggregate_state=pub["AggregateState"],
            current_period_state=envelope["current_period_state"],
            is_current=envelope["is_current"],
            roster_id=str(pub["RosterID"]),
            calculation_version=pub["CalculationVersion"],
        )
        if config["StartScanID"] == config["EndScanID"] and config["StartScanID"] is not None:
            if pub["AggregateState"] != "not_applicable" or pub["AggregateRevisionID"]:
                raise SourceConflict("Equal-endpoint aggregate is not applicable.")
        if (
            config["PeriodKind"] == "overall"
            and pub["AggregateRevisionID"]
            and pub["AggregateState"] not in ("final", "corrected_final")
        ):
            raise SourceConflict("Overall requires its separate final aggregate.")
        sections["KVK_Windows"].append(context)
        weight = snapshot.get("weights") or {}
        sections["KVK_DKP_Weights"].append(
            dict(context, **weight, status="available" if weight else "missing_configuration")
        )
        for role in ("start", "end"):
            endpoint = meta["endpoints"][role] or {}
            sections["KVK_Scan_Log"].append(
                dict(
                    context,
                    endpoint=role,
                    observation_id=endpoint.get("ObservationID"),
                    revision_id=pub.get(role.title() + "RevisionID"),
                    scan_start_utc=endpoint.get("ScanStartUTC"),
                    time_precision=endpoint.get("TimePrecision"),
                )
            )
        suffix = "Full" if config["PeriodKind"] == "overall" else "Windowed"
        for kind in ("player", "kingdom", "camp"):
            facts = _facts(envelope, meta, context, kind)
            sections[f"KVK_{kind.title()}_{suffix}"].extend(facts)
            all_facts.extend(facts)
            sections["KVK_Ingest_Negatives"].extend(
                f for f in facts if f.get("status") not in ("available", "not_applicable")
            )
    for season in sorted({s.kvk_no for s in selections}):
        if not any(row.get("kvk_no") == season for row in sections["KVK_Player_Full"]):
            for kind in ("player", "kingdom", "camp"):
                unavailable = dict(
                    schema_version=2,
                    source_key=SOURCE_KEY,
                    kvk_no=season,
                    period_key="overall",
                    entity_kind=kind,
                    status="not_received",
                )
                sections[f"KVK_{kind.title()}_Full"].append(unavailable)
                all_facts.append(unavailable)
    columns = {
        "KVK_Scan_Log": (
            *CONTEXT,
            "endpoint",
            "observation_id",
            "revision_id",
            "scan_start_utc",
            "time_precision",
        ),
        "KVK_Windows": CONTEXT,
        "KVK_DKP_Weights": (
            *CONTEXT,
            "WeightT4XSource",
            "WeightT5YSource",
            "WeightDeadsZSource",
            "EffectiveFromUTC",
            "status",
        ),
    }
    tables = [
        table(name, columns.get(name, FACT_COLUMNS), sections[name])
        for name in KVK_EXPORT_SECTION_NAMES
    ]
    tables.append(table("ALL_WINDOWS", FACT_COLUMNS, all_facts))
    tables.append(
        table(
            "COMPARISONS",
            (*FACT_COLUMNS, "comparison_status"),
            [dict(f, comparison_status="side_by_side_only") for f in all_facts],
        )
    )
    return ExportGeneration(tuple(selections), tuple(tables))


def compact_sheets_generation(generation):
    """Lossless physical projection: one entity row, metric columns, shared UTC context.

    Blank metric status means that metric did not occur in this logical section;
    explicit statuses remain explicit. KVK_Windows stores each complete context once.
    Canonical V2 exports and independent CSV renderers retain their existing shape.
    """
    contexts = {}
    output = []
    identity = (
        "schema_version",
        "source_key",
        "kvk_no",
        "period_key",
        "context_ref",
        "entity_kind",
        "entity_id",
        "name",
        "b0_kingdom",
        "camp_id",
    )
    attributes = ("value", "status", "raw", "unit", "precision", "rank", "cohort")
    for item in generation.tables:
        if "metric" not in item.columns:
            output.append(item)
            continue
        grouped = {}
        used = set()
        for values in item.rows:
            row = dict(zip(item.columns, values, strict=True))
            context = tuple(row[c] for c in CONTEXT)
            ref = hashlib.sha256(json.dumps(context, separators=(",", ":")).encode()).hexdigest()
            contexts[ref] = context
            row["context_ref"] = ref
            group = tuple(row[c] for c in identity)
            record = grouped.setdefault(group, dict(zip(identity, group, strict=True)))
            metric = row["metric"]
            if metric:
                for field in attributes:
                    column = metric + "::" + field
                    if column in record:
                        raise SourceConflict("Duplicate metric in compact entity row.")
                    record[column] = row[field]
                    if row[field]:
                        used.add(column)
            else:
                record["status"] = row["status"]
                used.add("status")
            if "comparison_status" in row:
                record["comparison_status"] = row["comparison_status"]
                used.add("comparison_status")
        columns = (*identity, *sorted(used))
        output.append(table(item.name, columns, grouped.values()))
    windows = next(t for t in output if t.name == "KVK_Windows")
    for values in windows.rows:
        row = dict(zip(windows.columns, values, strict=True))
        context = tuple(row[c] for c in CONTEXT)
        ref = hashlib.sha256(json.dumps(context, separators=(",", ":")).encode()).hexdigest()
        contexts[ref] = context
    windows = ExportTable(
        "KVK_Windows",
        (*CONTEXT, "context_ref"),
        tuple((*context, ref) for ref, context in sorted(contexts.items())),
    )
    return ExportGeneration(
        generation.selections, tuple(windows if t.name == "KVK_Windows" else t for t in output)
    )


def load_sheets_generation(*, connect, selections, snapshot_loader=None):
    """Compact each pinned period before combining, bounding transient long-form memory."""
    chosen = tuple(sorted(selections, key=lambda s: (s.kvk_no, s.period_id)))
    if not chosen or len({(s.kvk_no, s.period_id) for s in chosen}) != len(chosen):
        raise ValueError("Explicit unique selections required.")
    periods = [
        compact_sheets_generation(
            load_generation(connect=connect, selections=(s,), snapshot_loader=snapshot_loader)
        )
        for s in chosen
    ]
    # Per-period canonical output inserts unavailable overall placeholders. Keep those
    # only when no requested period supplies an actual overall publication.
    overall_seasons = {
        row[t.columns.index("kvk_no")]
        for p in periods
        for t in p.tables
        if t.name == "KVK_Windows"
        for row in t.rows
        if row[t.columns.index("period_key")] == "overall"
        and row[t.columns.index("publication_id")]
    }
    tables = []
    for name in (*KVK_EXPORT_SECTION_NAMES, "ALL_WINDOWS", "COMPARISONS"):
        parts = [next(t for t in p.tables if t.name == name) for p in periods]
        columns = tuple(dict.fromkeys(c for t in parts for c in t.columns))
        combined, seen = [], set()
        for part in parts:
            for values in part.rows:
                row = dict(zip(part.columns, values, strict=True))
                # Missing overall rows have no context publication; their reference
                # is deterministic and duplicate placeholders are removed below.
                if (
                    row.get("kvk_no") in overall_seasons
                    and row.get("period_key") == "overall"
                    and (
                        row.get("status") == "not_received"
                        or (name == "KVK_Windows" and not row.get("publication_id"))
                    )
                ):
                    continue
                result = tuple(row.get(c, "") for c in columns)
                if result not in seen:
                    seen.add(result)
                    combined.append(result)
        tables.append(ExportTable(name, columns, tuple(combined)))
    return ExportGeneration(chosen, tuple(tables))


@dataclass(frozen=True)
class SheetsRegistration:
    """Operator-owned dedicated workbooks; file IDs are configuration, never name searches."""

    index_file_id: str
    slot_file_ids: tuple[str, ...]
    owner_email: str
    service_account_email: str
    audience: str = "private"

    def __post_init__(self):
        import re

        if self.audience not in ("private", "public_viewer"):
            raise ValueError("Explicit private or public_viewer audience required.")

        ids = (self.index_file_id, *self.slot_file_ids)
        if (
            not isinstance(self.slot_file_ids, tuple)
            or len(self.slot_file_ids) < 2
            or len(set(ids)) != len(ids)
            or any(
                not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", i) for i in ids
            )
        ):
            raise ValueError("Register one index and at least two distinct workbook slot IDs.")
        if (
            not self.owner_email
            or "@" not in self.owner_email
            or not self.service_account_email.endswith(".iam.gserviceaccount.com")
            or self.owner_email == self.service_account_email
        ):
            raise ValueError("Explicit user owner and service-account editor are required.")


class GoogleSheetsTransport:
    """Registered My Drive slots with explicit private or link-Viewer publication.

    A SQL-backed reuse guard is mandatory. Generation-specific tab names prevent a
    delayed old values request from addressing replacement data in a reused file.
    Any ambiguous mutation blocks further delivery until terminal evidence is available.
    """

    _FIELDS = "id,mimeType,trashed,appProperties,description,driveId,capabilities(canEdit,canShare),permissions(id,type,role,emailAddress,allowFileDiscovery)"
    _MIME = "application/vnd.google-apps.spreadsheet"
    MAX_CELLS = 9_000_000  # Reserve headroom below Google's ten-million-cell hard limit.

    def __init__(
        self,
        *,
        drive,
        sheets,
        registration,
        reuse_guard,
        protected_file_ids,
        rows_per_request=500,
        request_pacer=None,
        retry_sleep=time.sleep,
    ):
        if not isinstance(registration, SheetsRegistration) or not callable(reuse_guard):
            raise ValueError("Explicit registration and durable reuse guard are required.")
        if type(rows_per_request) is not int or not 1 <= rows_per_request <= 1000:
            raise ValueError("Bounded row batches required.")
        self.drive, self.sheets = drive, sheets
        self.registration, self.reuse_guard = registration, reuse_guard
        self.protected = frozenset(protected_file_ids)
        if self.protected.intersection((registration.index_file_id, *registration.slot_file_ids)):
            raise ValueError("Protected configuration workbook cannot be an export destination.")
        self.batch_rows = rows_per_request
        self._retained = {}
        self._request_pacer = request_pacer or (lambda: None)
        self._retry_sleep = retry_sleep
        self.last_error = None
        self.quarantined = frozenset()
        self._verified = set()

    def prepare_generation(self, generation):
        # Final streams retain their physical export even after a newer selection.
        if any("metric" in t.columns for t in generation.tables):
            generation = compact_sheets_generation(generation)
        retained = False
        for item in generation.tables:
            for field in ("player_state", "aggregate_state", "current_period_state"):
                if field in item.columns:
                    index = item.columns.index(field)
                    retained |= any(
                        row[index] in ("final", "corrected_final", "final_unavailable")
                        for row in item.rows
                    )
        self._retained[generation.key] = retained
        return generation

    @classmethod
    def from_credentials(
        cls, *, credentials, registration, reuse_guard, protected_file_ids, timeout=30
    ):
        import google_auth_httplib2
        from googleapiclient.discovery import build
        import httplib2

        if type(timeout) is not int or not 1 <= timeout <= 60:
            raise ValueError("Google request timeout must be 1..60 seconds.")
        if (
            getattr(credentials, "service_account_email", None)
            != registration.service_account_email
        ):
            raise ValueError("Credentials must match the registered service account.")

        def client(api, version):
            http = google_auth_httplib2.AuthorizedHttp(
                credentials, http=httplib2.Http(timeout=timeout)
            )
            return build(api, version, http=http, cache_discovery=False, static_discovery=True)

        return cls(
            drive=client("drive", "v3"),
            sheets=client("sheets", "v4"),
            registration=registration,
            reuse_guard=reuse_guard,
            protected_file_ids=protected_file_ids,
            request_pacer=GoogleRequestPacer(registration.service_account_email),
        )

    def _execute(self, request):
        # Only idempotent GET requests retry. Mutations always execute exactly once.
        for attempt in range(3):
            self._request_pacer()
            try:
                return request.execute(num_retries=0)
            except Exception as exc:
                status = getattr(getattr(exc, "resp", None), "status", None)
                if (
                    getattr(request, "method", None) != "GET"
                    or status not in (429, 503)
                    or attempt == 2
                ):
                    self.last_error = google_error_details(request, exc)
                    raise
                self._retry_sleep(2**attempt)

    def _mutate(self, request):
        from kvk.services.new_source_delivery_service import (
            RemoteOutcomeUnknown,
            RemoteRequestRejected,
        )

        try:
            return self._execute(request)
        except Exception as exc:
            self.last_error = google_error_details(request, exc)
            logger.warning(
                "Google operation rejected/uncertain operation=%s status=%s reason=%s",
                *self.last_error.values(),
            )
            kind = (
                RemoteRequestRejected
                if self.last_error["status"] in (400, 401, 403, 404, 429)
                else RemoteOutcomeUnknown
            )
            raise kind("Google operation requires receipt inspection.") from exc

    def _identity(self, destination, key):
        import re

        if (
            destination.kind != "sheets"
            or destination.destination_id != self.registration.index_file_id
            or not re.fullmatch(r"[0-9a-f]{64}", key)
        ):
            raise ValueError(
                "Destination must be the registered index file ID and exact generation."
            )
        return hashlib.sha256(destination.destination_id.encode()).hexdigest()

    def _get(self, file_id):
        from kvk.services.new_source_delivery_service import DestinationSetupRequired

        instruction = (
            f"Create or restore dedicated workbook {file_id}, register its exact file ID, "
            f"and grant Editor access to {self.registration.service_account_email}."
        )
        try:
            file = self._execute(self.drive.files().get(fileId=file_id, fields=self._FIELDS))
        except Exception as exc:
            if getattr(getattr(exc, "resp", None), "status", None) in (403, 404):
                raise DestinationSetupRequired(instruction) from exc
            raise
        expected = {
            (self.registration.owner_email, "owner"),
            (self.registration.service_account_email, "writer"),
        }
        actual = {
            (p.get("emailAddress"), p.get("role"))
            for p in file.get("permissions", [])
            if p.get("type") == "user"
        }
        public = [p for p in file.get("permissions", []) if p.get("type") == "anyone"]
        public_ok = (
            self.registration.audience == "public_viewer"
            and len(public) == 1
            and public[0].get("role") == "reader"
            and public[0].get("allowFileDiscovery") is False
        )
        if (
            file.get("id") != file_id
            or file_id in self.protected
            or file.get("trashed")
            or file.get("mimeType") != self._MIME
            or file.get("driveId")
            or file.get("capabilities", {}).get("canEdit") is not True
            or len(file.get("permissions", [])) != 2 + int(public_ok)
            or actual != expected
        ):
            raise DestinationSetupRequired(
                instruction + " Verify the registered owner and remove other sharing."
            )
        return file

    def _private_file(self, file):
        """Revoke only the admitted public-reader permission, then re-read before writes."""
        if file["id"] in self.quarantined:
            raise SourceConflict("Quarantined workbook must never be written again.")
        for permission in file.get("permissions", []):
            if permission.get("type") == "anyone":
                if file.get("capabilities", {}).get("canShare") is not True:
                    raise SourceConflict("Service account cannot manage the registered audience.")
                self._mutate(
                    self.drive.permissions().delete(
                        fileId=file["id"], permissionId=permission["id"]
                    )
                )
        fresh = self._get(file["id"])
        if any(p.get("type") == "anyone" for p in fresh["permissions"]):
            raise SourceConflict("Private staging audience not established.")
        return fresh

    def _public_file(self, file):
        if file["id"] in self.quarantined:
            raise SourceConflict("Quarantined workbook cannot be published.")
        if not any(p.get("type") == "anyone" for p in file["permissions"]):
            if file.get("capabilities", {}).get("canShare") is not True:
                raise SourceConflict("Service account cannot publish Viewer access.")
            self._mutate(
                self.drive.permissions().create(
                    fileId=file["id"],
                    body={"type": "anyone", "role": "reader", "allowFileDiscovery": False},
                    fields="id",
                )
            )
        fresh = self._get(file["id"])
        if not any(p.get("type") == "anyone" for p in fresh["permissions"]):
            raise SourceConflict("Public Viewer audience not established.")

    @staticmethod
    def _tab(key, name):
        return key[:24] + "__" + name

    def _bound(self, destination, key, file, role):
        props = file.get("appProperties", {})
        if (
            props.get("k98Destination") != self._identity(destination, key)
            or props.get("k98Role") != role
        ):
            raise SourceConflict("Workbook is not bound to this registered destination.")
        return file

    def _index(self, destination, key):
        return self._bound(destination, key, self._get(self.registration.index_file_id), "index")

    @classmethod
    def partition_manifest(cls, manifest):
        """Pack bounded row slices; header and directory cells count toward every budget."""
        bins, current, cells = [], [], 0
        limit = cls.MAX_CELLS - 10_000
        for name, spec in sorted(manifest.items()):
            width, rows = spec["columns"], spec["rows"]
            if (
                type(width) is not int
                or not 1 <= width <= 18278
                or type(rows) is not int
                or rows < 0
            ):
                raise ValueError("Invalid manifest dimensions.")
            offset = 0
            while offset < rows or offset == 0:
                available = (limit - cells) // width - 1
                if available < max(1, min(rows - offset, 1)):
                    if not current:
                        raise ValueError("Table columns exceed workbook budget.")
                    bins.append(current)
                    current, cells = [], 0
                    continue
                count = min(rows - offset, available)
                piece = dict(
                    table=name,
                    offset=offset,
                    rows=count,
                    columns=width,
                    name=name + (f"_p{offset}" if offset else ""),
                )
                current.append(piece)
                cells += max(2, count + 1) * width
                offset += count
                if offset >= rows:
                    break
        if current:
            bins.append(current)
        if (sum(map(len, bins)) + 1) * 5 > 10_000:
            raise ValueError("Export directory exceeds bounded capacity.")
        return bins

    def _files(self, destination, key):
        found = []
        for id in self.registration.slot_file_ids:
            file = self._get(id)
            if file.get("appProperties", {}).get("k98Generation") == key:
                found.append(self._bound(destination, key, file, "generation"))
        if not found:
            raise SourceConflict("Generation has no registered parts.")
        manifest = json.loads(found[0]["description"])
        count = len(self.partition_manifest(manifest))
        if (
            len(found) != count
            or {f["appProperties"].get("k98Part") for f in found} != {str(i) for i in range(count)}
            or any(json.loads(f["description"]) != manifest for f in found)
        ):
            raise SourceConflict("Generation parts are incomplete or ambiguous.")
        return sorted(found, key=lambda f: int(f["appProperties"]["k98Part"]))

    def _file(self, destination, key):
        return self._files(destination, key)[0]

    def _pointer(self, index):
        return self._execute(
            self.sheets.spreadsheets()
            .values()
            .get(spreadsheetId=index["id"], range="Sheet1!A1:C1", valueRenderOption="FORMULA")
        ).get("values", [])

    def _bind(self, destination, key, file, role, manifest, part=0):
        self._mutate(
            self.drive.files().update(
                fileId=file["id"],
                body=dict(
                    appProperties=dict(
                        k98Destination=self._identity(destination, key),
                        k98Role=role,
                        k98Generation=key,
                        k98Retain=str(self._retained.get(key, True)),
                        k98Part=str(part),
                        k98Previous=file.get("appProperties", {}).get("k98Generation", "blank"),
                        k98Stage="preparing",
                    ),
                    description=json.dumps(manifest, sort_keys=True, separators=(",", ":")),
                ),
                fields="id",
            )
        )

    def _empty(self, file):
        props = self._execute(
            self.sheets.spreadsheets().get(spreadsheetId=file["id"], fields="sheets.properties")
        )
        sheets = props.get("sheets", [])
        if len(sheets) != 1 or sheets[0]["properties"]["title"] != "Sheet1":
            raise SourceConflict("Initial registration requires an empty dedicated workbook.")
        values = self._execute(
            self.sheets.spreadsheets()
            .values()
            .get(spreadsheetId=file["id"], range="Sheet1", valueRenderOption="FORMULA")
        )
        if values.get("values"):
            raise SourceConflict("Initial registration cannot overwrite existing workbook data.")

    def ensure_private(self, destination, key, manifest):
        from kvk.services.new_source_delivery_service import DestinationSetupRequired

        self._identity(destination, key)
        self.last_error = None
        self._verified.discard(key)
        if self.quarantined.intersection(self.registration.slot_file_ids):
            raise SourceConflict("Remove quarantined slots from destination registration.")
        if set(manifest) != {*KVK_EXPORT_SECTION_NAMES, "ALL_WINDOWS", "COMPARISONS"}:
            raise ValueError("Exactly twelve generation sections are required.")
        layout = self.partition_manifest(manifest)
        if len(layout) > len(self.registration.slot_file_ids):
            raise DestinationSetupRequired(
                f"This export needs {len(layout)} workbook slots per generation. "
                f"Register at least {2 * len(layout)} slots plus the index for current/staging reuse."
            )
        index = self._get(self.registration.index_file_id)
        files = [self._get(id) for id in self.registration.slot_file_ids]
        for f, role in [(index, "index"), *((f, "generation") for f in files)]:
            if f.get("appProperties"):
                self._bound(destination, key, f, role)
            else:
                self._empty(f)
        current = self._pointer(index)
        if current and (len(current) != 1 or len(current[0]) != 3):
            raise SourceConflict("Malformed current index requires reconciliation.")
        matches = [f for f in files if f.get("appProperties", {}).get("k98Generation") == key]
        replacing = not matches
        bound_parts = {}
        for file in matches:
            part = file["appProperties"].get("k98Part")
            if part not in {str(i) for i in range(len(layout))} or part in bound_parts:
                raise SourceConflict("Generation parts are incomplete or ambiguous.")
            if json.loads(file["description"]) != manifest:
                raise SourceConflict("Existing generation has another manifest.")
            bound_parts[part] = file
        missing = [str(i) for i in range(len(layout)) if str(i) not in bound_parts]
        if (
            matches
            and missing
            and (
                any(f["appProperties"].get("k98Stage") != "preparing" for f in matches)
                or (current and current[0][0] == key)
            )
        ):
            raise SourceConflict("Incomplete established generation requires reconciliation.")
        if missing:
            available = [f for f in files if not f.get("appProperties")]
            for candidate in files:
                if len(available) >= len(missing):
                    break
                props = candidate.get("appProperties", {})
                previous = props.get("k98Generation")
                if (
                    not previous
                    or previous == key
                    or props.get("k98Retain") != "False"
                    or (current and (current[0][0] == previous or candidate["id"] in current[0][2]))
                ):
                    continue
                if self.reuse_guard(destination, previous) is True:
                    available.append(candidate)
            if len(available) < len(missing):
                raise DestinationSetupRequired(
                    f"No reusable slot set: need {len(missing)}, have {len(available)}. "
                    "Retain current, final and referenced generations. Create dedicated workbooks, "
                    "grant the registered service account Editor access and register their file IDs."
                )
            for part, file in zip(missing, available[: len(missing)], strict=True):
                file = self._private_file(file)
                self._bind(destination, key, file, "generation", manifest, int(part))
                bound_parts[part] = self._get(file["id"])
        chosen = [bound_parts[str(i)] for i in range(len(layout))]
        for part, (file, pieces) in enumerate(zip(chosen, layout, strict=True)):
            self._private_file(self._get(file["id"]))
            props = self._execute(
                self.sheets.spreadsheets().get(spreadsheetId=file["id"], fields="sheets.properties")
            )
            existing = {x["properties"]["title"]: x["properties"] for x in props.get("sheets", [])}
            specs = [(p["name"], p["rows"], p["columns"]) for p in pieces]
            if part == 0:
                specs.append(("DIRECTORY", sum(map(len, layout)), 5))
            intended = {self._tab(key, name) for name, _, _ in specs}
            if set(existing) != intended:
                if not replacing:
                    previous = file.get("appProperties", {}).get("k98Previous")
                    resumable = file.get("appProperties", {}).get("k98Stage") == "preparing"
                    if previous == "blank":
                        resumable &= set(existing) == {"Sheet1"}
                    else:
                        resumable &= (
                            bool(previous)
                            and all(title.startswith(self._tab(previous, "")) for title in existing)
                            and self.reuse_guard(destination, previous) is True
                        )
                    if not resumable:
                        raise SourceConflict("Unexpected generation tabs require reconciliation.")
                # Shrink only retired/blank grids, keep a sheet alive, then add and delete.
                unfreeze = [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": p["sheetId"],
                                "gridProperties": {"frozenRowCount": 0, "frozenColumnCount": 0},
                            },
                            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
                        }
                    }
                    for p in existing.values()
                ]
                shrink = [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": p["sheetId"],
                                "gridProperties": {
                                    "rowCount": 1,
                                    "columnCount": 1,
                                },
                            },
                            "fields": "gridProperties.rowCount,gridProperties.columnCount",
                        }
                    }
                    for p in existing.values()
                ]
                additions = [
                    {
                        "addSheet": {
                            "properties": dict(
                                title=self._tab(key, name),
                                gridProperties=dict(
                                    rowCount=max(2, rows + 1),
                                    columnCount=columns,
                                    frozenRowCount=1,
                                ),
                            )
                        }
                    }
                    for name, rows, columns in specs
                ]
                deletes = [{"deleteSheet": {"sheetId": p["sheetId"]}} for p in existing.values()]
                self._mutate(
                    self.sheets.spreadsheets().batchUpdate(
                        spreadsheetId=file["id"],
                        body={"requests": unfreeze + shrink + additions + deletes},
                    )
                )
            self._mutate(
                self.drive.files().update(
                    fileId=file["id"], body={"appProperties": {"k98Stage": "built"}}, fields="id"
                )
            )
        directory = self._directory(chosen, key, layout)
        for offset in range(0, len(directory), self.batch_rows):
            self._mutate(
                self.sheets.spreadsheets()
                .values()
                .update(
                    spreadsheetId=chosen[0]["id"],
                    range=f"'{self._tab(key, 'DIRECTORY')}'!A{offset+1}",
                    valueInputOption="RAW",
                    body={"values": directory[offset : offset + self.batch_rows]},
                )
            )
        if not index.get("appProperties"):
            self._bind(destination, key, index, "index", {})

    def _directory(self, files, key, layout):
        rows = [["section", "first_data_row", "data_rows", "generation", "url"]]
        for file, pieces in zip(files, layout, strict=True):
            props = self._execute(
                self.sheets.spreadsheets().get(spreadsheetId=file["id"], fields="sheets.properties")
            )
            ids = {p["properties"]["title"]: p["properties"]["sheetId"] for p in props["sheets"]}
            for piece in pieces:
                sid = ids[self._tab(key, piece["name"])]
                rows.append(
                    [
                        piece["table"],
                        str(piece["offset"] + 1),
                        str(piece["rows"]),
                        key,
                        f"https://docs.google.com/spreadsheets/d/{file['id']}/edit#gid={sid}",
                    ]
                )
        return rows

    @staticmethod
    def _column(number):
        result = ""
        while number:
            number, rem = divmod(number - 1, 26)
            result = chr(65 + rem) + result
        return result

    def write_range(self, destination, key, name, cell, values, *, value_input_option):
        files = self._files(destination, key)
        manifest = json.loads(files[0]["description"])
        if cell != "A1" or value_input_option != "RAW" or name not in manifest:
            raise ValueError("Only manifest-bound RAW ranges are writable.")
        spec = manifest[name]
        candidate = ExportTable(name, tuple(values[0]), tuple(tuple(row) for row in values[1:]))
        if (
            len(candidate.rows) != spec["rows"]
            or len(candidate.columns) != spec["columns"]
            or candidate.sha256 != spec["sha256"]
        ):
            raise SourceConflict("Write does not match immutable generation.")
        for file, pieces in zip(files, self.partition_manifest(manifest), strict=True):
            if file["id"] in self.quarantined or any(
                p.get("type") == "anyone" for p in file["permissions"]
            ):
                raise SourceConflict("Private, non-quarantined ranges required for bulk writes.")
            for piece in pieces:
                if piece["table"] != name:
                    continue
                payload = [
                    values[0],
                    *values[piece["offset"] + 1 : piece["offset"] + piece["rows"] + 1],
                ]
                for offset in range(0, len(payload), self.batch_rows):
                    self._mutate(
                        self.sheets.spreadsheets()
                        .values()
                        .update(
                            spreadsheetId=file["id"],
                            range=f"'{self._tab(key, piece['name'])}'!A{offset + 1}",
                            valueInputOption="RAW",
                            body={"values": payload[offset : offset + self.batch_rows]},
                        )
                    )

    def _read_rectangle(self, file_id, title, rows, columns):
        return self._read_rectangles(file_id, {title: (rows, columns)})[title]

    def _read_rectangles(self, file_id, rectangles):
        values = {title: [] for title in rectangles}
        pending, cells = [], 0

        def flush():
            if not pending:
                return
            response = self._execute(
                self.sheets.spreadsheets()
                .values()
                .batchGet(
                    spreadsheetId=file_id,
                    ranges=[r[0] for r in pending],
                    valueRenderOption="FORMULA",
                )
            )
            blocks = response.get("valueRanges", [])
            if len(blocks) != len(pending):
                raise SourceConflict("Readback batch is incomplete.")
            for (a1, title, height, width), item in zip(pending, blocks, strict=True):
                if item.get("range", "").replace("'", "") != a1.replace("'", ""):
                    raise SourceConflict("Readback range identity differs.")
                block = item.get("values", [])
                if len(block) > height or any(len(row) > width for row in block):
                    raise SourceConflict("Provider rectangle exceeds manifest.")
                values[title].extend([*row, *([""] * (width - len(row)))] for row in block)
                values[title].extend([[""] * width for _ in range(height - len(block))])
            pending.clear()

        for title, (rows, columns) in rectangles.items():
            step = min(self.batch_rows, max(1, 50_000 // columns))
            for start in range(1, rows + 1, step):
                end = min(start + step - 1, rows)
                size = (end - start + 1) * columns
                if cells + size > 50_000 or len(pending) == 16:
                    flush()
                    cells = 0
                pending.append(
                    (
                        f"'{title}'!A{start}:{self._column(columns)}{end}",
                        title,
                        end - start + 1,
                        columns,
                    )
                )
                cells += size
        flush()
        return values

    def verify(self, destination, key):
        self._verified.discard(key)
        files = self._files(destination, key)
        manifest = json.loads(files[0]["description"])
        layout = self.partition_manifest(manifest)
        combined, headers = {n: [] for n in manifest}, {}
        actual_directory = None
        for part, (file, pieces) in enumerate(zip(files, layout, strict=True)):
            remote = self._execute(
                self.sheets.spreadsheets().get(spreadsheetId=file["id"], fields="sheets.properties")
            )
            properties = {p["properties"]["title"]: p["properties"] for p in remote["sheets"]}
            expected = {self._tab(key, p["name"]) for p in pieces}
            if part == 0:
                expected.add(self._tab(key, "DIRECTORY"))
            if set(properties) != expected:
                raise SourceConflict("Remote section inventory differs from generation.")
            rectangles = {
                self._tab(key, p["name"]): (max(2, p["rows"] + 1), p["columns"]) for p in pieces
            }
            if part == 0:
                rectangles[self._tab(key, "DIRECTORY")] = (sum(map(len, layout)) + 1, 5)
            readback = self._read_rectangles(file["id"], rectangles)
            if part == 0:
                actual_directory = readback[self._tab(key, "DIRECTORY")]
            if part == 0:
                grid = properties[self._tab(key, "DIRECTORY")]["gridProperties"]
                if (
                    grid["rowCount"] != max(2, sum(map(len, layout)) + 1)
                    or grid["columnCount"] != 5
                ):
                    raise SourceConflict("Directory dimensions differ from generation.")
            for piece in pieces:
                title = self._tab(key, piece["name"])
                grid = properties[title]["gridProperties"]
                row_count = max(2, piece["rows"] + 1)
                if grid["rowCount"] != row_count or grid["columnCount"] != piece["columns"]:
                    raise SourceConflict("Remote grid dimensions differ from generation.")
                values = readback[title]
                name = piece["table"]
                if name in headers and headers[name] != values[0]:
                    raise SourceConflict("Partition headers differ.")
                headers[name] = values[0]
                if not piece["rows"] and any(values[1]):
                    raise SourceConflict("Unexpected data in empty section.")
                combined[name].extend(tuple(row) for row in values[1 : piece["rows"] + 1])
        directory = self._directory(files, key, layout)
        if actual_directory != directory:
            raise SourceConflict("Generation directory differs from registered parts.")
        result = {}
        for name, rows in combined.items():
            item = ExportTable(name, tuple(headers[name]), tuple(rows))
            result[name] = dict(sha256=item.sha256, rows=len(rows), columns=len(item.columns))
        if result == manifest:
            self._verified.add(key)
        return result

    def publish_current(self, destination, key, fence):
        if key not in self._verified:
            raise SourceConflict("Verified generation required before audience publication.")
        file, index = self._file(destination, key), self._index(destination, key)
        current = self._pointer(index)
        if type(fence) is not int or fence <= 0:
            raise SourceConflict("Explicit positive fence required.")
        if current and (
            len(current) != 1
            or len(current[0]) != 3
            or not current[0][1].isdecimal()
            or (int(current[0][1]) >= fence and current[0][0] != key)
            or int(current[0][1]) > fence
        ):
            raise SourceConflict("A newer or conflicting remote fence is current.")
        # Link includes the exact generation tab. Retired URLs are not archival guarantees.
        props = self._execute(
            self.sheets.spreadsheets().get(spreadsheetId=file["id"], fields="sheets.properties")
        )
        sid = next(
            p["properties"]["sheetId"]
            for p in props["sheets"]
            if p["properties"]["title"] == self._tab(key, "DIRECTORY")
        )
        url = f"https://docs.google.com/spreadsheets/d/{file['id']}/edit#gid={sid}"
        if self.registration.audience == "public_viewer":
            for part in self._files(destination, key):
                self._public_file(part)
        self._mutate(
            self.sheets.spreadsheets()
            .values()
            .update(
                spreadsheetId=index["id"],
                range="Sheet1!A1:C1",
                valueInputOption="RAW",
                body={"values": [[key, str(fence), url]]},
            )
        )
        if self.registration.audience == "public_viewer":
            self._public_file(self._get(index["id"]))
        return url

    def reconcile(self, destination, claim):
        original = json.loads(claim.receipt)
        key = original["export_key"]
        try:
            file, index = self._file(destination, key), self._index(destination, key)
            if self.registration.audience == "public_viewer" and any(
                not any(p.get("type") == "anyone" for p in f["permissions"])
                for f in [index, *self._files(destination, key)]
            ):
                return "unknown", None
            values = self._pointer(index)
            if (
                not values
                or len(values) != 1
                or len(values[0]) != 3
                or values[0][:2] != [key, str(claim.fence)]
            ):
                return "unknown", None
            if self.verify(destination, key) != json.loads(file["description"]):
                return "unknown", None
            props = self._execute(
                self.sheets.spreadsheets().get(spreadsheetId=file["id"], fields="sheets.properties")
            )
            sid = next(
                p["properties"]["sheetId"]
                for p in props["sheets"]
                if p["properties"]["title"] == self._tab(key, "DIRECTORY")
            )
            expected = f"https://docs.google.com/spreadsheets/d/{file['id']}/edit#gid={sid}"
            if values[0][2] != expected:
                return "unknown", None
        except SourceConflict:
            return "unknown", None
        from kvk.services.new_source_delivery_service import _receipt

        return "confirmed", _receipt(
            key,
            publication_id=claim.selection.publication_id,
            selection_version=claim.selection.selection_version,
            export_complete=True,
            remote_id=expected,
            phase="published",
        )
