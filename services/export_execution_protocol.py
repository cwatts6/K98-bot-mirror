"""Versioned, bounded export-authority messages and fixed provider operations.

No credentials, URLs, code, SQL or import paths are accepted on this boundary.
Validation happens again in the authority; a Bot-side check is not authorization.
"""

from dataclasses import dataclass
import hashlib
import json
import re
from urllib.parse import parse_qsl, unquote, urlsplit
from uuid import UUID

PROTOCOL_VERSION = 1
MAX_MESSAGE_BYTES = 16 * 1024 * 1024
CATALOGUE_SEED = hashlib.sha256(b"K98-S11-CATALOGUE-1").digest()
READ_OPERATIONS = frozenset(
    {
        "sheets.get",
        "sheets.values.get",
        "sheets.values.batchGet",
        "drive.files.get",
        "drive.permissions.list",
    }
)
MUTATION_OPERATIONS = frozenset(
    {
        "sheets.batchUpdate",
        "sheets.values.update",
        "sheets.values.clear",
        "drive.files.update",
        "drive.permissions.create",
        "drive.permissions.delete",
    }
)
ENROLLMENT_OPERATIONS = frozenset(
    {
        "sheets.create",
        "drive.permissions.create",
        "drive.files.get",
        "drive.permissions.list",
        "sheets.get",
        "sheets.values.batchGet",
    }
)


def enrollment_create_arguments(plan_id, ordinal):
    """One private, empty, one-cell grid; no arbitrary template or creation body."""
    uuid_text(plan_id)
    if type(ordinal) is not int or not 0 <= ordinal <= 16:
        raise ProtocolError("Enrollment ordinal must be between zero and sixteen.")
    return {
        "plan_id": plan_id,
        "ordinal": ordinal,
        "body": {
            "properties": {"title": f"K98 enrollment {plan_id} {ordinal}"},
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Sheet1",
                        "gridProperties": {"rowCount": 1, "columnCount": 1},
                    }
                }
            ],
        },
    }


class ProtocolError(ValueError):
    """The message is not a supported bounded authority request."""


def uuid_text(value):
    if not isinstance(value, str):
        raise ProtocolError("Canonical UUID required.")
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except (ValueError, AttributeError) as exc:
        raise ProtocolError("Canonical UUID required.") from exc
    return value


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("Duplicate message key.")
        result[key] = value
    return result


def encode(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError) as exc:
        raise ProtocolError("JSON message required.") from exc
    if not 0 < len(raw) <= MAX_MESSAGE_BYTES:
        raise ProtocolError("Message exceeds protocol bound.")
    return raw


def decode(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_MESSAGE_BYTES:
        raise ProtocolError("Message exceeds protocol bound.")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ProtocolError("Non-finite number.")),
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("Invalid JSON message.") from exc
    if not isinstance(value, dict):
        raise ProtocolError("Message object required.")
    return value


def catalogue_step(previous, stream_id, version, event_digest):
    """Fixed ASCII/binary hash chain, identical to the SQL proof-issue contract.

    UUID text sorts lexically, not by SQL Server's uniqueidentifier ordering.
    Stream versions/sealed digests bind all request membership without truncating
    old streams to fit a JSON receipt. This is an inventory seal, not finality.
    """
    uuid_text(stream_id)
    if (
        type(version) is not int
        or not 0 < version < 2**63
        or not isinstance(previous, bytes)
        or len(previous) != 32
        or not isinstance(event_digest, bytes)
        or len(event_digest) != 32
    ):
        raise ProtocolError("Exact closed-stream catalogue identity required.")
    return hashlib.sha256(
        previous + stream_id.encode("ascii") + f":{version}:".encode("ascii") + event_digest
    ).digest()


def proof_membership(raw):
    """Bounded v2 coverage receipt: all relevant history plus one fresh probe."""
    if not isinstance(raw, str) or len(raw.encode("utf-16-le")) > 65536:
        raise ProtocolError("Bounded proof membership required.")
    value = decode(raw.encode("utf-8"))
    if (
        set(value) != {"version", "targets", "history", "probe"}
        or type(value["version"]) is not int
        or value["version"] != 2
    ):
        raise ProtocolError("Versioned complete catalogue membership required.")
    targets, history, probe = value["targets"], value["history"], value["probe"]
    if (
        not isinstance(targets, list)
        or not 1 <= len(targets) <= 17
        or any(
            not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", v) for v in targets
        )
        or targets != sorted(set(targets))
        or not isinstance(history, dict)
        or set(history) != {"count", "sha256"}
        or type(history["count"]) is not int
        or not 0 <= history["count"] < 2**63
        or not isinstance(history["sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", history["sha256"])
        or not isinstance(probe, dict)
        or set(probe) != {"stream_id", "version"}
        or type(probe["version"]) is not int
        or not 0 < probe["version"] < 2**63
    ):
        raise ProtocolError("Exact targets, history seal and closed probe required.")
    uuid_text(probe["stream_id"])
    return value


def _rectangle(value):
    """The readback adapter requests explicit, bounded A1 rectangles in row order."""
    if not isinstance(value, str) or not 0 < len(value) <= 4096:
        raise ProtocolError("Bounded explicit readback rectangle required.")
    match = re.fullmatch(
        r"('(?:[^']|'')+'|[^'!]+)!([A-Z]+)([1-9][0-9]*):([A-Z]+)([1-9][0-9]*)", value
    )
    if match is None:
        raise ProtocolError("Explicit sheet and closed readback rectangle required.")
    title, first_col, first_row, last_col, last_row = match.groups()
    if title.startswith("'"):
        title = title[1:-1].replace("''", "'")

    def column(text):
        result = 0
        for character in text:
            result = result * 26 + ord(character) - ord("A") + 1
        return result

    start_col, end_col = column(first_col), column(last_col)
    start_row, end_row = int(first_row), int(last_row)
    if not 1 <= start_col <= end_col <= 18278 or not 1 <= start_row <= end_row <= 2**31 - 1:
        raise ProtocolError("Readback rectangle bounds differ.")
    return (title, start_col, start_row, end_col, end_row)


@dataclass(frozen=True)
class ProviderRequest:
    request_id: str
    stream_id: str
    operation: str
    target: str
    arguments_json: bytes

    @classmethod
    def parse(cls, message, *, enrollment=False):
        if not isinstance(message, dict) or set(message) != {
            "version",
            "request_id",
            "stream_id",
            "operation",
            "target",
            "arguments",
        }:
            raise ProtocolError("Exact request envelope required.")
        if type(message["version"]) is not int or message["version"] != PROTOCOL_VERSION:
            raise ProtocolError("Unsupported protocol version.")
        operation = message["operation"]
        operations = ENROLLMENT_OPERATIONS if enrollment else READ_OPERATIONS | MUTATION_OPERATIONS
        if not isinstance(operation, str) or operation not in operations:
            raise ProtocolError("Unsupported provider operation.")
        target = message["target"]
        if not isinstance(target, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", target):
            raise ProtocolError("Registered provider file identity required.")
        arguments = message["arguments"]
        if not isinstance(arguments, dict):
            raise ProtocolError("Provider arguments must be an object.")
        allowed = {
            "sheets.get": {"fields", "includeGridData"},
            "sheets.values.get": {"range", "valueRenderOption", "dateTimeRenderOption"},
            "sheets.values.batchGet": {"ranges", "valueRenderOption", "dateTimeRenderOption"},
            "sheets.values.update": {"range", "valueInputOption", "body"},
            "sheets.values.clear": {"range", "body"},
            "sheets.batchUpdate": {"body"},
            "drive.files.get": {"fields"},
            "drive.files.update": {"fields", "body"},
            "drive.permissions.list": {"fields", "pageSize", "pageToken"},
            "drive.permissions.create": {"fields", "body"},
            "drive.permissions.delete": {"permissionId"},
            "sheets.create": {"body", "ordinal", "plan_id"},
        }[operation]
        if enrollment and operation == "drive.permissions.create":
            allowed = allowed | {"sendNotificationEmail"}
        if not set(arguments) <= allowed:
            raise ProtocolError("Arguments escape the fixed operation contract.")
        for key in ("fields", "pageToken", "valueRenderOption", "dateTimeRenderOption"):
            if key in arguments and (
                not isinstance(arguments[key], str) or not 0 < len(arguments[key]) <= 4096
            ):
                raise ProtocolError("Bounded provider option required.")
        if "includeGridData" in arguments and type(arguments["includeGridData"]) is not bool:
            raise ProtocolError("Boolean grid-data option required.")
        if "pageSize" in arguments and (
            type(arguments["pageSize"]) is not int or not 1 <= arguments["pageSize"] <= 1000
        ):
            raise ProtocolError("Bounded permission page size required.")
        if operation.startswith("sheets.values.") and operation != "sheets.values.batchGet":
            if (
                not isinstance(arguments.get("range"), str)
                or not 0 < len(arguments["range"]) <= 4096
            ):
                raise ProtocolError("Bounded explicit range required.")
        if operation == "sheets.values.batchGet":
            ranges = arguments.get("ranges")
            if not isinstance(ranges, list) or not 1 <= len(ranges) <= 16:
                raise ProtocolError("Readback requires one through sixteen ranges.")
            rectangles = [_rectangle(value) for value in ranges]
            if (
                len(set(rectangles)) != len(rectangles)
                or sum((c2 - c1 + 1) * (r2 - r1 + 1) for _, c1, r1, c2, r2 in rectangles) > 50_000
            ):
                raise ProtocolError("Readback ranges overlap in identity or exceed the cell bound.")
        if operation == "sheets.values.update":
            if arguments.get("valueInputOption") != "RAW":
                raise ProtocolError("Only captured RAW values may be written.")
            body = arguments.get("body")
            if (
                not isinstance(body, dict)
                or set(body) != {"values"}
                or not isinstance(body["values"], list)
            ):
                raise ProtocolError("Exact RAW values body required.")
            if any(not isinstance(row, list) for row in body["values"]):
                raise ProtocolError("Rows must be arrays.")
            if any(
                v is not None and type(v) not in (str, int, float, bool)
                for row in body["values"]
                for v in row
            ):
                raise ProtocolError("Cells must be scalar values.")
        if operation == "sheets.values.clear" and arguments.get("body") != {}:
            raise ProtocolError("Clear body must be empty.")
        if operation == "sheets.create":
            uuid_text(target)
            if arguments != enrollment_create_arguments(
                arguments.get("plan_id"), arguments.get("ordinal")
            ):
                raise ProtocolError("Exact fixed enrollment creation required.")
        if operation == "drive.permissions.create" and enrollment:
            body = arguments.get("body")
            if (
                not isinstance(body, dict)
                or set(body) != {"type", "role", "emailAddress"}
                or (body["type"], body["role"]) != ("user", "writer")
                or not isinstance(body["emailAddress"], str)
                or not re.fullmatch(
                    r"[a-z0-9-]+@[a-z0-9-]+\.iam\.gserviceaccount\.com", body["emailAddress"]
                )
                or arguments.get("sendNotificationEmail") is not False
                or arguments.get("fields") != "id,type,role,emailAddress"
            ):
                raise ProtocolError(
                    "Enrollment allows only the exact service-account Editor grant."
                )
        elif operation == "drive.permissions.create" and arguments.get("body") != {
            "type": "anyone",
            "role": "reader",
            "allowFileDiscovery": False,
        }:
            raise ProtocolError("Only the registered public Viewer transition is supported.")
        if operation == "drive.permissions.delete":
            permission = arguments.get("permissionId")
            if not isinstance(permission, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{1,128}", permission
            ):
                raise ProtocolError("Exact verified permission identity required.")
        if operation == "drive.files.update":
            body = arguments.get("body")
            if not isinstance(body, dict) or not {"appProperties"} <= set(body) <= {
                "appProperties",
                "description",
            }:
                raise ProtocolError("Only generation properties/description may change.")
            if "description" in body and (
                not isinstance(body["description"], str)
                or len(body["description"].encode()) > 65536
            ):
                raise ProtocolError("Bounded manifest description required.")
            props = body["appProperties"]
            if not isinstance(props, dict) or any(
                not isinstance(k, str)
                or not k.startswith("k98")
                or (v is not None and not isinstance(v, str))
                or len(k) + len(v or "") > 124
                for k, v in props.items()
            ):
                raise ProtocolError("Bounded K98 properties required.")
        if operation == "sheets.batchUpdate":
            body = arguments.get("body")
            if (
                not isinstance(body, dict)
                or set(body) != {"requests"}
                or not isinstance(body["requests"], list)
                or not 1 <= len(body["requests"]) <= 1024
            ):
                raise ProtocolError("Bounded batch requests required.")
            allowed_batches = {
                "addSheet",
                "deleteSheet",
                "updateSheetProperties",
                "repeatCell",
                "sortRange",
                "deleteNamedRange",
                "deleteDeveloperMetadata",
            }
            if any(
                not isinstance(item, dict) or len(item) != 1 or not set(item) <= allowed_batches
                for item in body["requests"]
            ):
                raise ProtocolError("Unsupported batch operation.")
            for item in body["requests"]:
                operation_name, instruction = next(iter(item.items()))
                if not isinstance(instruction, dict):
                    raise ProtocolError("Batch instruction must be an object.")
                if operation_name == "deleteNamedRange" and (
                    set(instruction) != {"namedRangeId"}
                    or not isinstance(instruction["namedRangeId"], str)
                    or not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", instruction["namedRangeId"])
                ):
                    raise ProtocolError("Exact named-range identity required for retirement.")
                if operation_name == "deleteDeveloperMetadata":
                    data_filter = instruction.get("dataFilter")
                    lookup = (
                        data_filter.get("developerMetadataLookup")
                        if isinstance(data_filter, dict)
                        else None
                    )
                    if (
                        set(instruction) != {"dataFilter"}
                        or not isinstance(data_filter, dict)
                        or set(data_filter) != {"developerMetadataLookup"}
                        or not isinstance(lookup, dict)
                        or set(lookup) != {"metadataId"}
                        or type(lookup["metadataId"]) is not int
                        or not 0 <= lookup["metadataId"] < 2**31
                    ):
                        raise ProtocolError("Retirement metadata deletion requires one exact ID.")
                if operation_name == "repeatCell" and (
                    set(instruction) != {"range", "cell", "fields"}
                    or instruction["fields"] != "userEnteredFormat.numberFormat"
                    or not isinstance(instruction["cell"], dict)
                    or set(instruction["cell"]) != {"userEnteredFormat"}
                    or not isinstance(instruction["cell"]["userEnteredFormat"], dict)
                    or set(instruction["cell"]["userEnteredFormat"]) != {"numberFormat"}
                ):
                    raise ProtocolError("Only captured number formatting may repeat cells.")
        return cls(
            uuid_text(message["request_id"]),
            uuid_text(message["stream_id"]),
            operation,
            target,
            encode(arguments),
        )

    @property
    def mutation(self):
        return self.operation in MUTATION_OPERATIONS or self.operation == "sheets.create"

    @property
    def arguments(self):
        return decode(self.arguments_json)

    def message(self):
        return dict(
            version=PROTOCOL_VERSION,
            request_id=self.request_id,
            stream_id=self.stream_id,
            operation=self.operation,
            target=self.target,
            arguments=self.arguments,
        )


def validate_response(request, response):
    """Validate synchronous method results before a durable success event.

    The child must separately verify the exact HTTP status. This is not a general
    classifier for exceptions, timeouts, HTTP 202 or partially decoded responses.
    """
    if request.operation == "drive.permissions.delete":
        if response not in (None, "", {}):
            raise ProtocolError("Unexpected permission deletion response.")
        return
    if not isinstance(response, dict):
        raise ProtocolError("Complete synchronous response object required.")
    op = request.operation
    if op == "sheets.create":
        created_properties = response.get("properties")
        created_sheets = response.get("sheets")
        if (
            not isinstance(response.get("spreadsheetId"), str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", response["spreadsheetId"])
            or response["spreadsheetId"] == request.target
            or not isinstance(created_properties, dict)
            or created_properties.get("title") != request.arguments["body"]["properties"]["title"]
            or not isinstance(created_sheets, list)
            or len(created_sheets) != 1
            or not isinstance(created_sheets[0], dict)
            or not isinstance(created_sheets[0].get("properties"), dict)
            or type(created_sheets[0]["properties"].get("sheetId")) is not int
            or created_sheets[0]["properties"]["sheetId"] != 0
        ):
            raise ProtocolError("Complete fixed creation identity required.")
    if (
        op.startswith("sheets.")
        and op not in {"sheets.values.get", "sheets.create"}
        and response.get("spreadsheetId") != request.target
    ):
        raise ProtocolError("Response spreadsheet identity differs.")
    if op == "sheets.batchUpdate":
        if not isinstance(response.get("replies"), list) or len(response["replies"]) != len(
            request.arguments["body"]["requests"]
        ):
            raise ProtocolError("Incomplete batch reply membership.")
        for action, reply in zip(
            request.arguments["body"]["requests"], response["replies"], strict=True
        ):
            if not isinstance(reply, dict):
                raise ProtocolError("Complete batch reply object required.")
            if "deleteNamedRange" in action and reply != {}:
                raise ProtocolError("Unexpected named-range deletion reply.")
            if "deleteDeveloperMetadata" in action:
                metadata_reply = reply.get("deleteDeveloperMetadata")
                deleted = (
                    metadata_reply.get("deletedDeveloperMetadata")
                    if isinstance(metadata_reply, dict)
                    else None
                )
                expected_id = action["deleteDeveloperMetadata"]["dataFilter"][
                    "developerMetadataLookup"
                ]["metadataId"]
                if (
                    not isinstance(deleted, list)
                    or len(deleted) != 1
                    or not isinstance(deleted[0], dict)
                    or type(deleted[0].get("metadataId")) is not int
                    or deleted[0]["metadataId"] != expected_id
                ):
                    raise ProtocolError("Metadata deletion reply differs from the exact ID.")
    elif op == "sheets.values.batchGet":
        blocks = response.get("valueRanges")
        ranges = request.arguments["ranges"]
        if not isinstance(blocks, list) or len(blocks) != len(ranges):
            raise ProtocolError("Incomplete readback range membership.")
        for requested, block in zip(ranges, blocks, strict=True):
            if not isinstance(block, dict) or _rectangle(block.get("range")) != _rectangle(
                requested
            ):
                raise ProtocolError("Readback range identity/order differs.")
            _, c1, r1, c2, r2 = _rectangle(requested)
            values = block.get("values", [])
            if (
                block.get("majorDimension", "ROWS") != "ROWS"
                or not isinstance(values, list)
                or len(values) > r2 - r1 + 1
                or any(not isinstance(row, list) or len(row) > c2 - c1 + 1 for row in values)
                or any(
                    v is not None and type(v) not in (str, int, float, bool)
                    for row in values
                    for v in row
                )
            ):
                raise ProtocolError("Readback values exceed the exact row/column contract.")
    elif op == "sheets.values.update":
        if not isinstance(response.get("updatedRange"), str) or any(
            type(response.get(k)) is not int or response[k] < 0
            for k in ("updatedRows", "updatedColumns", "updatedCells")
        ):
            raise ProtocolError("Incomplete update response.")
    elif op == "sheets.values.clear":
        if not isinstance(response.get("clearedRange"), str):
            raise ProtocolError("Incomplete clear response.")
    elif op == "sheets.values.get":
        # ValueRange responses carry range/values, not spreadsheetId.
        if not isinstance(response.get("range"), str) or not isinstance(
            response.get("values", []), list
        ):
            raise ProtocolError("Incomplete range response.")
    elif op.startswith("drive.files."):
        if response.get("id") != request.target:
            raise ProtocolError("Response file identity differs.")
    elif op == "drive.permissions.list":
        if not isinstance(response.get("permissions", []), list):
            raise ProtocolError("Incomplete permission response.")
    elif op == "drive.permissions.create":
        if not isinstance(response.get("id"), str) or not response["id"]:
            raise ProtocolError("Missing created permission identity.")
    encode(response)


def from_http(*, method, uri, body, stream_id, request_id, params=None):
    """Translate known SDK requests into typed actions; no URL crosses IPC."""
    parts = urlsplit(uri)
    if (
        parts.scheme != "https"
        or parts.hostname
        not in {"sheets.googleapis.com", "www.googleapis.com", "drive.googleapis.com"}
        or parts.port not in (None, 443)
        or parts.username
        or parts.password
        or parts.fragment
    ):
        raise ProtocolError("Unregistered provider endpoint.")
    path = parts.path
    method = method.upper()
    routes = [
        ("GET", r"/v4/spreadsheets/([A-Za-z0-9_-]+)", "sheets.get"),
        ("GET", r"/v4/spreadsheets/([A-Za-z0-9_-]+)/values:batchGet", "sheets.values.batchGet"),
        ("POST", r"/v4/spreadsheets/([A-Za-z0-9_-]+):batchUpdate", "sheets.batchUpdate"),
        ("GET", r"/v4/spreadsheets/([A-Za-z0-9_-]+)/values/(.+)", "sheets.values.get"),
        ("PUT", r"/v4/spreadsheets/([A-Za-z0-9_-]+)/values/(.+)", "sheets.values.update"),
        ("POST", r"/v4/spreadsheets/([A-Za-z0-9_-]+)/values/(.+):clear", "sheets.values.clear"),
        ("GET", r"/drive/v3/files/([A-Za-z0-9_-]+)", "drive.files.get"),
        ("PATCH", r"/drive/v3/files/([A-Za-z0-9_-]+)", "drive.files.update"),
        ("GET", r"/drive/v3/files/([A-Za-z0-9_-]+)/permissions", "drive.permissions.list"),
        ("POST", r"/drive/v3/files/([A-Za-z0-9_-]+)/permissions", "drive.permissions.create"),
        (
            "DELETE",
            r"/drive/v3/files/([A-Za-z0-9_-]+)/permissions/([A-Za-z0-9_-]+)",
            "drive.permissions.delete",
        ),
    ]
    selected = None
    for verb, pattern, operation in routes:
        match = re.fullmatch(pattern, path)
        if verb == method and match:
            selected = operation, match
            break
    if selected is None:
        raise ProtocolError("Unregistered SDK operation; no fallback request.")
    operation, match = selected
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    arguments = _object(
        (k, v) for k, v in pairs if operation != "sheets.values.batchGet" or k != "ranges"
    )
    if operation == "sheets.values.batchGet":
        ranges = [v for k, v in pairs if k == "ranges"]
        if ranges:
            arguments["ranges"] = ranges
    if params:
        if set(arguments) & set(params):
            raise ProtocolError("Duplicate URL/argument keys.")
        arguments.update(params)
    for key, allowed in {"alt": {"json"}, "prettyPrint": {"false", "true"}}.items():
        if key in arguments:
            if arguments.pop(key) not in allowed:
                raise ProtocolError("Unsupported representation.")
    if "includeGridData" in arguments and isinstance(arguments["includeGridData"], str):
        if arguments["includeGridData"] not in {"true", "false"}:
            raise ProtocolError("Boolean grid-data option required.")
        arguments["includeGridData"] = arguments["includeGridData"] == "true"
    if "pageSize" in arguments and isinstance(arguments["pageSize"], str):
        if not arguments["pageSize"].isdecimal():
            raise ProtocolError("Integer page size required.")
        arguments["pageSize"] = int(arguments["pageSize"])
    if operation.startswith("sheets.values.") and operation != "sheets.values.batchGet":
        if "range" in arguments:
            raise ProtocolError("Range must occur only in the fixed request path.")
        arguments["range"] = unquote(match[2])
    if operation == "drive.permissions.delete":
        if "permissionId" in arguments:
            raise ProtocolError("Permission identity must occur only in the request path.")
        arguments["permissionId"] = match[2]
    if body is not None:
        if isinstance(body, str):
            body = body.encode()
        arguments["body"] = decode(body) if isinstance(body, bytes) else body
    return ProviderRequest.parse(
        dict(
            version=1,
            request_id=request_id,
            stream_id=stream_id,
            operation=operation,
            target=match[1],
            arguments=arguments,
        )
    )
