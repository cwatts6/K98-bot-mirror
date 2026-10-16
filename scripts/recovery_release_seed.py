"""Derive a successor SQL observation from retained, independently checked SQL rows.

No deployment admission rule is changed. The full catalog observations must pass
the existing startup comparators against the immutable reviewed contracts. The
summary identity and installed contract fingerprint are reconstructed from those
actual rows; expected values never stand in for a collected observation.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4


def encode(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def checksum(value):
    return hashlib.sha256(encode(value)).hexdigest()


def sql_observation(bot, prior_record, collected):
    from kvk.dal.new_source_import_dal import digest
    from services.export_runtime_composition import (
        verify_application_installation_contract,
        verify_installation_contract,
        verify_legacy_installation_contract,
    )

    if set(collected) != {"observed_utc", "installation", "legacy", "application"}:
        raise ValueError("Complete collected SQL evidence required.")
    stamp = datetime.fromisoformat(collected["observed_utc"].replace("Z", "+00:00"))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Collected UTC observation time required.")
    approved = bot["sql_contract"]
    installed = collected["installation"]
    verify_installation_contract(installed, approved)
    verify_legacy_installation_contract(
        collected["legacy"], bot["legacy_sql_contract"], profile=approved["profile"]
    )
    verify_application_installation_contract(
        collected["application"], bot["application_sql_contract"]
    )
    target = installed["target"]
    actual_contract = deepcopy(approved)
    actual_contract.update(
        server=target["ServerName"],
        database=target["DatabaseName"],
        principal=target["Principal"],
        collation=target["DatabaseCollation"],
        metadata_hash=digest(installed["metadata"]).hex(),
        migration_hashes={
            m["MigrationId"]: m["ChecksumSha256"].lower() for m in installed["migrations"]
        },
    )
    if actual_contract != approved:
        raise ValueError("Collected SQL contract differs from reviewed expected contract.")
    record = deepcopy(prior_record)
    if set(record) != {"version", "kind", "deployment_id", "review_id", "observations"} or (
        record["version"] != 1 or record["kind"] != "sql_installation"
    ):
        raise ValueError("Exact deployment SQL observation record required.")
    record["observations"] = [
        dict(
            contract_sha256=checksum(actual_contract),
            observed_utc=collected["observed_utc"],
            server=target["ServerName"],
            database=target["DatabaseName"],
            principal=target["Principal"],
        )
    ]
    return record


def verified_seed(candidate, collected):
    """Return deterministic seed bytes from complete retained live SQL evidence."""
    values = {n: json.loads(b) for n, b in candidate.items() if n.endswith(".json")}
    bot = values["bot-template.json"]
    authority = values["authority-template.json"]
    if authority["sql_contract"] != bot["sql_contract"]:
        raise ValueError("Candidate bot/authority SQL contracts differ.")
    record = sql_observation(bot, values["sql_installation.json"], collected)
    values["sql_installation.json"] = record
    boundary = authority["deployment_boundary"]
    boundary["sql_contract_hash"] = record["observations"][0]["contract_sha256"]
    boundary["review"]["records"]["sql_installation"]["sha256"] = checksum(record)
    plan = values["ManualProcessPairPlan-CANDIDATE.json"]
    for role in ("bot", "authority"):
        plan["templates"][role]["sha256"] = checksum(values[role + "-template.json"])
    old_policy_hash = hashlib.sha256(candidate["AutomaticStartupPolicy.json"]).hexdigest()
    values["AutomaticStartupPolicy.json"]["seed_plan"]["sha256"] = checksum(plan)
    output = {**candidate, **{n: encode(v) for n, v in values.items()}}
    gate = candidate["Start-ReviewedAutomaticStartup.ps1"].decode("utf-8")
    if gate.count(old_policy_hash) != 1:
        raise ValueError("Exact candidate gate binding required.")
    output["Start-ReviewedAutomaticStartup.ps1"] = gate.replace(
        old_policy_hash, checksum(values["AutomaticStartupPolicy.json"])
    ).encode()
    return output


def effective_bindings(config, files):
    result = deepcopy(config)
    result["seed_members"] = [
        dict(name=n, sha256=hashlib.sha256(b).hexdigest()) for n, b in sorted(files.items())
    ]
    result["new_policy"] = json.loads(files["AutomaticStartupPolicy.json"])
    result["new_policy_sha256"] = checksum(result["new_policy"])
    for key in ("source_hashes", "flags", "state_directory", "predecessor"):
        if result["new_policy"][key] != config["new_policy"][key]:
            raise ValueError("SQL observation changed operational policy.")
    if result["new_policy"]["seed_plan"]["path"] != config["new_policy"]["seed_plan"]["path"]:
        raise ValueError("SQL observation changed the seed location.")
    return result


def candidate_files(config, directory, read):
    files = {}
    for item in config["seed_members"]:
        name = item["name"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,120}", name) or name in files:
            raise ValueError("Unique flat seed filenames required.")
        raw = read(directory / name)
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Immutable candidate seed differs: " + name)
        files[name] = raw
    return files


def prepare_verified_files(config, binding_hash, candidate, proof):
    if set(proof) != {"release_id", "bindings_sha256", "collected"} or (
        proof["release_id"] != config["release_id"] or proof["bindings_sha256"] != binding_hash
    ):
        raise ValueError("Collected SQL evidence belongs to another release.")
    files = verified_seed(candidate, proof["collected"])
    return {**files, "bindings.json": encode(effective_bindings(config, files))}


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    if not sys.flags.isolated:
        raise ValueError("Isolated reviewed Python required.")
    path = Path(args.bindings)
    with path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError("Immutable release bindings differ.")
    config = json.loads(raw)
    if config.get("recovery_seed") != "live_sql_observation_v1":
        raise ValueError("Exact coordinated recovery seed mode required.")
    # The native adapter authenticates complete target source and this helper
    # before invocation. Imports use that verified checkout, never target payload.
    sys.path.insert(0, config["root"])
    from core.export_startup_windows import administrative_path
    from scripts.prepare_k98_update import output_writers
    from scripts.verify_k98_update_pair import verify_bot_sql_contracts

    def read(member):
        protected = administrative_path(member, private=True)
        with protected.open("rb") as stream:
            value = stream.read(32 * 1024 * 1024 + 1)
        if not value or len(value) > 32 * 1024 * 1024:
            raise ValueError("Bounded protected SQL evidence required.")
        return value

    if read(path) != raw:
        raise ValueError("Protected binding readback differs.")
    candidate = candidate_files(config, path.parent, read)
    # This returns actual complete SQL query results only after all three live
    # comparisons pass. Retain those results, including their collection time.
    collected = verify_bot_sql_contracts(json.loads(candidate["bot-template.json"]))
    directory = path.parent / "verified-seed"
    if not directory.exists():
        if not args.create:
            return 10
        mkdir, _ = output_writers(config["sid"], secure_output=True)
        mkdir(directory)
    administrative_path(directory, private=True)
    proof_path = directory / "sql-evidence.json"

    def retain(name, content):
        target = directory / name
        if target.exists():
            if read(target) != content:
                raise ValueError("Existing verified seed differs: " + name)
            return
        _, write = output_writers(config["sid"], secure_output=True)
        scratch = directory / ("pending-" + uuid4().hex)
        write(scratch, content)
        scratch.rename(target)
        if read(target) != content:
            raise ValueError("Verified seed write/readback differs.")

    if not proof_path.exists():
        if any(
            not re.fullmatch(r"pending-[0-9a-f]{32}", p.name) or not p.is_file()
            for p in directory.iterdir()
        ):
            raise ValueError("Unexpected seed state without collected SQL evidence.")
        if not args.create:
            return 11
        retain(
            "sql-evidence.json",
            encode(
                dict(
                    release_id=config["release_id"],
                    bindings_sha256=args.sha256,
                    collected=collected,
                )
            ),
        )
    proof = json.loads(read(proof_path))
    files = prepare_verified_files(config, args.sha256, candidate, proof)
    for member in directory.iterdir():
        if member.name not in {*files, "sql-evidence.json"} and not re.fullmatch(
            r"pending-[0-9a-f]{32}", member.name
        ):
            raise ValueError("Unknown verified seed member.")
        administrative_path(member, private=True)
        if not member.is_file():
            raise ValueError("Unexpected verified seed directory.")
    complete = True
    for name, content in files.items():
        if args.create:
            retain(name, content)
        elif not (directory / name).exists():
            complete = False
        elif read(directory / name) != content:
            raise ValueError("Verified seed differs from collected evidence: " + name)
    if not complete:
        return 11
    print(json.dumps(dict(stage="RECOVERY_SEED_LIVE_SQL_VERIFIED", provider_work=False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
