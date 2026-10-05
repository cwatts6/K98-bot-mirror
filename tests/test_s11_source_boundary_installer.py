"""Native Windows guard tests; none perform administrative installation."""
import os
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install_s11_source_boundary.ps1"
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows filesystem guards")


def run_helpers(tmp_path, body):
    script = str(SCRIPT).replace("'", "''")
    fixture = str(tmp_path).replace("'", "''")
    source = f"""
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile('{script}',[ref]$tokens,[ref]$errors)
if($errors.Count){{throw 'Installer parse failure'}}
foreach($name in @('CanonicalPath','Inside','CheckedItem','FileDigest','ReadBoundedGit')){{
 $node=$ast.Find({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name}},$false)
 if($null -eq $node){{throw 'Helper missing'}}
 Invoke-Expression $node.Extent.Text
}}
$fixture='{fixture}'
{body}
"""
    probe = tmp_path / "native-guard-test.ps1"
    probe.write_text(source, encoding="utf-8-sig")
    result = subprocess.run(
        [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(probe)],
        capture_output=True, text=True, timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_reject_noncanonical_escape_network_root_and_stream(tmp_path):
    run_helpers(tmp_path, r"""
foreach($bad in @('relative\file','C:\','C:\root\..\outside','\\server\share\file','C:\root\file:stream')){
 $refused=$false
 try{$null=CanonicalPath $bad}catch{$refused=$true}
 if(-not $refused){throw "Unsafe path accepted: $bad"}
}
if(Inside 'C:\root-extra\file' 'C:\root'){throw 'Prefix escape accepted'}
if(-not (Inside 'C:\root\file' 'C:\root')){throw 'Valid child rejected'}
""")


def test_bounded_file_digest_and_no_overwrite_preservation(tmp_path):
    run_helpers(tmp_path, r"""
$file=Join-Path $fixture 'small.txt'; [IO.File]::WriteAllText($file,'reviewed')
if((FileDigest $file) -cnotmatch '^[0-9a-f]{64}$'){throw 'Digest failed'}
$large=Join-Path $fixture 'large.bin';$stream=[IO.File]::Open($large,[IO.FileMode]::CreateNew)
$stream.SetLength(16MB+1);$stream.Dispose()
$refused=$false;try{$null=FileDigest $large}catch{$refused=$true}
if(-not $refused){throw 'Oversize hash accepted'}
$from=Join-Path $fixture 'from';$to=Join-Path $fixture 'to'
$null=[IO.Directory]::CreateDirectory($from);$null=[IO.Directory]::CreateDirectory($to)
$refused=$false;try{[IO.Directory]::Move($from,$to)}catch{$refused=$true}
if(-not $refused -or -not (Test-Path -LiteralPath $from)){throw 'Move overwrote destination'}
$fresh=Join-Path $fixture 'fresh';[IO.Directory]::Move($from,$fresh)
if((Test-Path -LiteralPath $from) -or -not (Test-Path -LiteralPath $fresh)){throw 'Preservation move failed'}
""")


def test_bounded_git_reads_report_actual_failure(tmp_path):
    run_helpers(tmp_path, r"""
$git='C:\Program Files\Git\cmd\git.exe';$root=$fixture
$refused=$false;try{$null=ReadBoundedGit 'rev-parse HEAD'}catch{$refused=$true}
if(-not $refused){throw 'Git failure accepted as a binding'}
""")
