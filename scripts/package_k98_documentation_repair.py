"""Build the bounded P0a documentation-custody repair from immutable Git evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BEFORE = "ded19ccda7c3c7ebeeb9379b15a72ae39cb935a4"
TARGET = "6753d6879afdba416aeb82495ec4c5493974e4cb"
ROOT = "C:/discord_file_downloader/docs/task_packs"
R4 = "f576c7ab570b54590c917c9bd434f2e254e32d61c60cfca13467a0f7e029c37b"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def build(diagnostic, repo, output, source):
    report = json.loads(Path(diagnostic).read_bytes())
    if (
        report["stage"] != "COLLECTED_METADATA_NOT_REPAIR_APPROVAL"
        or report["host"] != "MINI_AMD"
        or report["expected_before"] != BEFORE
        or report["expected_target"] != TARGET
        or report["errors"]
    ):
        raise ValueError("Complete matching MINI_AMD diagnostic required")

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], timeout=30)

    rows = {}
    for row in report["records"]:
        path = row["path"].replace("\\", "/")
        if path == ROOT or path.startswith(ROOT + "/"):
            if path in rows or row["status"] != "OBSERVED_METADATA_ONLY":
                raise ValueError("Duplicate or unreadable repair entry")
            rows[path] = row
    sid = rows[ROOT]["owner_sid"]
    if not sid.startswith("S-1-5-21-") or not sid.endswith("-1001"):
        raise ValueError("Observed application principal differs")
    for row in rows.values():
        directory = row["directory"]
        owner_token = "BA" if row["owner_sid"] == "S-1-5-32-544" else sid
        inherit_token = "OICIID" if directory else "ID"
        expected_sddl = (
            f"O:{owner_token}G:{sid}D:AI(A;{inherit_token};FA;;;SY)"
            f"(A;{inherit_token};FA;;;BA)(A;{inherit_token};0x1200a9;;;{sid})"
        )
        if (
            row["attributes"] != (16 if directory else 32)
            or row["owner_sid"] not in {sid, "S-1-5-32-544"}
            or row["group_sid"] != sid
            or len(row["aces"]) != 3
            or row["access_protected"]
            or row["sddl"] != expected_sddl
        ):
            raise ValueError("Unexpected original metadata")
        rules = {ace["sid"]: ace for ace in row["aces"]}
        if set(rules) != {sid, "S-1-5-18", "S-1-5-32-544"}:
            raise ValueError("Unexpected original trustees")
        for trustee, ace in rules.items():
            if (
                ace["rights"] != (1179817 if trustee == sid else 2032127)
                or not ace["inherited"]
                or ace["type"] != "Allow"
                or ace["propagation"] != "None"
                or ace["inheritance"]
                != ("ContainerInherit, ObjectInherit" if directory else "None")
            ):
                raise ValueError("Original access differs from reviewed read-only application ACL")
    tree = git("ls-tree", "-r", "-z", BEFORE, "--", "docs/task_packs")
    blobs = {}
    for record in tree.split(b"\0"):
        if not record:
            continue
        header, path = record.split(b"\t", 1)
        mode, kind, oid = header.split()
        if mode != b"100644" or kind != b"blob":
            raise ValueError("Ordinary installed documentation blobs required")
        name = path.decode("utf-8").removeprefix("docs/task_packs/")
        raw = git("cat-file", "blob", oid.decode())
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Documentation member exceeds bound")
        variants = {raw, raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")}
        observed = rows.get(ROOT + "/" + name)
        if observed is None or observed["length"] not in {len(value) for value in variants}:
            raise ValueError("Observed documentation size differs from installed Git: " + name)
        blobs[name] = sorted(digest(value) for value in variants)
    observed_files = {path[len(ROOT) + 1 :] for path, row in rows.items() if not row["directory"]}
    observed_dirs = {path[len(ROOT) + 1 :] for path, row in rows.items() if row["directory"]}
    if observed_files != set(blobs) or len(blobs) != 357 or observed_dirs != {"", "archive"}:
        raise ValueError("Exact installed documentation inventory differs")
    entries = []
    for path, row in sorted(rows.items()):
        if path == ROOT:
            continue
        name = path[len(ROOT) + 1 :]
        entry = {"path": name, "directory": row["directory"], "sddl": row["sddl"]}
        if not row["directory"]:
            entry["hashes"] = blobs[name]
        entries.append(entry)
    plan = {
        "version": 1,
        "before": BEFORE,
        "target": TARGET,
        "sid": sid,
        "root_sddl": rows[ROOT]["sddl"],
        "entries": entries,
        "updater_manifest_sha256": R4,
        "failed_package": r"C:\ProgramData\K98\S11\updates\95c20000-a4e7-4f21-a0f3-b01ac8937a30\package",
        "bindings_sha256": "546c49772eacedf5ae0c16f543609291b4d95ddb9116f8e37f2f7ce619c2fd13",
    }
    raw_plan = (json.dumps(plan, ensure_ascii=True, indent=2) + "\n").encode()
    library = git("show", TARGET + ":scripts/K98-SourceUpdate.ps1")
    script = (Path(source) / "Repair-K98DocumentationCustody.ps1").read_text(encoding="utf-8")
    script = script.replace("__PLAN_SHA256__", digest(raw_plan)).replace(
        "__LIBRARY_SHA256__", digest(library)
    )
    output = Path(output)
    output.mkdir(exist_ok=False)
    for name, raw in {
        "CustodyRepairPlan.json": raw_plan,
        "K98-SourceUpdate.ps1": library,
        "Repair-K98DocumentationCustody.ps1": script.encode(),
    }.items():
        (output / name).write_bytes(raw)
    result = {
        "stage": "BUILT_NOT_APPROVED_OR_INSTALLED",
        "files": 357,
        "directories": 2,
        "before": BEFORE,
        "target": TARGET,
        "manifest_sha256": digest(raw_plan),
        "library_sha256": digest(library),
        "repair_script_sha256": digest(script.encode()),
        "diagnostic_sha256": digest(Path(diagnostic).read_bytes()),
    }
    (output / "package-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(
        json.dumps(build(args.diagnostic, args.repo, args.output, Path(__file__).parent), indent=2)
    )
