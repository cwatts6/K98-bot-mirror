"""Exact D5 release admission; no SQL, VM, provider or installed-host operations."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as update
from services.export_execution_protocol import encode

ROOT = Path(__file__).resolve().parents[1]
PATHS = sorted(update.P02_D5_COMBINED_PATHS)
TARGET = "d" * 40


def descriptor(transition=update.D5_CONTRACT_TRANSITION):
    return dict(
        version=4,
        profile="p02_d4_v1",
        bot_predecessors=[update.D4_PREDECESSOR],
        sql_commit=update.D4_SQL_COMMIT,
        migrations=[dict(id=update.D4_MIGRATION, sha256=update.D4_PROFILE_HASH)],
        contract_transition=transition,
    )


@pytest.fixture
def bound_pair(monkeypatch):
    """Hash-bound inert preimages, retaining real family selection and inventory.

    The real current 80 postimages have a separate assertion. These fixtures do
    not need private production Git history in mirror CI or execute source bytes.
    """
    original_hash = update.sha256
    marker = b"test-only-pinned-sha256:"
    monkeypatch.setattr(
        update,
        "sha256",
        lambda raw: raw[len(marker) :].decode() if raw.startswith(marker) else original_hash(raw),
    )

    def make(transition=update.D5_CONTRACT_TRANSITION):
        entry = next(t for t in update.reviewed_transitions() if t["id"] == transition)
        old, new = {}, {}
        for member in entry["members"]:
            for values, field in ((old, "before_sha256"), (new, "after_sha256")):
                values[member["path"]] = (
                    marker + member[field].encode() if member[field] is not None else None
                )
        new[update.RELEASE_DESCRIPTION] = encode(descriptor(transition))
        read = lambda revision, path: (old if revision == update.D4_PREDECESSOR else new).get(path)
        changes = [p for p in new if new[p] != old.get(p)]
        return old, new, read, changes

    return make


def test_all_89_historical_entries_preserved_and_current_family_exact():
    entries = update.reviewed_transitions()
    assert len(entries) == 92
    assert hashlib.sha256(encode(dict(version=1, transitions=entries[:89]))).hexdigest() == (
        "2dc508adfe1410609124eedeec41fb9c21855ab62e8d53e99f128eca45c04135"
    )
    current = next(t for t in entries if t["id"] == update.D5_CONTRACT_TRANSITION)
    assert current["id"] == update.D5_CONTRACT_TRANSITION
    assert {m["path"] for m in current["members"]} == update.P02_D5_COMBINED_PATHS
    assert len(current["members"]) == 80
    for member in current["members"]:
        from tests.updater_source_assertions import before_p02_maintenance_hash

        assert before_p02_maintenance_hash(ROOT, member["path"]) == member["after_sha256"], member[
            "path"
        ]
    assert json.loads((ROOT / update.RELEASE_DESCRIPTION).read_bytes()) == descriptor()


@pytest.mark.parametrize(
    "transition", [update.D4_CONTRACT_TRANSITION, update.D5_CONTRACT_TRANSITION]
)
def test_direct_complete_pair_and_descriptor_accept(bound_pair, transition):
    _, _, read, changes = bound_pair(transition)
    expected = (
        update.P02_D5_COMBINED_PATHS
        if transition == update.D5_CONTRACT_TRANSITION
        else update.P02_D4_COMBINED_PATHS
    )
    assert (
        update.check_protocol_transition(
            "services/maintenance_dal.py", read, update.D4_PREDECESSOR, TARGET
        )
        == expected
    )
    update.check_d4_release_binding(update.D4_PREDECESSOR, TARGET, changes, read)
    update.check_transition_inventory(changes, read, update.D4_PREDECESSOR, TARGET)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("damage", ["missing-target", "changed-target", "changed-preimage"])
def test_every_member_must_match_including_unchanged_peers(bound_pair, path, damage):
    old, new, read, changes = bound_pair()
    if damage == "missing-target":
        new.pop(path)
    elif damage == "changed-target":
        new[path] += b"drift"
    else:
        old[path] = b"wrong predecessor"
    with pytest.raises(ValueError, match="not installed/reviewed"):
        update.check_protocol_transition(
            "player_self_service/stats_runtime.py", read, update.D4_PREDECESSOR, TARGET
        )
    # Full entrypoint also handles an already-present/foreign D4 marker: the
    # adoption-only descriptor helper deliberately skips that historical case.
    with pytest.raises(ValueError):
        update.source_plan(
            {"AutomaticStartupPolicy.json": {"source_hashes": {}}},
            update.D4_PREDECESSOR,
            TARGET,
            changes,
            read,
        )


@pytest.mark.parametrize(
    "transition", [update.D4_CONTRACT_TRANSITION, update.D5_CONTRACT_TRANSITION]
)
def test_descriptor_cannot_select_the_other_source_family(bound_pair, transition):
    _, new, read, changes = bound_pair(transition)
    other = (
        update.D4_CONTRACT_TRANSITION
        if transition == update.D5_CONTRACT_TRANSITION
        else update.D5_CONTRACT_TRANSITION
    )
    new[update.RELEASE_DESCRIPTION] = encode(descriptor(other))
    with pytest.raises(ValueError):
        update.check_d4_release_binding(update.D4_PREDECESSOR, TARGET, changes, read)


@pytest.mark.parametrize(
    "damage",
    ["partial-inventory", "source-only", "wrong-predecessor", "old-maintenance", "old-stats"],
)
def test_partial_mixed_or_unbound_adoption_refuses(bound_pair, damage):
    _, new, read, changes = bound_pair()
    before = update.D4_PREDECESSOR
    if damage == "partial-inventory":
        changes.remove("player_self_service/stats_runtime.py")
    elif damage == "source-only":
        new.pop(update.RELEASE_DESCRIPTION)
    elif damage == "wrong-predecessor":
        before = "f" * 40
    elif damage == "old-maintenance":
        new["services/maintenance_dal.py"] = b"old maintenance"
    else:
        new["player_self_service/stats_runtime.py"] = b"old stats"
    with pytest.raises(ValueError):
        update.source_plan(
            {"AutomaticStartupPolicy.json": {"source_hashes": {}}},
            before,
            TARGET,
            changes,
            read,
        )


@pytest.mark.parametrize(
    "damage",
    [
        "91-entries",
        "81-members",
        "missing-member",
        "foreign-family",
        "foreign-path",
        "duplicate-member",
        "duplicate-id",
        "bad-hash",
        "oversize",
    ],
)
def test_registry_refuses_expansion_or_drift(monkeypatch, damage):
    value = json.loads((ROOT / "scripts/k98_update_transitions.json").read_bytes())
    current = value["transitions"][-1]
    if damage == "91-entries":
        value["transitions"].append(deepcopy(current))
    elif damage == "81-members":
        current["members"].append(deepcopy(current["members"][0]))
    elif damage == "missing-member":
        current["members"].pop()
    elif damage == "foreign-family":
        current["id"] = "unreviewed_large_family"
    elif damage == "foreign-path":
        current["members"][0]["path"] = "services/export_foreign.py"
    elif damage == "duplicate-member":
        current["members"][-1] = deepcopy(current["members"][0])
    elif damage == "duplicate-id":
        current["id"] = value["transitions"][0]["id"]
    elif damage == "bad-hash":
        current["members"][0]["after_sha256"] = "g" * 64
    raw = b" " * 232449 if damage == "oversize" else encode(value)
    original = Path.read_bytes
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: raw if p.name == "k98_update_transitions.json" else original(p),
    )
    with pytest.raises(ValueError):
        update.reviewed_transitions()


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_registry_newline_forms_fit_unchanged_byte_cap(monkeypatch, newline):
    raw = (
        (ROOT / "scripts/k98_update_transitions.json")
        .read_bytes()
        .replace(b"\r\n", b"\n")
        .replace(b"\n", newline)
    )
    assert len(raw) <= 232448
    original = Path.read_bytes
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: raw if p.name == "k98_update_transitions.json" else original(p),
    )
    assert len(update.reviewed_transitions()) == 91


def test_source_plan_binds_both_fixes_and_document_archive_without_new_runtime_pin(bound_pair):
    old, new, read, changes = bound_pair()
    old_doc, new_doc = "docs/task_packs/history.md", "docs/task_packs/archive/history.md"
    old[old_doc], new[new_doc] = b"preserved history", b"preserved history"
    changes += [old_doc, new_doc]
    previous = {
        "AutomaticStartupPolicy.json": {
            "source_hashes": {
                p: update.sha256(raw)
                for p, raw in old.items()
                if raw is not None and update.bootstrap_source_path(p)
            }
        }
    }
    plan, payload = update.source_plan(previous, update.D4_PREDECESSOR, TARGET, changes, read)
    for path in ("services/maintenance_dal.py", "player_self_service/stats_runtime.py"):
        assert plan["new_pins"][path] == update.sha256(new[path])
        assert payload[path] == new[path]
    assert old_doc not in plan["new_pins"] and new_doc not in plan["new_pins"]
    by_path = {x["path"]: x for x in plan["source_members"]}
    assert by_path[old_doc]["target_sha256"] is None
    assert by_path[new_doc]["before_sha256"] == []


def test_updater_package_binds_actual_new_tool_and_registry(tmp_path):
    from tests.updater_source_assertions import installed_tool_fixture

    tools, archive = installed_tool_fixture(tmp_path)
    manifest = json.loads((tools / "update-tool.json").read_bytes())
    for name in ("prepare_k98_update.py", "k98_update_transitions.json"):
        assert (tools / name).read_bytes() == (ROOT / "scripts" / name).read_bytes()
        assert hashlib.sha256((tools / name).read_bytes()).hexdigest() == manifest["files"][name]
    assert hashlib.sha256((tools / "contract_verifier.zip").read_bytes()).hexdigest() == archive


@pytest.mark.parametrize(
    "path", ["services/maintenance_dal.py", "player_self_service/stats_runtime.py"]
)
def test_historical_bridge_refuses_unknown_successor(monkeypatch, path):
    from tests.updater_source_assertions import before_d5_qualification_hash

    before_d5_qualification_hash(ROOT, path)
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: original(p) + b"\n# unknown\n")
    with pytest.raises(AssertionError):
        before_d5_qualification_hash(ROOT, path)
