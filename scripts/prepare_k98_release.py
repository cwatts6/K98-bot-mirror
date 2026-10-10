"""Package reviewed release steps; never connect to SQL or change a live install.

Run from the repository with ``python -m scripts.prepare_k98_release``. The input
specification selects the reviewed apply/verify scripts and explicit arguments.
This tool calculates their checksums; it does not decide which migrations to run.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
from uuid import UUID


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_manifest(value):
    """Generic reviewed packets retain the non-replaying v1-v3 protocol."""
    _validate_manifest(value, versions=(1, 2, 3))


def validate_updater_manifest(value):
    """V4 continuation is reserved for the normal updater's fixed adapters."""
    _validate_manifest(value, versions=(4,))
    bindings = [m for m in value["members"] if m["name"] == "ReleaseBindings.json"]
    if len(bindings) != 1:
        raise ValueError("Updater requires exact release bindings.")
    binding_hash = bindings[0]["sha256"]

    def invocation(action, migration=None):
        arguments = dict(Action=action, ExpectedBindingsSHA256=binding_hash)
        if migration is not None:
            arguments["MigrationId"] = migration
        return dict(file="Release-Step.ps1", arguments=arguments)

    expected = []
    for index, step in enumerate(s for s in value["steps"] if s["kind"] == "sql"):
        migration = step["apply"]["arguments"].get("MigrationId")
        if not isinstance(migration, str) or not re.fullmatch(
            r"[0-9]{8}_[0-9]{3}_[a-z0-9_]+", migration
        ):
            raise ValueError("Updater SQL step requires exact migration identity.")
        expected.append(
            dict(
                id=f"sql-{index:02d}",
                kind="sql",
                apply=invocation("ApplySql", migration),
                verify=invocation("VerifySql", migration),
            )
        )
    for kind, apply, verify in (
        ("source", "ApplySource", "VerifySource"),
        ("seed", "ApplySeed", "VerifySeed"),
        ("start", "ApplyStart", "VerifyStart"),
        ("readiness", "AwaitReadiness", "VerifyReadiness"),
    ):
        expected.append(
            dict(id=kind, kind=kind, apply=invocation(apply), verify=invocation(verify))
        )
    if value["preflight"] != invocation("Preflight") or value["steps"] != expected:
        raise ValueError("V4 requires the exact normal-updater adapter layout.")


def _validate_manifest(value, *, versions):
    """Validate the runner's bounded, ordered release protocol before packaging."""
    fields = {
        "version",
        "release_id",
        "host",
        "application_sid",
        "repository",
        "policy",
        "issuer_launcher",
        "members",
        "preflight",
        "steps",
    }
    if isinstance(value, dict) and value.get("version") in (2, 3):
        fields.add("amendment")
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Exact release manifest fields required.")
    if type(value["version"]) is not int or value["version"] not in versions:
        raise ValueError("Unsupported release version.")
    if value["version"] in (2, 3):
        amendment = value["amendment"]
        amendment_fields = {"id", "base_manifest_sha256", "failed_step_id"}
        if value["version"] == 3:
            amendment_fields.add("parent_amendment_id")
        if (
            not isinstance(amendment, dict)
            or set(amendment) != amendment_fields
            or not isinstance(amendment["id"], str)
            or str(UUID(amendment["id"])) != amendment["id"]
            or not isinstance(amendment["base_manifest_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", amendment["base_manifest_sha256"])
            or not isinstance(amendment["failed_step_id"], str)
            or not re.fullmatch(r"[a-z0-9-]{1,60}", amendment["failed_step_id"])
        ):
            raise ValueError("Exact first-SQL-step amendment reference required.")
        if value["version"] == 3 and (
            not isinstance(amendment["parent_amendment_id"], str)
            or str(UUID(amendment["parent_amendment_id"])) != amendment["parent_amendment_id"]
            or amendment["parent_amendment_id"] == amendment["id"]
        ):
            raise ValueError("Exact distinct selected-parent amendment required.")
    if str(UUID(value["release_id"])) != value["release_id"]:
        raise ValueError("Canonical release ID required.")
    for field in ("host", "application_sid", "repository"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError("Explicit release identity required.")
    for field in ("policy", "issuer_launcher"):
        ref = value[field]
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
            raise ValueError("Pinned installed policy and interpreter required.")
        if not isinstance(ref["path"], str) or not ref["path"]:
            raise ValueError("Installed reference path required.")
        if not isinstance(ref["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]):
            raise ValueError("Installed reference checksum required.")
    members = value["members"]
    if not isinstance(members, list) or not 1 <= len(members) <= 128:
        raise ValueError("Bounded release inventory required.")
    names = set()
    for member in members:
        if not isinstance(member, dict) or set(member) != {"name", "sha256"}:
            raise ValueError("Exact release member required.")
        name = member["name"]
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}", name)
            or name.casefold() in names
            or name.endswith(".")
            or name.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(10)),
                *(f"LPT{i}" for i in range(10)),
            }
            or name.casefold() in {"release.json", "deploy-k98release.ps1"}
        ):
            raise ValueError("Unique ordinary flat release filename required.")
        if not isinstance(member["sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", member["sha256"]
        ):
            raise ValueError("Release member checksum required.")
        names.add(name.casefold())

    def invocation(item):
        if not isinstance(item, dict) or set(item) != {"file", "arguments"}:
            raise ValueError("Explicit script invocation required.")
        if (
            not isinstance(item["file"], str)
            or item["file"].casefold() not in names
            or not item["file"].endswith(".ps1")
        ):
            raise ValueError("Listed PowerShell script required.")
        if not isinstance(item["arguments"], dict) or len(item["arguments"]) > 32:
            raise ValueError("Bounded explicit arguments required.")
        for name, argument in item["arguments"].items():
            if (
                not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name)
                or not isinstance(argument, str)
                or len(argument) > 4096
                or "\x00" in argument
            ):
                raise ValueError("Explicit string arguments required.")

    invocation(value["preflight"])
    steps = value["steps"]
    if not isinstance(steps, list) or not 3 <= len(steps) <= 32:
        raise ValueError("Bounded ordered release steps required.")
    order = {"sql": 1, "source": 2, "seed": 3, "start": 4, "readiness": 5}
    last, ids, counts = 0, set(), {}
    for step in steps:
        if not isinstance(step, dict) or set(step) != {"id", "kind", "apply", "verify"}:
            raise ValueError("Exact release step fields required.")
        name, kind = step["id"], step["kind"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,60}", name) or name in ids:
            raise ValueError("Unique release step ID required.")
        if not isinstance(kind, str) or kind not in order or order[kind] < last:
            raise ValueError("SQL/source/seed/start/readiness order required.")
        last = order[kind]
        ids.add(name)
        counts[kind] = counts.get(kind, 0) + 1
        invocation(step["apply"])
        invocation(step["verify"])
    if any(counts.get(kind) != 1 for kind in ("seed", "start", "readiness")):
        raise ValueError("Exactly one seed, start and readiness step required.")
    if value["version"] in (2, 3) and (
        steps[0]["kind"] != "sql" or value["amendment"]["failed_step_id"] in ids
    ):
        raise ValueError("Amendment must begin with a distinct corrective SQL step.")


def prepare(specification, output, runner):
    specification, output, runner = map(Path, (specification, output, runner))
    raw = specification.read_bytes()
    if len(raw) > 65536:
        raise ValueError("Release specification exceeds its bound.")
    manifest = json.loads(raw)
    payload = {}
    # Specification members are filenames relative to the reviewed packet.
    # Do not copy arbitrary paths or dynamically discover migrations.
    for member in manifest.get("members", []):
        name = member.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}", name):
            raise ValueError("Flat packet filename required.")
        path = specification.parent / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Bounded ordinary packet file required.")
        contents = path.read_bytes()
        if len(contents) > 16 * 1024 * 1024:
            raise ValueError("Packet file exceeds its bound.")
        # Supplied reviewed checksums are assertions, never silently overwritten.
        if member.get("sha256") not in (None, digest(contents)):
            raise ValueError("Reviewed packet member changed.")
        member["sha256"] = digest(contents)
        payload[name] = contents
    validate_manifest(manifest)
    encoded = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > 65536:
        raise ValueError("Encoded release exceeds runner's bound.")
    payload["release.json"] = encoded
    payload["Deploy-K98Release.ps1"] = runner.read_bytes()
    output.mkdir(parents=False, exist_ok=False)
    for name, contents in payload.items():
        with (output / name).open("xb") as stream:
            stream.write(contents)
    return dict(
        stage="RELEASE_PACKET_PREPARED_NOT_INSTALLED",
        release_id=manifest["release_id"],
        manifest=str((output / "release.json").resolve()),
        manifest_sha256=digest(encoded),
        runner_sha256=digest(payload["Deploy-K98Release.ps1"]),
        files=len(payload),
        production_changed=False,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            prepare(
                args.specification,
                args.output,
                Path(__file__).with_name("Deploy-K98Release.ps1"),
            )
        )
    )


if __name__ == "__main__":
    main()
