"""A bounded successor preserves both failed ancestors and their selections."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest
from test_prepare_k98_release import specification
from test_release_amendment import amendment

from scripts.prepare_k98_release import validate_manifest


def successor():
    value = amendment()
    value["version"] = 3
    value["amendment"]["parent_amendment_id"] = value["amendment"]["id"]
    value["amendment"]["id"] = "7850a12e-c27b-4674-a6d1-63e7f324e32f"
    value["amendment"]["failed_step_id"] = "sql-correction"
    value["steps"][0]["id"] = "sql-encoding"
    value["members"][0]["sha256"] = "e" * 64
    return value


@pytest.mark.parametrize("fault", [None, "parent_missing", "parent_bad", "same", "depth", "extra"])
def test_successor_manifest_is_explicit_and_bounded(fault):
    value = successor()
    if fault == "parent_missing":
        value["amendment"].pop("parent_amendment_id")
    if fault == "parent_bad":
        value["amendment"]["parent_amendment_id"] = "../escape"
    if fault == "same":
        value["amendment"]["parent_amendment_id"] = value["amendment"]["id"]
    if fault == "depth":
        value["version"] = 4
    if fault == "extra":
        value["amendment"]["auto_retry"] = True
    if fault is None:
        validate_manifest(value)
    else:
        with pytest.raises(ValueError):
            validate_manifest(value)


@pytest.mark.parametrize("version", [1, 2, 3])
@pytest.mark.parametrize("selected", [False, True])
def test_superseded_own_stage_stops_before_member_copy_or_preflight(tmp_path_factory, version, selected):
    ps = shutil.which("powershell.exe")
    if not ps:
        pytest.skip("Windows PowerShell required")
    # Keep the fixture below PS5.1's legacy path limit, as on the target host.
    tmp_path = tmp_path_factory.mktemp("early")
    value = {1: specification, 2: amendment, 3: successor}[version]()
    state = tmp_path / "state"
    root = state / ("release-" + value["release_id"])
    own = root
    if version == 3:
        own = own / ("amendment-" + value["amendment"]["parent_amendment_id"])
    if version in (2, 3):
        own = own / ("amendment-" + value["amendment"]["id"])
    own.mkdir(parents=True)
    (state / ("deployment-drained-" + value["release_id"] + ".json")).write_text("{}")
    if selected:
        (own / ".amendment-selected.json").write_text("{}")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(value))
    runner = Path(__file__).resolve().parents[1] / "scripts/Deploy-K98Release.ps1"
    source = runner.read_text(encoding="utf-8")
    start = source.index("$script:staged=Join-Path $policy.state_directory")
    end = source.index("$members=@($manifest.members)", start)
    script = tmp_path / "early.ps1"
    script.write_text(
        r"""
param([string]$Runner,[string]$ManifestPath,[string]$State)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
$ast=[Management.Automation.Language.Parser]::ParseFile($Runner,[ref]$null,[ref]$null)
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-OriginalReleaseUnselected'},$true)
. ([scriptblock]::Create($fn.Extent.Text))
function Assert-ReleaseAmendment($Current,[string]$Stage){}
function Assert-AmendmentSelection([string]$Path,$Current,[string]$Hash){}
$manifest=Get-Content -LiteralPath $ManifestPath -Raw|ConvertFrom-Json
$releaseId=$manifest.release_id;$ExpectedSHA256='fixture'
$policy=@{state_directory=$State}
""" + source[start:end] + "\nWrite-Output 'MEMBER_COPY_AND_PREFLIGHT_REACHABLE'\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            ps,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Runner",
            str(runner),
            "-ManifestPath",
            str(manifest_path),
            "-State",
            str(state),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert (result.returncode == 0) == (not selected), result.stdout + result.stderr
    assert ("MEMBER_COPY_AND_PREFLIGHT_REACHABLE" in result.stdout) == (not selected)
    if selected:
        assert "superseded" in result.stderr


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "parent_hash",
        "parent_selection",
        "parent_version",
        "parent_identity",
        "root_intent",
        "parent_intent",
        "root_complete",
        "parent_complete",
        "root_start",
        "parent_start",
        "root_script",
        "parent_script",
        "root_step",
        "parent_step",
        "later_root_script",
    ],
)
def test_native_successor_requires_exact_unadvanced_ancestors(tmp_path, fault):
    ps = shutil.which("powershell.exe")
    if not ps:
        pytest.skip("Windows PowerShell required")
    base = specification()
    parent = amendment()
    current = successor()
    root = tmp_path / "release"
    root.mkdir()
    parent_stage = root / ("amendment-" + parent["amendment"]["id"])
    parent_stage.mkdir()

    def write(path, value):
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    parent["amendment"]["base_manifest_sha256"] = write(root / ".release.json", base)
    if fault == "parent_version":
        parent["version"] = 3
    if fault == "parent_identity":
        parent["host"] = "different"
    current["amendment"]["base_manifest_sha256"] = write(parent_stage / ".release.json", parent)
    if fault == "parent_hash":
        current["amendment"]["base_manifest_sha256"] = "0" * 64
    selected = dict(
        release_id=base["release_id"],
        amendment_id=parent["amendment"]["id"],
        manifest_sha256=hashlib.sha256((parent_stage / ".release.json").read_bytes()).hexdigest(),
    )
    if fault == "parent_selection":
        selected["amendment_id"] = current["amendment"]["id"]
    write(root / ".amendment-selected.json", selected)
    for name, stage, step in [("root", root, "sql"), ("parent", parent_stage, "sql-correction")]:
        receipts = stage / ".receipts"
        receipts.mkdir()
        if fault != name + "_intent":
            write(
                receipts / (step + ".intent.json"),
                dict(stage="starting", release_id=base["release_id"], step=step),
            )
        if fault == name + "_complete":
            write(receipts / (step + ".complete.json"), {})
        if fault == name + "_start":
            write(stage / "start-requested.json", {})
    if fault in ("root_script", "parent_script"):
        current["members"][0]["sha256"] = (base if fault == "root_script" else parent)["members"][
            0
        ]["sha256"]
    if fault in ("root_step", "parent_step"):
        current["steps"][1]["id"] = "sql" if fault == "root_step" else "sql-correction"
    if fault == "later_root_script":
        current["members"].append(dict(name="old.ps1", sha256=base["members"][0]["sha256"]))
        current["steps"][-1]["verify"]["file"] = "old.ps1"
    write(tmp_path / "current.json", current)
    before = {
        p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    script = tmp_path / "gate.ps1"
    script.write_text(
        r"""
param([string]$Runner,[string]$Current,[string]$Parent)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
$ast=[Management.Automation.Language.Parser]::ParseFile($Runner,[ref]$null,[ref]$null)
foreach($name in @('Assert-ReleaseAmendment','Assert-AmendmentSelection')) {
 $fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 . ([scriptblock]::Create($fn.Extent.Text))
}
function Assert-AdminPath([string]$Path){if(-not(Test-Path -LiteralPath $Path)){throw 'Missing fixture'}}
function Read-Pinned([string]$Path,[string]$Hash,[long]$Limit){if((Get-FileHash -LiteralPath $Path).Hash.ToLowerInvariant() -cne $Hash){throw 'Hash differs'};return ,[IO.File]::ReadAllBytes($Path)}
function Read-Control([string]$Path){Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}
Assert-ReleaseAmendment (Read-Control $Current) $Parent
""",
        encoding="utf-8",
    )
    runner = Path(__file__).resolve().parents[1] / "scripts/Deploy-K98Release.ps1"
    result = subprocess.run(
        [
            ps,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Runner",
            str(runner),
            "-Current",
            str(tmp_path / "current.json"),
            "-Parent",
            str(parent_stage),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert (result.returncode == 0) == (fault is None), result.stdout + result.stderr
    assert {
        p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()
    } == before
