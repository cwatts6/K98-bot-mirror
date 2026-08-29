# Codex Chat Starter - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup

Use the task pack at:

`C:\discord_file_downloader\docs\task_packs\Codex Task Pack - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup.md`

Begin KingdomScanData4 Phase 5.2 post-stabilisation cleanup.

Production has completed a week of numerous successful imports without error, so the stability prerequisite is satisfied. RDP and `\\tsclient` shared-drive access to `MINI_AMD` are approved for the audit and approved cleanup workflow.

Start with Phase 1 read-only audit only. Inspect the local machine and `MINI_AMD` comprehensively, including repository tracked/untracked/ignored state, generated build/review/scan directories, one-off launchers, rehearsal fixtures/evidence, SQL databases and physical files, backup history and backup files, scheduled tasks/process references, Git branches/worktrees/stashes, and disk capacity. Do not delete, drop, detach, overwrite, prune, stash-drop, branch-delete, stop/restart the bot, or create a PR until you have presented the exact retain/commit/archive/quarantine/delete manifest and I approve it.

Protect and include in the eventual cleanup PR:

- `README-DEV.md`;
- deletion of `docs/task_packs/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md` from the active folder;
- the materially updated archived copy at `docs/task_packs/archive/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md`;
- the Phase 5.2 cleanup task pack and this chat starter.

Do not restore, discard, overwrite, or clean those files. The archived PR #552 task pack is not a byte-identical move.

Treat `ROK_TRACKER`, system databases, current production backup requirements, credentials/environment files, `venv`, live bot data/logs/cache/queue/lock state, canonical Phase 5.2 production evidence, and unrelated artifacts such as the CrystalTech archive as `RETAIN` unless the audit establishes a narrower approved disposition. Unknown items always default to retain.

Use `k98-architecture-scope`, `k98-sql-validation`, `k98-test-selection`, `k98-deferred-optimisation-capture`, and `k98-security-review-routing` as specified by the task pack. This task does not authorise a repository-wide or Deep security scan. Do not run full pytest on the live bot worktree.

Proceed efficiently with the read-only audit and stop only when the exact proposed destructive manifest is ready for my approval or a material access, identity, integrity, backup-chain, SQL, permissions, capacity, security, scheduler, or runtime blocker is found.
