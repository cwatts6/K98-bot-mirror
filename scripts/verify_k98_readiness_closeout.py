"""Read-only verification of an explicitly reviewed successor after lost readiness.

Does not invoke the release runner, start processes, settle work or write receipts.
The operator launcher separately records current Discord confirmation.
"""

import argparse
from contextlib import ExitStack
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import runpy
import sys


def checked_read(path, expected, limit=2 * 1024 * 1024):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Reviewed closeout bytes differ")
    return raw


def verify_chain(config, profile, predecessor, journals, sessions):
    """No age, missing-PID or log-text inference substitutes for this lineage."""
    if (
        config["release_id"] != profile["release_id"]
        or config["target"] != profile["target"]
        or config["new_policy_sha256"] != profile["policy_sha256"]
        or predecessor != config["old_journal"]["Record"]
        or len(journals) != len(profile["journals"])
        or not 1 <= len(journals) <= 16
    ):
        raise ValueError("Exact reviewed release and bounded lineage required")
    by_id = {str(row["SessionID"]).lower(): row for row in sessions}
    if len(by_id) != len(sessions) or set(by_id) != set(profile["sessions"]):
        raise ValueError("Exact reviewed SQL sessions required")
    for index, journal in enumerate(journals):
        if (
            type(journal["sequence"]) is not int
            or journal["sequence"] != predecessor["sequence"] + index + 1
            or journal["policy_sha256"] != config["new_policy_sha256"]
        ):
            raise ValueError("Successor sequence or policy differs")
    publications = [predecessor, *journals]
    ordered_sessions = []
    for index, previous in enumerate(publications):
        current = index == len(publications) - 1
        matches = [
            row
            for row in sessions
            if row["ManifestHash"].lower() == previous["publication"]["manifests"]["authority"]
        ]
        if len(matches) != 1:
            raise ValueError("One SQL session per exact publication required")
        row = matches[0]
        if (
            row["AuthorityPrincipal"] != "S11_ExportApplication"
            or row["HostIdentity"].lower() != "mini_amd"
            or row["State"] != ("open" if current else "closed")
            or row["Version"] != (1 if current else 2)
            or (row["ClosedUTC"] is None) != current
            or (not current and row["ClosedUTC"] < row["CreatedUTC"])
        ):
            raise ValueError("SQL publication lifecycle differs")
        if ordered_sessions and ordered_sessions[-1]["ClosedUTC"] > row["CreatedUTC"]:
            raise ValueError("Successor SQL sessions overlap")
        ordered_sessions.append(row)
    if str(ordered_sessions[-1]["SessionID"]).lower() != profile["current_session"]:
        raise ValueError("Current SQL session differs")


def verify(profile, config, verifier):
    policy = verifier["verify_live_source"](config)
    verifier["verify_sql_contracts"](config, policy)
    from core.export_deployment_handoff import RecordedTermination, termination_path
    from core.export_process_identity import open_pinned_process
    from core.export_startup_windows import administrative_path, signalled
    from kvk.dal.new_source_admin_dal import configured_connection

    def protected(path, expected=None):
        path = administrative_path(path, private=True)
        if expected:
            return json.loads(checked_read(path, expected))
        raw = verifier["read"](path)
        return json.loads(raw)

    if config["new_state_directory"] != policy["state_directory"]:
        raise ValueError("Current state directory differs from policy")
    state = administrative_path(config["new_state_directory"], private=True)
    paths = sorted(Path(state).glob("incarnation-*.json"))
    if [p.name for p in paths] != [r["name"] for r in profile["journals"]]:
        raise ValueError("Successor history advanced; obtain fresh review")
    journals = [
        protected(path, row["sha256"]) for path, row in zip(paths, profile["journals"], strict=True)
    ]
    predecessor = protected(config["old_journal"]["Path"], config["old_journal"]["SHA256"])
    # Require the issuer's original, exact retained-handle termination receipt.
    # Never manufacture it or use an absent process as proof.
    RecordedTermination(
        predecessor,
        termination_path(config["old_policy"]["StateDirectory"], predecessor),
        administrative_path,
    ).verify()
    for previous in journals[:-1]:
        RecordedTermination(
            previous, termination_path(state, previous), administrative_path
        ).verify()
    seed = protected(policy["seed_plan"]["path"], policy["seed_plan"]["sha256"])
    current = journals[-1]
    publication_id = paths[-1].stem.removeprefix(f"incarnation-{current['sequence']:020d}-")
    live = Path(seed["commit_file"]).parent.parent / publication_id
    publication = protected(live / "commit.json")
    if publication != current["publication"]:
        raise ValueError("Current publication differs from protected journal")
    plan = protected(live / "ManualProcessPairPlan-CANDIDATE.json", publication["plan_sha256"])
    if set(publication["manifests"]) != {"authority", "bot"} or set(current["bindings"]) != {
        "authority",
        "bot",
    }:
        raise ValueError("Exact supervised process pair required")
    for role, expected in publication["manifests"].items():
        protected(plan["manifests"][role], expected)
    issuer = protected(live / "AutomaticIssuer.json")
    if issuer["plan_sha256"] != publication["plan_sha256"]:
        raise ValueError("Issuer publication differs")
    bindings = [*current["bindings"].values(), issuer["issuer"]]
    if len({b["pid"] for b in bindings}) != 3:
        raise ValueError("Three distinct native process identities required")
    with ExitStack() as stack:
        handles = []
        for binding in bindings:
            handle = open_pinned_process(binding["pid"], binding)
            stack.callback(handle.Close)
            handles.append(handle)
        # The existing reviewed connection profile is selected by the installed policy.
        ref = seed["templates"]["bot"]
        bot = protected(ref["path"], ref["sha256"])
        connection = configured_connection(sql_profile=bot["sql_contract"]["profile"])
        connection.timeout = 15
        stack.callback(connection.close)
        cursor = connection.cursor()
        stack.callback(cursor.close)
        cursor.execute(
            "SELECT SessionID,AuthorityPrincipal,HostIdentity,CONVERT(varchar(64),ManifestHash,2) AS ManifestHash,"
            "State,Version,CreatedUTC,ClosedUTC FROM dbo.ExportExecutionSession "
            "WHERE HostIdentity='MINI_AMD' COLLATE Latin1_General_100_CI_AS "
            "AND (State='open' OR SessionID IN (?,?,?))",
            *profile["sessions"],
        )
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchmany(17)
        if len(rows) > 16:
            raise ValueError("SQL session inventory exceeds bound")
        sessions = [dict(zip(columns, row, strict=True)) for row in rows]
        verify_chain(config, profile, predecessor, journals, sessions)
        cursor.execute(
            "SELECT TOP (1) StreamID FROM dbo.ExportExecutionStream "
            "WHERE SessionID IN (?,?) AND State<>'closed'",
            *[key for key in profile["sessions"] if key != profile["current_session"]],
        )
        if cursor.fetchone():
            raise ValueError("A previous session retains an open provider stream")
        if any(signalled(h) for h in handles):
            raise ValueError("Current native process exited during verification")
        if sorted(p.name for p in Path(state).glob("incarnation-*.json")) != [
            p.name for p in paths
        ]:
            raise ValueError("Incarnation changed during verification")
        return dict(
            stage="CURRENT_SUCCESSOR_VERIFIED",
            release_id=config["release_id"],
            target=config["target"],
            sequence=current["sequence"],
            session_id=profile["current_session"],
            observed_utc=datetime.now(UTC).isoformat(),
            original_readiness="unconfirmed_preserved",
            import_export="degraded",
            provider_delivery_verified=False,
            discord_verified=False,
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if not sys.flags.isolated:
        raise ValueError("Isolated Python required")
    profile = json.loads(checked_read(args.profile, args.sha256))
    config = json.loads(checked_read(profile["bindings"], profile["bindings_sha256"]))
    members = [m for m in config["extra_members"] if m["name"] == "Verify-NewPair.py"]
    if len(members) != 1:
        raise ValueError("Retained verifier identity required")
    helper = Path(profile["bindings"]).parent / "Verify-NewPair.py"
    checked_read(helper, members[0]["sha256"])
    verifier = runpy.run_path(str(helper))
    print(json.dumps(verify(profile, config, verifier)))


if __name__ == "__main__":
    main()
