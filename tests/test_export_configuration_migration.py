"""Migration 010 embeds exactly the reviewed modules and guarded predecessors."""

import hashlib
import os
from pathlib import Path
import re
import subprocess

import pytest


def test_configuration_migration_literal_modules_and_predecessor_hashes():
    configured = os.getenv("K98_TARGET_CONTAINMENT_SQL_SOURCE")
    if not configured:
        pytest.skip("Explicit authoritative SQL source checkout required")
    root = Path(configured)
    text = (root / "migrations/20261015_010_configuration_replacement.sql").read_text(
        encoding="utf-8-sig"
    )
    literals = re.findall(r"SET @Apply=N'((?:[^']|'')*)';\nEXEC sys.sp_executesql @Apply;", text)
    assert len(literals) == 2
    for literal in literals:
        module = literal.replace("''", "'").replace(
            "CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1
        )
        name = module.splitlines()[0].split()[-1]
        relative = "sql_schema/" + name + ".StoredProcedure.sql"
        # Later migrations deliberately replace these procedures. Verify this
        # historical migration against its immutable reviewed postimage.
        source = (
            subprocess.check_output(
                ["git", "show", "95b4e91b86adbf66f7ab21fc48d195261bf3b4e3:" + relative], cwd=root
            )
            .decode("utf-8-sig")
            .replace("\r\n", "\n")
        )
        source = (
            source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").rstrip() + "\n"
        )
        assert module == source
        predecessor = (
            subprocess.check_output(
                ["git", "show", "9dc3e42beeed905ba9a3454ba1ad5e197c5db299:" + relative], cwd=root
            )
            .decode("utf-8-sig")
            .replace("\r\n", "\n")
        )
        predecessor = (
            predecessor[predecessor.index("CREATE PROCEDURE") :].strip().removesuffix("GO").rstrip()
            + "\n"
        )
        assert hashlib.sha256(predecessor.encode("utf-16-le")).hexdigest() in text
        assert hashlib.sha256(module.encode("utf-16-le")).hexdigest() in text
    assert "IF XACT_STATE()<>0 ROLLBACK" in text
    assert "sys.crypt_properties" in text
    assert "GRANT " not in text and "DROP " not in text
