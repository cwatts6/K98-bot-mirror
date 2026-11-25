"""A fresh observer cannot adopt a replacement sequence as its installation."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import timedelta
import json

import pytest

from services import catalogue_observation_contract as contract, catalogue_observation_dal as dal
from tests.test_catalogue_observation import Cursor, token


def approved():
    return dict(
        version=1,
        protocol_sha256=contract.PROTOCOL_SHA256,
        server="lab",
        database="fixture",
        database_id=7,
        principal="dbo",
        login="lab-user",
        sequence_object_id=100,
        sequence_created="2026-11-19T00:00:00.000000",
        sequence_modified="2026-11-19T00:00:00.000000",
        bootstrap_generation=1,
    )


def boundary(generation=2, absent=1):
    row = token(generation, absent)
    health = json.loads(row[-1])
    modules = contract.reviewed_protocol_modules()
    for module in health:
        module["definition"] = modules[module["name"]]
    row[-1] = json.dumps(health)
    return row


def test_full_read_uses_source_pinned_modules_and_immutable_installation():
    source = approved()
    installation = contract.ObservationInstallation(source)
    source["sequence_object_id"] = 101
    with pytest.raises(FrozenInstanceError):
        installation.identity = ()
    cursor = Cursor(boundary(), boundary(), boundary())

    def collect(checkpoint):
        checkpoint()
        return {"metadata": "complete"}

    result = dal.observe_catalogue(
        cursor,
        dict(installation.modules),
        collect,
        installation=installation,
    )
    assert result.value == {"metadata": "complete"}
    assert len(cursor.commands) == 3


@pytest.mark.parametrize("field", [0, 1, 2, 3, 4, 12, 13, 14])
@pytest.mark.parametrize("absent", [0, 1])
def test_first_read_refuses_other_target_or_recreated_sequence_even_when_busy(field, absent):
    installation = contract.ObservationInstallation(approved())
    row = boundary(absent=absent)
    if field in (13, 14):
        row[field] += timedelta(seconds=1)
    elif type(row[field]) is int:
        row[field] += 1
    else:
        row[field] += "-different"
    if field >= 12:
        row[field + 3] = row[field]  # A self-consistent but unapproved incarnation.
    cursor = Cursor(row)
    with pytest.raises(dal.ObservationContractError, match="protected target/sequence"):
        dal.observe_catalogue(
            cursor,
            dict(installation.modules),
            lambda _: pytest.fail("Metadata scan dispatched for unapproved installation"),
            installation=installation,
        )
    assert cursor.commands == [dal.BOUNDARY_SQL]


def test_correct_installation_keeps_active_writer_distinct_and_accepts_generation_gaps():
    installation = contract.ObservationInstallation(approved())
    with pytest.raises(dal.ObservationDeferred, match="active_writer"):
        dal.read_boundary(
            Cursor(boundary(absent=0)), dict(installation.modules), installation=installation
        )
    for generation in (1, 200):
        assert (
            dal.read_boundary(
                Cursor(boundary(generation)),
                dict(installation.modules),
                installation=installation,
            ).generation
            == generation
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("version", True),
        ("protocol_sha256", "0" * 64),
        ("bootstrap_generation", 0),
        ("bootstrap_generation", True),
        ("bootstrap_generation", 2),
        ("database_id", True),
        ("sequence_object_id", -1),
        ("principal", ""),
        ("sequence_created", "2026-11-19"),
        ("sequence_modified", "2026-11-19T00:00:01.000000"),
    ],
)
def test_missing_or_malformed_protected_bootstrap_and_identity_refuse(key, value):
    source = approved()
    source[key] = value
    with pytest.raises(dal.ObservationContractError):
        contract.ObservationInstallation(source)
    source = approved()
    del source[key]
    with pytest.raises(dal.ObservationContractError):
        contract.ObservationInstallation(source)


def test_caller_cannot_substitute_live_module_body_or_unvalidated_binding():
    installation = contract.ObservationInstallation(approved())
    modules = dict(installation.modules)
    modules[next(iter(modules))] += "\n-- changed"
    cursor = Cursor()
    with pytest.raises(dal.ObservationContractError, match="protected source"):
        dal.read_boundary(cursor, modules, installation=installation)
    with pytest.raises(dal.ObservationContractError, match="Validated protected"):
        dal.read_boundary(cursor, dict(installation.modules), installation=approved())
    assert cursor.commands == []


@pytest.mark.parametrize("damage", ["body", "bootstrap", "missing"])
def test_protocol_resource_drift_cannot_be_selected_by_a_protected_document(monkeypatch, damage):
    source = json.loads(contract.read_contract_resource("p02_observer_protocol.json"))
    source = deepcopy(source)
    if damage == "body":
        source["modules"][0]["definition"] += "\n"
    elif damage == "bootstrap":
        source["bootstrap_value"] = 0
    else:
        source["modules"].pop()
    monkeypatch.setattr(contract, "read_contract_resource", lambda _: json.dumps(source).encode())
    with pytest.raises(dal.ObservationContractError, match="Exact reviewed observation protocol"):
        contract.ObservationInstallation(approved())
