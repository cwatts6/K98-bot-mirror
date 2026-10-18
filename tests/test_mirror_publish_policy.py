"""Exercise the production publisher's rsync filter against inert files only."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / ".github/workflows/publish-mirror.yml"
BUILD_STEP = "Build publishable tree (exclude secrets)"
RSYNC_ARGUMENTS = (
    "-av",
    "--delete",
    "--exclude=.git/",
    "--exclude=publish/",
    "--exclude-from=.publishignore",
    "./",
    "./publish/",
)
AUTHORITY_PATHS = (
    "scripts/run_export_authority.py",
    "services/export_execution_authority.py",
    "tests/test_export_authority_boundaries.py",
    "tests/test_export_authority_launcher.py",
    "tests/test_export_execution_authority.py",
)


def publisher_rsync_arguments(workflow):
    """Validate the real invocation; never execute workflow shell text."""
    job = workflow["jobs"]["publish"]
    steps = [step for step in job["steps"] if step.get("name") == BUILD_STEP]
    if len(steps) != 1 or set(steps[0]) != {"name", "run"}:
        raise AssertionError("Expected one unconditional publisher build step")
    if workflow.get("defaults") or job.get("defaults"):
        raise AssertionError("Publisher shell/directory defaults need explicit review")
    lines = steps[0]["run"].replace("\\\n", " ").splitlines()
    commands = [shlex.split(line, comments=True) for line in lines]
    copies = [command for command in commands if command and command[0] == "rsync"]
    if copies != [["rsync", *RSYNC_ARGUMENTS]]:
        raise AssertionError("Publisher rsync invocation drifted from the reviewed filter contract")
    return copies[0][1:]


def load_publisher_arguments(path, *, required):
    if not path.is_file():
        if required:
            raise AssertionError("Production publisher workflow must be present")
        return None  # The scrubbed mirror deliberately excludes this workflow.
    return publisher_rsync_arguments(yaml.safe_load(path.read_text(encoding="utf-8")))


class MirrorPublishPolicyTests(unittest.TestCase):
    def publisher_arguments(self):
        return load_publisher_arguments(
            PUBLISHER,
            required=os.environ.get("GITHUB_REPOSITORY", "").casefold() == "cwatts6/k98-bot",
        )

    def test_actual_publisher_uses_reviewed_rsync_contract(self):
        arguments = self.publisher_arguments()
        if arguments is None:
            self.skipTest("Production-only publisher is absent from this scrubbed checkout")
        self.assertEqual(arguments, list(RSYNC_ARGUMENTS))

    def test_missing_publisher_fails_when_required(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.yml"
            with self.assertRaisesRegex(AssertionError, "must be present"):
                load_publisher_arguments(missing, required=True)
            self.assertIsNone(load_publisher_arguments(missing, required=False))

    def test_publisher_drift_is_rejected_before_execution(self):
        command = shlex.join(["rsync", *RSYNC_ARGUMENTS])
        for changed in (
            command.replace("--exclude-from=.publishignore", ""),
            command.replace(".publishignore", "other-filter"),
            command.replace("-av", "-avL"),
            command.replace("./publish/", "../outside/"),
            command + "; echo unexpected",
            command + "\n" + command,
            "# " + command,
            "echo publisher removed",
        ):
            with self.subTest(command=changed):
                workflow = {"jobs": {"publish": {"steps": [{"name": BUILD_STEP, "run": changed}]}}}
                with self.assertRaises(AssertionError):
                    publisher_rsync_arguments(workflow)
        workflow = {"jobs": {"publish": {"steps": [{"name": BUILD_STEP, "run": command}]}}}
        self.assertEqual(publisher_rsync_arguments(workflow), list(RSYNC_ARGUMENTS))

    def test_exceptions_are_exact_and_sources_exist(self):
        lines = (ROOT / ".publishignore").read_text(encoding="utf-8").splitlines()
        includes = [line for line in lines if line.startswith("+ ")]
        self.assertEqual(includes, [f"+ /{path}" for path in AUTHORITY_PATHS])
        for path in AUTHORITY_PATHS:
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertLess(lines.index(f"+ /{path}"), lines.index("**/*auth*"))

    def test_rsync_preserves_source_and_excludes_credentials(self):
        rsync = shutil.which("rsync")
        if rsync is None:
            self.skipTest("rsync is unavailable; the Linux publication-policy job requires it")
        # Production uses its actual validated argv. The scrubbed mirror tests
        # the same filter contract, with actual-publisher coverage skipped above.
        arguments = self.publisher_arguments() or list(RSYNC_ARGUMENTS)
        allowed = (*AUTHORITY_PATHS, "services/ordinary.py", "README.md", ".publishignore")
        excluded = (
            ".git/config",
            ".env",
            ".env.production",
            "credentials/synthetic.json",
            "nested/service_account-test.json",
            "nested/token-test.json",
            "nested/credentials-test.json",
            "nested/apikey-test.txt",
            "nested/api_key-test.txt",
            "nested/auth.json",
            "services/other_authority.py",
            "nested/private.json",
            "nested/id_rsa-test",
            "nested/key.pem",
            "nested/key.key",
            "statsupdate-synthetic.json",
            "logs/synthetic.txt",
            "data/synthetic.json",
            "downloads/synthetic.txt",
            "nested/scripts/run_export_authority.py",
            "scripts/run_export_authority.py.bak",
            "scripts/run_export_authority.py.key",
            ".github/workflows/publish-mirror.yml",
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            destination = source / "publish"
            destination.mkdir(parents=True)
            for name in (*allowed, *excluded):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"inert fixture, no credentials\n")
            (source / ".publishignore").write_bytes((ROOT / ".publishignore").read_bytes())
            subprocess.run(
                [rsync, *arguments],
                cwd=source,
                check=True,
                capture_output=True,
                timeout=30,
            )
            actual = {
                path.relative_to(destination).as_posix()
                for path in destination.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual, set(allowed))
            for name in allowed:
                self.assertEqual((source / name).read_bytes(), (destination / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
