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
    if set(value) != {"version", "before", "sources", "contracts", "sql"} or value["version"] != 1:
        raise ValueError("Exact installed recovery policy required.")
    if not re.fullmatch(r"[a-f0-9]{40}", value["before"]):
        raise ValueError("Exact recovery predecessor required.")
    if not 1 <= len(value["sources"]) <= 128:
        raise ValueError("Bounded protected recovery inventory required.")
    paths = set()
    for row in value["sources"]:
        if set(row) != {"path", "before", "after"} or not re.fullmatch(
            r"(?:core|services|scripts|ui/views)/[a-z_]+\.py|(?:run_bot|bot_config|constants|processing_pipeline|file_utils)\.py",
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
    return value


def validate_sql_policy(sql):
    if set(sql) != {"commit", "members", "profile"} or not re.fullmatch(
        r"[a-f0-9]{40}", sql["commit"]
    ):
        raise ValueError("Exact reviewed SQL revision required.")
    profile = sql["profile"]
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


def possible_paths(before, changes):
    spec = specification()
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
    spec = specification()
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
