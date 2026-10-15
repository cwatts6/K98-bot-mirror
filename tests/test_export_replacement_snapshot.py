import hashlib
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_replacement_snapshot import rebind_snapshot
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    OutputSection,
    configuration_digest,
    output_digest,
)


def fixture():
    sections = (OutputSection("original-data", ("ID", "Value"), ((1, "retained"),)),)
    config = dict(
        destinations=["old-file"],
        queries=["original query"],
        outputs=[
            dict(
                file_id="old-file",
                tab="Report",
                grid_id=7,
                section="original-data",
                format_requests=[
                    dict(
                        repeatCell=dict(
                            range=dict(sheetId=7),
                            fields="userEnteredFormat.numberFormat",
                            cell=dict(
                                userEnteredFormat=dict(
                                    numberFormat=dict(type="NUMBER", pattern="0")
                                )
                            ),
                        )
                    ),
                    dict(
                        updateSheetProperties=dict(
                            properties=dict(sheetId=7, index=0), fields="index"
                        )
                    ),
                ],
            )
        ],
    )
    old = LegacySnapshot.capture(
        consumer="scan_data",
        preparation_id=str(uuid4()),
        generation=dict(
            completion="committed",
            commit_identity="original SQL receipt",
            output_sha256=output_digest(sections),
            config_sha256=configuration_digest(config),
        ),
        config=config,
        provenance=dict(actor="original"),
        sections=sections,
    )
    job = dict(
        JobID=str(uuid4()),
        ConsumerKind="scan_data",
        InputHash=hashlib.sha256(old.payload).hexdigest(),
    )
    activated = dict(
        activation_id=str(uuid4()),
        replacement_id=str(uuid4()),
        mapping={"old-file": "fresh-file"},
        registration=dict(
            legacy_configuration=dict(
                scan_data=dict(destinations=["fresh-file"], grid_ids={"fresh-file": {"Report": 42}})
            )
        ),
    )
    return old, job, activated


def test_replacement_preserves_exact_committed_data_and_changes_only_routing():
    old, job, activated = fixture()
    replacement = rebind_snapshot(old, job=job, activation=activated)
    meta = replacement.metadata()
    assert replacement.sections() == old.sections()
    assert meta["generation"]["commit_identity"] == old.metadata()["generation"]["commit_identity"]
    assert meta["config"]["queries"] == ["original query"]
    output = meta["config"]["outputs"][0]
    assert (output["file_id"], output["grid_id"]) == ("fresh-file", 42)
    assert output["format_requests"][0]["repeatCell"]["range"]["sheetId"] == 42
    assert output["format_requests"][1]["updateSheetProperties"]["properties"]["sheetId"] == 42
    assert old.metadata()["config"]["outputs"][0]["file_id"] == "old-file"
    assert LegacySnapshot.load(replacement.payload) == replacement
    assert rebind_snapshot(old, job=job, activation=activated).payload == replacement.payload


@pytest.mark.parametrize("fault", ["hash", "consumer", "missing_mapping", "foreign_destination"])
def test_replacement_cannot_change_or_escape_original_job(fault):
    old, job, activated = fixture()
    if fault == "hash":
        job["InputHash"] = "0" * 64
    elif fault == "consumer":
        job["ConsumerKind"] = "all_kvk"
    elif fault == "missing_mapping":
        activated["mapping"] = {}
    else:
        activated["registration"]["legacy_configuration"]["scan_data"]["destinations"] = [
            "other-file"
        ]
    with pytest.raises(SourceConflict):
        rebind_snapshot(old, job=job, activation=activated)


def test_unconfigured_tab_avoids_fresh_default_grid_collision():
    from services.export_legacy_grid_identity import legacy_grid_identity

    candidate = legacy_grid_identity("Report", {})
    assert legacy_grid_identity("Report", {"Sheet1": candidate}) != candidate
    assert legacy_grid_identity("Report", {"Report": candidate}) == candidate
