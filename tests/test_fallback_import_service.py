from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from services import fallback_import_service as service

TOKEN = "0123456789abcdef0123456789abcdef"
COMPLETED = f"stats_{TOKEN}.ready.csv"


def _paths(tmp_path: Path) -> service.FallbackImportPaths:
    downloads = tmp_path / "downloads"
    return service.FallbackImportPaths(
        download_folder=str(downloads),
        source_file_2=str(downloads / "stats.xlsx"),
        archive_dir_1=str(downloads / "Databook_Archive"),
        archive_dir_2=str(downloads / "Import_Archive"),
        ready_dir=str(downloads / "Import_Ready"),
        import_metadata_file_path=str(downloads / "stats_import_metadata.json"),
    )


def test_publish_fallback_csv_uses_unique_closed_ready_identity(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    metadata = {"source_filename": "public upload.xlsx"}

    completed = service.publish_fallback_csv(
        pd.DataFrame([{"Governor ID": 123, "Name": "Alpha"}]),
        paths=paths,
        metadata=metadata,
        token_factory=lambda: TOKEN,
    )

    ready_path = Path(paths.ready_dir) / COMPLETED
    assert completed == COMPLETED
    assert ready_path.is_file()
    assert not (Path(paths.ready_dir) / f".stats_{TOKEN}.tmp").exists()
    assert ready_path.read_bytes().startswith(b"\xef\xbb\xbf")
    manifest = json.loads(Path(paths.import_metadata_file_path).read_text(encoding="utf-8"))
    assert manifest["completed_filename"] == COMPLETED
    assert manifest["publication_state"] == "published"
    assert manifest["source_filename"] == "public upload.xlsx"


def test_publish_fallback_csv_refuses_collision_without_overwrite(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ready_path = Path(paths.ready_dir) / COMPLETED
    ready_path.parent.mkdir(parents=True)
    ready_path.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        service.publish_fallback_csv(
            pd.DataFrame([{"Governor ID": 123}]),
            paths=paths,
            metadata={},
            token_factory=lambda: TOKEN,
        )

    assert ready_path.read_bytes() == b"existing"
    assert not (Path(paths.ready_dir) / f".stats_{TOKEN}.tmp").exists()


def test_same_content_publishes_as_distinct_completed_identities(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    frame = pd.DataFrame([{"Governor ID": 123, "Name": "Alpha"}])
    second_token = "fedcba9876543210fedcba9876543210"

    first_name = service.publish_fallback_csv(
        frame,
        paths=paths,
        metadata={},
        token_factory=lambda: TOKEN,
    )
    second_name = service.publish_fallback_csv(
        frame,
        paths=paths,
        metadata={},
        token_factory=lambda: second_token,
    )

    first_path = Path(paths.ready_dir) / first_name
    second_path = Path(paths.ready_dir) / second_name
    assert first_name != second_name
    assert first_path.read_bytes() == second_path.read_bytes()


def test_failed_identity_can_be_corrected_under_a_new_identity(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    corrected_token = "11111111111111111111111111111111"

    with pytest.raises(OSError, match="rename denied"):
        service.publish_fallback_csv(
            pd.DataFrame([{"Governor ID": "invalid"}]),
            paths=paths,
            metadata={},
            token_factory=lambda: TOKEN,
            rename_file=lambda _source, _target: (_ for _ in ()).throw(
                OSError("rename denied")
            ),
        )

    corrected_name = service.publish_fallback_csv(
        pd.DataFrame([{"Governor ID": 123}]),
        paths=paths,
        metadata={},
        token_factory=lambda: corrected_token,
    )

    assert corrected_name == f"stats_{corrected_token}.ready.csv"
    assert not (Path(paths.ready_dir) / COMPLETED).exists()
    assert (Path(paths.ready_dir) / corrected_name).is_file()


def test_publish_fallback_csv_write_failure_leaves_no_ready_object(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)

    def fail_sync(_fd: int) -> None:
        raise OSError("disk")

    with pytest.raises(OSError, match="disk"):
        service.publish_fallback_csv(
            pd.DataFrame([{"Governor ID": 123}]),
            paths=paths,
            metadata={},
            token_factory=lambda: TOKEN,
            sync_file=fail_sync,
        )

    assert not (Path(paths.ready_dir) / COMPLETED).exists()
    assert not (Path(paths.ready_dir) / f".stats_{TOKEN}.tmp").exists()
    assert (
        service.load_import_metadata(paths.import_metadata_file_path)["publication_state"]
        == "failed"
    )


def test_publish_fallback_csv_rename_failure_leaves_no_ready_object(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    def fail_rename(_source: str, _target: str) -> None:
        raise OSError("rename denied")

    with pytest.raises(OSError, match="rename denied"):
        service.publish_fallback_csv(
            pd.DataFrame([{"Governor ID": 123}]),
            paths=paths,
            metadata={},
            token_factory=lambda: TOKEN,
            rename_file=fail_rename,
        )

    assert not (Path(paths.ready_dir) / COMPLETED).exists()
    assert not (Path(paths.ready_dir) / f".stats_{TOKEN}.tmp").exists()


def test_resolve_recovers_crash_after_rename_before_manifest_advance(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ready_path = Path(paths.ready_dir) / COMPLETED
    ready_path.parent.mkdir(parents=True)
    ready_path.write_bytes(b"closed")
    metadata = {
        "publication_manifest_version": service.PUBLICATION_MANIFEST_VERSION,
        "completed_filename": COMPLETED,
        "publication_state": "prepared",
    }
    service.write_import_metadata(metadata, paths.import_metadata_file_path)

    assert (
        service.resolve_published_completed_filename(
            metadata_path=paths.import_metadata_file_path,
            ready_dir=paths.ready_dir,
        )
        == COMPLETED
    )
    assert (
        service.load_import_metadata(paths.import_metadata_file_path)["publication_state"]
        == "published"
    )


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {
            "publication_manifest_version": 1,
            "completed_filename": "stats.csv",
            "publication_state": "published",
        },
        {
            "publication_manifest_version": 1,
            "completed_filename": COMPLETED,
            "publication_state": "failed",
        },
    ],
)
def test_resolve_fails_closed_for_invalid_or_unpublished_manifest(
    tmp_path: Path, metadata: dict
) -> None:
    paths = _paths(tmp_path)
    with pytest.raises(ValueError):
        service.resolve_published_completed_filename(
            metadata_path=paths.import_metadata_file_path,
            ready_dir=paths.ready_dir,
            metadata=metadata,
        )


def test_resolve_cleans_only_manifest_owned_private_interrupted_file(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    private_path = Path(paths.ready_dir) / f".stats_{TOKEN}.tmp"
    private_path.parent.mkdir(parents=True)
    private_path.write_bytes(b"partial")
    metadata = {
        "publication_manifest_version": service.PUBLICATION_MANIFEST_VERSION,
        "completed_filename": COMPLETED,
        "publication_state": "private_writing",
    }

    with pytest.raises(ValueError):
        service.resolve_published_completed_filename(
            metadata_path=paths.import_metadata_file_path,
            ready_dir=paths.ready_dir,
            metadata=metadata,
        )

    assert not private_path.exists()
    assert not (Path(paths.ready_dir) / COMPLETED).exists()
