"""Explicit reader activation and shared physical planning; no ambient feature flags."""

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.new_source_reporting import CALCULATION_VERSION
from kvk.rendering.new_source_workbook import WORKBOOK_VERSION, WorkbookGeneration
from kvk.services.new_source_export_service import GoogleSheetsTransport, compact_sheets_generation


def physical_generation(generation):
    return (
        generation
        if isinstance(generation, WorkbookGeneration)
        else compact_sheets_generation(generation)
    )


def reader_manifest(manifest):
    versions = {entry.get("version") for entry in manifest.values()}
    if versions == {WORKBOOK_VERSION}:
        return True
    if versions != {None}:
        raise SourceConflict("Mixed or unsupported export layout versions.")
    return False


def partition_manifest(manifest):
    if reader_manifest(manifest):
        from kvk.services.new_source_workbook_transport import ReaderSheetsTransport

        return ReaderSheetsTransport.partition_manifest(manifest)
    return GoogleSheetsTransport.partition_manifest(manifest)


def validate_bindings(bindings, pool_ids):
    if not isinstance(bindings, list) or not 1 <= len(bindings) <= 8:
        raise SourceConflict("Bounded explicit reader activation bindings required.")
    seen = set()
    for binding in bindings:
        if (
            not isinstance(binding, dict)
            or set(binding) != {"pool_id", "kvk_no", "guild_id", "calculation_version"}
            or binding["pool_id"] not in pool_ids
            or type(binding["kvk_no"]) is not int
            or binding["kvk_no"] <= 0
            or binding["kvk_no"] in seen
            or not isinstance(binding["guild_id"], str)
            or not binding["guild_id"].isascii()
            or not binding["guild_id"].isdigit()
            or not 1 <= len(binding["guild_id"]) <= 32
            or binding["calculation_version"] != CALCULATION_VERSION
        ):
            raise SourceConflict("Exact pool, season, guild and calculation binding required.")
        seen.add(binding["kvk_no"])


def load_reader_generation(*, connect, intent_id, expected_hash, kvk_no, guild_id):
    from kvk.rendering.new_source_workbook import build_workbook_generation
    from kvk.services.new_source_reader_service import load_reader_projection

    return build_workbook_generation(
        load_reader_projection(
            connect=connect,
            intent_id=intent_id,
            expected_hash=expected_hash,
            kvk_no=kvk_no,
            guild_id=guild_id,
            with_checkpoints=True,
        )
    )
