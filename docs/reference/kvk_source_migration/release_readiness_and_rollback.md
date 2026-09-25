# KVK Source Migration S6 release readiness and rollback

## Current next step: deliver repair, then plan G4 — 2026-09-25

Delivery update: [Bot-mirror #282](https://github.com/cwatts6/K98-bot-mirror/pull/282) and
[SQL closeout #90](https://github.com/cwatts6/K98-bot-SQL-Server/pull/90) are open. Linux CI
passed the real rsync regression on the initial Bot head; see the
[published receipt](release_evidence_log.md#published-pr-handoff--2026-09-25). Review final-head
checks before merge; production promotion and all G4/G5 operations remain separate.

S11 mirror #281, SQL #89 and production #588 are already merged. The prior publication proposals
below are historical. The approved local mirror publication repair and current handoff documents
are ready for review together on `codex/s11-mirror-g4-handoff`; see the
[validation receipt](release_evidence_log.md#mirror-repair-and-g4g5-handoff-validation--2026-09-25).
The operator has now authorized separate Bot-mirror repair/handoff and SQL closeout PRs for
parallel review. No merge or production publisher run is implied. Before merging the repair,
require the new Linux Mirror Publication Policy check: real rsync is unavailable on this host.

Any authorized delivery must include the complete pending Bot union, including the new task
pack/starter, closeout and identity manifest. PR #282 now also corrects incomplete-drain exit
status and shared 429/503 cooldown feedback; see the [correction scope](s11_closeout_and_g4_handoff.md#pr-282-review-corrections--2026-09-25).
Production patch promotion must carry those runtime/test modifications and the filter/workflow/
docs delta. Compare current blobs and omit only still-identical additions; four of the five
initially restored source/test files now differ from production due to these corrections.
Verify exact filenames/blobs and production publisher synchronization; never mix histories.
The operator's latest instruction explicitly authorizes the two SQL closeout documents in their
own SQL PR now, superseding the earlier deferral for these entries. No SQL runtime delta is added.

G4 planning must pin the reviewed correction revision and refreshed protected source inventory.
Include incomplete-drain failure/session retention and 429/503 cooldown plus lost-checkpoint
cases in the exact later approved runtime evidence packet. If these fail, close admission,
retain claims/evidence and reconcile; never use a retry or claim release as rollback. Restoring
earlier source bytes does not settle a dispatched request or prove provider termination.

Use the new G4 pack to develop exact targets, commands, prerequisites, evidence, rollback and
approval checkpoints. No operation is executable while target/identity/source/approval fields
are unresolved. Controlled rollout executes only named approved packet operations. Operator G5
acceptance and activation are separate decisions after evidence review. No source or security
review result closes SQL/native/provider/deployment gates or retained S6/S8 uncertainties.

## Current delivery and next phase — 2026-09-25

S11 Bot mirror #281, SQL #89 and production Bot #588 are merged. See the
[source closeout and exact manifest](s11_closeout_and_g4_handoff.md) for delivered behavior, review
corrections, source pins and the mirror publication repair follow-up. Production deployment,
SQL installation, provider behavior and G5 acceptance are not established by these merges.

Next: **G4 plan development only**, using the [new task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md) and
[chat starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md). Controlled rollout executes only specifically approved
operations; G5 remains operator-owned. Earlier dated checkpoints below retain their original
scope/status as historical evidence, including headings used by existing links. They do not
reopen implementation or authorize live operations. Preserve S6/S8 gates, uncertainties and data.

## S11 local work complete; publication decision — 2026-09-25

Report qualification: the sealed Bot coverage flag retains an obsolete pending-review row.
The same bundle contains completed source reviews and exact hashes for every path named in
that row. The evidence receipt links the preserved report and standalone clarification; do
not treat the machine flag as complete. Local source work is complete, while actual native
remediation verification remains blocked until separately authorized G4 observations.

The approved local implementation, final offline checks and exact Bot Changes review are
complete. Scan 8cf1584b-9dd4-45bd-918d-7ad55c562173 has zero reportable findings; the separate
unchanged SQL review also has zero reportable findings. See the [final evidence receipt](release_evidence_log.md#s11-final-local-review-receipt--2026-09-25)
for exact target hashes, test chronology, coverage reuse and native/transaction/provider limits.
No further local-design approval or sample/credential input is pending.

The concrete next decision is the two draft-PR operations in the plan below: authorize separate
Bot and SQL branches, exact staging, commits, origin pushes and draft PRs, with per-file and
previous_filename readback. The complete exact path/action/hash manifests and archive proofs
are retained in .codex_artifacts/s11-authority-composition/final-delivery-manifest.json and its
readable final-delivery-plan.md. All mandatory document grouping is included. Source/test/SQL
hashes remain reviewed; only this and the evidence-log completion receipt follow the sealed
scan as documentation-only additions. No Git publication has occurred. The original explicit
publication restriction is why this decision is separate from completed local implementation.

Once delivery is authorized, use those manifests without resetting or dropping pending work.
The remaining live G4 and G5 rows below stay open and require their own exact operator packet.
Do not infer publication approval as permission to merge, promote, install, provision, pull,
restart, deploy, activate or rerun a predecessor. No live operation is needed for the draft PRs.

## S11 local closure and exact next approval — 2026-09-25

The approved single-host/fresh-identity design is implemented locally. No sample export, new
service-account detail or secret is needed to complete this local work. The latest validation
and final Changes-review receipts are in release_evidence_log. Earlier pending-design or
missing-implementation sections are historical. Source closure does not close operational gates.

| Boundary | Current local evidence | Remaining proof or authorization |
|---|---|---|
| Bot source/offline | Actual callers/helpers, closed runtime, trusted proof producers, all shared writers and owned shutdown drain; full 5,812-pass run followed by 704-pass final-delta run | Exact final Bot Changes receipt and source hashes; Git delivery remains separate |
| SQL source/static | Separate corrected 19-source review; 181 evidence and 454 legacy static assertions; 14 Bot metadata queries parsed | Actual installed source/signature/grant/shape/permission observations, not inferred from static success |
| SQL transactions | Gated disposable fixtures authored; ordinary offline tests use fakes | Named disposable target, backup and actual restore, engine CAS/NULL/fence/version/transaction outcomes |
| Windows/provider | Protected bootstrap, nonprivileged caller checks, supervised child, bounded pipe I/O, retained journals and fixed proof producers authored | Exact host/tokens/ACLs, exclusive fresh key custody, real containment/readback and no delayed effects |
| Deployment/G4 | Source pins and seven-record boundary format authored; admission closed | A concrete operator-approved operation packet, actual installation and observations |
| Acceptance/G5 | S6/S8 retained evidence unchanged | Operator-owned acceptance after G4, including open S6 gates and both uncertain publications |

The next delivery approval can be limited exactly to these operations:

1. In the Bot repository, create codex/s11-controlled-release-bot from the preserved current
   721ad7e0cd6b160ddddad328c2338a98bdfb6e0a checkout, preserving all pending work. Stage the exact
   reviewed Bot source/test/document manifest, commit, push that branch only to origin
   (K98-bot-mirror), and open a draft PR into its main branch. Include every pending Bot document,
   the S11 pack/starter, S10D/S10E closeouts and both source/destination sides of the S10E moves.
2. Separately in the SQL repository, create codex/s11-controlled-release-sql from the preserved
   current 2352a898881d4b74d6eec153bb3cb381d6162041 checkout. Stage its exact 19-source/two-document
   manifest, commit, push only to that repository's origin, and open a draft PR into main.
3. Read back each PR's exact filenames and previous_filename values. Compare every manifest
   path, including both archive sides; if Git represents a move differently, retain exact
   merged/content/absent-at-base proof. Counts alone do not establish inclusion. Attach both PRs.

This is a prepared approval plan, not publication authorization. Proposed branch names were
absent when checked; recheck refs and all file hashes before any authorized stage/commit. If a
path or target changes, reconcile that delta before delivery. No standalone documentation PR
or repository mixing is permitted. Pending preparation stays with the next genuine authorized
implementation PR. Production promotion, merging, Bot-machine actions and activation are not
included in this proposed draft-PR approval.

After delivery, prepare G4 against named machines, exact server/database/version and accounts,
Bot/authority SIDs, protected paths, source/config/SQL hashes, pool/file/grid IDs and protected
resource exclusions. The seven original observation records are host_acl, bot_identity,
identity_issuance, key_inventory, file_access, writer_drain and sql_installation. Missing or
conflicting records keep admission closed. Review actual observations; never let startup learn
its own expected metadata values. List exact old-writer/session termination, fresh-key issuance,
ACL/role/certificate/proxy provision, SQL install/reverse scripts, disposable restore and
transaction/provider/containment cases, promotion/pull/restart and observation points before
requesting that distinct operator approval. There are no current exact target values to execute.

Before installation, rollback is continued non-installation. Later, close admission and drain
owned delivery; retain uncertain claims, all receipts, origins, journals and data. Stop and prove
termination of old writers, then reconcile escaped or delayed effects. Private clear/readback
must precede audited reuse. Interrupted retirement requires explicit journal recovery and proof
of no delayed effects; a timeout, process restart or empty read alone never authorizes retry or
reuse. Do not silently restore copied-key legacy writers. S6 open gates and both uncertainties,
S8A's six scripts, S8B's 50 cases/actual restore versus offline history, and S8C's seven local
checks remain distinct. No predecessor rerun is part of this approval sequence.

## S11 composed runtime and remaining operational gates — 2026-09-24

The one-host/fresh-identity design is approved and its local composition is authored. No design
answer, sample export or service-account secret is required for the remaining local checks.
Earlier pending-answer and unimplemented-factory checkpoints are retained as history.

| Boundary | Source/offline evidence | Still required separately |
|---|---|---|
| Bot composition | Actual factories/callers, producer-cursor checks, shutdown lifetime, fixed authority issuer and typed publication outcomes authored | Final full regression and exact Bot Changes review, Deep off, recorded in release_evidence_log |
| SQL/static | Existing corrected SQL review remains the separate 19-source target; 14 new Bot metadata queries parse without SQL | Actual installed schema, shapes, signatures, privileges and metadata expected-value review |
| SQL transactions | Existing disabled disposable cases retained; new cursor checks tested with fakes | Approved target, backups and actual restore; real root/child transaction/CAS/fallback results |
| Windows authority | Seven-record deployment boundary, actual IPC token refusal, supervised children and private replay authored | Exact host/SIDs, nonprivileged Bot token, path ACLs, fresh key custody and no escaped/delayed writer proof |
| Provider | Recorded typed operations and positive content/absence/recovery proof logic tested offline | Exact resource ACLs/owners, actual readback, interruption, escaped request and delayed effect outcomes |
| Deployment/G5 | Default admission closed; no Bot-machine pull or activation | Separate delivery approval, exact operator-owned G4 operations, then independent G5 acceptance |

Ordered next approvals (not execution instructions):

1. Complete local regression/review and retain exact Bot and separate SQL source digests. Review
   the complete mandatory document/rename union; request Git delivery authorization separately.
2. Prepare a concrete G4 packet with named machine, server/database/version, restricted accounts,
   nonprivileged Bot and authority SIDs, private paths, source/config hashes, exact pool/file/grid
   inventory and protected resource exclusions. Review the original observation exports and
   normalize the seven records described in the integration contract. No approval Boolean is
   evidence; missing, opaque or conflicting observations leave admission closed.
3. List every proposed operation before approval: stopped old writers and ended SQL sessions,
   fresh SA/key issuance and custody, permissions and restricted proxy/signing-key provisioning,
   ordered SQL installation and reverse packet, approved disposable restore targets, exact
   containment/provider/transaction cases, Bot promotion/pull/restart and observation points.
   Retain public certificate/signature bytes, original module/signature/grant hashes, restore
   evidence and rollback custody. Independently derive expected metadata/permission hashes from
   reviewed source and installed observations; startup must never learn its own expected values.
4. The operator explicitly approves that exact G4 packet. Execute only its named operations,
   resolve uncertainty through the retained journals, and record actual results. No predecessor
   rerun, retained-file clearing, arbitrary pool reuse or broad activation follows implicitly.
5. The operator owns G5 acceptance after actual G4 evidence, including S6-OPS01/PERF01/CAP01 and
   both uncertain publications. S8A six scripts, S8B 50 cases/actual restore versus offline history,
   and S8C seven local checks remain distinct retained evidence, never substitute acceptance.

Before installation rollback is continued non-installation. After deployment, close admission,
drain owned producers/delivery, terminate old writers under exact identity and reconcile all
uncertain requests before any reversal or credential/file reuse. Do not simply turn the feature
off and resume legacy writers while claims or delayed effects remain unresolved. Retain SQL
claims, append-only dispositions, byte-exact receipts, private evidence, full S10C provenance/
spools, nested owners and retirement journals. Private clear/readback and audited reuse follow
termination and explicit recovery only. Preserve immutable A, eligible pending coalescing, daily
order/fairness, source/endpoint/UpdateID contracts, P/Q/R, 9,000,000-cell parts and 8/16 bounds.


## S11 corrected SQL review and remaining authority decision — 2026-09-24

The NULL guard corrections are locally complete, including their new separate SQL Changes
review with Deep off. The only new decision currently requested is the
[initial one-host/fresh-identity credential contract](integration_contract_and_consumer_matrix.md#s11-remaining-host-and-credential-decision--2026-09-24).
The same key on both machines, one reported Bot instance and viewer-only output sharing do
not supply independently enforced writer exclusion. Missing DPAPI history from another
authority cannot be replaced by SQL hashes. No response to this proposal has yet arrived.

| Boundary | Current evidence | Remaining requirement |
|---|---|---|
| SQL source/static | NULL guards corrected; 181 evidence and 454 legacy static assertions; three changed SQL drafts parse; current 19-source Changes review complete with zero reportable findings | No further SQL correctness finding from this review; assess any future actual SQL delta separately |
| Bot offline | 403 affected tests passed; 9 SQL cases skipped; lint/format and required architecture/deferred/routing/selection checks passed | Finish trusted issuer, complete runtime/caller/shutdown binding and complete application SQL readiness after the concrete credential decision |
| Final Bot review | Earlier full runtime suite retained: 5657 passed, 81 skipped; runtime Python unchanged by NULL correction | One settled regression/log-noise run and exact separate Bot Changes review, Deep off, after remaining implementation |
| SQL transaction/installation | Fixtures, exact source/signature and permission contracts authored only | Approved disposable target, actual backup/restore, engine outcomes, complete installed dependency/output metadata and effective privileges |
| Host/provider | Supervised local authority, origins, fixed probes and sealed replay authored | Actual credential custody/key inventory, exact host/SIDs/source/ACLs, complete writer exclusion, provider readback and escaped-request outcomes |
| Deployment/acceptance | Admission remains closed; no Bot-machine pull | Separately authorized Git delivery, exact G4 operations, then operator-owned G5 acceptance |

The proposed fresh identity provides a boundary from the copied legacy key; it is not itself
proof of custody or a deployed control. The actual G4 packet must establish that boundary
before any runtime admission. Current operational identities/files/data remain unchanged.
Before installation rollback is non-installation. Later rollback closes admission, drains
owned work and reconciles uncertainty while retaining claims, receipts, origins and journals.
Do not silently restore a copied-key writer, adopt old files, reuse capacity or retry unknown
requests. All S6 open gates and both uncertainties remain; S8A six scripts, S8B 50 cases and
actual restore versus offline history, and S8C seven local checks retain their distinct status.

No SQL/provider/Discord execution, real import/export, key/proxy provision, service installation,
Git publication, Bot-machine pull/restart/activation or predecessor rerun is authorized. All
pending Bot documents and exact archive sides retain their settled grouping; SQL stays separate.


## S11 SQL review correction approval — 2026-09-24

The exact SQL Changes review is complete with zero reportable security findings, but source
correctness is not yet ready for release. Approve the bounded [NULL guard correction design](integration_contract_and_consumer_matrix.md#s11-sql-null-guard-correction-proposal--2026-09-24)
and its [eleven existing-path manifest](integration_implementation_manifests.md#s11-sql-null-guard-correction-manifest--2026-09-24)
for local source changes, offline validation and a new separate SQL Changes review with Deep
off. This decision does not repeat the completed legacy certificate-permission authorization.
It covers newly discovered evidence-API and installer/fixture corrections outside that last
permission-only edit, while all previously authorized S11 implementation work remains authorized.

The security-diff-scan workflow requires asking before actionable remediation. The current
continuation therefore records the completed review and concrete correction proposal without
applying it. No security vulnerability label, new capability or expanded deployment authority
is inferred from the correctness defects.

| Boundary | Local work after correction approval | Separate evidence still required |
|---|---|---|
| SQL source/static | Reject NULL version/definition/permission observations; keep exact embedded/snapshot bodies aligned; verify all five definition guards; ScriptDom parse and both source-contract checks | Static acceptance does not prove any installed body, signature or token |
| Bot offline | Author gated NULL/stale/valid event cases; run the integration module with SQL gates disabled, focused authority/composition regressions and applicable lint/validators | Skipped engine cases remain unexecuted; no claim that a fake row proves SQL NULL semantics |
| SQL transaction/provider | Prepare exact negative/positive G4 cases: NULL/zero/stale/valid version, unchanged request/event/version counts on rejection; visible exact/drifted/unreadable definitions; unknown/allowed/denied permissions | Operator-approved disposable target, actual backup/restore, restricted identities, engine execution and retained outcomes |
| Review | Freeze corrected SQL patch and run Changes, Deep off; preserve current report as pre-correction evidence | Final exact Bot runtime Changes review after remaining composition settles; no repository mixing |
| Deployment/acceptance | Keep installation and runtime admission closed | Explicit Git delivery and exact G4 operations, then operator-owned G5 acceptance |

Use existing gated integration fixtures and authority/SQL helpers; do not introduce a new
runtime abstraction. Check architecture/deferred/security-routing validators and test selection,
plus both repositories' whitespace. Broaden tests only if the actual corrected scope requires
it. The completed 5657-pass suite covers unchanged runtime Python; any later result must name
its actual tree. Actual opaque-module installation/reapply and denied-token behavior remain
G4 tests even if the static guard checks pass.

Before installation rollback remains continued non-installation. The 20260924_001 draft is
uninstalled and may be corrected in place; do not assume an installed or published migration
can be edited. If contrary installation evidence appears, stop and scope an additive forward
fix. Preserve all existing SQL objects/data/receipts and the legacy 002 permission delivery.
Later rollback closes admission, drains/reconciles and retains claims on uncertainty. No
provider clear/reuse or retirement retry follows from this guard correction. Bot-machine pull,
restart, activation, provider/Discord/SQL execution, signing-key/proxy provisioning, real
imports/exports and predecessor reruns remain unauthorized.

All mandatory document grouping and exact archive identities stay settled. No further samples,
service-account details or inventory answers are required for this local correction decision.



## S11 correction approved; implementation continues — 2026-09-24

The operator approved the NULL guard correction and directed continued closure of remaining
authorized local implementation gaps. The eleven-path correction is applied and its focused
offline/static checks passed; no further source-correction approval is pending. Existing
proposal/approval text below is retained as history, not a renewed approval gate.

The next local work is the trusted proof issuer, runtime/caller/shutdown composition and
complete application SQL readiness, followed by settled regression and separate exact Bot/SQL
Changes reviews with Deep off. A deployment manifest, a viewer ACL or a successful readback
cannot replace exclusion of all former writers and reconciliation of escaped requests.

No SQL installation/transaction, provider/Discord operation, real import/export, key/proxy
provisioning, Git publication, bot-machine pull/restart/activation or predecessor rerun is
authorized. G4 exact operations and G5 acceptance remain operator-owned. Before installation,
rollback is continued non-installation. Later rollback closes admission, drains/reconciles,
retains uncertain claims and all evidence, and never blindly reuses or retries retired files.

## S11 legacy permission checkpoint and remaining gates — 2026-09-24

The additional SQL permission scope is approved and locally authored. No further approval was
needed for these source/offline changes. It does not authorize SQL installation, key or proxy
provisioning, provider/Discord operations, Git publication or bot-machine actions.

| Boundary | Current evidence | Still required |
|---|---|---|
| SQL source/static | 38 exact definitions, three signing groups, 26 explicit signature/grant entries each, guarded forward/reverse scripts and source checks | Separate SQL Changes review, Deep off, on the settled SQL delta |
| Bot static/offline | Source pin, 13 parsed metadata batches, same-session refusal before the producer; 561 focused tests passed | Remaining complete trusted-issuer/caller composition and settled regression/security review |
| SQL installation | Migration and read-only verification authored only | Exact target/version/default schema; actual module/dependency/output metadata; public certificate/signature packet, principals/grants and installed receipt |
| SQL transactions | Three new separately disabled legacy cases; nine SQL cases skipped overall | Actual denied-TRUNCATE fallback/rollback, all seven roots and necessary child paths, ownership/CAS behavior on approved disposable resources |
| Server/host | Master mapping and required bulk/file capabilities described in source | Actual restricted proxy identity, file ACLs, complete host/writer exclusion and no-delayed-effects evidence |
| Provider/deployment | Existing authority/origin/probe source retained; default production composition closed | Exact G4 provider/containment/drain/reconciliation operations and operator-owned G5 acceptance |

The version-1 legacy permission contract supplements the existing version-2 coordination
observation. It cannot stand in for complete table/view/trigger/output-shape or application-wide
readiness. This delivery supports SQL Server 2022 and ROK_TRACKER because current source contains
that explicit database and unqualified dbo-dependent names; the actual installed target is still
unobserved. A different version or resolution requires an exact assessed contract, not a bypass.

The approval sequence remains: finish the remaining authorized source composition; freeze exact
Bot and SQL patches and perform separate Changes reviews with Deep off; obtain explicit delivery
authorization; then prepare and approve an exact G4 packet. That packet identifies target/restore
resources, source and migration hashes, public certificate encodings and signature blobs, signing
key custody, restricted principal visibility/grants, proxy identity/ACLs, ordered installation,
the precise disposable cases and retained evidence locations. Key/proxy provisioning, permission
changes, root executions, provider operations and deployment need their own listed G4 operations.
The Bot machine still has no pull from this work. G5 acceptance is a separate operator decision.

Before installation rollback is continued non-installation. Later reversal closes admission and
drains/reconciles owned work first; it must use the original exact packet, unchanged delivery
marker/signatures/grants and an unmapped entry role. The inverse removes only delivery-owned
privileges/principals/signatures and retains certificates and all data/evidence. Unexpected drift,
interrupted retirement, uncertain requests or delayed-effect ambiguity requires explicit journal
recovery/reconciliation. It never permits claim release, old-writer reuse or a blind retry.

All prior invariants remain: immutable running A, eligible pending coalescing, fairness and daily
ordering, registration-aware intents, source/endpoint/UpdateID contracts, full S10C provenance
and spool/nested ownership, exact CAS, append-only dispositions and byte-exact receipts, P/Q/R,
9,000,000-cell parts and 8/16 bounds. S6 gates and both uncertain publications remain open and
retained. S8A's six scripts, S8B's 50 cases and actual-restore/offline-history distinction, and S8C's
seven local checks remain separate. Shutdown drains owned delivery; uncertainty retains claims.

## S11 additional SQL permission scope decision — 2026-09-24

The completed coordination-permission checkpoint passed 434 guarded tests. Continuing the wider
writer trace exposed a separate source-design gap: existing caller-context legacy procedures perform
DDL, dynamic SQL, bulk import and file claim/archive operations. Restricting the evidence tables is
not a complete least-privilege contract for those roots. The installed privileges and execution/proxy
identities are unproven; do not label this an observed production failure or silently grant broad access.

Approve or reject the [additional local SQL privilege-isolation proposal](integration_contract_and_consumer_matrix.md#s11-legacy-sql-privilege-isolation-proposal--2026-09-24)
with its [exact file manifest](integration_implementation_manifests.md#s11-legacy-sql-permission-scope-amendment--2026-09-24).
The recommendation is source-authored module signing/countersigning and exact readiness checks for
the existing call graph, with no business procedure rewrite. This introduces a certificate/signature
delivery contract beyond the approved evidence-ledger SQL file set, so it needs a scope decision.
Approval would cover local source/static/offline work only; it would not provision keys or authorize
installation, changed grants, proxy/host operations, real imports/exports, publication or activation.

| Layer | What is established now | Required next evidence/work |
|---|---|---|
| Fixed coordination | Version-2 object/column permission checks and 434 guarded tests | Later exact installation observation |
| Legacy source dependencies | Fourteen scan queries matched to thirteen authoritative SQL objects; seven procedure roots and 37 lexical candidate modules retained with exact hashes/lines | Approved privilege-isolation authoring; complete semantic/dynamic closure, precise grants/signatures and broader source/capture readiness |
| SQL transactions/server/host | Source shows existing caller-context DDL, xp_cmdshell/file operations and bulk import; no execution | Separately approved disposable permission/transaction cases, actual restore, exact identities/ACLs and server/proxy capabilities |
| Trusted issuer/runtime | Origin, closed-journal and five fixed probe primitives remain authored; factories remain closed | Complete trusted issuance, real caller composition and independent deployed writer exclusion |
| Delivery/acceptance | All pending work, archive identities and prior evidence retained | Settled regression, separate Bot/SQL Changes reviews with Deep off, authorized Git delivery, operator-owned G4 and G5 |

No further export samples or account inventory are needed for this scope decision. The earlier
statement that approved local work needs no further approval still applies to that existing scope;
this new certificate/signature delivery layer is the additional decision. Rollback remains continued
non-installation. Keep every claim, journal, byte-exact receipt, retained S6/S8 item and both uncertain
publications. No permission mismatch may be bypassed with db_owner, a privileged second Bot login,
a Boolean coverage flag, blind retry or an assumed successful predecessor deployment.

## S11 fixed coordination permission continuation — 2026-09-24

Version 2 now checks the fixed export objects' effective object and column permissions for the
authority and Bot reader profiles. Both authority and enrollment entries reject a mismatch before
creating a session, evidence store or provider child. See the
[source/test evidence](release_evidence_log.md#s11-fixed-coordination-permission-contract--2026-09-24).
This closes the fixed budget/preparation/domain permission-check gap identified in the previous
checkpoint. It does not establish installed grants or whole-application readiness.

| Boundary | Current evidence and remaining requirement |
|---|---|
| Fixed export coordination SQL | Source map, exact authoritative object definitions, parsed read-only metadata queries and 434 offline tests; no SQL execution |
| Broader application SQL | Import procedures and configured legacy/scan capture dependencies still need complete source-derived readiness and caller composition |
| Installed SQL and transactions | Separately approved exact target, principals, effective grants, definition fingerprints and transaction outcomes remain G4 evidence |
| Trusted ProofID and complete runtime | Independent complete writer/deployment coverage, fixed issuer orchestration, factories, every real caller and owned-delivery shutdown bindings remain implementation work |
| Provider and deployment | Both credential-holding hosts, human owner, old-writer termination, actual ACLs and no-delayed-effects proof remain unobserved; private clear/readback still precede reuse |
| Delivery and acceptance | Final settled regression and separate exact Bot/SQL Changes reviews, Deep off, precede authorized delivery; exact G4 and G5 remain operator-owned |

No new inventory answer or approval is needed for the remaining authorized local authoring.
No grant, credential, provider audience or factory activation changed. Rollback remains continued
non-installation with every claim, receipt, journal and uncertain publication retained. Do not
downgrade to a version 1 observation to bypass a permission mismatch. Resolve source/installation
drift under its exact later approval; uncertainty continues through reconciliation, never replay.
Mandatory Bot/SQL document grouping and all predecessor open gates remain unchanged.

## S11 exact proof acknowledgment continuation — 2026-09-24

The approved local DAL now requires a complete typed proof request and exact acknowledgment
after the SQL batch finishes. Lost COMMIT acknowledgments, changed proof identities and altered
receipt text remain uncertain, with no automatic issue retry. See the
[source/test record](release_evidence_log.md#s11-exact-proof-persistence-acknowledgment--2026-09-24).
This is a persistence check and cannot supply trusted finality or external-writer coverage.

| Remaining boundary | Local implementation or later evidence |
|---|---|
| Trusted ProofID producer | Fixed orchestration of authenticated origins, every closed request, fresh probe/snapshot and independently established deployment coverage remains to be composed; arbitrary flags/callbacks remain invalid |
| Actual runtime and shared callers | Complete factories, uploads/commands, scheduled/configuration/preparation writers and shutdown bindings remain local implementation work |
| Application SQL permission checks | Evidence-role checks exist; exact authority budget, enrollment preparation and Bot domain permissions still need complete source-derived profiles and readiness wiring |
| Installed SQL and transactions | Exact target/principal, grants, installation fingerprints and actual transaction outcomes remain separately approved G4 observations |
| Provider/host exclusion and finality | Both credential-holding machines, named human owner, old processes, current ACLs and all request outcomes remain G4 coverage; reported inventory alone does not prove them |
| Release acceptance | Final settled offline regression and separate Bot/SQL Changes reviews, Deep off, precede delivery; exact G4 execution and G5 acceptance remain operator-owned |

No additional user information is required for the remaining approved local authoring. This
continuation changes no SQL source, installed principal, credential, provider audience or factory
activation. Rollback remains continued non-installation with every claim, journal, receipt and
uncertain publication retained. A failed acknowledgment must be reconciled by its exact identity,
never by replaying a provider action or assuming an absent read means an in-flight issue cannot
commit later. Mandatory document/archive grouping remains settled and unchanged.

## S11 origin-bound probe continuation — 2026-09-24

The approved local probes now require exact authenticated enrollment origins for the complete
registered pool before provider admission, bind the origin digest into sealed observations,
and recheck origins followed by the current snapshot before returning. Missing origins or drift
remain unresolved; no adoption, historical reconstruction, ProofID or release follows.
See the [exact source/test checkpoint](release_evidence_log.md#s11-origin-bound-reconciliation-probes--2026-09-24).

This closes an origin-to-probe integration gap. Complete trusted issuance, actual runtime/caller
factories and deployed writer exclusion remain required. No SQL source changes in this continuation.
Final regression and separate Bot/SQL Changes reviews, Deep off, precede delivery; exact G4 and
operator G5 remain separate. Rollback is continued non-installation with all claims/data/evidence
retained. The confirmed anyone-with-link Viewer audience and both-host inventory remain applicable.

## S11 audience decision resolved — 2026-09-24

The operator confirms **anyone with the link — Viewer** and reports no secret output content.
Bind published output registrations to the existing public_viewer contract: anyone/reader with
allowFileDiscovery=false. The audience question in the historical coverage table below is now
resolved; actual ACL readback remains a later G4 observation. No sharing-policy amendment or
new runtime/SQL authoring follows from this answer. Preserve the agreed private enrollment and
private clear/readback lifecycle before reuse, along with all writer termination and reconciliation
requirements. No live permission change or release operation is authorized or performed here.

## S11 reported writer inventory and G4 coverage — 2026-09-24

The operator reports one Bot instance, Discord-upload imports only, no other import jobs/manual
mutation tools, a service-account credential on the Bot machine and development PC, no generated
output edits after upload, and read-only player sharing. Shared coordination is their preferred
treatment. The supplied account identifier is held in the local operator inventory artifact;
effective access and deployed processes remain unobserved. See the [evidence record](release_evidence_log.md#s11-account-and-host-inventory-response--2026-09-24).

The recommended normal production writer is the Bot machine's separately supervised authority.
Development remains offline or uses isolated test resources, with exact exclusion of its production
write capability reviewed and evidenced before production admission. Merely promising not to run
a script, retaining an accessible production key, or changing a coordination flag does not establish
that boundary. Participating development instead needs a registered local authority and the same
SQL coordination/storage contracts; no such second runtime is selected or activated here.

| Surface | Current evidence | Exact later closure required |
|---|---|---|
| Normal provider account | Email supplied; credential reported on two machines | Pin account/project, authorized credential identities, both host identities and all permitted users/processes; protect the authority credential and exclude direct Bot/legacy/development fallback |
| Human owner/enrollment | Admin creates current sheets; no later output edits reported | Identify approved owner and separate enrollment credential profile; verify grants and recorded origins for new managed files; do not adopt existing files or treat player Viewer status as owner exclusion |
| Player audience | Read-only for all players reported | Resolve anyone-with-link versus named/group viewers, then bind exact audience/file registrations and readback; no inferred public-sharing change |
| Bot and SQL writers | One Bot/no other jobs or mutation tools reported; source caller map exists | Bind all uploads, commands, scheduled/configuration work and preparation SQL producers to the reviewed runtime; independently verify installed principals, jobs and exclusion on the exact target |
| Termination and recovery | Source closure/probe machinery; no deployed observation | Establish exact old process/stream termination, complete request history and final provider outcomes; retain unresolved dispatched mutations and both historical uncertain publications |

The G4 packet must specify, before any operator approval: exact Bot/SQL revisions and targets;
host/service identities and executable/config hashes; credential/access control actions, if any,
on both machines; provider account/files/audience; installed schema and effective grants; private
spool/evidence ownership; start-closed/drain/reconciliation sequence; bounded tests; stop conditions;
and evidence retention/rollback. Choose actual controls and operations in that packet; this note
does not authorize reading/changing keys, enumerating live provider/SQL state, stopping processes,
installing anything or pulling/restarting the Bot machine.

Credential cleanup cannot substitute for complete historical request evidence or establish that
an already dispatched mutation cannot finish later. Preserve claims and reconciliation for unknown
effects. If G4 exclusion or readback fails, keep admission closed and retain all artifacts; do not
fall back to an uncoordinated client, another account/pool, blind retry or prior mutable writer.
G5 acceptance remains operator-owned after the exact approved G4 evidence is available.

This clarification requires no new SQL authoring or runtime behavior by itself. Existing local
implementation approval continues for the unfinished trusted issuer and complete caller composition.
Separate settled Bot/SQL Changes reviews with Deep off and final regression still precede delivery.
Mandatory document/archive grouping and all retained predecessor evidence remain unchanged.

## S11 approved fresh-file enrollment continuation — 2026-09-24

The operator approved the enrollment amendment. New dedicated files now have an authority-only
source path from a fixed recorded creation, through exact returned-file binding and closed child,
to an append-only eligible origin after the fixed Editor grant/private readback. Interrupted or
unknown operations retain preparation ownership and all evidence; there is no replay, adoption,
name search, deletion, automatic registration or activation. Existing files with unproven history
remain blocked. Prior proposal-only wording below is retained as historical evidence.

See [the enrollment source/evidence checkpoint](release_evidence_log.md#s11-fresh-file-enrollment-source-checkpoint--2026-09-24).
This establishes authored origin machinery, not deployed exclusion of every writer or provider
finality. Trusted ProofID issuance, final shared-caller composition and readiness remain pending.
Continue those under existing local implementation approval. Separate settled Bot/SQL Changes
reviews (Deep off), final full regression and exact operator-owned G4/G5 gates still apply.
Mandatory Bot document/archive grouping and separate SQL delivery remain unchanged.


## S11 drain and protected registration continuation — 2026-09-24

The approved local source now provides sealed rollover-drain observation, exact legacy/configuration
authority streams and immutable account/file/configuration registration. The independent launcher
requires that registration and checks scope before child/stream creation; recorded configuration
reads load no Bot provider credential or fallback client. These observations do not issue ProofIDs.

See [exact twelve Python paths, validation and limits](release_evidence_log.md#s11-drain-legacy-streams-and-protected-registration--2026-09-24).
The five existing Bot documentation paths changed additively. Other pending Bot bytes and all SQL
bytes/deletions remain unchanged; the exact checkpoint records preserve original document and
archive identities, indexes and comparison anchors. Mandatory document grouping remains settled.

The [initial file enrollment amendment](integration_contract_and_consumer_matrix.md#s11-initial-file-enrollment-additional-implementation-proposal)
is a concrete additional implementation proposal, not approved code: establish file origin through
recorded fresh creation, preserve the named human-owner contract with a separate narrowly scoped
owner-authorized credential profile, and add one SQL origin entity/transition API using existing
preparation ownership. It includes exact proposed Bot/SQL paths, tests, risks, rollback and the
source-only approval boundary. Its wider credential and persistence scope requires an explicit
operator decision before authoring. Existing files without authentic prior history remain blocked.

Trusted issuance, complete actual-caller factories and application/deployment readiness remain
unfinished; no generic callback or operator Boolean can substitute for them. Production admission
stays closed. Final separate Bot/SQL Changes reviews (Deep off) follow settled authoring. No live
execution, OAuth, credential change, Git publication, bot-machine operation or activation occurred.
S6 open gates, both uncertain publications, S8 evidence and G4/G5 boundaries are preserved.


## S11 sealed rollover completion observation continuation — 2026-09-24

The approved local source now verifies the original protected drain proof, every original private/
clear/setup phase stream, and a fresh sealed completion probe. Original index emptiness remains
distinct from its current marker; current slots must match the original clear sheet identities.
Unknown outcomes, missing phases, stale ownership or changed catalogue/journal evidence fail closed.
No ProofID, retry, adoption or settlement is produced.

See [exact source and limits](release_evidence_log.md#s11-sealed-rollover-completion-observation-checkpoint--2026-09-24).
Four Python paths plus these three Bot documents changed; the final 17-file suite passed 968 tests
with six gated skips. Lint/format/architecture/deferred/routing/import/registration and both repository
whitespace checks passed. All other pending Bot paths and every SQL byte/deletion remain exact;
all 59 original documentation identities and both exact archive pairs are retained.

Rollover drain, trusted proof issuance with complete writer/deployment coverage, actual-caller/
shared-writer composition, immutable bindings and remaining readiness gates are still unfinished.
Full pytest and separate exact Bot/SQL Changes reviews with Deep off follow the settled patch.
Factories remain closed, local implementation approval persists, and exact G4/G5 operations remain
operator-owned. Document grouping and retained predecessor/uncertain evidence are unchanged.
No live operation, publication, deployment or bot-machine action occurred.


## S11 complete rollover setup readback continuation — 2026-09-24

The existing rollover setup writer now verifies the whole final index through a fixed read-only
evaluator. The expected literal marker cannot hide extra tabs, cells, notes, metadata, k98 properties,
description or sharing. A successful result binds the current manifest and sheet ID, never claims
the marker-bearing index is empty, and never authorizes retry or proof issuance.

See [exact source and limits](release_evidence_log.md#s11-complete-rollover-setup-readback-checkpoint--2026-09-24).
Four Python paths plus the three Bot checkpoint documents changed. The 38 new setup cases and
the affected 16-file suite passed (893 tests, six gated skips). A subsequent historical-proof
JSON-type comparison fix passed all 63 recovery cases, including integer/float-for-Boolean rejection;
the 893-test run predates that final narrow fix. Other pending Bot files and every SQL
byte/deletion remain exact. Existing validation, archive identity and document grouping requirements
are preserved. No live operation, Git publication, deployment or activation occurred.

Complete trusted drain/completion producers, other ProofID orchestration and writer coverage,
actual-caller/shared-writer composition, immutable bindings and remaining readiness gates are still
pending. Full pytest and separate exact Bot/SQL Changes reviews with Deep off follow settled
composition. Factories stay closed; local implementation approval persists; G4 and G5 remain
operator-owned.


## S11 interrupted-retirement observation continuation — 2026-09-24

Approved local source now validates complete interrupted-retirement journals, reloads the original
protected SQL retirement ProofIDs, observes the current publication and all pending slots, and
replays their sealed private evidence. Exact old/nested ownership, disposition/proof bytes, catalogue
and snapshot changes fail closed. Current emptiness does not establish no-delayed-effects or grant
clear/recovery authority. Missing historical ProofIDs remain unresolved and retained.

See the [exact source and evidence](release_evidence_log.md#s11-interrupted-retirement-observation-checkpoint--2026-09-24):
three Python paths plus these three Bot docs; 855 passing affected tests, six gated skips, and
lint/format/architecture/deferred/security-routing/import/registration checks. All pending SQL bytes
remain unchanged. Full pytest and separate Bot/SQL Changes scans, Deep off, remain final gates.

Trusted proof issuance with complete writer/deployment coverage, rollover evidence, complete actual
caller/shared-writer wiring, immutable registration/storage bindings and remaining readiness work
are outstanding. Factories remain closed. The local approval persists; Git publication, exact G4
operations and G5 acceptance remain separate. Document grouping, retained uncertainties and exact
archive identities are preserved. No live execution, deployment or bot-machine action occurred.


## S11 ordinary-retirement observation continuation — 2026-09-24

The approved local implementation now has a fixed read-only ordinary-retirement evaluator and
sealed-probe sequence, bound to the exact pool snapshot consumed by retirement. It validates the
new publication, old unretained assignment/content and byte-exact receipt; closure, catalogue and
snapshot changes fail closed. No ProofID, release, clear or no-delayed-effects claim is produced.
See the [exact files and evidence](release_evidence_log.md#s11-ordinary-retirement-observation-checkpoint--2026-09-24).

Five Bot Python paths and these three Bot documents changed; all SQL pending bytes remain unchanged.
Affected validation: 794 passing tests and six gated skips, plus lint/format/architecture/deferred/
security-routing/guarded imports/command registration and both Git whitespace checks. Final full
pytest and separate Bot/SQL Changes scans (Deep off) await the completed implementation target.

Remaining real work: trusted ProofID producers with complete writer/deployment coverage, interrupted
retirement and rollover evidence, actual-caller/shared-writer composition, immutable registration/
storage bindings and remaining readiness checks. Factories remain closed. Local work needs no new
approval; exact Git publication, G4 operations and G5 acceptance remain separate operator decisions.
Retained uncertainty, predecessor evidence, exact archive identities and settled document grouping
are unchanged. No live execution or bot-machine action occurred.


## S11 foundation SQL startup-contract continuation — 2026-09-24

The independent authority's explicit launcher now checks a protected approved SQL contract before
session/store/provider-host creation. Fixed read-only DAL observations cover the required migration
checksums, 28 object definitions and effective evidence permissions; missing, drifted, opaque or
unsafe observations fail closed. Expected hashes cannot be learned during startup or supplied via
Bot IPC. See the [source checkpoint](release_evidence_log.md#s11-foundation-sql-startup-contract-checkpoint--2026-09-24)
for exact five Bot paths, 747 passing offline tests, nine parsed SELECT batches and execution limits.

This is one readiness prerequisite. Trusted ProofID issuance, complete caller/shared-writer and
registration/storage composition, remaining application permissions and actual deployment coverage
remain outstanding. The existing local implementation approval persists; no additional decision is
needed for local edits/tests. Factories remain closed, and Git publication, exact G4 operations and
operator G5 remain separate. Preserve all earlier evidence, uncertainties and settled document
grouping. No SQL/provider/Discord/containment/deployment operation or bot-machine change occurred.


## S11 sealed publication observation continuation — 2026-09-24

The fixed confirmed-publication evaluator and complete probe/sealed-replay sequence are authored
and tested locally. Existing coordinated receipt bytes are preserved exactly. Interrupted nested
retirement permits only the exact one-version transition for an uncertain read-only probe;
mutation admission remains current-version only. See the [source checkpoint](release_evidence_log.md#s11-sealed-publication-observation-checkpoint--2026-09-24)
for exact Bot/SQL paths, 689 passing offline tests, 125 SQL static assertions and remaining limits.

Trusted ProofID issuance for all settlement kinds, immutable readiness and complete actual-caller/
shared-writer composition remain implementation work. Source tests do not prove pre-S11/external
coverage, SQL installation/transactions, Windows containment, provider finality or deployment.
Both runtime factories remain closed. Existing local implementation approval persists; separate
Bot/SQL Changes reviews (Deep off), final full regression, exact G4 approvals and operator G5
remain required. Preserve all prior evidence, exact archive sides, document grouping and retained
uncertainties. No activation, publication, provider/SQL operation or bot-machine change occurred.


## S11 complete recorded-catalogue continuation — 2026-09-24

Proof membership now fingerprints every recorded stream touching registered files, with private
journal validation and independent SQL issuance/settlement rechecks. A writer opening and closing
after the probe invalidates settlement even if the domain snapshot is unchanged. Sealed probe
replay binds existing readback helpers to exact recorded requests without new provider calls.
See the [source-only checkpoint](release_evidence_log.md#s11-complete-recorded-catalogue-checkpoint--2026-09-24)
for exact paths, 653 passing offline tests, SQL's 121 static assertions and remaining limitations.

Complete trusted outcome/ProofID orchestration, pre-S11/external-writer coverage, immutable
readiness and complete actual-caller composition remain required. Catalogue lock cost and all
installation/transaction/provider/containment behavior remain unproven. Factories stay closed;
G4/G5 and Git publication remain operator-owned. Preserve all earlier evidence and settled Bot/
SQL document grouping. Rollback is non-installation and retention of claims and data.


## S11 adapter and retirement lifecycle continuation — 2026-09-24

Typed provider requests now cover actual bounded batch readback and exact rollover metadata
cleanup. Injected new-source delivery closes before retirement/final confirmation; each ordinary
or nested-recovery clear closes before audited reuse, with an in-transaction active-stream gate.
Fresh job/registration/journal scopes preserve exact ownership and forbid delivery replay.
See the [source-only checkpoint](release_evidence_log.md#s11-adapter-and-retirement-lifecycle-checkpoint--2026-09-24)
for exact paths, 611 passing offline tests and the separate SQL authoring change. Trusted proof
issuance/historical coverage, immutable readiness and complete production caller composition
remain incomplete. All configured production factories remain closed; no G4/G5 or publication
authority is inferred. Retain every prior evidence entry and the settled Bot/SQL document grouping.
Rollback remains non-installation and retained claims/evidence; there is no live change to undo.


## S11 closing-probe continuation — 2026-09-24

The closing-operation observational scope now exists in uninstalled SQL source and the explicit
Bot binding, with repeated registration/owner/version checks and mutation rejection. See the
[source-only checkpoint](release_evidence_log.md#s11-closing-probe-binding-checkpoint--2026-09-24).
The complete trusted issuer, historical coverage, retirement/recovery composition, immutable
deployment readiness and all-caller bindings remain implementation gates. Runtime transaction,
permission, provider and containment behavior are unproven. G4/G5 remain operator-owned; current
rollback remains non-installation and retention of all local work and evidence. No activation.


## S11 proof-consumption continuation — 2026-09-24

Six S11 settlement paths now resolve trusted SQL ProofID in their existing locked snapshot
transactions. Private-journal verification is implemented as a prerequisite to proof issuance;
the complete issuer, launcher and caller composition remain unfinished and disabled. See the
[current continuation evidence](release_evidence_log.md#s11-continuation-trusted-proof-consumption--2026-09-24)
for exact files and source-only validation. Earlier checkpoint statements remain historical.


## S11 implementation status — 2026-09-24

Implementation approval has been received for the expanded proposal; local foundations are incomplete and disabled. G4 and G5 remain operator-owned and unapproved. Do not install, start or activate the current patch. Required remaining implementation and the source-versus-runtime evidence distinction are in the [checkpoint](release_evidence_log.md#s11-approved-implementation-checkpoint--2026-09-24). Current rollback is preservation without activation; no live changes need reversing.


## S11 proof-design approval and rollback — 2026-09-24

**The approved mechanism-design pass is complete; implementation and operations remain separate.**
The recommendation is a separately supervised Windows export authority, approved provider
children, an authenticated local control channel, and additive SQL session/stream/request/event/
proof records. It closes genuine C1/C2 implementation gaps; it does not turn C3–C6 runtime
unknowns into proven facts. See the [mechanism contract](integration_contract_and_consumer_matrix.md#s11-proof-mechanism-decision-proposal--2026-09-24)
and [exact proposed Bot/SQL manifest amendment](integration_implementation_manifests.md#s11-proof-mechanism-manifest-amendment--2026-09-24).
The earlier statement that no SQL requirement was established is now superseded by this proposal.
No executable delta has been authored in either repository.

### Exact next approval and sequence

1. Approve or revise the proposed mechanism: independent Windows authority; five additive SQL
   evidence entities and four transition/issuance procedures; all affected callers routed through
   the authority; unknown dispatched mutations remain blocked, potentially indefinitely. This
   is the next implementation-scope decision. Approving it does not approve G4/G5 or Git publication.
2. Within that bounded scope, finish physical SQL types, keys, indexes, grants and transaction
   contracts before dependent Bot authoring. Author/review the SQL unit separately, then the
   disabled Bot authority unit, then complete composition. The exact paths and test categories
   are in the manifest amendment. Any additional path/behavior requires an explicit scope amendment.
3. Review deterministic local tests and static SQL contracts; perform separate Changes reviews,
   Deep off, on the exact Bot and real SQL deltas. Transaction, Windows process, provider and
   installation tests require their separately approved execution targets and evidence packets.
4. Authorize publication only after exact delivery review. The first genuine authorized Bot
   implementation PR carries every pending Bot document, pack/starter, closeout and both archive
   move sides. SQL closeouts belong in its next genuine SQL implementation PR. Preparation remains
   pending if no implementation is approved. Verify filename plus previous_filename, or exact
   merged/content/absent-at-base proof for every identity; counts never close this check.
5. Fill and approve exact G4 operations, then operator-owned G5 acceptance. No inferred deployment,
   admission, serving, source switch, predecessor rerun or bot-machine action follows from design.

### Additional G4 fields required by this mechanism

The existing target packet still applies. Add exact authority executable/revision/protocol;
Windows host and service/task identity/SID; child Job Object policy and launch configuration;
pipe name, DACL and peer checks; provider credential ownership and excluded legacy identities;
SQL bot/authority principals and effective grants; private evidence store identity, ACL, encryption,
retention and tested restore; session/stream registration; supported method/response validators;
and bounded shutdown, recovery and observation operations. No values are selected here.
Every shared writer and every nested/offloaded caller must be accounted for before admission.

### Rollback and unavailable evidence

Close admission first. Drain owned delivery where safe; freeze streams and establish exact old
provider-child termination. Retain claims, append-only events, spool, receipts and unresolved
requests. Never roll back by replaying unknown mutations, deleting evidence tables, force-releasing
claims, clearing destinations, or restarting an old bypass writer. New SQL evidence is additive:
retain it while reverting code to a compatible disabled state. Resume legacy writes only after a
separately approved ownership/credential exclusion and reconciliation decision. Rollback is not
proof that an escaped provider request cannot complete later.

Previously recorded temporary recovery archives are unavailable in this session. The fresh current
snapshot preserves repository evidence but cannot replace missing historical PR rename metadata
or recovery artifacts. This is an open delivery-evidence gap; recover the originals or establish
per-file equivalent immutable merged/content/absent-at-base proof before publication approval.
S6 open gates and both uncertain publications remain unchanged, with all retained data preserved.


## S11 preparation and release approval packet — 2026-09-24

**Preparation/design approved; runtime implementation, execution, publication, deployment and
activation remain unapproved.** The operator approved the initial S11 scope's preparation-only
next step. This section supersedes older next-step wording, without changing predecessor results.

Bot HEAD/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`, production/main
`3dbe63e7a47175df85ed17814ea06f9dd3d130b7`, SQL HEAD/origin main
`2352a898881d4b74d6eec153bb3cb381d6162041`; both branches main, indexes empty. These are
comparison anchors, never reset instructions. No changes have been pulled to the bot machine.

### Release blockers and evidence classification

| Gate | Current finding | Closure required |
|---|---|---|
| C1 production composition | Existing ready hook calls register_exports without factory; both configured factories raise; legacy runtime is only injected | Reviewed composition and all actual producer contexts, preserving disabled defaults |
| C2 trusted proof producers | Rollover/reconcile/retirement consume proof dictionaries; no production authority/probe composition found | Independently trusted process-incarnation/request-outcome evidence plus exact provider readback; unsupported outcomes remain blocked |
| C3 installed SQL | S10A has retained disposable execution; S10C/D/E have authoring/static evidence | Exact target catalog/history, backup/actual restore and authorized installation/transaction evidence |
| C4 all writers | Repository caller map exists; deployed SQL jobs, scripts, other hosts/account consumers are unknown | Exact version/account/resource inventory; each writer coordinated or verifiably excluded |
| C5 provider/Discord | Offline clients/callbacks and retained S6 measurements | Newly affected integrated SDK/ACL/interruption/rollover/operator evidence at approved new identities |
| C6 deployment/G5 | Source merges/local pulls only | Explicit production revision/process/config/schema association, bounded G4 and operator G5 |

See the [composition/proof design](integration_contract_and_consumer_matrix.md#s11-composition-and-trusted-proof-design--2026-09-24)
and [exact proposed implementation/tests](integration_implementation_manifests.md#s11-preparation-and-proposed-implementation-manifests--2026-09-24).
C1/C2 are genuine implementation/design gaps. C3/C5/C6 are unproven runtime facts, not reasons to
invent code. C4 needs deployment evidence as well as complete composition. No current SQL delta
is established. No blanket approval follows from S11 or from flipping SourceRouting.Enabled.

### Composition and installation order

1. Pin the proposed runtime revision and immutable deployment manifest; enumerate every process,
   account/project, SQL source/snapshot writer, destination alias and storage owner. Preserve
   configuration and source evidence without publishing secrets.
2. Keep admission/serving closed and stop or exclude every old writer before ownership migration
   or admission. Existing legacy behavior while the flag is false is not a coexistence guarantee.
3. Establish exact S8 prerequisites → S10A → S10C → S10D → S10E schema compatibility on the
   approved target. These are dependencies, not a command to rerun predecessor migrations. Read
   actual installed metadata and apply only separately approved missing work with backup/restore
   and lock bounds. Deploy migrations, not standalone schema snapshots. Preserve receipt bytes.
4. Provision the separately approved private durable spool outside Git and bind its storage owner;
   verify immutable complete captures. No temp or credential-relative authoritative spool.
5. Compose all three consumers and config reads with preparation/output-operation aware DALs,
   request budgets, registered provider clients, trusted probes and explicit retirement recovery.
   Bind every manual, scheduled and upload task; reject any incomplete version or registration.
6. Under G4, associate installed source and configuration with exact process incarnations; observe
   startup closed, then perform only the approved bounded admission/serving operations. Opening
   season intake, selecting a source, enabling serving and admitting exports are separate facts.

### G4 operation packet — not executable until exact fields are filled and approved

No new database, account, provider file, process or Discord identity is selected by this document.
Do not copy a retained S6/S8 identity into an empty field. The local SQL identity proposal and
backup/restore requirements are in the [SQL packet](../local_sql_development.md#s11-exact-target-packet--2026-09-24).

| Required field | Current value / required source |
|---|---|
| Packet ID, approver, UTC window, operator and abort owner | Unassigned; operator approval record required |
| Bot/SQL source hashes and dependency/SDK versions | Current source anchors above only; exact execution builds and hashes unassigned |
| Server, database, engine/collation/compatibility, data/log paths | Historical K98DEV reference only; exact new target and current identity verification pending |
| Backup and actual restore | New explicit backup path/hash and separate restore database/files; evidence and validation commands pending |
| Service account/project, coordinator AccountKey and permitted credential reference | Unassigned; derived/verified identities, never secret material in this packet |
| Index, slots, legacy/scan/config files and ACLs | Unassigned; exact IDs, owner/Editor/canShare/audience, alias disjointness and registration hash required |
| Season/ChoiceID, pool/epoch, synthetic inputs and case IDs | Unassigned; disjoint from retained publications, files and database rows |
| Spool root, storage owner, evidence root, ACLs and backup | Unassigned; private durable provisioned paths outside Git with worker affinity |
| Host/service/task/process incarnations and every external writer | Unassigned; exact running revisions, exclusion controls and supervisor authority required |
| Trusted proof producer/request-outcome authority | Unassigned; reviewed source/identity and authentic durable evidence required; no timeout-based absence |
| Discord guild/channel/actor/roles/message handling | Unassigned; explicit non-production destination, fresh authority, mention behavior and bounded actions |
| Operations, budgets, sequencing and failure triggers | Allowlist below is a proposal; exact commands, inputs, hashes, limits and expected results must be approved |

Proposed operation groups must be independently selectable; SQL approval never implies provider,
Discord or bot-machine approval:

| Group | Permitted actions only after exact approval | Required evidence / stop condition |
|---|---|---|
| G4-SQL | Target identity/catalog reads; approved new fixture setup; backup and actual restore; specifically listed installation and new transaction cases | Identity mismatch, schema drift, missing restore evidence or unexpected locks stop before further mutation; preserve state for forward fix |
| G4-PROVIDER-READ | Exact registered metadata/ACL/content/pointer reads through reviewed paced probe path | Any alias/ownership/audience mismatch or unresolvable escaped request blocks mutation |
| G4-PROVIDER-WRITE | Explicit synthetic input/generation, bounded private writes/readback, approved grants/pointer and interruption points | Ambiguous SDK/checkpoint result retains every claim; no automatic replay |
| G4-RETIRE | Exact old/new KVK/pool/epoch/file list, confirmed preview, drain/reconciliation, private ACL/clear/readback and journal recovery cases | Prove old/nested writers and no delayed effects first; partial or unknown outcome remains blocked; no retained S6/S8 target |
| G4-DISCORD | Existing grouped export/status/reconcile/rebuild/rollover smoke for exact actor/destination | Fresh permission checks, zero-provider confirmed no-op, read-only status, expiring preview/durable confirmation; no extra automatic daily send |
| G4-DEPLOY | Separately specified production-main pull/restart/config operations | Pin final merged revision, old-writer exclusions and rollback before action; source merge is not deployed-head evidence |

The exact command packet must be presented for operator review before execution. Empty fields,
wildcard targets, default connection fallbacks and environment authorization strings alone cannot
grant authority. Current preparation runs only offline documentation checks.

### Rollback and preservation

Close new admission and stop participating producers before toggling composition; simply setting
the flag false may restore uncoordinated legacy paths. Drain owned delivery through pacing,
readback and confirmation. If it cannot drain, preserve claims and all owner/request evidence;
neither process death nor lease age grants release. Reconcile exact jobs/operations explicitly.

Retain fixed season choice, sealed UpdateID/config/endpoint history, source facts, full-vector
intents, spool bytes, append-only assignments/dispositions and byte-exact receipts. Public serving
may become unavailable or an explicitly pinned previous publication/version with honest labels;
never silently fall back to legacy. A downgrade is blocked while it cannot understand retained
job/preparation/output-operation or nested retirement ownership.

SQL rollback is reviewed forward repair. Do not drop populated tables, rewrite historical receipts,
guess legacy mappings or restore over retained/live data as an improvised rollback. Restoring a
backup proves recoverability only for its approved separate target; it does not revoke remote writes.
Rollover closes admission and drains/reconciles; old-writer termination and private clear/readback
precede audited reuse. Interrupted retirement uses hashed journal recovery, exact nested CAS and
no-delayed-effects proof, read-before-clear, then fresh publication proof after owner revocation.

Keep S6-OPS01/PERF01/CAP01 open, both uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`,
and every retained database/file. P/Q/R includes protected and quarantined assignments; capacity
cannot be created by relabeling generations or deleting evidence. Preserve 9,000,000-cell parts
and 8/16 bounds. No new duration cap or predecessor reapproval is requested.

### Exact approval checkpoints

| Checkpoint | Status | Authority granted only by that checkpoint |
|---|---|---|
| S11 preparation/design | Approved 2026-09-24 | Eight-document preparation and offline documentation validation; this packet |
| Architecture/proof decision | Pending | Select authentic supervisor/request-outcome evidence mechanism, storage/access model and read-only probe admission; reject any unprovable terminal outcome |
| G3 implementation | Pending | Approve final exact Bot code/test/docs manifest and any separately justified SQL delta; disabled defaults retained |
| Offline handoff/security | Pending for future runtime | Focused/full isolated tests and Changes, Deep off, exact immutable target per repository; not operational permission |
| Git publication/promotion | Pending | Explicit publication with complete per-path union verification; production uses reviewed patch-based promotion |
| G4 | Pending | Only exact packet identities/actions, separately bounded by SQL/provider/Discord/deployment group |
| G5 | Pending; operator-owned | Accept measured outcomes/limits and decide remaining S6 gates and explicit activation |

Next requested approval is the architecture/proof decision and final implementation scope, not
G4. If the concrete proof mechanism needs additional supervisor/schema/config work, amend the
manifest before implementation. All pending docs remain for the next genuine implementation PR.

## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](s10e_closeout_and_s11_handoff.md).
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
See [S10D closeout and exact carry-forward manifests](s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
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
Use the [S10B task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md).
The [S10A closeout and exact carry-forward manifest](s10a_implementation_and_s10b_handoff.md) controls delivery.
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
in synchronized mirror main. See the [canonical closeout and exact carry-forward manifest](s8b_closeout_and_s8c_handoff.md)
for merge/content proof, final offline tests and the distinct historical disposable/runner evidence.
No fresh post-merge SQL or bot-machine smoke, deployment or activation is claimed.

**Next: S8C Intake and Admin Pairing UX in a new chat, initial review/scope only.**
Use the [S8C pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md).
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

[Settled requirements](post_s6_integration_requirements.md); [handoff and exact manifest](post_s6_handoff_log.md); [S7 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

> **2026-09-12 PR #272 routing review correction:** Public runtime routing is an
> OPEN implementation prerequisite. The current code does not consume
> SourceRouting.Enabled to switch ordinary readers to V2. The routing-row update
> below is only a conditional design and must not run until a separately approved,
> reviewed, deployed and accepted public routing consumer exists. Synthetic
> rehearsal acceptance does not close this gap or establish activation readiness.


> **2026-09-12 mirror PR authorization:** Chris Watts explicitly approved committing,
> pushing and opening the complete documentation-only draft PR in K98-bot-mirror.
> This supersedes the preceding pending-PR-permission statements. No merge,
> production promotion or activation is authorized. Rehearsal evidence is accepted;
> unresolved operational gates and all retained uncertain outputs remain preserved.


> **2026-09-12 operator acceptance update:** Chris Watts replied "approved please
> proceed" to the completed rehearsal report. The measured rehearsal outcomes are
> accepted. Outstanding scheduling, capacity/retention and uncertain-publication
> dispositions remain explicit release gates; this is not evidence of their
> resolution. The next proposed external step is the complete S6 documentation
> mirror PR. Its exact commit/push/PR permission is being clarified against the
> earlier explicit prohibition. Production operations remain unexecuted.


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


2026-09-12. **S6 G3 evidence preparation only; stopped at G4. Activation is not ready.**
Chris Watts owns G4 exact-operation approval and G5 acceptance. This document proposes operations;
none has been executed by S6. Read the [evidence log](release_evidence_log.md) and
[S6 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md).
All preceding slices remain accepted, including S5B-REC01. No predecessor rerun is required here.

## 1. Confirmed entry and authority

Local bot main and origin/main: `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`.
Local production/main: `c7e063f02ebe8287a584d0054ea14f91a0c0ecc6`, including S5B fix `e5bbd8f7`.
SQL main and origin/main: `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
These are independently inspected local refs, without fetch; remote freshness and deployment are
not established. Operator reports local pulls complete, successful S5B smoke acceptance and no
bot-machine pull. Recorded synthetic tests predate the merged entry tree; no fresh post-merge
or bot-machine smoke is claimed. Preserve the retained databases and exact historical scan targets.

The [approved architecture](phase_2_contract_and_architecture.md),
[Phase 2B plan](phase_2_implementation_plan.md) and its later accepted endpoint amendment govern:

- B0 freezes eligibility and kingdom attribution: recorded KVK-16 evidence is 5,806 governors,
  36 kingdoms; these are evidence counts, not universal importer limits. B0 scan start is
  operator-attested `2026-08-26 04:07 UTC`; original SHA-256 is
  `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`.
- Exact start/end observations determine each available metric. Missing endpoints remain unavailable;
  intermediate scans are unnecessary for final gain. Player DKP uses T4/T5 kills and total deaths
  with the approved frozen weights. Supplied kingdom/camp metrics and DKP remain authoritative.
- Illustrative start 10: interim `11−10`, then `12−10`; configured end 13: final `13−10`;
  authorized EndScanID update to 14 itself permits replacement `14−10`, without another correction
  command. If 14 is absent, desired config remains pending and the old 13 result is not current final.
  These numbers are examples, not verified live mappings. Either endpoint may change under the
  accepted amendment; end must be >= start. Equal endpoints give zero supported fight scores for
  all frozen B0 members, including absent scan members, and aggregates are not applicable.
- Distinct accepted scans advance ScanID and UTC scan start in order. Byte/semantic re-exports add
  evidence aliases, not scans, revisions, publications or deliveries. Source-content corrections
  remain separately reviewed. Upload time and local time never replace scan start.
- Player endpoint authority does not authorize weight/map/roster changes or aggregate corrections.
  Aggregate revisions supersede rather than sum; overall uses its separate report. Daily SCANORDER,
  legacy KVK_Scan and existing daily three-claim ownership remain separate.

## 2. Release target binding — unresolved before any operation

No S6 server/database, process, workbook, audience, channel, role or filesystem target is authorized.
Historical targets are retained evidence, not reusable S6 execution targets. The proposed rehearsal
database name is `K98_S6_Disposable_20260912` on the historically used local K98DEV instance;
existence, exact connection identity and permission to create/use it have **not** been checked or granted.
Do not connect using this proposal. No default connection or credential discovery is permitted.

| Binding to record privately for G4 review | Current evidence / blocking gap |
|---|---|
| Rehearsal process executable, absolute checkout/artifact root, launch parameters, process/child IDs, shutdown method, database identity and allowed mutations | Unbound. Use a separate synthetic process and dedicated new database/files; never interrupt the bot or reuse predecessor databases. |
| Production SQL server/database, principal and migration history; exact deployed bot checkout/SHA and config fingerprint | Unqueried. Local definitions and operator parity attestation do not prove live state. |
| KVK_NO, source, displayed PeriodID, selected PublicationID, SelectionVersion, RoutingVersion, desired/selected ConfigVersionID | Unqueried. KVK 16 is intended source context; no actual IDs or versions inferred from illustrative scans. |
| B0 RosterID/revision/digest, observation/time-to-scan bindings, Windows rows, approved map and exact weight strings/version | Historical source evidence available; current imported rows and authorization provenance unverified. |
| Config sheet editors, scheduled/manual import paths and ProcConfig/jobs; external SQL/Sheets readers and cleanup jobs | Inventory and readback pending. Include system import identity where a human editor cannot be established. |
| Dedicated index and each slot ID, owner, service-account Editor, canShare, intended audience; protected/shared-file exclusion | Exact provisioned S6 IDs/ACLs unbound. Public Viewer needs explicit audience approval. No provider discovery or provisioning now. |
| Intake channel/guild/uploader/admin identities, private artifact-root ACL, SQL principal rights | Unverified. Existing syntax checks do not prove deployed permissions. Keep identities/credentials outside Git. |
| Backup IDs/UTC/checksums, restore test, recovery receipts/quarantine and prior compatible publication/legacy evidence | No current recoverability proof. Retain originals/configs/publications/receipts; no deletion-based rollback. |
| Capability manifest and CapabilitiesVersion value bound to exact bot/SQL revisions and all consumers | Not yet accepted. SQL stores a string; it is not itself proof that consumers support V2. |

Every private evidence record must identify collector, UTC, exact target/revisions, allowed operation,
before/after state, outcome, evidence path/hash, unresolved uncertainty and Chris Watts's acceptance.
Publish only redacted counts/status and evidence references here, never player rows or credentials.

## 3. Verified local capabilities and proposed release sequence

**Blocking implementation prerequisite — runtime routing consumer is absent.**
At the reviewed bot revision `758d6be163026f0299c05c3ad0bf2c4517c55932`,
`kvk/dal/new_source_config_dal.py:13–28` locks the routing row for configuration,
and `kvk/dal/new_source_admin_dal.py:494–498` creates disabled onboarding rows.
Neither dispatches public reads. `stats_alerts/embeds/kvk.py:154–185` reaches V2
only through an explicit diagnostic `source_selection`; its ordinary path remains
legacy. Setting `SourceRouting.Enabled=1` therefore does not activate public V2
readers. The synthetic export and diagnostic results do not prove public routing.

Before any activation transaction, require a separately scoped, approved, reviewed
and deployed runtime routing implementation covering every intended public consumer.
Its evidence must demonstrate ordinary report/card requests selecting the approved
V2 generation when enabled, preserving approved legacy behavior when disabled,
pinning routing/selection versions for a request, rejecting unavailable/stale or
incompatible source state, and handling cache invalidation/restart and rollback.
Bind the implementation revision and tests to the consumer capability manifest;
explicit diagnostic injection or a SQL flag readback cannot satisfy this gate.
This documentation PR does not authorize that implementation or close this blocker.

Source contracts were checked statically at the entry revisions, using authoritative SQL snapshots.
Deploy reviewed migrations in order, only if live migration history proves them absent and the
operator approves that exact target/operation; never redeploy merely because this list exists:

1. `migrations/20260909_001_kvk_source_observation_facts.sql` — SHA-256
   `4b19c8e54a7555e796c06124640efd27b6838c8360d352bd55265d04bdc1614c`.
2. `migrations/20260910_001_kvk_source_publication_state.sql` — SHA-256
   `2985551c7cac6ba158a38c436389aa13b44fe36235ccf6768b684037cce77fbc`.

Both are additive, backup-required, manual rollback/retain-objects migrations. SQL snapshots are
reference shapes, not deployment scripts. No migration, SQL validator or connection ran in S6.
The SQL repo has no root AGENTS.md or SECURITY.md; its schema/migrations READMEs and
SQL_DATA_MIGRATION_GUARDRAILS supplied the applicable local SQL instructions.

Proposed sequence, each step subject to exact G4 authorization:

1. Bind the target table above; capture current jobs/editors/readers, backups and restore evidence.
   Freeze conflicting new-source writers by an approved maintenance procedure; leave daily systems
   under their existing owners. Establish explicit stop/rollback thresholds before work begins.
2. Validate/deploy required SQL with `SourceRouting.Enabled=0`. Read back migration IDs/hashes,
   expected tables/columns/constraints and permissions. Stop on drift; never repair live data implicitly.
3. Deploy only the accepted private `K98-bot/main` revision after separately authorized promotion
   review. Keep `KVK_SOURCE_INTAKE_ENABLED=false`, `KVK_SOURCE_RECOVERY_ENABLED=false` and
   `KVK_SOURCE_EXPORT_REGISTRATIONS=[]` initially. Capture deployed SHA and effective defaults.
   No bot-machine deployment or restart is authorized by this document.
4. In the separately bound synthetic environment, enable only the explicitly approved private
   capabilities. Exercise the scenario matrix in the evidence log and gates below. Production
   serving stays off. Export tests use dedicated synthetic workbooks, literal RAW writes and full
   manifest/directory/section readback, never protected legacy sheets or real player exports.
5. Accept OPS01/PERF01/CAP01 measurements and the full consumer capability manifest. Reconcile
   all destination fences/receipts and unresolved writes. Confirm restore/rollback paths, then
   refresh routing/selection/config versions for the activation transaction review.
6. Stop unless the runtime routing consumer prerequisite above has been implemented,
   reviewed, deployed and accepted for every intended public reader. Only then obtain
   the separate activation decision for the exact filled preview below. Perform only that
   approved operation, independently read back the committed outcome, and monitor the agreed
   observation window. Chris Watts alone grants G5. A rehearsal approval is not activation approval.

The capability manifest must account for C15–C43 reports/cards/exports and C61/C65 integration,
including twelve report blocks, ALL_WINDOWS/comparisons, exact RAW/CSV precision and versioned
cache/read envelopes. C44–C60/C63 daily/KS4/targets/history/rankings/profile/calendar behavior and
C62 cleanup protection remain regression boundaries. Verify external readers separately; source
presence and prior tests are insufficient evidence of deployed capability.

Config review uses [ENV_REFERENCE](../ENV_REFERENCE.md#kvk-source-recovery-s5b): interval 1–300
seconds (default 30), batch 1–32 (default 8), 0–8 registrations, 2–16 distinct slots per
registration, bounded receipt capacity and protected-file exclusion. Verify the exact process-mode
allowlist entry `proc_config_import:run_proc_config_import_payload` if an allowlist is configured,
and preserve the default worker telemetry cutoff or larger. No configuration value is changed here.

## 4. Activation transaction preview — specification only, not executable

There is no activation helper in the accepted implementation. Do not invent a command or infer
capability from a nonempty database string. The following is the precise transaction review
contract. Exact literal values, audit record and transaction text remain a G4 binding prerequisite;
any new executable helper requires a separately approved bounded implementation manifest.

**This is a conditional routing-state transaction design, not a working activation
procedure for the current code.** The missing public runtime routing consumer in
section 3 blocks execution. A successful row update alone cannot switch readers
or establish activation, even if its SQL predicates and audit requirements pass.

Inputs: approved exact server/database; SourceKey=`snapshot_report_v1`; KVK_NO; displayed PeriodID;
expected disabled routing version R; expected selection version S/publication P; expected desired
and selected config C; publication manifest hash H; accepted capability version V and private
capability evidence hash; actual approving actor A and approval UTC. **All live values are unbound.**

1. Before connecting, verify G4 covers this exact operation and evidence fingerprint, all three S6
   gates are accepted, and backups/consumer/permission evidence matches the intended environment.
   Require the separately reviewed public routing implementation, deployed revision,
   ordinary-reader enable/disable tests and accepted capability manifest from section 3.
   If absent, stop without issuing this transaction.
2. Assert server/database identity and schema/migration parity. Begin an explicit transaction with
   XACT_ABORT enabled. Acquire the existing transaction-owned exclusive application lock
   `kvk-source:snapshot_report_v1:<KVK_NO>` with the existing 10,000 ms timeout; negative lock
   result aborts. Follow existing order: routing, period selection, then config requests under
   UPDLOCK/HOLDLOCK. No external API work while holding SQL locks.
3. Require exactly one `KVK.SourceRouting` row for the KVK, source match, `Enabled=0`,
   `RoutingVersion=R`, and R below bigint maximum. Missing routing means separately approved
   onboarding is needed; this activation does not insert it. Capture all prior routing fields.
4. Require exactly one same-source/KVK/period `KVK.SourceSelection` row with
   `SelectionVersion=S` and `PublicationID=P`. Require its `KVK.SourcePublication` complete,
   nonnull CompletedUTC/ManifestHash, hash H, matching config C and validated counts. Resolve
   desired config from the latest non-rejected request by ConfigVersion, as the accepted DAL does;
   if absent, use selected publication config. Require desired C equals selected C. Abort for
   pending desired endpoint or any stale version; older historical pending links alone are not
   the latest desired config. Revalidate pinned inputs/roster/map/weights and stream labels.
5. Match the reviewed consumer capability manifest to V and the deployed routing-consumer
   revisions. A SQL schema probe alone is insufficient. Only after that implementation
   prerequisite is satisfied, the proposed routing-state assignment in `KVK.SourceRouting` is:
   `DisplayPeriodID=approved PeriodID`, `Enabled=1`, `RoutingVersion=R+1`,
   `CapabilitiesVersion=V`, `ApprovedBy=A`, `ApprovedUTC=approved UTC`.
   Predicate: exact KVK_NO, SourceKey, Enabled=0 and RoutingVersion=R. Require @@ROWCOUNT=1.
   **SourceSelection, input/config rows, source facts and daily claims do not change.**
6. Retain before/after routing values and exact authorization with a durable operator release
   receipt. The current SourceAction contract is for publication actions; do not invent an
   activation action type. Review an explicit durable audit strategy before enabling; missing
   audit capability blocks execution or requires separately scoped implementation.
7. Preview rehearsal must roll back and independently confirm original routing/selection. A
   separately authorized live transaction may commit only after all predicates pass. On an
   ambiguous commit response, read back R/P/S/C and the durable approval evidence from a fresh
   connection. Never blindly repeat the update. Conflicting or unavailable evidence blocks.
8. Fresh readback must show exactly R+1, P/S unchanged, correct period/source and honest stream
   status. Verify versioned cache/readers and registered destination reconciliation within the
   approved window. Any deviation invokes the reviewed stop/rollback decision, not auto-repair.

## 5. Open operational gates and reviewable rehearsal steps

All three gates are **OPEN / NOT EXECUTED / NOT ACCEPTED**. S6 author owns the plan and evidence;
Chris Watts owns exact-operation approval, thresholds and acceptance. See the
[carried-forward register](phase_2_implementation_plan.md#s4b-follow-ups).

### S6-OPS01 — real interruption and recovery

Bind one isolated process/database/index and disjoint private/current/staging/quarantine slots
before approval. For each row, record actual process exit/restart UTC and IDs, SQL DeliveryState,
OwnerID/Fence/Receipt, remote ACLs, manifests/directory/index, selected publications and repeat calls.

| Planned interruption boundary | Required accepted outcome |
|---|---|
| After durable private_started checkpoint; during multipart private write/readback | Prior possible targets remain quarantined and unchanged by recovery; new owner/fence and disjoint registered slots only. No TTL reclaim or inference from one missing read. |
| After full private verification and durable publication_pending; during Viewer grant or lost grant response | Ambiguous permission outcome stays blocked/uncertain until terminal external evidence resolves it; private-recovery route cannot reclaim publication uncertainty. |
| During fenced current-index publication; response lost after remote success | Fresh client reconciles exact generation/key/fence/index and durable receipt. Old current pointer cannot be replaced by a stale job; no duplicate publication after restart/repeat. |
| After confirmed receipt and caller acknowledgment loss | Repeat returns the existing result with no additional publication or permission mutation. Daily claim ownership/count remains unchanged. |

Actual in-flight request interruption is required; deterministic exceptions and new service instances
alone do not close this gate. Never kill an unidentified process. Stop on unexpected ACLs, stale
fence, changed quarantined bytes, incomplete visible generation or uncertain outcome without proof.

### S6-PERF01 — representative throughput and shared quota

Agree maximum elapsed duration, scheduled cadence, peak player/period volume, concurrent demand,
request budget and retry tolerance before measuring. Values are currently **unset**. Proposed
synthetic volume points: recorded 5,806-player roster scale and the historical 10,000-player /
10-period sizing case; operator must accept their representativeness. No private player fixtures.
For every run measure cells/bytes per section and file, multipart count, actual Sheets/Drive
read/write/permission API calls, complete readback calls, elapsed time, 429/503 counts and retry
delays, final status and shared service-account consumers/budget. Account for other machines
without invoking production work. Existing 2.1-second process pacing is not global quota control.
Include bounded read retry and mutation-uncertainty outcomes; do not replay an uncertain mutation.
Accept only measured end-to-end results within agreed limits; the small S4B timings are not a load pass.

### S6-CAP01 — slots, permissions, retention and bounded receipts

Size `1 index + current generation files + staging generation files + retained final/reference
files + quarantine + approved reserve`, counting the union of distinct protected/current identities
once. Record maximum planned periods/players, files per generation, retention horizon, projected
corrections and interruption allowance. Historical four files/generation yielded nine initial
current/staging/index files; nine is not a lifetime cap.
Read back each provisioned ID, owner, service-account Editor, canShare and intended audience.
Rehearse too few slots, receipt exhaustion at the accepted `nvarchar(1024)` boundary, retained
final/reference conflicts and quarantine growth. Require setup-required/fail-closed before claim
or publication, old current output intact, no evidence truncation or quarantined/final reuse.
Review a fresh dedicated destination with its own exact registration as the recovery option;
do not silently widen schema or use more than configured bounds. Any needed helper/schema delta
requires separate approval and exact per-repo Changes reviews, Deep off.

## 6. Rollback and stop criteria

Before activation, retain previous routing fields R, selected P/S/C, input/config hashes, compatible
prior publication IDs, all destination receipts/fences and independently verified backups. Agree
observation duration, error/latency thresholds and responsible operator; these remain unbound.
Wrong source/period/current-final labels, permission leaks, missing capabilities, stale pointers,
quota/capacity exhaustion or unresolved remote mutation require a stop.

Proposed serving rollback selects a verified older same-scope publication through the existing
publication service, with an incremented SelectionVersion and delivery fences, explicit actor/reason
and config compatibility. Preserve originals, finals and accepted requests. Refresh dependent
versioned caches and reconcile registered destinations; never manually decrement versions or erase
receipts. A historical final is still labelled against its historical config.

Disabling routing also requires an expected-current RoutingVersion predicate and incremented version,
with before/after evidence and no change to source history. **Disabled routing selects legacy through
existing callers**: first verify matching legacy data/period exists. If unavailable, keep the affected
surface explicitly unavailable or retain a clearly stale verified new result under an independently
approved containment plan. No fabricated fallback or source splice. This plan is a gate, not a claim
that a containment helper exists. Old-bot downgrade is blocked until unsupported serving/writers are
safely disabled and compatibility is proved. Intake/recovery disablement retains persisted work.

No table drop, rollback database deletion, history rebuild, message retraction or universal exactly-once
guarantee is promised. Backups must include database, private originals, configuration, receipts and
relevant DATA_DIR/log evidence with a tested restore path. Generic runbook commands do not authorize
pull/reset/merge/push/PR, SQL, imports/exports, Discord, restart, deployment or activation in S6 G3.

**G4 remains pending; G5 remains operator-owned. Preparation may be reviewed now while every
unmeasured operational gate stays open. No later task starts automatically.**

## 2026-09-12 authorized local rehearsal — partial evidence, gates OPEN

Chris Watts approved "local database on K98DEV server" and "approval to begin
rehearsal" after the retained G3 preparation checkpoint. This authorizes the local
synthetic work recorded here; it is not production activation or G5 acceptance.
No predecessor pack was executed. No real player import/export, Discord action,
bot-machine update/restart, Git publication, deployment or activation was performed.

### Exact execution and retained evidence

- Local server identity: `9SX2VF4\K98DEV`, SQL Server `16.0.1200.5`; shared-memory
  connection `lpc:localhost\K98DEV`, Windows authentication.
- New, previously absent database: `K98_S6_Disposable_20260912`, collation
  `Latin1_General_CI_AS`, compatibility 160. Retained predecessor databases were
  not modified. Installed accepted migrations `20260909_001_kvk_source_observation_facts.sql`
  (SHA-256 `4b19c8e54a7555e796c06124640efd27b6838c8360d352bd55265d04bdc1614c`)
  and `20260910_001_kvk_source_publication_state.sql`
  (`2985551c7cac6ba158a38c436389aa13b44fe36235ccf6768b684037cce77fbc`).
  Synthetic KVK_Windows fixture matches authoritative columns, primary key, default
  and checks; legacy secondary indexes were not installed. There are 26 KVK tables;
  setup reported zero disabled/untrusted constraints. This is not a full production schema.
- Bot main/origin-main `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`;
  SQL main/origin-main `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
  Remotes retain the section-1 entry mapping; no fetch, pull or ref mutation.
- Temporary S6 harness uses existing synthetic helper functions and current DAL/services;
  it does not invoke predecessor test suites. Only owned hidden child processes exit.
  No production bot process is started or killed. All database connections assert the
  exact server and database. Evidence directory (outside Git):
  `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
- `setup.py` completed once. Initial sandbox Windows-authentication connection failed;
  the same target succeeded with approved elevated execution. No authentication or
  TLS-verification bypass was added to resolve that failure.
- `local_rehearsal.py` completed once, exit 0, from
  `2026-09-12T14:42:16.747885Z` to `2026-09-12T14:42:27.478053Z`.
  Exact outcomes, UTC timestamps, publication/period IDs and versions are retained in
  `local-results.json`; child process IDs and committed/checkpoint evidence are in
  `before_commit-exit.json`, `after_commit-exit.json`, `private_started-exit.json`
  and `publication_pending-exit.json`. Preserve this directory and database; no cleanup
  or blind replay is authorized. Entry documentation backups are in `entry.json`.

### Actual results and limits

| Check | Actual result | Limit / scenario allocation |
|---|---|---|
| Synthetic endpoints in seasons 139295168 and 65250356 | Both advanced live 11−10, live 12−10, final 13−10 | Partial T68–T70; two synthetic governors, not representative population |
| Duplicate observation 13 | Existing ScanID 13 returned; recovery allocated no publication | Semantic duplicate path checked; not a full ZIP/format variation matrix |
| Owned process exit before transaction commit | Fresh connection observed zero config requests and zero Windows rows; prior publication retained | Partial T46–T51; no SQL server restart |
| Owned process exit after commit/lost acknowledgement | One durable request and Windows row; fresh process recovered pending live 13−10, then corrected_final 14−10 after scan 14 arrived | EndScanID update itself supplied authority; no separate correction command; second recovery no-op |
| Exit after private_started checkpoint | Normal retry blocked; explicit local recovery changed owner and fence 1→2; two old synthetic slot IDs quarantined | S6-OPS01 partial only: no Google request was in flight |
| Exit after publication_pending checkpoint | Normal retry and private recovery both blocked | S6-OPS01 partial only: no grant or pointer mutation performed |
| Receipt boundary | Exactly 1024 UTF-16 units accepted; 1025 rejected | S6-CAP01 partial only: direct serializer contract, not actual multipart/provider exhaustion |
| Isolation | Routing enabled rows = 0; aggregate state remained not_received | No inferred aggregate report, daily SCANORDER operation or real data import |

### Workbook inventory and outstanding operator inputs

B0, F1S, F1M and F1E source workbooks are present in Downloads and their SHA-256
hashes match the accepted evidence. The A1 aggregate example is also present under
the private evidence directory and matches
`563e7a67948dbcde211764e30645a1188d06d7e39335e5793335a23f6ea9d2e3`.
Presence/hash verification did not import their contents or approve their endpoint
mapping. A1 remains a format/example artifact unless separately bound. No required
recorded source workbook is missing from this inventory; it does not establish a
future production input set. Private workbooks and credentials remain outside Git.

Read-only Google metadata checks found all five registered S4B workbooks accessible:
index `1xwF92PbxgXD0InA-ekuEPkN8MA5pgd1navpMyxEe6_Y`, quarantined slots
`1lD6o6uOKUg1e0H0cAz2guFOkFG0sXDntjt9wz_oDC3I` and
`1_Jb6hkBreXTR256MEYgFAraKDjytcQtCjEPe26qABFg`, retained recovery slots
`1bcqUkN3fySc34BsEDo_nflU3hfHJLqe5pBM6med9VS4` and
`1H9kXpIl0Vg5zv1CoLghp680j0Q90mD3fE_IpIIPG-7M`.
Existing service-account Editor access and owner's canShare were verified. Index
and recovery slots have link Viewer access; quarantined slots remain private.
These are retained evidence, not disposable S6 destinations; none was mutated.
No dedicated S6 workbook set was found in the metadata search. Approval to provision
a separate index/eight blank slots with exact rehearsal sharing, or operator-supplied
dedicated IDs, remains pending. A proposed eight-slot set is not yet a proven retention budget.

| Gate | Status after local rehearsal | Still required before acceptance |
|---|---|---|
| S6-OPS01 | OPEN; local process/SQL recovery evidence added | Dedicated Google targets and authorized sharing; measured interruption during private writes, Viewer grants and index pointer; actual external readback, fences/receipts, quarantine and reconciliation |
| S6-PERF01 | OPEN; no representative load measurement | Operator export cadence, maximum duration and other service-account consumers; agreed shared budget; actual representative multipart bytes/cells/API calls/readbacks/timing/429/503 outcomes |
| S6-CAP01 | OPEN; receipt boundary and existing ACL metadata checked | Dedicated owner/Editor/canShare/audience proof, measured active/staging/final/reference/quarantine retention, insufficient-slot and receipt-exhaustion behavior at actual provider scale |

G4 authorization remains bounded to approved rehearsal operations. G5 acceptance
and production activation remain operator-owned; none of these gates is accepted
by this local pass. Earlier unexecuted scenario rows retain their historical G3
meaning; only the partial evidence explicitly allocated above is new.

### Security, delivery and rollback disposition

Tracked changes remain the exact documentation carry-forward manifest, including
both archive rename sides. Temporary synthetic harnesses and results stay outside
Git; no production implementation, config, schema source or test file changed.
Bot security target remains the exact 18-path Markdown working-tree delta against
`85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`: documented inert-evidence skip.
SQL target remains separately `44afa315dd6cbfe9fec101f2a39a62e534f5b583` to itself,
empty delta: no-change skip. Runtime rehearsal evidence does not constitute a new
security scan. Any required later review must use Changes at exact separate repo
targets, Deep off. No standard/deep scan or automatic new task was launched.

No new deferred item was identified. Promotion verdict remains **Do not promote**:
provider evidence, acceptance, exact production operations and rollback authority
are unresolved. Retain local artifacts and disabled routing; do not delete/reuse
quarantined or retained workbooks. Canonical delivery remains sections 1–11 plus
this dated supplement. Eventual separately authorized PR and production promotion
must include the complete carry-forward manifest or prove individual paths merged.

### Local evidence SHA-256 manifest

| File | SHA-256 |
|---|---|
| `setup.py` | `56004b38572af3e4922ceecee5125f3bb133c3569a3b4da8581fb3c94a29644a` |
| `local_rehearsal.py` | `5982c3bd0c81b2e57edab75f003c12cee08c9b149f267cda9e5641a91d9c5acb` |
| `local-results.json` | `1be09acac6cdf679377a3994c7db4adb3e09a32bed5e601141022fdf355ba7ba` |
| `before_commit-exit.json` | `bbe1bf6084afcaa981b9d7cd458aaaeb84518a0a3da24589dfc7aef7a249978a` |
| `after_commit-exit.json` | `71d0faed122a7d540afe68c96cca510d2b57e3929ca46dc85333a5c1e5e9a783` |
| `private_started-exit.json` | `f1d94f5a4283832604d15d3e44e420aef2c836dca462751e3ad029afeb65fa3c` |
| `publication_pending-exit.json` | `a8faeaad3a71229522a17fd31db2962a386078cef6a26714800687d5e0beff66` |

### Rehearsal documentation validation

Fresh architecture validation passed (0 Python paths); deferred validation passed
(16 Markdown documents); security-routing validation passed (0 errors/warnings);
`git diff --check` passed. Exact-path test selection passed for all 18 manifest
paths; generic smoke-import/command-registration recommendations are skipped for
this documentation delta. No predecessor suite or full runtime suite was rerun.
The separately executed S6 synthetic process/SQL harness outcome is recorded above.

Manifest/preservation and link checks passed: exactly 18 Git paths, 16 extant
documents, all original rehearsal-entry bytes retained, three carried archived
documents unchanged, both archive source deletions preserved, 174 local links and
13 fragments resolved. Bot index remains empty; SQL repo remains clean; branches,
HEADs, origin/main refs and remotes remain at entry. Read-only local refs do not
prove remote freshness. Detailed validation and exact-path selection are retained
as `documentation-validation.json` and `selected-tests.txt` in the local evidence
directory. Earlier pre-commit orchestration limitations remain; no new blanket
pre-commit or security-scan pass is claimed. No private rows or credentials were
added to Git. Required eventual PR Files changed verification remains pending.

## 2026-09-12 S6 output provisioning and shared-consumer review

### Authority and operator performance expectations

Chris Watts approved S6 outputs and asked Codex to create them. The earlier question
specified a separate index/eight blank slots, the existing service-account Editor,
and Viewer sharing only for verified synthetic publication rehearsal. Creation and
Editor grants are now complete. No public Viewer grant, synthetic Google export or
pointer publication has yet been executed in S6. Retained S4B workbooks were untouched.

Operator expectation: **two or three exports per day; no fixed maximum duration**,
with runtime to be measured and made efficient where authorized. This removes the
unanswered cadence/duration question; do not invent a duration pass threshold.
Expected other service-account consumers are the all-KVK importer and scan-data
importer. The operator believed controls may prevent overlap and requested a check.
No account-wide quota isolation or runtime exclusivity is attested by that belief.
Performance acceptance should report actual elapsed time, size, calls, readbacks,
throttling and remaining headroom, then retain the operator's G5 decision.

### Created output manifest and verification

Nine unique native Google spreadsheets were imported from one verified blank local
XLSX into the new private My Drive `ChatGPT` folder
`1DMOF77hmxhY8PVS5R99E7kXFm3OKzU1k`. All title prefixes are
`K98 S6 rehearsal 2026-09-12`. The index and slots have distinct IDs from all retained
S4B/protected workbooks. No production config was changed to register these IDs.

| Role | Exact Google spreadsheet ID |
|---|---|
| index | `19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g` |
| slot01 | `1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw` |
| slot02 | `1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU` |
| slot03 | `1LeoZ5bySHbGTAyNUGNiKyUiG9zqn56eRvD-CTQvH7RI` |
| slot04 | `1i3o7DxQnsECQnFJ9bzI_mx6BBXb8-zvkVRU7pxQYWQ8` |
| slot05 | `1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg` |
| slot06 | `1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0` |
| slot07 | `1zMc_m7I70jr1s-GDBq035mGh0orXBAl3v2VJ-KZeY9k` |
| slot08 | `10GwOQWI5TgC2StB7axq3zZrMyjlQgj-PX_i6Ku3d2Lw` |

Connected-owner Drive metadata verified owner Chris Watts and exactly one additional
permission: the existing service-account Editor. There are no anyone/domain/group
permissions. Owner canShare is true for all nine. This is not yet evidence that the
runtime service-account credential can authenticate or that its canShare is true.
Native Sheets metadata verified one `Sheet1` per file, 1000 rows by 26 columns.
Bounded formula-mode readback of `Sheet1!A1:Z1000` returned no cells for every file.
They are intentionally blank operational slots, not finished reader-facing reports.
Native metadata retained hidden gridlines; no populated view exists for visual QA.
Default workbook timezone is America/Los_Angeles; no date values/formulas were
written. This timezone does not assign or alter UTC scan-start evidence; any later
timestamp handling must preserve the approved explicit UTC contract.

The local artifact builder exported and rendered the empty XLSX, then its process
returned exit 1 despite reporting completion. This is not recorded as a clean
builder process pass. Independent saved-XLSX inspection found only Sheet1 and no
populated cells; all nine native conversions and blank readbacks succeeded.

### Shared-consumer controls — static findings at exact accepted bot HEAD

| Code evidence | Finding and implication |
|---|---|
| `bot_helpers.py:280–339`; `services/fallback_upload_staging_service.py:79–101` | Monitored scan uploads share a process-local processing_lock across downstream processing. This protects that queue's participants. |
| `dl_bot.py:635–658` | All-KVK upload is a separate route before the fallback queue, returning without enqueueing there. |
| `upload_routes/kvk_all_route.py:535–548`; `kvk_all_importer.py:134–151` | All-KVK auto-export is scheduled as its own task and offloaded to a thread. The scan processing_lock is not acquired here. |
| `file_utils.py:1355–1400` | Thread offload runs the callable via asyncio.to_thread; its telemetry registry is not a global export queue. |
| `kvk/dal/new_source_delivery_dal.py:220–249` | S6 SQL session lock is keyed by destination kind/ID. It serializes participants for that destination, not all Google consumers. |
| `kvk/services/new_source_export_service.py:23–35,665–688` | S6 service-account pacing is 2.1 seconds between calls within a process. Other processes and legacy gsheet callers do not share that process memory. GET 429/503 retry behavior does not serialize mutations across consumers. |

Conclusion: **the current code does not establish a common lock/queue across all
three consumers**. Two or three exports/day does not preclude simultaneous bursts.
This is a concrete S6-PERF01 release gap, not a request to rewrite the importers or
run them concurrently. No live importer, bot-machine or credential consumer was
started to test contention. Runtime deployed versions/settings remain unverified.
Use separately verified scheduling/exclusivity or an explicitly approved shared
control change before claiming account-wide serialization; no implementation change
is included in this evidence-only delivery.

### Runtime preflight blocker and open acceptance gates

`sdk_preflight.py` ran once at `2026-09-12T14:59:38.149140Z` and failed before any
Google API call with FileNotFoundError. Read-only configuration resolution confirmed
the current GOOGLE_CREDENTIALS_FILE target is
`C:/discord_file_downloader/statsupdate-0d8b70356ef2.json`, which is absent; the default
credentials.json path is also absent. The existing trust bundle is present and TLS
verification remains enabled. No key was printed, created, copied or put in Git.
The operator was asked for the existing local key path or restoration at the configured
path; only a filesystem path/confirmation is needed, not key contents in chat.

Connected-owner Google Drive access was used for authorized provisioning and
readback; it must not substitute for the missing runtime service-account identity
in OPS01/PERF01/CAP01 measurements. No automatic retry of the failed preflight,
provider mutation or predecessor execution occurred. Preserve its failed result.

| Gate | Current status | Remaining exact evidence |
|---|---|---|
| S6-OPS01 | OPEN; local process evidence retained, dedicated outputs now bound | Restore local runtime credential; actual private-write/grant/pointer interruption and fresh-process external readback/reconciliation |
| S6-PERF01 | OPEN; 2–3/day, no hard duration cap recorded; shared-lock gap evidenced | Authenticated representative multipart measurement with actual calls/readbacks/bytes/timing/retries; shared-consumer budget or verified exclusivity; operator acceptance |
| S6-CAP01 | OPEN; nine private files provisioned; owner/Editor/blank readback passed | Runtime service-account canShare and synthetic Viewer publication proof; actual capacity/retention/insufficient-slot/receipt exhaustion; operator acceptance |

No G5 acceptance or production activation is granted. Database remains
`K98_S6_Disposable_20260912` with routing disabled from the retained local result;
this provisioning step did not write SQL. No pull/reset/merge/push/PR, production
SQL, real data import/export, Discord action, restart, deployment or activation.
All existing documentation, untracked archives and both rename sides remain in
the exact S6 carry-forward manifest. Canonical delivery is sections 1–11 plus the
dated supplements; previous pending-output/cadence statements are historical.

### Retained evidence manifest

Evidence directory remains `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.

| File | SHA-256 |
|---|---|
| `s6-output-ids.json` | `b567d50aac28788ed83dcace812169edf77f4c2edcfbc0b6b8b330d61ac4dd5e` |
| `s6-output-metadata.json` | `dfac47c6338ddab0205972ad4f93c1441c5dec98a96955183529f8842e686a58` |
| `s6-output-blank-readback.json` | `6a3db33da630e95a6657500e3f2ddd13ad5fe1502344aaadbba51b2a3afc0054` |
| `sdk_preflight.py` | `1398e0d0f0c2981c8f05fb460819edbac40a5c4c9c9ced3450528c65234c3d8b` |
| `sdk-preflight-results.json` | `e95b26f5867247350f07ef6c2ff2afa25d70befc45033bdb99d1ca6b1a91b5e3` |

## 2026-09-12 authenticated S6 rehearsal and representative benchmark

### Authority, isolation and immutable revisions

The operator restored the configured local credential and explicitly approved
**5,806 synthetic players across ten periods**, confirming that the all-KVK and
scan-data importers would remain idle. This is operator-attested isolation during
this benchmark, not independent monitoring or a proven common concurrency lock.
Earlier approval covers the local K98DEV rehearsal and dedicated S6 outputs.
No real source-player workbook was imported or exported. Existing S4B files and
accepted predecessor evidence remain untouched; no predecessor was rerun.

Bot main/origin main remains `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`,
with local production/main anchor `c7e063f02ebe8287a584d0054ea14f91a0c0ecc6`.
Bot origin is `https://github.com/cwatts6/K98-bot-mirror.git`; production is
`https://github.com/cwatts6/K98-bot.git`. SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin
`https://github.com/cwatts6/K98-bot-SQL-Server.git`, with no SQL Git changes.
There are no runtime-source or tracked-test edits. Temporary rehearsal harnesses
and exact result artifacts are retained outside Git in the evidence directory below.

The only database written is retained disposable `K98_S6_Disposable_20260912`
on verified `9SX2VF4\K98DEV`, reached using `lpc:localhost\K98DEV` and Windows
authentication. Completed checks assert zero enabled SourceRouting rows. No
production SQL, bot-machine update, restart, real import/export, Discord operation,
deployment, activation, pull/reset/merge/push/PR or commit occurred.

The configured service-account key was restored locally and remains Git-ignored;
its contents are absent from Git and evidence. The restored runtime preflight
authenticated successfully and checked all nine original S6 files private/blank,
service-account Editor and canShare. The earlier missing-key failure remains
retained rather than rewritten. TLS verification used the existing trust bundle.

### Actual operations, recovery and limits of interruption evidence

The small operational scenarios deliberately use an **11,223-cell test ceiling**
to force two real Google files from 2,286 logical cells. This is a temporary harness
override; the accepted production 9,000,000-cell limit is unchanged. These scenarios
are operational proofs, not representative performance measurements.

* A child process exited after submitting a private data-write body, before reading
  its response. A fresh process observed the durable private_started claim and
  blocked blind retry. Explicit private recovery used fresh original slots 03–04,
  changed owner/fence 1→2, quarantined slots 01–02, fully verified and published.
  An independent audit found the quarantined grids/values unchanged. Confirmed
  repeat returned the same receipt with zero Google calls.
* Receipt-capacity exhaustion was rejected before SQL claim or provider calls using
  sixteen synthetic, unallocated 128-character IDs. No fake ID was accessed. Actual
  retained-slot exhaustion refused original slots 03–04 with setup_required after
  four GETs and no provider mutation. This proves fail-closed behavior, not an
  accepted long-term retention budget.
* The original pointer send-boundary interruption did **not** advance the index.
  Its planned confirmation assertion failed: fresh external readback correctly
  left the claim unresolved at publication_pending. Original slots 05–06 are
  verified public Viewer files, but the original index still references the prior
  confirmed generation in slots 03–04. Blind retry and private reclaim were blocked.
  This uncertainty is preserved; no forced pointer write or receipt repair occurred.
* A separate small scenario on the benchmark destination exits **after Google
  returns pointer success but before SQL confirmation**. Fresh-process reconciliation
  confirms the exact pointer/key/fence/directory evidence; a repeat makes zero
  Google calls. This proves loss of the application's acknowledgment, not an
  in-flight network cut that happened to succeed remotely.
* A separate Viewer-grant interruption submits the first grant, holds the response
  unread for one second, and exits. Fresh external ACL/pointer readback records the
  actual resulting permissions. Its publication_pending claim remains unresolved;
  blind retry and private reclaim remain blocked. No permission replay or repair
  is attempted. See the retained readback JSON for exact observed ACLs.

Intentional exit markers requested codes 88/89; the shell runner reported exit 1
for those interrupted processes. They are recorded as deliberate interruptions,
not clean process passes or observed runner exit codes 88/89. The original pointer
readback assertion failure is retained distinctly from the safe blocked outcome.

### Representative performance measured with normal settings

The accepted SQL publication path supplied 5,806 synthetic B0-eligible players and
ten fight-period publications, across two synthetic kingdoms/camps. All ten selected
publications contain 5,806 player results. This is a representative row/period load,
not the real B0 workbook's 36-kingdom distribution or a mixed aggregate-report case.
Independent aggregate/overall reports remain honestly not_received. No fight sum
was presented as an authoritative aggregate. Daily SCANORDER remains separate.

The run used the unchanged **9,000,000 cells per part**, **500 rows per data write**,
and **2.1-second service-account pacing**, followed by full provider value readback
before Viewer publication and index confirmation. There were 17,831,186 logical
data cells and 17,831,355 physical cells including repeated headers and directory,
split across two output files. These are measured/planned generation counts, not
an assertion that all cells contain nonempty values.

| Measurement | Actual result |
|---|---|
| Run UTC | `2026-09-12T15:27:06.420046+00:00` to `2026-09-12T16:07:01.192365+00:00` |
| Generation loading | 92.281 seconds |
| Export including full readback and publication | 2248.609 seconds (37.48 minutes) |
| Export API calls (excludes initial preflight) | 991 |
| Encoded request-body bytes | 219796508 |
| Decoded response JSON bytes | 202250907 |
| HTTP error status counts | `{}` |
| Durable outcome | confirmed, export_complete; repeat identical receipt with zero Google calls |

Response JSON bytes are decoded application measurements, not compressed wire
traffic. Elapsed time includes the actual default pacing and provider/network time.
The operator specified two or three exports daily with no fixed maximum duration;
no invented timing threshold or claim of optimal performance is applied.

| Actual export method | Calls |
|---|---|
| `drive.files.get` | 110 |
| `drive.files.update` | 5 |
| `drive.permissions.create` | 3 |
| `sheets.spreadsheets.batchUpdate` | 2 |
| `sheets.spreadsheets.get` | 16 |
| `sheets.spreadsheets.values.batchGet` | 368 |
| `sheets.spreadsheets.values.get` | 9 |
| `sheets.spreadsheets.values.update` | 478 |

### Dedicated benchmark output manifest and retained state

These additional seven synthetic files were created under the existing S6 output
and benchmark approvals. Initial runtime preflight verified private blank files,
Editor access and canShare. Full benchmark files 01–02 are retained unchanged by
the subsequent small operational checks. Slots 03–04 hold the independently
confirmed small acknowledgment-loss generation. Slots 05–06 hold the later
grant-interruption generation with unresolved publication. The benchmark index
therefore points to the confirmed small generation after those checks; use the
large generation's retained receipt directory URL to inspect the benchmark.

| Role | Exact Google spreadsheet ID |
|---|---|
| index | `1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY` |
| slot01 | `1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU` |
| slot02 | `1CkgvVGNN-UUBfM0rCVxmHoDbWK_5nfDU7R63j2EYP6g` |
| slot03 | `1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU` |
| slot04 | `1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU` |
| slot05 | `1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ` |
| slot06 | `1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk` |

Large-generation receipt (exact): `{"delivery_state": "confirmed", "diagnostic": null, "export_complete": true, "receipt": "{\"export_key\":\"eca93ecc70fe04cb836a483fafb65fa17cd0a990730d4ca77e5d55667557b9ea\",\"publication_id\":\"390dd712-10c4-5cc3-befd-7dbb067e300c\",\"selection_version\":1,\"export_complete\":true,\"remote_id\":\"https://docs.google.com/spreadsheets/d/1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU/edit#gid=2036238961\",\"phase\":\"published\",\"audience\":\"public_viewer\",\"attempt_slots\":[\"1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU\",\"1CkgvVGNN-UUBfM0rCVxmHoDbWK_5nfDU7R63j2EYP6g\",\"1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU\",\"1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU\",\"1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ\",\"1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk\"]}", "setup_required": null, "sql_selected": true}`

### Acceptance gates and rollback boundary

| Gate | Status and evidence | Remaining operator-owned decision |
|---|---|---|
| S6-OPS01 | OPEN: real private-write interruption/recovery/quarantine, successful-pointer acknowledgment-loss reconciliation and grant uncertainty readback recorded | Accept precise measured evidence; decide exact handling of retained publication_pending claims. Do not blind-retry, reclaim or erase them. |
| S6-PERF01 | OPEN: approved 5,806 × ten-period normal-budget full-readback measurement completed under operator-attested importer idleness | Accept measured duration/cadence and representative-profile limits; establish verified scheduling/exclusivity or separately approved shared control. Static review found no common lock across all three consumers. |
| S6-CAP01 | OPEN: real multipart publication/ACL checks, retained-slot refusal and receipt-size fail-closed checks recorded | Accept retention horizon, correction/quarantine allowance and provisioned-slot budget; unresolved files remain occupied evidence, not reusable capacity. |

The original final/interim contracts remain: B0 eligibility, exact endpoint IDs,
UTC scan start, semantic re-export deduplication, interim 11−10 then 12−10, final
13−10 and authorized EndScanID 14 permitting replacement 14−10 without another
correction command. Accepted preceding slices and S5B-REC01 remain closed. No
G5 acceptance is inferred from rehearsal execution. Live G4 exact operations and
G5 acceptance remain operator-owned; production activation is not authorized.

Rollback readiness here means preserving disabled routing, original files and
receipts, all uncertain/quarantined outputs, and the isolated disposable database.
No destructive cleanup, live rollback or activation action was executed.

### Canonical validation, carry-forward and exact evidence manifest

This appendix supplements canonical delivery sections 1–11 and earlier dated
evidence; prior blockers and failures are historical records, not current claims.
The exact eighteen Git paths remain the required delivery manifest: sixteen
existing Markdown files plus both deleted rename sources, with an empty index.
All pre-existing closeout work and untracked archives must accompany the eventual
separately authorized S6 PR; no Files changed verification against a PR is possible
because no PR exists. The three carried archived delivery/starter documents remain
byte-for-byte unchanged. Final local path/link/hash verification is recorded in
documentation-validation.json after this update.

Tracked-source tests are not rerun for this Markdown-only update. Architecture,
deferred-item, security-routing, test-selection and whitespace checks are recorded
separately. Earlier pre-commit environment/cache limitations and historical README
trailing spaces remain qualified; no blanket pre-commit or gitleaks pass is claimed.
Security routing remains the documented documentation-only skip: exact Bot
working-tree eighteen-path delta against 85f303f6, separate SQL empty delta against
44afa315. No new Changes review is claimed for temporary harnesses. Any separately
required review must use Changes at separate exact repo targets, Deep off; no
standard/deep scan or automatic task was started.

Evidence directory: `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
Artifacts below are local evidence, not committed data. Retain them for operator
acceptance; temporary storage is not a durable external archive.

| Result artifact | Actual status | Wall seconds | API calls | SHA-256 |
|---|---|---|---|---|
| `sdk-preflight-results.json` | failed | None | 0 | `e95b26f5867247350f07ef6c2ff2afa25d70befc45033bdb99d1ca6b1a91b5e3` |
| `sdk-preflight-restored-results.json` | passed | 62.692 | 27 | `056f413efcf9779f6e7fb814b8d9a246ad6f59fce99a9baadd4166b3f2fc3cc7` |
| `provider-private_interrupt.json` | process_exit_after_request_body_sent | 67.452 | 33 | `d0f79b7bbe3507a919a4c6bf281fb5270f2e8d7d260e6e7cd322aa595581e0db` |
| `provider-private_readback.json` | passed | 40.762 | 20 | `87794272a267676f4d1e384cf05a36ddcb9870659c2a2416bf66d8cd1226a158` |
| `provider-private_recover.json` | passed | 181.493 | 87 | `2fbe2c65f0c547b9ba86db0d90dcd755a57badb8b2ba5bd9301027941fc182e3` |
| `provider-quarantine_audit.json` | passed | 36.483 | 18 | `2bb7c23be548ce38fea1277d8c45a4cf0518c9987c10a0f1b8bbe2afe0f46aa0` |
| `provider-confirmed_repeat.json` | passed | 0.202 | 0 | `414442b4f63d187d9bba88690dfce4a247bc0e5981f368a5b76db2e612680a30` |
| `provider-receipt_capacity.json` | passed | 0.173 | 0 | `7d57b9e391a4f742c26016c0186c067cee3709c2e7ee65069304063060a0ef3b` |
| `provider-insufficient_slots.json` | passed | 7.137 | 4 | `27a05211d2113d071246b48a1ba0bfa2814dbdd95b1a18c7bc36d8cd04bc2179` |
| `provider-pointer_interrupt.json` | process_exit_after_request_body_sent | 189.391 | 84 | `bd2b272bbcce4912786307d608479d1bb8030918e117fe94d959a046c3d41952` |
| `provider-pointer_readback.json` | failed | None | 26 | `be2df5ccfdc28ed4d0d1dbbc8c5dfef7e96041bebd98c55b3d3d03c8b3a69757` |
| `benchmark-plan.json` | prepared | 384.769 | 0 | `80f063bc02c9e81c1f94ada693144899df105458f28461ab8cf8e39127182c37` |
| `benchmark-results.json` | passed | 2394.772 | 1012 | `3587bbafc0bc145744c79ff03cb51e119915ad373ec3dd428385051880615e7b` |
| `benchmark-ops/provider-pointer_interrupt.json` | process_exit_after_google_success_before_sql_confirmation | 175.194 | 84 | `cd4564f160011a516b373048ad6d13ec2756ef1431e1a3ab15bac09367b79833` |
| `benchmark-ops/provider-pointer_readback.json` | passed | 72.031 | 35 | `4584425b6995f81788a2f2ca4947d3033f9683e1ffcd0f5c5b73e3f6a1de6752` |
| `benchmark-ops/provider-pointer_repeat.json` | passed | 0.118 | 0 | `c0519e4c8b4bde982a35e9dd34993a0d9d6919da38cfeeff6e7bee878499e393` |
| `benchmark-ops/provider-grant_interrupt.json` | process_exit_after_request_body_sent | 167.528 | 80 | `be447d3ce3eef8740c402957b948ebb72cced27b2a8d1dbbab863de6834bb82c` |
| `benchmark-ops/provider-grant_readback.json` | passed | 50.941 | 25 | `adabc4e3d5b404e5bc4ef755e66e2c783b581e301c680f75bd507763b4bfe553` |

### Exact interruption readback identities


`provider-pointer_readback.json`:

```json
{
  "index": "19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g",
  "key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
  "slots": [
    "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
    "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 4,
    "owner": "bca05d8c-2fa1-43b2-a036-9905e45150f0",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "quarantined_slots": [
        "1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU",
        "1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw"
      ],
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
        "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "claimed",
    "fence": 4,
    "owner": "bca05d8c-2fa1-43b2-a036-9905e45150f0",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "quarantined_slots": [
        "1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU",
        "1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw"
      ],
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
        "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "78792a5a9782b69ca430cc3a5deeecf5a8e8ff7090dd547cbe533d229c589d56",
      "2",
      "https://docs.google.com/spreadsheets/d/1LeoZ5bySHbGTAyNUGNiKyUiG9zqn56eRvD-CTQvH7RI/edit#gid=1761925453"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

`benchmark-ops/provider-pointer_readback.json`:

```json
{
  "index": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
  "key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
  "slots": [
    "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
    "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 2,
    "owner": "11e75cb1-3ec1-4371-bcab-73d5898ed90b",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
        "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "confirmed",
    "fence": 2,
    "owner": "11e75cb1-3ec1-4371-bcab-73d5898ed90b",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "export_complete": true,
      "remote_id": "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482",
      "phase": "published",
      "attempt_slots": [
        "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
        "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "2",
      "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

`benchmark-ops/provider-grant_readback.json`:

```json
{
  "index": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
  "key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
  "slots": [
    "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
    "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 3,
    "owner": "487a17d9-c64d-4116-9274-143ddffbabb1",
    "receipt": {
      "export_key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
      "publication_id": "54a2480a-26fb-5bad-a3f5-9321525a731c",
      "selection_version": 1,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
        "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "claimed",
    "fence": 3,
    "owner": "487a17d9-c64d-4116-9274-143ddffbabb1",
    "receipt": {
      "export_key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
      "publication_id": "54a2480a-26fb-5bad-a3f5-9321525a731c",
      "selection_version": 1,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
        "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "2",
      "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk",
      "permissions": [
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

| Additional exact artifact | SHA-256 |
|---|---|
| `local_rehearsal.py` | `5982c3bd0c81b2e57edab75f003c12cee08c9b149f267cda9e5641a91d9c5acb` |
| `local-results.json` | `1be09acac6cdf679377a3994c7db4adb3e09a32bed5e601141022fdf355ba7ba` |
| `provider_ops.py` | `024042a7326dd52a20e029300cdcd67da2e5d3b8e038a1c940c1f02742f78fb4` |
| `provider_followups.py` | `3e0ebe1ff201ee86e0a500d503261cff60c857395d2d30e15336b744d75e65eb` |
| `provider-plan.json` | `0d9beb3c2d8468493aaa440f5dfdbd6602462557f32185e50c61bf011df0e05d` |
| `benchmark_setup.py` | `7e3c752531519e1c00bd753694f029bb2497d71fad29296e0e3397071b50f161` |
| `benchmark_run.py` | `ebe84bad8a1dd3cdf35ad4b1ece6dde27af2b549d151324d8204d286fc1d7502` |
| `benchmark_operational_followups.py` | `2c1c4af4334699b99603a33368556f21a2643f1ef7c0de6b529a6bfd99d8f885` |
| `benchmark-output-ids.json` | `b7d62f7be4937a7478ba0ce57e0e6ec0e5bb09f55d8b3fc7df91732e5aa80483` |
| `benchmark-output-metadata.json` | `f2f49b7b1c90a7eb56487ba88ee071a2796c7f6afbdccf43253c12bdd080efbe` |
| `benchmark-request-estimate.json` | `bee223dd1ca04c7f9d5c90a57d6db5eed07fbe2e7e727348f327bf800ae24c9d` |
| `runtime-summary.json` | `ca3866531e21cf29ee47d377b8fea667cc2657b635c30fcc26205846da161222` |

### Final authenticated-rehearsal documentation validation

After recording the actual runtime outcomes, architecture validation passed
(0 changed Python files), deferred-item validation passed (16 Markdown files),
security-routing validation passed (0 errors/warnings), and git diff --check passed.
Exact-path test selection passed; its generic smoke-import and command-registration
recommendations are skipped because runtime source/registration are unchanged and
no PR is being handed off. No predecessor tests or production smoke were rerun.
The complete 18-path manifest, empty Git index, all original evidence-entry bytes,
three unchanged carried archive documents and both rename deletions were verified.
All 174 local links and 13 fragments resolved. Bot/SQL main and origin/main remain
at the entry anchors; remotes were rechecked, SQL status is clean, and bot changes
are exactly the preserved documentation manifest. Local production/main is still
c7e063f02ebe8287a584d0054ea14f91a0c0ecc6. No remote fetch was performed.

All required source workbooks are present according to the retained read-only
inventory; the restored credential now authenticates. No additional workbook or
credential creation is required for this completed rehearsal. S6-OPS01, S6-PERF01
and S6-CAP01 remain OPEN with the precise acceptance gaps above. No production G4
action, G5 acceptance, PR or activation is claimed.

## 2026-09-12 operator approval of completed rehearsal evidence

Chris Watts approved proceeding after the completed rehearsal report. Record this
as acceptance of the measured synthetic results, including the 37m 29s full export
and verification, successful private recovery and pointer acknowledgment-loss
reconciliation, and safe blocking of the two uncertain publications. Earlier
statements awaiting acceptance of those measured results are historical.

This approval supplies no new scheduling window, shared-consumer control, retention
horizon, correction/quarantine allowance or exact recovery operation for uncertain
publications. Those facts must not be invented or marked implemented. S6-OPS01,
S6-PERF01 and S6-CAP01 therefore retain their open operational components, with
the measured rehearsal evidence now operator accepted. Full release G5 acceptance
and production G4 execution are not inferred.

The concrete next proposed action is a documentation-only mirror branch
`codex/kvk-source-migration-s6-release-evidence`, exact eighteen-path commit and
push to `origin` (`cwatts6/K98-bot-mirror`), and a draft PR into `main` titled
"Document KVK S6 rehearsal evidence and release gates". Include all pending
closeout documentation, both S5B rename sides and untracked archive files. After
creation, verify the PR Files changed against the complete manifest; do not merge
or promote. This is a prepared proposal, not a claim that a branch/commit/PR exists.
The earlier explicit no-push/no-PR restriction makes clarification of this exact
external step necessary; rehearsal acceptance alone does not identify it.

Validation at approval entry reconfirmed both repository HEADs/remotes/status,
all eighteen Git paths, empty index, clean SQL tree, preserved original document
bytes, 174 local links and 13 fragments. This update changes documentation only;
the existing runtime-test and separate-repository security skip decisions remain
applicable. No SQL, Google, Discord, Git publication or production action is part
of this approval record. Preserve all disposable databases and retained outputs.

## PR 272 review correction — missing public routing consumer

Review comment 3996906362 is valid. At reviewed bot commit
`758d6be163026f0299c05c3ad0bf2c4517c55932`, routing-row access in
`kvk/dal/new_source_config_dal.py:13–28` and
`kvk/dal/new_source_admin_dal.py:494–498` provides locking/onboarding, not public
read dispatch. `stats_alerts/embeds/kvk.py:154–185` selects V2 only with explicit
diagnostic source_selection; ordinary requests retain the legacy path.

A successful SourceRouting.Enabled update alone cannot activate public V2 readers.
The readiness sequence and transaction preconditions now explicitly stop until a
separately approved, reviewed, deployed and accepted routing consumer covers all
intended public readers. Require ordinary-request enable/disable behavior, pinned
routing/selection versions, unavailable/stale/capability handling, cache/restart
behavior and rollback tests bound to the deployed consumer revision. This is an
implementation gap, not merely missing deployment evidence or an activation helper.
No runtime implementation is included or authorized by this documentation correction.
S6-OPS01/PERF01/CAP01 and all retained uncertainty remain as previously recorded;
this additional prerequisite cannot be discharged by their synthetic measurements.

Copilot reviewed 16/16 files and generated no inline comments, but requested final
human review of the large evidence record. That requirement remains: operator
rehearsal acceptance is recorded, while independent remote reviewers cannot verify
local disposable databases, runtime JSON artifacts or every historical claim from
the PR alone. Hashes identify retained artifacts; they do not substitute for access
and inspection. No independent review or full release acceptance is invented.

Validation for this correction: Markdown-only; no runtime tests or predecessor
rehearsals rerun. Recheck local links, the complete 18-path PR manifest, staged
whitespace, architecture/deferred/security-routing and staged secrets. Security
routing remains documentation-only skip for the exact Bot review-fix diff; SQL
remains unchanged at 44afa315dd6cbfe9fec101f2a39a62e534f5b583. No activation,
merge, production promotion, SQL execution or Google operation is performed.


## S10E repository closeout and S11 preparation boundary — 2026-09-15

S10E mirror #280 / production #587 / SQL #88 are merged and locally synchronized. The operator
confirms no bot-machine pull. Final offline suite: 4,664 passed / 71 skipped; Changes review and CI
passed. This is source/repository delivery, not installation, runtime deployment, provider proof,
activation or G5 acceptance. [Exact closeout and carry-forward manifest](s10e_closeout_and_s11_handoff.md).

S11 begins review/scope from the approved eight-document release proposal. Reconcile disabled
composition, trusted termination/reconciliation/retirement-recovery producers, compatible shared
writers and S10C/D/E SQL installation evidence before proposing exact G4 operations. No predecessor
rerun or use of retained S6/S8 data as disposable targets. Keep OPS01/PERF01/CAP01 and both uncertain
publications open; do not infer runtime truth from static SQL, merged commits or fake-client tests.

Release rollback stops admission and drains/reconciles owned work. Preserve sealed inputs, receipt
bytes, history, old/nested-owner evidence and uncertain claims; forward-fix installed SQL. Only an
explicit target/operation approval permits any provider/Discord/SQL or bot-machine action.
