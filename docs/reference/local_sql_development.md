# Local SQL development environment
## S11 complete application readiness authoring — 2026-09-24

services/export_execution_dal.py now authors 14 read-only metadata batches covering application
objects/columns/indexes/checks/FKs/triggers, UDTs, dependencies, synonyms, database triggers and
effective schema/object/column permissions. ScriptDom parsed all 14 with zero errors; none ran
against SQL Server. Both startup and each actual producer cursor compare independently reviewed
expected hashes. Existing producer transaction ownership is preserved.

application_sql_contract version 1 requires server, database, principal, sources, dynamic_objects,
metadata_hash, permissions_hash and review_id. Canonical sources pins all 538 current sql_schema
files (382 tables, 96 procedures, 49 views, nine functions and two UDTs), sorted by path, as
name/type/path/sha256 records. Its canonical digest is
0fcc6360f17cc6017801b074117b6b7d6fb8ebb0bd808d686971511b350a27d2.
The exact generated source inventory is retained in the local composition artifact directory;
recompute against the SQL authority and compare the runtime constant when preparing G4.
Dynamic object entries must name a bounded dbo/KVK object, U/V type and reviewed producer modules.
They require exact metadata shape review, not a wildcard or inferred permission. The complete
metadata response is bounded to 16 MiB. Historical constraint/trigger dispositions remain pinned
rather than requiring unrelated repairs; opaque modules or changed shapes still refuse readiness.

The source-file hash is an authoring anchor, not an installation certificate. G4 must independently
compare source, real installed definitions/dependencies/dynamic output shapes and effective
permissions before writing approved expected hashes. Missing historical source objects or larger
metadata on the actual target are real G4 compatibility questions, not permission to auto-create
objects, loosen the contract or accept observations as their own expected values. No SQL repository
bytes changed for this Bot metadata/readiness continuation. The corrected SQL Changes result and
pending SQL closeouts remain separate from the final Bot runtime review.


## S11 legacy permission fixture boundary — authored 2026-09-24

The approved source-only permission delivery adds migration 20260924_002 after the S11 evidence
migration. It leaves all business modules unchanged. The SQL manifest pins exact source bodies,
three root signing groups and their required child countersignatures. Public-only certificates,
exported exact signature blobs and protected deployment inputs are separate G4 prerequisites;
no local test here generates keys, enables xp_cmdshell, creates its proxy or installs grants.

Current legacy source explicitly names ROK_TRACKER and relies on dbo resolution. Its new disabled
fixture therefore needs a separate, explicitly named K98_S11_Disposable_ SQL instance with database
ROK_TRACKER. It cannot reuse the ordinary S11 evidence fixture simply by renaming that database.
The operator must approve actual backup/restore evidence, the restricted real login and exact
readiness/denial/configuration-fallback operations. The fallback case requires precisely one
synthetic ProcConfig_Staging row: KVK_NO 2147483000, all nine remaining columns NULL. It writes a
different synthetic KVK_NO inside the caller's transaction and rolls it back under both XACT_ABORT
settings. No upsert, root import, export, provider or predecessor scenario is invoked.

These tests are authored, not executed. A failed or doomed fallback is a real compatibility issue
to reconcile before admission; it is not permission to grant the Bot schema ALTER or retry an
uncertain import. The separate actual root/nested/bulk/proxy and output-shape cases remain G4 work.
Source parsing and mocked metadata tests do not replace those observations.

## S11 implementation status — 2026-09-24

S11 additive evidence SQL source is authored separately under implementation approval. The offline checker passed 87 assertions and ScriptDom parsed 11 files; no SQL connection, installation or transaction fixture ran. The guarded new disposable-target fixture remains opt-in and is not a predecessor rerun. See [checkpoint](kvk_source_migration/release_evidence_log.md#s11-approved-implementation-checkpoint--2026-09-24).


## S11 evidence-ledger design amendment — 2026-09-24

The mechanism design now establishes a proposed additive SQL requirement: execution sessions,
streams, immutable provider requests, append-only request events and reconciliation proofs, with
four narrowly permissioned transition/issuance procedures. Existing aggregate request-budget and
attempt/preparation records do not provide that independent request evidence. This supersedes the
earlier no-established-SQL-requirement checkpoint; there is still no authored SQL delta.

Use the [exact SQL paths and table contracts](kvk_source_migration/integration_implementation_manifests.md#s11-proof-mechanism-manifest-amendment--2026-09-24).
Resolve physical types, bounds, keys, lock order, indexes and effective permissions against the
source-of-truth schema before dependent implementation. The reserved migration filename must be
re-resolved for the actual authoring date/available ordinal; never rename merged migrations.
Do not reconstruct historical request certainty or release existing claims during installation.

Static authoring can establish object and caller alignment. Only separately authorized disposable
SQL execution can establish transaction rollback, concurrent CAS, proof consumption/replay,
permission isolation and installation behavior. Provider finality and Windows process termination
need their own evidence. No database identity is assigned, no connection is opened and no previous
fixture is rerun in this design pass. S8A VERIFYONLY, S8B actual restore and offline history, S8C
local checks, and S10C/D/E static evidence remain distinct. Pending SQL closeout documents remain
untouched for the next actual authorized SQL implementation PR, separately from Bot delivery.


## S11 exact-target packet — 2026-09-24

S11 preparation/design is approved; **no SQL connection, service start, database creation,
fixture execution, migration, backup or restore is authorized**. The historical instance is
`9SX2VF4\K98DEV` (alias `localhost\K98DEV`), SQL Server 2022 Developer `16.0.1200.5`, compatibility
160 and development collation `Latin1_General_CI_AS`. These are dated observations, not current
verification. The authoritative repository remains `C:/K98-bot-SQL-Server` at
`2352a898881d4b74d6eec153bb3cb381d6162041`; it has two pending Markdown files and no new SQL delta.

### Exact installation dependencies and evidence

| Slice | Exact SQL-repository migration | Current evidence boundary |
|---|---|---|
| S10A | `migrations/20260914_001_shared_export_coordination.sql` | Accepted earlier disposable execution/actual restore; no new target installation inferred |
| S10C | `migrations/20260914_002_legacy_export_preparation.sql` | Authored/static; preparation/resource ownership must exist before composed writers |
| S10D | `migrations/20260915_001_kvk_output_pool_rollover.sql` | Authored/static; typed file/pool/slot/disposition identities and attempt references |
| S10E | `migrations/20260915_002_kvk_output_operation_ownership.sql` | Authored/static; operation/resource ownership, third mutually exclusive ExportResource owner |

S8 source/update/selection/intent prerequisites precede these. Compare actual catalog and migration
history before selecting installation work. Never rerun a predecessor to manufacture S11 evidence
or apply an older exact-shape guard blindly after a successor changed that shape. Standalone
`sql_schema` files are reference contracts, not an alternate installation procedure. Preserve
short schema transactions, lock bounds, trusted scoped FKs and receipt bytes; no data backfill,
registration seeding, grants or activation is implicit in schema installation.

### Proposed operation packet fields — all unresolved values block execution

| Field | Required exact value before G4-SQL |
|---|---|
| Server and authentication | Operator-approved instance and current SERVERPROPERTY identity; no default production connection |
| Primary disposable database | A new explicit name and confirmed absence; never an existing S6/S8 evidence database |
| Restore database | Another new explicit name, data/log file paths and confirmed absence; no WITH REPLACE over retained data |
| Engine/collation/compatibility | Current values, required contract and mismatch stop condition |
| Fixture/prerequisite plan | Exact source hashes, ordered objects and synthetic seed IDs; no real import or inferred historical classification |
| Installation plan | Exact missing migration hashes/commands and permitted lock budget, pre/post catalog assertions |
| Backup | Explicit new path, COPY_ONLY/CHECKSUM options as applicable, hash and readable backup metadata |
| Actual restore | Separate target, exact MOVE paths/commands, DBCC/catalog/row-content checks and expected results; VERIFYONLY alone insufficient |
| Transaction cases | Exact selected cases/operation IDs, connection/process count, interruption points, timeouts and expected retained states |
| Preservation | Before/after retained-row/receipt/claim evidence, database/file exclusion list and evidence output path |

Existing opt-in S10E tests require a name matching `K98_S10E_Disposable_YYYYMMDD_validation`,
the exact server/database, backup/restore evidence and distinct ready/CAS/contention/confirmation
IDs. No name or ID is allocated here; if a different S11 naming scheme is chosen, the test-gate
change needs explicit manifest approval. Authorization strings are safeguards, not approval.

Use `tests/test_kvk_export_sql_integration.py` in Bot and the separately selected SQL fixtures
`validation/kvk_source/s10c_legacy_export_preparation.sql`, `s10_output_pool_rollover.sql` and
`s10e_output_operation_ownership.sql` only after exact target/case authorization. Test independent
stale owner, fence and version with a positive control; job/preparation/operation contention;
closing replay/lost acknowledgments; and newly affected nested recovery. Mock results cannot
close transaction gates. Do not automatically execute an entire predecessor fixture pack.

All retained S1-S10 databases, backups, synthetic rows, originals and provider receipts are excluded
from new destructive/setup operations. S8A six scripts/VERIFYONLY, S8B 50 cases/actual restore and
later offline runner history stay separate. S10C/D/E installation is unproven. New backup/restore
evidence must name its source revision and actual target; no transitive installation claim.

Abort on target mismatch, partial/incompatible schema, untrusted constraints, unexpected populated
rows, unapproved locks or preservation differences. Leave evidence intact and propose forward
repair. No blanket reset, cleanup, retention deletion or implicit SQL PR. See the
[release approval packet](kvk_source_migration/release_readiness_and_rollback.md#s11-preparation-and-release-approval-packet--2026-09-24).

## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](kvk_source_migration/s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

## Historical S10A closeout status — 2026-09-14

S10A SQL #85 is merged and locally pulled at `3776dfa6b0892a8800d236fdf111c4d2f93c3813`.
All five disposable fixture modes, 76 unique cases in install and constraints, direct apply/rerun,
backup/actual restore and final preservation checks passed; final CI passed. Results accepted.
No changes have been pulled to the bot machine; no production SQL deployment or activation.
S9B mirror #277, production #584 and SQL #84 remain delivered. Bot comparison anchors are unchanged.

Next: **S10B Shared Export Coordination Worker and Durable Budget, initial review/scope only**.
Use the [S10B task pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md) and [starter](../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md).
The [S10A closeout and exact carry-forward manifest](kvk_source_migration/s10a_implementation_and_s10b_handoff.md) controls delivery.
Completed S10A and S9B packs/starters are archived; retained execution/operator evidence stays available.
Every pending Bot document and archive destination belongs in the eventual S10B implementation PR.
Check exact filename AND previous_filename, with explicit absent-at-base proof for never-committed
S10A source paths. No standalone documentation PR or repository mixing; grouping is settled.
Both mandatory SQL delivery documents were included and merged in SQL #85.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
S8B accepted smoke/50-case and actual-restore evidence remains distinct from offline runner history,
S8A six-script evidence and S8C seven local checks; S8C is not live Discord acceptance.
No S10B implementation, Git publication, runtime execution, deployment, activation or automatic new task
is authorized by this closeout. SourceRouting.Enabled alone never enables source activation.
Earlier dated checkpoints below are historical.


## Historical S8B closeout status — 2026-09-13

S8B is complete, operator accepted, successfully smoke tested and delivered through merged
production #581 and SQL #81. Local pulls are complete; **no changes have been pulled to the
bot machine**. Mirror #274 is closed without a merge record; its delivered content is verified
in synchronized mirror main. See the [canonical closeout and exact carry-forward manifest](kvk_source_migration/s8b_closeout_and_s8c_handoff.md)
for merge/content proof, final offline tests and the distinct historical disposable/runner evidence.
No fresh post-merge SQL or bot-machine smoke, deployment or activation is claimed.

**Next: S8C Intake and Admin Pairing UX in a new chat, initial review/scope only.**
Use the [S8C pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md) and [starter](../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md).
The eventual separately authorized S8C Bot PR must include all closeout documentation and both
sides of both S8B archive moves, checking actual filename and previous_filename; SQL delivery-log
carry-forward is separate. S7 decisions and predecessor acceptance remain settled. S9 public
routing and S10 export coordination remain later work; SourceRouting.Enabled alone is insufficient.
Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
Earlier dated scope/approval/next-slice statements are historical and do not reopen accepted work.

## Historical delivery — 2026-09-12 post-S6 closeout

**S6 evidence/rehearsal delivered, accepted and merged; feature activation remains blocked.**
Mirror [#272](https://github.com/cwatts6/K98-bot-mirror/pull/272) merged at
19:20:50 UTC as `016df1e61c8017556a7e8ba8374d31375aebfb74`; production-repository
[#579](https://github.com/cwatts6/k98-bot/pull/579) merged at 19:21:34 UTC as
`a8c9c515066ca6ef079120b76dd160e3389badab` (reviewed/final head
`b9c84751d3cc1deaba0a5772ab45d89263fcb398`). Mirror review fix `fa1f4733` records
the missing public routing consumer. Bot local main/origin main is
`a2f148fa9bd4fb367fd46d0500a768c14fee915b`; SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both were clean at this update's entry.

Operator reports merged and deployed locally, with nothing pushed to production.
GitHub confirms the production-repository merge above; **no production runtime or
bot-machine deployment, source activation, or fresh post-merge smoke is claimed**.
Local deployment is operator-attested; exact running process/config was not checked.

All preceding slices remain accepted. S6-OPS01/PERF01/CAP01 retain their open
operational components; accepted measured evidence is not pending reapproval.
The newly agreed requirements are fixed source per KVK for all affected outputs,
matched-pair public publication, confirmed reuse of an unchanged correction
counterpart, import-triggered serialized/latest-pending exports, export-only
recovery, retained input/publication history and safe output reuse after each KVK.
These are requirements, not claims of implemented behavior.

**Historical next-slice selection: S8B followed S7/S8A; current next slice is S8C above.**
Follow the current status above; do not rerun predecessors or start later implementation packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](kvk_source_migration/post_s6_integration_requirements.md); [handoff and exact manifest](kvk_source_migration/post_s6_handoff_log.md); [S7 pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

> **2026-09-12 S6 authenticated rehearsal update:** The operator restored the ignored
> local credential and approved the 5,806-player × ten-period synthetic benchmark,
> confirming both other importers would remain idle. Actual Google write/readback
> and local K98DEV rehearsal evidence now supersedes the earlier credential blocker.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN for operator acceptance and the exact
> unresolved operational gates recorded in the latest appendix of both release
> documents and the S6 pack. No production activation or G5 acceptance is claimed.


> **2026-09-12 S6 output-provisioning update:** Separate S6 output creation was
> approved and completed: one private index and eight private slots, owner and
> service-account Editor metadata verified. Operator expectation is 2–3 exports/day,
> with no fixed maximum duration. Code review found no common lock across S6,
> all-KVK export and scan-data import. Runtime Google rehearsal is currently blocked
> by the missing configured local service-account key; no provider interruption or
> representative-load pass is claimed. All three S6 gates remain OPEN. See the latest
> provisioning appendix in the two release documents and S6 pack.


> **2026-09-12 S6 rehearsal update:** Chris Watts subsequently approved a local
> K98DEV database and beginning rehearsal. Synthetic local SQL/process checks passed
> in `K98_S6_Disposable_20260912`; no production activation occurred.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN pending provider evidence and operator
> acceptance. Earlier G3-only/no-rehearsal statements below describe the retained
> preparation checkpoint, not the subsequent local rehearsal. See the dated
> rehearsal appendix in both S6 release documents for exact outcomes and gaps.


## Current S6 evidence preparation - 2026-09-12

**S6 G3 approved for documentation/evidence preparation only; stopped at G4.**
All preceding slices remain accepted; S5B-REC01 is closed. S6-OPS01, S6-PERF01 and
S6-CAP01 remain OPEN until separately authorized measurements and Chris Watts's acceptance.
G4 exact-operation approval and G5 acceptance remain operator-owned. No rehearsal, bot-machine
update, SQL operation, real import/export, Discord action, restart, deployment or activation.
The exact 18-path S6 documentation delivery includes all 16 pending closeout paths and both
S5B archive move sides. Eventual PR Files changed verification and promotion remain separately
authorized gates. Historical status blocks below retain their original dated evidence;
their pending/next-slice wording does not reopen accepted slices or authorize execution.

[Readiness and rollback](kvk_source_migration/release_readiness_and_rollback.md); [Canonical S6 evidence and delivery](kvk_source_migration/release_evidence_log.md).


## Current KVK delivery status - S5B closeout, 2026-09-12

**S5B is complete, operator accepted, successfully smoke tested and merged.**
Mirror [#271](https://github.com/cwatts6/K98-bot-mirror/pull/271) merged at 13:49:41 UTC as
`65c535dce831d0840f1a047b9c58f29c562df3df`; production
[#578](https://github.com/cwatts6/k98-bot/pull/578) merged at 13:50:14 UTC as
`c7e063f02ebe8287a584d0054ea14f91a0c0ecc6` on 2026-09-12, including final fix `e5bbd8f7`.
Local mirror main/origin main is `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`, synchronized from
that production merge; the final recovery fix and tests match production/main. This closes the
prior mirror synchronization handover item. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry. Local pulls are complete. The operator confirms
**no changes have been pulled to the bot machine**; repository merge is not runtime deployment.

Smoke acceptance is operator-reported and supported by recorded local import smoke and synthetic
recovery/transaction checks, not a fresh post-merge or bot-machine smoke. Final review-fix evidence:
186 focused tests passed, including five disposable SQL cases on local K98DEV database
`K98_S5B_Disposable_20260912`; split full suite 4,084 passed / 39 skipped, operational logs unchanged.
Imports, registration (36 top-level / 101 grouped), architecture, deferred-items, routing, lint/type
and staged secret checks passed. Production CI passed. Exact Changes review, Deep off,
`cf5a25c1-f9c6-431b-a2c6-fa9dba1716a7` completed with zero findings; earlier exact-slice evidence is
retained in the archived S5B pack. Historical results are not fresh tests of this closeout patch.

**Next: S6 Release Readiness and Controlled Activation in a new chat, after explicit S6 G3.**
All preceding slices remain accepted; S5B-REC01 is closed by accepted caller/lifecycle and disposable
SQL recovery evidence. S6 prepares documentation only and stops for separate G4 operational approval.
S6-OPS01, S6-PERF01 and S6-CAP01 remain open pre-activation evidence gates. G5 acceptance remains
operator-owned. The prepared S6 pack/starter require every pending closeout documentation change,
both S5B archive move sides and repaired links in the eventual separately authorized S6 PR.
No S6 execution or new chat is started by this closeout. Preserve all retained synthetic databases
and review evidence. Source routing and intake/recovery defaults remain disabled; no bot-machine
update, restart, production SQL, real import/export, Discord action, deployment or activation here.

## Historical KVK delivery status - S5A closeout, 2026-09-12

**S5A is complete, operator accepted, successfully smoke tested (operator reported) and merged.**
Mirror [#270](https://github.com/cwatts6/K98-bot-mirror/pull/270) merged at 08:53:35 UTC as
`c78823d5ae6852b251b2ea6dbc35fa2b4af7e42c`; private bot [#577](https://github.com/cwatts6/k98-bot/pull/577)
merged at 08:54:15 UTC as `dd69666a04daa47d6d596e694aff024a02417144` on 2026-09-12.
Local mirror main/origin main is `90aea74c93c6aad2c890d1783ff53f109cc7bf8a` (synchronized from that private merge);
local production/main matches the private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. **No changes have been pulled
to the bot machine**, as explicitly confirmed by the operator. Repository promotion is not deployment.

Successful S5A smoke is operator-attested; its detailed environment, commands and transcript were not
supplied in this closeout. Do not infer live SQL, real provider/Discord execution or a bot-machine smoke.
Recorded deterministic evidence remains 162 focused tests and 4,033 full tests passed / 34 skipped,
operational logs unchanged, import smoke passed, and registration 36 top-level / 101 grouped.
Every command group is <=25 children (kvk_admin 8; largest ops 24). Exact Changes review, Deep off,
scan `541665eb-2d37-4e14-8ce9-038329bf9653` has complete coverage and zero findings. Earlier gaps
remain historical in the archived S5A delivery; these tests/reviews are not fresh closeout reruns.

**Next: S5B Endpoint Config and Recovery Integration in a new chat, after explicit S5B G3 approval.**
S3B/S4B/S5A prerequisites are accepted. The S5B pack/starter are prepared; no S5B implementation or new
chat is started by this closeout. Recheck both repos and preserve the exact pending documentation
carry-forward manifest in S5B, including both S5A archive move sides and repaired links.
Use mocks/fake destinations until an exact disposable SQL target and operations are explicitly
authorized. S5B's required transaction/recovery SQL evidence remains a separate execution prerequisite;
full S5B acceptance cannot substitute mocks for that requirement. Preserve all retained databases.

S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open. S5A smoke does not close them. Source routing remains
disabled; intake/recovery defaults remain false. No bot-machine action, deployment or activation is
performed here. Historical statuses below are dated evidence, not instructions to rerun accepted slices.

## Historical S4B closeout - 2026-09-11

**S4B is complete, operator accepted, successfully synthetic-smoke tested and merged.**
Mirror [#269](https://github.com/cwatts6/K98-bot-mirror/pull/269) merged at 21:06:11 UTC as
`39c93df39485d796fd66881e47562da112886da1`; private bot [#576](https://github.com/cwatts6/k98-bot/pull/576)
merged at 21:06:38 UTC as `63fcb392385fd2ccad78801cbd4f8bd70f426cc3` on 2026-09-11.
Local mirror main/origin main is `64f6b058c224e749ece334d66cdf0efc81bd983d` (synchronized from the private merge);
local production/main matches that private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. The operator confirms **no bot-machine pull**.

The archived S4B pack retains actual real-SDK/disposable-SQL synthetic smoke: private recovery,
public Viewer publication, fresh-client reconciliation/deduplication and retired-slot reuse succeeded.
These are historical bounded smoke results, not a post-merge live rerun. Final review-fix validation:
150 focused tests passed; full suites passed in both checkouts with 3,940 passed / 34 skipped
(production 166.93s, mirror 168.50s), operational logs unchanged. Imports and registration 36/100 passed.
Separate exact Changes reviews, Deep off, completed with zero findings; both review comments were resolved.
Production quality and secret CI passed. Earlier incomplete smoke attempts remain historical evidence.

**Next: S5A Private Intake and Admin Controls in a new chat, after explicit S5A G3 approval.**
S1/S3B/S4A/S4B prerequisites are accepted. Start with fresh repo/contract checks and preserve this pending
closeout documentation. The S5A pack requires its exact documentation carry-forward manifest, both sides
of both S4B archive moves, repaired links and this evidence in its eventual separately authorized PR.
No S5A implementation or new chat was started by this closeout.

S4B-MP01 is complete. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open under their named gates;
they do not block mocked S5A development and are not closed by S4B smoke. Source routing remains disabled.
No bot-machine update/restart, deployment, production SQL, real import/export or Discord action is authorized.
Use mocks/fake destinations; any disposable SQL target and exact operations require explicit authorization.
Preserve all retained predecessor and S4B disposable databases. Historical prerequisite wording below is
retained as history; accepted slices stay closed and S5A/S5B/S6 retain separate approval gates.


## S4A completed closeout — 2026-09-10

**S4A is complete, operator smoke accepted and merged.** Mirror [#268](https://github.com/cwatts6/K98-bot-mirror/pull/268) merged on 2026-09-10 at 16:12:39 UTC as `eba04639eced51e368d6fc7036284f25640ce871`; private bot [#575](https://github.com/cwatts6/k98-bot/pull/575) merged at 16:13:04 UTC as `021fc7adc9952ab07d21517e8e47f3966c285f7a`.
Operator candidate smoke on `055b9590e1114661ff0369c7815fbbea82661454` passed imports, registration **36/100** without drift/duplicates, **134 focused tests in 11.97s**, and **3,810 full-suite tests with 34 skipped in 134.19s**. Both pytest runs left operational logs unchanged. This closes the S4A full-suite gap; earlier stalls and passes remain historical evidence, not a post-merge rerun.
Local mirror `main` is `7baf92c7badc3f40006841046825a788bc823373`; local `production/main` is `021fc7adc9952ab07d21517e8e47f3966c285f7a`; SQL `main` remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot and SQL checkouts were clean at closeout entry. Local pulls are complete, per operator and local refs; **nothing has been pulled to the bot machine**.
S4A pack/starter are archived. **Next: S4B Versioned Exports and Delivery in a new chat, with separate S4B G3 approval.** S4B's pack requires all pending closeout documents and both archive rename sides in its eventual separately authorized PR. Prior S3B closeout documents were included in the merged S4A PRs.
Source routing remains disabled. No bot-machine update/restart, SQL deployment, live imports/exports, Discord action or activation is needed for S4B local development. Use mocks/fake destinations unless a disposable SQL target and exact operations are explicitly authorized first; preserve retained S2A/S2B/S3B databases. Historical prerequisite wording below does not reopen completed slices.

## Purpose and boundary

Use this permanent local SQL Server instance for explicitly approved development and disposable
integration tests. It is independent of the production SQL server. It is not a replicated mirror
and does not contain a production data copy. Authoritative SQL definitions remain in
`C:/K98-bot-SQL-Server`; database contents are test evidence, not the schema source of truth.

## Verified setup — 2026-09-09

| Setting | Value |
|---|---|
| Local server | `9SX2VF4\K98DEV` |
| Local connection alias | `localhost\K98DEV` |
| Engine | SQL Server 2022 Developer, 64-bit |
| Version | `16.0.1200.5` (KB5122771), matched to operator-supplied production version |
| Authentication | Windows Authentication; installing Windows user added as SQL administrator |
| Server collation | `SQL_Latin1_General_CP1_CI_AS` |
| Development database collation | `Latin1_General_CI_AS` |
| Database compatibility | `160` |
| SQL max server memory | `8192 MB`, configured and active; host has 32 GB RAM |
| Service | `SQL Server (K98DEV)` / `MSSQL$K98DEV`, Manual startup |
| Client | SSMS installed separately; local connection uses Trust server certificate |

The instance was patched and the PC restarted before the final version verification. Microsoft
signature and published update SHA-256 were checked. These are dated setup facts; verify the
current instance/database before each execution. Read-only service check on 2026-09-10 found
`MSSQL$K98DEV` stopped, with Manual startup unchanged.

## Starting a local session

1. Open SQL Server Configuration Manager, select SQL Server Services and start only
   SQL Server (K98DEV) if stopped. No production service or bot restart is involved.
2. In SSMS, connect to `localhost\K98DEV` using Windows Authentication. Trust server certificate
   is a setting for this local development connection; it is not a production connection policy.
3. Verify `SERVERPROPERTY('ServerName')`, `SERVERPROPERTY('ProductVersion')`, `DB_NAME()`, database
   collation and compatibility against the explicitly authorized target before executing SQL.

SQLCMD is available at
`C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/170/Tools/Binn/SQLCMD.EXE`.
Prior local runs used explicit `-S lpc:localhost\K98DEV`, Windows authentication `-E`, `-C`, a
named database `-d` and fail-on-error `-b`. No password or production connection string is needed.
The agent sandbox could not authenticate; approved elevated local tool calls worked. This is
execution-environment behavior, not permission to search for credentials or alter security config.

## Retained S2A evidence database

`K98_S2A_Disposable_20260909` on the server above was explicitly authorized for S2A only. It has
the revised twelve S2A tables, 18 enabled/trusted foreign keys and 89 enabled/trusted CHECK
constraints. Last independent readback after the review fixes found zero rows in every table.
The fixture passed 96 expected rejection cases and positive correction/status checks, with full
rollback; the static validator passed 401 assertions. No production data was imported.

Retain this database as S2A evidence unless its rebuild/removal is separately within an approved
test operation. It is not an automatically authorized target for S2B or later slices.

## Retained S2B evidence — 2026-09-10

The operator authorized `9SX2VF4\K98DEV` and `K98_S2B_Disposable_20260910` for S2B.
Creation with compatibility 160 and `Latin1_General_CI_AS`, accepted S2A prerequisite
installation and migration `20260910_001_kvk_source_publication_state.sql` passed.
The service was already running at execution; no start or restart occurred.
Initial validation passed 131 rejection cases; the S2B PR review revision passed 144, with
265 static assertions and full 25-table rollback. The reviewed migration was retested by
transactionally replacing only verified-empty S2B tables in this same authorized database.
The accepted S2A migration and separate S2A evidence database were preserved. Independent
readback found 25 empty tables, 47 trusted/enabled FKs and 165 trusted/enabled CHECKs.
The separate S2A evidence database remained unchanged. Both databases are retained.

## Future slices

The instance can be reused; each slice must explicitly name and authorize its disposable database.
S2B authorization and completed execution are recorded above; neither retained evidence database
is automatically authorized for a later slice or destructive rebuild.
Use synthetic fixtures and the accepted S2A migration as prerequisites; installing prerequisites
in a fresh test database does not reopen S2A implementation or automatically execute another pack.

Keep migrations/fixtures in their owning slice's exact SQL manifest. Recheck migration date and
sequence at authoring time; the proposal in a prepared task pack is not an allocated slot.
Production deployment, real imports/exports, Discord actions and source activation remain separate.

## S2B repository closeout — 2026-09-10

S2B SQL #79, mirror #265 and private bot #572 are merged. Both local repositories were pulled
by the operator; the bot machine was not updated. Repository merge is not production SQL
execution. Preserve both evidence databases. S3A uses pure offline tests and requires no SQL
connection, database rebuild, bot restart or source activation.


## S3A merged closeout and S3B handoff — 2026-09-10

GitHub readback confirms mirror #266 merged at 11:28:48 UTC as
`3154997fa2dfc124da75ee35dca79463c3196a43`, and private bot #573 at 11:29:18 UTC as
`140fc89765b1d6ec8418ac6f6d039e575419c29e`. The synchronized local mirror main is
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`; SQL main is
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both local repos were clean at documentation
entry. Operator confirms local pulls complete, with no bot-machine pull or restart.

Operator smoke on mirror `d5cf27613e54047efb856f4bc3777ee6923fa14e` passed 77 tests in
3.10s, operational logs unchanged, and command registration 36/100 without drift or duplicates.
The prior implementation/regression results (260 tests) and separate completed production/mirror
Changes reviews remain in the archived S3A pack; those are historical runs, not newly rerun here.
S3A runtime/test contents matched the production candidate. Repository merge is not deployment.

S3A pack and starter are archived with repaired links. All predecessor evidence is retained.
Start S3B in a new chat using its refreshed pack/starter only with explicit S3B G3 approval and
an explicitly named disposable SQL integration target. Existing S2A/S2B evidence databases are
retained and not authorized for reuse/rebuild by this handoff. The bot machine need not be updated
for S3B local development. No SQL connection, service start, production action or successor
implementation occurred in this documentation closeout.

These documentation edits, including untracked archive destinations, remain pending for the
separately authorized S3B PR. Its pack contains the full carried-forward manifest and requires
both sides of renames, repaired links and preservation checks. No commit/push/PR is performed
by this closeout. Security routing: exact Markdown-only skip (status, evidence, links and archive
moves; no runtime/config/permission/data-access effect), plus separate SQL no-change skip.

## S3B merged closeout and S4A handoff — 2026-09-10

**S3B is complete, operator smoke accepted and merged.** Mirror
[PR #267](https://github.com/cwatts6/K98-bot-mirror/pull/267) merged at 13:59:47 UTC as
`e915f9727f9492fe4ecc02b5c0d9f3c6e443be13`; private bot
[PR #574](https://github.com/cwatts6/k98-bot/pull/574) merged at 14:01:14 UTC as
`a8ad9f1d81cfb7884a9cdcc0b067c4346a204488` on 2026-09-10.
Operator post-merge smoke on mirror main `e915f972`: import smoke passed, registration
36/100 without drift or duplicates, **36 tests passed in 9.11s** (4 publication + 32 SQL).
Current synchronized local mirror main is `02385a0edc0ec83f77241e02648eabb3b7640ea6`;
local production/main is `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both repos were clean at closeout entry.
S3B pack/starter are archived. **Next: S4A Shared Reports and Cards in a new chat, with
separate S4A G3 approval.** Preserve pending S3B closeout docs and both archive moves
for the eventual separately authorized S4A PR; its pack contains the complete manifest.
S3B's latest full-suite rerun stalled around 19% and remains incomplete; the accepted smoke
does not replace it. The earlier 3,764-pass full result is pre-review-fix evidence.

The operator confirms local pulls completed and no changes were pulled to the bot machine.
No bot-machine restart, production SQL deployment or source activation is evidenced or performed.
S4A local development does not require a bot-machine deployment. New routing remains disabled.

The accepted S3B boundary includes immutable acceptance, atomic publication and four review fixes:
rollback delivery reconciliation with increasing fences; aggregate rejection for equal-endpoint
no-fight windows; complete immutable action replay scope; accepted revision period-scope checks.
All five inline threads were replied to and resolved before merge. The two separate final
five-file Changes reviews, Deep off, completed with zero findings/deferred/open questions:
mirror `308e7130-8e09-45fc-9765-c4c9673fc21f`, private
`97196427-2c4a-40e5-acbd-3f3c3f71c6e9`. Earlier implementation/security evidence is retained.

Preserve the operator-approved endpoint amendment: either StartScanID or EndScanID may change;
a supplied end must be >= start. Distinct imported scans advance both ScanID and UTC scan start,
oldest first; semantic re-exports allocate no new scan. Blank/future end uses the latest eligible
interim; an available end pins the final, and an authorized endpoint update permits replacement
without a separate correction command. Equal endpoints produce zero supported fight scores for
every frozen B0-eligible member, including absent scan members, with aggregates not applicable.
Ordinary missing-data states remain explicit. Aggregate reports and daily SCANORDER stay separate.

The authorized S3B test target was `9SX2VF4\K98DEV` /
`K98_S3B_Disposable_20260910`, including prerequisite schema and synthetic two-connection tests.
Retain this database and the separate S2A/S2B evidence databases; no reuse/rebuild for S4A is
implicitly authorized. S4A uses mocks by default; any SQL integration must first have an explicitly
authorized disposable target and operations. No connection or setup was performed in this closeout.

The supplied transcript shows 36 passed in 9.11s on merged mirror main `e915f972`, import smoke
success and registration 36/100 without drift/duplicates. Its raw attachment stays outside Git.
The current synchronized main contains identical KVK source and these test files to private merge
`a8ad9f1d`. Historical 257 affected regressions passed with logs unchanged. The operator smoke
did not run the log-noise wrapper, so it is not new log-hygiene or full-suite evidence.
The interrupted post-review full suite remains an explicit S4A validation follow-up; investigate
its cause and run the required full suite/log-noise gate without silently expanding runtime scope.

S3B pack and historical starter are archived, with links repaired and delivery history retained.
The S4A pack/starter require all pending closeout documentation, including untracked archive
destinations and both source deletions, in the eventual separately authorized S4A PR.
These edits stay uncommitted for that handoff. No new chat or S4A implementation is started here.
Documentation-only security skip: exact closeout/status/links/archive manifest, no runtime,
configuration, permission, data-access or deployment effect. SQL repository: separate no-change skip.
Runtime pytest/smoke/registration reruns are skipped for this Markdown-only closeout.
