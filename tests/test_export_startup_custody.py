"""Administrative controls reject ordinary writers before imports or native writes."""

import builtins
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import core.export_execution_host as host
import core.export_startup_windows as native
import scripts.run_export_authority as launcher
import scripts.run_export_startup_issuer as issuer
from tests.test_export_authority_boundaries import source_tree

SID = "S-1-5-21-1-2-3-1001"


def native_acl(
    monkeypatch,
    affected,
    *,
    owner="S-1-5-32-544",
    rights=0x1200A9,
    reparse=False,
    other_reader=False,
):
    affected = Path(affected)

    class ACL:
        def __init__(self, path):
            self.path = Path(path)

        def GetAceCount(self):
            return 4 if other_reader and self.path == affected else 3

        def GetAce(self, index):
            entries = [
                ((0, 0), 0x1F01FF, "S-1-5-18"),
                ((0, 0), 0x1F01FF, "S-1-5-32-544"),
                ((0, 0), rights if self.path == affected else 0x1200A9, SID),
                ((0, 0), 1, "S-1-5-32-545"),
            ]
            return entries[index]

    class Descriptor:
        def __init__(self, path):
            self.path = Path(path)

        def GetSecurityDescriptorOwner(self):
            return owner if self.path == affected else "S-1-5-32-544"

        def GetSecurityDescriptorDacl(self):
            return ACL(self.path)

    file = SimpleNamespace(
        GetFileAttributes=lambda p: 0x400 if reparse and Path(p) == affected else 0
    )
    security = SimpleNamespace(
        LookupAccountName=lambda *_: ("installer", None, None),
        ConvertSidToStringSid=str,
        GetNamedSecurityInfo=lambda p, *_: Descriptor(p),
    )
    monkeypatch.setitem(sys.modules, "win32file", file)
    monkeypatch.setitem(sys.modules, "win32security", security)
    monkeypatch.setattr(launcher, "windows_sid", lambda: SID)
    monkeypatch.setattr(host, "current_sid", lambda: SID)
    return file


@pytest.mark.parametrize(
    "kind",
    [
        "source.py",
        "policy.json",
        "history.json",
        "publication.json",
        "source_directory",
        "state_directory",
    ],
)
@pytest.mark.parametrize(
    "damage",
    [
        None,
        "owner",
        "write",
        "create",
        "delete_child",
        "delete",
        "acl",
        "take_owner",
        "reparse",
        "private_reader",
    ],
)
def test_issuer_and_native_control_custody_are_strict(tmp_path, monkeypatch, kind, damage):
    path = tmp_path / kind
    if kind.endswith("directory"):
        path.mkdir()
    else:
        path.write_bytes(b"inert control")
    mask = {
        "write": 0x2,
        "create": 0x4,
        "delete_child": 0x40,
        "delete": 0x10000,
        "acl": 0x40000,
        "take_owner": 0x80000,
    }.get(damage, 0x1200A9)
    native_acl(
        monkeypatch,
        path,
        owner=SID if damage == "owner" else "S-1-5-32-544",
        rights=mask,
        reparse=damage == "reparse",
        other_reader=damage == "private_reader",
    )
    inspect = issuer.administrative_inspector({"protected_path": launcher.protected_path})
    for check in (inspect, native.administrative_path):
        if damage:
            with pytest.raises((launcher.AuthorityStartupError, host.HostBoundaryError)):
                check(path, private=True)
        else:
            assert check(path, private=True) == path


def test_matching_hash_does_not_allow_ordinary_policy_before_app_imports(tmp_path, monkeypatch):
    _, manifest, state = source_tree(tmp_path, monkeypatch)
    native_acl(monkeypatch, manifest, rights=0x1F01FF)
    monkeypatch.setattr(issuer, "__file__", str(tmp_path / "scripts" / "issuer.py"))
    monkeypatch.setattr(
        issuer.runpy,
        "run_path",
        lambda _: {"bootstrap": launcher.bootstrap, "protected_path": launcher.protected_path},
    )
    original = builtins.__import__
    application_imports = []

    def tracked_import(name, *args, **kwargs):
        if name.startswith(("core.", "services.", "kvk.")):
            application_imports.append(name)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    with pytest.raises(launcher.AuthorityStartupError):
        issuer.main(["--policy", str(manifest)])
    assert not application_imports and state.path == []


@pytest.mark.parametrize("operation", ["directory", "file"])
def test_unsafe_parent_stops_before_native_creation(tmp_path, monkeypatch, operation):
    file = native_acl(monkeypatch, tmp_path, rights=0x1F01FF)
    file.CreateDirectory = Mock()
    file.CreateFile = Mock()
    target = tmp_path / "fresh"
    with pytest.raises(host.HostBoundaryError):
        if operation == "directory":
            native.create_private_directory(target, SID)
        else:
            native.write_new_protected(target, b"bounded", SID)
    file.CreateDirectory.assert_not_called()
    file.CreateFile.assert_not_called()
    assert not target.exists()


def test_generated_directory_preserves_readers_and_checks_result(tmp_path, monkeypatch):
    target = tmp_path / "fresh"
    file = native_acl(monkeypatch, target)
    marker = object()
    attrs = Mock(return_value=marker)
    monkeypatch.setattr(native, "_attributes", attrs)
    file.CreateDirectory = Mock(side_effect=lambda p, _: Path(p).mkdir())
    native.create_private_directory(target, SID)
    attrs.assert_called_once_with(SID, directory=True)
    file.CreateDirectory.assert_called_once_with(str(target), marker)


@pytest.mark.parametrize("bad_result", [False, True])
def test_immutable_file_is_flushed_closed_and_readback_checked(tmp_path, monkeypatch, bad_result):
    target = tmp_path / "fresh.json"
    file = native_acl(monkeypatch, target, rights=0x1F01FF if bad_result else 0x1200A9)
    marker = object()
    monkeypatch.setattr(native, "_attributes", Mock(return_value=marker))
    handle = Mock()

    def create(p, access, share, attributes, disposition, flags, template):
        assert (access, share, attributes, disposition, flags, template) == (
            0x40000000,
            0,
            marker,
            1,
            0x80000000,
            None,
        )
        Path(p).touch(exist_ok=False)
        return handle

    file.CreateFile = Mock(side_effect=create)
    file.WriteFile = Mock(side_effect=lambda h, raw: target.write_bytes(raw))
    file.FlushFileBuffers = Mock()
    if bad_result:
        with pytest.raises(host.HostBoundaryError):
            native.write_new_protected(target, b"immutable", SID)
    else:
        native.write_new_protected(target, b"immutable", SID)
    handle.Close.assert_called_once()
    file.FlushFileBuffers.assert_called_once_with(handle)
    assert target.read_bytes() == b"immutable"
