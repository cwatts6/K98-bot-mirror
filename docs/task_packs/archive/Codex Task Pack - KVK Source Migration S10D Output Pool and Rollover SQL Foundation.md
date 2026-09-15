# S10D — Output Pool and Rollover SQL Foundation

## Current status — S10D SQL merged; S10E scope next, 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](../../reference/kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
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

Historical S10D scope instructions follow; #87 and the current closeout supersede their pending status.

## Status and authority — 2026-09-15

**Prepared for initial review/scope only. S10C is reviewed, merged and locally pulled.**
No changes have been pulled to the bot machine. This pack authorizes no implementation, SQL
execution, provider/Discord operation, real import/export, Git publication, deployment, activation,
predecessor rerun or automatic new task. Return scope, risks, tests and an implementation plan for
approval before authoring SQL. Earlier S10C implementation/execution boundaries are not S10D authority.

Read the [S10C closeout and exact documentation manifests](../../reference/kvk_source_migration/s10c_closeout_and_s10d_handoff.md)
and [starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10D%20Output%20Pool%20and%20Rollover%20SQL%20Foundation.md).
Bot main/origin main is `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main is
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`; SQL main/origin main is
`a03835a12feb0d52374e00206f944a02d8937fbd`. Recheck both repos and preserve all pending work.
These are comparison anchors, never reset instructions. Mirror #279, production #586 and SQL #86
are merged; no predecessor reapproval is required. SQL repository merge is not installation proof.

## Required references

Read current AGENTS/core references and the authoritative SQL repository's guidance. Apply
`k98-architecture-scope`, `k98-sql-validation`, `k98-test-selection` and security routing as relevant.
Read the approved S7 [contract](../../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md),
[exact manifests](../../reference/kvk_source_migration/integration_implementation_manifests.md#s10d),
architecture/EndScanID amendment in the [phase 2 architecture](../../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
[retained release evidence](../../reference/kvk_source_migration/release_evidence_log.md) and
[readiness/rollback](../../reference/kvk_source_migration/release_readiness_and_rollback.md).
Retain S6/S8 evidence distinctions in the closeout; accepted historical results are not fresh S10D evidence.

## Exact S7 SQL boundary and scope-time reconciliation

S10D is a **SQL-only implementation slice**. No Bot runtime, commands, services, views, configuration,
S10E operator/rollover implementation or S11 release implementation is included. The exact S7 proposal is:

| Action | SQL-repository path | Scope note |
|---|---|---|
| Create | `migrations/20260912_003_kvk_output_pool_rollover.sql` | Historical S7 proposed name; replace with actual creation date/free daily ordinal during scope, before approval/authoring |
| Create | `sql_schema/KVK.SourceOutputPool.Table.sql` | Pool ownership and epoch/lifecycle shape |
| Create | `sql_schema/KVK.SourceOutputSlot.Table.sql` | Unique physical file identity and current slot assignment |
| Create | `sql_schema/KVK.SourceOutputDisposition.Table.sql` | Append-only disposition/evidence history |
| Create | `validation/kvk_source/s10_output_pool_rollover.sql` | Authored validation, never implicit execution |
| Modify | `docs/SQL_DELIVERY_LOG.md` | Mandatory delivery documentation |
| Modify | `migrations/README.md` | Mandatory carried documentation in addition to the original S7 six-path table |

At closeout the three proposed table snapshots and proposed migration/validation files are absent.
Do not create them in this documentation task. During S10D scope, verify absence/collisions again,
read migration naming and metadata standards, and record the exact resolved filename and complete
seven-path baseline. Never rename a merged migration. Any required additional checker, FK/index
snapshot or existing-object change must be justified in the exact implementation scope before approval.

Validate against authoritative SQL source, not Python guesses: `KVK.SeasonSource`, `KVK.SourceRouting`,
`KVK.SourceDelivery`, `dbo.ExportJob`, `dbo.ExportJobResource`, `dbo.ExportResource`,
`dbo.ExportRequestBudget`, `dbo.ExportAttempt`, `dbo.ExportAttemptPart`, and the S10C
`dbo.ExportPreparation`/`dbo.ExportPreparationResource` extension. S10C added mutually exclusive
job/preparation resource ownership and membership FKs; do not reconstruct the pre-S10C shape.
No deployed schema or rows have been checked. Explicitly report missing or ambiguous objects.

## Contract to scope

Derive exact keys, types, enums, scoped FKs, indexes and checks from S7 and the accepted source.
The proposed objects are design contracts, not claims of deployed columns:

- Pool: PoolID, unique stable IndexFileID, active KVK/ChoiceID, Epoch, lifecycle state
  active/closing/closed/setup/blocked, OwnerID/Fence/Version, registered account/audience metadata.
- Slot: unique FileID, PoolID, state free/staging/active/quarantined/retired, epoch and exact
  attempt/part reference with versioned assignment. File IDs cannot alias another pool or stable
  index identity. Scope enforcement across both tables; two independent UNIQUE constraints do
  not by themselves prove cross-table uniqueness.
- Disposition: immutable identity, pool/file/attempt scope, old/new epochs, action
  retire/quarantine/clear/assign, actor/reason/UTC and bounded evidence/hash. Preserve prior receipts;
  current assignment state must not erase append-only assignment/disposition history.

Define how each invariant is enforced: SQL static constraint, transaction/CAS under a named owner,
or later S10E provider evidence. Do not describe a table CHECK as proof that a remote file is private,
empty, absent, or safe to reuse. Do not add a database-time release rule for old leases or job states.
Reject malformed/blank/padded identities, illegal ownership/state combinations, scope-mismatched
attempt parts, epoch regression and stale versions. Use accepted BIN2 identity conventions,
bounded JSON/DATALENGTH, UTC, deterministic lock order and non-cascading history references.

Capacity retains S7-D08: **1 stable index + P active + P staging + max(P,Q) quarantine + P reserve + R**.
P comes from the real partition plan, Q is actual quarantine, R is other protected references.
P=2, Q<=2, R=0 gives nine files; it is not proof that retained S6 pools or larger reports fit.
Preserve the 9,000,000-cell part ceiling, at most eight registrations and sixteen slots per registration
unless a separate limit change is approved. Capacity/receipt preflight must finish before mutation;
exhaustion returns setup required, never silent reuse. Preserve normalized attempts/parts and existing
bounded legacy receipts without truncation, blind remapping or rewriting their bytes.

Rollover requires explicit preview, old/new KVK and epoch, closing old admission, draining/reconciling
running work, and audited cancellation of only never-started pending exports. Publications and inputs
remain. Epoch advancement requires proof that no old writer can act; SQL fences cannot cancel an
already-submitted provider request. Reuse requires separately authorized private-ACL verification,
complete clear of prior content/formatting/named ranges and empty-manifest readback. Uncertain ACL,
clear or pointer outcomes remain quarantined/blocked. Record old URLs as retired/reused rather than
permanent archives. No silent Discord edits/deletions and no automatic replacement of an uncertain index.
S10D designs persistence for these gates; S10E implements workflows and later exact authorization permits I/O.

Retain running immutable A when B/C arrive, eligible pending-only coalescing, account fairness,
daily SCANORDER/history, destination-ID alias rejection, owner/fence/version CAS and exact scoped
receipt identity. S10C captures complete output/config/header/provenance under shared admission,
passes owners to nested writers, preserves UPDATE_ALL2 transaction ownership, and paces both SDKs
using server-UTC reservations/completion/cooldown. Shutdown stops new admissions and drains claimed
deliveries; uncertainty or late threads retain claims until authoritative reconciliation. No SQL
transaction over waits/provider calls, mutable per-tab rereads, ScanID completion inference or
relabeling advanced output as an earlier generation. Retain durable spool digest/length/owner,
pending capture evidence and explicit unavailable results. Keep registration-aware intent lifecycle
and one-period-at-a-time compaction.

Preserve fixed source per season and independent stats/targets/publication/roster/history/daily
consumers; supplied overall/B0 and authoritative aggregates/DKP; UTC starts, unused scans, movable
within-season windows and the exact 11−10 / 12−10 / final 13−10 / authorized 14−10 endpoint chain.
Keep sealed inputs/CAS, matched UpdateID and explicit counterpart attestation. No mixed sources,
summed-fight overall, silent legacy fallback or SourceRouting.Enabled-only activation.

## Tests, migration and approval output

Return a bounded implementation plan with exact files/objects, FK and ownership matrix, static versus
temporal/provider guarantees, migration metadata/order, data-safety/backup and forward-fix strategy,
risks and explicit implementation approval checkpoint. Validate inherited accepted shape before
alteration/sealing; reject drift rather than blessing observed metadata. Existing receipts/history
must remain byte-preserved; ambiguous legacy mappings block rather than become guessed assignments.
Additive installation is not activation. Do not promise drop-table rollback after history exists.

Map S7-T14/T15 to authored SQL cases for valid/invalid scopes, ownership states, duplicate file/index
aliases, attempt-part FKs, stale CAS, monotonic epoch, append-only dispositions, malformed evidence,
capacity boundaries and quarantine protection. Identify separately authorized disposable install/rerun,
partial/drifted installation, two-connection concurrency, lost acknowledgement and backup/actual-restore
tests. Those cases are a future operation plan, not permission to execute them or use retained S6/S8 databases.
Bot rollover/operator tests in S7 belong to S10E; do not manufacture Bot implementation for test coverage.

After implementation approval, use security routing then **Changes, Deep off**, on the exact SQL
base/head or immutable working-tree patch. Bot documentation alone gets a precise documentation-only
skip; any independently approved Bot runtime delta requires its own Bot Changes target. Never combine
repository histories or substitute a full/deep codebase scan. Run relevant SQL static/metadata validators
and document limitations. No actual DB/provider/Discord execution without later exact target/operation approval.

## Mandatory documentation delivery and carry-forward

The [closeout's exact pending Bot and SQL manifests](../../reference/kvk_source_migration/s10c_closeout_and_s10d_handoff.md#exact-pending-bot-documentation-manifest)
are mandatory S10D scope inputs. Reconcile fresh Git status, including staged/unstaged/untracked/deleted
files, and extend the manifests for later task-produced documents. **The eventual S10D SQL implementation
PR must include every pending SQL document**, including both delivery log and migration README.

**Every pending Bot document, this pack/starter, the closeout and both source/destination sides of both
S10C archive moves must remain grouped in the next authorized Bot implementation PR, currently S10E.**
S10D must carry that exact list into its closeout and S10E task; completing the SQL PR does not deliver
Bot files. If S10D scope proves a necessary separately approved Bot implementation delta, those documents
accompany that Bot PR; never create runtime work just to publish docs. No standalone docs PR, repository
mixing, omitted archives or renewed grouping/predecessor acceptance questions.

Before PR handoff and again at promotion, verify every required path against all GitHub `filename`
AND `previous_filename` entries. An already-delivered path requires exact merged commit/content proof;
an archive source absent at base requires exact base/absence proof. Counts alone are insufficient.
The merged S10C 83-identity Bot/eight-path SQL delivery is complete; distinguish newly pending changes
from already-delivered historical work.

Preserve S6-OPS01/PERF01/CAP01, uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and
`54a2480a-26fb-5bad-a3f5-9321525a731c`, and every retained database/file. S8A six scripts, S8B accepted
50 cases/actual restore versus offline history, and S8C seven local checks remain distinct. Nothing in
this pack is fresh live Discord/provider/deployment evidence or authority to probe, clear, reuse or delete them.
