"""Package a bounded, reviewed pre-incarnation startup correction for MINI_AMD."""

import argparse
import base64
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
from uuid import UUID

from scripts.package_k98_update_tool import INSTALLER, package
from scripts.prepare_k98_startup_correction import FAILED_TARGET

RECEIPTS = {
    "source.intent.json",
    "source.complete.json",
    "seed.intent.json",
    "seed.complete.json",
    "start.intent.json",
}


def validate_profile(profile):
    expected = {
        "release_id",
        "recovery_id",
        "stage",
        "work",
        "bindings",
        "bindings_sha256",
        "manifest_sha256",
        "library_sha256",
        "failed_target",
        "target",
        "receipts",
        "start_request",
    }
    if set(profile) != expected:
        raise ValueError("Exact startup correction profile fields required.")
    for key in ("release_id", "recovery_id"):
        if str(UUID(profile[key])) != profile[key]:
            raise ValueError("Canonical correction identifiers required.")
    if profile["release_id"] == profile["recovery_id"]:
        raise ValueError("Separate correction identity required.")
    guid = r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}"
    if (
        not re.fullmatch(
            r"C:\\ProgramData\\K98\\S11\\automatic-startup\\"
            + guid
            + r"\\release-"
            + profile["release_id"],
            profile["stage"],
        )
        or not re.fullmatch(r"C:\\ProgramData\\K98\\S11\\updates\\" + guid, profile["work"])
        or profile["bindings"] != str(PureWindowsPath(profile["stage"]) / "ReleaseBindings.json")
        or profile["failed_target"] != FAILED_TARGET
        or not re.fullmatch(r"[a-f0-9]{40}", profile["target"])
        or profile["target"] == profile["failed_target"]
    ):
        raise ValueError("Exact production release paths and source target required.")
    if set(profile["receipts"]) != RECEIPTS:
        raise ValueError("Only the five failed-start receipts are supported.")
    hashes = [profile[k] for k in ("bindings_sha256", "manifest_sha256", "library_sha256")]
    hashes += list(profile["receipts"].values())
    if any(
        not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value) for value in hashes
    ):
        raise ValueError("Exact reviewed hashes required.")
    start = profile["start_request"]
    if (
        set(start) != {"release_id", "requested_utc", "log_offset"}
        or start["release_id"] != profile["release_id"]
        or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,7}Z", start["requested_utc"]
        )
        or type(start["log_offset"]) is not int
        or start["log_offset"] < 0
    ):
        raise ValueError("Exact original start intent required.")


def build(profile, tool_files, helper, template):
    validate_profile(profile)
    if hashlib.sha256(tool_files["K98-SourceUpdate.ps1"]).hexdigest() != profile["library_sha256"]:
        raise ValueError("Recovery must reuse the exact installed source adapter.")
    prefix = INSTALLER.split("$encoded='__PAYLOAD__'", 1)[0]
    if prefix.count("param()") != 1:
        raise ValueError("Reviewed installer parameter boundary differs.")
    prefix = prefix.replace(
        "param()", "param([ValidateSet('Inspect','Apply')][string]$Action='Inspect')"
    )
    files = dict(tool_files, **{"prepare_k98_startup_correction.py": helper})
    for placeholder, value in (
        ("__PROFILE__", json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()),
        (
            "__PAYLOAD__",
            json.dumps(
                {k: base64.b64encode(v).decode() for k, v in sorted(files.items())}
            ).encode(),
        ),
    ):
        # The template's introductory comment also names these placeholders.
        needle = "'" + placeholder + "'"
        if template.count(needle) != 1:
            raise ValueError("Exact correction template constants required.")
        template = template.replace(needle, "'" + base64.b64encode(value).decode() + "'")
    return (prefix + template).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--installed-tool-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
    validate_profile(profile)
    args.output.mkdir(parents=True, exist_ok=False)
    scripts = Path(__file__).parent
    # Retain the normal installer/upgrade pair for the subsequent tool upgrade.
    normal = package(args.output / "updater", previous_manifest=args.installed_tool_manifest)
    installer = Path(normal["installer"]).read_text(encoding="utf-8")
    matches = re.findall(r"^\$encoded='([A-Za-z0-9+/=]+)'$", installer, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Exact normal updater payload required.")
    tool_files = {
        name: base64.b64decode(raw, validate=True)
        for name, raw in json.loads(base64.b64decode(matches[0], validate=True)).items()
    }
    raw = build(
        profile,
        tool_files,
        scripts.joinpath("prepare_k98_startup_correction.py").read_bytes().replace(b"\r\n", b"\n"),
        scripts.joinpath("Recover-K98StartupEvidence.ps1").read_text(encoding="utf-8"),
    )
    output = args.output / "Recover-K98StartupEvidence.ps1"
    with output.open("xb") as stream:
        stream.write(raw)
    print(
        json.dumps(
            dict(
                stage="CORRECTION_BUILT_NOT_DEPLOYED",
                path=str(output.resolve()),
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
    )


if __name__ == "__main__":
    main()
