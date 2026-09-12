# Codex Chat Starter — CrystalTech Path Refresh and Config Corrections

> **Status: delivered and operator accepted on 2026-08-25.** Mirror PR #234 and production PR
> #541 are ready for manual merge. This starter is retained as an archived execution record; its
> pre-implementation instructions are historical and are not an active task.

Work in the current `K98-bot-mirror` repository and complete the attached task pack:

`docs/task_packs/archive/Codex Task Pack - CrystalTech Path Refresh and Config Corrections.md`

Supporting source files:

- `crystaltech_paths.v1.proposed.json`
- `crystaltech_paths_review_corrected.xlsx`
- `CrystalTech Path Review - 2026-08-25.md`

The proposed JSON is the approved runtime data source. Its expected SHA-256 before changing only `meta.updated_at_utc` is:

`59daed30ae758a0b86f7d83168dd1b30519d27b3bfcabe6341d975dc76bb0bca`

The current production config should be:

- `config/crystaltech_paths.v1.json`
- Git blob SHA-1 `cd36a2402714c2e862ebd1e98b13444a854c43e9`
- SHA-256 `cdf57b8db36517e4de125e0db44f5b9f3b133072ca6d1bda82f55888cc1dd21f`

One-pass execution is approved for the task pack's locked config-only scope.

Proceed as follows:

1. Read `AGENTS.md`, `README-DEV.md`, `docs/reference/README.md`, `SECURITY.md`, the task pack, and applicable indexed references.
2. Use `k98-architecture-scope` for a concise pre-edit scope check. Do not stop unless the current config/source differs or scope must expand.
3. Use `k98-security-review-routing` and record a **Changes review** for the final `origin/main...HEAD` bot diff with **Deep Off**. Do not run a standard or deep codebase audit.
4. Create a focused branch from current `main`, suggested name `fix/crystaltech-path-refresh-2026-08`.
5. Verify the current config hash/blob before replacing it.
6. Copy the reviewed candidate into `config/crystaltech_paths.v1.json`.
7. Refresh only `meta.updated_at_utc` to the actual implementation UTC timestamp. Preserve all other metadata.
8. Do not regenerate from the uncorrected workbook.
9. Do not modify CrystalTech commands, services, assets, SQL, runtime progress, command registration, or archive/copy JSON files.
10. Add focused production-config regression tests as specified in the task pack.
11. Run the existing CLI validator, selected focused tests, repository gates, and pre-commit.
12. Inspect the final diff against the locked counts, totals, UIDs, semantic corrections, and ordering contract.
13. Run `k98-pr-review`.
14. Run `$codex-security:security-diff-scan` against the final base/head using `Scan type: Changes` and `Deep: Off`.
15. Commit, push, and create or update a PR against `K98-bot-mirror/main`.
16. Do not merge, promote, deploy, reload, or reset CrystalTech state. Return the PR ready for operator review.

Hard stops:

- Do not continue if the current config no longer matches the reviewed source.
- Do not continue if the proposed JSON hash differs before the permitted timestamp refresh.
- Do not expand into runtime code, SQL, assets, schema, or player-progress migration without reporting the blocker.
- Never run `/crystaltech admin_reset`.
- At initial execution, do not silently alter the pre-existing image/spelling consistency warnings
  excluded by the task pack. The operator later supplied an updated workbook and explicitly
  approved all four warning groups in the same PR.

Return the task pack's required delivery output, including:

- exact file manifest
- source-contract reconciliation
- counts and crystal-cost totals by path
- added/removed UID verification
- test and validator results
- final security routing and Changes-review evidence
- PR link and commit
- deployment and rollback handoff
- explicit confirmation of no SQL, command, UI, asset, progress-reset, or archive-config changes
