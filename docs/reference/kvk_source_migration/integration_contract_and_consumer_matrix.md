# S7 integration contract and consumer matrix
## S11 authority and caller composition authored — 2026-09-24

The operator approved the one-host/fresh-identity contract and continued local implementation.
Earlier unanswered-proposal and closed-factory statements below are historical. The actual
factories are now authored behind complete readiness; nothing has been activated or installed.

The Bot process owns command authorization, producer scopes and durable SQL coordination.
The separate Windows authority owns the fresh service-account key, supervised provider children,
private DPAPI evidence and fixed proof producers. Only identifiers and an expected snapshot hash
cross the proof IPC boundary. The authority obtains the current SQL snapshot itself, runs the
fixed producer and sealed replay, checks every session belongs to its host, rechecks the exact
snapshot and protected deployment records, stores/readbacks private evidence and submits one
exact proof CAS. The Bot cannot provide evidence JSON, termination flags or substitute a probe.
Unknown commit/response outcomes retain ownership and require reconciliation.

Publication proof supports confirmed, positively damaged and proven absent. Damage requires
byte-different cell content after the expected ACL, structure, manifest and pointer all match;
ACL/pointer/structure errors and provider exceptions remain unresolved. Absence requires a closed
complete history with no dispatched mutation for the exact job, no generation marker, and an
empty pointer or the exact previous confirmed pointer. SQL independently enforces the no-dispatch
condition. A missing marker or a Boolean alone never proves absence or no delayed effects.
Ordinary retirement, interrupted journal recovery, rollover drain and rollover completion retain
their distinct fixed producers, private replay and owner/fence/version checks.

One immutable ExportRuntime binds worker, operator, rollover, delivery and legacy capture services.
Actual daily pipeline, standalone procedure/cache refresh, configuration import, kvk_all import/
automatic export and manual export roots bind this bundle. Nested ownership persists across thread
offloads. Cancellation drains owned work; shutdown closes new admission and waits for existing
roots/entered children. Readiness runs outside the publication lock; shutdown during readiness
cannot publish a late bundle. The existing upload offload is already thread-only; commands pass
to bound functions. No additional upload route or command implementation was necessary.

Readiness checks fixed coordination SQL, the legacy signed-module permission closure and the
whole application metadata/permissions against independently reviewed pins. It also pins source,
export configuration, host/SIDs, deployment hash, registration and an existing private spool.
The actual producer cursor is checked before its first write, including kvk_all ingest and window
recompute; a separate guard connection is insufficient. Metadata reads do not commit, rollback or
close the producer's connection. Existing producer transaction ownership remains unchanged.

The G4 protected deployment boundary requires seven typed source records: host_acl, bot_identity,
identity_issuance, key_inventory, file_access, writer_drain and sql_installation. They bind the same
deployment/review UUIDs and exact protected bytes. The Bot account must be nonprivileged; every
Bot IPC request checks its actual token, including deny-only administrator groups and disabled
privileges. Windows can re-enable a privilege already in a token; see [Microsoft's token guidance](https://learn.microsoft.com/en-us/windows/win32/secbp/changing-privileges-in-a-token).
Authority child authentication remains a separate SID/PID check. Trusted Windows/SQL/provider
administrators remain trusted: reviewed records are not independent discovery of key custody or
proof that an administrator made no later change. G4 must review original source observations,
all issuance/impersonation capabilities, old processes/sessions, ACLs and credential holders.
No live Windows/provider observation has been made by this authoring work.

The old shared service account remains outside S11 execution. The fresh key stays only in the
Bot machine's authority-private custody; development remains source/offline. Player link access
may remain viewer-only. The owner administrator remains a trusted maintenance actor and must
freeze edits during accepted execution; viewer settings do not establish writer exclusion.


## S11 single-authority contract approved — 2026-09-24

The operator answered "Approved please continue" to the one-Bot-machine execution
authority and fresh S11 service-account proposal below. Its earlier unanswered wording
is retained as historical evidence; this approval is satisfied. Local implementation of
the protected deployment evidence contract, trusted proof issuer, runtime composition,
actual shared callers and readiness checks may proceed under the existing exact manifest.

Provisioning the identity/key, editing sharing, live SQL/provider/Discord work, deployment,
activation, G4 operations and G5 acceptance remain separately operator-owned. A reviewed
structured deployment packet is a prerequisite, never an invented success flag. Closed
source implementation and offline validation must remain distinct from those live proofs.

## S11 remaining host and credential decision — 2026-09-24

The approved NULL guard correction and its separate SQL Changes review are complete. The
remaining local issuer/runtime authoring needs a concrete credential-custody boundary; the
operator has been asked to confirm the following recommendation. No reply has yet been
received. This does not revoke earlier local implementation authority or authorize G4 actions.


The current service-account key is present on both machines. The user reports one Bot instance
and no other imports or manual writers, but that inventory is not enforced credential exclusion.
The authored Windows authority supervises only its own children. Its private DPAPI evidence is
also local to that authority identity; SQL hashes cannot make another host's missing private
journal readable. A successful fixed probe proves the observed response, not closure of an
unregistered holder of the same key. The existing runtime/proof factories therefore remain closed.

Current sources: core/export_execution_host.py (PrivateEvidenceStore and protected ACL checks),
services/export_execution_authority.py (owned stream/child closure),
services/export_reconciliation_service.py (complete recorded catalogue and private replay),
scripts/run_export_authority.py (local authenticated pipe), and
services/export_runtime_composition.py (registration is explicitly not deployment proof).

### Recommended initial release contract

1. Use one execution authority, on the Bot machine, for all admitted legacy/configuration and
   new-source provider calls. The development machine remains a source/offline-test host.
   Keep the shared SQL coordinator and account budget. No cross-host replay, automatic failover,
   network RPC or transfer of an old authority's private evidence is added.
2. Provision a fresh S11 service-account identity for that authority at G4. Its credential is
   issued into protected custody on the Bot machine; the ordinary Bot and development machine
   cannot read it. This is a proposed identity/custody change, not a claim that it is provisioned.
   The current identity and retained files are untouched during authoring.
3. Admin-created legacy/configuration sheets are explicitly shared with the new identity when
   G4 authorizes the exact cutover. New S11 pools use the existing fresh-file enrollment path.
   The old identity must have no write capability over S11 files. Public viewer sharing remains
   the chosen audience. Do not infer editor exclusion from viewer visibility.
4. G4 must establish the closed writer boundary with an actual, reviewed evidence packet:
   exact host and Windows SIDs; authority/child/source hashes; protected credential and evidence
   paths and ACL observations; provider identity/key inventory and issuance/custody evidence;
   exact file owner/editor/audience observations; old process/SQL-producer drain evidence; exact
   SQL target, installed metadata and effective privileges. Name the trusted OS/SQL/provider
   administrators and permitted maintenance changes. Missing evidence or an unexplained writer
   keeps admission closed. A free-text assertion or a Boolean configuration flag is insufficient.
5. Proof issuance can then combine that established deployment boundary with authenticated
   origins, complete closed request catalogues, exact current snapshots, fixed fresh probes and
   private replay. It must refuse foreign-host evidence, unknown outcomes, missing origins,
   interrupted journals or stale snapshots. No token-expiry timer or repeated empty read becomes
   a no-delayed-effects proof. Existing S6 files/publications remain protected and ineligible
   for automatic adoption or reuse.

The fresh identity provides a clear boundary from the copied legacy key. Keeping the existing
identity is possible only after separately designing and proving an equally concrete exclusion
of all former keys/tokens/writers. The current inventory alone does not supply that proof.

This recommendation is an inference from the current code and custody facts. Google documents
that possession of a service-account private key permits authentication as that identity and
recommends preventing copies during deployment ([key management](https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)).
Drive grants edit capability through writer permissions, separately from reader visibility
([Drive roles](https://developers.google.com/workspace/drive/api/guides/ref-roles)). These sources
support the identity/access boundary; they do not certify a deployed writer inventory or the
outcome of an escaped request.


The current confirmation is the initial one-host/fresh-identity design and local authoring
only. No service account, key, permission, SQL object or host process is changed now. The
existing [implementation manifest](integration_implementation_manifests.md#s11-preparation-and-proposed-implementation-manifests--2026-09-24)
states: "If it needs a supervisor change, additional durable SQL state, a new configuration
surface or credential protocol, return an exact amended manifest before coding." The
fresh-identity/custody contract is that new decision. No samples or private keys are requested.
The exact affected source/test owners and remaining stage gates are recorded in the current
[manifest](integration_implementation_manifests.md#s11-remaining-authority-composition-scope--2026-09-24)
and [release matrix](release_readiness_and_rollback.md#s11-corrected-sql-review-and-remaining-authority-decision--2026-09-24).


## S11 SQL NULL guard correction proposal — 2026-09-24

The completed SQL Changes review found no reportable security vulnerability under the
inspected authority and protected-code boundaries. It did identify source defects that
must be corrected before release. These are implementation defects, not missing provider
proof, and security suppression does not accept them as correct.

1. dbo.usp_ExportProviderRequestEventAppend accepts an explicit NULL ExpectedVersion. Its
   inequality against the current non-NULL version then evaluates UNKNOWN, allowing an
   otherwise-valid event without an exact observed-version precondition. Add an explicit
   NULL rejection to the SQL API and synchronize both embedded migration copies. Keep
   authority/session, owner/fence, resource, state and append-only checks intact. The real
   authority supplies its own SQL-derived stream.version; IPC cannot supply this parameter.
2. The five API definition comparisons in 20260924_001 use OBJECT_DEFINITION inequality
   without rejecting an unavailable definition. An existing complete installation can
   therefore pass that check with an opaque body and otherwise matching module metadata.
   Reject NULL definitions before granting authority execution. Do not adopt, decrypt,
   overwrite or repair an unknown installed body automatically. Fresh-install literals
   currently match the exact snapshots. Producing malicious existing code requires a
   protected schema/deployment capability; runtime readiness independently rejects opaque
   definitions. That limits security reportability but does not repair the installer.
3. The narrow S11 SQL fixture also compares HAS_PERMS_BY_NAME and administrator-membership
   observations without consistently rejecting NULL. Make an unknown permission/token
   observation fail closed before any synthetic session operation. This is fixture
   correctness, not evidence that a real restricted token or installed schema was tested.

This proposal is limited to the existing S11 evidence API/installer/fixture and regression
authoring. No new SQL object, role, grant, certificate, credential, provider protocol or
business procedure is proposed. No command/view/DAL refactor, query optimisation or cache
change is needed. The existing evidence DAL remains the caller. Retained state, receipts,
claims and all source/endpoint/UpdateID, P/Q/R, 9,000,000-cell and 8/16 contracts stay intact.

See the [exact correction manifest](integration_implementation_manifests.md#s11-sql-null-guard-correction-manifest--2026-09-24)
and [approval, validation and rollback plan](release_readiness_and_rollback.md#s11-sql-review-correction-approval--2026-09-24).
The correction proposal has not been implemented or executed.



## S11 approved SQL NULL guard corrections — 2026-09-24

The operator approved the eleven-path correction plan and continued local gap closure.
The event API now explicitly rejects NULL expected/current versions before mutation. The
uninstalled 001 draft synchronizes the API body and comparison literal and rejects NULL
definitions for all five evidence APIs. Its static checker compares both embedded bodies
against each source snapshot. The narrow fixture rejects unknown permission/admin tokens.
No existing business procedure, role, grant or migration identity changed.

The gated event regression now includes NULL, zero, negative and stale prepare versions,
NULL/zero/stale terminal versions, exact unchanged stream/request/event observations on
rejection, and the existing positive prepare/not_sent/freeze/close sequence. These engine
cases are authored but remain disabled and unexecuted. Static/offline validation cannot
establish actual SQL NULL, permission, installation or provider behavior.

The prior proposal below remains historical evidence; its approval requirement is satisfied.
Trusted issuance, complete shared-caller composition, application readiness and final reviews
remain authorized local work. Live operations and G4/G5 acceptance remain separately gated.

## S11 legacy SQL permission implementation — 2026-09-24

The operator approved the proposal below with "approved please continue". Its earlier
approval-request wording is retained as historical evidence. The additional local SQL
source, Bot readiness and offline-test authoring is now implemented. No existing business
procedure, merged migration, configuration query or private credential was rewritten.

The source manifest pins 37 procedures and dbo.fn_NormalizeGovernorNameKey. UPDATE_ALL2,
sp_TARGETS_MASTER and SP_Stats_for_Upload get separate root signatures; 23 countersignatures
retain the appropriate capability along the reviewed child paths. The function, pure fixed
DML/read children, three KVK roots and two existing EXECUTE AS OWNER helpers receive no
unnecessary signature. This corrects the first lexical inventory's omission of INSERT EXEC
calls without treating its comment/string candidates as actual modules.

Import/target certificate users have the DDL and SELECT/INSERT capabilities required by
existing output-table replacement and numeric-season objects. Schema UPDATE/DELETE is not
granted. Stats has schema SELECT and ALTER on STATS_FOR_UPLOAD for its existing statistics
refresh. Only import has CHECKPOINT, the separate master certificate-user xp_cmdshell and
xp_fileexist EXECUTE grants, and certificate-login bulk/performance grants. The Bot receives
none of those certificate capabilities. ExportLegacyEntryReader contains only the seven
public entry EXECUTE grants; application membership is a later explicit G4 operation.

The additive SQL delivery requires independently provisioned public-only certificates,
exact source/body hashes and exported signature blobs. It does not generate a signing key,
enable xp_cmdshell, create its proxy credential or change Windows ACLs. Signature validity,
exact grant rows, certificate principal identities and exclusive signature placement must
match. Unknown existing names, signatures, partial states or drift refuse; exact reapplication
verifies the existing delivery. The inverse requires the original packet and unchanged
delivery with no remaining application membership; it retains certificates and all evidence.

The Bot source pin is a canonical hash of that exact SQL manifest, not an installation-derived
allowlist. A protected version-1 legacy_sql_contract carries the source manifest, exact server,
ROK_TRACKER database, application principal, public-key/thumbprint pins, signature hashes,
migration hash and metadata fingerprint. Its 13 bounded read-only batches use the producer's
own connection. Source definitions, certificate identities/grants, forbidden direct or inherited
DDL/impersonation/grant-option permissions and owned schemas/objects/principals must match.
SQL Server 2022 and dbo default-schema resolution are explicit supported prerequisites.

LegacySnapshotDAL with execution_evidence=True requires that contract at construction and
checks the same SQL session before entering the producer. Validation failure closes its cursor,
retains durable ownership and neither commits, rolls back nor executes the producer. Nested
ownership and the existing session app-lock remain intact. The older version-2 fixed coordination
contract remains a separate prerequisite. No production factory or caller is opened by this gate.

This is a module/permission prerequisite. Complete installed table/view/trigger dependencies,
dynamic output shapes, actual root/nested transactions, bulk/proxy behavior, independently proven
writer coverage and provider/host evidence remain separate. The new disabled SQL fixture covers
restricted-login denial and the original configuration helper's real denied-TRUNCATE/DELETE
fallback with explicit caller rollback under both XACT_ABORT settings. Its behavior is unproven
until the exact G4 fixture is approved and executed; failure does not justify broad Bot DDL.

## S11 legacy SQL privilege-isolation proposal — 2026-09-24

This is a newly identified scope decision, not permission to execute or install SQL. The approved
evidence-ledger implementation and fixed coordination checks continue to stand. Their restricted
Bot/authority profiles cannot be treated as a complete permission plan for existing legacy writers.
The source gap is an explicit contract for elevated legacy operations while keeping the Bot unable
to author trusted evidence. Installed grants, signatures, proxy identity and behavior are unobserved;
this is not a claim that production is currently broken or exploitable.

### Source evidence and affected existing behavior

The fourteen SELECTs in config/sheet_config.json resolve in the authoritative repository to thirteen
distinct table/view definitions. Some names are unqualified; two queries explicitly name ROK_TRACKER.
Future capture readiness must bind actual database/default-schema resolution, exact definitions and
column/result shapes rather than assuming that matching query text selects the intended object.
The all-KVK capture calls KVK.sp_KVK_Get_Exports and consumes its ten existing ordered result sets.

Seven existing procedure roots were followed through a static candidate inventory: dbo.UPDATE_ALL2,
dbo.SP_Stats_for_Upload, dbo.sp_TARGETS_MASTER, dbo.sp_Upsert_ProcConfig_From_Staging,
KVK.sp_KVK_AllPlayers_Ingest, KVK.sp_KVK_Recompute_Windows and KVK.sp_KVK_Get_Exports.
The retained artifact records exact paths, content hashes and call-site lines for 37 procedure
candidates. It is a lexical inventory, including conditional/dynamic-call review points, not a
complete runtime call graph or an instruction to sign all 37 modules.

| Existing source | Concrete additional permission boundary |
|---|---|
| dbo.UPDATE_ALL2 | EXECUTE AS CALLER; index/statistics maintenance, table truncation and calls that rebuild output tables; preserve its public-entry transaction refusal and original import ownership |
| dbo.sp_Rebuild_ExcelForDashboard | EXECUTE AS CALLER; dynamic DROP and SELECT INTO dbo.EXCEL_FOR_DASHBOARD, using existing integer season-derived tables |
| dbo.sp_Prep_TargetTable, dbo.sp_Prep_ExcelExportTable and related output helpers | Existing dynamic per-season object creation and later refresh/index/view work need an exact reviewed dependency/permission closure |
| dbo.CLAIM_KS4_IMPORT_FILE, dbo.ARCHIVE_IMPORT_STAGING_FILE, dbo.HASH_KS4_IMPORT_ARCHIVE_FILE | Existing master.dbo.xp_cmdshell/file-existence calls; actual execution/proxy identity and file ACLs are separate server/host evidence |
| dbo.IMPORT_STAGING_PROC_CORE | Existing dynamic BULK INSERT of the claimed file; preserve file hash, single-owner and archive contracts |
| proc_config_import.py via sheet_importer.py | Existing TRUNCATE-to-DELETE fallback and direct fixed-table writes; do not grant broad DDL merely to make the first branch succeed or assume fallback transaction behavior is proven |

SQL Server requires database CREATE TABLE and schema ALTER for SELECT INTO. Microsoft also describes
ownership-chain risks from schema ALTER with object-creation capabilities; table-level evidence
denials alone are not a complete application privilege design. See
[SELECT INTO permissions](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-into-clause-transact-sql?view=sql-server-ver17)
and [schema permission implications](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-schema-permissions-transact-sql?view=sql-server-ver17).
No certificate/module-signing contract was found in repository SQL, PowerShell or Markdown. That
source search does not establish whether an unrecorded installation has signatures or other grants.

### Recommended additional local scope

Author a separate, additive SQL module-permission delivery contract. Grant elevated capabilities to
certificate-mapped identities used only by exact reviewed modules; ordinary Bot connections retain
the required data operations and exact entry-point EXECUTE permissions without general schema/module
control. Do not solve this by granting db_owner, retaining a second unrestricted Bot credential or
placing the Bot in ExportExecutionAuthority. The authority/enrollment identities remain separate.

1. Resolve the complete privilege-requiring closure from the seven existing roots, including dynamic
   SQL, called modules, server operations and the existing configuration helper. Record exact module
   definition hashes, parameters, required capabilities and existing caller/transaction ownership.
   Unknown dynamic targets or parameter-to-command ambiguity block that root. Pure read/DML modules
   receive no unnecessary elevated signature. No automatic database-wide module enumeration/signing.
2. Author explicit root signatures and necessary child countersignatures, narrowly scoped certificate
   principals/grants and read-only verification. Signing must bind independently approved module
   bytes. A procedure edit invalidates its signature and readiness; never silently sign whatever is
   currently installed. No business procedure body, output contract or old migration is rewritten.
3. Specify the separate master/server side only for the existing file/bulk operations that require
   it. No sysadmin/CONTROL SERVER grant, automatic xp_cmdshell enablement, proxy credential creation,
   file ACL change or signing-key generation follows from local authoring. Those identities and exact
   operations need their own G4 packet. Unsupported execution contexts remain closed.
4. Extend Bot readiness to validate this source-derived module/permission contract, actual target
   resolution and relevant schema/module capabilities. The current version-2 fixed export observation
   stays a bounded prerequisite; it must not be promoted into a whole-application certificate. Reuse
   existing DAL and composition boundaries and guard checks before any producer starts.
5. Retain the configuration helper's current behavior during this scope. Validate its denied-TRUNCATE
   fallback and transaction outcome in the separately disabled SQL fixture. If preserving semantics
   requires a new helper/procedure body change, report that concrete exception before expanding edits.

Module signatures do not automatically survive a nested procedure call: explicit countersignatures
can preserve the matching signature along a reviewed chain. Changing a module removes its signature.
These constraints shape the proposed allowlist and readiness tests; signing is not itself proof that
the existing inputs/privileges are safe. See Microsoft's
[ADD SIGNATURE contract](https://learn.microsoft.com/en-us/sql/t-sql/statements/add-signature-transact-sql?view=sql-server-ver17).

### Validation, delivery and rollback

Offline validation will cover exact root/child allowlists, definition or signer drift, missing/extra
signatures/grants, changed default schema/database resolution, direct evidence mutation/DDL rejection,
and refusal before producer admission. Static SQL parsing and both repository Changes reviews, Deep
off, remain distinct from the disabled exact-target SQL permission/transaction fixtures. Actual
root/nested calls, proxy/bulk behavior and private-key handling require operator-approved disposable
resources and actual restore evidence under G4; no predecessor scenario is rerun automatically.

Before installation, rollback remains continued non-installation. Later reversal requires admission
closure, owned work drain/reconciliation and exact pre-change permission/signature evidence. Remove
only this delivery's signatures/grants under an approved reverse plan, retaining journals/claims,
origin evidence, historical receipts and both uncertain publications. Do not delete signing material
needed to restore existing signatures or weaken evidence denials to restore a legacy writer.

The [exact additional file proposal](integration_implementation_manifests.md#s11-legacy-sql-permission-scope-amendment--2026-09-24)
and [approval boundary](release_readiness_and_rollback.md#s11-additional-sql-permission-scope-decision--2026-09-24)
are ready for review. The request is for local source/static/offline authoring of this additional
SQL privilege-isolation layer. Git publication, SQL/provider/Discord operations, credential/signing
key provisioning, bot-machine actions, activation, G4 execution and G5 acceptance remain unapproved.

## S11 file enrollment approval — 2026-09-24

The operator approved the additional implementation proposal below with “approved please
proceed”. This authorizes its exact local source, SQL authoring and offline validation scope.
The proposal's earlier approval-request wording remains historical evidence. Live G4/G5
operations, credentials, provider/SQL execution, publication and deployment remain unapproved.

The origin entity uses append-only `created` and `eligible` records. Creation retains its exact
preparation, ordinal, request, response and closed child stream; eligibility appends the sealed
verification stream and private evidence without rewriting creation. Interrupted enrollment
retains ownership. Catalogue membership includes every stream of each origin's preparation,
including the account-only stream preceding the first returned file ID. A completed preparation
alone cannot authenticate origin eligibility; the authority-written eligible records are required.

## S11 initial file enrollment: additional implementation proposal

Status: reviewable proposal only. No additional code, SQL object, credential flow or live
operation described below is authorized or implemented by this document. Existing approved
local implementation authority and every G4/G5 restriction remain intact.

### Finding and decision

The current independent authority can establish exact S11 child closure and terminal outcomes
for its recorded requests. CatalogueVerifier checks every relevant registered stream and the
five fixed probes replay sealed response bytes. None establishes a file's history before that
recording boundary, or excludes an unregistered credential-bearing writer. RuntimeRegistration
now binds admitted account/files/configuration; that protected allowlist is not historical proof.

The current SQL stream requires a pre-existing job/preparation/output-operation owner and
immutable resources. ProviderRequest and the child currently refuse create/discovery. There is
no durable binding from an independently observed creation request to a newly returned file ID.
SourceOutputDisposition supports only retire/quarantine/clear/assign; it is not a file-origin ledger.
Fabricating a baseline, treating a current blank file as a virgin file, importing a caller Boolean,
or treating zero S11 rows as complete history would violate the approved proof contract.

Recommend adding a narrowly scoped enrollment path for **new dedicated output files** whose
creation and complete subsequent managed request history can be recorded from the start.
Existing files without independently verifiable origin/history stay ineligible for automatic
finality/reuse; all retained S6 data and both uncertain publications remain untouched. This does
not add capacity to an existing blocked pool or let another account bypass an unresolved claim.
Existing registrations remain unchanged until separately authorized exact G4 operations.

Google documents that service accounts cannot own files and have no storage quota; shared-drive
files instead have organizational ownership and no individual owner role. The existing transport
requires an exact human owner. Therefore this proposal uses a separate **human-authorized,
authority-held creation credential**, bounded to the application's newly created files, while
retaining the existing service-account Editor identity for normal execution. No shared-drive
contract change or domain-wide delegation is inferred. The concrete OAuth client, user identity,
consent, token provisioning and any actual creation require a separate exact G4 approval.

Primary sources checked 2026-09-24:
- [Google Drive ownership and service-account limits](https://developers.google.com/workspace/drive/api/guides/about-shareddrives)
- [Sheets create API and returned spreadsheet](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/create)
- [Service-account impersonation prerequisites](https://developers.google.com/identity/protocols/oauth2/service-account)

This is a proposed implementation direction, not proof that a future deployment has excluded all
external writers. The exact G4 inventory must still cover every host, identity, credential copy,
SQL producer, manual/scheduled caller and destination alias. The named owner and privileged OS/SQL
administrators remain inside the existing trusted computing base; owner automation is not exempt
from the writer inventory. A missing or unverifiable exclusion stops admission.

### Proposed fixed flow

1. An explicit authority-side enrollment command accepts a protected, exact approved plan: one
   account/project, human owner, service-account Editor, requested index/slot count, private initial
   audience, source/build hashes and SQL/storage identities. No title-based discovery or Bot IPC
   enrollment. All 8/16 and protected-file/alias bounds remain. No command runs on import/startup.
2. Use the approved preparation ownership model with a new, strictly typed `output_enrollment`
   request purpose and account-only preflight under exact owner/fence/version CAS. This is a
   separately created preparation, never an existing configuration-read claim. Only the protected
   authority-side command may create it; normal Bot configuration requests cannot request this
   capability. Existing unresolved account/request ownership blocks it. Each creation ordinal is
   unique. Do not invent a completed job, replace a preparation or adopt an old claim.
3. Supervise one owner-authorized child, record a fixed create request before dispatch, validate its
   exact synchronous response and newly returned ID, then close/seal the stream. An ambiguous
   creation remains blocked: no repeat, name search, duplicate creation, adoption or cleanup.
4. Associate each returned ID with its original successful request and closed stream in an
   authority-only origin record. Add that exact destination to provisioning ownership only through
   the account/sorted-resource/owner lock order and current-version CAS. Never mutate old stream
   scope or substitute returned IDs. New streams use the enlarged exact resource membership.
5. Record the bounded Editor grant and complete private workbook/ACL readback under the exact
   owner. Close the owner-capable child and all bootstrap streams before eligibility. No public
   grant or real data export occurs in enrollment. Unknown grants/readbacks retain the operation.
6. Seal a canonical origin/evidence digest. Register a pool only from the completed origin set via
   separately authorized G4 SQL operations; do not automatically alter active registrations. The
   trusted issuer requires the original protected origin proof plus every subsequent relevant
   stream, including bootstrap streams whose original account-only scope preceded file creation.
7. The fixed publication/retirement/recovery/rollover probes can then issue SQL ProofIDs only after
   complete origin/history, snapshot, deployment and current observation checks. Unsupported
   history and unknown outcomes remain reconciliation, potentially indefinitely. Status never
   starts a probe. No caller-authored evidence flags can cross the trust boundary.

### Exact proposed authoring manifest amendment

All paths below are proposed, not newly authored by this packet. Existing pending documents remain
grouped with the next genuine Bot implementation PR; SQL implementation and its two closeouts are
separate. No standalone documentation PR or Git publication is requested here.

New Bot paths:
- `services/export_enrollment_service.py`: fixed provisioning/origin and complete-history verifier.
- `scripts/enroll_export_output_pool.py`: explicit authority-side entry; closed by default.
- `tests/test_export_enrollment_service.py`: offline state/identity/ambiguity/coverage cases.

Additional behavior in already pending Bot paths:
- `services/export_execution_protocol.py`: bounded typed create request/response, no generic endpoint.
- `services/export_execution_authority.py`: exact enrollment preparation and returned-file association.
- `services/export_execution_dal.py`: typed provisioning/origin procedures and complete membership.
- `services/export_reconciliation_service.py`: origin-gated issuance, retaining fixed sealed probes.
- `services/export_runtime_composition.py`: separate protected bootstrap profile and completed-origin
  readiness; retain normal Bot/service-account identity and every shared-writer gate.
- `scripts/run_export_authority.py`, `scripts/run_export_provider_child.py`: isolated creation
  credential profile, exact identity/operation allowlist and no fallback to broader credentials.
- `tests/test_export_execution_protocol.py`, `tests/test_export_execution_authority.py`,
  `tests/test_export_execution_sql_integration.py`, `tests/test_export_runtime_composition.py`,
  `tests/test_export_authority_launcher.py`, `tests/test_export_reconciliation_service.py`.
- Existing integration contract/manifests, release evidence/readiness, ENV_REFERENCE and startup/
  shutdown/diagnostics runbooks receive additive contracts and exact non-executed G4 steps.

New SQL paths (separate repository):
- `sql_schema/dbo.ExportManagedFileOrigin.Table.sql`
- `sql_schema/dbo.usp_ExportOutputEnrollmentTransition.StoredProcedure.sql`

Existing pending SQL paths requiring amendment:
- `migrations/20260924_001_export_execution_evidence.sql` (unmerged/uninstalled only; never rewrite
  a merged migration; re-resolve date/ordinal if this is no longer the current unmerged migration).
- `sql_schema/dbo.ExportExecutionStream.Table.sql`
- `sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql`
- `sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql`
- `sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql`
- `validation/kvk_source/s11_export_execution_evidence.sql`
- `deploy/Test-ExportExecutionEvidenceContracts.ps1`
- `docs/SQL_DELIVERY_LOG.md`, `migrations/README.md`.

Physical SQL design precedes dependent Bot authoring: immutable preparation/plan identity; exact
account/owner/fence/version and monotonic phase; unique file ID and creation ordinal/request;
foreign keys to the existing preparation and authenticated session/stream/request; original credential-profile/registration
and response/closure digest references; bounded canonical evidence; no DELETE/update-origin API;
authority-only EXECUTE and evidence writes; reader-only ordinary Bot evidence access. Creation
streams join proof membership through authoritative origins even if their initial scope had no
file ID. SQL must independently repeat that membership at issue and consuming settlement.

### Validation, risks and rollback

| Layer | Local authoring/validation proposal | Separate live evidence required |
|---|---|---|
| Bot/static | Fixed method/body/response parsing, origin lineage, claim/resource/epoch binding, guarded imports, caller matrix, complete pytest and log hygiene | None claimed by offline passes |
| SQL/static | New schemas/procedures/migration sync, keys/role predicates, complete catalogue selection | Installation, effective permissions, rollback/locking/CAS races and actual restore |
| Transaction | Disabled tests for duplicate/unknown create, atomic origin registration, cross-account/file substitution, proof-vs-provisioning races, replay refusal | Exact approved disposable target and operator packet |
| Provider/OS | Fake successful, partial, wrong-ID, lost-response, grant-loss, closure-loss and restart cases | Owner consent/credential isolation, actual private creation/readback, exact child closure, all-writer exclusion |
| Deployment | Separate profiles; no startup/bootstrap side effects; unsupported pre-S11 history blocked | Approved identities/builds/paths, complete writer inventory and G4 operations; G5 operator acceptance |

Main risks are broader credential authority, accidental creation replay, incomplete bootstrap
membership and treating enrollment as old-history repair. Keep the creation capability outside
Bot IPC, limited to fixed reviewed operations on newly created files, with all bytes/evidence
retained. Every negative outcome preserves claims and does not create reusable capacity. Tests
must verify no direct credential fallback and that pre-S11/forged/cross-file origins never issue a
ProofID. Bot and SQL require separate exact Changes reviews with Deep off after settled authoring.

Rollback now is non-installation. After a separately authorized deployment, close admission,
drain/freeze and observe owned children, retain every origin/request/claim and uncertain remote
file, and forward-fix SQL. Never delete unknown creations, reset versions, reuse old files or
restore an old direct writer as an automatic rollback. No retained predecessor is a test fixture.

### Approval requested

Approve or reject the additional local implementation scope above: trusted fresh-file enrollment,
the separate owner-authorized creation profile, one additional SQL evidence entity/procedure,
and origin-gated proof issuance. This approval would authorize source/static/offline work only.
It would not authorize OAuth consent, credential access/provisioning, SQL/provider/Discord
execution, creation of any real file, Git publication, bot-machine changes, deployment or activation.

The current release plan requires an explicit scope amendment for additional behavior/paths.
The choice is material because the original five-entity request ledger alone cannot authenticate
pre-recording file history, and the existing service-account-only credential contract cannot own
new human-owned workbooks. Do not quietly broaden either trust boundary during composition.


## S11 proof-consumption continuation — 2026-09-24

Six S11 settlement paths now resolve trusted SQL ProofID in their existing locked snapshot
transactions. Private-journal verification is implemented as a prerequisite to proof issuance;
the complete issuer, launcher and caller composition remain unfinished and disabled. See the
[current continuation evidence](release_evidence_log.md#s11-continuation-trusted-proof-consumption--2026-09-24)
for exact files and source-only validation. Earlier checkpoint statements remain historical.


## S11 implementation status — 2026-09-24

The operator approved this mechanism for implementation. Current source authoring implements only the evidence/transport foundations and optional admission gates. Trusted proof production/consumption and complete caller composition remain real implementation gaps. No source/static check establishes installation, containment or provider behavior. See [checkpoint](release_evidence_log.md#s11-approved-implementation-checkpoint--2026-09-24).


## S11 proof-mechanism decision proposal — 2026-09-24

The operator agreed to the architecture direction and authorized this bounded mechanism-design
pass after the preparation summary. **Only documentation/design is authorized.** The recommendation
below makes the earlier unresolved proof interface concrete; it adds a genuine proposed Bot/SQL/
deployment scope that still needs G3 approval. Earlier statements that no new SQL need was
established describe the initial scope checkpoint, not the result of this deeper investigation.

### Decision and limits

Recommend an independent Windows export authority with supervised provider-execution children,
and a normalized SQL request/evidence ledger in the existing coordinator database. All participating
export/config/provisioning SDK traffic must cross this boundary. Keep existing domain planners,
queue fairness, claims, storage/provenance and delivery/retirement state machines. Do not place
the authority in Discord handlers or treat an in-process Boolean callback as trusted evidence.

This is a conservative recovery mechanism, not a guarantee that every interrupted operation can
be recovered. A possibly dispatched mutation without durable terminal success remains unknown.
No timer, repeated readback, fresh process or marker alone upgrades it to no-delayed-effects proof.
This can block a pool/account indefinitely. A different destination or provider-assisted resolution
would need its own reviewed operation; neither frees the original claims nor silently adds capacity.

Evidence for the need: ExportRequestBudget contains aggregate timing/version state, ExportAttempt
contains phase/manifest/receipt state, and ExportPreparation contains generation/spool state.
None records every outbound request or a trusted process incarnation. Both SDK paths can issue
requests after an ownership check; that check alone cannot revoke a request already in flight.
`run_bot.py` waits for its child but is not an independent durable export-request authority.
`process_utils.py` provides best-effort PID checks and conservative fallbacks, not proof of closure.

### Trust and process model

- Run a dedicated authority under a separate explicitly registered Windows identity per participating
  host. Use the existing pywin32 dependency. This is a new supervised runtime entry point, not a
  rewrite of the bot watchdog. Its exact service/task launcher, account, ACL and executable hash
  belong in G4; no service installation or credential move is authorized now.
- Local Bot callers use a versioned, authenticated named-pipe protocol with explicit DACL, bounded
  messages, peer identity checks and denied remote access. It accepts only registered typed actions,
  resource identities and validated claims, not arbitrary Python, SQL, URLs, credentials or shell
  commands. Hosts use their own local authority and the same SQL coordinator; no network RPC server
  or automatic cross-host authority failover is proposed.
- The authority owns credential access, request dispatch and evidence writes. Bot callers cannot
  create terminal evidence rows or read provider credentials. Provider children run approved fixed
  code, are created suspended, attached to a non-breakaway Windows Job Object before execution,
  and identified by retained process handles plus launch/session UUIDs, host and executable hash.
  Close-on-authority-loss termination is required; no credential-bearing orphan may survive.
- A provider-execution child is scoped to one owner/stream. A closing stream accepts no new work.
  The authority observes child termination using OS handles, verifies the supervised process set,
  and commits closure. It never maps an inaccessible/reused PID, missing lock file, watchdog log or
  RPC disconnect to `writer_terminated`. The Bot process itself need not exit, but the exact old
  provider writer must terminate and its capability must be permanently revoked.
- The trusted computing base includes authority/child code, OS and SQL administrators, protected
  configuration and the provider. This does not defend against their compromise. Deployment must
  exclude old credential copies and all unregistered account/file writers; direct SDK fallback
  remains forbidden in admitted mode. Merely changing an environment flag does not prove exclusion.
- Preparation SQL writers still use existing session admission and nested owner tokens. Before
  provider/rollover release, verify their exact resources drained/reconciled as well; a provider-child
  exit cannot prove a separate SQL producer stopped. No reinterpretation of UPDATE_ALL2 ownership.

Windows supports process grouping/termination through [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and persistent [process handles](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers).
These primitives motivate the proposed implementation; they do not prove any deployed process has
been contained. The named pipe requires an explicit security descriptor rather than permissive
defaults; see [Microsoft's access-rights guidance](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights).

### Durable request protocol

Use append-only request identities/events and a CAS-controlled session/stream lifecycle. Never
hold a SQL transaction while waiting, doing IPC, joining a child or calling Google. One request
dispatch is outstanding per owned account initially; existing fair job tickets remain authoritative.

1. Resolve exact job/preparation/output-operation or nested recovery owner, current CAS versions,
   registration, file set, purpose and account. Persist immutable RequestID/sequence, request kind,
   method, resolved resource scope, canonical payload hash and encrypted/private payload reference.
   File discovery/create binds its preparation scope; returned file IDs are durably registered before
   any content mutation. Unknown create outcome blocks admission, never rediscovers by title.
2. Reserve/refresh the existing server-UTC budget. Recheck ownership after waiting. Under the
   authority's stream admission lock, persist `dispatch_intent` before allowing the child to send.
   A close request uses the same boundary so it cannot omit an escaping request. SQL commit loss
   before send prohibits sending until exact RequestID readback resolves it. No automatic mutation
   retry at SDK, HTTP, child, IPC or queue layers.
3. Child reports a completed response to its parent; parent records a bounded response digest,
   method-specific validated outcome and timestamps. `succeeded` requires a supported synchronous
   success response; arbitrary HTTP 2xx, partial bodies or asynchronous acceptance are not enough.
   Method allowlists must include exact success-body validators and tests before implementation
   handoff. Unsupported methods remain closed. Raw tokens/content never enter ordinary logs.
4. Durably checkpoint budget completion separately. If response evidence exists but budget/job
   acknowledgment is lost, reconcile the SQL checkpoint without repeating the provider mutation.
   A success result held only in child/parent memory is not durable evidence after their loss.
5. Freeze the stream, drain completed work, terminate/observe the exact provider child and commit
   stream closure with its final request sequence and event digest. Proof generation rejects missing,
   contradictory, duplicated or mutable request/event membership. A `dispatch_intent` with no
   conclusive terminal event is unknown even if the child died before it probably sent anything.
6. On authority restart, open a new SessionID. Never relabel an old session or replay its uncertain
   requests. If containment/closure cannot be re-established from trusted OS and durable records,
   old session closure remains unknown; no lease-based takeover. Cleanly sealed old sessions can
   be read without replay, subject to fresh snapshot and provider verification.

`not_sent` is permitted only while the trusted authority can prove dispatch was never authorized
and atomically closes that request/stream against future dispatch. For the first version, every
possibly dispatched mutation error (including timeout, 429/503 and ambiguous transport failures)
is unknown unless a separately reviewed method-specific terminal classifier proves otherwise.
Existing exception classes such as RemoteRequestRejected are not terminal evidence by themselves.
GET retries remain bounded/paced, with a distinct record per attempt, never disguised mutations.

Google documents atomic Sheets updates and a 180-second processing timeout in its
[usage limits](https://developers.google.com/workspace/sheets/api/limits). The design does not infer
a cancellation/finality certificate from that timeout: the cited page does not supply a request
outcome query for our lost-response case. Drive also disallows concurrent permission modifications
on the same file across clients; all such operations need serialization and external-writer
exclusion. See [permissions.create](https://developers.google.com/workspace/drive/api/reference/rest/v3/permissions/create).

### Decision table for settlement and reuse

| Durable evidence after exact writer closure | Permitted outcome |
|---|---|
| Every relevant mutation has validated terminal success; fresh exact content/ACL/pointer matches | Candidate confirmed proof; commit only against current snapshot/CAS |
| No mutation was dispatched; all requests are proven not_sent; fresh readback agrees | Candidate absence proof, preserving original receipts/history; any retry still uses existing explicit safe-retry authority |
| Mutation succeeded but response-event persistence failed; output currently looks correct | Unknown; readback cannot close an unrecorded escaped request |
| dispatch_intent exists but no terminal response, timeout, process loss or ambiguous error | Unknown; retain claims and occupied capacity; no automatic retry, clear, epoch advance or reuse |
| Confirmed publication later differs, and all former requests/owners are conclusively closed | Damage proof may support explicit RepairID after current registration/capacity checks |
| Retirement clear succeeded and terminal record exists, but slot CAS acknowledgment was lost | Journal recovery may read-before-clear and finish exact nested CAS; do not replay confirmed clear |
| Retirement clear response itself is unknown, including a prior nested recovery writer | No no-delayed-retirement-effects proof; recovery remains blocked even if file currently appears empty |
| Rollover interrupted after only some files were processed | No generic completion proof; preserve partial journal and claims. This proposal does not invent a partial-rollover retry workflow |

### Read-only probes, proof storage and consuming CAS

Probe authority is a separate read-only stream referencing the retained owner, exact resource set
and immutable snapshot. It does not claim a new export or free blocked resources. The SQL stream
gate serializes account access with jobs, preparations, output operations and other probes; all
admission paths must observe it. Existing ownership remains intact. Under uncertainty only a
registered observational probe can run, after local writers are stopped; GETs cannot certify that
an unresolved remote mutation will never complete. Pace them through the same RequestBudget.
Forbid mutations, discovery, creation and permission changes in this stream.

Persist an immutable proof record containing ProofID/type, authenticated authority SessionID,
snapshot hash, source claim identities/versions, complete closed-stream/request high-watermarks,
registration/epoch, outcome and hashes/references for fresh observations. SQL stores normalized
membership and bounded metadata; private evidence files hold larger sanitized response material
with hashes, ACLs, durable flush and backup. A hash detects byte mismatch; it does not authenticate
an untrusted producer. SQL credentials/roles and authority identity supply that trust. Evidence
cannot share a disposable temp root or an ordinary caller-writable spool path. Missing/corrupt
evidence fails closed; no garbage collection or retention horizon is introduced here.

Settlement takes ProofID, loads the authoritative record in its existing short transaction, checks
the full current snapshot and source versions, and records the exact proof association in the
append-only audit. It must not trust a caller-built dictionary with true flags. Replay of the same
proof/outcome is idempotent; changed snapshot or outcome requires a new proof. Old proof is never
relabelled after a version change. Status reads do not issue provider probes or settle anything.

Ordinary retirement verifies the old attempt's writer and outstanding requests are closed while
the current owning job still holds its claim. Its own clear operations use a separately identified
child/stream. Interrupted retirement covers every previous nested writer, uses the existing hashed
journal and exact versioned recovery owner, then revokes/terminates that recovery stream and performs
a fresh publication probe. Successful clear does not rewrite historical receipts. Complete P/Q/R,
9,000,000-cell parts, 8/16 bounds, protected finals and both retained S6 uncertainties stay intact.

### Implementation consequence

New supervisor/IPC, per-request journaling, authenticated proof loading and independent evidence
permissions are necessary for this recommendation. They are not present in the earlier two-module
composition proposal. The [manifest amendment](integration_implementation_manifests.md#s11-proof-mechanism-manifest-amendment--2026-09-24)
lists the additional exact Bot/SQL paths and validation. No SQL/runtime file is created now.
The operational tradeoff requiring operator acceptance is indefinite blocking after genuinely
unprovable mutations; implementing a gateway does not make those outcomes knowable.

## S11 composition and trusted-proof design — 2026-09-24

**Approved work: documentation preparation/design only. Proposed runtime design below is not
implemented or authorized.** Current S7 source, endpoint, UpdateID, counterpart, B0/overall and
independent-consumer contracts remain binding; no new product decision is introduced.

### Actual ownership map and composition gaps

| Producer/caller | Existing path and ownership | Required composition boundary |
|---|---|---|
| Ready lifecycle | `bot_instance.py:_run_ready_runtime_services` calls `register_exports(task_monitor)`; `services/export_coordination_service.py` refuses a missing factory | Supply a verified composition only after gates; retain one supervised worker and disabled default |
| Grouped operator actions | `commands/stats_cmds.py` and `kvk/services/kvk_admin_service.py` call `configured_operator_service`, which raises | Return the same registered runtime's operator service; preserve fresh access checks and no new command |
| New-source publication/recovery | Complete selection and durable full-vector intent; recovery wakes export discovery | Compose immutable generation loader, `ExportCoordinator`, `SourceOutputPlanner` and `deliver_coordinated_export`; never deliver raw component selections |
| Legacy upload/recompute | `upload_routes/kvk_all_route.py` → `kvk_all_importer.py` → `kvk/dal/kvk_all_import_dal.py`; admin recompute uses `kvk/dal/kvk_admin_dal.py` | Bind `LegacyExportRuntime` at actual orchestration entry, across nested helpers and auto-export capture; accepted generation/provenance remains pinned |
| Daily scan processing | `processing_pipeline.py`, `stats_module.py` (`UPDATE_ALL2`), `player_stats_cache.py`, both `proc_config_import.py` branches | Bind one runtime per task; preserve nested owner, SQL session admission, complete captures and existing daily order/SCANORDER |
| Manual exports | `commands/admin_cmds.py` → `gsheet_module.py:run_all_exports`; legacy admin export and compatibility wrappers | Reuse verified ready capture; queue JobID is not a provider-completion receipt |
| Compatibility/provisioning | `run_single_export`, `transfer_and_sort`, `run_kvk_export_test`, `run_kvk_proc_exports`, `run_kvk_proc_exports_with_alerts`, `create_additional_kvk_spreadsheets` | Each deployed caller must be bound or explicitly excluded; account admission precedes discovery/create and IDs precede mutation |
| Rollover/retirement | `source_output_pool_service.py`, `source_output_pool_dal.py`, `source_export_operator_service.py` already implement durable transitions and explicit journal recovery | Supply termination verifier, reconciler, retirement verifier and `RetirementRecovery`; never substitute test dictionaries |
| External writers | SQL Agent, standalone/manual SQL, other hosts/services and all users of the account/project | Operator inventory required; compatible shared coordination or verified exclusion, with a named owner for each process |

Source searches found no production caller constructing `LegacyExportRuntime`/using `use_runtime`,
and no production implementation supplying the trusted rollover/retirement proof callbacks.
`configured_coordinator` and `configured_operator_service` are deliberately closed. Existing SQL
and provider adapter authoring is not installation evidence. No claim about absent external
processes follows from source search.

### Proposed runtime composition contract

Use a service-owned composition root; commands/views keep validation, fresh permissions and
rendering, DALs keep SQL and short transactions. Proposed file placement is in the
[exact manifest](integration_implementation_manifests.md#s11-preparation-and-proposed-implementation-manifests--2026-09-24).

1. Closed/default construction must not open SQL, credentials, SDK clients or create storage.
   Read a versioned, immutable approved deployment manifest only through an explicit gate.
   A flag or user-supplied command payload is not that manifest's authority.
2. The admitted manifest binds the one coordinator database, Bot/SQL protocol revisions, account/
   project identity, all writer identities, exact destination/index/slot IDs and registration hash,
   season/choice/epoch, audience/owner, and existing private spool root/storage owner. Reject missing,
   conflicting, overlapping, stale or unsupported identities; do not infer IDs from titles.
3. Validate S10A/C/D/E installation and enable both preparation and output-operation ownership in
   every relevant DAL instance. No old two-owner writer may coexist with operation admission.
4. Compose existing generation loader/partitioner, planner, coordinator, `LegacyProviderJob`, owned
   new-source delivery, `RequestBudget`, pool service, operator service and retirement recovery.
   Dedicated SDK clients remain per owner. Budget all reads, retries, grants, clear/readback and
   formatting using server UTC; no SQL transaction spans provider I/O or waits.
5. Bind `use_runtime` at each actual asynchronous/synchronous orchestration boundary, including
   manual commands, automatic capture/export, config refresh and scheduled writers. Startup task
   context alone does not establish later Discord task context. Test offload propagation explicitly;
   do not replace existing nested owner tokens or detach cancellation from an owned thread.
6. Preserve immutable running A; only eligible pending work coalesces. Keep original fairness age,
   daily ordering/history, registration-aware waiting intents and one-period compaction. Keep full
   output/config/header/provenance capture, spool digest/length/owner and unavailable capture state.
7. Shutdown closes admission first, then drains owned SDK/budget/readback/confirmation. Timeout,
   forced exit, missing spool or lost checkpoint retain claims for explicit reconciliation.

Reuse existing snapshot, provider, budget, partition, full-readback, access and interaction helpers.
No parser/calculator rewrite, command SQL, new top-level command, unrelated cleanup or dependency
is proposed. These are required release dependencies, not deferred optimisation items.

### Trusted proof production and conservative outcomes

The SQL/DAL checks validate proof shape and exact CAS; they cannot certify the producer. Proposed
proof service must combine an independently controlled execution-authority record with fresh,
read-only provider observations. Evidence must be private, durable, attributable and bound to the
exact snapshot hash, account/files, job/attempt or operation, owner/fence/version, epoch and
registration. A free-text operator assertion, editable Boolean, SQL lease, timestamp or PID alone
is insufficient. PID reuse must not identify a process incarnation.

| Consumer | Existing proof contract | Producer obligation |
|---|---|---|
| Rollover drain | `all_writers_terminated`, `remote_outcomes_reconciled`, `snapshot_hash`, `evidence_id` | Enumerate all old writers and nested owners; independently prevent further requests and reconcile already escaped requests before `ready` |
| Export reconciliation | `writer_terminated`, `state`, exact snapshot/evidence; confirmed receipt pins export key, attempt, fence, ordered files, audience and remote ID | Read exact attempt output, ACL and pointer; preserve an existing receipt byte-for-byte; mismatches remain uncertain |
| Terminal absence | Above plus `no_delayed_effect` | Positive closure of all escaped request outcomes; missing pointer or repeated empty reads alone cannot prove absence |
| Ordinary retirement | Termination, current pointer and no-live-reference proof bound to exact old/new attempt | Verify superseded, explicitly non-final, unreferenced generation and complete slot membership; final/unknown/uncertain/quarantined assignments stay protected |
| Interrupted retirement | Confirmed publication plus `retirement_outcomes_reconciled` and `no_delayed_retirement_effects` | Reconstruct hashed journal/assignment evidence, cover former nested recovery owners, then admit exact versioned recovery token; read-before-clear; revoke recovery owner and freshly probe publication |
| Rollover completion | Terminated writer, completed state, exact files with private/empty evidence and old/new-season setup marker | Verify every registered file and marker against current operation snapshot before CAS; no speculative continuation of partial rollover |

Provider requests already accepted remotely can outlive a dead process. No finite sleep is proposed
as a no-delayed-effects proof. Until a concrete execution authority and request-outcome mechanism
are reviewed, the adapter must return unavailable/uncertain and perform no settlement, retry or
reuse. This unresolved mechanism is an explicit implementation-design gate, not a claim that an
injectable interface solves it. The initial implementation proposal may safely reject unsupported
proofs; it may not claim release readiness without the approved real evidence producer.

Reconciliation reads themselves require a reviewed account-budget/read-only authorization path
compatible with retained blocked claims. They must not steal a normal job claim, issue an unpaced
SDK call or acquire a conflicting SQL transaction across I/O. Exact producer deployment/credential
identity, evidence storage and request-outcome authority remain unfilled in the G4 packet.

### Unchanged release invariants

Retain fixed season source; supplied overall/B0 and authoritative aggregate/DKP; exact 11-10,
12-10, final 13-10 and authorized 14-10 with explicit counterpart attestation and matched UpdateID.
Preserve exact owner/fence/version CAS, monotonic epochs, append-only dispositions and byte-exact
receipts. Capacity is `1 + P + P + max(P,Q) + P + R` using actual 9,000,000-cell parts, with 8/16
bounds; retained evidence is never free capacity. Rollover closes admission, drains/reconciles,
proves termination and privately clears/reads back before audited reuse. Uncertain remains
reconciliation, never blind retry or mutable generation relabeling.

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

2026-09-12. Documentation/read-only S7 approved by Chris Watts in the task starter.
**Design delivered for review; runtime, SQL, configuration and operations are not approved.**
Read with [exact manifests and validation](integration_implementation_manifests.md),
[settled decisions](post_s6_integration_requirements.md), the
[approved architecture](phase_2_contract_and_architecture.md) and
[handoff](post_s6_handoff_log.md). S7-D01–D09 are settled, not questions.

## 1. Scope summary and evidence boundary

Ordinary whole-KVK reports, linked card context, diagnostics and spreadsheet outputs
need an actual season resolver and a complete-update selection. Existing V2 adapters
are useful foundations, not public integration. Source-independent KS4 metrics,
targets, finalized history and calendar systems retain the approved architecture's
ownership; every C01–C65 row below is classified explicitly. No all-kingdom records
enter daily SCANORDER or replace independent target/profile/history data.

Read-only entry: Bot main/origin/main `a2f148fa9bd4fb367fd46d0500a768c14fee915b`,
local production/main `a8c9c515066ca6ef079120b76dd160e3389badab`; SQL main/origin/main
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot origin is
`https://github.com/cwatts6/K98-bot-mirror.git`, production is
`https://github.com/cwatts6/K98-bot.git`.
SQL origin is `https://github.com/cwatts6/K98-bot-SQL-Server.git`. Bot has the 23-path
handoff delta; SQL is clean. Tracking refs are local observations, not freshly fetched
remote heads. No fetch or provider query was used. SQL has no tracked AGENTS.md or
SECURITY.md; the supplied Bot/SQL-source instructions and migrations/README.md apply.

Mirror #272 and production-repository #579 are accepted merged evidence. Local
deployment is operator-attested. Neither production runtime deployment nor a fresh
post-merge smoke is established. All S1–S5B and S6 acceptance remains intact.

## 2. Fixed season source and serving contract — S7-D01/D02

Add `KVK.SeasonSource`, keyed by positive int KVK_NO, containing immutable
SourceKey (`legacy_full_data` or `snapshot_report_v1`), ChoiceID UUID, ChosenBy,
ChosenUTC, Reason, provenance and lifecycle (`planned`, `open`, `closing`, `closed`).
SourceKey/ChoiceID cannot be updated or deleted by ordinary workflow APIs. Lifecycle
changes use monotonic SeasonVersion CAS. Serving is a separate availability decision:
for new source retain SourceRouting.Enabled, RoutingVersion, DisplayPeriodID and
CapabilitiesVersion. Disabling serving never changes SeasonSource or permits legacy fallback.

New seasons require explicit admin choice before either importer accepts facts.
Neither first upload wins a source race nor channel selection chooses the season source.
Concurrent same-choice requests return the same audited choice; opposing requests
conflict. Enforce this again at the DAL acceptance transaction, including legacy intake
after its timestamp-based KVK resolution, before writing accepted rows or recomputing.
New intake without onboarding returns setup required; no implicit legacy default.
Distinct player observations remain accepted oldest first, with both logical ScanID and
UTC scan start increasing; do not use the older architecture draft's delayed-arrival example
to bypass the approved ordering amendment. A delayed older distinct event is rejected for
normal admission; corrections/semantic aliases retain their accepted identities.

Compatibility: a reviewed migration inventories historical legacy KVKs from existing
KVK_Scan and records legacy choices with migration provenance; existing new SourceRouting/
observations require explicit classification because S6 synthetic and partial selections
must not become public choices by accident. If both streams exist, migration reports the
conflict and does not choose. Do not infer identity from Enabled. Historical compatibility
is provided by these explicit SeasonSource rows with migration provenance, not a second
implicit-source rule: a read without a choice is unavailable. Backfill reviewed legacy seasons
before enabling ordinary reader integration; do not infer legacy from a moving date cutoff.
No data backfill is authorized in S7.

Proposed `resolve_season_read(kvk_no, period=None, capability=...)` returns one token:
source, ChoiceID/SeasonVersion, RoutingVersion, selected PeriodID, PublicSelectionVersion,
UpdateID/PublicationID, selected and desired config IDs, availability and reason. Resolve
under one short DAL transaction. A legacy token dispatches to unchanged legacy semantics;
a new token requires enabled serving, understood capability version and complete selection.
Missing row, incompatible schema, disabled serving, missing selection and failed integrity
are explicit unavailable outcomes. Database failure must not be interpreted as legacy.
Private diagnostics may deliberately inspect accepted incomplete state with admin access;
ordinary calls cannot inject a source or publication to bypass the resolver.

Requests load all blocks from the token's immutable publication. Cache keys include
source/KVK/period/publication/public-selection-version/schema and desired config version;
pointer resolution is authoritative on each new request, so notification loss cannot
serve old data as current indefinitely. Request-held cards/views remain pinned and labelled;
refresh replaces the whole envelope. Final action callbacks recheck actor and CAS versions.
Independent player/target/history cache keys and daily send counters are unchanged.

## 3. Matched update and endpoint contract — S7-D03/D04

Use a durable UpdateID UUID created by explicit metadata confirmation, not arrival order,
filename adjacency or equal timestamps. An update scope binds SourceKey/KVK_NO/PeriodID,
report family, intended coverage start/end and as-of context, config and roster versions.
Each accepted stream can reference that UpdateID. Existing attempts, immutable revisions,
semantic digests and logical-scan registry remain the acceptance authority.

For a normal fight, a sealed `KVK.SourceUpdate` binds exact start/end player revision IDs
and ScanIDs, aggregate report/revision ID (both kingdom/camp tabs), config/roster,
player and aggregate finality, confirmer and confirmation provenance. Enforce composite
same-source/KVK/period FKs and verify observation-to-logical-binding identity in the DAL.
An aggregate has no player ScanID. Both aggregate tabs are already one accepted revision.

Compatibility is a validated declared reporting context, not timestamp equality. Player
scan-start UTC and aggregate coverage/as-of remain independently visible. The metadata
confirmation names the intended update and exact stream revisions; coverage must belong
to the same fight and declared live/final scope, use its frozen camp map and expected
kingdom/camp identities, and contain no conflicting period designation. A new as-of value
does not silently retag another update. Unknown A1 fight assignment remains unselectable.
No numerical equality test with player sums, kingdom sums or regenerated aggregate DKP.

| Transition | Durable result and public effect |
|---|---|
| Create context; player first or aggregate first | Accept independently; `waiting_player` or `waiting_aggregate`; public selection unchanged |
| Second compatible accepted stream | Validate versions and membership; seal immutable revision tuple; candidate build may start |
| Incompatible second stream or stale confirmation | Reject association; preserve accepted input privately; public selection unchanged |
| Correction of one stream | Create successor update referencing correction and exact unchanged counterpart; require counterpart-validity confirmation with actor/reason/context |
| Complete candidate | In one transaction seal selection and export intent after CAS recheck; preserve prior complete selection/history |
| Duplicate semantic re-export | Existing attempt outcome/alias only; no new scan, update generation or export request |
| Build failure/restart | Resume sealed tuple; no reimport, guessed counterpart or MAX-scan reselection |

Counterpart confirmation can be supplied in the same normal import/config confirmation.
It names base update, retained counterpart revision, intended new player/config context and
actor. It is invalidated by any changed referenced revision/config/roster/coverage. Unattended
config refresh cannot manufacture an operator's attestation. If the attestation was supplied
while an authorized endpoint was pending, arrival of that exact endpoint resumes automatically.

Preserve interim 11−10, then 12−10, final 13−10. An authorized EndScanID change to 14
permits replacement 14−10 **without another correction command**. The normal config
confirmation may also confirm that the exact retained aggregate remains valid for the new
context. Without that confirmation or a new matched aggregate, the player calculation can
complete privately but public selection waits. This is pair eligibility, not a second
authorization to correct the player endpoint. No synthetic aggregate upload is required.
The old 13−10 result is labelled previous/config pending against desired 14; it is not current
final. Failed config processing retains durable desired intent; endpoint chains and CAS prevent
older builders winning. Unrelated weight/map/roster changes still need their own reviewed authority.

### Domain exceptions, not generic partial-publication bypasses

| Context | Rule |
|---|---|
| B0 onboarding | Accept/freeze eligible roster and B0 kingdom attribution privately without aggregate; no combat public update/export intent is generated by onboarding |
| Configured equal endpoints/no-fight | All frozen B0 members receive supported zero fight scores under the accepted resolver, including absent scan members; no combat ranks; aggregate `not_applicable`; explicit typed no-fight update can select without fabricated report |
| Missing individual metric/member endpoints | Keep available/unavailable states; complete pair means both intended streams, not every metric or governor usable; never substitute zero |
| Overall before its aggregate | Player B0→latest calculation remains private; ordinary overall reports say waiting for separate overall aggregate; last eligible complete overall may be shown as previous |
| Complete overall | Bind separately supplied final overall aggregate to explicitly selected B0→end player context; independently label stream finality; no fight sum or arbitrary first/last player fallback |
| Config-only display rename | Reuse exact immutable inputs with new reviewed config provenance; no numerical rewrite; no-op digest creates no export |
| Config changes inputs/coverage | Successor update must meet pair rules; endpoint authority is carried from SourceConfigRequest; weight/map/roster changes never inherit endpoint-only authority |
| Legacy season | Legacy Full Data is the legacy complete source unit; do not demand the new two-workbook format or reinterpret historical calculations |

Earlier T40 partial-stream public selection and generic final-unavailable substitution are
superseded for normal public combat updates. Accepted private component behavior remains
historical evidence. T36 player overall without aggregate is now private-only; an explicit
unavailable public message is permitted. T66 cross-source fallback is prohibited within a
fixed-source season, even if legacy observations exist. T58 stale pending export is coalesced;
an already running export follows the finish-current rule below.

## 4. Atomic complete selection and export intent

Retain SourcePublication and SourceSelection as accepted component history. Add
`KVK.SourceCompleteSelection`, keyed by source/KVK/period, pointing to sealed UpdateID
and a complete immutable PublicationID with increasing PublicSelectionVersion. Ordinary
reads/exports must use this gate, not an arbitrary complete SourcePublication (which can
legitimately have missing aggregate under predecessor contracts).

A sealed update selects its explicitly matched player/aggregate revisions even if a newer
unmatched stream has been accepted. Existing `validate_snapshot_inputs` checks the global
latest logical scan for live candidates; S8B must replace that check for paired publication
with sealed-update identity/CAS validation, so an unmatched input cannot starve a complete
pair. Accepted correction policy still applies.

Build facts outside the selection transaction. The short commit locks season then period,
checks fixed source, lifecycle, expected public/config/input versions and sealed pair,
verifies complete counts/hash, advances the complete pointer, records action and inserts
`KVK.SourceExportIntent` plus its `SourceExportIntentPublication` rows. The intent pins the
full current complete per-period vector, including unchanged periods, for one season update.
The vector includes public versions, config IDs and a content hash. No target registration
is needed to retain intent; missing destination leaves `waiting_destination`, not lost work.

All new-source writers use one SQL lock order: SeasonSource → SourceRouting → sorted
period selection rows (component and complete) → config/request/update rows → intent/vector
rows. Adapt existing routing-first helpers to acquire the season guard first; no opposite
ordering. The season guard serializes vector snapshots, so simultaneous completed periods
cannot lose each other's membership.

The stable intent key is source/KVK/vector-hash/export-schema, with a new explicit rebuild
revision only for output repair. Publication commit acknowledgment loss returns existing
selection/intent. Intake acceptance followed by failed candidate build remains accepted
and resumable; public commit and export intent cannot diverge. SourceAction alone cannot
record season/queue/rollover actions because its schema requires a period and new publication.

Publication availability and spreadsheet readiness are separate receipts. Public command
data may use the new complete SQL publication while Sheets still shows an older confirmed
export; label export age/key separately. Automatic import export does not authorize an extra
Discord send. Existing stats dispatch remains the sole owner of its daily claim policy.

## 5. Shared coordination and restart contract — S7-D05/D06/D07

New source uses durable SQL job/admission state shared with all-KVK and scan-data export
wrappers. `dbo.ExportJob` binds consumer, season when relevant, immutable input/intent,
account identity, registered destination set, pool epoch, state, owner/fence and enqueue
sequence. `dbo.ExportJobResource` records conflicts; `dbo.ExportResource` owns active
job/owner/fence and blocked reason. General tables use dbo because daily exports are not
new-source KVK publications. One coordinator database is required for all participating
machines/processes; separate local DBs cannot establish mutual exclusion.

Resources: resolved Google spreadsheet IDs (including index, parts and all legacy output
files), account identity plus project budget, and legacy SQL snapshot resource for mutable
source tables/config. Sheet titles are discovery labels, not resource identity. Register IDs
before mutation; aliases to the same file conflict. Provisioning must reserve account admission
before discovery/create and register returned IDs before content mutation. Overlap between
new pool and legacy/scan output IDs is rejected at registration. No user-supplied arbitrary URL.

Use conservative one-running-export-per-account admission initially. Other accounts with
disjoint destinations can proceed. New immutable input acceptance and candidate calculation
can proceed while a provider export runs. Legacy SQL ingestion/recompute/config and scan-data
snapshot acquisition share a short SQL-resource/session lock through their Bot wrappers,
released before provider work. Capture all export result sets/config/provenance together into
an immutable durable spool with SQL digest/length/owner receipt, then use only that snapshot.
Do not read mutable tables between provider tabs. Snapshot capture and legacy writers must
participate in the same admission protocol across processes; external SQL agents/standalone
scripts are a deployment inventory gate, not an assumed participant. No UPDATE_ALL2 transaction
wrapper: it owns/rejects ambient transactions; use session admission outside its internal phases.

Acquire legacy SQL snapshot admission once at the producer orchestration boundary and pass a
validated ownership token to nested DAL/config helpers; do not reacquire the same exclusive
resource through another connection while the caller holds it. Keep the producer's import
receipt, committed output provenance and snapshot capture associated under that admission.
Config provider reads are collected before entering the SQL portion. Failure after SQL commit
but before spool registration records pending snapshot work for that committed generation;
if mutable output has since advanced, report that mismatch and require a fresh explicitly
identified snapshot, never label newer values as the failed import's output.

Spool location is a registered private durable storage root shared by eligible workers; do not
use a temporary directory or credential-relative path as authority. Missing/corrupt spool makes
the job blocked; rebuild snapshot only before external mutation, with a new audited job identity.
If no shared storage is provisioned, pin spool jobs to a worker/storage identity; another machine
can report/reconcile but cannot claim execution. New-source jobs can reload immutable SQL facts.

Legacy all-KVK acceptance and recompute currently commit separately. A raw ScanID alone
does not prove output completion. Its coordinated producer records a ready snapshot/job only
after successful recompute and consistent export capture, with exact scan/config/output hashes
in provenance. Manual legacy export may reuse a verified ready snapshot without recompute;
if no valid completion provenance exists, report setup/output unavailable rather than invent
a complete publication. Daily jobs similarly pin their existing committed output/header proof.
This adds export evidence without repurposing SourcePublication for legacy or daily schemas.

Account budget is separate from destination ownership. `dbo.ExportRequestBudget` reserves
the next request time using SQL UTC under a short transaction, then waits outside SQL.
Initially preserve the measured conservative 2.1-second spacing; this is an engineering
starting budget, not a provider quota claim. Wrap both gspread HTTP requests and google-api
execute calls, including reads, retries, grants and formatting. A second process cannot bypass
it. 429/503 update a common cooldown from bounded validated Retry-After/backoff; mutation
ambiguity does not become permission for blind replay. Other account consumers must be
registered or operationally excluded at S11; this code cannot pace unknown external clients.

Lock order: account admission, sorted destination IDs/pool epoch, then short job-row CAS;
season/period/publication transactions never wait for provider admission. Budget reservations
are independent short transactions. No SQL transaction spans any Google request, including
pointer publication. Current `DeliveryRepository.publication_gate` holds a transaction around
publication and checks latest selection; replace that use for coordinated jobs with durable
attempt/epoch authorization before each external phase and monotonic destination sequencing.

| Job state/event | Required transition |
|---|---|
| A running; complete B then C arrive | A's vector never changes; B pending request becomes `coalesced` with SupersededBy=C; B inputs/publication/intent remain; C is latest pending |
| A completes | Record remote verification and confirmed receipt; release resources; latest pending C becomes eligible, subject to account fairness |
| Several consumers waiting | Oldest admission ticket across consumers; replacing one consumer's pending vector retains its original ticket age; no manual priority jump; after each job admit the oldest eligible ticket |
| Failure before any provider mutation | Audited retry eligible; recheck epoch/source; no new import or calculation |
| Failure after private writes | Retain attempt and exact parts; use accepted quarantine/fresh-slot recovery only after old worker cannot advance publication |
| Grant/pointer timeout, process loss or late completion | Mark uncertain and block conflicting destination; lease expiry/session loss is not absence proof; probe exact attempt evidence; no automatic takeover |
| Cancellation/shutdown | Stop new admission; pending remains durable; running worker checkpoints and drains where possible; detaching a timed-out thread does not release its resources |
| A superseded while running | Allow A to finish against pinned authorized job/epoch even though public selection has advanced; C then advances the export pointer; never overwrite a newer confirmed destination sequence |

A failed/uncertain A must reach a permitted terminal or isolated recovery state before C can
advance that destination. SQL fences cannot cancel an already submitted Google request.
Keep the blocked epoch until readback plus terminated-worker evidence resolves uncertainty;
for private abandoned attempts isolate fresh files and forbid old pointer/grant phases.
Do not implement automatic lease-steal publication. Long jobs (accepted ~38 minutes) make
unconditional timeouts unsafe. Coalescing affects pending new-source exports only; daily
SCANORDER jobs/import history retain their existing ordering and are not discarded.

## 6. Grouped export-only UX — S7-D09

Extend existing `/kvk_admin source` action choices rather than create a top-level command:
`export`, `export_status`, `export_reconcile`, `export_rebuild`, and `rollover_preview`/
`rollover_confirm`. Season choice and pair association are additional `source` actions
`choose_source` and `match_update`; extend existing intake confirmation for UpdateID and
counterpart validity. Final option names/signature changes are reviewed with registration.
Commands/views enforce configured guild/channel/admin role and recheck current authority at
confirmation. Services accept typed actor authorization context, not Discord objects.

Export takes KVK and a registered destination key, pins the selected complete vector, and
queues without parsing, importing, recalculating, changing endpoints or publishing Discord.
Ephemeral reply: queued/running/waiting for counterpart/confirmed/no-op/blocked for reconciliation,
with period/as-of and current output link only when confirmed. Ordinary `export_all` delegates
to the fixed-source service; legacy export behavior remains for legacy seasons. Recompute on
new source is private inspection/build policy, not an export-only shortcut or implicit correction.

Confirmed same generation returns no-op with zero provider calls. Failed safe retry retains
identity. Uncertain attempt uses readback/reconcile, never `retry=true`. Damaged confirmed
output requires explicit rebuild preview and confirmation with reason, expected generation/
epoch and fresh RepairID: same accepted input/publication/vector, new export attempt. Retain
original confirmed receipt and damage/rebuild audit. A status query is read-only. Stale buttons,
wrong owner/guild, expired token or lost role cannot enqueue. Rehydrate confirmation from SQL
or make it expire safely on restart; no in-memory-only authority. No raw private rows/paths in replies.

## 7. File pool and rollover — S7-D08; S6-CAP01

Let P be the maximum measured/planned parts per generation from the existing partitioner,
including headers/directory and the 9,000,000-cell per-part ceiling. Initial recommended
capacity is **1 stable index + P active + P staging + max(P,Q) quarantine + P reserve + R**,
where Q is actual quarantined parts and R is other protected final/referenced parts that
cannot yet retire. For P=2, Q<=2 and R=0 this is nine files, a minimum allowance rather than
a guarantee for the retained S6 pools. This covers one quarantined generation, not unlimited
uncertain attempts. Recompute P/Q/R before writes for actual 36-kingdom/mixed reports and future
period counts. Do not equate the synthetic two-kingdom benchmark with a production maximum.

Register pool/slot ownership durably with unique file IDs and epoch. A slot is free, staging,
active, quarantined or retired; assignments/attempt-part receipts are append-only history.
Never overwrite current, uncertain, still-owned or quarantined files based on age. Preflight
all required parts and receipt capacity before claim/provider mutation. Normalize new multipart
receipts into attempt/part rows rather than growing the existing nvarchar(1024) JSON indefinitely.
Existing SourceDelivery receipts remain byte-preserved; migration does not truncate or rewrite them.
Keep the current registration bounds (at most eight registrations and sixteen slots per
registration) until a separately reviewed limit change. A computed allowance exceeding those
bounds returns setup required before mutation. During the KVK, existing final/live-reference
protection remains; at rollover explicit retirement releases confirmed historical remote
representations while retaining their input/publication facts. No final-history deletion is needed.

Rollover: preview exact old/new KVK, all jobs/receipts/file IDs and epoch; freeze old-season
admission (`closing`); finish/reconcile running work; cancel only never-started pending export
requests with audit; preserve publications/inputs; increment epoch after proving no old writer
can act; mark confirmed remote receipts `retired` by a separate disposition event. Their old
URL means retired/reused, not a continuing archive. Discord messages are not silently edited
or removed. The stable index shows season ended/setup until the next verified generation.

Before reusing a file, remove prior public Viewer exposure under explicit rollover authority,
verify private ACL, clear all prior tabs/data/formatting/named ranges and replace with the
expected empty manifest. Read back before assignment to the new epoch. Uncertain ACL/clear
leaves quarantine. Exact current/uncertain index cannot be reused under a new epoch without
resolving the old pointer operation; using a new index instead is a separately reviewed destination
change. New generation fully verifies privately, then audience grants and pointer publication
follow the accepted receipt protocol. Late old completions fail epoch validation and do not free
slots. There is no lifetime spreadsheet-archive requirement; SQL/input/audit history remains.

## 8. Authoritative SQL comparison and proposed state

Source snapshots read at SQL `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; no SQL server
connection or execution. SQL deployment remains unsafe until future migrations/tests/review.

| Existing exact object | Verified constraint and design consequence |
|---|---|
| KVK.SourceRouting | PK KVK_NO; SourceKey check only snapshot_report_v1; Enabled approval guard and FK to SourceSelection; add separate SeasonSource, do not reinterpret this as legacy choice |
| KVK.SourceSelection | Composite source/KVK/period PK and scoped publication FK; SelectionVersion >0; no pair registry; add SourceCompleteSelection |
| KVK.SourcePublication | UUID PK, scoped unique keys, config/roster/start/end/aggregate FKs; complete BuildState proves counts/hash but permits absent aggregate; retain historical rows and require sealed update for public pointer |
| KVK.SourceDelivery | PK publication/kind/destination; destination <=128; receipt nvarchar(1024); owner/fence/state constraints; cannot identify arbitrary legacy/daily jobs or repeated repaired output attempts |
| KVK.SourceImportAttempt | Guild/message/attachment/action replay unique; exactly one accepted revision kind; provenance JSON <=65536 bytes; no explicit pair ID; association belongs in SourceUpdate |
| KVK.SourceObservationRevision / SourceLogicalScan / SourceScanBinding | Separate immutable revision/scan binding namespace; association must verify exact observation behind each logical scan; aggregates never allocate scans |
| KVK.SourceAggregateRevision / SourceKingdomReportRow / SourceCampReportRow | Scoped accepted revision with both tab sets; Decimal/raw precision remain authoritative; pair does not recompute values |
| KVK.SourceConfigVersion / SourceWindowConfig / SourceCampConfig / SourceWeightConfig | Versioned roster/window/map/decimal coefficient snapshots; references remain immutable; no changes to sheet A:F/A:D contracts |
| KVK.SourceConfigRequest | Endpoint chain, desired/base config, Origin/Actor/Reason, requested/pending/applied/rejected; replay unique by config hash/base; use for endpoint authority, not aggregate attestation |
| KVK.SourceAction | Period/new-publication required; limited action enum and provenance; retain publication actions, use new queue/season audit fields for other scopes |
| KVK.KVK_AllPlayers_Stage / Raw / Player_Baseline / Player_Windowed / Kingdom_Windowed / Camp_Windowed | Legacy keys omit source/revision and recompute rebuilds partition; no new-source inserts or semantic reinterpretation |
| KVK.KVK_Windows / KVK.KVK_CampMap / KVK.KVK_DKPWeights | Source-independent configuration input; version before new-source use; no sheet layout or inferred ID namespace change |
| dbo.ProcConfig / dbo.STAGING_STATS / dbo.STATS_FOR_UPLOAD / dbo.EXCEL_FOR_KVK_* / dbo.KingdomScanData4 | Daily target/history pipeline, not a destination for new all-kingdom facts; retain exact output and SCANORDER contracts |

New entity column/key specifications and exact migration paths are in the manifest document.
No new UDT is required. Old SQL procedures/views/functions remain legacy contracts. Missing
proposed objects are deliberate creates, not claims of deployed schema. Read-only discovery found
no `KVK.SourceEndpointRequest`: the actual existing object is `KVK.SourceConfigRequest`.

## 9. Consumer matrix

Each row below records the current entry symbol/path at the verified Bot/SQL heads, current
source and proposed seam. Historical C IDs are retained. `R` means fixed-source resolver and
complete token from section 2; `Q` means shared admission/snapshot/pacing from section 5;
`I` means deliberately independent per approved architecture, with no source migration.
Tests are exact Bot paths under `tests/` unless prefixed SQL. A listed test is planned coverage,
not a new pass. Current line locations are navigation aids, not historic Phase-1 line assertions.

| ID | Current exact entry | Current source → output | Proposed seam and chosen-source coverage | Version/cache owner | Planned test files |
|---|---|---|---|---|---|
| C01 | `DL_bot.py:518` — `on_message` | legacy whole-KVK / Discord channel dispatch → handle_kvk_all_upload | R admission before legacy acceptance; new private route remains first; Q automatic export handoff | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_upload_route.py`; `tests/test_kvk_source_upload_route.py` |
| C02 | `upload_routes/kvk_all_route.py:271` — `handle_kvk_all_upload` | legacy whole-KVK / PROKINGDOM_CHANNEL_ID attachments → ingest_kvk_all_excel | R admission before legacy acceptance; new private route remains first; Q automatic export handoff | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_upload_route.py`; `tests/test_kvk_source_upload_route.py` |
| C03 | `kvk_all_importer.py:42` — `ingest_kvk_all_excel` | legacy whole-KVK / prepare_kvk_all_import → ingest_prepared_import | R admission before legacy acceptance; new private route remains first; Q automatic export handoff | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_upload_route.py`; `tests/test_kvk_source_upload_route.py` |
| C04 | `kvk/services/kvk_all_import_service.py:72` — `read_full_data_workbook` | legacy whole-KVK / Full Data only → canonical frame | Legacy-only parser unchanged; fixed-source rejection occurs before accepted persistence, never parse new source as Full Data | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_service.py`; `tests/test_kvk_new_source_parser.py` |
| C05 | `kvk/services/kvk_all_import_service.py:175` — `coerce_full_data_frame` | legacy whole-KVK / legacy frame → stage fields | Legacy-only parser unchanged; fixed-source rejection occurs before accepted persistence, never parse new source as Full Data | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_service.py`; `tests/test_kvk_new_source_parser.py` |
| C06 | `kvk/dal/kvk_all_import_dal.py:289` — `ingest_prepared_import` | legacy whole-KVK / stage insert + ingest procedure → raw + recomputed outputs | R fixed-source check after resolved KVK and before accepted writes; Q legacy SQL snapshot admission | R token/pinned publication; Q job vector where exported | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_season_source.py` |
| C07 | `services/kvk_all_import_audit_service.py:1` — `services/kvk_all_import_audit_service.py` | legacy whole-KVK / upload audit context → dbo.ImportAuditBatch/ImportAuditPhase through shared service | Preserve best-effort audit; add job/choice IDs at caller; audit is not admission authority | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_audit_service.py` |
| C08 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_Scan | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C09 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_AllPlayers_Raw | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C10 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_Player_Baseline | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C11 | SQL `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:1` — `sp_KVK_AllPlayers_Ingest` | legacy whole-KVK / KVK.KVK_AllPlayers_Stage → KVK.KVK_Ingest_Negatives | Legacy-only proc, R guarded Bot DAL; historical SQL preserved; external writers require S11 inventory | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_all_recompute_sql_contract.py` |
| C12 | SQL `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:1` — `sp_KVK_Recompute_Windows` | legacy whole-KVK / KVK_Scan/Windows/Raw/Baseline/Weights/CampMap → KVK.KVK_Player_Windowed | Legacy-only recompute; R rejects new-season invocation; Q snapshot lock in caller; no new facts written here | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py`; `tests/test_kvk_admin_service.py` |
| C13 | SQL `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:1` — `sp_KVK_Recompute_Windows` | legacy whole-KVK / KVK.KVK_Player_Windowed → KVK.KVK_Kingdom_Windowed | Legacy-only recompute; R rejects new-season invocation; Q snapshot lock in caller; no new facts written here | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py`; `tests/test_kvk_admin_service.py` |
| C14 | SQL `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:1` — `sp_KVK_Recompute_Windows` | legacy whole-KVK / KVK.KVK_Player_Windowed + CampMap → KVK.KVK_Camp_Windowed | Legacy-only recompute; R rejects new-season invocation; Q snapshot lock in caller; no new facts written here | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py`; `tests/test_kvk_admin_service.py` |
| C15 | SQL `sql_schema/dbo.fn_KVK_Player_Aggregated.UserDefinedFunction.sql:1` — `fn_KVK_Player_Aggregated` | legacy whole-KVK / KVK.KVK_Player_Windowed + KVK_Windows → dbo.fn_KVK_Player_Aggregated | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C16 | SQL `sql_schema/dbo.fn_KVK_Kingdom_Aggregated.UserDefinedFunction.sql:1` — `fn_KVK_Kingdom_Aggregated` | legacy whole-KVK / KVK.KVK_Kingdom_Windowed + KVK_Windows → dbo.fn_KVK_Kingdom_Aggregated | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C17 | SQL `sql_schema/dbo.fn_KVK_Camp_Aggregated.UserDefinedFunction.sql:1` — `fn_KVK_Camp_Aggregated` | legacy whole-KVK / KVK.KVK_Camp_Windowed + KVK_Windows → dbo.fn_KVK_Camp_Aggregated | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C18 | SQL `sql_schema/KVK.vw_FightingDataset.View.sql:1` — `vw_FightingDataset` | legacy whole-KVK / KVK_Player_Windowed + KVK_Windows → KVK.vw_FightingDataset | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C19 | SQL `sql_schema/KVK.vw_Player_Overall_KVK_Rank.View.sql:1` — `vw_Player_Overall_KVK_Rank` | legacy whole-KVK / KVK.KVK_Player_Windowed Full → KVK.vw_Player_Overall_KVK_Rank | Legacy-only object retained; new R service bypasses legacy sum/rank objects; no runtime direct view activation | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_public_routing.py`; `tests/test_kvk_stats_card_sql_contract.py` |
| C20 | `kvk/dal/kvk_reporting_dal.py:58` — `fetch_top_players` | legacy whole-KVK / fn_KVK_Player_Aggregated + latest KVK_DKPWeights → players_by_kills/deads/dkp; our_top_players | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C21 | `kvk/dal/kvk_reporting_dal.py:105` — `fetch_top_kingdoms` | legacy whole-KVK / fn_KVK_Kingdom_Aggregated + latest KVK_DKPWeights → kingdoms_by_kills/deads/dkp | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C22 | `kvk/dal/kvk_reporting_dal.py:138` — `fetch_top_camps` | legacy whole-KVK / fn_KVK_Camp_Aggregated + latest KVK_DKPWeights → camps_by_kills/deads/dkp | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C23 | `kvk/dal/kvk_reporting_dal.py:170` — `fetch_kingdom_summary` | legacy whole-KVK / KVK_Kingdom_Windowed + latest KVK_DKPWeights → our_kingdom | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C24 | `kvk/dal/kvk_reporting_dal.py:206` — `fetch_camp_summary` | legacy whole-KVK / KVK_Camp_Windowed + latest KVK_DKPWeights → our_camp | R at enclosing report service; new publication DAL supplies ranks and independent aggregate rows; legacy query only with legacy token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_source_reporting.py` |
| C25 | `kvk/services/kvk_reporting_service.py:68` — `load_allkingdom_reporting_blocks` | legacy whole-KVK / kvk_reporting_dal → 12 report blocks | R ordinary service entry; one token for all twelve blocks; V2 never passes legacy zero normalization | R token/pinned publication; Q job vector where exported | `tests/test_kvk_reporting_service.py`; `tests/test_kvk_public_routing.py` |
| C26 | `stats_alerts/embeds/kvk.py:153` — `build_kvk_preview` | legacy whole-KVK / allkingdom blocks + KVK metadata → two fighting embeds | R ordinary preview/send, same V2 renderer as diagnostic; stale/unavailable explicit | R token/pinned publication; Q job vector where exported | `tests/test_kvk_embed.py`; `tests/test_kvk_public_routing.py` |
| C27 | `stats_alerts/interface.py:24` — `_send_stats_update_embed` | legacy whole-KVK / ks4 lifecycle + fighting preview → send_kvk_embed and guard claim | R through build_kvk_preview; preserve CSV daily cap/receipt ownership; wake is not automatic Discord authorization | R token/pinned publication; Q job vector where exported | `tests/test_stats_alerts_fighting_lifecycle.py`; `tests/test_stats_alerts_guard.py` |
| C28 | `admin_helpers.py:101` — `log_processing_result` | legacy whole-KVK / kingdom processing successful steps → send_stats_update_embed | R through build_kvk_preview; preserve CSV daily cap/receipt ownership; wake is not automatic Discord authorization | R token/pinned publication; Q job vector where exported | `tests/test_stats_alerts_fighting_lifecycle.py`; `tests/test_stats_alerts_guard.py` |
| C29 | SQL `sql_schema/KVK.sp_KVK_Get_Exports.StoredProcedure.sql:1` — `sp_KVK_Get_Exports` | legacy whole-KVK / KVK scan/config/windowed/negative objects → ten named export result sets | Legacy sections remain legacy; R selects V2 generation builder for new season; never bind V2 by legacy positional inference | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_export_service.py`; `tests/test_kvk_source_exports.py` |
| C30 | `kvk/services/kvk_export_service.py:272` — `bind_kvk_export_sections` | legacy whole-KVK / ten SQL result sets → stable section names | Legacy sections remain legacy; R selects V2 generation builder for new season; never bind V2 by legacy positional inference | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_export_service.py`; `tests/test_kvk_source_exports.py` |
| C31 | `gsheet_module.py:3326` — `run_kvk_proc_exports_with_alerts` | legacy whole-KVK / sp_KVK_Get_Exports → primary and additional Google spreadsheets | R/Q wrapper delegates to immutable generation or legacy snapshot with durable job; no direct public new-source write | R token/pinned publication; Q job vector where exported | `tests/test_kvk_export_coordination.py`; `tests/test_gsheet_module.py` |
| C32 | `gsheet_module.py:1891` — `_aggregate_windowed_dfs` | legacy whole-KVK / player/kingdom/camp Windowed sections → ALL_WINDOWS | Legacy-only summation/pivots retained; R new export bypasses and uses exact period vector/independent overall; Q all provider writes | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_source_exports.py`; `tests/test_kvk_export_service.py` |
| C33 | `gsheet_module.py:2059` — `create_additional_kvk_spreadsheets` | legacy whole-KVK / windowed sections → Pass4/Altar1-3/Pass7/Pass8/GreatZig/Pass9 and comparison sheets | Legacy-only summation/pivots retained; R new export bypasses and uses exact period vector/independent overall; Q all provider writes | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_source_exports.py`; `tests/test_kvk_export_service.py` |
| C34 | `gsheet_module.py:782` — `export_dataframe_to_sheet` | legacy whole-KVK / DataFrame → Google Sheets RAW values | Q transport pacing/destination ownership; retain RAW values, literal text and formatting | R token/pinned publication; Q job vector where exported | `tests/test_gsheet_module.py`; `tests/test_kvk_export_coordination.py` |
| C35 | `commands/stats_cmds.py:483` — `kvk_export_all` | legacy whole-KVK / admin service/export runner → Sheets | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C36 | `commands/stats_cmds.py:556` — `kvk_recompute` | legacy whole-KVK / admin service/recompute proc → windowed outputs | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C37 | `commands/stats_cmds.py:582` — `kvk_list_scans` | legacy whole-KVK / admin DAL/KVK_Scan → recent-scan diagnostic | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C38 | `commands/stats_cmds.py:720` — `kvk_window_preview` | legacy whole-KVK / admin DAL/Windows/Scan/Player_Windowed → window diagnostic | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C39 | `commands/stats_cmds.py:614` — `test_kvk_embed` | legacy whole-KVK / build_kvk_preview → isolated embed | R grouped admin service; export through Q, new recompute cannot silently rewrite finals, private previews retain explicit pinning | R token/pinned publication; Q job vector where exported | `tests/test_kvk_admin_service.py`; `tests/test_kvk_embed_diagnostic_command.py`; `tests/test_kvk_export_operator.py` |
| C40 | `kvk/dal/kvk_stats_card_dal.py:19` — `fetch_kvk_stats_card_context` | legacy whole-KVK / Player_Windowed Full preferred + CampMap + overall rank view → /kvk stats card context | R card context only; new source reads frozen B0 camp/rank from publication, never legacy camp fallback | R token/pinned publication; Q job vector where exported | `tests/test_kvk_source_card_context.py`; `tests/test_kvk_stats_card_dal.py` |
| C41 | `services/kvk_personal_service.py:21` — `load_kvk_personal_stats` | kingdom-only KS4 / utils.load_stat_row → /kvk stats main statistics | I main KS4 numerator/targets; separate source context via C43, no all-kingdom metric injection | Existing independent owner; no source cache mutation | `tests/test_kvk_personal_service.py`; `tests/test_kvk_personal_views.py` |
| C42 | `commands/kvk_cmds.py:541` — `register_kvk` | mixed / personal/target/history/rank services → /kvk stats/targets/history/rankings | Mixed: I command main stats/targets/history/rankings; R source context via posting helper; view refresh remains whole-token | R token/pinned publication; Q job vector where exported | `tests/test_kvk_cmds.py`; `tests/test_kvk_stats_card_views.py` |
| C43 | `kvk/services/kvk_stats_card_service.py:182` — `build_kvk_stats_card_payload` | mixed / stats cache + C40 context → stats card/renderers/fallback | R context resolver invoked by ordinary payload; preserve I main measures; separate labelled source/cohort or suppress context | R token/pinned publication; Q job vector where exported | `tests/test_kvk_stats_card_payload.py`; `tests/test_kvk_source_card_context.py` |
| C44 | `player_stats_cache.py:755` — `_build_cache_sync` | kingdom-only KS4 / SP_Stats_for_Upload + STATS_FOR_UPLOAD → player stats JSON cache | I immutable validated KS4 cache provenance/atomic replacement; no new-source invalidation | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline_build_cache.py` |
| C45 | SQL `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql:1` — `SP_Stats_for_Upload` | kingdom-only KS4 / ProcConfig/KingdomScanData4/KVKFinalReportHeader/EXCEL_FOR_KVK_n → dbo.STATS_FOR_UPLOAD | I KS4 output/final-header contracts; Q consistent legacy snapshot acquisition, no source schema rewrite | Existing independent owner; no source cache mutation | `tests/test_kvk_history_dal.py`; `tests/test_kvk_rankings_finalized_sql_contract.py` |
| C46 | SQL `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql:1` — `sp_ExcelOutput_ByKVK` | kingdom-only KS4 / KS4 + ProcConfig + delta tables → STAGING_STATS then EXCEL_FOR_KVK_n + final report header | I KS4 output/final-header contracts; Q consistent legacy snapshot acquisition, no source schema rewrite | Existing independent owner; no source cache mutation | `tests/test_kvk_history_dal.py`; `tests/test_kvk_rankings_finalized_sql_contract.py` |
| C47 | SQL `sql_schema/dbo.IMPORT_STAGING_PROC_CORE.StoredProcedure.sql:1` — `IMPORT_STAGING_PROC_CORE` | kingdom-only KS4 / immutable fallback CSV + receipt → IMPORT_STAGING | I daily SCANORDER and fallback receipts; Q Bot pipeline session admission around mutable SQL work; no all-kingdom intake | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline.py`; `tests/test_kvk_export_coordination.py` |
| C48 | SQL `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql:1` — `UPDATE_ALL2` | kingdom-only KS4 / IMPORT_STAGING → KS5 -> KS4 -> delta/output orchestration | I daily SCANORDER and fallback receipts; Q Bot pipeline session admission around mutable SQL work; no all-kingdom intake | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline.py`; `tests/test_kvk_export_coordination.py` |
| C49 | `processing_pipeline.py:163` — `execute_processing_pipeline` | kingdom-only KS4 / fallback queue/stats_module → cache/config/export/delivery steps | I import lifecycle/cache order; Q capture committed snapshot and durable job, remove timeout-detached ownership release | Existing independent owner; no source cache mutation | `tests/test_processing_pipeline.py`; `tests/test_processing_pipeline_run_step_and_normalization.py` |
| C50 | `kvk/services/kvk_rankings_service.py:445` — `build_kvk_rankings_payload` | kingdom-only KS4 / utils.load_stat_cache → current rankings cards/Top25/50/My Rank/CSV | I KS4 rankings (Top25/50/My Rank/CSV), not whole-KVK reporting rank; preserve cache cohort | Existing independent owner; no source cache mutation | `tests/test_kvk_rankings_service.py`; `tests/test_kvk_rankings_browser_view.py` |
| C51 | `kvk/dal/kvk_history_dal.py:135` — `fetch_modern_history_rows_for_governors` | kingdom-only KS4 / v_EXCEL_FOR_KVK_Started + KVKFinalReportHeader → /kvk history service/cards/export | I finalized KS4 history/output headers; no retroactive new source history population | Existing independent owner; no source cache mutation | `tests/test_kvk_history_dal.py`; `tests/test_kvk_history_service.py` |
| C52 | `kvk/dal/kvk_rankings_dal.py:22` — `fetch_hall_of_fame_records` | kingdom-only KS4 / v_EXCEL_FOR_KVK_Started + final header → rankings records/cards/CSV | I finalized KS4 Hall of Fame; no cross-source record ranking | Existing independent owner; no source cache mutation | `tests/test_kvk_rankings_finalized_sql_contract.py`; `tests/test_kvk_rankings_records_view.py` |
| C53 | SQL `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql:1` — `sp_TARGETS_MASTER` | kingdom-only KS4 / ProcConfig + KS4 + target helper outputs → KVK_Target_Publication/Row and target views | I frozen target publication and versioned cache; no B0 target roster replacement; Q only where config import shares provider budget | Existing independent owner; no source cache mutation | `tests/test_kvk_target_publication.py`; `tests/test_kvk_target_cache_repository.py` |
| C54 | `kvk/target_cache_repository.py:1` — `kvk/target_cache_repository.py` | kingdom-only KS4 / v_KVK_TARGETS_FOR_BOT via publication DAL → /kvk targets cards/views | I frozen target publication and versioned cache; no B0 target roster replacement; Q only where config import shares provider budget | Existing independent owner; no source cache mutation | `tests/test_kvk_target_publication.py`; `tests/test_kvk_target_cache_repository.py` |
| C55 | `player_self_service/stats_service.py:427` — `build_personal_stats_payload` | kingdom-only KS4 / personal_stats_dal/usp_GetPersonalStatsDaily → /me stats/Stats views | I daily personal account statistics; no all-kingdom profile or counter admission | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py` |
| C56 | SQL `sql_schema/dbo.vDaily_PlayerExport.View.sql:1` — `vDaily_PlayerExport` | kingdom-only KS4 / KingdomScanData4 + alliance/rally daily views → stats export DAL/CSV/Sheets downloads | I daily SCANORDER export view; Q only shared provider wrapper, not metric migration | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py`; `tests/test_kvk_export_coordination.py` |
| C57 | `player_self_service/governor_dashboard_dal.py:74` — `fetch_governor_dashboard_data` | kingdom-only KS4 / KS4 latest + location/civilization → /me dashboard | I latest daily profile/dashboard; no new-source VIP/profile overwrite | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py` |
| C58 | `leadership_player_review/dal.py:419` — `fetch_kvk_history` | kingdom-only KS4 / usp_GetLeadershipPlayerKvkHistory → /stats player leadership report | I leadership finalized history; source basis labels preserved | Existing independent owner; no source cache mutation | `tests/test_kvk_source_independent_consumers.py` |
| C59 | `stats_alerts/embeds/kingdom_summary.py:379` — `send_kingdom_summary` | kingdom-only KS4 / dbo.KS → standalone kingdom summary | I standalone kingdom daily summary and claim; R fighting embed remains separate adjacent component | Existing independent owner; no source cache mutation | `tests/test_stats_alerts_offseason_flow.py`; `tests/test_stats_alerts_fighting_lifecycle.py` |
| C60 | `daily_KVK_overview_embed.py:30` — `post_or_update_daily_KVK_overview` | calendar / event_cache → daily KVK calendar embed | I calendar/event timing and scheduled message owner; not combat source data | Existing independent owner; no source cache mutation | `tests/test_daily_kvk_overview_lifecycle.py` |
| C61 | `proc_config_import.py:582` — `run_proc_config_import` | shared configuration / KVK LIST named sheet ranges → ProcConfig + KVK Details/Windows/Weights/CampMap | Version desired endpoints via existing S5B hook; bind counterpart confirmation; Q account reads/SQL snapshot admission; no sheet column change | R token/pinned publication; Q job vector where exported | `tests/test_kvk_source_config_hook.py`; `tests/test_kvk_source_config_service.py`; `tests/test_proc_config_import.py` |
| C62 | SQL `sql_schema/KVK.sp_KVK_Ingest_Cleanup.StoredProcedure.sql:1` — `sp_KVK_Ingest_Cleanup` | legacy whole-KVK / Stage/Diagnostics/Negatives → retained diagnostics and cleanup counts | Legacy diagnostics-only cleanup retained; never new pair/input/publication/receipt cleanup owner | Legacy owner unchanged; new route bypasses or gates caller | `tests/test_kvk_all_recompute_sql_contract.py` |
| C63 | `kvk/dal/kvk_lifecycle_dal.py:136` — `fetch_max_scan_order` | shared lifecycle / KS4 max ScanOrder + KVK Details/ProcConfig → kvk_state and seasonal dispatch | I daily lifecycle from KS4 max SCANORDER; new logical scans cannot open/finish daily state | Existing independent owner; no source cache mutation | `tests/test_kvk_lifecycle_dal.py`; `tests/test_stats_alerts_fighting_lifecycle.py` |
| C64 | `kvk/rendering/kvk_rankings_csv.py:82` — `_csv_text_cell` | kingdom-only KS4 / rankings payload → download CSV | I rankings CSV semantics; reuse existing formula-prefix escaping for any human export; preserve numeric type | Existing independent owner; no source cache mutation | `tests/test_kvk_source_exports.py`; `tests/test_kvk_rankings_service.py` |
| C65 | `bot_instance.py:1` — `bot_instance.py` | shared orchestration / startup/background scheduling → stats caches/event overview | I existing startup caches/schedulers; register coordinated recovery without automatic recompute/send; Q durable discovery after restart | Existing independent owner; no source cache mutation | `tests/test_kvk_source_recovery.py`; `tests/test_kvk_export_coordination.py` |

## 10. Indirect callers and resource ownership

| ID | Exact caller chain / current evidence | Required integration and test |
|---|---|---|
| N01 | `DL_bot.py:on_message` now invokes `upload_routes/kvk_source_route.py:handle_configured_kvk_source_upload` before legacy routes | Keep private intake precedence/authorization; both admission DALs check SeasonSource. `tests/test_kvk_source_upload_route.py`, `tests/test_kvk_all_upload_route.py` |
| N02 | `kvk_all_importer.py:_auto_export_kvk` → `gsheet_module.py:run_kvk_proc_exports_with_alerts`; route schedules independent task | Q job ownership replaces detached export execution; notify confirmed completion only. `tests/test_kvk_all_upload_route.py`, `tests/test_kvk_export_coordination.py` |
| N03 | `commands/admin_cmds.py:run_gsheets_export_command` callback → `gsheet_module.py:run_all_exports`; `processing_pipeline.py:execute_processing_pipeline` also calls it through a timeout/thread wrapper | Both manual and automatic scan exports use same durable Q job; timeout cannot release still-running worker. `tests/test_processing_pipeline.py`, `tests/test_kvk_export_coordination.py` |
| N04 | `gsheet_module.py:run_single_export`, `transfer_and_sort`, `run_kvk_export_test` are public/manual compatibility entry points | All provider calls, including test/provisioning wrappers, require registered resource admission; snapshots captured once. `tests/test_gsheet_module.py`, `tests/test_kvk_export_coordination.py` |
| N05 | `stats_alerts/allkingdoms.py:load_allkingdom_blocks` → ordinary reporting; `stats_alerts/embeds/kvk.py:send_kvk_embed` → `build_kvk_preview` without selection | R automatic resolution, missing pair/disabled route explicit; existing public receipt and cap logic remain. `tests/test_kvk_public_routing.py`, `tests/test_stats_alerts_fighting_lifecycle.py` |
| N06 | `commands/kvk_stats_card_posting.py:post_kvk_stats_output` → `build_kvk_stats_card_payload` → context; `ui/views/kvk_stats_card_views.py` holds the rendered payload; `ui/views/kvk_personal_views.py` invokes that posting flow | R ordinary context must not fetch legacy camp when new source unavailable; old views remain labelled/pinned or refresh wholesale. `tests/test_kvk_stats_card_posting.py`, `tests/test_kvk_stats_card_views.py` |
| N07 | `stats_alerts/kvk_diagnostics.py` and `stats_alerts/kvk_diagnostic_sessions.py` persist explicit diagnostic selection | Keep private pinned session/replay contract, add public-token provenance to ordinary-source diagnostics; never make injection a public activation mechanism. `tests/test_kvk_embed_diagnostic_lifecycle.py`, `tests/test_kvk_embed_diagnostics.py` |
| N08 | `kvk/services/new_source_recovery_service.py:RecoveryIntakeAdapter.confirm`, `RecoveryService.run_batch`, `deliver_current_exports`; `bot_instance.py:1786` registers recovery | Pair-aware discovery → complete selection/intent → Q; no direct delivery of every raw SourceSelection; restart recovers pinned intent. `tests/test_kvk_source_recovery.py`, `tests/test_kvk_source_pairs.py` |
| N09 | `proc_config_import.py:run_proc_config_import` → `snapshot_config_import`; `SourceConfigRequest` endpoint chains | Persist counterpart attestation reference with desired update, separate from config authority; account pacing also covers Google config reads. `tests/test_kvk_source_config_hook.py`, `tests/test_kvk_source_pairs.py` |
| N10 | `config/sheet_config.json` supplies 14 local scan export queries: KS, POWER_BY_MONTH, ALL_STATS_FOR_DASHBAORD, STATS_FOR_UPLOAD, RALLY_EXPORT, SUMMARY_CHANGE_EXPORT, ALL_GOVS, ALL_GOVS_NAMES, ALL_GOVS_ALLIANCES, v_TARGETS_FOR_UPLOAD, INACTIVE_GOVERNORS, SCAN_LIST, ROK_TRACKER.dbo.ALL_GOVS, ROK_TRACKER.dbo.v_PlayerAccounts_Migrate | All are independent daily/profile/target/history exports; Q shared provider resources. Two tabs share Governor Names, two share Governors, two share KVK LIST. Register spreadsheet IDs and preserve SCANORDER, not new logical IDs. Local config is read-only evidence, not live parity. `tests/test_kvk_source_independent_consumers.py`, `tests/test_kvk_export_coordination.py` |
| N11 | `kvk/services/kvk_targets_card_service.py:build_kvk_targets_presentation_input` calls `load_kvk_stats_card_context` at line 305; its three result paths copy camp_name into target payload; renderer displays it | R applies to camp context only. Add source/period/stale context label through `kvk/models/kvk_targets_card.py` and `kvk/rendering/kvk_targets_card_renderer.py`; target numbers/cache/roster stay independent. Missing complete context suppresses camp rather than querying legacy. `tests/test_kvk_targets_card_service.py`, `tests/test_kvk_targets_card_renderer.py`, `tests/test_kvk_targets_card_posting.py` |
| N12 | `gsheet_module.py:run_kvk_source_export` directly delegates to `deliver_export`; no current production caller found in tracked Python | Require authorized Q job/epoch at delivery boundary; explicit diagnostic/test composition is not an ordinary bypass. `tests/test_kvk_source_delivery.py`, `tests/test_kvk_export_coordination.py` |

The current caller symbols and view paths above were checked in source. New files are
only the separately enumerated future Creates.

Repository search cannot inventory external SQL clients, deployed export job config,
or other machines sharing an account. Those are explicit S11 parity/admission gates. The bounded
code inventory includes direct wrappers and scheduled/manual callers; no unknown external reader
is declared migrated. All intended deployed consumers must be classified before activation.

## 11. Retained S6 evidence and remaining technical review

Canonical exact results, IDs, SHA-256 hashes, tested revisions and failure JSON remain in
[archived S6 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md),
[release evidence](release_evidence_log.md) and [readiness](release_readiness_and_rollback.md).
These files are preserved byte-for-byte from S7 entry. They are incorporated as evidence,
not replaced by this summary or claimed rerun. S6 ran Bot `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`
and SQL `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, disposable `K98_S6_Disposable_20260912`
on `9SX2VF4\K98DEV` via `lpc:localhost\K98DEV`. All other retained predecessor databases remain.

| Gate | Accepted evidence and exact retained state | Remaining owner/work |
|---|---|---|
| S6-OPS01 | Private-write exit/recovery changed owner/fence 1→2 and quarantined original slots 01–02; original pointer interruption publication `e19c89ac-7977-5f28-ae4c-031807cd1728` remains publication_pending (original slots 05–06); grant interruption `54a2480a-26fb-5bad-a3f5-9321525a731c` remains publication_pending (benchmark slots 05–06); blind retry/private reclaim blocked | S10 implement queue/epoch recovery; S11 exact interruption evidence and operator disposition. Do not repair either retained uncertainty here |
| S6-PERF01 | 5,806 players × ten periods, 17,831,186 logical cells / 17,831,355 physical; two parts; generation load 92.281s, full export/readback 2248.609s, 991 export calls, no recorded HTTP errors; other importers operator-attested idle | S10 prove cross-process admission/pacing/fairness; S11 deployed profile. Normal 1–2/day, peak 2–3/day accepted; no new duration-cap decision |
| S6-CAP01 | Original nine and benchmark seven file IDs/ACLs/receipts in archive; receipt overflow fails before claim/provider, retained-slot refusal after four GETs/no mutation. Large benchmark publication `390dd712-10c4-5cc3-befd-7dbb067e300c`, export hash `eca93ecc70fe04cb836a483fafb65fa17cd0a990730d4ca77e5d55667557b9ea` | S10 normalized part receipts, bounded pool and rollover; S11 actual capacity/ACL/epoch proof; no archive horizon question |

Evidence directory: `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
`benchmark-results.json` SHA-256 `3587bbafc0bc145744c79ff03cb51e119915ad373ec3dd428385051880615e7b`.
These are retained references; S7 did not open credentials, raw workbooks or connect to those targets.
S6's player-only benchmark publications are accepted component evidence, not proof of the new
matched-publication gate. Its successful pointer-ack-loss case is distinct from the unresolved
in-flight pointer case; no exactly-once provider claim follows.

Exact unresolved receipts (historical readback, not a fresh probe):

| Evidence | Pointer interruption | Viewer-grant interruption |
|---|---|---|
| Artifact | `provider-pointer_readback.json` | `benchmark-ops/provider-grant_readback.json` |
| Index ID | `19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g` | `1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY` |
| Part IDs | `1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg`; `1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0` | `1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ`; `1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk` |
| Export key | `e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a` | `c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c` |
| SQL state / phase | claimed / publication_pending | claimed / publication_pending |
| Owner / fence / selection version | `bca05d8c-2fa1-43b2-a036-9905e45150f0` / 4 / 5 | `487a17d9-c64d-4116-9274-143ddffbabb1` / 3 / 1 |
| Observed index still selected | Prior key `78792a5a9782b69ca430cc3a5deeecf5a8e8ff7090dd547cbe533d229c589d56`, fence 2, directory in original slot03 | Prior key `e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a`, fence 2, directory in benchmark slot03 |

Original quarantined IDs remain `1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU`
and `1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw`. Both unresolved cases report
blind_retry_blocked and private_reclaim_blocked. The exact JSON/ACL readbacks and all
artifact hashes remain in the archived pack; no retained file counts as available new capacity.

Only evidenced technical tradeoffs remain for contract review:

1. **Coordinator availability versus scope:** proposed conservative account serialization and
   durable SQL budget are simplest to prove with the three current writers. Per-destination
   concurrent exports could improve latency but need quota/fairness evidence not supplied by S6.
   Recommend serialized account jobs initially; no fixed schedule is proposed.
2. **Legacy snapshot storage:** new-source facts already reload from immutable SQL; legacy
   `transfer_and_sort` reads mutable SQL per tab. Recommend a registered durable spool with
   SQL manifest/owner, plus worker affinity if storage is not shared. Provisioning topology is
   a later environment choice; SQL blobs would increase database/storage and migration scope.
3. **Pool reserve:** recommend one quarantined generation and one spare generation (nine files
   for P=2); more quarantine needs additional approved capacity or blocks progress. S6 proves
   refusal, not a production upper bound. Retained uncertain files never count as free reserve.

These are engineering recommendations for review, not repeated S7-D01–D09 questions.
No unrelated reliability WS1 rewrite is required by this contract. Required extraction of
legacy export snapshot/admission/pacing is a bounded integration dependency, not deferred debt.


## Approved S8C intake and configuration amendment - 2026-09-13

- Support one file then counterpart, two files in one message, and existing grouped-command
  intake with two optional attachments. Either file order is valid; receiving two files is not
  counterpart attestation. Structure supplies a format suggestion; filenames are optional hints.
- Confirm season before durable file receipt. Default to the baseline season (otherwise imported
  setup); allow explicit override before receipt creation. Accepted source/season cannot switch.
- Confirm actual scan-start UTC, reporting coverage/as-of and finality. Never substitute upload
  time or infer counterpart validity from names, order or equal timestamps.
- Missing/invalid imported kingdoms/camps/weights blocks B0 acceptance, retaining the private
  receipt and original. Review imported configuration, Check again, or cancel pending work.
  Initial configuration approval opens the fixed season for matched updates, never public routing.
- Retain valid scans without reporting selection. Scans 15/16 may remain unused after 10-14;
  later assigning 17-18 selects 18-17 using explicit configuration/update authority. Original
  file metadata, facts, IDs and season are unchanged. Configured starts may be unknown initially.
- Approved within-season map/weight/scope corrections create new versions. Original B0 evidence
  bounds eligibility. Player weights affect player DKP/ranking only. Supplied kingdom/camp totals
  and DKP remain authoritative, and overall remains independent. Incompatible aggregates leave
  the previous complete result selected and the configuration pending until compatible evidence.
- Configuration confirmation may explicitly attest displayed retained counterparts. Unattended
  imports persist original decimal tokens and pending desired intent without that attestation.
  The exact sealed update still validates source/season/period/config/roster/coverage and CAS.
- Cancel stops pending work without deleting receipts, accepted revisions, publications or files.
  SQL reviews persist ownership, channel, expiry, payload hash, versions and outcomes across restart.
  A semantic duplicate returns its retained target outcome rather than issuing another selection.
- Export consumes a completed selected result; export execution does not recalculate. S9 routing
  and S10 export coordination remain outside S8C; SourceRouting.Enabled alone is insufficient.

The approved 69-path Bot and separate 6-path SQL unions are recorded in the implementation
manifest. Retain B0, UTC starts, semantic deduplication, no-fight, daily SCANORDER, exact
11-10 / 12-10 / final 13-10 then authorized 14-10, sealed inputs, atomic complete selection and
full-vector intent, and the legacy season-admission lock through recomputation.
