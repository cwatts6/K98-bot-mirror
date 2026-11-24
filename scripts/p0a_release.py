"""Installed, finite policy for the reviewed coordinated P0a recovery release.

This policy is authenticated by the updater inventory, never supplied by the
acquired target tree. It authorizes exact source pairs and independently derived
SQL images. Live environment values bind ambient compatibility only; neither
object images nor expected permissions are learned from the installation.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re


def encode(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def specification():
    raw = Path(__file__).with_name("p0a_release_spec.json").read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError("Bounded installed recovery policy required.")
    value = json.loads(raw)
    if isinstance(value, dict) and value.get("version") == 2:
        if (
            set(value) != {"version", "releases"}
            or not isinstance(value["releases"], list)
            or not 1 <= len(value["releases"]) <= 4
        ):
            raise ValueError("Bounded installed coordinated release policies required.")
        for item in value["releases"]:
            validate_specification(item)
        if len({item["before"] for item in value["releases"]}) != len(value["releases"]):
            raise ValueError("One installed policy per exact predecessor required.")
        return value
    validate_specification(value)
    return value


def validate_specification(value):
    if not isinstance(value, dict):
        raise ValueError("Exact installed recovery policy required.")
    if set(value) != {"version", "before", "sources", "contracts", "sql"} or value["version"] != 1:
        raise ValueError("Exact installed recovery policy required.")
    if not re.fullmatch(r"[a-f0-9]{40}", value["before"]):
        raise ValueError("Exact recovery predecessor required.")
    if not 1 <= len(value["sources"]) <= 128:
        raise ValueError("Bounded protected recovery inventory required.")
    family = value.get("sql", {}).get("profile", {}).get("profile")
    observer = family in {"p02_catalogue_observer_v1", "p02_observer_return_v1"}
    source_pattern = r"(?:core|services|scripts|ui/views)/[a-z_]+\.py|(?:run_bot|bot_config|constants|processing_pipeline|file_utils)\.py"
    if observer:
        source_pattern += r"|scripts/[a-z0-9_]+\.py|kvk/(?:dal|services)/[a-z_]+\.py|(?:bot_instance|proc_config_import|player_stats_cache|kvk_all_importer|stats_module)\.py|deploy/p02_observer_(?:protocol|legacy_source|activation_scope|application_sources)\.json"
    paths = set()
    for row in value["sources"]:
        if set(row) != {"path", "before", "after"} or not re.fullmatch(
            source_pattern,
            row["path"],
        ):
            raise ValueError("Exact protected recovery source member required.")
        if row["path"] in paths:
            raise ValueError("Repeated protected recovery member.")
        paths.add(row["path"])
        for key in ("before", "after"):
            if row[key] is not None and not re.fullmatch(r"[a-f0-9]{64}", row[key]):
                raise ValueError("Exact reviewed source hashes required.")
    if set(value["contracts"]) != {
        "sql_contract",
        "legacy_sql_contract",
        "application_sql_contract",
    }:
        raise ValueError("All three reviewed SQL contracts required.")
    for pair in value["contracts"].values():
        if set(pair) != {"before", "after"}:
            raise ValueError("Exact before/after SQL contracts required.")
    validate_sql_policy(value["sql"])
    if observer:
        for key, pair in value["contracts"].items():
            before, after = pair["before"], pair["after"]
            if (
                not isinstance(before, dict)
                or not isinstance(after, dict)
                or any(
                    before.get(name) != after.get(name)
                    for name in ("server", "database", "principal")
                )
            ):
                raise ValueError("Observer contract target cannot be replaced.")
            if (
                family == "p02_catalogue_observer_v1"
                and key != "sql_contract"
                and (
                    after.get("observer_installation") != OBSERVER_MIGRATION
                    or before.get("observer_installation") is not None
                    or "observation_installation" in after
                )
            ):
                raise ValueError(
                    "Unissued observer successor over its reviewed predecessor required."
                )
        fixed = value["contracts"]["sql_contract"]["after"]
        if (
            fixed.get("version") != 4
            or fixed.get("profile") != "application"
            or any(
                pair["after"].get(name) != fixed.get(name)
                for pair in value["contracts"].values()
                for name in ("server", "database", "principal")
            )
        ):
            raise ValueError("Three matching application contracts required.")
        if family == "p02_observer_return_v1":
            validate_return_contracts(value)


def validate_sql_policy(sql):
    if set(sql) != {"commit", "members", "profile"} or not re.fullmatch(
        r"[a-f0-9]{40}", sql["commit"]
    ):
        raise ValueError("Exact reviewed SQL revision required.")
    profile = sql["profile"]
    if isinstance(profile, dict) and profile.get("profile") == "p02_observer_return_v1":
        return validate_return_sql_policy(sql)
    if isinstance(profile, dict) and profile.get("profile") == "p02_catalogue_observer_v1":
        return validate_observer_sql_policy(sql)
    if (
        set(profile) != {"version", "profile", "migration_id", "images", "scripts", "requires"}
        or profile["version"] != 1
        or profile["profile"] != "coordinated_recovery_v1"
        or profile["migration_id"]
        not in {
            "20261016_003_guided_recovery_release",
            "20261022_002_p0_completion_release",
            "20261022_004_stats_report_boundary_release",
            "20261023_002_legacy_export_closeout_release",
        }
    ):
        raise ValueError("Exact coordinated recovery profile required.")
    completion = profile["migration_id"] == "20261022_002_p0_completion_release"
    report_boundary = profile["migration_id"] == "20261022_004_stats_report_boundary_release"
    legacy_closeout = profile["migration_id"] == "20261023_002_legacy_export_closeout_release"
    for rows, count, keys, identity, pattern in (
        (
            sql["members"],
            4 if completion or report_boundary or legacy_closeout else 15,
            {"path", "sha256"},
            "path",
            r"(?:deploy|migrations)/[A-Za-z0-9_.-]+",
        ),
        (
            profile["images"],
            6 if legacy_closeout else 1 if report_boundary else 11 if completion else 26,
            {"name", "before", "after"},
            "name",
            r"(?:dbo|KVK)\.[A-Za-z0-9_]+",
        ),
        (
            profile["scripts"],
            1 if completion or report_boundary or legacy_closeout else 12,
            {"id", "sha256"},
            "id",
            r"[0-9]{8}_[0-9]{3}_[a-z0-9_]+",
        ),
        (
            profile["requires"],
            18 if legacy_closeout else 17 if report_boundary else 16 if completion else 11,
            {"migration_id", "sha256", "status"},
            "migration_id",
            r"[0-9]{8}_[0-9]{3}_[a-z0-9_]+",
        ),
    ):
        if len(rows) != count or len({row[identity].casefold() for row in rows}) != count:
            raise ValueError("Complete unique SQL release inventory required.")
        for row in rows:
            if set(row) != keys or not re.fullmatch(pattern, row[identity]):
                raise ValueError("SQL release member shape differs.")
            for key in keys - {identity, "status"}:
                if not re.fullmatch(r"[a-f0-9]{64}", row[key]):
                    raise ValueError("Exact SQL image/member hash required.")
            if "status" in row and row["status"] != "Applied":
                raise ValueError("Applied SQL predecessor required.")
    if report_boundary and (
        [row["name"] for row in profile["images"]] != ["dbo.usp_S11CompleteStatsReports"]
        or [row["id"] for row in profile["scripts"]]
        != ["20261022_003_stats_report_recovery_boundary"]
    ):
        raise ValueError("Exact reporting boundary inventory required.")
    if legacy_closeout and (
        [row["name"] for row in profile["images"]]
        != sorted(
            [
                "dbo.ExportLegacyCloseout",
                "dbo.ExportActiveContainedTarget",
                "dbo.usp_ExportLegacyCloseout",
                "dbo.usp_ExportExecutionStreamTransition",
                "dbo.usp_ExportProviderRequestEventAppend",
                "dbo.usp_ExportReconciliationProofIssue",
            ]
        )
        or [row["id"] for row in profile["scripts"]] != ["20261023_001_legacy_export_closeout"]
    ):
        raise ValueError("Exact legacy closeout inventory required.")
    expected = {
        "deploy/" + name
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.RecoveryRelease.ps1",
        )
    }
    expected.update("migrations/" + row["id"] + ".sql" for row in profile["scripts"])
    members = {row["path"]: row["sha256"] for row in sql["members"]}
    if set(members) != expected or any(
        members["migrations/" + row["id"] + ".sql"] != row["sha256"] for row in profile["scripts"]
    ):
        raise ValueError("SQL adapter and migration payload disagree.")


OBSERVER_MIGRATION = "20261120_001_p02_catalogue_observer"
OBSERVER_PROFILE_SHA256 = "cd3bcb8c1f7303b8b45d5dc2b3d118aad70002f684ae847ffaf400c056bc1692"


def validate_observer_sql_policy(sql):
    """Fixed candidate profile and complete runner closure; no live image adoption."""
    profile = sql["profile"]
    if (
        profile.get("version") != 1
        or profile.get("migration_id") != OBSERVER_MIGRATION
        or profile.get("bootstrap_generation") != 1
        or profile.get("requires")
        != [
            {
                "migration_id": "20261111_001_p02_d4_combined",
                "sha256": "57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171",
                "status": "Applied",
            }
        ]
    ):
        raise ValueError("Exact observer predecessor and profile required.")
    expected = {
        "deploy/" + name
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.P02D4Release.ps1",
            "SqlDeploy.Phase1Release.ps1",
            "SqlDeploy.P02ObserverRelease.ps1",
        )
    }
    expected.update(
        "migrations/" + OBSERVER_MIGRATION + suffix
        for suffix in (".sql", ".release.json", ".before.sql", ".after.sql")
    )
    members = sql["members"]
    if not isinstance(members, list) or len(members) != len(expected):
        raise ValueError("Complete observer runner and SQL inventory required.")
    for row in members:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256"}
            or row["path"] not in expected
            or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"])
        ):
            raise ValueError("Exact observer SQL member required.")
    pins = {row["path"]: row["sha256"] for row in members}
    if (
        set(pins) != expected
        or pins["migrations/" + OBSERVER_MIGRATION + ".release.json"] != OBSERVER_PROFILE_SHA256
    ):
        raise ValueError("Fixed reviewed observer profile bytes required.")
    for item, suffix in (
        (profile["script"], ".sql"),
        (profile["checks"]["before"], ".before.sql"),
        (profile["checks"]["after"], ".after.sql"),
    ):
        if (
            set(item) != {"file", "sha256"}
            or item["file"] != OBSERVER_MIGRATION + suffix
            or pins["migrations/" + item["file"]] != item["sha256"]
        ):
            raise ValueError("Observer source and SQL payload disagree.")


RETURN_PROFILES = {
    "20261123_001_p02_observer_return": (
        "return",
        "c7d24d3e25c3a3f62fba6484e993c26a19fcb8cefe1d55a607027907beced71c",
    ),
    "20261123_002_p02_observer_reupgrade": (
        "reupgrade",
        "4fb8a16cfd8a09420a4d8d11a40a1eb36496fa611e4c16bc6d290b7973f3d577",
    ),
}


def validate_return_sql_policy(sql):
    """Only the reviewed return/reupgrade pair, with the existing runner closure."""
    profile = sql["profile"]
    identity = profile.get("migration_id")
    if identity not in RETURN_PROFILES or profile.get("action") != RETURN_PROFILES[identity][0]:
        raise ValueError("Exact fixed observer return transition required.")
    expected = {
        "deploy/" + name
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.P02D4Release.ps1",
            "SqlDeploy.Phase1Release.ps1",
            "SqlDeploy.P02ObserverRelease.ps1",
            "SqlDeploy.P02ObserverReturn.ps1",
        )
    }
    expected.update(
        "migrations/" + identity + suffix
        for suffix in (".sql", ".release.json", ".before.sql", ".after.sql")
    )
    rows = sql["members"]
    if (
        not isinstance(rows, list)
        or len(rows) != len(expected)
        or any(
            not isinstance(row, dict)
            or set(row) != {"path", "sha256"}
            or row["path"] not in expected
            or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"])
            for row in rows
        )
    ):
        raise ValueError("Complete return SQL runner inventory required.")
    pins = {row["path"]: row["sha256"] for row in rows}
    if (
        set(pins) != expected
        or pins["migrations/" + identity + ".release.json"] != RETURN_PROFILES[identity][1]
    ):
        raise ValueError("Fixed reviewed return profile bytes required.")
    for member, suffix in (
        (profile["script"], ".sql"),
        (profile["checks"]["before"], ".before.sql"),
        (profile["checks"]["after"], ".after.sql"),
    ):
        if (
            set(member) != {"file", "sha256"}
            or member["file"] != identity + suffix
            or pins["migrations/" + member["file"]] != member["sha256"]
        ):
            raise ValueError("Return profile and SQL member disagree.")


def validate_return_contracts(value):
    """Carry the independently approved original incarnation through reupgrade."""
    contracts = value["contracts"]
    if contracts["sql_contract"]["before"] != contracts["sql_contract"]["after"]:
        raise ValueError("Return cannot change the fixed SQL authority contract.")
    phase = "before" if value["sql"]["profile"]["action"] == "return" else "after"
    plain = "after" if phase == "before" else "before"
    for name in ("legacy_sql_contract", "application_sql_contract"):
        observed, predecessor = contracts[name][phase], contracts[name][plain]
        if observed.get("observer_installation") != OBSERVER_MIGRATION or any(
            key in predecessor for key in ("observer_installation", "observation_installation")
        ):
            raise ValueError("Exact observer and predecessor contract pair required.")
    installed = contracts["application_sql_contract"][phase].get("observation_installation")
    if not isinstance(installed, dict) or not installed:
        raise ValueError("Retained issued observer incarnation required; no new installation.")
    if "observation_installation" in contracts["legacy_sql_contract"][phase]:
        raise ValueError("Only the application contract carries the original incarnation.")


def selected_specification(before):
    value = specification()
    specs = value["releases"] if value.get("version") == 2 else [value]
    return next((spec for spec in specs if spec["before"] == before), None)


def possible_paths(before, changes):
    spec = selected_specification(before)
    if spec is None:
        return set()
    paths = {row["path"] for row in spec["sources"]}
    if before != spec["before"] or not paths.intersection(changes):
        return set()
    if not paths <= set(changes):
        raise ValueError("Incomplete coordinated recovery source inventory.")
    return paths


def selected(before, target, changes, read_blob):
    paths = possible_paths(before, changes)
    if not paths:
        return None
    spec = selected_specification(before)
    if spec is None:
        raise ValueError("Protected recovery policy changed during selection.")
    for row in spec["sources"]:
        for commit, field in ((before, "before"), (target, "after")):
            raw = read_blob(commit, row["path"])
            actual = sha(raw.replace(b"\r\n", b"\n")) if raw is not None else None
            if actual != row[field]:
                raise ValueError("Protected recovery source differs: " + row["path"])
    return spec


def sql_payload(spec, environment, read_blob):
    sql = spec["sql"]
    if not isinstance(environment, dict) or set(environment) != {
        "server",
        "database",
        "database_collation",
        "tempdb_collation",
        "compatibility_level",
    }:
        raise ValueError("Complete fresh SQL environment observation required.")
    if any(
        not isinstance(environment[key], str)
        for key in ("server", "database", "database_collation", "tempdb_collation")
    ):
        raise ValueError("SQL environment identity and collations must be strings.")
    before = spec["contracts"]["sql_contract"]["before"]
    if (
        environment["server"].casefold() != before["server"].casefold()
        or environment["database"] != before["database"]
        or environment["database_collation"] != before["collation"]
    ):
        raise ValueError("Recovery SQL environment belongs to another installation.")
    if (
        type(environment["compatibility_level"]) is not int
        or environment["compatibility_level"] not in (130, 140, 150, 160)
        or not re.fullmatch(r"[A-Za-z0-9_]{1,128}", environment["tempdb_collation"])
    ):
        raise ValueError("Unsupported SQL compatibility/collation.")
    files = {}
    for item in sql["members"]:
        path = item["path"]
        if not re.fullmatch(r"(?:deploy|migrations)/[A-Za-z0-9_.-]+", path):
            raise ValueError("Fixed SQL member path required.")
        raw = read_blob(path)
        name = path.split("/")[1]
        if name in files or not raw or len(raw) > 2 * 1024 * 1024 or sha(raw) != item["sha256"]:
            raise ValueError("Reviewed recovery SQL member differs: " + path)
        files[name] = raw
    profile = deepcopy(sql["profile"])
    name = profile["migration_id"] + ".release.json"
    if profile.get("profile") in {"p02_catalogue_observer_v1", "p02_observer_return_v1"}:
        validate_sql_policy(sql)
        raw = files[name]
        expected = (
            OBSERVER_PROFILE_SHA256
            if profile["profile"] == "p02_catalogue_observer_v1"
            else RETURN_PROFILES[profile["migration_id"]][1]
        )
        if sha(raw) != expected or json.loads(raw) != profile:
            raise ValueError(
                "Exact sealed observer profile required; no serialization replacement."
            )
        if any(
            profile[key] != environment[key]
            for key in ("database_collation", "tempdb_collation", "compatibility_level")
        ):
            raise ValueError("Observer environment differs from the reviewed release.")
        return (
            dict(
                commit=sql["commit"],
                profiles=[dict(id=profile["migration_id"], file=name, sha256=sha(raw))],
                members=[dict(name=n, sha256=sha(b)) for n, b in sorted(files.items())],
            ),
            files,
        )
    profile.update(
        {
            key: environment[key]
            for key in ("database_collation", "tempdb_collation", "compatibility_level")
        }
    )
    name = profile["migration_id"] + ".release.json"
    files[name] = encode(profile)
    return (
        dict(
            commit=sql["commit"],
            profiles=[dict(id=profile["migration_id"], file=name, sha256=sha(files[name]))],
            members=[dict(name=n, sha256=sha(b)) for n, b in sorted(files.items())],
        ),
        files,
    )


def adapt_candidate(seed, spec):
    """Bind reviewed successor expectations; actual observation is collected later."""
    values = {n: json.loads(b) for n, b in seed.items() if n.endswith(".json")}
    bot, authority = values["bot-template.json"], values["authority-template.json"]
    if authority["sql_contract"] != spec["contracts"]["sql_contract"]["before"]:
        raise ValueError("Authority predecessor SQL contract differs.")
    for key, pair in spec["contracts"].items():
        if bot[key] != pair["before"]:
            raise ValueError("Bot predecessor SQL contract differs: " + key)
        bot[key] = deepcopy(pair["after"])
    authority["sql_contract"] = deepcopy(bot["sql_contract"])
    # Keep the old observation intact in this candidate. It cannot pass admission
    # until the approved post-SQL verifier collects real evidence and seals it.
    authority["deployment_boundary"]["sql_contract_hash"] = sha(encode(bot["sql_contract"]))
    plan = values["ManualProcessPairPlan-CANDIDATE.json"]
    for role in ("bot", "authority"):
        plan["templates"][role]["sha256"] = sha(encode(values[role + "-template.json"]))
    old_hash = sha(seed["AutomaticStartupPolicy.json"])
    values["AutomaticStartupPolicy.json"]["seed_plan"]["sha256"] = sha(encode(plan))
    result = {**seed, **{n: encode(v) for n, v in values.items()}}
    gate = seed["Start-ReviewedAutomaticStartup.ps1"].decode()
    if gate.count(old_hash) != 1:
        raise ValueError("Exact candidate gate policy binding required.")
    result["Start-ReviewedAutomaticStartup.ps1"] = gate.replace(
        old_hash, sha(result["AutomaticStartupPolicy.json"])
    ).encode()
    return result
