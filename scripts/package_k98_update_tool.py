"""Build the one-time updater installer. Routine releases do not run this tool."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

INSTALLER = r"""[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Establish trusted module/executable resolution before the first cmdlet.
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
$env:PATHEXT='.EXE;.COM'
$env:SystemRoot='C:\Windows';$env:windir='C:\Windows';$env:ComSpec='C:\Windows\System32\cmd.exe'
if($env:COMPUTERNAME -cne 'MINI_AMD' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Run this one-time installer on MINI_AMD in Windows PowerShell 5.1.'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as administrator using the existing deployment account.'}
$sid=$identity.User.Value
$task=Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
$taskSid=[Security.Principal.NTAccount]::new($task.Principal.UserId).Translate([Security.Principal.SecurityIdentifier]).Value
if($sid -cne $taskSid){throw 'Installed deployment account differs'}
function Assert-Custody([string]$Path) {
 $item=Get-Item -LiteralPath $Path -Force
 $strict=if($item -is [IO.DirectoryInfo]){0}else{1};$depth=0
 $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
 while($null -ne $item) {
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Reparse path: '+$item.FullName)}
  $acl=Get-Acl -LiteralPath $item.FullName
  if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw ('Owner differs: '+$item.FullName)}
  $mask=if($depth -le $strict){0x500d0156}else{0x500d0040}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
   if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
      ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and
      $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band $mask) -ne 0){throw ('Write access differs: '+$item.FullName)}
  }
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory};$depth++
 }
}
function New-Acl([bool]$Directory) {
 $acl=if($Directory){[Security.AccessControl.DirectorySecurity]::new()}else{[Security.AccessControl.FileSecurity]::new()}
 $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'));$acl.SetAccessRuleProtection($true,$false)
 $inherit=if($Directory){[Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit}else{[Security.AccessControl.InheritanceFlags]::None}
 foreach($who in @('S-1-5-18','S-1-5-32-544',$sid)) {
  $rights=if($who -ceq $sid){[Security.AccessControl.FileSystemRights]::ReadAndExecute}else{[Security.AccessControl.FileSystemRights]::FullControl}
  $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($who),$rights,$inherit,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
 }
 return $acl
}
function Hash([byte[]]$Bytes) {
 $hash=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
}
$encoded='__PAYLOAD__'
$payload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))|ConvertFrom-Json
$destination='C:\ProgramData\K98\S11\updater'
Assert-Custody (Split-Path -Parent $destination)
if(-not(Test-Path -LiteralPath $destination)){$null=[IO.Directory]::CreateDirectory($destination,(New-Acl $true))}
Assert-Custody $destination
foreach($member in $payload.PSObject.Properties) {
 if($member.Name -cnotmatch '^[A-Za-z][A-Za-z0-9_.-]+$'){throw 'Installer member name differs'}
 $bytes=[Convert]::FromBase64String($member.Value)
 $path=Join-Path $destination $member.Name
 if(Test-Path -LiteralPath $path) {
  Assert-Custody $path
  if((Hash ([IO.File]::ReadAllBytes($path))) -cne (Hash $bytes)){throw 'A different updater version exists; do not overwrite an active tool'}
 } else {
  $stream=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,(New-Acl $false))
  try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
  Assert-Custody $path
  if((Hash ([IO.File]::ReadAllBytes($path))) -cne (Hash $bytes)){throw 'Updater installation readback differs'}
 }
}
Write-Host 'Updater installed. Bot, source, startup policy and scheduled task are unchanged.'
Write-Host 'For every routine source update, run:'
Write-Host "& 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'"
Write-Host 'Then run /ops graceful_restart once, only when prompted.'
"""


def package(output, source=None, *, previous_manifest=None):
    source = Path(source) if source else Path(__file__).parent
    names = (
        "Update-K98.ps1",
        "K98-SourceUpdate.ps1",
        "Deploy-K98Release.ps1",
        "prepare_k98_update.py",
        "prepare_k98_release.py",
        "verify_k98_update_pair.py",
        "package_k98_update_tool.py",
    )
    # Ship Git's LF form even from a Windows CRLF checkout, so exact target
    # blob comparison during the first routine release is reproducible.
    files = {name: (source / name).read_bytes().replace(b"\r\n", b"\n") for name in names}
    files["EmptyGitConfig.txt"] = b""
    manifest = dict(
        version=1, files={name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    )
    files["update-tool.json"] = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    payload = json.dumps(
        {name: base64.b64encode(raw).decode("ascii") for name, raw in files.items()},
        sort_keys=True,
    ).encode()
    script = INSTALLER.replace("__PAYLOAD__", base64.b64encode(payload).decode("ascii")).encode()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / "Install-K98UpdateTool.ps1"
    with target.open("xb") as stream:
        stream.write(script)
    upgrade = None
    if previous_manifest is not None:
        previous_raw = Path(previous_manifest).read_bytes()
        previous = json.loads(previous_raw)
        required = set(names) - {"prepare_k98_release.py"}
        inventory = set(previous.get("files", {})) - {"EmptyGitConfig.txt"}
        if previous.get("version") != 1 or inventory not in (required, set(names)):
            raise ValueError("Exact installed predecessor tool manifest required for upgrade.")
        old_hash = hashlib.sha256(previous_raw).hexdigest()
        new_hash = hashlib.sha256(files["update-tool.json"]).hexdigest()
        template = (source / "Upgrade-K98InstalledUpdater.ps1").read_text(encoding="utf-8")
        # Generated defaults bind one reviewed old/new pair. The operator still
        # runs one fixed filename without calculating or substituting hashes.
        for old, new in (
            ("cd112e1912ec04318a463a48d8df20e88d6dae4dd20c45368f517deadc318871", old_hash),
            (
                "ab69591f89a88628a729eb35a08eadda4ed0602d7512291075e5ab746017fd30",
                hashlib.sha256(script).hexdigest(),
            ),
            ("6562c4cf8970c8fe5c776d10275aab6f2211fc2e814a9d3a529a56a15c34c50b", new_hash),
        ):
            if template.count(old) != 1:
                raise ValueError("Upgrade template pin is missing or ambiguous.")
            template = template.replace(old, new)
        upgrade = output / "Upgrade-K98InstalledUpdater.ps1"
        with upgrade.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(template)
    return dict(
        installer=str(target.resolve()),
        sha256=hashlib.sha256(script).hexdigest(),
        status="BUILT_NOT_INSTALLED",
        production_changed=False,
        upgrade=str(upgrade.resolve()) if upgrade else None,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".codex_artifacts/k98-update-tool")
    parser.add_argument("--previous-manifest")
    args = parser.parse_args()
    print(json.dumps(package(args.output, previous_manifest=args.previous_manifest)))


if __name__ == "__main__":
    main()
