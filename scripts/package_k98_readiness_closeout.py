"""Build an exact, guided administrative closeout; never alter old step receipts."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import zipfile

from scripts.package_k98_update_tool import INSTALLER

LIBRARY_SHA256 = "76434df2a10e1065706e3941fc403b57d77674130452a4957dfcd4ee06c23310"
RELEASE = "8d368128-2c86-46b3-bee6-6c2a1c7d29d1"
STAGE = (
    "C:\\ProgramData\\K98\\S11\\automatic-startup\\d4e442a4-b634-4124-9bf6-ac30e9d4a399"
    "\\release-" + RELEASE
)

BODY = r"""
$library='C:\ProgramData\K98\S11\updater\K98-SourceUpdate.ps1'
Assert-Custody $library
if((Hash ([IO.File]::ReadAllBytes($library))) -cne '__LIBRARY_HASH__'){throw 'Installed verifier version differs; no changes made'}
. $library -Action Library
$profileBytes=[Convert]::FromBase64String('__PROFILE__')
$profile=[Text.Encoding]::UTF8.GetString($profileBytes)|ConvertFrom-Json
$helperBytes=[Convert]::FromBase64String('__HELPER__')
$script:c=Read-Json $profile.bindings $profile.bindings_sha256
if($c.sid -cne $sid -or $c.host -cne 'MINI_AMD' -or $c.release_id -cne $profile.release_id -or $c.target -cne $profile.target){throw 'Exact deployment identity differs'}
$updates='C:\ProgramData\K98\S11\updates'
Assert-Protected $updates
$lockPath=Join-Path $updates 'operator.lock'
Assert-Protected $lockPath
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
 $activePath=Join-Path $updates 'active.json'
 $active=Read-Json $activePath
 if($active.release_id -cne $profile.release_id -or $active.directory -cnotmatch '^C:\\ProgramData\\K98\\S11\\updates\\[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'){throw 'Active update differs'}
 $work=$active.directory
 $prepared=Read-Json (Join-Path $work 'prepared.json')
 if($prepared.release_id -cne $profile.release_id -or $prepared.target -cne $profile.target -or $prepared.bindings_sha256 -cne $profile.bindings_sha256){throw 'Prepared update identity differs'}
 if($prepared.manifest -cne (Join-Path $work 'package\release.json')){throw 'Prepared manifest path differs'}
 $manifest=Read-Json $prepared.manifest $prepared.manifest_sha256
 $null=Read-Bytes (Join-Path $profile.stage '.release.json') $prepared.manifest_sha256
 if($manifest.release_id -cne $profile.release_id -or (@($manifest.steps.id) -join ',') -cne 'source,seed,start,readiness'){throw 'Only the reviewed source-only release may close'}
 if(Test-Path -LiteralPath (Join-Path $profile.stage '.amendment-selected.json')){throw 'Amended release needs its own recovery'}
 $completePath=Join-Path $work 'verified.json'
 if(Test-Path -LiteralPath $completePath){
  $prior=Read-Json $completePath
  if($prior.release_id -cne $profile.release_id -or $prior.target -cne $profile.target -or $prior.closeout_kind -cne 'current_successor_admin_verified_v1' -or $prior.profile_sha256 -cne (Hash $profileBytes)){throw 'A different closeout exists; preserve it'}
  Write-Host 'This exact administrative closeout is already recorded. Run the normal updater once to finalize its pointer. No restart is required.'
  return
 }
 function Assert-HistoricalRecords {
  foreach($item in $profile.receipts){
   $record=Read-Json (Join-Path (Join-Path $profile.stage '.receipts') $item.name) $item.sha256
   if($record.release_id -cne $profile.release_id -or $record.stage -cne $item.stage -or $record.step -cne $item.step){throw 'Historical step identity differs'}
  }
  if(Test-Path -LiteralPath (Join-Path $profile.stage '.receipts\readiness.complete.json')){throw 'Normal readiness completed; use normal updater'}
  if(Test-Path -LiteralPath (Join-Path $profile.stage 'readiness-status.json')){throw 'A readiness classification now exists; preserve and review it'}
  $null=Read-Bytes (Join-Path $profile.stage 'start-requested.json') $profile.start_sha256
 }
 Assert-HistoricalRecords
 # This folder is new recovery evidence, not a replacement of the original packet.
 $destination=Join-Path $updates ('readiness-closeout-'+$profile.release_id)
 if(-not(Test-Path -LiteralPath $destination)){New-Directory $destination}
 Assert-Protected $destination
 foreach($entry in @(@('profile.json',$profileBytes),@('verify_closeout.py',$helperBytes))){
  $path=Join-Path $destination $entry[0]
  if(-not(Test-Path -LiteralPath $path)){Write-New $path $entry[1]}
  $null=Read-Bytes $path (Hash $entry[1])
 }
 $newGate=Join-Path $c.new_seed_directory 'Start-ReviewedAutomaticStartup.ps1'
 function Verify-Current {
  Assert-HistoricalRecords
  $null=Read-Bytes (Join-Path $destination 'profile.json') (Hash $profileBytes)
  $null=Read-Bytes (Join-Path $destination 'verify_closeout.py') (Hash $helperBytes)
  Assert-Source $c.new_pins $c.target
  if(-not(Seed-Complete)){throw 'Installed successor seed does not verify'}
  $null=Read-Bytes $c.venv.path $c.venv.sha256 4MB
  $member=@($c.extra_members|Where-Object {$_.name -ceq 'Verify-NewPair.py'})
  if($member.Count -ne 1){throw 'Pinned original verifier missing'}
  $null=Read-Bytes (Join-Path $profile.stage 'Verify-NewPair.py') $member[0].sha256
  $output=@(& $c.venv.path -I -B (Join-Path $destination 'verify_closeout.py') --profile (Join-Path $destination 'profile.json') --sha256 (Hash $profileBytes))
  if($LASTEXITCODE -ne 0){throw 'Current successor verification failed; no closeout written'}
  $proof=$output[-1]|ConvertFrom-Json
  if($proof.stage -cne 'CURRENT_SUCCESSOR_VERIFIED' -or $proof.release_id -cne $profile.release_id -or $proof.target -cne $profile.target -or $proof.session_id -cne $profile.current_session){throw 'Current successor proof differs'}
  return $proof
 }
 $proof=Verify-Current
 Write-Host 'Source, seed, exact restart chain, native identities and SQL sessions verified.'
 Write-Host 'The original readiness intent will remain unconfirmed. This records a separate current-successor acceptance; no business repair, replay or restart occurs.'
 Write-Host 'In Discord run /ops dl_bot_status now. Confirm the bot responds and is online. Import/export warnings and queued recovery may remain; this does not certify them.'
 $answer=Read-Host 'Type CONFIRM ONLINE to record the closeout, or press Enter to leave it unchanged'
 if($answer -cne 'CONFIRM ONLINE'){Write-Host 'No closeout written. All original evidence retained.';return}
 # Revalidate after the human check, never rely on a stale pre-prompt observation.
 $proof=Verify-Current
 $acceptance=@{version=1;release_id=$profile.release_id;target=$profile.target;verified_utc=[DateTime]::UtcNow.ToString('o');closeout_kind='current_successor_admin_verified_v1';profile_sha256=(Hash $profileBytes);helper_sha256=(Hash $helperBytes);actor_sid=$sid;current_successor=$proof;readiness=@{discord_status='operator_confirmed_online';import_export=@{status='degraded';provider_delivery_verified=$false};original_readiness='unconfirmed_preserved'}}|ConvertTo-Json -Depth 15 -Compress|ConvertFrom-Json
 Write-AtomicRecord $completePath $acceptance
 $saved=Read-Json $completePath
 if(-not(Same $saved $acceptance)){throw 'Closeout readback differs; retain evidence'}
 Assert-HistoricalRecords
 Write-Host 'CLOSEOUT RECORDED AND READ BACK. Original receipts unchanged; no restart or business repair performed.'
 Write-Host 'Run the normal updater once now to clear only its completed active pointer. After the recovery PRs merge, use the normal updater again for their deployment.'
} finally {$lock.Dispose()}
"""


def profile_from_diagnostic(document):
    sections = document["sections"]
    binding = sections["binding"]
    if (
        document["format"] != "k98-readiness-diagnostic-v1"
        or document["errors"]
        or binding["release_id"] != RELEASE
        or binding["original_sha256"] != binding["selected_sha256"]
        or sections["readiness_status_exists"]
        or [j["record"]["sequence"] for j in sections["successor_journals"]] != [22, 23]
        or len(sections["receipts"]) != 7
    ):
        raise ValueError("Only the explicitly reviewed two-incarnation closeout is supported")
    expected_receipts = {
        f"{step}.{suffix}.json": (step, stage)
        for step in ("source", "seed", "start", "readiness")
        for suffix, stage in (("intent", "starting"), ("complete", "verified"))
        if not (step == "readiness" and suffix == "complete")
    }
    if {r["name"]: (r["step"], r["stage"]) for r in sections["receipts"]} != expected_receipts:
        raise ValueError("Exact historical receipt set required")
    hashes = [binding["selected_sha256"], binding["new_policy_sha256"], sections["start"]["sha256"]]
    hashes.extend(r["sha256"] for r in sections["receipts"])
    hashes.extend(j["sha256"] for j in sections["successor_journals"])
    if any(not re.fullmatch(r"[a-f0-9]{64}", h) for h in hashes):
        raise ValueError("Canonical hashes required")
    if binding["target"] != "471742d76a21f1ab888a6c20741bcba341df80fd":
        raise ValueError("Exact installed target required")
    for journal in sections["successor_journals"]:
        if not re.fullmatch(
            rf"incarnation-{journal['record']['sequence']:020d}-[a-f0-9]{{8}}(?:-[a-f0-9]{{4}}){{3}}-[a-f0-9]{{12}}\.json",
            journal["name"],
        ):
            raise ValueError("Canonical journal identity required")
    sessions = sections["recent_sessions"][:3]
    if [s["State"] for s in sessions] != ["open", "closed", "closed"]:
        raise ValueError("Reviewed current and two closed sessions required")
    if any(
        not re.fullmatch(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", s["SessionID"])
        for s in sessions
    ):
        raise ValueError("Canonical session identities required")
    return dict(
        release_id=RELEASE,
        stage=STAGE,
        bindings=STAGE + "\\ReleaseBindings.json",
        bindings_sha256=binding["selected_sha256"],
        target=binding["target"],
        policy_sha256=binding["new_policy_sha256"],
        journals=[dict(name=j["name"], sha256=j["sha256"]) for j in sections["successor_journals"]],
        sessions=[s["SessionID"].lower() for s in sessions],
        current_session=sessions[0]["SessionID"].lower(),
        receipts=[
            {k: r[k] for k in ("name", "sha256", "stage", "step")} for r in sections["receipts"]
        ],
        start_sha256=sections["start"]["sha256"],
    )


def build(document, helper):
    profile = json.dumps(profile_from_diagnostic(document), sort_keys=True).encode()
    # Reuse the reviewed updater installer's trusted module resolution, admin
    # identity and custody checks. No installer payload or install loop is used.
    prefix = INSTALLER.split("$encoded='__PAYLOAD__'", 1)[0]
    body = BODY.replace("__LIBRARY_HASH__", LIBRARY_SHA256)
    body = body.replace("__PROFILE__", base64.b64encode(profile).decode())
    body = body.replace("__HELPER__", base64.b64encode(helper).decode())
    return (prefix + body).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.diagnostic.read_text(encoding="utf-8-sig"))
    helper = (
        Path(__file__)
        .with_name("verify_k98_readiness_closeout.py")
        .read_bytes()
        .replace(b"\r\n", b"\n")
    )
    raw = build(document, helper)
    with zipfile.ZipFile(args.output, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Close-K98Readiness.ps1", raw)
        archive.writestr(
            "README.txt",
            "Extract on MINI_AMD. In administrator Windows PowerShell 5.1 run:\n"
            "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\Close-K98Readiness.ps1\n"
            "The script verifies the exact release and current successor, then guides your live Discord confirmation.\n"
            "No restart, SQL write or business repair occurs. Original readiness remains unconfirmed and preserved.\n"
            "After success run the installed Update-K98.ps1 once to finalize its active pointer.\n",
        )
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
