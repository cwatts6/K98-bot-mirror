"""Exercise the offline caller at its real updater handoff."""

import io
import json
from pathlib import Path
import zipfile

import pytest

from scripts import rehearse_p0a_package as rehearsal
from scripts.verify_k98_update_pair import validate_contract_archive


@pytest.mark.parametrize("missing", [False, True])
def test_rehearsal_binds_projected_private_archive_before_prepare(tmp_path, monkeypatch, missing):
    source_root = Path(rehearsal.__file__).resolve().parents[1]
    names = set(rehearsal.TOOL_SOURCE_PATHS) | set(rehearsal.CONTRACT_ARCHIVE_MEMBERS)
    mirror_files = {name: (source_root / name).read_bytes() for name in names}
    private_files = dict(mirror_files)
    # An unchanged private-only source difference must survive mirror promotion.
    special = "services/__init__.py"
    private_files[special] += b"\n# retained private predecessor\n"
    if missing:
        del private_files[special]
    root = tmp_path / "checkout"
    for name, raw in mirror_files.items():
        member = root / name
        member.parent.mkdir(parents=True, exist_ok=True)
        member.write_bytes(raw)

    def archive(files):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as stream:
            for name, raw in files.items():
                stream.writestr(name, raw)
        return out.getvalue()

    before = "a" * 40
    spec = {
        "before": before,
        "contracts": {
            "sql_contract": {
                "before": {"server": "MINI_AMD", "database": "ROK_TRACKER", "collation": "test"}
            }
        },
    }
    monkeypatch.setattr(rehearsal, "specification", lambda: spec)
    monkeypatch.setattr(rehearsal, "ROOT", root)

    def git(unused_root, *args):
        if args[0] == "archive":
            return archive(private_files if args[-1] == before else mirror_files)
        assert args == ("ls-files", "--cached", "--others", "--exclude-standard")
        return "\n".join(sorted(names)).encode()

    monkeypatch.setattr(rehearsal, "git", git)
    seed = tmp_path / "seed"
    seed.mkdir()
    for name in (
        "ReleaseBindings",
        "authority-template",
        "bot-template",
        "AutomaticStartupPolicy",
        "ManualProcessPairPlan-CANDIDATE",
        "host_acl",
        "bot_identity",
        "identity_issuance",
        "file_access",
        "key_inventory",
        "writer_drain",
        "sql_installation",
    ):
        value = {"seed_plan": {"path": "C:/lab/seed.json"}, "state_directory": "C:/lab/state"}
        (seed / (name + ".json")).write_text(json.dumps(value))
    (seed / "Start-ReviewedAutomaticStartup.ps1").write_text("# fixture")
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(rehearsal.tempfile, "mkdtemp", lambda **kw: str(output))
    monkeypatch.setattr(
        rehearsal.sys,
        "argv",
        ["rehearse", "--seed-directory", str(seed), "--sql-source", str(tmp_path / "sql")],
    )

    class HandoffReached(Exception):
        pass

    def prepare(observation, changes, blob, destination, tools, **kwargs):
        raw = (tools / "contract_verifier.zip").read_bytes()
        pin = observation["bindings"]["contract_verifier_sha256"]
        validate_contract_archive(raw, pin)
        with zipfile.ZipFile(io.BytesIO(raw)) as stream:
            assert stream.namelist() == sorted(rehearsal.CONTRACT_ARCHIVE_MEMBERS)
            assert stream.read(special) == private_files[special].replace(b"\r\n", b"\n")
        assert observation["bindings"]["target"] == "0" * 40
        assert not destination.exists()
        raise HandoffReached

    monkeypatch.setattr(rehearsal, "prepare_update", prepare)
    if missing:
        with pytest.raises(ValueError, match="Rehearsal contract source missing"):
            rehearsal.main()
        assert not (output / "tool/contract_verifier.zip").exists()
    else:
        with pytest.raises(HandoffReached):
            rehearsal.main()
