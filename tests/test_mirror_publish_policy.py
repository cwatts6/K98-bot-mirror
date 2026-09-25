"""Exercise the production publisher's rsync filter against inert files only."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATHS = (
    "scripts/run_export_authority.py",
    "services/export_execution_authority.py",
    "tests/test_export_authority_boundaries.py",
    "tests/test_export_authority_launcher.py",
    "tests/test_export_execution_authority.py",
)


class MirrorPublishPolicyTests(unittest.TestCase):
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
        allowed = (*AUTHORITY_PATHS, "services/ordinary.py", "README.md")
        excluded = (
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
            destination = Path(directory) / "publish"
            destination.mkdir()
            for name in (*allowed, *excluded):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"inert fixture, no credentials\n")
            subprocess.run(
                [
                    rsync,
                    "-av",
                    "--delete",
                    "--exclude=.git/",
                    "--exclude=publish/",
                    f"--exclude-from={ROOT / '.publishignore'}",
                    f"{source}/",
                    f"{destination}/",
                ],
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
