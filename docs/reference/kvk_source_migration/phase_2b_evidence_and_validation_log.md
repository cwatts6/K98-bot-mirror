# KVK Source Migration — Phase 2B evidence and validation log

## Current KVK delivery status - 2026-09-09

**S1 is accepted and merged** through mirror PR #263 and production PR #570. Its archived
200-test smoke and restart/startup evidence remain historical S1 results.

**S2A is implemented, disposable-SQL validated and operator accepted.** The migration created
twelve tables; all 96 expected-rejection tests and complete fixture rollback passed.
SQL [PR #78](https://github.com/cwatts6/K98-bot-SQL-Server/pull/78) and documentation
[PR #264](https://github.com/cwatts6/K98-bot-mirror/pull/264) are in review; review fixes and their
fresh validation are recorded in the S2A delivery. PR acceptance/merge must be rechecked at handoff.

**Next: finish S2A PR review, then scope S2B for its own explicit G3 approval.** Do not rerun S1
or S2A as an unstarted slice. S2B has no implementation approval; no production SQL deployment,
source activation or successor execution is authorized. This current status supersedes historical
pending/next-S1/S2A preparation wording below.

2026-09-09. Current authority: Chris Watts **“G2 approved, please proceed”.**

## 1. Summary

G2 approval is recorded, including the authorized EndScanID correction workflow. Phase 2B
prepares ten bounded implementation packs and ten matching approval starters, with exact file
manifests, dependencies, tests, security boundaries and rollback. G3 remains pending for each
slice. S1 is ready for the first implementation approval. No implementation has run.

## 2. File Manifest

Only 28 Markdown paths are authored in this pass: 22 new and six additive updates below.
A pre-edit snapshot captured 1,502 existing files, including ignored Phase-1 CSV evidence.
Existing unrelated work is retained. Temporary authoring/check scripts are outside the repository.

## 3. New Files

- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S1 Offline Source Validation.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S1 Offline Source Validation.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S2A SQL Observation Facts.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S2A SQL Observation Facts.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S2B SQL Publication State.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S2B SQL Publication State.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S3A Player Window Calculations.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S3A Player Window Calculations.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S3B Acceptance and Atomic Publication.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S3B Acceptance and Atomic Publication.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S4A Shared Reports and Cards.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S4A Shared Reports and Cards.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S6 Release Readiness and Controlled Activation.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S6 Release Readiness and Controlled Activation.md`

## 4. Modified Files

Append-only approval/delivery/navigation entries preserve historical pending-gate statements.
These latest entries establish current authority rather than rewriting prior evidence.

- `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md`
- `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/README.md`
- `docs/reference/README.md`

## 5. SQL Changes

None. SQL repo main HEAD `fc0e94ebd2e0a98286069c8a8b71365dd5178657`, origin
`https://github.com/cwatts6/K98-bot-SQL-Server.git`, clean at inspection. Proposed S2A/S2B
migration/table/validation paths are manifests only; none created. No database access or RDP.
SQL/config production parity is operator-attested, not independently queried live evidence.

Bot main HEAD `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; origin
`https://github.com/cwatts6/K98-bot-mirror.git`, production `https://github.com/cwatts6/K98-bot.git`.
Existing documentation changes were present on entry. No Git synchronization, branch change,
commit, staging, PR or push. Local definitions remain distinct from deployed evidence.

## 6. Helpers Reused

Read current core instructions, canonical task template and Phase-1/2 references. Previously read
core references were hash-checked unchanged. Focused drift checks found 48 distinct Phase-1
C01–C65 source paths still matching HEAD after LF normalization. Planning inspected existing
route, DAL, reporting, export, config transaction and startup integration points. Reuse contracts
are assigned to exact packs, not implemented. No private workbook/player rows were copied.

## 7. Refactor Findings

Split SQL facts from publication state, pure calculations from transaction integration, shared
reports from exports, and intake from config/recovery. Keep legacy export grouping and generic
ProcConfig/WS1 reliability debt out of scope. The config request must share the Windows import
transaction and survive a subsequent importer error; S5B owns this bounded integration. G2
semantics are unchanged. Migration names remain proposed with date/sequence allocation controlled
before future authoring. No helper code or runtime scaffolding is created by this pass.

## 8. Test Plan and Actual Outcomes

Only safe documentation/static checks run in this pass; final actual results are appended below.
Per-slice pytest/disposable-SQL cases in packs are future requirements, not claimed passes.
No pytest, smoke imports, registration runtime, SQL deployment validator or workbook processing:
there are no executable changes. SQL validators can write logs/connect, so are not run against
the read-only SQL repository. A first oversized temporary generator invocation hit Windows
command-length error 206 before execution; shorter temporary scripts completed authoring.

## 9. Security Review Decision and Evidence

Bot: documented docs-only skip for exactly these 28 Markdown paths. No parser, permission,
network, config, persistence, SQL or execution behavior changed. Existing unrelated dirty files
are excluded. SQL: separate no-change skip at the recorded HEAD. No standard/deep scan or
Changes scan run. Future code slices require separate exact bot/SQL Changes targets, Deep off,
through k98-security-review-routing; S6 documentation-only scope has its own skip. No public
workbooks, player rows, credentials or vulnerability evidence are included.

## 10. Deployment Steps

None authorized or performed. Approve G3 for S1 only to begin offline source validation.
Review each delivered slice before its successor; no starter executes itself. S6 prepares
concrete readiness/rollback evidence and stops at G4 before deployment, imports, exports,
Discord actions, restarts or activation. Live jobs/config editor paths, permissions, external
consumers and operational recovery remain bounded readiness gaps. They do not block S1.
A later fight or final overall report is not required; use synthetic aggregate revision cases.

## 11. Deferred Optimisations

No new deferred item established. Preserve existing WS1 and legacy reporting debt separately.
Do not use migration implementation as permission for a generic exporter/config rewrite.


### Final actual document checks

- Architecture validator: passed, 0 Python files checked.
- Deferred-item validator: passed, 53 Markdown files checked.
- Security-routing validator: passed, 0 errors and 0 warnings.
- Test selector: exit 0 with all 28 authored paths explicitly supplied. Recommended smoke imports
  and command registration deliberately skipped: documentation creates no runtime surface.
- git diff --check: passed.
- All ten packs contain ordered canonical sections 1–17. Existing/read/predecessor paths resolve;
  proposed create paths do not collide. All 96 local links in new/appended text resolve; text
  hygiene passed. Future SQL migration names remain controlled proposals.
- Preservation passed across all 1,502 captured files: six original append prefixes intact,
  every other captured file byte-identical, exactly 22 expected new documentation paths.
- Both branches/HEADs unchanged, both staging areas empty, SQL worktree clean. The approved
  70-scenario document and original evidence files remain unchanged in this planning pass.

These checks validate documentation consistency and preservation, not implementation behavior,
SQL concurrency, deployed parity or operational readiness. Stop at G3 review; S1 is recommended.
