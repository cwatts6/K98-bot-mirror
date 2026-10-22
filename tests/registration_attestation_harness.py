"""Shared pool cases exercise the same activation service and SQL journals."""

from uuid import UUID, uuid4

from services import export_containment_attestation, export_registration_attestation


def qualify_pool_attestation(r, *, lost):
    containment = r.service.proposals.containment
    account = containment.registration.value()["account"]
    pool = containment._scope(r.f.job)[1]
    if lost == "containment":
        snapshot = containment.dal.snapshot(r.f.job, account=account, pool_id=pool)
        del r.docs[str(UUID(snapshot["receipt"]["ReceiptReference"]))]
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
        del r.docs[str(UUID(row["ReceiptReference"]))]
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
