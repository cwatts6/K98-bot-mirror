from copy import deepcopy
import json
from uuid import uuid4

import pytest
from test_observer_contract_selection import approved  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.catalogue_observation_contract import ObservationContractError
from services.export_observer_contract import MIGRATION_ID, PROFILE_SHA256
from services.observer_release_issuance import bind_observer_candidate


@pytest.fixture
def issuance(approved):  # noqa: F811
    application = deepcopy(approved)
    installation = application.pop("observation_installation")
    installation.pop("principal")
    installation.pop("login")
    fixed = {key: application[key] for key in ("server", "database", "principal")}
    fixed.update(version=4, profile="application")
    legacy = {
        key: application[key]
        for key in (
            "server",
            "database",
            "principal",
            "phase1_installation",
            "d4_installation",
            "observer_installation",
        )
    }
    bot = dict(sql_contract=fixed, legacy_sql_contract=legacy, application_sql_contract=application)
    config = dict(
        release_id=str(uuid4()),
        sql=dict(
            commit="a" * 40,
            profiles=[
                dict(id=MIGRATION_ID, file=MIGRATION_ID + ".release.json", sha256=PROFILE_SHA256)
            ],
        ),
    )
    binding = dict(
        migration_id=MIGRATION_ID,
        profile_sha256=PROFILE_SHA256,
        sql_commit=config["sql"]["commit"],
        release_id=config["release_id"],
        observation_installation=installation,
    )
    receipt = dict(
        migration_status="Applied",
        profile_sha256=PROFILE_SHA256,
        sql_commit=config["sql"]["commit"],
        deployment_id=str(uuid4()),
        deployment_status="Succeeded",
        deployment_commit=config["sql"]["commit"],
        deployment_profile="p02_catalogue_observer_v1",
        deployment_database="ROK_TRACKER",
        binding=json.dumps(binding),
        **{
            key: installation[key]
            for key in (
                "server",
                "database",
                "database_id",
                "sequence_object_id",
                "sequence_created",
                "sequence_modified",
            )
        },
        principal=fixed["principal"],
        login=fixed["principal"],
    )
    return config, bot, receipt


def test_issued_candidate_changes_only_exact_committed_incarnation(issuance):
    config, bot, receipt = issuance
    original = deepcopy(issuance)
    result = bind_observer_candidate(config, bot, receipt)
    installed = result["application_sql_contract"].pop("observation_installation")
    assert result == bot
    assert installed["sequence_object_id"] == receipt["sequence_object_id"]
    assert installed["login"] == bot["sql_contract"]["principal"]
    assert issuance == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("migration_status", "Failed"),
        ("profile_sha256", "0" * 64),
        ("sql_commit", "b" * 40),
        ("deployment_status", "Started"),
        ("deployment_commit", "c" * 40),
        ("deployment_profile", "other"),
        ("deployment_database", "other"),
        ("server", "other"),
        ("database", "other"),
        ("principal", "admin"),
        ("login", "admin"),
        ("sequence_object_id", 101),
        ("database_id", "7"),
        ("database_id", True),
        ("database_id", 7.0),
        ("sequence_created", "2026-11-20T12:00:00.001000"),
    ],
)
def test_native_receipt_mismatch_never_binds(issuance, field, value):
    config, bot, receipt = issuance
    receipt[field] = value
    with pytest.raises((SourceConflict, ObservationContractError)):
        bind_observer_candidate(config, bot, receipt)
    assert "observation_installation" not in bot["application_sql_contract"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("release_id", str(uuid4())),
        ("sql_commit", "b" * 40),
        ("migration_id", "other"),
        ("profile_sha256", "0" * 64),
    ],
)
def test_retained_binding_must_belong_to_same_sealed_release(issuance, field, value):
    config, bot, receipt = issuance
    binding = json.loads(receipt["binding"])
    binding[field] = value
    receipt["binding"] = json.dumps(binding)
    with pytest.raises(SourceConflict):
        bind_observer_candidate(config, bot, receipt)


@pytest.mark.parametrize(
    "field,value",
    [
        ("bootstrap_generation", 2),
        ("bootstrap_generation", True),
        ("principal", "app"),
        ("login", "admin"),
        ("database_id", "7"),
        ("sequence_object_id", 101),
        ("sequence_modified", "2026-11-20T12:00:00.001000"),
    ],
)
def test_receipt_cannot_supply_application_authority_or_guess_incarnation(issuance, field, value):
    config, bot, receipt = issuance
    binding = json.loads(receipt["binding"])
    binding["observation_installation"][field] = value
    receipt["binding"] = json.dumps(binding)
    with pytest.raises((SourceConflict, ObservationContractError)):
        bind_observer_candidate(config, bot, receipt)


def test_duplicate_binding_fields_and_missing_commit_are_refused(issuance):
    config, bot, receipt = issuance
    receipt["binding"] = receipt["binding"].replace("{", '{"release_id":"duplicate",', 1)
    with pytest.raises(SourceConflict, match="Duplicate"):
        bind_observer_candidate(config, bot, receipt)
    receipt.pop("deployment_id")
    with pytest.raises(SourceConflict, match="Complete linked"):
        bind_observer_candidate(config, bot, receipt)


def test_existing_installation_is_never_rebound(issuance):
    config, bot, receipt = issuance
    bound = bind_observer_candidate(config, bot, receipt)
    with pytest.raises(SourceConflict, match="unissued"):
        bind_observer_candidate(config, bound, receipt)


def test_source_expectations_cannot_be_adopted_from_receipt(issuance):
    config, bot, receipt = issuance
    receipt["metadata_hash"] = "0" * 64
    with pytest.raises(SourceConflict, match="Complete linked"):
        bind_observer_candidate(config, bot, receipt)


def test_seed_derivation_requires_commit_before_full_comparison(monkeypatch, issuance):
    from scripts import recovery_release_seed as seed

    config, bot, receipt = issuance
    candidate = {"bot-template.json": seed.encode(bot)}
    proof = dict(
        release_id=config["release_id"],
        bindings_sha256="c" * 64,
        observer_release=receipt,
        collected={"actual": "rows"},
    )
    calls = []

    def full_compare(files, collected):
        bound = json.loads(files["bot-template.json"])
        assert (
            bound["application_sql_contract"]["observation_installation"]["sequence_object_id"]
            == 100
        )
        calls.append(collected)
        raise SourceConflict("Injected three-contract refusal")

    monkeypatch.setattr(seed, "verified_seed", full_compare)
    with pytest.raises(SourceConflict, match="three-contract refusal"):
        seed.prepare_verified_files(config, "c" * 64, candidate, proof)
    assert calls == [{"actual": "rows"}]
    proof.pop("observer_release")
    with pytest.raises(ValueError, match="another release"):
        seed.prepare_verified_files(config, "c" * 64, candidate, proof)
    assert len(calls) == 1


@pytest.mark.parametrize("stamp", ["2026-11-20T13:14:27.063000", "2026-11-17T17:34:47.357000"])
def test_application_receipt_preserves_native_odbc_timestamp(monkeypatch, stamp):
    from datetime import datetime

    from services import observer_release_dal as dal

    row = dict(
        sequence_created=datetime.fromisoformat(stamp),
        sequence_modified=datetime.fromisoformat(stamp),
        sql_commit="a" * 40,
        deployment_id="7D96F4AF-4930-47D0-8C67-64DA71BD5F0B",
    )
    monkeypatch.setattr(dal, "rows", lambda cursor: [row])

    class Cursor:
        def execute(self, *args):
            self.arguments = args

    cursor = Cursor()
    result = dal.committed_observer_receipt(cursor)
    assert result["sequence_created"] == result["sequence_modified"] == stamp
    assert result["sql_commit"] == "a" * 40
    assert cursor.arguments[1:] == (MIGRATION_ID,)


@pytest.mark.parametrize("stamp", ["2026-11-20T13:14:27.063000", None, 123])
def test_application_receipt_requires_typed_native_timestamp(monkeypatch, stamp):
    from services import observer_release_dal as dal

    monkeypatch.setattr(
        dal, "rows", lambda cursor: [dict(sequence_created=stamp, sequence_modified=stamp)]
    )

    class Cursor:
        def execute(self, *args):
            pass

    with pytest.raises(SourceConflict, match="Typed ODBC"):
        dal.committed_observer_receipt(Cursor())


@pytest.mark.parametrize("uppercase", [False, True])
def test_native_dal_uuid_transport_reaches_strict_issuer(issuance, uppercase):
    from datetime import datetime

    from services.observer_release_dal import committed_observer_receipt

    config, bot, expected = issuance
    native = dict(expected)
    if uppercase:
        native["deployment_id"] = expected["deployment_id"].upper()
    for key in ("sequence_created", "sequence_modified"):
        native[key] = datetime.fromisoformat(native[key])

    class Cursor:
        def __init__(self):
            self.description = [(name,) for name in native]

        def execute(self, *args):
            self.arguments = args

        def fetchall(self):
            return [tuple(native.values())]

    cursor = Cursor()
    receipt = committed_observer_receipt(cursor)
    assert receipt == expected
    bound = bind_observer_candidate(config, bot, receipt)
    assert bound["application_sql_contract"]["observation_installation"]["sequence_object_id"] == (
        expected["sequence_object_id"]
    )
    assert cursor.arguments[1:] == (MIGRATION_ID,)
    assert "observation_installation" not in bot["application_sql_contract"]


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        123,
        True,
        "not-a-guid",
        " 7D96F4AF-4930-47D0-8C67-64DA71BD5F0B",
        "{7D96F4AF-4930-47D0-8C67-64DA71BD5F0B}",
        "7D96F4AF493047D08C6764DA71BD5F0B",
    ],
)
def test_native_dal_rejects_non_sql_uuid_representations(monkeypatch, issuance, identifier):
    from datetime import datetime

    from services import observer_release_dal as dal

    _, _, expected = issuance
    native = dict(expected, deployment_id=identifier)
    for key in ("sequence_created", "sequence_modified"):
        native[key] = datetime.fromisoformat(native[key])
    monkeypatch.setattr(dal, "rows", lambda _: [native])

    class Cursor:
        def execute(self, *args):
            pass

    with pytest.raises(SourceConflict, match="SQL deployment UUID"):
        dal.committed_observer_receipt(Cursor())
