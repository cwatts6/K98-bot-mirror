# S7 exact implementation manifests and delivery
## S11 final client compatibility delta — 2026-09-25

The final local compatibility correction changes these existing pending paths:

- core/export_execution_host.py: shared client opener and matching narrow server access mask.
- services/export_runtime_composition.py: Bot client uses that opener.
- scripts/run_export_provider_child.py: supervised child uses that opener.
- tests/test_export_authority_boundaries.py: five additional fake-native access/cleanup cases.

The explicit mask adds FILE_WRITE_ATTRIBUTES so both clients can select message-read mode,
while continuing to exclude FILE_CREATE_PIPE_INSTANCE. No protocol, SQL, credential, endpoint,
registration or retry contract changes. The 704-pass final focused result follows this delta;
the 5,812-pass full run precedes it. The final exact Bot Changes review must name this tree.
The earlier correction and complete pending implementation/document union below remain intact.

## S11 authority boundary correction delta — 2026-09-25

The approved local completion includes corrections in these exact Bot paths:

- core/export_execution_host.py
- scripts/run_export_authority.py
- scripts/run_export_provider_child.py
- scripts/enroll_export_output_pool.py
- tests/test_export_authority_launcher.py
- tests/test_export_authority_boundaries.py (new offline boundary regression file)

The native-only shared bootstrap remains in the existing authority launcher. No new launcher,
service, dependency, deployment action or SQL change is introduced. The complete earlier source
manifest and every pending Bot document remain in the genuine implementation delivery union.
ENV_REFERENCE records the source-only deployment and trusted-launcher preconditions. Actual
Windows behavior remains G4 evidence; source tests do not replace it. Both sides of the S10E
archive moves and the separate SQL documentation grouping remain mandatory.

## S11 actual authority composition delta — 2026-09-24

The one-host/fresh-key proposal is approved. The following exact existing pending Bot paths
changed in this continuation; all previous pending source and mandatory documentation remain.
The candidate SHA-256 inventory and entry comparison are retained under the ignored local
.codex_artifacts/s11-authority-composition directory. No SQL byte changed in this continuation.

- bot_instance.py
- core/export_execution_host.py
- gsheet_module.py
- kvk/dal/kvk_admin_dal.py
- kvk/dal/kvk_all_import_dal.py
- kvk/dal/source_output_pool_dal.py
- kvk/services/kvk_admin_service.py
- kvk/services/new_source_export_service.py
- kvk/services/source_export_operator_service.py
- kvk_all_importer.py
- player_stats_cache.py
- proc_config_import.py
- processing_pipeline.py
- scripts/run_export_authority.py
- scripts/run_export_provider_child.py
- services/export_coordination_service.py
- services/export_execution_dal.py
- services/export_provider_adapter.py
- services/export_reconciliation_service.py
- services/export_runtime_composition.py
- services/legacy_export_snapshot_dal.py
- services/legacy_export_snapshot_service.py
- stats_module.py

The two actual DAL helpers kvk/dal/kvk_all_import_dal.py and kvk/dal/kvk_admin_dal.py were required
to validate the producer connection before its first write. new_source_export_service.py now
separates positive content damage from uncertainty. source_output_pool_dal.py and
export_provider_adapter.py receive formatting only in this continuation; their earlier pending
behavior remains part of the complete runtime patch. These are actual caller/helper amendments
to the preceding proposal, not new import features or invented runtime requirements.

Reused without a new semantic change: export_rollover_evidence.py, export_retirement_evidence.py,
export_retirement_recovery_evidence.py, source_output_pool_service.py and
new_source_delivery_service.py. commands/admin_cmds.py already delegates to the now-bound export
function; upload_routes/kvk_all_route.py delegates to DL_bot's existing thread-only offload. Their
source needs no change. event_data_loader.py's unrelated read-only calendar access is not an
S11 shared writer and is not moved into this account's request budget.

Exact test files changed in this continuation:

- tests/test_export_authority_launcher.py
- tests/test_export_execution_host.py
- tests/test_export_reconciliation_service.py
- tests/test_export_runtime_composition.py
- tests/test_gsheet_module.py
- tests/test_legacy_export_snapshot.py

All runtime/test paths in the earlier complete implementation manifests remain included in the
final Bot Changes review. Every pending Bot document, this S11 pack/starter, S10D/S10E closeouts
and both S10E archive sides belong in the next genuine authorized Bot implementation PR. SQL's
pending closeouts remain with its separate actual implementation PR. Preserve filename and
previous_filename or exact content/base-absence evidence; do not replace the union by counts.
No stage, commit, push, PR, promotion or deployment is authorized here.


## S11 remaining authority composition scope — 2026-09-24

The [one-host/fresh-identity contract](integration_contract_and_consumer_matrix.md#s11-remaining-host-and-credential-decision--2026-09-24)
is a concrete proposed credential amendment awaiting the operator's answer. The existing
issuer/caller/runtime implementation remains authorized; no live cutover or new SQL object
is inferred. The exact remaining implementation owners are below. Every proposed runtime
and test path was verified to exist; record actual edits and justified untouched paths when
authoring resumes. This table does not replace the full mandatory pending-document union.

| Exact Bot path | Remaining responsibility |
|---|---|
| core/export_execution_host.py | Validate the selected local authority and protected evidence/custody boundary |
| scripts/run_export_authority.py | Bind the sole-host deployment packet and construct the trusted local issuer |
| scripts/run_export_provider_child.py | Match the exact provisioned provider identity/key to the protected contract |
| services/export_execution_dal.py | Complete application metadata/permission observations and exact proof persistence |
| services/export_runtime_composition.py | Immutable deployment/runtime bundle, complete service factory and task lifetime binding |
| services/export_reconciliation_service.py | Trusted issue orchestration using the existing publication/origin/catalogue probes |
| services/export_rollover_evidence.py | Connect existing drain/completion evidence to the issuer |
| services/export_retirement_evidence.py | Connect ordinary retirement evidence to the issuer |
| services/export_retirement_recovery_evidence.py | Connect exact journal recovery evidence to the issuer |
| services/export_coordination_service.py | Resolve the admitted bundle, maintain one worker, close admission and drain |
| services/legacy_export_snapshot_service.py | Bind complete producer/capture/export scopes without losing nested owners |
| services/legacy_export_snapshot_dal.py | Apply complete readiness on the producer's actual SQL session |
| kvk/services/source_export_operator_service.py | Resolve the same runtime's operator/proof/recovery services |
| kvk/services/source_output_pool_service.py | Preserve exact proof/stream ownership through rollover and recovery |
| kvk/services/new_source_delivery_service.py | Complete owned delivery and retirement composition |
| bot_instance.py | Use the existing ready and teardown hooks |
| processing_pipeline.py | Bind the complete daily pipeline and draining thread offloads |
| kvk_all_importer.py | Bind legacy import/capture/automatic export |
| commands/admin_cmds.py | Thin handoff for the existing manual scan export |
| kvk/services/kvk_admin_service.py | Bind existing legacy recompute/export actions |
| proc_config_import.py | Bind both configuration branches and standalone scheduling |
| stats_module.py | Bind independently callable daily procedure work |
| player_stats_cache.py | Bind standalone output refresh while preserving inherited ownership |
| gsheet_module.py | Reuse the authority-backed compatibility calls and registered destinations |
| services/export_provider_adapter.py | Reuse recorded per-owner provider execution |


Exact existing test owners:

- tests/test_export_authority_launcher.py
- tests/test_export_execution_host.py
- tests/test_export_execution_authority.py
- tests/test_export_execution_protocol.py
- tests/test_export_execution_sql_integration.py
- tests/test_export_runtime_composition.py
- tests/test_export_reconciliation_service.py
- tests/test_export_retirement_evidence.py
- tests/test_export_retirement_recovery_evidence.py
- tests/test_export_rollover_evidence.py
- tests/test_export_provider_adapter.py
- tests/test_kvk_export_coordination.py
- tests/test_legacy_export_snapshot.py
- tests/test_kvk_export_operator.py
- tests/test_kvk_output_rollover.py
- tests/test_kvk_source_delivery.py
- tests/test_processing_pipeline.py
- tests/test_startup_lifecycle.py
- tests/test_proc_config_import.py
- tests/test_gsheet_module.py

This decision checkpoint modifies only the integration contract, this implementation manifest,
release readiness and release evidence documents. It does not change any Python or SQL byte
after the NULL guard checkpoint. Both repositories' indexes and all comparison anchors remain
unchanged. The 59 original document identities and both exact S10E archive source/destination
pairs are retained, with filename/previous_filename plus content/absent-at-base evidence.
Every pending Bot document, S11 pack/starter and S10D/S10E closeout still belongs in the next
genuine authorized Bot implementation PR. SQL closeouts remain with the separate actual SQL
implementation PR. No standalone documentation PR or Git publication is authorized.


## S11 SQL NULL guard correction manifest — 2026-09-24

Proposed local correction scope following the completed frozen SQL review. Every path below
already exists as pending work; preserve its earlier content and all other pending paths.
SQL and Bot keep separate histories. This proposal adds no new migration identity.

| Repository | Exact path | Proposed correction |
|---|---|---|
| SQL | sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql | Explicit NULL ExpectedVersion rejection |
| SQL | migrations/20260924_001_export_execution_evidence.sql | Synchronize event payload/comparison literal; reject NULL definitions for all five APIs |
| SQL | deploy/Test-ExportExecutionEvidenceContracts.ps1 | Validate each exact NULL guard and source/migration correspondence |
| SQL | validation/kvk_source/s11_export_execution_evidence.sql | Fail closed on unknown permission or administrator-token observations |
| SQL | docs/SQL_DELIVERY_LOG.md | Add actual correction and validation evidence without rewriting closeouts |
| SQL | migrations/README.md | Record corrected draft and unchanged installation/forward-fix boundary |
| Bot | tests/test_export_execution_sql_integration.py | Author exact NULL/stale/valid event-version cases under existing disabled disposable SQL gates |
| Bot | docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md | Retain design and final contract result |
| Bot | docs/reference/kvk_source_migration/integration_implementation_manifests.md | Retain this exact scope and actual delta |
| Bot | docs/reference/kvk_source_migration/release_evidence_log.md | Add measured offline results and exact review target |
| Bot | docs/reference/kvk_source_migration/release_readiness_and_rollback.md | Maintain approval, tests, installation and rollback matrix |

The corrected SQL source needs its own new immutable Changes target, Deep off; the completed
review is evidence only for its frozen pre-correction digest. The eventual complete Bot
runtime patch still needs its separate Changes review after composition settles. SQL fixture
and Python SQL integration changes are authoring only; their engine execution is not proposed.

The current continuation edits only the four Bot Markdown documents in this table. All Bot
Python and every SQL path remain byte-exact to the legacy-module checkpoint. No Git index,
branch or comparison anchor changed. sql-review-scope-delta.json records the exact difference.
The entire original 59-document identity manifest and both S10E filename/previous_filename
archive proofs are rechecked, not replaced by counts. All pending Bot documents, pack/starter,
S10D/S10E closeouts and both archive sides still belong in the next genuine authorized Bot
implementation PR. SQL closeouts accompany the separate actual SQL implementation PR. No
standalone docs PR, repository mixing or publication is authorized by this proposal.



## S11 NULL guard correction delivery — 2026-09-24

The approved correction changes exactly the eleven existing paths in the following manifest:
six SQL paths, one Bot test and these four Bot checkpoint documents. The six SQL copies were
applied only after exact before/after hashes matched. No other pending source byte changed
in this correction. sql-null-guards-delta.json records the exact repository/path union.

All 59 original document identities and both S10E archive source/destination identities are
rechecked against retained content and Git-base evidence. Indexes, branches and anchors stay
unchanged. Every pending Bot document, S11 pack/starter, S10D/S10E closeouts and both archive
sides remain grouped with the next genuine authorized Bot implementation PR. SQL closeouts
remain with the separate actual SQL implementation PR. No publication occurs here.

## S11 approved legacy permission delivery manifest — 2026-09-24

The operator approved the preceding scope amendment. The implementation changes exactly six
existing pending Bot Python files: services/export_execution_dal.py,
services/export_runtime_composition.py, services/legacy_export_snapshot_dal.py,
tests/test_export_runtime_composition.py, tests/test_legacy_export_snapshot.py and
tests/test_export_execution_sql_integration.py. tests/test_export_authority_launcher.py was
an approved possible target but required no edit; its tests were included in validation.

Seven existing Bot documents receive additive checkpoint notes: ENV_REFERENCE.md,
local_sql_development.md, runbook_startup.md and the integration contract, this manifest,
release evidence and release readiness documents in kvk_source_migration.

SQL changes are the exact five new paths approved below: the 20260924_002 forward/reverse
scripts, deploy/export_legacy_module_permission_manifest.json,
deploy/Test-ExportLegacyModulePermissionContracts.ps1 and
validation/kvk_source/s11_export_legacy_module_permissions.sql, plus additive updates to
docs/SQL_DELIVERY_LOG.md and migrations/README.md. All seven SQL paths were applied with
before/after hash guards. Existing business procedures and prior SQL migration bytes remain
outside this edit. SQL source and Bot code keep their separate Git histories and review targets.

All original pending document identities, recovered evidence and both S10E archive move sides
remain mandatory. The eventual genuine authorized Bot implementation PR includes every pending
Bot document, this pack/starter and S10D/S10E closeouts; verification uses exact filename and
previous_filename or merged/content/absent-at-base proof, never counts. SQL closeout documents
accompany the separate actual SQL implementation PR. No standalone docs PR, publication or
deployment is implied by the authoring checkpoint.

## S11 legacy SQL permission scope amendment — 2026-09-24

New proposal only; the additional implementation below is not yet approved. The existing evidence
SQL manifest does not include certificate principals, module signatures/countersignatures or the
master/server-side permission delivery required to isolate privileged legacy calls. See the
[source-backed design and tests](integration_contract_and_consumer_matrix.md#s11-legacy-sql-privilege-isolation-proposal--2026-09-24).
This is a separate actual SQL scope assessment, not an instruction to grant broad Bot access.

| Repo | Action | Exact additional implementation path |
|---|---|---|
| SQL | Create | migrations/20260924_002_export_legacy_module_permissions.sql |
| SQL | Create | migrations/rollback/20260924_002_export_legacy_module_permissions_rollback.sql |
| SQL | Create | deploy/export_legacy_module_permission_manifest.json |
| SQL | Create | deploy/Test-ExportLegacyModulePermissionContracts.ps1 |
| SQL | Create | validation/kvk_source/s11_export_legacy_module_permissions.sql |
| SQL | Modify | docs/SQL_DELIVERY_LOG.md |
| SQL | Modify | migrations/README.md |
| Bot | Modify existing pending path | services/export_execution_dal.py |
| Bot | Modify existing pending path | services/export_runtime_composition.py |
| Bot | Modify existing pending path | services/legacy_export_snapshot_dal.py |
| Bot | Modify existing pending path | tests/test_export_runtime_composition.py |
| Bot | Modify existing pending path | tests/test_export_authority_launcher.py |
| Bot | Modify existing pending path | tests/test_export_execution_sql_integration.py |
| Bot | Modify existing pending path | tests/test_legacy_export_snapshot.py |
| Bot | Modify existing pending path | docs/reference/ENV_REFERENCE.md |
| Bot | Modify existing pending path | docs/reference/local_sql_development.md |
| Bot | Modify existing pending path | docs/reference/runbook_startup.md |
| Bot | Modify existing pending path | docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md |
| Bot | Modify existing pending path | docs/reference/kvk_source_migration/integration_implementation_manifests.md |
| Bot | Modify existing pending path | docs/reference/kvk_source_migration/release_evidence_log.md |
| Bot | Modify existing pending path | docs/reference/kvk_source_migration/release_readiness_and_rollback.md |

The five proposed SQL paths were confirmed absent; ordinal 002 is available on the current date.
Recheck date/availability before authoring; do not overwrite another change or rename a merged
migration. The proposed JSON is a source-reviewed module/capability inventory, not private key
material, real account credentials or a runtime-supplied signing allowlist. No existing procedure
body, output table, old migration, sheet configuration or private credential is an edit target.
Any required exception must be made concrete and scoped before implementation. This amendment
leaves the already approved issuer/caller/runtime composition scope and all release gates intact.

This review added only four existing Bot documents: this manifest, the integration contract,
release readiness and release evidence. The 434-test permission checkpoint's Python stays exact,
and every SQL byte/deletion stays unchanged. All mandatory pending Bot documents, this pack/starter,
S10D/S10E closeouts and both exact archive move identities still accompany the next genuine
authorized Bot implementation PR. SQL implementation and pending SQL closeout docs stay in the
separate actual SQL implementation PR. No standalone documentation PR or Git publication.

## S11 fixed coordination permission continuation — 2026-09-24

The approved continuation changes these exact existing pending Bot paths:

- services/export_execution_dal.py
- services/export_runtime_composition.py
- tests/test_export_runtime_composition.py
- tests/test_export_authority_launcher.py
- docs/reference/ENV_REFERENCE.md
- docs/reference/runbook_startup.md
- docs/reference/kvk_source_migration/release_evidence_log.md
- docs/reference/kvk_source_migration/release_readiness_and_rollback.md
- docs/reference/kvk_source_migration/integration_implementation_manifests.md

The fixed SQL observation/contract moves to version 2, covering export coordination object and
column permissions before authority/enrollment admission. The outer protected manifest and
enrollment profile retain version 1. No SQL source, grant or operational state changes in this
continuation. See the [exact source/test record](release_evidence_log.md#s11-fixed-coordination-permission-contract--2026-09-24)
and [remaining gates](release_readiness_and_rollback.md#s11-fixed-coordination-permission-continuation--2026-09-24).
Other pending Bot paths/deletions and all SQL bytes/deletions are preserved against the preceding
proof-acknowledgment checkpoint. Every original pending document and both archive move identities
remain subject to exact filename/previous_filename and merged/content/absent-at-base verification.
The eventual genuine authorized Bot implementation PR still includes all pending Bot documents,
this pack/starter and S10D/S10E closeouts. SQL closeout documents accompany the separate next actual
authorized SQL implementation PR. No standalone documentation PR or publication occurs here.

## S11 exact proof acknowledgment continuation — 2026-09-24

The approved continuation changes these exact existing pending Bot paths:

- services/export_execution_dal.py
- tests/test_export_execution_authority.py
- docs/reference/kvk_source_migration/release_evidence_log.md
- docs/reference/kvk_source_migration/release_readiness_and_rollback.md
- docs/reference/kvk_source_migration/integration_implementation_manifests.md

The persistence boundary validates complete proof inputs before SQL and the exact returned
identity/hash/receipt bytes after the batch completes. No issue retry, trusted finality producer,
provider operation or new SQL behavior is introduced. See the
[exact source/test record](release_evidence_log.md#s11-exact-proof-persistence-acknowledgment--2026-09-24)
and [remaining implementation/deployment distinction](release_readiness_and_rollback.md#s11-exact-proof-acknowledgment-continuation--2026-09-24).
Every other pending path/deletion, original document identity, both archive sides and comparison
anchor remains subject to the existing exact-content preservation checks. Eventual Bot delivery
still includes every pending Bot document and this pack/starter; SQL authoring/closeouts remain
separate. No standalone documentation PR or Git publication is authorized by this checkpoint.

## S11 origin-bound probe continuation — 2026-09-24

The approved continuation changes these exact existing pending Bot paths:

- services/export_reconciliation_service.py
- services/export_retirement_evidence.py
- services/export_retirement_recovery_evidence.py
- services/export_rollover_evidence.py
- tests/test_export_reconciliation_service.py
- tests/test_export_retirement_evidence.py
- tests/test_export_retirement_recovery_evidence.py
- tests/test_export_rollover_evidence.py
- tests/test_export_enrollment_service.py
- docs/reference/kvk_source_migration/release_evidence_log.md
- docs/reference/kvk_source_migration/release_readiness_and_rollback.md
- docs/reference/kvk_source_migration/integration_implementation_manifests.md

The five probe paths now bind complete authenticated origins before provider admission and
recheck them before the final current-snapshot read. See the [source/evidence checkpoint](release_evidence_log.md#s11-origin-bound-reconciliation-probes--2026-09-24).
No SQL source, deployment configuration, credential or actual provider state changed. All other
pending files/deletions, exact archive sides and mandatory Bot/SQL document grouping remain intact.
Trusted proof issuance, complete runtime/caller factories, final validation and exact G4/G5 gates
remain required; origin authentication alone establishes no external-writer exclusion or finality.

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

The approved uninstalled S11 SQL contract and Bot binding now support the exact unowned
closing-operation observational scope. Legacy/configuration callers also bind the actual
authority-stream interface. Exact paths and offline evidence are recorded in the
[closing-probe checkpoint](release_evidence_log.md#s11-closing-probe-binding-checkpoint--2026-09-24).
The complete trusted proof issuer, readiness and all-caller composition remain incomplete and
disabled. This does not authorize G4/G5 or publication. Full pending Bot and separate SQL document
grouping remains unchanged; all earlier dated checkpoints are retained below.


## S11 proof-consumption continuation — 2026-09-24

Six S11 settlement paths now resolve trusted SQL ProofID in their existing locked snapshot
transactions. Private-journal verification is implemented as a prerequisite to proof issuance;
the complete issuer, launcher and caller composition remain unfinished and disabled. See the
[current continuation evidence](release_evidence_log.md#s11-continuation-trusted-proof-consumption--2026-09-24)
for exact files and source-only validation. Earlier checkpoint statements remain historical.


## S11 implementation status — 2026-09-24

The operator has approved the expanded Bot and separate SQL proposal below. Evidence foundations, optional DAL gates and the recorded SDK bridge are now authored; launcher, proof producer and complete caller composition are still unimplemented. The executable manifest is no longer empty. Exact authored paths are recorded in the checkpoint artifact manifest. The full mandatory pending-document union remains part of the next genuine implementation PR. See [checkpoint](release_evidence_log.md#s11-approved-implementation-checkpoint--2026-09-24).


## S11 proof-mechanism manifest amendment — 2026-09-24

The operator approved a bounded proof-mechanism design pass, not implementation. The
[recommended mechanism](integration_contract_and_consumer_matrix.md#s11-proof-mechanism-decision-proposal--2026-09-24)
requires additional real infrastructure. This amendment supersedes the earlier proposal's
two-module-only assumption and initial no-SQL-need conclusion. **Current executable edit manifest
is still empty in both repositories.** Today's edits remain the same eight preparation documents.

### Exact additional Bot paths proposed for G3

Take the union with the earlier 22-path code/test proposal below and the full 57-identity pending
documentation manifest. Listed existing supporting contracts now become proposed edit targets
only for the stated proof boundary. New filenames are proposals, not existing capabilities.

| Action | Exact Bot path | Reason |
|---|---|---|
| Create | `services/export_execution_authority.py` | Trusted stream lifecycle, request dispatch/result protocol, credential ownership and closure |
| Create | `services/export_execution_protocol.py` | Bounded typed IPC messages, canonical identities, method/result allowlists; no arbitrary callable/URL |
| Create | `services/export_execution_dal.py` | Parameterized evidence transition/read APIs and same-transaction ProofID validation |
| Create | `core/export_execution_host.py` | Windows named-pipe authentication/DACL and exact process-handle/Job Object containment |
| Create | `scripts/run_export_authority.py` | Explicit standalone supervisor entry, no automatic service installation |
| Create | `scripts/run_export_provider_child.py` | Fixed supervised provider runner; no unmanaged credential-bearing descendants |
| Modify | `services/export_provider_adapter.py` | Route owned legacy/config SDK calls through request-recorded execution; retain budget/uncertainty semantics |
| Modify | `kvk/services/new_source_export_service.py` | Route new-source read/mutation/retirement/rollover calls through same boundary; no direct SDK bypass |
| Modify | `gsheet_module.py` | Bind compatibility/provisioning request paths to authority in admitted mode; preserve output/header contracts |
| Modify | `services/export_coordination_dal.py` | Observe probe/stream admission and load trusted ProofID in existing settlement/CAS transactions |
| Modify | `services/legacy_export_snapshot_dal.py` | Preparation admission observes authority/probe gate without nested lock inversion |
| Modify | `kvk/dal/source_output_pool_dal.py` | ProofID and stream/operation admission for rollover, retirement and nested recovery; preserve exact CAS/audit |
| Modify | `kvk/services/source_output_pool_service.py` | Pass trusted proof references and child stream identities through existing lifecycle |
| Modify | `kvk/services/new_source_delivery_service.py` | Bind owned delivery/retirement streams without changing immutable generation or receipt semantics |
| Create | `tests/test_export_execution_authority.py` | Dispatch/closure races, outcome matrix, restart gaps, evidence permissions and no retries |
| Create | `tests/test_export_execution_protocol.py` | Peer/identity/method/body bounds, duplicate and malformed IPC, no arbitrary execution |
| Create | `tests/test_export_execution_host.py` | Mocked OS contract plus separately opt-in isolated Windows containment cases |
| Create | `tests/test_export_execution_sql_integration.py` | Disabled exact-target evidence/permission/concurrency tests; never connect by default |
| Modify | `tests/test_export_provider_adapter.py` | Each escaped call is recorded and paced; retry distinction; completion/checkpoint loss |
| Modify | `tests/test_gsheet_module.py` | All admitted compatibility/provisioning routes recorded or refused; complete formatting/config coverage |
| Modify | `docs/reference/ENV_REFERENCE.md` | New manifest/identity/storage requirements and disabled startup, no credentials or actual config edits |
| Modify | `docs/reference/runbook_startup.md` | Supervisor readiness, exact protocol/schema/account gating and no old writers |
| Modify | `docs/reference/runbook_shutdown.md` | Child drain/termination evidence and retained unknown requests |
| Modify | `docs/reference/runbook_diagnostics.md` | Read-only probe purpose, ProofID inspection and unavailable historical evidence |

The four reference documents above already belong to the mandatory 57-document union. Existing
`requirements.txt` already includes Windows pywin32; no dependency change is proposed. Keep
`run_bot.py`, `process_utils.py`, `singleton_lock.py`, old migration files and actual credentials/
`.env`/sheet config unchanged. The authority launcher is separately provisioned under G4 rather
than embedding a second service into the bot watchdog. Any required exception needs a revised scope.

### Exact separate SQL proposal — no files authored

Source search at SQL `2352a898881d4b74d6eec153bb3cb381d6162041` found none of the five proposed
evidence entities below. Existing attempt/preparation/budget fields do not supply equivalent
per-request identities or independent authority. These are proposed new objects, not inferred live
schema. Reserve the following filename only if authoring occurs on 2026-09-24 and ordinal 001
remains free; otherwise resolve the actual-date/free-ordinal name before approval/authoring. Never
rename a merged migration.

| Action | Exact SQL path |
|---|---|
| Create | `migrations/20260924_001_export_execution_evidence.sql` |
| Create | `sql_schema/dbo.ExportExecutionSession.Table.sql` |
| Create | `sql_schema/dbo.ExportExecutionStream.Table.sql` |
| Create | `sql_schema/dbo.ExportProviderRequest.Table.sql` |
| Create | `sql_schema/dbo.ExportProviderRequestEvent.Table.sql` |
| Create | `sql_schema/dbo.ExportReconciliationProof.Table.sql` |
| Create | `sql_schema/dbo.usp_ExportExecutionSessionTransition.StoredProcedure.sql` |
| Create | `sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql` |
| Create | `sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql` |
| Create | `sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql` |
| Create | `validation/kvk_source/s11_export_execution_evidence.sql` |
| Create | `deploy/Test-ExportExecutionEvidenceContracts.ps1` |
| Modify | `docs/SQL_DELIVERY_LOG.md` |
| Modify | `migrations/README.md` |

Schema is additive after S10E, with no historical request reconstruction, receipt rewrite, claims
release or activation. Define narrow SQL roles/EXECUTE permissions in the migration; actual login
mapping and removal of incompatible privileged access require explicit G4. No deploy-time default
login, password, broad grant or provider credential is invented. Schema design requirements:

| Proposed object | Required contract |
|---|---|
| ExportExecutionSession | SessionID UUID PK; registered authority/host/boot/executable/manifest identity; protocol version, state and monotonic Version; UTC open/closure; immutable identity, authenticated writer |
| ExportExecutionStream | StreamID UUID PK/session FK; exactly one typed job/preparation/output-operation owner plus nested token where applicable; account/resource-set/registration/epoch and pinned owner/fence; purpose mutation/probe; CAS state, final sequence/event digest and OS closure evidence; probe retains referenced original claims |
| ExportProviderRequest | RequestID UUID PK; immutable StreamID/sequence unique; allowed method/operation, complete target scope, payload hash/reference and request kind; no arbitrary endpoint; exact membership and non-cascading FKs |
| ExportProviderRequestEvent | Immutable event ID and RequestID/sequence unique; prepared/dispatch_intent/succeeded/not_sent/unknown transitions enforced by append procedure; bounded response classification/hash/reference and SQL UTC; no UPDATE/DELETE API; no guessed success |
| ExportReconciliationProof | ProofID UUID PK; authenticated issuer session, purpose/snapshot/registration/claim versions, closed-stream/request membership digest and immutable bounded outcome/evidence; same ProofID cannot change content; audit associates settlement under existing CAS |

Resolve exact types, bounds, FK keys, indexes and transition predicates in the authorized SQL
physical-design step before dependent Bot authoring. Preserve account → sorted resource → owner
lock order, incorporating stream locks last; close/admission cannot acquire those in reverse.
No transaction spans I/O. Direct table DML to evidence is unavailable to ordinary Bot identities;
the authority appends through narrow procedures. Principals able to alter/grant evidence authority
cannot serve as untrusted Bot callers. Fixture tests must verify effective permissions, not only
the presence of GRANT/DENY text. Privileged administrators remain inside the declared trust boundary.

### Bounded implementation order and acceptance cases

Recommended separate reviewable units: (1) SQL evidence schema/procedures/disabled fixture;
(2) Bot authority/protocol/host/DAL plus offline tests, production defaults still closed;
(3) composition/caller/transport/proof integration and affected regressions. The first genuine
authorized Bot implementation PR must carry the entire pending document union. SQL carries its
own two closeouts in its actual SQL PR. No standalone docs PR or repository mixing. Later units
must not enable earlier scaffolding until all required contracts and proofs are present.

Required cases: freeze vs dispatch race; child exits before dispatch; crash after dispatch_intent;
success before durable result; durable result before budget/job acknowledgment; duplicate response;
IPC caller retry without SDK replay; OS handle/PID reuse; escaped descendant or failed Job Object
assignment; authority restart without closure; forged/other-account/stale ProofID; direct evidence
DML rejection; probe-vs-job/preparation/rollover contention; bounded GET retries; ambiguous create;
clear success with lost slot CAS versus clear response loss; nested recovery revoked then fresh
probe; history byte preservation. Every negative case retains existing claim/fence/version and
does not create provider mutation or capacity. Retained S6 uncertainties are not test fixtures.

Windows lifecycle tests that start disposable processes and SQL integration tests remain opt-in
with exact targets/operations; pure mocked tests are offline evidence only. No provider/Discord or
old fixture rerun follows. Required security setup remains Changes, Deep off, separate immutable
Bot and SQL targets. This Markdown-only design pass retains its precise scan skip.

## S11 preparation and proposed implementation manifests — 2026-09-24

Operator approval covers **preparation/design only**. The following runtime manifest is a bounded
proposal for review, not approved edits. Source truth and proof requirements are in the
[composition design](integration_contract_and_consumer_matrix.md#s11-composition-and-trusted-proof-design--2026-09-24).
The [release packet](release_readiness_and_rollback.md#s11-preparation-and-release-approval-packet--2026-09-24)
keeps implementation, Git delivery, G4 and G5 separate.

### Actual preparation edit manifest

All paths are Bot-relative. Modify exactly these eight existing documents; preserve previous
dated evidence and all other pending files byte-for-byte:

| Action | Exact path |
|---|---|
| Modify | `README-DEV.md` |
| Modify | `docs/reference/README.md` |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` |
| Modify | `docs/reference/local_sql_development.md` |

SQL edit manifest: empty. Its existing `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md` stay
pending unchanged. The complete next Bot PR must include all 57 identities in the
[S10E mandatory manifest](s10e_closeout_and_s11_handoff.md#exact-mandatory-next-pr-documentation-manifest),
plus any subsequent task-produced files. These eight edits do not replace that union. The S11
pack/starter and both S10D/S10E closeouts stay mandatory even though this step does not edit them.
No standalone documentation PR or manufactured implementation. If no genuine implementation PR
is authorized, retain the entire pending union. Grouping is settled.

### Proposed bounded Bot implementation manifest — not authorized

Proposed new modules have no current implementation. Their purpose is limited to the demonstrated
composition/proof gaps. Before G3, resolve the trusted authority, evidence durability and read-only
reconciliation admission design; otherwise keep the proposal at design review. Any expansion of
this manifest requires a reason and approval, not an inferred release mandate.

| Action | Exact path | Bounded purpose |
|---|---|---|
| Create | `services/export_runtime_composition.py` | Closed-by-default validated runtime bundle, immutable registration and scoped writer binding; reuse existing services/DALs |
| Create | `services/export_reconciliation_service.py` | Trusted evidence adapter, exact read-only probes and conservative proof construction; no fabricated termination/absence |
| Modify | `services/export_coordination_service.py` | Delegate configured factory to admitted bundle; retain existing worker/fairness/drain semantics |
| Modify | `services/legacy_export_snapshot_service.py` | Explicit composition binding seam for existing task/writer contexts; preserve nested ownership and complete spool capture |
| Modify | `kvk/services/source_export_operator_service.py` | Resolve admitted bundle and inject reconciler/RetirementRecovery; keep existing grouped actions and fresh authority |
| Modify | `bot_instance.py` | Pass admitted factory at existing ready hook and bind lifecycle-owned producers; preserve teardown ordering |
| Modify | `processing_pipeline.py` | Bind runtime over complete daily producer/capture/export orchestration and offloads |
| Modify | `kvk_all_importer.py` | Bind runtime over legacy ingest/recompute/capture/automatic export |
| Modify | `commands/admin_cmds.py` | Thin runtime handoff for existing manual scan-export entry |
| Modify | `kvk/services/kvk_admin_service.py` | Bind legacy admin recompute/export orchestration without changing public semantics |
| Modify | `proc_config_import.py` | Ensure both config branches and standalone scheduled entry use admitted runtime; collect provider reads before SQL |
| Modify | `stats_module.py` | Bind independently callable daily procedure entry; keep UPDATE_ALL2 transaction ownership |
| Modify | `player_stats_cache.py` | Bind independently callable output-refresh entry while preserving inherited owner |
| Create | `tests/test_export_runtime_composition.py` | Default closure, schema/registration/storage mismatch, all caller bindings and context propagation |
| Create | `tests/test_export_reconciliation_service.py` | Evidence authenticity/binding, stale snapshots, ambiguous requests, nested owners and read-only pacing |
| Modify | `tests/test_kvk_export_coordination.py` | Composed A/B/C, fairness, registration and shutdown regressions |
| Modify | `tests/test_legacy_export_snapshot.py` | Complete producer capture/provenance, nested owner, standalone and manual caller binding |
| Modify | `tests/test_kvk_export_operator.py` | Composed factory, fresh authority, no-op/status, repair and reconciliation |
| Modify | `tests/test_kvk_output_rollover.py` | Trusted drain/proof handoff, retirement recovery and pool preflight |
| Modify | `tests/test_kvk_source_delivery.py` | Exact owned delivery and retirement verifier injection, retained uncertainty |
| Modify | `tests/test_processing_pipeline.py` | Runtime scope survives asynchronous/thread boundaries and cancellation |
| Modify | `tests/test_startup_lifecycle.py` | Existing ready hook, single worker, closed defaults and no early clients |

The runtime proposal is conditional on the proof authority being implementable within these
boundaries. If it needs a supervisor change, additional durable SQL state, a new configuration
surface or credential protocol, return an exact amended manifest before coding. Do not hide that
work in this proposal. No SQL migration is presently justified. Existing `gsheet_module.py`,
`services/export_provider_adapter.py`, `services/export_request_budget.py`,
`services/export_snapshot_store.py`, `services/export_coordination_dal.py`,
`services/legacy_export_snapshot_dal.py`, `kvk/dal/source_output_pool_dal.py`,
`kvk/services/source_output_pool_service.py` and `kvk/services/new_source_delivery_service.py`
are supporting contracts to reuse and inspect, not automatic edit targets.

### Tests and evidence required after relevant authorization

| Layer | Exact existing/new owners | Required evidence |
|---|---|---|
| Composition | Proposed two new test files; `tests/test_startup_lifecycle.py` | No clients/storage creation when closed; exact protocol/registration; all entry points bind runtime; no duplicate worker |
| Coordination/adapters | `tests/test_kvk_export_coordination.py`, `tests/test_export_provider_adapter.py`, `tests/test_legacy_export_snapshot.py`, `tests/test_processing_pipeline.py` | Immutable A; eligible B→C; fair original ticket; daily order; SDK pacing; no transaction over I/O; complete capture; cancellation drains |
| Operator/pool | `tests/test_kvk_export_operator.py`, `tests/test_kvk_output_rollover.py`, `tests/test_kvk_source_delivery.py` | Fresh access, zero-provider no-op/status, explicit RepairID, P/Q/R, 9,000,000 cells, 8/16 bounds, journal recovery and fresh post-revocation proof |
| Unchanged source contracts | `tests/test_kvk_source_pairs.py`, `tests/test_kvk_source_recovery.py`, `tests/test_kvk_public_routing.py`, `tests/test_kvk_source_independent_consumers.py` | Only affected regressions: fixed source, complete UpdateID, supplied overall/B0, 11/12/13/14 endpoints, counterpart attestation and independent daily/target/history behavior |
| Real SQL | `tests/test_kvk_export_sql_integration.py`; SQL `validation/kvk_source/s10c_legacy_export_preparation.sql`, `validation/kvk_source/s10_output_pool_rollover.sql`, `validation/kvk_source/s10e_output_operation_ownership.sql` | Separately authorized new targets/cases: contention, independent stale owner/fence/version plus positive control, closing/replay, lost acknowledgment, nested recovery; authored fixtures are not results |

Preparation gates: `python scripts/validate_architecture_boundaries.py`,
`python scripts/validate_deferred_items.py`, `python scripts/validate_codex_security_routing.py`,
exact-path `python scripts/select_tests.py`, whitespace/relative-link/identity checks. Skip runtime
pytest, imports, registration and log-noise execution for this Markdown-only step.

For a later runtime patch, use exact-path selection and focused tests above, relevant lint/type,
smoke imports and command registration, then isolated full-suite/log-noise validation via
`scripts/analyse_pytest_log_noise.py`. SQL opt-in gates remain disabled in offline runs. Never
claim skipped transaction tests as passes. Retained predecessor outcomes remain historical.

Security routing: precise Markdown-only skip for this preparation at the current Bot anchor;
SQL unchanged by this step. A future executable patch requires Changes, Deep off, exact immutable
base/head or patch; separately review any genuine SQL delta. Resolve future revisions at that time.

### Delivery identity acceptance

Before staging and again at PR head/merge, reconcile the complete staged/unstaged/untracked/deleted
union against every exact path in the S10E manifest. Check `filename` AND `previous_filename`.
For delete/add presentation, verify source-present and archive-absent at base, source-absent and
exact archive content at head/merge. Use individual merged-content proof for any already delivered
identity; counts never prove inclusion. Preserve both S10E source deletions and both destinations.
Production delivery, if later authorized, follows the current patch-based Promotion Guide on
production/main; never mix mirror/production histories or Bot/SQL repositories.

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

## S9B implementation authorization — 2026-09-14

The operator approved the initial review and implementation plan with the two exact path
amendments: `commands/kvk_targets_card_posting.py` for send/edit/retry freshness, and
`docs/reference/canonical_command_reference.md` for existing grouped-command semantics.
The original 22 runtime/test paths remain in scope; the amended runtime/test scope is **23**.
The mandatory documentation carry-forward is now **35 physical paths**. The eventual Bot
union is **58 physical paths**, including both sides of both S9A archive moves. This approval
permits local implementation and offline validation/review, not staging, commits, publication,
live operations or activation. The original scope-only starter below is historical.
SQL's two pending documentation paths remain a separate SQL PR in the same delivery cycle.


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

2026-09-12. **S7 documentation/read-only work only; stop for contract/manifests review.**
The [contract and complete consumer matrix](integration_contract_and_consumer_matrix.md)
defines semantics. These are proposed implementation boundaries, not runnable task packs,
standing approval, deployment steps to execute now, or claims that proposed tests passed.

## 1. Summary

Resolve the missing ordinary routing with a fixed season choice and complete paired public
selection. Add durable export intent/admission across three consumers, export-only recovery
and safe file reuse. Preserve B0, independent aggregates/overall, exact endpoints, UTC,
semantic deduplication, daily SCANORDER and accepted predecessor evidence. S7-D01–D09 are
settled; only the contract's three evidenced technical tradeoffs need design review.

S7 actual edits are Markdown only. Bot entry/final target is the uncommitted handoff plus
S7 patch against `a2f148fa9bd4fb367fd46d0500a768c14fee915b`. SQL has no changes at
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`; local production/main remains
`a8c9c515066ca6ef079120b76dd160e3389badab`. No reset/pull/fetch, commit/push/PR/merge,
SQL connection, provider write, real import/export, Discord, restart, deployment or activation.

## 2. File manifest

### S7 actual deliverable and future PR carry-forward

The exact 23 paths and actions in [handoff section 2](post_s6_handoff_log.md#2-exact-next-slice-carry-forward-file-manifest)
plus the two Create paths below form a **25-path union**, counting archive deletions and
destinations separately. No path may be omitted as pre-existing work. Both S6 archive source
deletions and both destinations remain mandatory. Final local status is checked against this
union, including untracked files and empty index. No path is claimed already merged.

The next separately authorized slice PR must compare its actual Files changed (filename
and previous_filename) against this union plus its separately approved implementation manifest.
Any omitted path requires exact merge/ancestor/content evidence. No PR exists for this S7
delta, so remote Files changed verification is a future gate, not a claimed current result.

### Ordered PR-sized implementation boundaries

Effort is an engineering estimate in focused working days, including focused tests and review
fixes, excluding approval/provider/SQL-environment wait. It is based on the actual missing
seams and accepted reuse, not measured implementation throughput. Risk remains high for
concurrency/old-worker recovery. Do not execute multiple boundaries under S7 approval.

| Boundary | Result and dependency | Estimate / principal risk |
|---|---|---|
| S8A SQL | Add fixed source, update/public pointer and immutable intent schema; review migration classification separately | 2–3 days; existing mixed-history classification |
| S8B Bot | DAL/services enforce source/pair/publication/intent, preserve endpoint chain and accepted calculations | 3–5 days; partial selection bypass and stale builders |
| S8C Bot | Intake/admin pairing and source onboarding UX using S8B; no new top-level command | 1–2 days; stale/unauthorized confirmation |
| S9A Bot | Ordinary reporting/dispatch resolver and availability/caches; S8B/C | 2–3 days; mixed blocks/legacy normalization |
| S9B Bot | Stats/target card context and grouped admin source dispatch; S9A | 2–3 days; legacy camp leakage or wrong cohort |
| S10A SQL | General export jobs/resources/budget/attempt-part schema; S8A intent contract | 2–3 days; lock/state integrity |
| S10B Bot | Queue worker, pinned generations and durable budget; S10A and S8B | 3–5 days; latest-selection checks currently abort A when B arrives |
| S10C Bot | Legacy/scan automatic/manual adapters, immutable snapshots and common provider client pacing; S10B | 3–5 days; mutable per-tab SQL and detached timeout threads |
| S10D SQL | Pool/slot/disposition schema; S10A | 1–2 days; occupied/uncertain file identity |
| S10E Bot | Export-only/status/reconcile/rebuild and rollover; S10B/C/D and S9B | 3–4 days; public ACL uncertainty and late old writes |
| S11 docs/release | Exact environment/operation plan and new evidence, after all preceding integration slices accepted | 1–2 days preparation; execution duration only after exact G4 targets/operations are approved |

Total proposed engineering range: 23–37 focused days plus separately authorized operational
evidence. S10C may be reviewed as two commits within its bounded PR (snapshot capture and
provider adapters); if its verified surface grows, stop to amend that exact manifest instead
of expanding into general reliability WS1. Additive schema may deploy inertly before Bot,
but no source serving/queue activation before all required compatibility gates are complete.

### Exact source/test paths by boundary

`Create` names below are deliberate proposed files, currently absent; `Modify` names are
current files verified by local inventory. Tests in this table are edits, not just tests to run.
Unlisted runtime, SQL or config files remain outside each proposed boundary. The S7 handoff
union accompanies the first separately authorized slice PR; later PRs prove those paths merged.

#### S8A

| Repository | Action | Exact path |
|---|---|---|
| SQL | Create | `migrations/20260912_001_kvk_season_complete_updates.sql` |
| SQL | Create | `sql_schema/KVK.SeasonSource.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceUpdate.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceCompleteSelection.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceExportIntent.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceExportIntentPublication.Table.sql` |
| SQL | Create | `validation/kvk_source/s8_season_complete_updates.sql` |
| SQL | Modify | `docs/SQL_DELIVERY_LOG.md` |

#### S8B

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

#### S8C

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `ui/views/kvk_source_import_view.py` |
| Bot | Modify | `upload_routes/kvk_source_route.py` |
| Bot | Modify | `upload_routes/kvk_all_route.py` |
| Bot | Modify | `kvk/services/new_source_admin_service.py` |
| Bot | Modify | `kvk/dal/new_source_admin_dal.py` |
| Bot | Modify | `proc_config_import.py` |
| Bot | Modify | `docs/reference/canonical_command_reference.md` |
| Bot | Modify | `tests/test_kvk_source_admin.py` |
| Bot | Modify | `tests/test_kvk_source_import_view.py` |
| Bot | Modify | `tests/test_kvk_source_upload_route.py` |
| Bot | Modify | `tests/test_kvk_all_upload_route.py` |
| Bot | Modify | `tests/test_kvk_source_config_hook.py` |

#### S9A

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/dal/source_routing_dal.py` |
| Bot | Create | `kvk/services/source_routing_service.py` |
| Bot | Create | `tests/test_kvk_public_routing.py` |
| Bot | Create | `tests/test_kvk_source_independent_consumers.py` |
| Bot | Modify | `kvk/models/source_integration.py` |
| Bot | Modify | `kvk/dal/new_source_reporting_dal.py` |
| Bot | Modify | `kvk/dal/kvk_reporting_dal.py` |
| Bot | Modify | `kvk/services/kvk_reporting_service.py` |
| Bot | Modify | `kvk/services/new_source_reporting_service.py` |
| Bot | Modify | `stats_alerts/allkingdoms.py` |
| Bot | Modify | `stats_alerts/embeds/kvk.py` |
| Bot | Modify | `stats_alerts/kvk_diagnostics.py` |
| Bot | Modify | `stats_alerts/kvk_diagnostic_sessions.py` |
| Bot | Modify | `tests/test_kvk_reporting_service.py` |
| Bot | Modify | `tests/test_kvk_source_reporting.py` |
| Bot | Modify | `tests/test_kvk_source_reporting_models.py` |
| Bot | Modify | `tests/test_kvk_embed.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostics.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostic_lifecycle.py` |
| Bot | Modify | `tests/test_stats_alerts_fighting_lifecycle.py` |

#### S9B

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `kvk/services/kvk_stats_card_service.py` |
| Bot | Modify | `kvk/dal/kvk_stats_card_dal.py` |
| Bot | Modify | `kvk/models/kvk_stats_card.py` |
| Bot | Modify | `kvk/rendering/kvk_stats_card_renderer.py` |
| Bot | Modify | `commands/kvk_stats_card_posting.py` |
| Bot | Modify | `ui/views/kvk_stats_card_views.py` |
| Bot | Modify | `kvk/services/kvk_admin_service.py` |
| Bot | Modify | `kvk/dal/kvk_admin_dal.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `tests/test_kvk_source_card_context.py` |
| Bot | Modify | `tests/test_kvk_stats_card_payload.py` |
| Bot | Modify | `tests/test_kvk_stats_card_dal.py` |
| Bot | Modify | `tests/test_kvk_stats_card_posting.py` |
| Bot | Modify | `tests/test_kvk_stats_card_views.py` |
| Bot | Modify | `tests/test_kvk_admin_service.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostic_command.py` |
| Bot | Modify | `kvk/services/kvk_targets_card_service.py` |
| Bot | Modify | `kvk/models/kvk_targets_card.py` |
| Bot | Modify | `kvk/rendering/kvk_targets_card_renderer.py` |
| Bot | Modify | `tests/test_kvk_targets_card_service.py` |
| Bot | Modify | `tests/test_kvk_targets_card_renderer.py` |
| Bot | Modify | `tests/test_kvk_targets_card_posting.py` |

#### S10A

| Repository | Action | Exact path |
|---|---|---|
| SQL | Create | `migrations/20260912_002_shared_export_coordination.sql` |
| SQL | Create | `sql_schema/dbo.ExportJob.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportJobResource.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportResource.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportRequestBudget.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportAttempt.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportAttemptPart.Table.sql` |
| SQL | Create | `validation/kvk_source/s10_export_coordination.sql` |
| SQL | Modify | `docs/SQL_DELIVERY_LOG.md` |

#### S10B

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `services/export_coordination_service.py` |
| Bot | Create | `services/export_request_budget.py` |
| Bot | Create | `services/export_coordination_dal.py` |
| Bot | Create | `services/export_snapshot_store.py` |
| Bot | Create | `tests/test_kvk_export_coordination.py` |
| Bot | Create | `tests/test_kvk_export_sql_integration.py` |
| Bot | Modify | `kvk/services/new_source_recovery_service.py` |
| Bot | Modify | `kvk/services/new_source_export_service.py` |
| Bot | Modify | `kvk/services/new_source_delivery_service.py` |
| Bot | Modify | `kvk/dal/new_source_delivery_dal.py` |
| Bot | Modify | `kvk/dal/source_update_dal.py` |
| Bot | Modify | `bot_instance.py` |
| Bot | Modify | `bot_config.py` |
| Bot | Modify | `docs/reference/ENV_REFERENCE.md` |
| Bot | Modify | `docs/reference/runbook_startup.md` |
| Bot | Modify | `docs/reference/runbook_shutdown.md` |
| Bot | Modify | `tests/test_kvk_source_exports.py` |
| Bot | Modify | `tests/test_kvk_source_delivery.py` |
| Bot | Modify | `tests/test_kvk_source_recovery.py` |

#### S10C

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `services/legacy_export_snapshot_service.py` |
| Bot | Create | `services/legacy_export_snapshot_dal.py` |
| Bot | Create | `services/export_provider_adapter.py` |
| Bot | Create | `tests/test_legacy_export_snapshot.py` |
| Bot | Create | `tests/test_export_provider_adapter.py` |
| Bot | Modify | `gsheet_module.py` |
| Bot | Modify | `processing_pipeline.py` |
| Bot | Modify | `stats_module.py` |
| Bot | Modify | `kvk_all_importer.py` |
| Bot | Modify | `upload_routes/kvk_all_route.py` |
| Bot | Modify | `commands/admin_cmds.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `kvk/services/kvk_admin_service.py` |
| Bot | Modify | `kvk/dal/kvk_admin_dal.py` |
| Bot | Modify | `kvk/dal/kvk_all_import_dal.py` |
| Bot | Modify | `proc_config_import.py` |
| Bot | Modify | `services/export_coordination_service.py` |
| Bot | Modify | `tests/test_gsheet_module.py` |
| Bot | Modify | `tests/test_gsheet_helpers.py` |
| Bot | Modify | `tests/test_gsheet_sorting.py` |
| Bot | Modify | `tests/test_kvk_all_upload_route.py` |
| Bot | Modify | `tests/test_kvk_all_import_dal.py` |
| Bot | Modify | `tests/test_processing_pipeline.py` |
| Bot | Modify | `tests/test_processing_pipeline_run_step_and_normalization.py` |
| Bot | Modify | `tests/test_proc_config_import.py` |
| Bot | Modify | `tests/test_kvk_export_coordination.py` |

#### S10D

**Delivered reconciliation — 2026-09-15:** SQL #87 merged at
`80353a6280e523f30c27e724f71e7b47dadadd16`. The original proposal below is retained
as S7 history: the resolved migration is `migrations/20260915_001_kvk_output_pool_rollover.sql`.
The approved implementation also included mandatory `migrations/README.md` and four justified
additions: `sql_schema/KVK.SourceOutputFile.Table.sql`, `sql_schema/dbo.ExportAttempt.Table.sql`,
`sql_schema/dbo.ExportAttemptPart.Table.sql` and `deploy/Test-OutputPoolRolloverContracts.ps1`.
See the [exact eleven delivered paths and evidence limits](s10d_closeout_and_s10e_handoff.md).
No SQL installation or runtime/provider proof is inferred; do not rerun predecessors.


Current handoff: [S10C closeout and exact pending documentation manifests](s10c_closeout_and_s10d_handoff.md).
Historical scope requirement: the six SQL rows below were the approved S7 proposal. S10D scope had to resolve the migration's
actual creation date/free daily ordinal before authoring and include the newly pending SQL
`migrations/README.md` alongside `docs/SQL_DELIVERY_LOG.md`. Bot closeout documents, S10D pack/starter
and both S10C archive move sides remain grouped for the next authorized Bot implementation PR,
currently S10E; S10D must carry that exact manifest forward. No standalone docs PR or repository mixing.

| Repository | Action | Exact path |
|---|---|---|
| SQL | Create | `migrations/20260912_003_kvk_output_pool_rollover.sql` |
| SQL | Create | `sql_schema/KVK.SourceOutputPool.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceOutputSlot.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceOutputDisposition.Table.sql` |
| SQL | Create | `validation/kvk_source/s10_output_pool_rollover.sql` |
| SQL | Modify | `docs/SQL_DELIVERY_LOG.md` |

#### S10E

**Current handoff:** initial review/scope only. Reconcile these twenty starting paths with current
Bot and authoritative merged SQL before implementation approval. The eventual Bot implementation
PR must also include the full [pending documentation manifest](s10d_closeout_and_s10e_handoff.md),
including both S10C archive move sides, S10D archive destinations and S10E pack/starter.
Verify filename AND previous_filename or explicit content/base-absence proof; counts are insufficient.
Any genuine SQL delta requires its own approved target and both pending SQL delivery documents.


| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/dal/source_output_pool_dal.py` |
| Bot | Create | `kvk/services/source_output_pool_service.py` |
| Bot | Create | `kvk/services/source_export_operator_service.py` |
| Bot | Create | `ui/views/kvk_source_export_view.py` |
| Bot | Create | `tests/test_kvk_export_operator.py` |
| Bot | Create | `tests/test_kvk_output_rollover.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `kvk/services/new_source_admin_service.py` |
| Bot | Modify | `kvk/services/new_source_export_service.py` |
| Bot | Modify | `kvk/services/new_source_delivery_service.py` |
| Bot | Modify | `kvk/dal/new_source_delivery_dal.py` |
| Bot | Modify | `services/export_coordination_service.py` |
| Bot | Modify | `services/export_coordination_dal.py` |
| Bot | Modify | `docs/reference/canonical_command_reference.md` |
| Bot | Modify | `docs/reference/ENV_REFERENCE.md` |
| Bot | Modify | `docs/reference/runbook_diagnostics.md` |
| Bot | Modify | `tests/test_kvk_source_admin.py` |
| Bot | Modify | `tests/test_kvk_source_delivery.py` |
| Bot | Modify | `tests/test_kvk_export_sql_integration.py` |
| Bot | Modify | `tests/test_kvk_export_coordination.py` |

#### S11

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` |
| Bot | Modify | `docs/reference/local_sql_development.md` |
| Bot | Modify | `README-DEV.md` |
| Bot | Modify | `docs/reference/README.md` |


## 3. New files

Only these two repository files are created by S7:

- `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md`
- `docs/reference/kvk_source_migration/integration_implementation_manifests.md`

All runtime/test/SQL Create paths above are planning only. Local scratch backup/check scripts
are outside Git at `C:/Users/cwatt/AppData/Local/Temp/k98-s7-docs-9ib_g9cd`.

## 4. Modified files

S7 updates these six existing handoff documents, in addition to its two Create outputs:

- `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md`
- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/post_s6_handoff_log.md`
- `docs/reference/kvk_source_migration/post_s6_integration_requirements.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md`

Existing handoff edits remain; measured S6 evidence,
release files and both archived S6 bodies are preserved byte-for-byte from S7 entry.
Historical pending/next-slice statements retain their dates; latest S7 status controls.
Runtime helpers, SQL, test files, configuration and source workbooks are unchanged.

## 5. SQL changes — proposed only

No SQL changes executed. Read source definitions from authoritative SQL repository; no live
rows, SQL Agent jobs, deployed migration state, permissions or provider identity checked.
No new UDTs or numerical calculation stored procedures. Use the existing versioned
observation/config/result schemas; never widen legacy facts to store new-source results.

New definitions below use UUID=uniqueidentifier, hash=binary(32), UTC=datetime2(0) except
budget scheduling=datetime2(3), positive bigint counters, positive int KVK_NO, enums with
explicit BIN2 comparison and DATALENGTH checks, actors nvarchar(128), reasons nvarchar(1024).
All FK scope keys carry SourceKey/KVK_NO/PeriodID where applicable. No cascading deletes.
JSON has ISJSON and explicit byte bounds, never private data in public diagnostic payloads.

Interface ownership is explicit: `season_source_dal` creates/reads a choice and lifecycle CAS;
`source_update_dal` associates accepted revisions using expected update version, seals them,
and commits complete selection plus intent in one transaction. `source_update_service`
validates pairing/counterpart authority and invokes the accepted calculation service.
`source_routing_dal` returns the complete read token; `source_routing_service` dispatches
legacy/V2/unavailable without consulting upload order. `export_coordination_dal` owns job,
resource, budget and attempt CAS; the service owns coalescing, fairness and recovery policy.
`legacy_export_snapshot_dal` reads result sets under producer admission; its service/spool
store verifies immutable bytes and provenance before recording the job. Provider adapters
require a live job/epoch token at every mutation boundary. Pool DAL owns slot/disposition CAS;
pool service owns lifecycle and privacy/readback policy. No command invokes SQL directly.

S10B config addition is `EXPORT_COORDINATION_ENABLED`, default false; it enables the common
coordinator only after all adapters are deployed. A registered durable snapshot root and
storage-owner identity are passed through `EXPORT_SNAPSHOT_ROOT` and
`EXPORT_STORAGE_OWNER`. Use the existing configured SQL connection factory for the single
coordinator database; no parallel default SQL server or new embedded credentials. Extend
existing source export registrations to validated account/destination/pool identities; legacy
title discovery resolves to registered file IDs. Missing schema, unsupported worker protocol,
unregistered destination or missing durable storage blocks the affected job. No new dependencies
or edits to actual `.env`/`config/sheet_config.json` are planned. Environment provisioning is S11.

| Proposed object | Exact required key, columns and constraints |
|---|---|
| KVK.SeasonSource | PK KVK_NO; UQ(KVK_NO,SourceKey,ChoiceID); SourceKey varchar(32) allowlists legacy_full_data/snapshot_report_v1; ChoiceID; ChosenBy/ChosenUTC/Reason/ProvenanceJson <=65536 bytes; SeasonState planned/open/closing/closed; SeasonVersion; optional compatibility provenance. DAL exposes create/read/lifecycle CAS, no source update/delete. Migration rejects ambiguous historical scopes |
| KVK.SourceUpdate | PK UpdateID; UQ(source/KVK/period/UpdateID); ChoiceID FK; ConfigVersionID/RosterID; start/end revision and logical scan IDs; AggregateReportID/AggregateRevisionID; CoverageStartUTC/CoverageEndUTC/AsOfUTC; UpdateKind fight/overall/no_fight; UpdateState waiting_player/waiting_aggregate/ready/selected/superseded/rejected; BaseUpdateID; CounterpartRevisionID/ConfirmedBy/ConfirmedUTC/ConfirmationJson <=65536; RequestID FK SourceConfigRequest; ContentHash, Version. Nullable stream fields only while waiting; sealed tuple immutable; same-source scoped FKs; no-fight explicitly forbids aggregate |
| KVK.SourceCompleteSelection | PK(source/KVK/period); UpdateID scoped FK; PublicationID scoped FK; PublicSelectionVersion; SelectedUTC. Unique update/publication association checked against candidate manifest in commit; no ordinary unpaired pointer |
| KVK.SourceExportIntent | PK IntentID; source/KVK/ChoiceID; CommitSequence bigint unique per season; VectorHash; ExportSchemaVersion; IntentState pending/waiting_destination/materialized/coalesced/confirmed/blocked; CreatedUTC; SupersededByIntentID nullable same-season FK. UQ(source/KVK/VectorHash/ExportSchemaVersion); never delete accepted intent history |
| KVK.SourceExportIntentPublication | PK(IntentID,PeriodID); source/KVK/UpdateID/PublicationID/PublicSelectionVersion/ConfigVersionID; scoped immutable FKs; selected vector row count/hash verified before commit; unchanged periods copied into each vector |
| dbo.ExportJob | PK JobID; ConsumerKind new_source/all_kvk/scan_data; optional IntentID FK; AccountKey varchar(128), DestinationSetHash, InputHash/SpoolKey/SpoolBytes/StorageOwner, KVK_NO nullable, PoolEpoch nullable, RepairID nullable; EnqueueSequence; State waiting/ready/running/confirmed/failed/uncertain/coalesced/cancelled; OwnerID/Fence; CreatedUTC/UpdatedUTC; SupersededByJobID; Actor/Reason/ProvenanceJson. UQ replay key includes consumer/input/destination/epoch/repair; no replay collision between distinct damage repairs |
| dbo.ExportJobResource | PK(JobID,ResourceKey); ResourceKey varchar(256) FK; resource set frozen before running; sorted deterministic acquisition |
| dbo.ExportResource | PK ResourceKey varchar(256); ResourceKind account/destination/sql_snapshot; ActiveJobID nullable FK, OwnerID/Fence, BlockedReason, Version; owner and job nullability paired; CAS updates; job state alone cannot release uncertain resource |
| dbo.ExportRequestBudget | PK(AccountKey,BudgetKind); NextAllowedUTC datetime2(3); CooldownUntilUTC; Version; interval/policy version; request reservation uses server UTC, waits outside transaction; no SQL transaction during provider request |
| dbo.ExportAttempt | PK AttemptID; JobID FK, AttemptNo UQ per job, OwnerID/Fence, Epoch, Phase private_started/verified/publication_pending/published/failed/uncertain/retired; RemoteSequence; timestamps; ManifestHash; legacy SourceDelivery key reference optional; bounded receipt metadata; append-only attempts, phase CAS |
| dbo.ExportAttemptPart | PK(AttemptID,PartNo); FileID nvarchar(128), role, manifest hash, grid/row/cell counts, verified/ACL state and UTC, quarantine disposition; unique assigned file per attempt; preflight maximum parts/count/receipt fields, never truncate evidence |
| KVK.SourceOutputPool | PK PoolID; stable IndexFileID UQ; ActiveKVK/ChoiceID; Epoch; PoolState active/closing/closed/setup/blocked; OwnerID/Fence; Version; expected account/owner/audience metadata, lifecycle audit |
| KVK.SourceOutputSlot | PK FileID nvarchar(128); PoolID FK; State free/staging/active/quarantined/retired; Epoch; AttemptID nullable; PartNo; Version; unique assignment under pool lock; file cannot belong to another pool |
| KVK.SourceOutputDisposition | PK DispositionID; PoolID/FileID/AttemptID; OldEpoch/NewEpoch; Action retire/quarantine/clear/assign; actor/reason/UTC; evidence hash and bounded JSON; append-only record so old receipt is never rewritten to look absent |

Migration paths in the exact manifest reserve the 20260912 date for review. SQL convention
requires actual creation date; if authored on another day, revise the three exact migration
filenames during the separately approved slice scope before writing them. Never rename a
merged migration. Include normal metadata, backup/data-safety and forward-fix notes.

S8A classification backfill is DataChange: Yes and requires an exact row preview/allowlist,
conflict rejection and backup authorization later; do not auto-classify all observed new-source
seasons as activated. Existing partial SourceSelections stay private until an explicit reviewed
pair is sealed; S6 databases are not migration targets by default. No live execution now.

Order: S8A schema and constraints → S8B/C writers → S9 readers; S10A schema → S10B/C
coordinator/adapters → S10D pool schema → S10E rollover. S10A/D are additive; old receipts
are imported into references only when unambiguously mapped, preserving bytes. Unknown
claims remain blocked. Do not turn on new queue writers while any old writer bypasses admission.
Reversible application rollout uses disabled admission/serving; rollback keeps schema/history
and fences. Drop-table rollback after data exists is not safe. Old-bot downgrade requires
draining/blocking all affected writers first; it cannot reinterpret a new-source KVK as legacy.

## 6. Helpers reused

Reuse `PublicationService.build_candidate`, `calculate_period`, `resolve_window`, semantic
digest/artifact store and existing import replay logic; extend selection validation for a sealed
pair rather than choosing globally newest unpaired input. Reuse `load_report_v2`/`card_context`
and V2 rendering, but give them the ordinary resolver token and exact immutable selection.
Reuse export generation partitioning, RAW values, full readback, quarantine and reconciliation;
replace latest-selection publication checks only for a valid running job/epoch. Existing receipt
uncertainty is never downgraded to failure based on time.

Reuse `file_utils.run_blocking_in_thread` for offload/telemetry, not ownership; shared locks or
offload registries do not provide a durable export queue. Reuse established atomic file helpers
for spools, verifying digest before SQL intent; do not introduce filename-driven paths.
Use `core/interaction_safety.py`, existing decorators and operator diagnostic packing/redaction
in commands/views. Reuse target-cache versioning pattern and CSV literal protection without
moving independent cache/data ownership. No helper implementation changed in S7.

## 7. Refactor findings

Required integration work: extract new queue/snapshot/provider-admission policy into services
and DAL; keep gsheet_module/processing_pipeline/kvk_all_importer compatibility wrappers thin.
Current account pacer is process-local; current export publication gate spans provider work;
current scan exporter reads SQL per tab and timeout can outlive its caller. These are bounded
S10 dependencies, not deferred optimizations or a general reliability WS1 programme.
No new SQL/business policy in commands or views. No unrelated helper cleanup, SQL rewrite,
dead-code deletion or new dependency is proposed. No unrelated actionable debt is captured.

## 8. Test plan with actual outcomes

### Required new scenarios and exact owners

| Scenario | Boundary | Exact test files | Required assertion |
|---|---|---|---|
| S7-T01 | S8A/B/C | `tests/test_kvk_season_source.py`; `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_source_admin.py` | Concurrent same/different source, absent choice, restart and historical conflict migration |
| S7-T02 | S9A/B | `tests/test_kvk_public_routing.py`; `tests/test_kvk_source_card_context.py` | Ordinary calls without injection; legacy/new/unavailable/disabled/capability states |
| S7-T03 | S8B/C | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_upload_route.py` | Both upload orders; first side cannot select publicly/enqueue; exact complete UpdateID |
| S7-T04 | S8A/B | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_sql_integration.py` | Wrong source/KVK/period/coverage/roster/config/revision; SQL scoped FKs and stale CAS |
| S7-T05 | S8B/C | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_import_view.py`; `tests/test_kvk_source_import_dal.py` | Explicit retained counterpart/actor, semantic alias/correction replay; no extra aggregate ScanID |
| S7-T06 | S8B/S9A | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_public_routing.py`; `tests/test_kvk_source_recovery.py` | Failed second side preserves previous label; first pair waiting; desired 14 old 13 not current final |
| S7-T07 | S8B | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_window_resolver.py`; `tests/test_kvk_source_config_service.py` | B0, no-fight absent members, separate overall, config-only and 11/12/13/14 exact sequence |
| S7-T08 | S8A/B | `tests/test_kvk_source_sql_integration.py`; `tests/test_kvk_source_pairs.py` | Kill before/after complete-selection/intent commit and lost acknowledgment |
| S7-T09 | S10A/B | `tests/test_kvk_export_coordination.py`; `tests/test_kvk_export_sql_integration.py` | Immutable running A then latest C; B history retained; fairness ticket not reset |
| S7-T10 | S10A/B/C | `tests/test_kvk_export_coordination.py`; `tests/test_export_provider_adapter.py`; `tests/test_legacy_export_snapshot.py` | Three consumers/manual/automatic/two processes; alias IDs, shared budget/cooldown; no SQL transaction over API |
| S7-T11 | S10B/C | `tests/test_kvk_source_delivery.py`; `tests/test_kvk_export_coordination.py`; `tests/test_kvk_export_sql_integration.py` | Worker loss/late effects; timeout thread retains ownership; uncertain blocks advance |
| S7-T12 | S10E | `tests/test_kvk_export_operator.py`; `tests/test_kvk_source_admin.py` | Export-only no parser/calculator; duplicate zero-API no-op; wrong actor/guild/role rejected |
| S7-T13 | S10E | `tests/test_kvk_export_operator.py`; `tests/test_kvk_source_delivery.py` | Explicit damage confirmation/RepairID; same inputs; old receipt retained; uncertain rebuild denied |
| S7-T14 | S10D/E | `tests/test_kvk_output_rollover.py`; `tests/test_kvk_export_sql_integration.py` | Drain/epoch/late writer; private clear/readback uncertainty; retired links and history |
| S7-T15 | S10D/E | `tests/test_kvk_output_rollover.py`; `tests/test_kvk_source_delivery.py` | P=2/larger partitions/quarantine exhaustion; receipt limit; no mutation before capacity |
| S7-T16 | S9A/B/S10C | `tests/test_kvk_source_independent_consumers.py`; `tests/test_stats_alerts_fighting_lifecycle.py`; `tests/test_kvk_public_routing.py` | C01-C65/N01-N12 covered; daily claims/SCANORDER/targets/history unchanged; precision and views |

Original T01–T70 remain accepted at their original revisions. Rerun only affected regression
coverage in implementation, never call this a predecessor reapproval:

| Original contracts | Exact existing test files to run/update where the changed behavior requires it |
|---|---|
| T01–T20 parser/digest/metadata | `tests/test_kvk_new_source_schema.py`, `tests/test_kvk_new_source_parser.py`, `tests/test_kvk_new_source_metadata.py`, `tests/test_kvk_new_source_digest.py`; run as intake boundary regressions, parser semantics unchanged |
| T21–T34, T68–T70 endpoints/B0/no-fight | `tests/test_kvk_source_calculation.py`, `tests/test_kvk_source_window_resolver.py`, `tests/test_kvk_source_config_service.py`, `tests/test_kvk_source_config_hook.py`; pair gating must preserve 11−10, 12−10, 13−10, authorized 14−10 |
| T35–T45 authoritative reports/finality/correction | `tests/test_kvk_source_publication.py`, `tests/test_kvk_source_reporting.py`, `tests/test_kvk_source_pairs.py`; T36/T40 private component behavior retained, public partial exposure superseded by S7 |
| T46–T51 atomicity/CAS/config races | `tests/test_kvk_source_sql_integration.py`, `tests/test_kvk_source_pairs.py`, `tests/test_kvk_export_sql_integration.py`; real two-connection disposable tests required after exact target approval |
| T52–T55 caches/views/availability | `tests/test_kvk_public_routing.py`, `tests/test_kvk_source_reporting_models.py`, `tests/test_kvk_embed_diagnostic_lifecycle.py`, `tests/test_kvk_stats_card_views.py` |
| T56–T59 multipart, coalescing and uncertainty | `tests/test_kvk_source_exports.py`, `tests/test_kvk_source_delivery.py`, `tests/test_kvk_export_coordination.py`; T58 pending B coalesces but running A may finish; T59 existing Discord uncertainty/caps unchanged |
| T60–T64 mixed card/independent/security boundaries | `tests/test_kvk_source_card_context.py`, `tests/test_kvk_source_independent_consumers.py`, `tests/test_kvk_source_admin.py`, `tests/test_kvk_source_import_view.py`, `tests/test_stats_alerts_guard.py` |
| T65–T67 rollback/history basis | `tests/test_kvk_source_recovery.py`, `tests/test_kvk_public_routing.py`, `tests/test_kvk_source_reporting.py`; T66 fixed-source disable is unavailable, never switch to legacy |

Each Bot runtime boundary: exact-path selector, focused pytest on its manifest's test files,
architecture/deferred/routing validators, smoke imports, command-registration validator where
command/lifecycle wiring changes, lint/type checks per repository hooks. Full suite through
`python scripts/analyse_pytest_log_noise.py` before broad integration handoff; record actual
count/skips and unchanged operational logs. Preserve existing legacy SQL contract tests.
Registration stays within the existing `kvk_admin` group, <=25 children; validate actual counts,
no assumed historical 36/101 result for changed code. No top-level allowlist expansion.
S9B renderer changes require synthetic visual samples for both stats and target cards,
including missing/stale context and long Unicode names; existing target numbers must stay
identical. The text-only S7 plan creates no sample or runtime renderer test now.

SQL schema slices: static snapshot/migration shape tests, then independently approved disposable
installation twice (idempotence), historical/mixed-state migration rejection, same/different-source
concurrent onboarding, pair FKs, two builders/commit acknowledgment loss, one owner per resource,
deadlock ordering and normalized receipt capacity. Mocks cannot close transaction/restart gates.
S11 exercises only newly affected provider/ACL/queue/rollover cases at approved exact targets;
retains S6 benchmark without rerunning it automatically. Real SQL/provider/Discord execution
requires a later exact operation/target approval; no connection strings to defaults in tests.

### S7 actual local checks

Recorded after final edits in [handoff S7 validation](post_s6_handoff_log.md#s7-documentation-delivery-and-validation).
Runtime pytest/full-suite/log-noise, smoke imports and command registration are skipped because
the actual delta is Markdown-only and no runtime/test/config source changed. Proposed tests
above have not run. No staging or staged-secrets scan authorized; no blanket hook pass claim.

## 9. Security review decision and evidence

Use k98-security-review-routing: **Bot documented skip**, exact 25-path Markdown-only patch
against `a2f148fa9bd4fb367fd46d0500a768c14fee915b`; no executable permission/input/network/
SQL/config/persistence change. **SQL separate no-change skip**, HEAD
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Root SECURITY.md supplies policy context;
no scan started. The final manifest/status/whitespace/link/evidence checks support the skip.

Every future runtime/SQL slice above requires a separate **Changes** review, **Deep off**, at
that repository's exact verified base/head or immutable working patch. Future SHAs do not yet
exist: resolve and record them immediately before review, do not reuse S7 anchors as invented
future targets. Store scan ID, manifest/findings/coverage, all reviewed paths and dispositions;
re-review relevant changed scope after fixes. Bot/SQL histories are never one combined target.
S11 documentation-only evidence may use a precise skip if it remains non-executable. No
standard/deep audit, automatic new task, PR, merge or live action follows from this plan.

## 10. Deployment/rollback

Nothing deployed. Future releases need repository-reviewed migrations before dependent Bot,
verified schema/backup/audit state, all participating writers on coordinated versions, exact
account/destination IDs and capability manifest, then separate G4 operations and G5 acceptance.
SourceRouting.Enabled alone is not activation. Mirror #272 and production #579 are merged;
local deployment is operator-attested only, not production runtime or fresh post-merge smoke.

Rollback means disable new admission/serving, retain fixed choice, finish/reconcile pinned jobs,
advance fences for explicitly selected older complete publication and report stale/unavailable.
Do not mutate accepted facts, delete receipts, reclaim uncertain files, reimport or silently route
to another source. Spreadsheet retirement is explicit and audited; no historical archive is required.
Preserve all S6 databases/files/uncertain states with their exact evidence references.

## 11. Follow-ups and approval

Stop for Chris Watts's review of the contract and exact manifests. S8–S11 implementation and
each operational action need separate approval. Remaining finite work is the eleven boundaries
in section 2, deployment/external-consumer inventory, exact SQL/provider operation plans,
S6-OPS01/PERF01/CAP01 integration evidence and operator G5 acceptance. No repeated product
decisions. Technical recommendations: initial account serialization, durable legacy spool with
worker affinity where needed, and one-generation quarantine/reserve allowance.

Completed-documentation review uses k98-pr-review for the local delta, not promotion readiness.
No runtime readiness or PR merge verdict can substitute for contract review, future security
reviews, actual deployed parity or Files changed verification after a PR is separately authorized.


## S8C approved implementation amendment - 2026-09-13

The operator approved the revised scope and implementation plan in this task. This supersedes
S8C's initial-review-only selection; S7 decisions and completed S8B acceptance remain settled.
The original 13 paths remain mandatory. Approved additional paths support durable non-file
reviews, later within-season window assignment and reviewed post-use configuration corrections.
No S9/S10 work, public activation, SQL execution, provider writes, Discord operation, bot-machine
pull/restart/deployment, predecessor operation or Git publication is authorized.

### Exact Bot implementation union (39 paths)

| Action | Path |
|---|---|
| Modify | `commands/stats_cmds.py` |
| Modify | `ui/views/kvk_source_import_view.py` |
| Modify | `upload_routes/kvk_source_route.py` |
| Modify | `upload_routes/kvk_all_route.py` |
| Modify | `kvk/services/new_source_admin_service.py` |
| Modify | `kvk/dal/new_source_admin_dal.py` |
| Modify | `proc_config_import.py` |
| Modify | `docs/reference/canonical_command_reference.md` |
| Modify | `tests/test_kvk_source_admin.py` |
| Modify | `tests/test_kvk_source_import_view.py` |
| Modify | `tests/test_kvk_source_upload_route.py` |
| Modify | `tests/test_kvk_all_upload_route.py` |
| Modify | `tests/test_kvk_source_config_hook.py` |
| Modify | `kvk/models/source_integration.py` |
| Modify | `kvk/models/new_source_reporting.py` |
| Modify | `kvk/services/new_source_parser.py` |
| Modify | `kvk/services/new_source_config_service.py` |
| Modify | `kvk/dal/new_source_config_dal.py` |
| Modify | `kvk/services/new_source_recovery_service.py` |
| Modify | `kvk/dal/new_source_recovery_dal.py` |
| Modify | `kvk/services/source_update_service.py` |
| Modify | `kvk/dal/source_update_dal.py` |
| Modify | `kvk/services/new_source_window_resolver.py` |
| Modify | `kvk/services/new_source_calculation.py` |
| Modify | `kvk/services/new_source_publication_service.py` |
| Modify | `kvk/dal/new_source_publication_dal.py` |
| Modify | `tests/test_kvk_new_source_parser.py` |
| Modify | `tests/test_kvk_source_config_service.py` |
| Modify | `tests/test_kvk_source_recovery.py` |
| Modify | `tests/test_kvk_source_pairs.py` |
| Modify | `tests/test_kvk_source_window_resolver.py` |
| Modify | `tests/test_kvk_source_calculation.py` |
| Modify | `tests/test_kvk_source_publication.py` |
| Modify | `tests/test_kvk_source_reporting_models.py` |
| Modify | `tests/test_kvk_source_sql_integration.py` |
| Create | `kvk/services/source_admin_review_service.py` |
| Create | `kvk/dal/source_admin_review_dal.py` |
| Create | `tests/test_kvk_source_admin_review.py` |
| Modify | `tests/test_kvk_admin_service.py` |

Add all 30 physical documentation paths in the S8B closeout section 3, including both archive
origins and both destinations and the S8C pack/starter. The complete Bot union is **69 paths**.
An eventual separately authorized PR must verify actual `filename` AND `previous_filename`
against this union or supply individual merged-content proof; local counts alone are not proof.
No PR or remote Files changed verification is claimed by local implementation.

### Separate SQL union (6 paths)

| Action | Path |
|---|---|
| Create | `migrations/20260913_002_kvk_source_admin_reviews.sql` |
| Create | `sql_schema/KVK.SourceAdminReview.Table.sql` |
| Create | `validation/kvk_source/s8c_admin_reviews.sql` |
| Create | `deploy/Test-KvkSourceAdminReviewContracts.ps1` |
| Modify | `docs/SQL_DELIVERY_LOG.md` |
| Modify | `migrations/README.md` |

These are SQL-repository paths only and must never enter the Bot PR. Authoring is approved;
execution/deployment and SQL publication require separate authorization. ReviewSequence orders
configuration snapshots only; it is not a scan ID or SCANORDER allocator.

The existing command registration regression test is included because its required-receipt assertion must change for approved setup and attachment actions. This adds one directly affected test path to the approved feature scope.


## S9B delivered / S10A initial scope checkpoint — 2026-09-14

S9B is repository-delivered through merged mirror #277, production #584 and SQL #84; local pulls
are complete and the bot machine remains unchanged. The [current closeout](s9b_closeout_and_s10a_handoff.md)
controls fresh anchors, retained evidence and the exact pending documentation set.

S10A is next for initial scope only. Its nine S7-reserved SQL paths remain the starting boundary;
the approved `migrations/README.md` carry-forward makes ten initial SQL delivery paths including
both SQL documentation files. Reconcile the reserved migration's date/sequence explicitly before
authoring; no SQL file is created by this checkpoint. The S10A SQL PR must include both docs.
The Bot documentation set in the current closeout is mandatory for S10B's next Bot implementation
PR; S10A scope/closeout must preserve and hand it onward. No standalone docs PR, mixed-repository
PR or renewed grouping approval. Exact filename/previous_filename coverage remains mandatory.


## S10B delivered / S10C initial scope checkpoint — 2026-09-14

S10B is merged in mirror #278 and production #585 and locally pulled, including the final memory correction. No bot-machine pull occurred. The [S10B closeout](s10b_closeout_and_s10c_handoff.md) is the current evidence and exact pending documentation authority. The 26-path S7 S10C table above remains the initial implementation boundary; union it with every pending Bot document in the closeout, including both S10B archive source/destination pairs and the S10C pack/starter. Reconcile any necessary source/test additions at scope time. No standalone docs PR or repository mixing; require filename/previous_filename or exact merged/absent-at-base proof. Separate SQL delivery-log and migration-README updates accompany the next authorized SQL PR. This checkpoint does not authorize implementation, execution or publication.
