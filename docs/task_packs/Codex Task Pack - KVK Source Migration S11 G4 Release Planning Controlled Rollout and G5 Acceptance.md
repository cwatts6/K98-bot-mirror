# S11 — G4 release planning, controlled rollout and G5 acceptance

Follow-up delivery: [Bot-mirror #282](https://github.com/cwatts6/K98-bot-mirror/pull/282) and
[SQL closeout #90](https://github.com/cwatts6/K98-bot-SQL-Server/pull/90) are open for review.
Recheck their final outcomes and any later production promotion in the S11 closeout before
choosing release pins. These PRs do not authorize G4 execution or G5 acceptance.

## Entry boundary: G4 plan development only

Prepared 2026-09-25 after S11 source delivery. Begin with **review and plan development only**.
Read the [S11 closeout](../reference/kvk_source_migration/s11_closeout_and_g4_handoff.md),
which records merged source, the mirror publication repair and their distinct delivery states.
Recheck both repositories, remotes, indexes, pending documents and exact source identities.
Preserve pending work and recovered evidence. Anchors are comparisons, never reset commands.

No SQL connection/execution, provider/Discord call, real import/export, credential provisioning,
bot-machine pull/restart/deployment, activation, predecessor rerun, Git publication or automatic
new task is authorized by this pack. Planning may inspect repository files and retained offline
evidence. Even live read-only inventory requires its own named target and approval.
Do not execute examples or enable gated fixtures while developing the plan.

The later phases are distinct: **controlled rollout executes only specifically approved
operations**; **G5 acceptance is an operator decision on the resulting evidence**. A general
request to continue carries the current phase forward; it does not authorize an unspecified
operation, a changed target, or the next phase.

## Delivered design and evidence limits

Bot mirror #281, SQL #89 and production Bot #588 are merged. The production publisher omitted
five authority source/test paths because of `**/*auth*`; the initial follow-up restored their
exact reviewed production bytes and added exact-path exceptions. PR #282 review corrections
then added incomplete-drain failure status and bounded, durable shared 429/503 cooldown
feedback without replay or release. Verify the final correction revision and production
synchronization before selecting release/source-hash pins. Compare current files individually;
the original five-file identity proof must not cause new corrections to be omitted in promotion.
Plan explicit shutdown/retained-session and cooldown/lost-checkpoint evidence cases for later
approved G4 execution. No SQL runtime change is required by these two corrections.

The implemented design has one protected authority host and a fresh authority-only provider
identity. Bot callers submit bounded requests through the authenticated local channel; the
authority owns supervised provider execution and durable proof. SQL supplies exact ownership,
request/evidence state and restricted module access. Complete application metadata and protected
runtime manifests must agree before admission. Every shared writer must use the closed
composition. Shutdown closes admission and drains owned delivery; uncertainty retains claims.

Merged code and offline tests establish source behavior, not installed SQL, Windows containment,
exclusive key custody, provider finality, actual restore, successful deployment or G5 acceptance.
Classify each gap as missing source, configuration/prerequisite, or unproven runtime behavior.
Scope and obtain approval for a genuine missing implementation separately; do not invent code
changes to carry documents or rerun completed predecessor slices.

## Required reading

Read current AGENTS, README-DEV, reference index and all required core standards. Then read:

- [S11 closeout and exact merged identities](../reference/kvk_source_migration/s11_closeout_and_g4_handoff.md),
  [release readiness/rollback](../reference/kvk_source_migration/release_readiness_and_rollback.md)
  and [release evidence](../reference/kvk_source_migration/release_evidence_log.md).
- S7 [contracts/consumer matrix](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md)
  and [implementation manifests](../reference/kvk_source_migration/integration_implementation_manifests.md);
  [architecture and EndScanID amendment](../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
  [acceptance scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md),
  [decisions](../reference/kvk_source_migration/decision_and_evidence_register.md) and
  [post-S6 handoff](../reference/kvk_source_migration/post_s6_handoff_log.md).
- S10A/C/D/E closeouts and authoritative SQL in `C:/K98-bot-SQL-Server`, including S11 migrations,
  schema snapshots, source manifest, static checkers and gated transaction fixtures. Do not infer
  installed objects from Python calls or approved source.
- Retained S6/S8 evidence, [local SQL guidance](../reference/local_sql_development.md),
  [environment reference](../reference/ENV_REFERENCE.md), startup/shutdown/diagnostics runbooks,
  [Promotion Guide](../reference/Promotion%20Guide.md) and rollback references.

Historical dated status blocks and old packs are evidence, not current instructions to repeat
implementation, PR creation or predecessor execution.

## Phase 1 deliverable: an exact operation packet

Produce a reviewable packet with these fields. Unknown values must be marked **UNRESOLVED**;
never substitute examples or derive expected metadata from the system being checked. No group
is executable until its exact targets, commands, prerequisites and approval are recorded.

| Area | Required exact values |
|---|---|
| Control | Packet ID/version/SHA-256; approver, operator and abort owner; window, expiry, approved operation IDs and evidence directory |
| Source | Production Bot commit and file hashes, separate SQL commit/migration/manifest hashes, Python/SDK versions, protected configuration hashes; repaired mirror/production identity proof |
| Hosts | Bot and authority machine names, Windows accounts/SIDs/tokens, service/task definitions, process incarnations, all writer inventory and exclusion mechanism |
| SQL | Instance/database/version/compatibility/collation, login/users/roles, catalog/signature/grant/shape expectations, existing migration state, transaction/lock/time budgets |
| Recovery | Backup path/hash/owner, actual restore target and physical files, disjoint disposable databases and case IDs, retention policy; VERIFYONLY alone is insufficient |
| Credentials | Fresh authority-only identity, key issuance/custody/revocation plan, file ACLs and role separation; secret references only, never key bytes in Git/chat |
| Durable storage | Private spool, origin, retirement journal and receipt paths; ACL/storage owner, capacity and recovery access; outside Git |
| Provider | Account/project, exact pool/file/grid/alias IDs, protected exclusions, owner/editor/viewer ACLs, private output creation and clear/readback targets |
| Discord | Exact guild/channel/actor/roles, upload and command cases, bounded expected responses; no incidental daily job or additional import |
| Each operation | Literal command/action, target, state/identity preconditions, read/write effects, timeout and budget, expected evidence/receipt, stop trigger, recovery action and approval coverage |

The seven protected observation records are `host_acl`, `bot_identity`, `identity_issuance`,
`key_inventory`, `file_access`, `writer_drain` and `sql_installation`. Preserve original evidence,
hashes, observation time and provenance; do not fabricate a record from desired configuration.
Observation and provisioning are separate approved operations.

Known operator context: an external system creates exports and an admin uploads them to Discord;
all imports are upload-triggered; no other import jobs, manual write tools or bot instances were
reported. Admin-created outputs are not edited after upload and players have anyone-with-link
Viewer access. The historical service account `sheets-service@statsupdate.iam.gserviceaccount.com`
has a key on both machines. Those statements guide planning but do not prove current inventory
or the new authority-exclusive custody boundary. Plan fresh identity/custody and old-writer
exclusion explicitly. Do not ask for private keys. Sample files are optional only where a named
new case needs them; list the specific shape and purpose before requesting them.

## Operation groups and approval checkpoints

| Group | Plan and approve separately | Prerequisite / stop boundary |
|---|---|---|
| G4-00 inventory | Named host/SQL/provider read-only observations | Exact read scope; no implicit provisioning or writes |
| G4-01 SQL recovery | Backup and actual restore to a named disposable target; preservation comparisons | Verified isolation from retained data; failed restore stops installation |
| G4-02 SQL install/tests | Exact missing dependencies, signatures/grants/roles and bounded new transaction cases | Closed admission/old-writer exclusion; expected source and metadata match |
| G4-03 host/identity | Fresh identity issuance, protected paths/ACLs, role separation, authority service/task setup | Separate provisioning approval; Bot cannot obtain provider key or become producer |
| G4-04 native/provider | Exact containment, pipe, enrollment, request, readback and recovery cases; reads and writes explicitly distinguished | Installed SQL/identity proof; fresh private outputs; no blind request replay |
| G4-05 rollover/retirement | Close admission, drain/reconcile, termination proof, private clear/readback, journal recovery and audited reuse | Every ownership and no-delayed-effects prerequisite; ambiguity stops reuse |
| G4-06 deployment/Discord | Production-only Bot pull/restart/configuration, bounded smoke/upload/operator cases and observations | Exact reviewed build and compatible dependencies; operational rollback ready |
| G5 acceptance | Accept/reject/defer each evidence gate and residual risk | Evidence complete for named target; operator signs; activation decision explicit and separate |

Planning determines the dependency graph and literal commands; this table does not prescribe a
blind batch. Resolve installation from actual approved catalog observations against source:
S8 source/update/admin dependencies → S10A coordination → S10C legacy preparation → S10D pool →
S10E ownership → S11 evidence and legacy permissions. Include only actually missing/changed
objects. Do not replay all migrations or edit already-installed history. SQL dependencies precede
admission of dependent Bot behavior. A disabled routing flag can expose old uncoordinated writers;
it is not, by itself, proof of safe rollback or writer exclusion.

At each checkpoint present the exact packet delta and requested operation IDs. Record the
operator's answer against packet hash and targets. Changed command, target, source, identity or
write effect invalidates approval for the affected operation and requires review. Unrelated
approved groups may proceed only if their prerequisites remain satisfied.

## Evidence and test matrix

| Boundary | Retained/source evidence | New G4 evidence required |
|---|---|---|
| Bot source/static | Merged source, earlier full/focused tests, exact corrected Changes reviews, mirror restoration identity proof | Final release file/config/dependency hashes; bounded regression only for a real new delta |
| SQL source/static | Separate SQL #89, exact snapshots/migrations/manifest; 193 evidence + 454 permission assertions and five ScriptDom parses in final review | Installed bodies, signatures, grants, roles, shapes and version observations; static success cannot substitute |
| SQL engine/transactions | Authored gated fixtures and fake/offline DAL tests | Actual restore; positive controls and independent stale owner/fence/version/NULL rejection; concurrent close/admission; role collision/reapply; prepared/dispatch-intent close refusal and frozen terminal append |
| Windows authority | Offline host/client/launcher tests | Exact tokens/ACLs, authenticated peer access, busy-pipe pre-send acquisition, bounded child hello/cancel/drain, retained process handles and no escaped delayed effects |
| Provider | Source contracts and fake adapters | Fresh key custody, exact granted scopes, request uncertainty/finality, byte-exact readback, protected exclusions, retirement recovery and private reuse |
| Delivery/Discord | Closed callers, registration/intents, fairness/coalescing and owned shutdown source | Named cases for immutable running A, eligible pending B, ordered daily work, nested ownership, lost acknowledgement and shutdown uncertainty |
| Deployment/G5 | User reports no bot-machine update; no runtime attestation from merges | Exact production build, startup/admission evidence, observation window, residual gate decisions and explicit operator acceptance |

Candidate files to inspect/select, not commands to execute now:
`tests/test_export_authority_boundaries.py`, `tests/test_export_authority_launcher.py`,
`tests/test_export_execution_authority.py`, `tests/test_export_execution_host.py`,
`tests/test_export_execution_protocol.py`, `tests/test_export_runtime_composition.py`,
`tests/test_export_enrollment_service.py`, `tests/test_export_execution_sql_integration.py`,
`tests/test_kvk_export_sql_integration.py`; SQL `validation/kvk_source/s11_export_execution_evidence.sql`
and `validation/kvk_source/s11_export_legacy_module_permissions.sql`, plus the exact new cases
mapped to S10C/D/E ownership/rollover dependencies. Keep live authorization variables disabled
until the corresponding exact operations are approved. Pipe acquisition may retry before send;
connected requests/replies must never be replayed after uncertainty.

S6-OPS01, S6-PERF01 and S6-CAP01 remain open. Retain uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c` and every
retained database/file. S8A's six scripts/VERIFYONLY, S8B's 50 cases/**actual restore versus
offline history**, and S8C's seven local checks stay distinct. S10C/D/E source authoring is not
installation/provider proof. Reuse prior evidence; do not rerun predecessors to populate a checklist.

## Invariants and stop conditions

Preserve fixed season source and source/endpoint/UpdateID contracts, authoritative aggregates/DKP,
supplied overall/B0 and the exact 11-10 / 12-10 / final 13-10 / authorized 14-10 endpoint chain.
Preserve immutable running A, eligible pending coalescing, daily ordering/history and account
fairness, registration-aware intents, complete S10C provenance/spool and nested ownership.
Use exact owner/fence/version CAS, append-only assignments/dispositions, byte-exact receipts,
P/Q/R capacity, 9,000,000-cell parts and 8/16 pool bounds. No SQL transaction spans provider I/O
or waits. No generation relabeling, guessed receipt mapping or silent legacy fallback.

Rollover closes admission and drains/reconciles. Prove old-writer termination and perform approved
private clear/readback before audited reuse. Interrupted retirement requires explicit journal
recovery, read-before-clear, nested versioned ownership and fresh publication probe after owner
revocation, with proof of no delayed effects. Unknown outcomes require reconciliation, never
blind retry. Unknown cannot establish termination/proof; terminal job state or lease age cannot
release claims. Frozen evidence streams may append legal terminal outcomes but cannot rewrite
history; unresolved prepared/dispatch-intent requests block closure.

Stop the affected group on target/hash/ACL/permission drift, unexpected writer, preservation
failure, uncertain request, incomplete termination/restore, provider mismatch, unsupported SDK
semantics, ownership/version conflict or breached budget. Capture the exact state before choosing
reconciliation/recovery. Do not continue by weakening a guard or by using an administrator identity
to make a restricted-identity test pass.

## Rollback and G5 acceptance record

Before installation, rollback is continued non-installation and closed admission. Afterwards,
close admission, drain owned work, preserve uncertain claims and reconcile requests. Retain SQL
history, receipts, origins, journals, dispositions, configuration/source pins, protected evidence
and all retained files. Prove termination of old writers and absence of delayed effects before
reuse. Pin a compatible serving version explicitly; do not re-enable copied-key legacy writers.
Use separately reviewed forward SQL fixes when installed state needs correction, not destructive
drops or edits to deployed history. List any reverse operation with its exact eligibility and
backup/restore consequences before approval. No generic reset/clean/drop/restore-over-retained-data.

G5 records each gate's target/source/packet identity, evidence location/hash/time, observed result,
operator, accept/reject/defer decision, limitations, unresolved risk, owner and follow-up. Include
S6 open gates, retained uncertainties, SQL restore/installation/transactions, all-writer exclusion,
containment/provider recovery, shutdown, fairness/capacity and deployed behavior. Missing required
evidence remains open; local/CI success cannot be relabelled as acceptance. Overall acceptance
and activation require explicit operator decisions after reviewing the complete record.

## Documentation, review and delivery

Start with S7's eight documents: release readiness, release evidence, integration contract,
implementation manifests, post-S6 handoff, local SQL guidance, README-DEV and reference index.
Update the new closeout, this pack/starter, programme/task index and relevant environment/runbooks
when outcomes change. Preserve predecessor closeouts and both sides of the S10E archive identities.

Planning-only Markdown has a precise documented security skip. For any genuine new runtime or
deployment/configuration patch, route security to **Changes, Deep off**, on the exact immutable
target; assess real SQL deltas separately. Select offline tests and architecture/deferred/security
routing/registration/import gates appropriate to the delta. SQL/provider/deployment execution is
not part of those local checks.

The approved mirror filter repair is the genuine Bot change carrying this handoff; verify every
pending Bot file by filename plus previous_filename or exact content/base/absence proof before
any separately authorized publication. The five restored files already exist identically in
production: promotion must omit duplicate additions using that proof and carry the filter/docs
delta. No repository history mixing or separate Bot documentation PR. On 2026-09-25 the operator
explicitly authorized a separate SQL documentation closeout PR for `docs/SQL_DELIVERY_LOG.md`
and `migrations/README.md`, to be reviewed alongside this Bot repair/handoff. That authorization
supersedes the earlier deferral for those two entries; no SQL implementation is invented.
Recheck both PR outcomes before G4. Future preparation-only edits retain their same-repository
grouping if no implementation or explicit documentation publication is authorized.
