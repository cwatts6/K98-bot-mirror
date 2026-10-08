"""Generate routine source-only release inputs from the protected installed seed.

This module never installs source, connects to SQL, or starts processes. The
Windows updater owns acquisition, custody checks and the deployment protocol.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from uuid import uuid4

if __name__ == "__main__" and not __package__:
    # The Windows launcher verifies installed source and administrator custody
    # before invoking this file with the pinned venv and -I -B.
    sys.path.insert(0, "C:/discord_file_downloader")

from core.export_release_seed import successor_seed
from services.export_execution_protocol import encode


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary_path(path):
    """Reject paths whose Windows interpretation differs from a Git tree path."""
    if (
        not isinstance(path, str)
        or len(path) > 240
        or not re.fullmatch(r"[A-Za-z0-9_ .()/+-]+", path)
        or any(
            part in {"", ".", ".."}
            or part.endswith((".", " "))
            or part.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(10)),
                *(f"LPT{i}" for i in range(10)),
            }
            for part in path.split("/")
        )
        or path.casefold().startswith((".git/", "venv/", ".venv/"))
    ):
        raise ValueError(f"Unsupported source path: {path!r}")
    return path


def check_source_only(paths):
    """Routine mode cannot silently install dependencies, SQL or environment."""
    for path in paths:
        ordinary_path(path)
        lower = path.casefold()
        if lower.startswith(
            ("requirements", "sql/", "migrations/", "config/", ".env")
        ) or lower in {"pyproject.toml", "poetry.lock", "uv.lock", "pipfile", "pipfile.lock"}:
            raise ValueError(f"Release includes a non-source contract change: {path}")


def source_plan(previous, before, target, changes, read_blob):
    """Build exact source hashes using authenticated Git blobs, not live new bytes.

    ``changes`` contains ordinary add/modify/delete paths; renames are represented
    as delete+add. ``read_blob(commit, path)`` returns bytes or None for absence.
    Preserve installed newline conventions for existing source pins. New members
    use repository blob bytes; installation must explicitly verify those bytes.
    """
    if any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in (before, target)):
        raise ValueError("Exact private-main commits required.")
    if before == target:
        raise ValueError("Source is already current.")
    if not changes or len(changes) > 4096 or len(set(changes)) != len(changes):
        raise ValueError("Bounded unique changed paths required.")
    check_source_only(changes)
    folded = [path.casefold() for path in changes]
    if len(set(folded)) != len(folded):
        raise ValueError("Case-colliding source paths refused.")
    pins = deepcopy(previous["AutomaticStartupPolicy.json"]["source_hashes"])
    conventions = {}
    for path, digest in pins.items():
        ordinary_path(path)
        raw = read_blob(before, path)
        if raw is None:
            raise ValueError(f"Installed source absent from predecessor: {path}")
        lf = raw.replace(b"\r\n", b"\n")
        if sha256(raw) == digest:
            conventions[path] = b"\r\n" if b"\r\n" in raw else b"\n"
        elif sha256(lf) == digest:
            conventions[path] = b"\n"
        elif sha256(lf.replace(b"\n", b"\r\n")) == digest:
            conventions[path] = b"\r\n"
        else:
            raise ValueError(f"Installed policy does not match predecessor source: {path}")
    members, payload = [], {}
    for path in sorted(changes):
        old, new = read_blob(before, path), read_blob(target, path)
        if old == new or (old is None and new is None):
            raise ValueError(f"Changed-path inventory differs: {path}")
        if any(raw is not None and len(raw) > 2 * 1024 * 1024 for raw in (old, new)):
            raise ValueError(f"Source member exceeds bound: {path}")
        runtime = path in pins or (
            path.endswith(".py") and not path.startswith(("tests/", "docs/"))
        )
        if new is None:
            pins.pop(path, None)
        else:
            if path in conventions:
                new = new.replace(b"\r\n", b"\n").replace(b"\n", conventions[path])
            payload[path] = new
            if runtime:
                pins[path] = sha256(new)
        members.append(
            dict(
                path=path,
                target_sha256=sha256(new) if new is not None else None,
                runtime=runtime,
                deleted=new is None,
            )
        )
    if sum(map(len, payload.values())) > 64 * 1024 * 1024:
        raise ValueError("Source payload exceeds bound.")
    # Verify unchanged pins against the target as well: a missing diff member
    # must never produce a policy for a mixed predecessor/successor source tree.
    for path, digest in pins.items():
        raw = payload.get(path)
        if raw is None:
            raw = read_blob(target, path)
            if raw is None:
                raise ValueError(f"Target source pin is missing: {path}")
            raw = raw.replace(b"\r\n", b"\n").replace(b"\n", conventions[path])
        if sha256(raw) != digest:
            raise ValueError(f"Target inventory omitted changed source: {path}")
    return dict(before=before, target=target, source_members=members, new_pins=pins), payload


def release_seed(previous, pins, gate):
    """Derive fresh metadata and update only exact predecessor gate bindings."""
    deployment, review, pipe = (str(uuid4()) for _ in range(3))
    payload = successor_seed(
        previous, pins, deployment_id=deployment, review_id=review, pipe_id=pipe
    )
    old = previous["AutomaticStartupPolicy.json"]
    new = json.loads(payload["AutomaticStartupPolicy.json"])
    old_directory = str(PureWindowsPath(old["seed_plan"]["path"]).parent)
    new_directory = str(PureWindowsPath(new["seed_plan"]["path"]).parent)
    # A launch gate remains reviewed code. No eval, regex template engine or
    # guessed substitution is used to alter executable behavior.
    old_hash = sha256(encode(old))
    if old_directory not in gate or old_hash not in gate:
        raise ValueError("Installed launch gate does not bind predecessor policy.")
    gate = gate.replace(old_directory, new_directory).replace(
        old_hash, sha256(payload["AutomaticStartupPolicy.json"])
    )
    for path, old_digest in old["source_hashes"].items():
        if old_digest in gate:
            if path not in pins:
                raise ValueError("Launch-gate source member cannot be removed by a routine update.")
            gate = gate.replace(old_digest, pins[path])
    payload["Start-ReviewedAutomaticStartup.ps1"] = gate.encode("utf-8")
    return payload


def prepare_update(
    observation, changes, read_blob, destination, tool_directory, *, secure_output=False
):
    """Prepare an executable source-only package; all inputs are machine-derived.

    The caller has authenticated installed metadata and acquired an exact private
    main revision. The generated binding is rechecked by preflight before drain.
    """
    previous = observation["seed"]
    config = deepcopy(observation["bindings"])
    plan, payload = source_plan(previous, config["before"], config["target"], changes, read_blob)
    config.update(plan)
    seed = release_seed(previous, plan["new_pins"], observation["gate"])
    config["release_id"] = str(uuid4())
    config["seed_members"] = [
        dict(name=name, sha256=sha256(raw)) for name, raw in sorted(seed.items())
    ]
    config["new_policy"] = json.loads(seed["AutomaticStartupPolicy.json"])
    config["new_policy_sha256"] = sha256(seed["AutomaticStartupPolicy.json"])
    config["new_seed_directory"] = str(
        PureWindowsPath(config["new_policy"]["seed_plan"]["path"]).parent
    )
    config["new_state_directory"] = config["new_policy"]["state_directory"]
    config["old_pins"] = previous["AutomaticStartupPolicy.json"]["source_hashes"]
    config["flags"] = previous["AutomaticStartupPolicy.json"]["flags"]
    files = dict(seed)
    tools = Path(tool_directory)
    files["Release-Step.ps1"] = (tools / "K98-SourceUpdate.ps1").read_bytes()
    files["Verify-NewPair.py"] = (tools / "verify_k98_update_pair.py").read_bytes()
    files["EmptyGitConfig.txt"] = b""
    config["extra_members"] = [
        dict(name="Verify-NewPair.py", sha256=sha256(files["Verify-NewPair.py"]))
    ]
    # Flat payload names keep the runner's bounded inventory and avoid archive
    # extraction. Every target path is separately validated by the adapter.
    for index, member in enumerate(config["source_members"]):
        if not member["deleted"]:
            member["payload"] = f"source-{index:04d}.bin"
            files[member["payload"]] = payload[member["path"]]
    files["ReleaseBindings.json"] = encode(config)
    binding_hash = sha256(files["ReleaseBindings.json"])

    def invocation(action):
        return dict(
            file="Release-Step.ps1",
            arguments=dict(Action=action, ExpectedBindingsSHA256=binding_hash),
        )

    manifest = dict(
        version=1,
        release_id=config["release_id"],
        host=config["host"],
        application_sid=config["sid"],
        repository=config["root"],
        policy=dict(path=config["old_policy"]["Path"], sha256=config["old_policy"]["SHA256"]),
        issuer_launcher=dict(
            path=config["old_plan"]["Python"], sha256=config["old_plan"]["PythonSHA256"]
        ),
        members=[dict(name=name, sha256=sha256(raw)) for name, raw in sorted(files.items())],
        preflight=invocation("Preflight"),
        steps=[
            dict(id=kind, kind=kind, apply=invocation(apply), verify=invocation(verify))
            for kind, apply, verify in (
                ("source", "ApplySource", "VerifySource"),
                ("seed", "ApplySeed", "VerifySeed"),
                ("start", "ApplyStart", "VerifyStart"),
                ("readiness", "AwaitReadiness", "VerifyReadiness"),
            )
        ],
    )
    # Validate before writing anything, including the runner's 128-member bound.
    from scripts.prepare_k98_release import validate_manifest

    validate_manifest(manifest)
    destination = Path(destination)
    mkdir, write = output_writers(config["sid"], secure_output=secure_output)
    mkdir(destination)
    inputs = destination / "inputs"
    mkdir(inputs)
    for name, raw in files.items():
        write(inputs / name, raw)
    specification = inputs / "specification.json"
    write(specification, encode(manifest))
    # Match the existing packager's exact canonical manifest protocol while
    # creating native administrative custody atomically, before any bytes exist.
    package = destination / "package"
    mkdir(package)
    for name, raw in files.items():
        write(package / name, raw)
    manifest_raw = encode(manifest)
    runner_raw = (tools / "Deploy-K98Release.ps1").read_bytes()
    write(package / "release.json", manifest_raw)
    write(package / "Deploy-K98Release.ps1", runner_raw)
    result = dict(
        stage="RELEASE_PACKET_PREPARED_NOT_INSTALLED",
        release_id=config["release_id"],
        manifest=str((package / "release.json").resolve()),
        manifest_sha256=sha256(manifest_raw),
        runner_sha256=sha256(runner_raw),
        files=len(files) + 2,
        production_changed=False,
    )
    result.update(target=config["target"], before=config["before"], bindings_sha256=binding_hash)
    write(destination / "prepared.json", encode(result))
    return result


def output_writers(sid, *, secure_output):
    if not secure_output:

        def mkdir(path):
            path.mkdir(exist_ok=False)

        def write(path, raw):
            with path.open("xb") as stream:
                stream.write(raw)

        return mkdir, write
    import win32file

    from core.export_startup_windows import (
        _attributes,
        administrative_path,
        create_private_directory,
        write_new_protected,
    )

    if not re.fullmatch(r"S-1-5-21-(?:[0-9]+-){3}[0-9]+", sid):
        raise ValueError("Canonical application SID required.")

    def mkdir(path):
        create_private_directory(path, sid)

    def write(path, raw):
        if raw:
            write_new_protected(path, raw, sid)
            return
        # The Git configuration sentinel is the only empty member; retain the
        # same atomic ACL and exclusive creation as the existing startup helper.
        administrative_path(path.parent, private=True)
        handle = win32file.CreateFile(
            str(path), 0x40000000, 0, _attributes(sid), 1, 0x80000000, None
        )
        try:
            win32file.FlushFileBuffers(handle)
        finally:
            handle.Close()
        administrative_path(path, private=True)

    return mkdir, write


def main():
    import argparse
    import os
    import subprocess

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = Path(args.observation).read_bytes()
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Installed observation exceeds bound.")
    observation = json.loads(raw)
    config = observation["bindings"]
    before, target = config["before"], config["target"]
    if any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in (before, target)):
        raise ValueError("Exact commit binding required.")
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")
    }
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_ATTR_NOSYSTEM="1",
    )

    def git(*arguments, data=None):
        result = subprocess.run(
            [
                config["git_path"],
                "--no-optional-locks",
                "-c",
                "core.hooksPath=NUL",
                "-c",
                "core.fsmonitor=false",
                "-c",
                f"safe.directory={config['root'].replace(chr(92), '/')}",
                "-C",
                config["root"],
                *arguments,
            ],
            input=data,
            capture_output=True,
            check=True,
            timeout=60,
            env=environment,
        )
        return result.stdout

    changes = (
        git("diff", "--no-renames", "--name-only", "-z", before, target)
        .decode("utf-8")
        .rstrip("\0")
        .split("\0")
    )
    check_source_only(changes)
    requested = sorted(
        set(changes) | set(observation["seed"]["AutomaticStartupPolicy.json"]["source_hashes"])
    )
    objects = {}
    for commit in (before, target):
        tree = git("ls-tree", "-r", "-l", "-z", commit)
        if len(tree) > 4 * 1024 * 1024:
            raise ValueError("Git tree inventory exceeds bound.")
        wanted = set(requested)
        for entry in tree.rstrip(b"\0").split(b"\0"):
            header, path_raw = entry.split(b"\t", 1)
            path = path_raw.decode("utf-8")
            if path not in wanted:
                continue
            mode, kind, oid, length = header.split()
            if (
                mode not in {b"100644", b"100755"}
                or kind != b"blob"
                or int(length) > 2 * 1024 * 1024
            ):
                raise ValueError(f"Unsupported source object: {path}")
            objects[(commit, path)] = (oid, int(length))
    if sum(size for _, size in objects.values()) > 128 * 1024 * 1024:
        raise ValueError("Git source inventory exceeds bound.")
    # One subprocess for all blobs avoids per-file process startup overhead.
    keys = list(objects)
    batch = git("cat-file", "--batch", data=b"".join(objects[key][0] + b"\n" for key in keys))
    offset, blobs = 0, {}
    for key in keys:
        end = batch.index(b"\n", offset)
        oid, kind, size = batch[offset:end].split()
        expected_oid, expected_size = objects[key]
        if oid != expected_oid or kind != b"blob" or int(size) != expected_size:
            raise ValueError("Git object changed during preparation.")
        offset = end + 1
        content = batch[offset : offset + expected_size]
        if (
            len(content) != expected_size
            or batch[offset + expected_size : offset + expected_size + 1] != b"\n"
        ):
            raise ValueError("Truncated Git object stream.")
        blobs[key] = content
        offset += expected_size + 1
    if offset != len(batch):
        raise ValueError("Unexpected Git object stream suffix.")
    result = prepare_update(
        observation,
        changes,
        lambda commit, path: blobs.get((commit, path)),
        args.output,
        Path(__file__).parent,
        secure_output=True,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
