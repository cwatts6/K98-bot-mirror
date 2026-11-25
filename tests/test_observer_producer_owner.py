"""The existing producer guard owns reusable metadata and its cleanup lifetime."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import application_observation_admission as admission
from services.legacy_export_snapshot_dal import LegacySnapshotDAL, PreparationClaim
from tests.test_observer_contract_selection import approved as application_contract


@pytest.mark.parametrize("failure", [None, "read", "unbracketed"])
def test_owned_collection_is_one_attempt_without_redundant_boundary(monkeypatch, failure):
    from services import export_runtime_composition as composition
    from services.catalogue_observation_contract import reviewed_protocol_modules
    from services.catalogue_observation_dal import (
        CoherentObservation,
        ObservationBoundary,
        ObservationContractError,
    )

    approved = application_contract.__wrapped__()
    claim = PreparationClaim("preparation", "account", "owner", 4, 8, ())
    modules = reviewed_protocol_modules()
    binding = admission.AdmissionBinding.for_claim(
        claim,
        configuration="current",
        registration={"scope": 1},
        approved=approved,
        expected_modules=modules,
    )
    proof = CoherentObservation(
        dict(metadata={"objects": ["original"]}, schema_identity={"id": 1}),
        ObservationBoundary((), 1),
    )
    collect = Mock(return_value=proof)
    verify = Mock(return_value="verified")
    monkeypatch.setattr(composition, "application_snapshot_for_contract", collect)
    monkeypatch.setattr(composition, "verify_application_installation_contract", verify)
    monkeypatch.setattr(
        admission, "read_boundary", Mock(side_effect=AssertionError("redundant boundary"))
    )
    cursor = SimpleNamespace(connection=object())
    if failure == "read":
        collect.side_effect = RuntimeError("original read failure")
    elif failure == "unbracketed":
        collect.return_value = proof.value
    with admission.AdmissionMetadata(binding, approved=approved, expected_modules=modules) as owned:
        if failure:
            expected = RuntimeError if failure == "read" else ObservationContractError
            with pytest.raises(expected):
                owned.collect(cursor)
            verify.assert_not_called()
            assert owned._saved is None
        else:
            assert owned.collect(cursor) == "verified"
            verify.assert_called_once_with(proof.value, approved, observation=proof)
            proof.value["metadata"]["objects"].clear()
            assert owned._saved[1]["objects"] == ["original"]
        with pytest.raises(ObservationContractError, match="One protected"):
            owned.collect(cursor)
        collect.assert_called_once_with(cursor, approved)
    assert owned._saved is owned._origin is None


def test_service_transfers_owned_observation_and_uses_current_entry_configuration(tmp_path):
    from contextlib import contextmanager
    import json

    from services import legacy_export_snapshot_service as service
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    dal.application_sql_contract = application_contract.__wrapped__()
    evidence = object()
    events = []

    @contextmanager
    def guard(*args, **kwargs):
        events.append(("enter", args, kwargs))
        try:
            yield evidence
        finally:
            events.append(("exit",))

    dal.session.side_effect = guard
    owner = runtime.begin_writer("all_kvk")
    assert owner.observation is evidence
    from services.application_observation_schedule import ObservationRequest

    assert type(events[0][2]["observation_request"]) is ObservationRequest
    assert events[0][2]["observation_context"] == dict(
        configuration=runtime.configuration,
        registration=json.loads(runtime.configuration)["all_kvk"],
    )
    changed = json.loads(runtime.configuration)
    changed["all_kvk"]["destinations"] = ["changed"]
    runtime.configuration = json.dumps(changed)
    cursor = object()
    token = service._owner.set(owner)
    try:
        with service.use_runtime(runtime):
            service.verify_producer_cursor(cursor)
        dal.verify_producer_cursor.assert_called_once_with(
            owner.claim,
            cursor,
            observation=evidence,
            observation_context=dict(
                configuration=runtime.configuration, registration=changed["all_kvk"]
            ),
        )
    finally:
        service._owner.reset(token)
        owner.session_guard.__exit__(None, None, None)
        owner.connection.close()
    assert events[-1] == ("exit",)


@pytest.mark.parametrize("failure", [False, True])
def test_actual_dal_owner_collects_once_consumes_current_binding_and_discards_before_close(
    monkeypatch, failure
):
    from core import export_sql_connection
    from services import export_execution_dal, export_runtime_composition, export_sql_health_dal

    approved = application_contract.__wrapped__()
    events = []

    class Evidence:
        def __init__(self, binding, *, approved, expected_modules):
            self.binding = binding
            self.active = False

        def __enter__(self):
            self.active = True
            events.append("enter")
            return self

        def collect(self, cursor):
            assert self.active
            events.append("collect")

        def consume(self, cursor, binding):
            assert self.active and binding == self.binding
            events.append("consume")
            if failure:
                raise SourceConflict("entry failed")

        def __exit__(self, *_):
            self.active = False
            events.append("discard")

    monkeypatch.setattr(admission, "AdmissionMetadata", Evidence)
    legacy_read = Mock(return_value={})
    legacy_verify = Mock()
    monkeypatch.setattr(export_execution_dal, "legacy_installation_snapshot", legacy_read)
    monkeypatch.setattr(
        export_runtime_composition, "verify_legacy_installation_contract", legacy_verify
    )
    monkeypatch.setattr(
        export_runtime_composition,
        "verify_application_cursor",
        Mock(side_effect=AssertionError("duplicate full scan")),
    )
    headroom = Mock()
    monkeypatch.setattr(export_sql_health_dal, "verify_headroom", headroom)
    monkeypatch.setattr(export_sql_connection, "settings", lambda: "actual settings")

    dal = object.__new__(LegacySnapshotDAL)
    dal.application_sql_contract = approved
    dal.legacy_sql_contract = {"source": "qualified legacy source"}
    dal.execution_evidence = True
    dal.sql_profile = "application"
    dal.authorize = Mock()
    claim = PreparationClaim(
        "preparation", "account", "owner", 4, 8, (("sql_snapshot:legacy_outputs", 2),)
    )
    context = dict(configuration="current configuration", registration={"current": "registration"})
    origin = Mock()
    origin.fetchone.return_value = ("NoLock",)
    origin.close.side_effect = lambda: events.append("cursor_close")
    connection = SimpleNamespace(autocommit=True, cursor=lambda: origin)
    origin.connection = connection
    producer = object()

    def use():
        with dal.session(claim, connection, observation_context=context) as saved:
            assert type(saved) is Evidence and saved.active
            dal.verify_producer_cursor(
                claim, producer, observation=saved, observation_context=context
            )
        assert not saved.active

    if failure:
        with pytest.raises(SourceConflict, match="entry failed"):
            use()
    else:
        use()
    assert events == ["enter", "collect", "consume", "discard", "cursor_close"]
    assert legacy_read.call_count == legacy_verify.call_count == dal.authorize.call_count == 2
    headroom.assert_called_once_with(producer, "actual settings")
    assert origin.execute.call_count == 2  # Genuine writer acquire and release only.


def test_changed_live_configuration_is_not_replaced_by_saved_context():
    dal = object.__new__(LegacySnapshotDAL)
    dal.application_sql_contract = application_contract.__wrapped__()
    claim = PreparationClaim(
        "preparation", "account", "owner", 4, 8, (("sql_snapshot:legacy_outputs", 2),)
    )
    context = dict(configuration="old", registration={"current": "registration"})
    before, modules = dal._observation_binding(claim, context)
    after, fresh_modules = dal._observation_binding(claim, dict(context, configuration="new"))
    assert before != after and modules == fresh_modules
