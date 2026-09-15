"""Request-level SDK adapters for an already owned account/resource claim.

Dedicated SDK clients must never be shared across workers. No fallback client,
local quota approximation, blind mutation retry or SQL transaction surrounds I/O.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from types import SimpleNamespace
from urllib.parse import urlparse

from services.export_request_budget import BudgetCompletionUnknown


class ProviderOutcomeUnknown(BudgetCompletionUnknown):
    """Retain the durable claim until authoritative request reconciliation."""


_provider = ContextVar("export_request_provider", default=None)


def current_provider():
    return _provider.get()


@contextmanager
def use_provider(adapter):
    token = _provider.set(adapter)
    try:
        yield adapter
    finally:
        _provider.reset(token)


def _feedback(error):
    response = getattr(error, "resp", None)
    if response is None:
        response = getattr(error, "response", None)
    if response is None:
        return error
    status = getattr(response, "status", None) or getattr(response, "status_code", None)
    headers = getattr(response, "headers", response)

    class Response(dict):
        pass

    result = Response()
    result.status = status
    if hasattr(headers, "get"):
        result["retry-after"] = headers.get("retry-after") or headers.get("Retry-After")
    return SimpleNamespace(resp=result)


class ProviderAdapter:
    def __init__(self, *, budget, authorize, destinations):
        self.budget, self.authorize = budget, authorize
        self.destinations = frozenset(destinations)
        if not self.destinations:
            raise ValueError("Registered destinations are required.")
        self.uncertain = False

    def _destination(self, uri, *, mutation):
        parsed = urlparse(uri)
        if (
            parsed.scheme != "https"
            or parsed.hostname
            not in {"sheets.googleapis.com", "www.googleapis.com", "drive.googleapis.com"}
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        ):
            raise ValueError("Unregistered provider endpoint.")
        parts = parsed.path.strip("/").split("/")
        for marker in ("spreadsheets", "files"):
            if marker in parts:
                index = parts.index(marker) + 1
                if index < len(parts):
                    destination = parts[index].split(":", 1)[0]
                    if destination not in self.destinations:
                        raise ValueError(
                            "Request destination is outside the admitted resource set."
                        )
                    return destination
        # Creation/listing belongs to preparation admission, not an output job.
        raise ValueError("Request requires separate discovery/provisioning admission.")

    def call(self, request, *, mutation, destination):
        if self.uncertain:
            raise ProviderOutcomeUnknown("Provider claim requires reconciliation.")
        if destination not in self.destinations:
            raise ValueError("Destination was not admitted.")
        self.authorize(mutation=mutation)
        try:
            self.budget()
        except Exception as exc:
            self.uncertain = True
            raise ProviderOutcomeUnknown(
                "Request reservation outcome requires reconciliation."
            ) from exc
        # Recheck after an arbitrarily long cooldown, before a request escapes.
        self.authorize(mutation=mutation)
        error = None
        try:
            return request()
        except Exception as exc:
            error = exc
            if mutation:
                self.uncertain = True
                raise ProviderOutcomeUnknown("Mutation outcome requires reconciliation.") from exc
            raise
        finally:
            try:
                if error is not None:
                    self.budget.rejected(_feedback(error))
                self.budget.completed()
            except Exception as exc:
                self.uncertain = True
                raise ProviderOutcomeUnknown("Request checkpoint requires reconciliation.") from exc

    def execute(self, request):
        method = request.method.upper()
        mutation = method not in {"GET", "HEAD", "OPTIONS"}
        destination = self._destination(request.uri, mutation=mutation)
        return self.call(
            lambda: request.execute(num_retries=0), mutation=mutation, destination=destination
        )

    def bind_gspread(self, http_client):
        """Wrap the dedicated HTTPClient request, below multi-request SDK methods."""
        from gspread.http_client import BackOffHTTPClient

        if isinstance(http_client, BackOffHTTPClient):
            raise ValueError("SDK backoff must not bypass common durable request pacing.")
        if getattr(http_client, "_export_admission_bound", False):
            raise ValueError("SDK client already belongs to an export claim.")
        original = http_client.request

        def request(method, endpoint, *args, **kwargs):
            mutation = method.upper() not in {"GET", "HEAD", "OPTIONS"}
            destination = self._destination(endpoint, mutation=mutation)
            return self.call(
                lambda: original(method, endpoint, *args, **kwargs),
                mutation=mutation,
                destination=destination,
            )

        http_client.request = request
        http_client._export_admission_bound = True
        return http_client


class LegacyProviderJob:
    """Deliver an entirely captured tab plan using a dedicated Sheets SDK client.

    All title resolution and output transformation happens before this adapter.
    Existing/public outputs are never described as privately staged. The transport
    factory must return (Sheets service, Drive service), without provider I/O.
    """

    def __init__(self, clients):
        self.clients = clients

    def __call__(self, job, claim, dal, budget, stop, payload):
        from collections import defaultdict
        import hashlib
        import json

        from services.legacy_export_snapshot_service import LegacySnapshot, SnapshotUnavailable

        snapshot = LegacySnapshot.load(payload)
        metadata = snapshot.metadata()
        config = metadata["config"]
        if metadata["consumer"] != job["ConsumerKind"] or hashlib.sha256(payload).digest() != bytes(
            job["InputHash"]
        ):
            raise SnapshotUnavailable("Job differs from its immutable snapshot.")
        outputs = config["outputs"]
        sections = {s.name: s for s in snapshot.sections()}
        destinations = tuple(sorted(set(config["destinations"])))
        if not outputs or {o["file_id"] for o in outputs} != set(destinations):
            raise SnapshotUnavailable("Complete registered output plan required.")
        if len({(o["file_id"], o["tab"]) for o in outputs}) != len(outputs):
            raise SnapshotUnavailable("Duplicate output tab identity.")
        # RAW-ready values are captured, including headers. No live SQL/parser.
        prepared = []
        for output in outputs:
            section = sections[output["section"]]
            values = [list(section.columns), *(list(row) for row in section.rows)]
            if any(
                v is not None and type(v) not in (str, int, float, bool)
                for row in values
                for v in row
            ):
                raise SnapshotUnavailable(
                    "Provider values must be prepared before durable capture."
                )
            if type(output["grid_id"]) is not int or output["grid_id"] < 0:
                raise SnapshotUnavailable("Invalid captured grid identity.")
            for formatting in output.get("format_requests", []):
                if set(formatting) == {"repeatCell"}:
                    instruction = formatting["repeatCell"]
                    if (
                        instruction.get("range", {}).get("sheetId") != output["grid_id"]
                        or instruction.get("fields") != "userEnteredFormat.numberFormat"
                    ):
                        raise SnapshotUnavailable("Formatting escapes its captured grid.")
                elif set(formatting) == {"updateSheetProperties"}:
                    instruction = formatting["updateSheetProperties"]
                    if (
                        instruction.get("properties", {}).get("sheetId") != output["grid_id"]
                        or instruction.get("fields") != "index"
                        or set(instruction["properties"]) != {"sheetId", "index"}
                    ):
                        raise SnapshotUnavailable("Tab ordering escapes its captured identity.")
                else:
                    raise SnapshotUnavailable("Unsupported captured formatting operation.")
            prepared.append((output, values))
        sheets, drive = self.clients(job)
        adapter = ProviderAdapter(
            budget=budget,
            authorize=lambda **kw: dal.authorize(claim, **kw),
            destinations=destinations,
        )

        def execute(request):
            if stop.is_set():
                raise InterruptedError("Export admission stopped.")
            return adapter.execute(request)

        audiences = {}
        grids = {}
        for file_id in destinations:
            permissions = execute(
                drive.permissions().list(
                    fileId=file_id, fields="permissions(type,role),nextPageToken"
                )
            )
            if permissions.get("nextPageToken"):
                raise SnapshotUnavailable("Complete ACL readback is required.")
            public = [
                p for p in permissions.get("permissions", []) if p["type"] in {"anyone", "domain"}
            ]
            if any(p["type"] != "anyone" or p["role"] != "reader" for p in public):
                raise SnapshotUnavailable("Unapproved output audience.")
            audiences[file_id] = "public_viewer" if public else "private"
            response = execute(
                sheets.spreadsheets().get(spreadsheetId=file_id, fields="sheets.properties")
            )
            grids[file_id] = response.get("sheets", [])
        if len(set(audiences.values())) != 1:
            raise SnapshotUnavailable(
                "Mixed output audiences require an explicit publication plan."
            )
        audience = next(iter(audiences.values()))
        # Resolve all conflicts before the first mutation/attempt. Checking one
        # tab at a time would partially overwrite an earlier valid destination.
        for output, values in prepared:
            existing = [g["properties"] for g in grids[output["file_id"]]]
            if any(
                (g["title"] == output["tab"]) != (g["sheetId"] == output["grid_id"])
                for g in existing
            ):
                raise SnapshotUnavailable("Captured tab identity conflicts with provider metadata.")
        grouped = defaultdict(list)
        for output, values in prepared:
            grouped[output["file_id"]].append((output, values))
        parts = []
        for file_id in destinations:
            plan = grouped[file_id]
            parts.append(
                dict(
                    file_id=file_id,
                    role="output",
                    manifest_hash=hashlib.sha256(
                        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
                    ).hexdigest(),
                    grids=len(plan),
                    rows=sum(len(v) for _, v in plan),
                    cells=sum(len(v) * len(v[0]) for _, v in plan),
                )
            )
        manifest = dict(
            export_key=bytes(job["InputHash"]).hex(), preparation_id=metadata["preparation_id"]
        )
        attempt = dal.begin_attempt(claim, manifest, parts)
        for output, values in prepared:
            file_id, tab, grid_id = output["file_id"], output["tab"], output["grid_id"]
            existing = [g["properties"] for g in grids[file_id]]
            matches = [g for g in existing if g["title"] == tab]
            if matches and matches[0]["sheetId"] != grid_id:
                raise SnapshotUnavailable(
                    "Captured tab identity no longer matches provider metadata."
                )
            if not matches:
                if any(g["sheetId"] == grid_id for g in existing):
                    raise SnapshotUnavailable("Captured grid ID belongs to another tab.")
                execute(
                    sheets.spreadsheets().batchUpdate(
                        spreadsheetId=file_id,
                        body={
                            "requests": [
                                {
                                    "addSheet": {
                                        "properties": {
                                            "sheetId": grid_id,
                                            "title": tab,
                                            "gridProperties": {
                                                "rowCount": max(1, len(values)),
                                                "columnCount": len(values[0]),
                                            },
                                        }
                                    }
                                }
                            ]
                        },
                    )
                )
            else:
                dimensions = matches[0].get("gridProperties", {})
                execute(
                    sheets.spreadsheets().batchUpdate(
                        spreadsheetId=file_id,
                        body={
                            "requests": [
                                {
                                    "updateSheetProperties": {
                                        "properties": {
                                            "sheetId": grid_id,
                                            "gridProperties": {
                                                "rowCount": max(
                                                    dimensions.get("rowCount", 0), len(values)
                                                ),
                                                "columnCount": max(
                                                    dimensions.get("columnCount", 0), len(values[0])
                                                ),
                                            },
                                        },
                                        "fields": "gridProperties.rowCount,gridProperties.columnCount",
                                    }
                                }
                            ]
                        },
                    )
                )
            quoted = "'" + tab.replace("'", "''") + "'"
            execute(
                sheets.spreadsheets().values().clear(spreadsheetId=file_id, range=quoted, body={})
            )
            for offset in range(0, len(values), 500):
                execute(
                    sheets.spreadsheets()
                    .values()
                    .update(
                        spreadsheetId=file_id,
                        range=f"{quoted}!A{offset+1}",
                        valueInputOption="RAW",
                        body={"values": values[offset : offset + 500]},
                    )
                )
            if output.get("format_requests"):
                execute(
                    sheets.spreadsheets().batchUpdate(
                        spreadsheetId=file_id, body={"requests": output["format_requests"]}
                    )
                )
            readback = execute(
                sheets.spreadsheets()
                .values()
                .get(spreadsheetId=file_id, range=quoted, valueRenderOption="UNFORMATTED_VALUE")
            )
            actual = readback.get("values", [])
            normalize = lambda rows: [
                list(row) + [""] * (len(values[0]) - len(row)) for row in rows
            ]
            expected = [["" if v is None else v for v in row] for row in values]
            padded = normalize(actual) + [
                [""] * len(values[0]) for _ in range(max(0, len(expected) - len(actual)))
            ]
            if padded != expected:
                raise ProviderOutcomeUnknown(
                    "Full output readback differs; retain attempt and resources."
                )
        # Recheck audience after data writes; an external ACL change is uncertainty.
        for file_id in destinations:
            response = execute(
                drive.permissions().list(
                    fileId=file_id, fields="permissions(type,role),nextPageToken"
                )
            )
            public = [
                p for p in response.get("permissions", []) if p["type"] in {"anyone", "domain"}
            ]
            actual = "public_viewer" if public else "private"
            if (
                response.get("nextPageToken")
                or actual != audience
                or any(p["type"] != "anyone" or p["role"] != "reader" for p in public)
            ):
                raise ProviderOutcomeUnknown("Output audience changed during delivery.")
        dal.verified(claim, attempt, audience=audience)
        dal.publication_pending(claim, attempt)
        dal.confirm(
            claim,
            attempt,
            dict(
                export_key=manifest["export_key"],
                fence=claim.fence,
                attempt_id=attempt,
                files=list(destinations),
                audience=audience,
                remote_id="https://docs.google.com/spreadsheets/d/" + destinations[0],
            ),
        )
