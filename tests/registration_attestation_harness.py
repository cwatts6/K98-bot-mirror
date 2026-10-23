"""Shared pool cases exercise the same activation service and SQL journals."""

from uuid import UUID, uuid4

from core.export_execution_host import HostBoundaryError
from services import export_containment_attestation, export_registration_attestation


def qualify_pool_attestation(r, *, lost, damage="missing"):
    containment = r.service.proposals.containment

    def lose(reference):
        reference = str(UUID(reference))
        if damage == "missing":
            del r.docs[reference]
            return
        original = containment.store.read_reference

        def read(key, expected_hash):
            if str(UUID(str(key))) == reference:
                raise HostBoundaryError("Corrupt retained encrypted evidence")
            return original(key, expected_hash)

        containment.store.read_reference = read

    account = containment.registration.value()["account"]
    pool = containment._scope(r.f.job)[1]
    if lost == "containment":
        snapshot = containment.dal.snapshot(r.f.job, account=account, pool_id=pool)
        lose(snapshot["receipt"]["ReceiptReference"])
        _, token, _ = export_containment_attestation.inspect(containment, snapshot)
        export_containment_attestation.apply(
            containment,
            snapshot,
            token=token,
            actor="recovery:" + str(uuid4()),
            reason="Verify current permanent pool isolation",
        )
    expected = r.apply()
    if lost == "activation":
        row = r.activation.dal.chain(account)[0]
        lose(row["ReceiptReference"])
        _, token, _ = export_registration_attestation.inspect(
            r.activation, row, r.service.proposals.registration
        )
        export_registration_attestation.apply(
            r.activation,
            row,
            r.service.proposals.registration,
            token=token,
            actor="recovery:" + str(uuid4()),
            reason="Verify independent current registration dependencies",
        )
    count = len(r.runtime.sent)
    assert r.apply() == expected
    assert len(r.runtime.sent) == count
    assert containment.inspect(r.f.job)["business_resolved"] is False
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 1
    from services.export_enrollment_service import ManagedOriginVerifier

    observed = ManagedOriginVerifier(
        dal=r.service.authority.dal, store=r.service.authority.store
    ).verify(
        account=account,
        targets=sorted(expected["mapping"].values()),
        owner_email="owner@example.com",
        editor_email="editor@example.iam.gserviceaccount.com",
    )
    assert sorted(file["file_id"] for file in observed["files"]) == sorted(
        expected["mapping"].values()
    )
