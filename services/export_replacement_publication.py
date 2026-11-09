"""Reconstruct retained content from private publication evidence, without I/O."""

from contextlib import closing
from copy import deepcopy
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_execution_protocol import ProviderRequest, decode
from services.legacy_export_snapshot_service import OutputSection, output_digest


def publication_records(dal, store, stream_id):
    """Caller first verifies the complete closed stream and every private event."""
    result = []
    with closing(dal.request_ids(stream_id)) as identities:
        for identifier in identities:
            request, events = dal.read_request(identifier)
            if events[-1]["State"] == "not_sent":
                continue
            if events[-1]["State"] != "succeeded":
                raise SourceConflict("Publication contains an unverified provider result.")
            payload = decode(
                store.read_reference(request["PayloadReference"], request["PayloadHash"])
            )
            event = events[-1]
            response = decode(
                store.read_reference(event["EvidenceReference"], event["EvidenceHash"])
            )
            result.append((ProviderRequest.parse(payload), response["response"]))
    return result


def legacy_content(records, mappings, expected_hash):
    """Accept only the existing clear/contiguous RAW chunks/exact readback grammar."""
    sections, active, completed, grids = [], None, set(), {}
    for request, response in records:
        args = request.arguments
        if request.operation == "sheets.get":
            for sheet in response.get("sheets", []):
                props = sheet["properties"]
                grids[request.target, props["sheetId"]] = props["title"]
        elif request.operation == "sheets.values.clear":
            if active is not None:
                raise SourceConflict("Retained output has no complete readback.")
            match = re.fullmatch(r"'((?:[^']|'')+)'", args.get("range", ""))
            if match is None:
                raise SourceConflict("Exact whole-tab clear is required.")
            tab = match[1].replace("''", "'")
            key = (request.target, tab)
            if key in completed:
                raise SourceConflict("A verified output was overwritten again.")
            active = dict(file=request.target, tab=tab, quoted=args["range"], values=[])
        elif request.operation == "sheets.values.update":
            if (
                active is None
                or request.target != active["file"]
                or args.get("range") != active["quoted"] + "!A" + str(len(active["values"]) + 1)
                or args.get("valueInputOption") != "RAW"
                or not isinstance(args.get("body", {}).get("values"), list)
                or not 1 <= len(args["body"]["values"]) <= 500
            ):
                raise SourceConflict(
                    "Retained output chunks are missing, reordered or overlapping."
                )
            active["values"].extend(deepcopy(args["body"]["values"]))
        elif request.operation == "sheets.values.get":
            if (
                active is None
                or request.target != active["file"]
                or args.get("range") != active["quoted"]
                or args.get("valueRenderOption") != "UNFORMATTED_VALUE"
                or not active["values"]
            ):
                raise SourceConflict("Retained readback does not cover its complete output.")
            values = active["values"]
            width = len(values[0])
            if not width or any(len(row) != width for row in values):
                raise SourceConflict("Retained output is not a complete rectangle.")
            actual = response.get("values", [])
            if len(actual) > len(values) or any(len(row) > width for row in actual):
                raise SourceConflict("Retained readback exceeds its original output.")
            padded = [list(row) + [""] * (width - len(row)) for row in actual]
            padded += [[""] * width for _ in range(len(values) - len(actual))]
            if padded != [["" if v is None else v for v in row] for row in values]:
                raise SourceConflict("Private output readback differs from its written content.")
            sections.append((active["file"], active["tab"], values))
            completed.add((active["file"], active["tab"]))
            active = None
        elif request.mutation:
            # The legacy publisher only changes grid dimensions/format between
            # value writes. No second value-writing operation may be ignored.
            if request.operation != "sheets.batchUpdate":
                raise SourceConflict("Unexpected mutation in retained legacy publication.")
            for instruction in args.get("body", {}).get("requests", []):
                if set(instruction) not in (
                    {"addSheet"},
                    {"updateSheetProperties"},
                    {"repeatCell"},
                ):
                    raise SourceConflict("Unexpected grid mutation in retained publication.")
                if (
                    "repeatCell" in instruction
                    and instruction["repeatCell"].get("fields") != "userEnteredFormat.numberFormat"
                ):
                    raise SourceConflict("Retained formatting may not replace values.")
                if "addSheet" in instruction:
                    props = instruction["addSheet"]["properties"]
                    if (request.target, props["sheetId"]) in grids:
                        raise SourceConflict("A retained grid identity was reused.")
                    grids[request.target, props["sheetId"]] = props["title"]
                elif "updateSheetProperties" in instruction:
                    props = instruction["updateSheetProperties"]["properties"]
                    title = grids.get((request.target, props["sheetId"]))
                    if (request.target, title) in completed:
                        raise SourceConflict("A verified output grid was changed after readback.")
                    if instruction["updateSheetProperties"].get("fields") not in {
                        "index",
                        "gridProperties.rowCount,gridProperties.columnCount",
                    }:
                        raise SourceConflict("Unexpected retained grid properties mutation.")
    if active is not None or not sections:
        raise SourceConflict("Complete bounded retained publication is required.")
    # Rebinding preserves section names from the capture, including through
    # several replacements. Try only authenticated historical file mappings;
    # the original private digest selects the exact capture naming generation.
    files = [file for file, _, _ in sections]
    hops = 0
    for mapping in [None, *reversed(mappings)]:
        if mapping is not None:
            reverse = {new: old for old, new in mapping.items()}
            previous = [reverse.get(file, file) for file in files]
            if previous == files:
                continue
            hops += 1
            if hops > 64:
                raise SourceConflict("Retained publication replacement chain exceeds its bound.")
            files = previous
        outputs = tuple(
            OutputSection(
                file + ":" + tab, tuple(values[0]), tuple(tuple(row) for row in values[1:])
            )
            for file, (_, tab, values) in zip(files, sections, strict=True)
        )
        if output_digest(outputs) == expected_hash:
            return
    raise SourceConflict("Published content differs from the original private input commitment.")


def source_content(records, *, registration, generation, files, fence, expected, stream_id):
    """Replay the final publication readback from its closed mutation journal."""
    from kvk.dal.new_source_delivery_dal import Destination
    from kvk.services.new_source_export_service import GoogleSheetsTransport
    from kvk.services.new_source_workbook_transport import ReaderSheetsTransport
    from services.export_provider_adapter import ProviderOutcomeUnknown

    if generation.get("content_key") != expected.get("generation_key") or digest(
        generation.get("tables")
    ).hex() != expected.get("manifest_hash"):
        raise SourceConflict("Published source differs from its original content commitment.")
    transport_type = (
        ReaderSheetsTransport if "reader_bindings" in generation else GoogleSheetsTransport
    )
    if transport_type is ReaderSheetsTransport:
        ReaderSheetsTransport.validate_observation(generation, files)
    last_mutation = max(
        (i for i, (request, _) in enumerate(records) if request.mutation), default=-1
    )
    suffix = records[last_mutation + 1 :]
    if not suffix:
        raise SourceConflict("Publication has no final private readback.")
    # The publisher's final reconciliation uses the same fixed read-only
    # transport evaluator. Earlier successful staging reads cannot stand in for
    # the final suffix, and every request from the selected start must match.
    first_signature = None
    for start in range(len(suffix)):
        first = suffix[start][0]
        if (
            first_signature is not None
            and (first.operation, first.target, first.arguments) != first_signature
        ):
            continue
        index = start

        def execute(message):
            nonlocal index, first_signature
            requested = ProviderRequest.parse(message)
            signature = (requested.operation, requested.target, requested.arguments)
            if first_signature is None:
                first_signature = signature
            if index >= len(suffix) or requested.mutation:
                raise SourceConflict("Final publication readback is incomplete.")
            actual, response = suffix[index]
            if signature != (
                actual.operation,
                actual.target,
                actual.arguments,
            ):
                raise SourceConflict("Final publication readback order differs.")
            index += 1
            return deepcopy(response)

        transport = transport_type.from_authority(
            registration=registration,
            reuse_guard=lambda *_: False,
            protected_file_ids=(),
            execution=execute,
            stream_id=stream_id,
            authorize=lambda **_: None,
            preserve_public_staging=generation.get("staging_audience") == "public_viewer",
        )
        transport._registered_quarantine = True
        if transport_type is ReaderSheetsTransport:
            transport.observation_bindings = generation["reader_bindings"]
            transport.observation_index_id = generation["reader_index_id"]
        try:
            remote = transport.read_coordinated_publication(
                Destination("sheets", registration.index_file_id),
                generation["export_key"],
                fence,
                manifest=generation["tables"],
                files=files,
            )
        except (SourceConflict, ProviderOutcomeUnknown):
            continue
        if index == len(suffix):
            return remote
    raise SourceConflict("The complete final publication transcript cannot be authenticated.")
