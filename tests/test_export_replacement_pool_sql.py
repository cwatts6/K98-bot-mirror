import json
import os

import pytest

from kvk.dal.new_source_import_dal import digest
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_runtime_composition import RuntimeRegistration
from tests import (
    test_export_target_containment as authority_fixture,
    test_export_target_containment_sql as fixture_module,
)
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    verification as verification,
)
from tests.test_export_runtime_composition import registration_fixture

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def recovery(contained_job):
    service, f, docs = authority_fixture.recovery.__wrapped__(contained_job)
    pool_id, _ = fixture_module.pool_job(f, slot_count=4)
    config = registration_fixture()
    config.update(account="test-account", storage_owner="disk")
    descriptor = dict(pool=0)
    config["pools"][0].update(
        pool_id=pool_id, index_file_id="old-file", slot_file_ids=[f"old-slot-{i}" for i in range(1, 5)]
    )
    registered = config["pools"][0]
    f.sql.execute(
        "UPDATE #SourceOutputPool SET ExpectedOwner=?,RegistrationHash=CAST(? AS binary(32)),RegistrationJson=?",
        registered["owner_email"],
        digest(descriptor),
        json.dumps(descriptor),
    )
    f.sql.execute(
        "UPDATE #ExportExecutionStream SET RegistrationHash=CAST(? AS binary(32))",
        digest(descriptor),
    )
    service.registration = RuntimeRegistration(config)
    service.discovery = ExportRecoveryDAL(f.connect, registration=service.registration)
    return service, f, docs


def test_full_pool_activation_reuses_capacity_number_and_preserves_old_history(activation):
    r = activation
    old_slots = [
        tuple(row) for row in r.f.sql.execute("SELECT * FROM #SourceOutputSlot ORDER BY SlotNo")
    ]
    result = r.apply()
    assert result["business_resolved"] is False
    pools = list(
        r.f.sql.execute(
            "SELECT PoolID,RegistrationNo,RetiredByReplacementID,PoolState FROM #SourceOutputPool ORDER BY CreatedUTC,PoolID"
        )
    )
    assert len(pools) == 2
    assert {p.RegistrationNo for p in pools} == {1}
    assert sum(p.RetiredByReplacementID is None for p in pools) == 1
    assert [
        tuple(row)
        for row in r.f.sql.execute(
            "SELECT * FROM #SourceOutputSlot WHERE FileID LIKE 'old-%' ORDER BY SlotNo"
        )
    ] == old_slots
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert r.service.proposals.containment.inspect(r.f.job)["outcome"] == "targets_isolated"
    assert r.apply() == result
    from services.export_enrollment_service import ManagedOriginVerifier

    seal = ManagedOriginVerifier(
        dal=r.service.authority.dal, store=r.service.authority.store
    ).verify(
        account="test-account",
        targets=sorted(result["mapping"].values()),
        owner_email="owner@example.com",
        editor_email="editor@example.iam.gserviceaccount.com",
    )
    assert sorted(f["file_id"] for f in seal["files"]) == sorted(result["mapping"].values())
