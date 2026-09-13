from dataclasses import replace

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, SourceImportDAL
from kvk.services.new_source_artifact_store import ArtifactStore
from tests.test_kvk_source_sql_integration import admission, observation


def test_prepared_mismatch_rejected_before_connection(tmp_path):
    store = ArtifactStore(tmp_path)
    prepared, artifact = observation(16, 1, store)

    def forbidden():
        pytest.fail("Invalid prepared input must not acquire SQL.")

    with pytest.raises(SourceConflict, match="original"):
        SourceImportDAL(forbidden, store).accept_observation(
            replace(prepared, rows=()), artifact, admission()
        )


def test_correction_requires_both_exact_revision_and_version():
    valid = admission(admin_authorized=True, expected_revision_id="revision", expected_version=3)
    SourceImportDAL._correction(valid, "revision", 3)
    for bad in (
        replace(valid, admin_authorized=False),
        replace(valid, expected_version=2),
        replace(valid, expected_revision_id="other"),
    ):
        with pytest.raises(SourceConflict):
            SourceImportDAL._correction(bad, "revision", 3)
