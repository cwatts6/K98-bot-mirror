"""Seal a verification-only packet from reviewed code and a private exact profile."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import zipfile

from scripts.package_k98_update_tool import INSTALLER
from scripts.verify_k98_update_pair import build_contract_archive

UUID = r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}"
RECEIPTS = {
    "source.intent.json",
    "source.complete.json",
    "seed.intent.json",
    "seed.complete.json",
    "start.intent.json",
}


def validate_profile(profile):
    hashes = {
        "active",
        "bindings",
        "manifest",
        "start",
        "journal",
        "original_retirement",
        "failure_evidence",
    }
    fields = {
        "version",
        "kind",
        "host",
        "sid",
        "release_id",
        "target",
        "work",
        "stage",
        "journal_name",
        "receipts",
        "original_retirement_path",
        *(x + "_sha256" for x in hashes),
    }
    if (
        not isinstance(profile, dict)
        or set(profile) != fields
        or type(profile["version"]) is not int
        or profile["version"] != 1
        or profile["kind"] != "running_release_verification_v1"
        or profile["host"] != "MINI_AMD"
    ):
        raise ValueError("Exact running-release verification profile required")
    patterns = dict(
        sid=r"S-1-5-21-(?:[0-9]+-){3}[0-9]+",
        release_id=UUID,
        target=r"[a-f0-9]{40}",
        work=r"C:\\ProgramData\\K98\\S11\\updates\\" + UUID,
        stage=r"C:\\ProgramData\\K98\\S11\\automatic-startup\\"
        + UUID
        + r"\\release-"
        + re.escape(profile["release_id"]),
        journal_name=r"incarnation-[0-9]{20}-" + UUID + r"\.json",
        original_retirement_path=r"C:\\ProgramData\\K98\\S11\\updates\\retirements\\"
        + UUID
        + r"\\complete\.json",
        **{x + "_sha256": r"[a-f0-9]{64}" for x in hashes},
    )
    if any(
        not isinstance(profile[k], str) or not re.fullmatch(p, profile[k])
        for k, p in patterns.items()
    ):
        raise ValueError("Canonical running-release identity required")
    if (
        not isinstance(profile["receipts"], dict)
        or set(profile["receipts"]) != RECEIPTS
        or any(
            not isinstance(h, str) or not re.fullmatch(r"[a-f0-9]{64}", h)
            for h in profile["receipts"].values()
        )
    ):
        raise ValueError("Exactly verified source/seed and unconfirmed start required")
    if profile["release_id"] in profile["original_retirement_path"]:
        raise ValueError("Retired release cannot be verified")


def build(profile, root):
    validate_profile(profile)
    root = Path(root)
    names = {
        "Source-Library.ps1": "K98-SourceUpdate.ps1",
        "Custody-Library.ps1": "K98-FailedReadiness.ps1",
        "Running-Library.ps1": "K98-VerifyRunningRelease.ps1",
        "Verify-NewPair.py": "verify_k98_update_pair.py",
        "Verify-RunningRelease.py": "verify_k98_running_release.py",
    }
    members = {
        name: (root / "scripts" / source).read_bytes().replace(b"\r\n", b"\n")
        for name, source in names.items()
    }
    members["contract_verifier.zip"] = build_contract_archive(root)
    digests = {k: hashlib.sha256(v).hexdigest() for k, v in members.items()}
    sealed = dict(
        profile,
        members=digests,
        pair_sha256=digests["Verify-NewPair.py"],
        archive_sha256=digests["contract_verifier.zip"],
    )
    raw = (json.dumps(sealed, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(raw) > 65536 or any(len(v) > 4 * 1024 * 1024 for v in members.values()):
        raise ValueError("Verification packet bound exceeded")
    digest = hashlib.sha256(raw).hexdigest()
    members["profile.json"] = raw
    payload = base64.b64encode(
        json.dumps(
            {k: base64.b64encode(v).decode() for k, v in members.items()}, sort_keys=True
        ).encode()
    ).decode()
    # Keep the existing trusted-resolution/admin bootstrap, but none of its updater install actions.
    prefix = INSTALLER.split("$encoded='__PAYLOAD__'", 1)[0].replace(
        "Run this one-time installer on MINI_AMD in Windows PowerShell 5.1.",
        "Run this verification-only packet on MINI_AMD in Windows PowerShell 5.1.",
    )
    body = r"""
$profileHash='__PROFILE_HASH__'
$payload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__PAYLOAD__'))|ConvertFrom-Json
$profile=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload.'profile.json'))|ConvertFrom-Json
if($sid -cne $profile.sid){throw 'Reviewed deployment account differs'}
$destination=Join-Path 'C:\ProgramData\K98\S11\updates' ('verification-'+$profile.release_id+'-'+$profileHash)
Assert-Custody (Split-Path -Parent $destination)
if(-not(Test-Path -LiteralPath $destination)){$null=[IO.Directory]::CreateDirectory($destination,(New-Acl $true))}
Assert-Custody $destination
foreach($entry in $payload.PSObject.Properties) {
 if($entry.Name -cnotmatch '^[A-Za-z][A-Za-z0-9_.-]+$'){throw 'Packet member path differs'}
 $path=Join-Path $destination $entry.Name;$bytes=[Convert]::FromBase64String($entry.Value)
 if(-not(Test-Path -LiteralPath $path)) {
  $stream=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,(New-Acl $false))
  try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 }
 Assert-Custody $path
 if((Hash ([IO.File]::ReadAllBytes($path))) -cne (Hash $bytes)){throw 'Sealed packet differs; preserve partial state'}
}
. (Join-Path $destination 'Source-Library.ps1') -Action Library
. (Join-Path $destination 'Custody-Library.ps1')
. (Join-Path $destination 'Running-Library.ps1')
Invoke-RunningReleaseVerification $profile $profileHash $destination
"""
    return (
        prefix + body.replace("__PROFILE_HASH__", digest).replace("__PAYLOAD__", payload)
    ).encode(), sealed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw, sealed = build(
        json.loads(args.profile.read_text(encoding="utf-8-sig")),
        Path(__file__).resolve().parents[1],
    )
    with zipfile.ZipFile(args.output, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Verify-K98RunningRelease.ps1", raw)
        archive.writestr("profile.json", json.dumps(sealed, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                package=str(args.output),
                sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
            )
        )
    )


if __name__ == "__main__":
    main()
