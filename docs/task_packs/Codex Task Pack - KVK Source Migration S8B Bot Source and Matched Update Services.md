# KVK Source Migration S8B — Bot Source and Matched Update Services

## 1. Task header and authority

Prepared 2026-09-13 for Chris Watts. Type: bounded Bot DAL/service integration.
Preparation is approved; **S8B implementation is not authorized by this pack alone**.
Start a new chat using the companion starter. First response is review/scope only.
Once the operator approves that concrete scope, continue without re-asking S7 decisions.
Estimated implementation effort from S7: 3–5 focused days, excluding approval/environment waits.

## 2. Required reading and entry

Read current AGENTS.md, README-DEV.md, docs/reference/README.md and all indexed core
engineering, execution, testing, skills/refactor and deferred-optimisation standards.
Read root/applicable SECURITY.md as context and use security routing.

- [Canonical S7/S8A closeout and exact documentation carry-forward](../reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md)
- [Approved integration contract and C01–C65 consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md)
- [Approved exact implementation/test manifests](../reference/kvk_source_migration/integration_implementation_manifests.md), especially S8B and S7-T01–T08
- [Architecture and EndScanID amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md)
- [Acceptance scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md)
- [Post-S6 requirements](../reference/kvk_source_migration/post_s6_integration_requirements.md) and [retained handoff](../reference/kvk_source_migration/post_s6_handoff_log.md)
- [S6 evidence](../reference/kvk_source_migration/release_evidence_log.md), [readiness](../reference/kvk_source_migration/release_readiness_and_rollback.md) and archived S7/S8A packs linked from the closeout

Read authoritative SQL instructions, migrations/README.md, docs/SQL_DELIVERY_LOG.md,
SQL_DATA_MIGRATION_GUARDRAILS.md and the five S8A snapshots plus all referenced legacy/new
input, publication, selection, config/request and routing objects in C:\K98-bot-SQL-Server.
Do not infer physical schema from Python or from proposed S7 names. Use conditional helper,
local SQL and startup/recovery references only where traced paths require them.

Recheck both branches, HEADs, remotes and status; preserve pending changes and ignored evidence.
Bot main/origin main anchor: 4f3bfadeb03258b1f0ddf28201862ba7afbc7a10.
Production/main: aa08f54cd67e0db89a2e64eedc6f79a57e098a29.
SQL main/origin main: 50310950a1adb7425e6db6bc86f38bdeb38e0830.
These are comparison anchors, never reset instructions. Both repos were clean before this
closeout documentation was authored. No bot-machine pulls have occurred.

## 3. Objective and boundaries

Implement durable fixed-season-source admission and sealed matched-update services, then
commit complete public selection and its immutable export intent atomically. These are Bot
service/DAL foundations; S8C owns upload/admin UX, S9 ordinary public readers and cards,
and S10 export coordination/workers. Do not claim S8B alone activates public routing.

No command/view/upload-route or runtime configuration-file changes, SQL schema changes, S8C/S9/S10 work,
provider/Discord write, real import/export, restart, deployment or activation is in scope.
S8A is accepted: do not rerun it or predecessors. A demonstrated SQL incompatibility needs
an exact separate SQL manifest/PR decision before changing schema. Retain the pending
SQL delivery-log documentation append separately; it cannot be included in the Bot PR.

## 4. Exact source and test manifest

Seven Create and thirteen Modify paths were checked against the entry checkout.
Unlisted runtime/test/config paths require an evidenced scope amendment. The documentation
carry-forward in section 5 is additional and mandatory.

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/models/source_integration.py` |
| Bot | Create | `kvk/dal/season_source_dal.py` |
| Bot | Create | `kvk/dal/source_update_dal.py` |
| Bot | Create | `kvk/services/season_source_service.py` |
| Bot | Create | `kvk/services/source_update_service.py` |
| Bot | Create | `tests/test_kvk_season_source.py` |
| Bot | Create | `tests/test_kvk_source_pairs.py` |
| Bot | Modify | `kvk/dal/new_source_import_dal.py` |
| Bot | Modify | `kvk/dal/kvk_all_import_dal.py` |
| Bot | Modify | `kvk/dal/new_source_publication_dal.py` |
| Bot | Modify | `kvk/dal/new_source_recovery_dal.py` |
| Bot | Modify | `kvk/dal/new_source_config_dal.py` |
| Bot | Modify | `kvk/services/new_source_publication_service.py` |
| Bot | Modify | `kvk/services/new_source_recovery_service.py` |
| Bot | Modify | `kvk/services/new_source_config_service.py` |
| Bot | Modify | `tests/test_kvk_source_publication.py` |
| Bot | Modify | `tests/test_kvk_source_recovery.py` |
| Bot | Modify | `tests/test_kvk_source_config_service.py` |
| Bot | Modify | `tests/test_kvk_source_sql_integration.py` |
| Bot | Modify | `tests/test_kvk_all_import_dal.py` |

## 5. Required documentation carry-forward and PR verification

The exact physical-path list in [closeout section 3](../reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md#3-exact-documentation-carry-forward-manifest)
is part of this task's file manifest, including this pack/starter, updated references and
both source deletion and archive destination for each of the four S7/S8A moves.
Preserve every path when branching; do not discard the local closeout because it is not
runtime work. Include all of it in the eventual separately authorized S8B Bot PR.

Before PR handoff, compare actual GitHub Files changed filename plus previous_filename to
the union of the 20 source/test paths, every closeout documentation path, and any explicitly
approved amendments. Prove specific omitted paths already merged with commit/ancestor and
content evidence; a statement that docs were handled earlier is insufficient. The original
27-path S7/S8A union is already merged in #273/#580; preserve that evidence and its contents.
SQL changes require their own SQL PR; record the single SQL documentation carry-forward separately.
No stage/commit/push/PR/merge/pull/fetch/reset is granted by this preparation starter.

## 6. Required behavior and architecture

- Models express source choice, lifecycle, update state, scoped identities, counterpart
  attestation and complete-selection/intent results. Services own business validation;
  DAL owns SQL, transactions, lock ordering and CAS. No Discord types in services.
- Explicit authorized source choice precedes both importers. Missing choice is setup-required;
  opposing source conflicts; same-choice retries return the original audited choice. No first
  upload wins, no legacy fallback on errors/disabled serving, no changing fixed source.
- Bind UpdateID to exact source/KVK/period/coverage/config/roster and immutable input revisions.
  Both upload orders work; first side remains private and generates no public selection or
  export intent. Seal only eligible matches or typed no-fight exception. Validate logical scan
  bindings, aggregate report identity and both tabs. Do not invent aggregate ScanIDs.
- Reuse an unchanged counterpart only with explicit retained revision/base update, actor and
  context confirmation. Reject stale revision/config/coverage/roster confirmations. Semantic
  duplicates retain logical identities and create no new generation/intent.
- Preserve B0/private onboarding, UTC increasing scan starts, no-fight zero/member rules,
  independent authoritative aggregates and overall, daily SCANORDER and legacy semantics.
  Preserve exact 11−10, 12−10, 13−10 and authorized 14−10 without another correction command.
  Pending exact endpoint resumes using valid prior authority; unmatched new endpoint remains
  private and labels the old final previous/config-pending. Do not manufacture attestation.
- Build outside the commit transaction. Validate the sealed tuple rather than global MAX/latest
  scan so later unmatched facts cannot starve a complete pair. Adapt publication/config/recovery
  callers in the manifest; accepted partial component history remains private history.
- Lock SeasonSource → SourceRouting → sorted component/complete period selections →
  config/request/update → intent/vector. Recheck lifecycle/source and expected versions;
  validate counts/hash and full unchanged-period membership. Commit complete pointer, audit
  and immutable deduplicated intent/vector together. Missing destination retains intent.
  No provider call inside a SQL transaction. No opposite lock order in participating writers.
- Retry/lost acknowledgement finds the existing selection/intent. Build failures retain accepted
  input and resume exact sealed revisions; restart must not guess counterparts or select MAX.
  Concurrent completed periods preserve each other's vector membership.

## 7. Helpers and refactor review

Reuse accepted calculation/window resolution, semantic digest, immutable publication builders,
DAL transaction and config/recovery helpers. Inspect existing helpers before adding utilities.
Replace only incompatible latest-input/routing-first checks in the manifested paths; avoid
parallel helpers with the same responsibility. Identify stale caller bypasses in the initial
scope. No command/view SQL refactor is selected. Export pacing/worker/pool concerns stay S10.
Capture unrelated debt in the required deferred format; never defer a required S8B invariant.

## 8. Validation plan and evidence boundary

Run the exact-path test selector and risk-based focused tests. Cover S7-T01, T03–T08's
service/DAL portions: same/opposing-source admission; missing/disabled source; both pair
orders; wrong source/KVK/period/revision/config/roster/coverage; semantic duplicates;
confirmed/stale counterpart; B0/no-fight/overall; failed second side; exact endpoint chain;
stale CAS; atomic pointer+intent/vector; acknowledgement loss and restart.
S8C UI and S9 public-reader acceptance remain separately owned.

Run all seven test files in the manifest, plus affected calculation/window/digest regressions
selected from the approved matrix. Existing regression paths may be run without expanding
the edit manifest. Run architecture, deferred and security-routing validators, lint/type hooks,
smoke imports, and justify command-registration/full-suite decisions from actual changed scope.
Before broad integration handoff run full tests through scripts/analyse_pytest_log_noise.py;
record counts/skips and unchanged operational logs. Never claim a historical pass as fresh.

Use mocks/synthetic fixtures for development. Prepare an exact proposed disposable plan for
same/opposing-choice races, two builders/config races, deadlock ordering, simultaneous vector
membership, rollback and lost commit acknowledgement using two real connections. Stop for
separate approval of actual server/database, backup, row preview, script hashes and operations.
Mocks do not close SQL transaction/concurrency gates. New S8A runner execution is also separately
gated; its earlier offline pass is not an SQL execution result. Never use retained predecessor
DBs as default targets, invent real allowlist rows, or delete retained data.

## 9. Skills and security routing

Use k98-architecture-scope before implementation, k98-sql-validation for authoritative schema,
k98-test-selection for focused/runtime gates, k98-pr-review for the completed diff, and
k98-security-review-routing before the security workflow. k98-discord-command-feature is not
applicable to this service/DAL slice. k98-deferred-optimisation-capture applies only to actual
out-of-scope debt; k98-promotion-check applies only after separate promotion authorization.

Preparation: documented skip for the exact Markdown-only Bot closeout and SQL delivery-log
append, with no executable/config/permission/data-access/persistence change.
S8B implementation: use $codex-security:security-diff-scan at the exact Bot base/head or immutable
working patch because admission, SQL access and restart-sensitive transactions change.
Confirm **Scan type: Changes; Deep off** and record target/scan ID, manifest/findings/coverage
and findings disposition. Review later security-relevant fixes at their exact delta. SQL has
its own target if changed. No standard/deep scan or automatic new task is authorized.

## 10. Handoff and approval checkpoints

Initial new-chat response: inspect current state, validate the 20-file manifest/schema and
caller/lock-order risks, select tests, identify concrete blockers and request only S8B scope
approval that has not yet been given. Do not ask again for S7 product decisions.
After implementation approval: author, validate and review the bounded diff; retain an exact
proposed disposable execution plan and stop at the separate operations/PR gates.
S1–S6 acceptance, S6-OPS01/PERF01/CAP01, both uncertain publications and all retained evidence
remain intact. SourceRouting.Enabled is not public routing. No bot-machine action is authorized.


## S8B implementation review — 2026-09-13

The operator approved the scoped Bot implementation in this task. The working tree contains
all 20 approved source/test files plus the exact 31 documentation carry-forward paths.
Both sides of all four archive moves remain present as deletion/destination pairs. No path
is claimed already merged as an exemption. GitHub filename/previous_filename verification
belongs to the eventual separately authorized PR; no S8B PR exists yet.

Implemented foundation: fixed audited source choice and lifecycle CAS; both importer guards;
explicit, immutable matched input associations and counterpart attestation; exact endpoint
resume from retained request authority; sealed candidate building; complete-selection CAS;
atomic action/request/pointer/full-vector intent commit; exact immutable replay readback;
restart discovery of explicit updates; no automatic provider delivery. Window-label-only
configuration changes require admin authority and identical input/calculation context.
SourceRouting.Enabled alone still does not implement S9 public routing.

Validation on the reviewed implementation: focused seven files 87 passed / 37 skipped;
full `scripts/analyse_pytest_log_noise.py` 4,127 passed / 44 skipped, all four operational
logs unchanged. All skips are retained opt-in/environment gates, including no SQL execution.
Architecture checked 20 Python files; deferred validator checked 27 Markdown files; routing
validator zero errors/warnings; smoke imports and command registration passed (36 primary,
101 grouped subcommands, zero duplicate drift). Exact-path selector requested full tests,
smoke and registration. Ruff passed. Black 26.3.1's CLI stalled; direct formatting API with
fast=False and the repository's line length/target verified all 20 files without changes.
Configured Pyright scope passed with zero errors and five existing dependency-resolution
warnings; this is not a claim of strict typing across KVK. No pre-commit staging or staged
secret check was performed because the index must remain untouched.

The initial immutable Changes scan ed2f7db0-ef7f-4485-80de-7844b760682d completed with
zero reportable security findings across all 13 changed source files; tests/docs were also
reviewed. Snapshot digest: 9edbafd56040e05db031dfb1125665368bd8d54585ea052d517184f7d23ccb71.
That scan is not a functional merge certification. Subsequent functional review fixed
sealed pairs being starved by newer unmatched revisions, and now requires exact durable
BaseUpdateID against the current complete selection for every nonduplicate successor.
Association still checks current revisions; sealed publication verifies immutable facts,
configuration and base CAS without requiring a latest input pointer. Complete commit
acknowledgement-loss replay is covered by an added in-memory transaction case.
The follow-up delta changes only source_update_dal.py, new_source_recovery_dal.py and
its manifested source-pair tests; SHA256 c0bcf8132a58a42df62dc2372fc8ace6fc498d438b92fd34084092005fcb6786.
Final target security/test evidence is recorded with the task handoff; do not use the initial
scan as proof of later source bytes. No production exposure is inferred from service flags.

### Open implementation/schema gate

S8A `KVK.SourceUpdate` binds UpdateKind to the SourcePeriod PeriodKind by FK_SourceUpdate_Kind;
CK_SourceUpdate_State requires an aggregate for every ready fight update. SourcePeriod's kind
check requires `fight:*` for fight and `no_fight:*` for no_fight. Consequently an existing
fight period whose configured endpoints are equal cannot select the approved zero-score
exception without an aggregate. Dedicated typed no_fight periods work. Do not fabricate a
report, retag an existing period, alter immutable configuration/history or silently drop this
S7 requirement. An exact separately approved SQL amendment is required to express the
no-fight update exception in an existing fight period. S8B must not be declared complete or
merge-ready until that compatibility issue is resolved. SQL source was inspected at
50310950a1adb7425e6db6bc86f38bdeb38e0830; no SQL files were modified by this implementation.

A proposed separate SQL implementation manifest is: Create
`migrations/20260913_001_kvk_source_update_no_fight_context.sql`; Modify
`sql_schema/KVK.SourceUpdate.Table.sql`, `migrations/README.md` and
`docs/SQL_DELIVERY_LOG.md`. These paths are a proposal only and have not been created/edited.
The amendment must separate immutable period classification from an explicitly confirmed
no-fight update mode, preserve existing scoped period/config/revision FKs, require equal
player endpoints and no aggregate for the exception, and reject wrong-kind overall/fight
reports. Migration preview must enumerate affected rows and constraint changes; no rewrite
of retained publication/update meaning or period identities. Its exact definition, static
checks and disposable validation need independent SQL review before implementation.
The Bot adaptation then remains in source_update_dal.py and test_kvk_source_pairs.py / SQL
integration test paths already authorized. This addresses schema expressiveness, not a new
S7 product decision. The current Bot correctly fails closed instead of bypassing SQL.

### Proposed disposable SQL validation operations — NOT EXECUTED

No actual server/database, backup receipt or execution has been approved in this task.
The test harness refuses all connections unless KVK_S8B_SQL_ENABLE=1 and an explicit
KVK_S8B_SQL_SERVER / KVK_S8B_SQL_DATABASE pair exactly matches
KVK_S8B_SQL_APPROVED_TARGET=`server|database`. Database must have the fresh S8B disposable
prefix, and runtime server/database identity is rechecked. S3B/S5B variables cannot enable
this harness. Never use any retained predecessor database as a default target.

1. Review the separate schema amendment first. Before connection approval, name the exact
   local instance and fresh disposable database, database creation/provisioning method,
   synthetic-only provenance, backup/restore receipt, expected empty KVK scope preview,
   all schema/test input hashes and precise operations. The fixture assumes the accepted
   observation/publication/S8A schema already exists. It does not deploy migrations. Do not
   rerun the S8A runner or predecessors under approval of a Bot test command.
2. With that separate approval, verify server identity, database identity, compatibility,
   trusted constraints and empty/isolated synthetic scopes using reviewed read-only queries.
   Fail closed on real history or unexpected rows. Save metadata/count evidence and hashes.
3. Run only the approved test node IDs in tests/test_kvk_source_sql_integration.py. New
   ready-to-run nodes cover same/opposing source races using two connections, competing
   builders/replay producing one complete selection/intent, and interruption before intent
   or vector write with complete transaction rollback and subsequent exact retry.
4. Review these deterministic two-connection schedules before the remaining S7-T08 runs:
   A/B different periods: seal both against their own prior complete bases, build both,
   synchronize before selection; release A then B and reverse the order in a fresh scope.
   Expect one intent per successful selection, second vector contains both exact publications,
   and every unchanged member retains update/config/publication/public-version identity.
   Config race: build A under config N; B persists exact N→N+1 endpoint request and commits;
   release A selection and expect stale desired-config/CAS with zero pointer/intent mutation.
   Lock-order case: A pauses after season lock; B starts the other-period/config writer;
   release A within the 10-second app-lock timeout. Repeat reversed writers; record observed
   order and bounded wait. A deliberate held-lock timeout must leave zero partial writes.
   Commit-loss case: build beforehand; fault only the selecting connection immediately before
   commit (expect no selection/intent), then after underlying commit but before acknowledgement
   (expect exactly one retained selection/intent). Fresh service must return the same IDs.
   These are explicit proposed schedules, not executed tests or new predecessor permission.
   They require approved fixture additions in the existing SQL integration test path and fresh
   hashes before execution. In-memory and older private-publication cases do not close them.
5. Capture each synthetic season/update/publication/intent ID, complete vector membership,
   before/after row counts, states, hashes and transaction outcome. Retain committed test
   evidence and artifact directories; no cleanup/drop/truncate or provider calls. Stop on
   ambiguity and inspect durable results before any retry.

The existing S8B SQL fixture file is the executable test input; rehash immediately before
any separately approved run. Provisioning and the additional deterministic SQL schedules
are not yet an approved execution pack. This proposal is not authorization to connect.

### Retained operational and Git gates

Bot HEAD/origin/main 4f3bfadeb03258b1f0ddf28201862ba7afbc7a10 and production/main
 aa08f54cd67e0db89a2e64eedc6f79a57e098a29 remain comparison anchors. SQL HEAD/origin/main
50310950a1adb7425e6db6bc86f38bdeb38e0830 remains unchanged; its 33-line
`docs/SQL_DELIVERY_LOG.md` append is separate SQL PR carry-forward, never Bot PR content.
No Git stage/commit/push/PR/merge/pull/fetch/reset, SQL connection/execution, real import/export,
provider/Discord write, restart/deployment/activation or bot-machine action occurred.
Operator smoke acceptance, six-script disposable S8A evidence and the offline-only runner
fix remain distinct; no fresh post-merge SQL run is claimed. S6-OPS01/PERF01/CAP01, both
uncertain publications and retained databases/files remain open/preserved.

SQL integration test SHA256 at handoff: `448cc1971615e5229100b6a4e368e33fefb857dd7823b5a5c80c67a4eae96be3`.

### Final source validation and review evidence

Final unchanged source target: Bot working tree versus
`4f3bfadeb03258b1f0ddf28201862ba7afbc7a10`, scan snapshot
`36f1da471920c42c7c155f513fad9f6805977a5f00fabd0ac4c3da396cfa81ac`.
Changes scan `699f4dee-c828-434e-9249-336c7f69cfca` completed and sealed with zero
reportable security findings. Deep was off. The prior full review's unchanged source-text
coverage plus the exact follow-up delta were verified; two retained baseline comparisons
normalize line endings, so no historical raw-byte identity claim is made for those two.
Canonical report directory: `%LOCALAPPDATA%/Temp/codex-security-scans-eb54AK/discord_file_downloader/4f3bfadeb03258b1f0ddf28201862ba7afbc7a10_20260913T075742Z_1o6y8g_7/`.
Report, findings, coverage, manifest and SARIF remain retained there. The scan's reported
usage was 1,503,641 tokens including 1,481,984 cached-input tokens; this is tool accounting,
not a billing estimate. The final scan goal reports 37,728 tokens over 154 seconds.

Final full `analyse_pytest_log_noise.py`: **4,131 passed, 44 skipped**, 141.17 seconds;
production logs unchanged. Final exact seven-file run: **91 passed, 37 skipped**.
Architecture/deferred/routing checks passed again; 397 relative documentation link targets
resolve and exact 51-path union matches the working tree. Ruff and Black API checks passed.
Pyright with explicit `.venv/Scripts/python.exe` passed with **zero errors and warnings**
within the configured scope, resolving the earlier interpreter-selection warnings.
Smoke imports and command registration passed before the final two-DAL change; the final
full suite covered that delta. No additional runtime or external operations were performed.

The final evidence paragraph added after scan sealing is a documentation-only delta in this
same manifested task pack. Security routing: documented skip for that evidence append only;
no runtime, authority, configuration, SQL execution, dependency or deployment behavior changes.
The source bytes remain the reviewed target. The equal-endpoint fight/no-fight SQL mismatch
and unexecuted SQL concurrency scenarios remain blocking integration evidence, not deferred
optimisation. **Review verdict: do not merge yet.** No unrelated deferred refactor was added.


## Approved gap closure — 2026-09-13

The operator instructed this task to close the recorded gaps and add the required functionality.
This approves the previously proposed four-path SQL source amendment and Bot adaptation; it does
not authorize SQL connections/execution, provider/Discord operations, Git publication or deployment.
Earlier statements that the amendment is only proposed describe the previous checkpoint.

The schema expressiveness gap is now addressed in authored source. `KVK.SourceUpdate.PeriodKind`
is copied from the existing immutable scoped period and becomes the kind FK column. `UpdateKind`
may equal it, or be `no_fight` within a `fight` period; all other cross-kind modes reject. The DAL
derives classification from SQL, requires explicitly confirmed equal configured endpoints, equal
player scan/revision endpoints and no aggregate. No period is retagged; every original update CHECK
and other scoped FK remains unchanged. Existing update IDs, hashes, confirmations, inputs, state,
selections and intents are preserved. PeriodKind is functionally determined by PeriodID and does
not change the semantic hash contract. Public routing and provider execution remain S9/S10 work.

Bot follow-up edits remain exactly `kvk/dal/source_update_dal.py`, `tests/test_kvk_source_pairs.py`
and `tests/test_kvk_source_sql_integration.py`, within the approved 20 source/test paths. The full
31-path documentation carry-forward and all four archive origin/destination pairs remain required.
The eventual Bot PR must include all 51 physical paths or provide exact merged filename and
previous_filename proof. No path exemption or provider verification is claimed here.

Separate SQL delivery, never included in Bot PR:

- Create `migrations/20260913_001_kvk_source_update_no_fight_context.sql`.
- Modify `sql_schema/KVK.SourceUpdate.Table.sql`.
- Modify `migrations/README.md`.
- Modify `docs/SQL_DELIVERY_LOG.md`, preserving the pre-existing S8A closeout append.

Migration SHA256: `aa66a2015e089a7df9ae5cdb6e4d89f96e3d0cfacfa119ba9ca7d39dcf8ac807`.
Snapshot SHA256: `bdf354f1c78fb113c04b22d073a0ee5fd6771d41e79f31ec1d5cb8ec5cad432a`.
Migration preview takes bounded installer/table locks, returns scoped row and constraint inventory,
and rolls back without DDL. Apply checks target/evidence/expected row count, backfills only the new
classification column, and changes the kind FK plus new mode CHECK atomically. Rerun verifies the
column, exact mode expression and ordered scoped FK rather than rewriting data. Application uses a
fresh dedicated session with all source writers idle. Apply SQL before the revised Bot writer;
older SourceUpdate inserts omit the new required column and fail closed. Forward fixes only after
retaining fight-period no-fight updates. The generic pending runner does not supply the required
input table: no runner or migration-history edits are implied, and no predecessor rerun is approved.

### Added disposable schedules, authored but not executed

The earlier schedule-only gaps now have concrete gated test nodes in the existing SQL integration
file. All use fresh synthetic seasons, retained artifacts and no provider calls:

- `test_s8b_no_fight_in_existing_fight_period_selects_zero_members_and_replays`.
- `test_s8b_sql_rejects_invalid_no_fight_shape` (classification, mode, unequal inputs, aggregate).
- `test_s8b_simultaneous_periods_preserve_complete_vector` (both writer orders).
- `test_s8b_config_change_rejects_prebuilt_candidate_without_partial_selection`.
- `test_s8b_config_and_other_period_selection_share_lock_order` (both writer orders).
- `test_s8b_season_lock_timeout_leaves_no_partial_selection`.
- `test_s8b_complete_commit_loss_fresh_client_readback` (before/after underlying COMMIT).

The two-connection schedules build candidates first, gate the first writer after its season lock,
observe the other entering the same lock, then release. Both-period success must preserve exact
update/config/publication/public-version membership. A persisted desired-config change invalidates
the old candidate with no pointer/action/intent writes. Deliberate lock timeout rolls back all public
writes; retry selects once. Fresh clients distinguish before-COMMIT rollback from lost acknowledgement
after COMMIT and reuse the durable intent. Earlier same/opposing-choice, competing-builder and
statement-boundary rollback nodes remain. These are test implementations, not claimed SQL results.

The existing harness still requires KVK_S8B_SQL_ENABLE=1 and an exact explicitly approved server,
new S8B disposable database and matching KVK_S8B_SQL_APPROVED_TARGET; runtime identity is rechecked.
No default, retained predecessor target, actual backup receipt or provisioning permission was added.
The next operational approval must bind exact server/database, provisioned prerequisite schema,
synthetic-only provenance, backup/restore receipt, expected update-row preview, source/test hashes
and node IDs. The new migration additionally requires one #S8BNoFightApproval row with exact target,
BackupEvidence, PreviewEvidence, ExpectedUpdateRows and preview/apply mode. Migration preview/apply,
verified rerun, rollback on count/catalog mismatch, and original-row identity/hash preservation must
be exercised before the Bot nodes. No SQL compiler/constraint/concurrency pass is inferred from mocks.
The actual database creation/bootstrap/backup commands remain a separate reviewed operations packet;
this source implementation does not authorize any command in the earlier predecessor runners.

### Fresh offline validation

Seven manifested test files: **99 passed / 50 skipped**. Full log-noise rerun: **4,139 passed /
57 skipped in 138.79 seconds**, all operational logs unchanged. The first full attempt recorded
4,138 passed / 57 skipped and one unrelated Windows WinError 5 during atomic JSON replacement in
`test_commit_observation_does_not_change_lifetime_contract[None]`; its targeted three variants
passed on rerun. That code was not changed. Both outcomes remain evidence, not silently discarded.

Architecture checked all 20 Python paths. Smoke imports and registration passed (36 primary,
101 grouped, no duplicate/drift). Ruff passed; direct Black API verified the three follow-up Python
files with the repository format settings. Configured Pyright scope: zero errors/warnings.
Exact-path test selector requested full tests/smoke/registration, all completed. SQL repo validator
passed on an isolated source copy in the local Temp directory, with 15 warnings confined to older
migrations and none for this amendment; operational SQL repo logs were not touched. SQLFluff T-SQL
parsing passed the migration, both constant dynamic batches and snapshot. Static comparison confirms
all original CHECKs and all scoped FKs other than the deliberately rebound kind FK remain identical.
No live SQL parsing/compilation, constraint execution, lock timing or migration test is claimed.

Security routing: two exact working-tree Changes reviews, Deep off; Bot at 4f3bfadeb03258b1f0ddf28201862ba7afbc7a10
and SQL at 50310950a1adb7425e6db6bc86f38bdeb38e0830. New evidence follows below when sealed.
The prior final Bot review's 12 other source files and five other tests match the retained raw-byte
hashes; the three follow-up paths were reviewed anew with their callers and authoritative schema.
No unrelated refactor was selected. Reused transaction/CAS, configuration, calculation, publication
and commit-fault helpers; additional synchronization helpers are synthetic test fixtures only.

**Do not mark S8B merge-ready yet:** implementation/source compatibility is addressed, but migration
execution and real SQL transaction/concurrency acceptance remain required. S6-OPS01/PERF01/CAP01,
both uncertain publications, all retained databases/files and the distinct operator-smoke/six-script/
offline-runner evidence remain intact. No new post-merge SQL run or bot-machine change is claimed.


### Sealed gap-closure review evidence

Both Changes reviews completed with Deep off, zero findings and complete source coverage:

- Bot `62a6d306-fc1d-4d6c-9028-94c8fd58bc5e`, sealed 2026-09-13 08:32:52 UTC;
  snapshot `67e9266e21c5cce11c951dcd92cc95181a5d0f1369b2e90f3d8ddff48c56b2da`.
- SQL `ebf9cb6a-f2a8-4399-9879-ec1d5b67458b`, sealed 2026-09-13 08:33:04 UTC;
  snapshot `49a1bcb632ba32c6aa3032b986e3b23c57621478c8e5f7bba62d710d944b2816`.

Canonical findings, coverage, threat models and reports were retained and completed documents
read back. Inventory: 13 Bot source files and two SQL source files; tests and documentation also
reviewed. Independent architecture review found no security candidates. Daybreak advisory:
status granted, Daybreak Blue, for both scans. Capability preflights passed without config edits.
The goal tracked 113,852 tokens and 394 seconds. Tool rollout accounting reports Bot 4,398,645
and SQL 4,580,370 total tokens (4,255,616 and 4,436,736 cached respectively); these overlapping
shared-task counters must not be summed or described as billable usage.

Documentation-only status/evidence additions after the captured snapshots have a precise security
skip: five existing manifested Bot Markdown paths and the separate SQL delivery-log evidence
append change no executable, configuration, permissions, input, data-access or persistence logic.
All executable source/test bytes remain those reviewed. Final architecture/deferred/routing,
formatter and manifest checks passed: Bot exact 51 paths (20 source/test +31 documentation),
SQL exact four paths, both indexes empty, repository anchors unchanged. The retained S6 benchmark
hash remains 3587bbafc0bc145744c79ff03cb51e119915ad373ec3dd428385051880615e7b.
No Git operation changed repository refs/index and no connection or external operation ran.

Review verdict: **Do not merge yet**, solely pending the approved-contract real SQL migration and
transaction/concurrency evidence plus separately authorized publication gates. This source work
resolves the previously identified equal-endpoint schema incompatibility; it does not claim the
migration has been applied. No S7 decision needs reapproval.


### Exact disposable packet prepared — 2026-09-13

After the operator said "approved please proceed", preparation advanced to the previously
unspecified actual target/provisioning/backup packet. No SQL connection or execution has occurred.
The original exact-target requirement cannot be satisfied by an unnamed database approval.
Proposed target: `9SX2VF4\K98DEV` / `K98_S8B_Disposable_20260913_validation`, plus
new restore-proof database `K98_S8B_Disposable_20260913_validation_restore`. The concrete
packet is retained at `C:/Users/cwatt/AppData/Local/Temp/k98-s8b-execution-dzmmcw49` (`README.md`, `manifest.json`,
`run_validation.py`, baseline snapshot/bootstrap/seed/amendment SQL and offline parser evidence).
Manifest SHA256 `ab149d5622661a059736b149d9a03500f91f26f8ef75bc09efaff32f1beaedbb`. It requests new-only schema fixture provisioning, three synthetic
retention-probe updates, exact COPY_ONLY/CHECKSUM backup and actual restore to the second new DB,
wrong-target/count rejection, preview/apply/rerun with original-row digest preservation, and all
50 SQL integration test cases. Both names and all new files must be absent; failures preserve
evidence and never resume/overwrite automatically. No predecessor runner or retained DB is used.

Operator confirmation of these exact names/backup/restore operations remains the final boundary
because the earlier handoff did not specify them. This does not re-request S7 or implementation
approval. No production/provider/Git/Discord/restart/deployment/activation permission is implied.


## Approved disposable execution results — 2026-09-13

The operator explicitly approved the exact packet and both database names. Execution and related
synthetic fixture corrections are complete. This section supersedes the earlier unexecuted SQL
status; it does not alter historical S7/S8A acceptance or authorize further operations.

Target: `9SX2VF4\K98DEV`, Windows integrated local shared-memory connection. Created
`K98_S8B_Disposable_20260913_validation`; actual backup restore created
`K98_S8B_Disposable_20260913_validation_restore`. Both are retained, together with the backup,
restored files, all synthetic seasons/artifacts and every failed/successful receipt.

Evidence root: `C:/Users/cwatt/AppData/Local/Temp/k98-s8b-execution-dzmmcw49`.
Original manifest SHA256: `ab149d5622661a059736b149d9a03500f91f26f8ef75bc09efaff32f1beaedbb`.
Reviewed continuation: `reviewed-continuation-01`, manifest SHA256
`227d69ca50840654b250e39804974141222bc923c20a08ea71343b24c0f6d0ad`.
Original packet files and manifests remain unchanged as historical proposed artifacts. See the
continuation execution receipt and `execution-summary.md` for the actual outcomes.

- Initial sandbox connection failed before SQL execution. The approved Windows-auth retry created
  the new target, then bootstrap rolled back because the roster eligibility unique key appeared
  after its referencing FK. Readback verified zero tables and no KVK schema. The reviewed
  continuation moved that existing key before the dependent table, verified the target was still
  empty, and proceeded without deleting/recreating any database or replacing original evidence.
- Thirty authoritative baseline tables and deferred FKs were provisioned; entirely synthetic
  baseline probes included three SourceUpdates. COPY_ONLY/CHECKSUM backup, RESTORE VERIFYONLY
  and an actual restore to the second new database passed. All thirty original table column,
  count and content digests matched the restored baseline.
- Wrong target and wrong expected count rejected without changes. Migration preview made no
  DDL/data change. Apply and a fresh-session rerun passed, preserving every original-column row
  count/content digest; only the added PeriodKind column is outside that original projection.
- Initial SQL suite: **30 passed / 20 failed**. Four delivery fixtures lacked required owner/state
  timestamps. Sixteen matched fixtures failed on conflicting synthetic coverage confirmation.
  Fixtures now use coherent parameterized delivery state, matching confirmation/candidate UTC
  coverage, a valid numeric aggregate token, and no aggregate preparation for no-fight updates.
  Production validation was not relaxed. Focused rerun: **22 passed / 28 deselected**.
- Final complete SQL suite: **50 passed in 25.09 seconds**, including both writer orders,
  complete-vector atomicity, desired-config races, lock timeout, no-fight SQL checks and both
  commit-acknowledgement-loss cases. Retained files: `pytest-final-01.txt`, `.xml`, `.json`.
  Test SHA256: `55e4ff31078e5e3c2281e5709dc9c4ee3492cd79f618c6f7576d0c35a61e5173`.
- Final offline suite with all SQL opt-ins removed: **4,139 passed / 57 skipped in 184.73 seconds**;
  all four operational log hashes unchanged (`offline-final-01.txt` and `.json`). Architecture
  checked all twenty paths; deferred/routing, smoke imports and registration passed. Ruff and
  direct Black checks passed for the final fixture change. Earlier full-source lint/type and
  SQL static checks remain applicable because nineteen source/test files and both SQL source
  files are unchanged; the one subsequent source delta was independently reviewed.

Final Bot Changes review `65cd02c7-32ec-47dc-ae4f-f054a79246d7`, Deep off, completed and read back
at 09:09:12 UTC: zero findings, complete coverage. Snapshot digest
`4f7bf100d52b73b9262b8d620438038bff9924009de47f8d83937db6b161f67f`.
It retains prior reviewed source evidence only for byte-identical files and independently reviews
both fixture changes and the exact target guard. Daybreak status granted, Daybreak Blue. Review
goal accounting: 43,944 tokens, 154 seconds (task accounting, not a billing estimate).
The separate SQL Changes review `ebf9cb6a-f2a8-4399-9879-ec1d5b67458b` still matches both executable
SQL source hashes; this delivery-log evidence append has a documentation-only security skip.
Final Markdown status/evidence edits in these five manifested Bot documents also have a precise
skip: no executable, configuration, permission, input, data-access or persistence effect.

The SQL compatibility and disposable transaction/concurrency evidence gaps are closed. Results
are ready for operator acceptance and separately authorized publication review. This is fresh
bounded S8B disposable validation, not a fresh S7/S8A post-merge smoke or production run. Historical
operator smoke acceptance, six-script evidence and the offline-only runner fix remain distinct.
No bot-machine action, provider write, real import/export, Discord operation, deployment,
activation, predecessor operation, cleanup or Git mutation occurred.

Future delivery must preserve exactly twenty Bot source/test plus thirty-one documentation
physical paths, including both sides of all four archive moves, and verify actual PR `filename`
and `previous_filename` or specific merged-path proof. The separate four-file SQL delivery,
including its full delivery-log carry-forward, must precede Bot with source writers idle.
Publication/merge/deployment remain unauthorized. S8C/S9/S10 are not implemented; full-vector
export intent remains waiting_destination and SourceRouting.Enabled alone is not public routing.
S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files remain intact.


## Operator acceptance and publication approval — 2026-09-13

The operator accepted the completed S8B implementation, gap closure and disposable validation,
and explicitly approved publication. Publish separate Bot mirror and SQL PRs with the exact
51-path Bot and four-path SQL manifests. This supersedes earlier pending acceptance/publication
wording; it does not authorize merge, production promotion, deployment, activation or new runtime
operations. Preserve all earlier evidence and verify actual PR filename plus previous_filename
for every path, including the four archive origin/destination pairs. SQL delivery-log carry-forward
remains exclusively in the SQL PR. Source/test bytes are unchanged from accepted validation and
final Changes reviews; these acceptance/status edits have a documentation-only security skip.


## PR review actions — Bot #274 and SQL #81

The operator authorized checking, fixing, publishing, replying to and resolving actionable review
comments. The Bot P2 duplicate-identity finding was confirmed: complete semantic duplicates and
unchanged display-configuration requests now persist their exact attached inputs/hash with
UpdateState=superseded and a CAS version increment before returning the prior result. Original
identity reads expose the terminal state, recovery excludes it, and no new publication/intent is
created. Confirmation/base provenance and the existing SQL shape checks are preserved. Failed
finalization rolls back without losing the original waiting identity.

The SQL P1 deployment-runner finding was confirmed. A hash-checked exact-target/exact-migration
S8B input path supplies #S8BNoFightApproval on the migration connection and rejects preview mode
before execution. The existing runner records Applied only after success and Failed on rejection.
A shared session executor retains the S8A wrapper/guard. Offline tests exercise actual runner
parameter gates, pending guard and application/history loop with fake connections and history.
No new live SQL or predecessor operation was run for this review fix.

Bot delivery remains exactly 20 source/test plus31 documentation physical paths. The SQL delivery
is explicitly extended for this requested fix from four to six paths, adding
Deploy-SqlMigration.ps1 and Test-S8AMigrationInputs.ps1 under deploy. All original SQL paths,
including the complete delivery-log carry-forward, remain exclusively in SQL PR #81.
Historical accepted 50-case SQL evidence remains valid for its recorded source hash; it is not
claimed as execution of these later review fixes. Fresh focused/offline/security evidence follows.


PR-fix validation: 48 focused pair tests passed; full offline suite **4,149 passed /57 skipped
in147.77 seconds**, four operational logs unchanged. Architecture, deferred, routing, smoke,
registration and Ruff passed. SQL S8A/S8B offline runner regressions passed with mock connections.
Separate Changes reviews, Deep off, sealed and read back with zero findings and complete coverage:
Bot ef9cf7e4-f388-4e8b-9f64-dfaba85f13b1 (09:54:50 UTC), SQL
33e0bcba-9127-45a8-95d5-b2fa26e048f2 (09:55:32 UTC). The SQL draft's initial uppercase coverage-ID
format error was corrected within the same scan; no review source or finding was changed.
Final evidence/status-only Markdown changes have a documented security skip. The shared-session
SQL runner path is offline-validated only; no new SQL execution or production deployment occurred.
