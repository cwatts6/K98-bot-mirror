"""Installed authority, import ordering, payload identity and recovery boundaries."""

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from scripts import verify_k98_update_pair as verifier
from tests.updater_source_assertions import installed_tool_fixture

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture(scope="module")
def archive():
    return verifier.build_contract_archive(ROOT)


def isolated(code, *arguments):
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, *map(str, arguments)],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


def test_archive_is_deterministic_and_contains_exact_source_bytes(archive):
    assert archive == verifier.build_contract_archive(ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert tuple(z.namelist()) == verifier.CONTRACT_ARCHIVE_MEMBERS
        for name in z.namelist():
            assert z.read(name) == (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
    assert all(not n.startswith("core/") for n in verifier.CONTRACT_ARCHIVE_MEMBERS)


@pytest.mark.parametrize(
    "damage",
    [
        "hash",
        "missing",
        "extra",
        "case",
        "traversal",
        "compressed",
        "duplicate",
        "trailer",
        "oversize",
    ],
)
def test_archive_refuses_ambiguity_even_with_matching_digest(archive, damage):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        members = {n: z.read(n) for n in z.namelist()}
    if damage == "hash":
        with pytest.raises(ValueError, match="identity"):
            verifier.validate_contract_archive(archive, "0" * 64)
        return
    if damage == "missing":
        del members["services/__init__.py"]
    elif damage in {"extra", "case", "traversal"}:
        members[
            {"extra": "core/evil.py", "case": "Services/__init__.py", "traversal": "../evil.py"}[
                damage
            ]
        ] = b"raise Exception()"
    elif damage == "oversize":
        members["services/__init__.py"] = b"x" * verifier.CONTRACT_ARCHIVE_LIMIT
    raw = verifier._archive_bytes(members)
    if damage == "compressed":
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for n, b in sorted(members.items()):
                z.writestr(n, b)
        raw = stream.getvalue()
    elif damage == "duplicate":
        stream = io.BytesIO(raw)
        with pytest.warns(UserWarning, match="Duplicate"):
            with zipfile.ZipFile(stream, "a") as z:
                z.writestr("services/__init__.py", b"")
        raw = stream.getvalue()
    elif damage == "trailer":
        raw += b"extra bytes"
    with pytest.raises(ValueError):
        verifier.validate_contract_archive(raw, sha(raw))


@pytest.mark.parametrize(
    "conflict",
    [
        "services",
        "kvk.dal.new_source_admin_dal",
        "core.export_sql_connection",
        "bot_config",
        "constants",
        "file_utils",
        "event_cache",
    ],
)
def test_activation_refuses_preloaded_modules_without_eviction(tmp_path, archive, conflict):
    path = tmp_path / verifier.CONTRACT_ARCHIVE
    path.write_bytes(archive)
    result = isolated(
        """
import runpy,sys,types
v=runpy.run_path(sys.argv[1]); marker=types.ModuleType(sys.argv[5]);sys.modules[sys.argv[5]]=marker
try:v['activate_contract_archive'](sys.argv[2],sys.argv[3],sys.argv[4])
except ValueError as e:
 assert 'before verifier selection' in str(e)
 assert sys.modules[sys.argv[5]] is marker
else:raise AssertionError('conflict admitted')
""",
        ROOT / "scripts/verify_k98_update_pair.py",
        path,
        sha(archive),
        tmp_path,
        conflict,
    )
    assert result.returncode == 0, result.stderr


def test_real_archive_imports_override_old_modules_but_preserve_core_root(tmp_path, archive):
    path = tmp_path / verifier.CONTRACT_ARCHIVE
    path.write_bytes(archive)
    result = isolated(
        """
import runpy,sys,pathlib
v=runpy.run_path(sys.argv[1]);v['activate_contract_archive'](sys.argv[2],sys.argv[3],sys.argv[4])
import services.export_execution_dal as dal
import services.export_runtime_composition as composition
import core.export_release_seed as seed
assert dal.__file__.startswith(sys.argv[2])
assert composition.__file__.startswith(sys.argv[2])
assert pathlib.Path(seed.__file__).resolve()==pathlib.Path(sys.argv[4])/'core/export_release_seed.py'
assert 'bot_config' not in sys.modules
try:import services.this_is_not_bundled
except ModuleNotFoundError:pass
else:raise AssertionError('unexpected package fallback')
""",
        ROOT / "scripts/verify_k98_update_pair.py",
        path,
        sha(archive),
        ROOT,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("damage", [None, "archive", "observation", "binding", "verifier"])
def test_real_isolated_preparer_selects_archive_before_application_imports(tmp_path, damage):
    tools, digest = installed_tool_fixture(tmp_path)
    observation = tmp_path / "observation.json"
    # Invalid commits force a stop before Git, output or runtime operations, but
    # only after the real isolated bootstrap and transitive core imports succeed.
    observation.write_text(
        json.dumps(
            {
                "bindings": {
                    "root": str(ROOT),
                    "before": "invalid",
                    "target": "invalid",
                    "contract_verifier_sha256": digest,
                }
            }
        )
    )
    expected = sha(observation.read_bytes())
    if damage == "archive":
        (tools / verifier.CONTRACT_ARCHIVE).write_bytes(b"tampered")
    elif damage == "observation":
        observation.write_text("{}")
    elif damage == "binding":
        data = json.loads(observation.read_bytes())
        data["bindings"]["contract_verifier_sha256"] = "0" * 64
        observation.write_text(json.dumps(data))
        expected = sha(observation.read_bytes())
    elif damage == "verifier":
        (tools / "verify_k98_update_pair.py").write_text("raise Exception('EXECUTED_TAMPER')")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(tools / "prepare_k98_update.py"),
            "--observation",
            str(observation),
            "--observation-sha256",
            expected,
            "--output",
            str(tmp_path / "unused"),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode != 0
    message = {
        None: "Exact commit binding required",
        "archive": "archive identity differs",
        "observation": "Protected observation identity differs",
        "binding": "Observation and installed verifier differ",
        "verifier": "Installed verifier identity differs",
    }[damage]
    assert message in result.stderr, result.stderr
    assert "EXECUTED_TAMPER" not in result.stderr
    assert not (tmp_path / "unused").exists()


@pytest.mark.parametrize("damage", [None, "pair", "archive", "binding", "duplicate"])
def test_recovery_loads_sealed_pair_before_any_application_import(tmp_path, damage):
    tools, digest = installed_tool_fixture(tmp_path)
    release = tmp_path / "release"
    release.mkdir()
    for old, new in [
        ("verify_k98_update_pair.py", "Verify-NewPair.py"),
        ("recovery_release_seed.py", "Verify-RecoverySeed.py"),
        (verifier.CONTRACT_ARCHIVE, verifier.CONTRACT_ARCHIVE),
    ]:
        (release / new).write_bytes((tools / old).read_bytes())
    config = {
        "root": str(ROOT),
        "contract_verifier_sha256": digest,
        "extra_members": [
            {
                "name": "Verify-NewPair.py",
                "sha256": sha((release / "Verify-NewPair.py").read_bytes()),
            },
            {"name": verifier.CONTRACT_ARCHIVE, "sha256": digest},
        ],
    }
    if damage == "pair":
        (release / "Verify-NewPair.py").write_text("raise Exception('EXECUTED_TAMPER')")
    elif damage == "archive":
        (release / verifier.CONTRACT_ARCHIVE).write_bytes(b"tampered")
    elif damage == "binding":
        config["extra_members"][1]["sha256"] = "0" * 64
    elif damage == "duplicate":
        config["extra_members"].append(config["extra_members"][1])
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps(config))
    result = isolated(
        """
import sys,runpy,json
h=runpy.run_path(sys.argv[1]);v=h['load_release_verifier'](json.load(open(sys.argv[2])))
assert callable(v['verify_bot_sql_contracts'])
assert 'bot_config' not in sys.modules
import services.export_execution_dal as d
assert 'contract_verifier.zip' in d.__file__
""",
        release / "Verify-RecoverySeed.py",
        conf,
    )
    if damage is None:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
        assert "EXECUTED_TAMPER" not in result.stderr
        assert "differs" in result.stderr, result.stderr


def test_release_archive_binding_is_required_before_import(tmp_path):
    with pytest.raises(ValueError, match="binding"):
        verifier.activate_release_archive(
            {"contract_verifier_sha256": "a" * 64, "extra_members": []}, tmp_path
        )


def test_pair_bootstrap_authenticates_source_before_selecting_archive(monkeypatch, tmp_path):
    from types import SimpleNamespace

    config = {"root": str(tmp_path)}
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps(config))
    steps = []
    monkeypatch.setattr(
        verifier.sys,
        "argv",
        [
            "pair",
            "--bindings",
            str(path),
            "--sha256",
            sha(path.read_bytes()),
            "--preflight",
            "--sql-contracts",
        ],
    )
    monkeypatch.setattr(verifier, "sys", SimpleNamespace(flags=SimpleNamespace(isolated=True)))
    # argparse owns real sys.argv; native source/custody and SQL are test seams.
    monkeypatch.setattr(
        verifier, "verify_live_source", lambda c, **kw: steps.append("source") or {}
    )
    monkeypatch.setattr(verifier, "activate_release_archive", lambda c, p: steps.append("archive"))
    monkeypatch.setattr(verifier, "verify_sql_contracts", lambda c, p: steps.append("sql"))
    verifier.main()
    assert steps == ["source", "archive", "sql"]


@pytest.mark.parametrize("damage", ["missing", "changed"])
def test_source_compatibility_cannot_claim_current_archive_without_its_hash(damage):
    from scripts.validate_k98_update_compatibility import classify
    from tests.test_update_application_compatibility import NEW, OLD, PATH, installed_manifest

    installed = installed_manifest()
    if damage == "missing":
        del installed["files"]["contract_verifier.zip"]
    else:
        installed["files"]["contract_verifier.zip"] = "0" * 64
    result = classify(
        "a" * 40,
        "b" * 40,
        [PATH],
        lambda commit, path: OLD if commit == "a" * 40 else NEW,
        installed,
    )
    assert result["classification"] == "UPDATER_UPGRADE_REQUIRED"
    assert "contract_verifier.zip" in result["updater_members"]


def test_native_manifest_and_archive_gates_in_windows_powershell(tmp_path):
    import os

    if os.name != "nt":
        pytest.skip("Windows PowerShell 5.1 parser and gate execution")
    tools, digest = installed_tool_fixture(tmp_path)
    manifest_path = tools / "update-tool.json"
    manifest_hash = sha(manifest_path.read_bytes())
    script = tmp_path / "gates.ps1"
    script.write_text(
        r"""
param([string]$Root,[string]$Tools,[string]$ManifestHash,[string]$ArchiveHash)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$checked=0
foreach($name in @('K98-SourceUpdate.ps1','Update-K98.ps1','Upgrade-K98InstalledUpdater.ps1')) {
 $tokens=$null;$errors=$null
 $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $Root ('scripts/'+$name)),[ref]$tokens,[ref]$errors)
 if($errors.Count){throw 'Native syntax error'}
 foreach($func in @($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true))) {
  if($func.Name -in @('Assert-UpgradeTool','Upgrade-Hash','Assert-ContractVerifier')) {
   $definition=Join-Path (Split-Path -Parent $Tools) ($func.Name+'.ps1')
   [IO.File]::WriteAllText($definition,$func.Extent.Text)
   . $definition
  }
 }
 $checked++
}
# Exercise exact inventory/hash gates; native ACL creation is covered separately.
function Assert-Custody([string]$Path) { if(-not(Test-Path -LiteralPath $Path)){throw 'Missing custody target'} }
function Must-Refuse([scriptblock]$Action) {
 $refused=$false
 try { & $Action } catch { $refused=$true }
 if(-not $refused){throw 'Damaged input admitted'}
 $script:checked++
}
Assert-UpgradeTool $Tools $ManifestHash;$checked++
$archive=Join-Path $Tools 'contract_verifier.zip'
$bytes=[IO.File]::ReadAllBytes($archive)
[IO.File]::WriteAllBytes($archive,[byte[]]@(1,2,3))
Must-Refuse { Assert-UpgradeTool $Tools $ManifestHash }
[IO.File]::WriteAllBytes($archive,$bytes)
$manifest=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes((Join-Path $Tools 'update-tool.json')))|ConvertFrom-Json
# A complete historical package without the archive remains a valid upgrade source.
$old=Join-Path (Split-Path -Parent $Tools) 'historical';$null=New-Item -ItemType Directory -Path $old
foreach($file in Get-ChildItem -LiteralPath $Tools -File){if($file.Name -notin @('contract_verifier.zip','update-tool.json')){Copy-Item -LiteralPath $file.FullName -Destination $old}}
$manifest.files.PSObject.Properties.Remove('contract_verifier.zip')
$oldRaw=[Text.Encoding]::UTF8.GetBytes(($manifest|ConvertTo-Json -Depth 5 -Compress))
[IO.File]::WriteAllBytes((Join-Path $old 'update-tool.json'),$oldRaw)
Assert-UpgradeTool $old (Upgrade-Hash $oldRaw);$checked++
function Read-Bytes([string]$Path,[string]$Expected,[long]$Limit) {
 if($Limit -ne 2MB -or $Expected -cne $ArchiveHash -or (Split-Path -Leaf $Path) -cne 'contract_verifier.zip'){throw 'Archive read not exactly bound'}
 return [byte[]]@(0)
}
$c=[pscustomobject]@{contract_verifier_sha256=$ArchiveHash;extra_members=@([pscustomobject]@{name='contract_verifier.zip';sha256=$ArchiveHash})}
Assert-ContractVerifier;$checked++
$c.extra_members=@();Must-Refuse { Assert-ContractVerifier }
$c.extra_members=@([pscustomobject]@{name='contract_verifier.zip';sha256=('0'*64)});Must-Refuse { Assert-ContractVerifier }
$c.extra_members=@([pscustomobject]@{name='contract_verifier.zip';sha256=$ArchiveHash},[pscustomobject]@{name='contract_verifier.zip';sha256=$ArchiveHash});Must-Refuse { Assert-ContractVerifier }
@{status='PASS';checks=$checked;native_acl_mocked=$true}|ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            str(ROOT),
            str(tools),
            manifest_hash,
            digest,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["checks"] == 10
