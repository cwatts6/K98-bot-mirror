from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _script(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


def test_acl_configuration_uses_protected_allow_list_and_owner_transfer() -> None:
    script = _script("Configure-Phase51ImmutableHandoffAcl.ps1")

    assert "SetAccessRuleProtection($true, $false)" in script
    assert "$acl.SetOwner($SqlSid)" in script
    assert "FileSystemRights]::Modify" in script
    assert script.count("FileSystemRights]::ReadAndExecute") >= 3
    assert "'S-1-1-0'" in script
    assert "'S-1-5-11'" in script
    assert "'S-1-5-32-545'" in script
    assert "ConfirmProductionRoot" in script
    assert "ConfirmWritersStopped" in script
    assert "phase5-1-acl-configuration/v1" in script


def test_evidence_runner_requires_frozen_commits_and_persists_failures() -> None:
    script = _script("Invoke-Phase51ImmutableHandoffEvidence.ps1")

    assert "[string]$ExpectedSqlCommit" in script
    assert "[string]$ExpectedBotCommit" in script
    assert "receipt.failed.json" in script
    assert "EvidenceVersion = 2" in script
    assert "AclHardenedAtUtc" in script
    assert "AclOwnerIdentity" in script
    assert "ClaimedFileAcl" in script
    assert "Assert-TrackedWorktreeClean -RepositoryRoot $SqlRepoRoot" in script
    assert "Assert-TrackedWorktreeClean -RepositoryRoot $BotRepoRoot" in script
    assert "is not a live DL_bot.py process" in script
    assert "if (-not $attempt.Denied)" in script
    assert script.index("MutationAttempts = @($mutationAttempts)") < script.index("Status = 'FAIL'")


def test_evidence_runner_counts_only_access_denied_as_denial() -> None:
    script = _script("Invoke-Phase51ImmutableHandoffEvidence.ps1")

    assert "$exception -is [UnauthorizedAccessException]" in script
    assert "$exception.HResult -eq -2147024891" in script
    assert "Denied = $accessDenied" in script
    assert "Delete returned without access denial" in script
    assert "throw [UnauthorizedAccessException]::new(" not in script


def test_failed_evidence_reset_is_pinned_and_shape_specific() -> None:
    script = _script("Reset-Phase51FailedEvidence.ps1")

    assert "ROK_TRACKER_BACKUP_TEST_KS4_PHASE3_REHEARSAL" in script
    assert "Phase 5.1 failed-evidence reset refuses the production database." in script
    assert "ConfirmDiscardFailedAttempt" in script
    assert "ConfirmWritersStopped" in script
    assert "receipt.failed.json" in script
    assert "95713E9CBDD1DFCB2D4080C2537F418D43CA0DA25F0D7D6631F4F7C97B89DC47" in script
    assert script.index("Move-Item -LiteralPath $renamedPath") < script.index(
        "DELETE dbo.KS4_ImportFileClaim"
    )
    assert "IF @@ROWCOUNT <> 1" in script
    assert "phase5-1-failed-evidence-reset/v1" in script
