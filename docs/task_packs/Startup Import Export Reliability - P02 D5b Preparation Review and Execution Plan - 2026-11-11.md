# P02 D5b preparation review and execution plan — 2026-11-11

**Source-only preparation review complete. Recommend a bounded offline test and
case-binding packet next; full native D5b remains no-go under the unchanged
limits.** No runtime, SQL, test, permission or VM change was made in this review.
This packet is the requested plan before further implementation/native work.

## Scope summary and evidence status

The approved D5 scope and D5a closeout remain authoritative. Preserve F01–F32,
C01–C16, 73 action pairs, 52 actions, 22 kinds, four empty kinds and separately
counted Recheck/group/batch/outcome paths. D5b still requires 42 detailed states,
14 exports, exact numeric/latest-name semantics, original queued bytes and all
six actual maintenance children. Offline tests do not replace those native cases.

All 21 inputs remain consumed. No extra input, replay, copy/reset/restore,
scheduling change, installation, grant or production/provider action is assumed.
The three D5a.2 receipts, original drain failures and SQL 3961 evidence remain
unchanged. The failed inventory's missing session-closure evidence remains
unverified; later successful observations do not repair it retroactively.

Bot source is `e7443e37212ca91e20d531b3684cc369d0fe1505` plus the approved
uncommitted D5a.1 patch. SQL source HEAD is
`b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; the fixed release payload remains
`ba5c6acbefba0eb89cb18842a7f6c6811096759b`, migration
`20261111_001_p02_d4_combined`, profile `p02_d4_v1`. The combined script/profile
SHA-256 values remain `8c0c99d92c14cac6da6e22076a5620927bac4c8af3deaa50950d66062381a8dc`
and `57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171`.

## Receipt reconciliation findings

| Question | Source/retained evidence | Disposition |
| --- | --- | --- |
| Why is the October 3 migration's deployment link missing? | The October lab fixture explicitly imported 23 historical migration rows without executing those migrations. Its body inserts `SchemaMigrationHistory`, not matching deployment rows. Historical readback labels this row `LAB_IMPORTED_HISTORY/20261003_001_export_legacy_direct_permissions.sql`, applied by `LAB_METADATA_IMPORT_FROM_RETAINED_READ_20261029`, retaining deployment ID `66cebeda-882c-43d1-9c64-25b9d5455724`. | Imported fixture lineage explains the dangling reference. It is not evidence that a local deployment row was lost. Do not manufacture a deployment row or rerun the historical migration. The latest inventory did not select the provenance label; this explanation rests on labelled historical readback and matching observed migration tuple. |
| Does the missing old deployment link itself fail D4 prerequisite admission? | `deploy/SqlDeploy.ModuleRelease.ps1` checks each prerequisite's unique Applied status and exact checksum. Its separate outcome check requires deployment linkage for the release being adjudicated. | Do not turn the older prerequisite link into an invented mandatory repair. Preserve its provenance limitation. This does not waive either of the two genuinely absent prerequisite rows. |
| Do the matching 174 module hashes establish the formal Phase 1 release? | Retained `phase1_fresh_support.py` installed 139 numeric column changes and 11 procedures using its own guarded transaction. `phase1_shared_names_install.py` installed 26 modules, checked permissions/other definitions and committed. They recorded local installation results, not formal migration/deployment receipts. | The VM received rehearsal-specific changes. Body matches cannot establish execution of `20261109_001_p02_phase1_sql_exports`. Its Applied receipt is absent. Do not insert a synthetic receipt or rerun the formal installer over an unqualified postimage. |
| Is the daily read plan installed? | `20261106_001_personal_stats_daily_read_plan` is absent from the current selected history. Its formal migration also guards a procedure image and a covering-index shape; D5a raw module hashes did not inventory that entire contract. | Actual formal pre/postimage remains unclassified. Neither absence of the receipt nor a procedure match alone proves the index state. Historical production observations are not proof about this VM. |

Private provenance anchors, read locally only:

- `.codex_artifacts/mge-isolated-vm-plan-20261029/qualification-preparation/MigrationFixture.Body.ps1`
  and `archive-contracts-payload.json` (`migration_fixture` only).
- `.codex_artifacts/mge-isolated-vm-plan-20261029/sql-baseline-verify-20261031T101051247Z-4c3fe57d624f4420b2b87d16c89d6c39.json`,
  `guest_result.fixture_history_readback` for the exact historical row.
- `.codex_artifacts/p021/phase1-final-continuation-result-7aea1e23b649448ea68df59b714445cb/`,
  the two named installer sources and `result.json` installation receipts.
- `.codex_artifacts/p025/d5a2-inventory-result-4833c46c87d94bd0b203753ee843458d.json`,
  SHA-256 `75f86c3597cf01cd8421938170767c58d4c07a461a866c1e968fcdaca315686a`.

## Qualification target and installer boundary

The retained target is `MINI_AMD` / `K98_P021_PreImport_20261107`, database ID 7,
READ_ONLY / RESTRICTED_USER. Its 174 matching definitions are raw UTF-8 hashes,
not D4's structural preimages including ownership, signatures and permissions.
All 17 D4 additions, including four work ledgers, are absent. Their absence is
not an empty-work pass.

The production release coordinator requires `MINI_AMD` / `ROK_TRACKER`, writable
MULTI_USER state, exact predecessor contracts, sequence identity and fixed
backup-wrapper/job/permission bindings. It also checks backup age and trigger
conditions not established by D5a. Its resource gate requires 8 GiB available
memory on the SQL host. That cannot be satisfied as a free-memory reserve inside
the fixed 8 GiB VM. The original qualification rule remains 8 GiB free host RAM
before VM start; neither gate is silently substituted for the other.

Do not run the production Apply path against the retained target. Do not rename
the database, add memory, relax the production gate, grant rights or label a lab
receipt as a formal release installation. Any future lab adapter needs its own
reviewed identity/resource contract and explicit qualification-only receipt.
Production installer qualification remains a separate obligation.

Existing SQL tests `tests/test_d4_combined_release.py` and
`tests/test_p02_d4_installed_dependencies.py` demonstrate narrowly controlled
test copies, fixture receipts and disposable local databases. They do not
authorize a new database here. The combined-release test's single database-guard
substitution is a pattern to review, not sufficient adaptation for D5b. These
opt-in native tests were not executed.

## Case-to-state bindings

| Case | Existing usable evidence | Requirement before native acceptance |
| --- | --- | --- |
| 42 detailed states / 14 exports | Retained reference and candidate captures, independent oracle and final continuation result. | Exact new combined candidate and explicitly authorized comparable state for each case. Map historical case IDs to current candidate producers/readers; do not relabel a historical pass. |
| Original queued bytes | Immutable 14-section payload, SHA-256 `24e9f15dc71d0e3ef2b0d2e08383f9c623bb37328521126336504b896775264c`. | Offline decoding/formatting compatibility may be tested with inert adapters. A later candidate capture comparison needs its own authorized SQL read/work packet; never regenerate and overwrite the original. |
| `import` child | Existing full-sized data can support physical statistics/index work without consuming a new file. | Writable installed target, legitimately admitted due generation and actual child entry. No fresh producer/import is currently authorized; do not replay the ready file or fabricate due work. |
| `configuration` child | Retained configuration/report data. | Eligible counters, scan/generation and threshold branch. Do not force counts or age timestamps to make the branch run. |
| `player_report` child | Retained player-report output. | Actual owned due work and FULLSCAN statistics operation on `STATS_FOR_UPLOAD`, not merely invocation of a skipped child. |
| `kvk_output` child | Retained KVK outputs. | Valid output-complete provenance and matching per-KVK generation/object identity/header revision plus aggregate claim. An initially empty ledger is insufficient. |
| `final_stats` child | Retained dashboard/summary results. | Running claim and exact generation/flags for actual dashboard/summary maintenance; final-stats backup demand must remain visible in the receipt contract. |
| `post_import` child | Historical completed import/continuation receipt. | Authorized current due request and actual `sp_updatestats` work; prior completion does not authorize replay or create current work. |
| Q05 receipt negative controls | Current SQL returns the six fixed kinds. Bot validation only requires `post_import`, and completeness is computed over returned rows. | Offline omission/malformed-response tests first. An incomplete six-kind response must not become complete; physical cleanup and original errors must remain preserved. |
| Q06 isolation boundary | Original raw-reader error 3961 and managed-reader guard sources. | Classify actual readers/guards now; both native arrival orders remain D5c. No claim of general raw-reader/DDL safety. |

The six SQL children require autocommit/session ownership and perform durable
ledger, statistics or index changes. An enclosing rollback-only transaction is
rejected and cannot supply repeatable equivalent pre-states. Existing completed
data may support some physical operations without new inputs, but that does not
establish valid due work, installation or permission to mutate this target.
Full D5b and balanced D5e execution therefore have no executable route under the
current unchanged state and authorization.

## Concrete next execution plan: offline packet only

The following is proposed for a separate bounded test-only implementation. It
requires no native SQL/VM work, input consumption, production code correction or
permission change. Do not import historical installer/runner modules: several
have installation/reset or connection behavior. Read their source and use only
explicitly isolated data/oracle adapters.

1. **Bind the candidate and case manifest.** Record Bot HEAD plus the exact
   approved drain-patch bytes, SQL payload/profile hashes and the retained audit's
   artifact hashes. Include every D5b case, its baseline artifact, callable/layer,
   required state, expected effect, evidence fields and explicit offline/native
   status. A missing mapping blocks that case; zero rows or a missing timing is
   not a pass. Do not include credentials or copy retained input files.
2. **Challenge Q05 without SQL.** Add a focused test-only module alongside
   `tests/test_maintenance_dal.py`, using inert connection/cursor doubles. Cover
   each single-kind omission, post-import-only response, empty response,
   duplicate/foreign kind, multiple result sets, invalid due/completed/claimed
   generation and claim identity combinations. Preserve the first failing
   result. Do not change assertions or production validation to get green.
   Pin accepted generation/claim combinations to `usp_RunMaintenance` and the
   ledger definition before encoding them as expectations.
3. **Exercise service completeness and cleanup.** For the six-kind positive
   response, check complete versus pending/failed/unknown; for positive
   final-stats demand, require its backup-request evidence. Missing final_stats
   must not bypass that obligation. Drive `run_maintenance`, `result` and
   `evidence`, including a late provider error followed by cleanup failure.
   Check no success receipt escapes and foreign/unknown ownership is retained.
4. **Bind the retained oracle and queued-payload tests.** Reuse the existing
   audited 42-state/14-export map and original payload. Isolate candidate pure
   conversion/serialization paths with network and SQL constructors replaced by
   fail-fast doubles before import. Compare exact bigint/decimal/NULL/negative/
   overflow/halfway behavior and retained latest-name semantics. Preserve the
   original execution-clock cutoff and separate tied-zero-rank adjudication.
   Do not treat reference replay as new database-output correctness.
5. **Return the results before correction/native action.** Deliver the manifest,
   executed test hashes, exact failures/passes, uncovered cases and a proposed
   minimal correction if Q05 is reproduced. The recommended response contract is
   exactly one row for each of the six kinds because the current SQL endpoint is
   unscoped. A scoped subset would require an explicit different endpoint
   contract; it must not be inferred from missing rows.

Proposed files are a focused `tests/test_p02_d5b_receipt_contract.py`, a focused
retained-payload test if existing tests cannot accommodate inert fixtures, and
private `.codex_artifacts/p025/d5b-*` manifests/results. Runtime ownership stays
in `services/maintenance_dal.py` and `services/maintenance_service.py`; commands
and views gain no SQL or validation logic. Reuse existing custody helpers and
test doubles. No broader refactor is needed. Q05 is already an in-scope finding,
not a new deferred item or a proved production truncation incident.

## Conditional native packet — not authorized or ready

Before proposing commands, all of the following must be concrete:

1. An explicitly authorized suitable target/state and case-by-case due-work
   provenance, with no implicit copy/reset/restore/new input. No alternative
   database is selected by this review. The present read-only target fails this
   prerequisite. If no permissible state exists, retain no-go.
2. A reviewed qualification installation/adapter design: full structural
   pre/postimages including the daily-plan index, receipt provenance, exact
   candidate bytes, target identity and resource rules. Preserve production
   release guards and report lab qualification separately from installation.
3. A complete permission/dependency matrix: current observer access does not
   prove application least privilege, sequence/backup rights or job identity.
   No permission change or backup dispatch follows automatically from metadata.
4. A one-attempt operation table for installation, each output case and each
   actual child, with owned session/claim identity, entry/exit observations,
   resources, stop conditions and cleanup/outcome adjudication. Unknown effects
   stop further work; no blind retry, guessed KILL or released-claim replay.
5. Operator review of that exact packet before any native work. Do not run
   another broad inventory merely to reconfirm known absent prerequisites. If a
   narrow metadata observation is genuinely needed, specify it separately with
   exact allowlists and the existing D5a.2 bounds, then return its findings.

Keep the VM at four CPUs / 8 GiB / zero adapters. Preserve the host pre-start
8 GiB memory floor, disk reserves at least 8 GiB, RCSI off, version store below
512 MiB, optional-statistics log below 70%, observation timeout three seconds /
zero lock wait and held-metadata tests at most 30 seconds. Any later D5a.2-style
observation remains one attempt / 300 seconds / 48 statements / 512 rows per
statement / 2,048 total rows / 1 MiB receipt; it grants no workload authority.

D5e still requires equal warmup and at least five balanced OFF/ON pairs with
alternating first arm and comparable admitted pre-states. Overall median ON
must be <= OFF × 1.20 + 1,000 ms; each report stage <= OFF × 1.20 + 250 ms.
The 1,800-second rehearsal ceiling does not extend Bot timeouts. D5c/d/e/f,
D6 promotion, P03 blockers, essential P04 and D7/P05 acceptance remain separate.

## Validation and review boundary

This delta is a plan plus ignored source/evidence hash metadata. Documentation
validation and custody checks are recorded in
`.codex_artifacts/p025/d5b-preparation-review-validation.json`. Existing code,
collectors, test files, receipts and release pins are unchanged. No workload,
native test, migration or historical runner was executed.

Security routing for this documentation-only delta is a documented skip: it
adds no executable data access, permissions, persistence or file-handling path.
The later test/adapter patch needs its own Changes-only routing decision before
implementation/review; no Codebase or Deep scan is implied. Broad pytest,
smoke imports and command registration are skipped because they cannot validate
these documentary findings and could run outside the approved source-only scope.
Focused inert tests belong to the proposed next packet, not this review.

References:
[D5 scope](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20Review%20-%202026-11-11.md),
[obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md),
[D5a closeout](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Closeout%20and%20Feasibility%20-%202026-11-11.md).
