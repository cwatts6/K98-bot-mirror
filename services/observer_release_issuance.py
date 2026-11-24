"""Bind an unissued candidate to its committed release, without adopting schema.

Only the installation incarnation comes from the linked commit receipt plus a
separate current read. All schema/permission expectations remain sealed inputs;
the caller must pass all three comparators before writing any protected seed.
"""

from copy import deepcopy
import json
import re
from uuid import UUID

from kvk.dal.new_source_import_dal import SourceConflict
from services.catalogue_observation_contract import PROTOCOL_SHA256, ObservationInstallation
from services.export_observer_contract import (
    MIGRATION_ID,
    PROFILE_SHA256,
    observer_contract,
    require_observer_contract_pair,
)


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceConflict("Duplicate observer receipt field.")
        result[key] = value
    return result


def bind_observer_candidate(config, candidate_bot, receipt):
    """Pure verification; returns an in-memory candidate, never release authority."""
    bot = deepcopy(candidate_bot)
    fixed, legacy, application = (
        bot[key] for key in ("sql_contract", "legacy_sql_contract", "application_sql_contract")
    )
    if not observer_contract(legacy) or not observer_contract(application):
        raise SourceConflict("Both sealed observer successor contracts are required.")
    if "observation_installation" in application:
        raise SourceConflict("Only an unissued observer candidate may receive a commit binding.")
    sql = config.get("sql", {})
    if (
        not re.fullmatch(r"[a-f0-9]{40}", sql.get("commit", ""))
        or sql.get("profiles")
        != [dict(id=MIGRATION_ID, file=MIGRATION_ID + ".release.json", sha256=PROFILE_SHA256)]
        or str(UUID(config["release_id"])) != config["release_id"]
    ):
        raise SourceConflict("Exact sealed observer SQL release is required.")
    fields = {
        "migration_status",
        "profile_sha256",
        "sql_commit",
        "deployment_id",
        "deployment_status",
        "deployment_commit",
        "deployment_profile",
        "deployment_database",
        "binding",
        "server",
        "database",
        "database_id",
        "principal",
        "login",
        "sequence_object_id",
        "sequence_created",
        "sequence_modified",
    }
    if not isinstance(receipt, dict) or set(receipt) != fields:
        raise SourceConflict("Complete linked observer commit evidence is required.")
    if (
        receipt["migration_status"] != "Applied"
        or receipt["profile_sha256"] != PROFILE_SHA256
        or receipt["sql_commit"] != sql["commit"]
        or receipt["deployment_commit"] != sql["commit"]
        or receipt["deployment_status"] != "Succeeded"
        or receipt["deployment_profile"] != "p02_catalogue_observer_v1"
        or receipt["deployment_database"] != fixed["database"]
        or str(UUID(receipt["deployment_id"])) != receipt["deployment_id"]
        or any(receipt[key] != fixed[key] for key in ("server", "database", "principal"))
        or receipt["login"] != fixed["principal"]
        or not isinstance(receipt["binding"], str)
        or len(receipt["binding"]) > 8192
    ):
        raise SourceConflict("Linked observer release or application target differs.")
    binding = json.loads(receipt["binding"], object_pairs_hook=_json_object)
    if (
        not isinstance(binding, dict)
        or set(binding)
        != {
            "migration_id",
            "profile_sha256",
            "sql_commit",
            "release_id",
            "observation_installation",
        }
        or any(
            binding[key] != expected
            for key, expected in (
                ("migration_id", MIGRATION_ID),
                ("profile_sha256", PROFILE_SHA256),
                ("sql_commit", sql["commit"]),
                ("release_id", config["release_id"]),
            )
        )
    ):
        raise SourceConflict("Committed observer binding belongs to another release.")
    installed = deepcopy(binding["observation_installation"])
    if not isinstance(installed, dict) or "principal" in installed or "login" in installed:
        raise SourceConflict("Coordinator incarnation must not supply application authority.")
    installed.update(principal=fixed["principal"], login=fixed["principal"])
    ObservationInstallation(installed)
    # Validate current SQL types independently: bool/float/string are not IDs.
    fresh = {
        key: receipt[key]
        for key in (
            "server",
            "database",
            "database_id",
            "principal",
            "login",
            "sequence_object_id",
            "sequence_created",
            "sequence_modified",
        )
    }
    fresh.update(version=1, protocol_sha256=PROTOCOL_SHA256, bootstrap_generation=1)
    ObservationInstallation(fresh)
    if fresh != installed:
        raise SourceConflict("Current sequence differs from the committed observer incarnation.")
    application["observation_installation"] = installed
    require_observer_contract_pair(fixed, legacy, application)
    from services.export_runtime_composition import validate_application_installation_contract

    validate_application_installation_contract(application)
    return bot
