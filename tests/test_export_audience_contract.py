"""Persisted audience transitions, independent of transport mocks."""

from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_audience import check_audience
from services.export_coordination_dal import ExportCoordinationDAL, bounded_json


@pytest.mark.parametrize(
    "pinned,audience,recorded,accepted",
    [
        (None, "private", False, True),
        ("private", "private", True, True),
        ("public_viewer", "public_viewer", True, True),
        ("private", "public_viewer", True, False),
        ("public_viewer", "private", True, False),
        ("public_viewer", "public_viewer", False, False),
    ],
)
def test_real_verified_transition_requires_durable_audience(
    monkeypatch, pinned, audience, recorded, accepted
):
    dal = ExportCoordinationDAL(
        Mock(), preparations=recorded, output_operations=recorded, execution_evidence=recorded
    )
    cursor = Mock()

    @contextmanager
    def owned(_):
        yield cursor, {"ConsumerKind": "new_source"}

    dal._owned = owned
    generation = {} if pinned is None else {"staging_audience": pinned}
    dal._attempt = Mock(
        return_value=(
            dict(
                Phase="private_started",
                Version=1,
                ManifestJson=bounded_json({"generation": generation}),
            ),
            [dict(Role="generation", PartNo=2, Version=1)],
        )
    )
    cas = Mock()
    monkeypatch.setattr("services.export_coordination_dal._cas", cas)
    if not accepted:
        with pytest.raises(SourceConflict):
            dal.verified(object(), "attempt", audience=audience)
        cas.assert_not_called()
    else:
        dal.verified(object(), "attempt", audience=audience)
        assert len(cas.call_args_list) == 2
        assert "AclState='" + audience + "'" in cas.call_args_list[0].args[1]


@pytest.mark.parametrize(
    "policy,private,audience,accepted",
    [
        ("private", True, None, True),
        ("public_viewer", True, None, True),
        ("public_viewer", False, "public_viewer", True),
        ("private", False, "public_viewer", False),
        ("public_viewer", True, "public_viewer", False),
        ("public_viewer", False, None, False),
    ],
)
def test_clear_evidence_never_claims_public_and_private_together(
    policy, private, audience, accepted
):
    evidence = {"private": private}
    if audience is not None:
        evidence["audience"] = audience
    pool = {"RegistrationJson": bounded_json({"audience": policy})}
    if accepted:
        assert check_audience(evidence, pool) in {"private", "public_viewer"}
    else:
        with pytest.raises(SourceConflict):
            check_audience(evidence, pool)
