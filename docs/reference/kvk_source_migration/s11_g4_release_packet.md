# S11 G4 release packet — planning revision 1

> **Publication checkpoint — 2026-10-02:** [Bot PR #284](https://github.com/cwatts6/K98-bot-mirror/pull/284) and [SQL PR #91](https://github.com/cwatts6/K98-bot-SQL-Server/pull/91) are authorized, open and ready for review; **leave unmerged**. See the [current PR review checkpoint](s11_g4_pr_review_checkpoint_20261002.md) for final checks, review fixes and source-pin qualifications. This supersedes older draft/publication-pending text. Bounded production inventory remains approved; merge, deployment and activation remain separate.

## Local review accepted; production inventory approved — 2026-10-02

Chris has **accepted and CLOSED the local implementation review** and **APPROVED bounded production inventory and staged rollout preparation**. Follow the [current approval/handoff](s11_g4_production_inventory_handoff_20261002.md), [handover task](../../task_packs/S11%20G4%20Production%20Inventory%20and%20Staged%20Rollout%20-%20Task%20Pack%20-%2020261002.md) and [new chat starter](../../task_packs/S11%20G4%20Production%20Inventory%20-%20Chat%20Starter%20-%2020261002.md). Carry this approval forward without repeating the question. Prepare exact bounded read commands, preserve their hashes/copies, then execute the permitted production reads. Installation, publication/PR, deployment/restart, enrollment/export writes and G5/activation remain separate decisions. Version 5 operator control and the verified five-file pool remain accepted; do not reopen settled choices. Earlier approval/status statements below are dated history, not current stage authority. No production observation was performed for this documentation update.

## Operator-controlled readiness decision — current 2026-10-02 overlay

Read the [current operator-control result and decision packet](s11_g4_operator_control_readiness_20261002.md) first. The operator-approved simpler version 5 model is implemented: Chris controls commands/imports; no remote shutdown/process-session inventory or fixed duration cap is required. The five candidate files (Slots 02–06) passed actual read-only owner/Editor/Viewer/blank-grid checks; proposed roles and protected exclusions are pinned. 644 focused tests passed, one skipped; Changes review completed 21/21 with no findings. This resolves the local source/minimum-file blockers. Actual enrollment, target installation/configuration/process proofs, S6/S8 operational gates, production rollout and G5 remain separate. Historical bodies and seals below are preserved.

## Coordinated Viewer / two-host amendment — current 2026-10-02 overlay

Read the [completed local amendment](s11_g4_coordinated_viewer_custody_amendment_20261002.md) before older R1/R2 source-blocker statements. Coordinated public Viewer preparation/verification/retirement/rollover/recovery and version 4 two-host custody are now implemented and locally tested. Historical private recovery keeps its original policy. The Changes review and final-source pin qualification are retained. Actual seven-proof G4 evidence, fresh pool capacity/targets, production installation/rollout and G5 remain open; no activation follows. Earlier source seals and evidence remain historical.


## Full readiness review — current 2026-10-02 overlay

**Review complete; DO NOT PROMOTE or activate.** Read the [full readiness review](s11_g4_full_readiness_review_20261002.md) before dated readiness statements below. Local calculation and standalone Sheets reuse succeeded, but coordinated public Viewer semantics, two-host custody/writer proof, pool capacity and seven current typed proofs remain unresolved. The initial broad offline run found 16 stale-fixture failures; all were corrected and both affected modules passed (391 tests). Runtime source is unchanged by this review. Separate Bot/SQL security evidence and its SQL coverage qualification are retained. Production and G5 remain unapproved.


## Current development SQL checkpoint — 2026-10-01

Read the [disposable SQL repair and retest checkpoint](s11_g4_disposable_sql_retest_20261001.md) before the dated installation and next-step statements below. The explicitly approved isolated development installation and SQL synthetic rehearsal have now run, encountered guarded failures, been corrected and completed across retained reconciled attempts. The development TrustServerCertificate exception remains connection-local. Production, real exports, the seven complete typed G4 proofs and G5 remain outside this result. All original bodies and seals below remain historical evidence.


## Public Viewer correction — current 2026-09-29 overlay

Read the [public Viewer implementation update](s11_g4_public_viewer_implementation_20260929.md) before older policy/source statements below. The operator explicitly retains anyone-with-link Viewer access. Local manual plan v3 and coordinated SQL correction are implemented, offline-tested and separately reviewed; no installation, registration, export, deployment or activation follows. Private-only initial wording and older source pins below are historical. Existing receipt interpretations, seals and reference/uncertainty protections remain preserved.


## Current S11 checkpoint — 2026-09-29

Read the [current validation handoff](s11_g4_validation_handoff_20260929.md) first and use the [new-chat starter](../../task_packs/S11%20G4%20Controlled%20Validation%20-%20Chat%20Starter%20-%2020260929.md) for the next chat. It supersedes earlier dated S11 next-step, OAuth/fresh-identity, fresh-file and restore-incomplete statements below. Their original bodies remain historical evidence; general engineering/runbook requirements still apply.

The approved single-account/manual-Sheets source implementation and focused local review are complete, pending and unpublished. Chris manually creates Sheets as `chrislos35@gmail.com`; existing `sheets-service@statsupdate.iam.gserviceaccount.com` writes to the registered fixed pool. No human OAuth, automated creation or replacement identity is planned. Equivalent reports and safe referenced/uncertain-output protection remain required.

The 119-set development restore, recovery and clean CHECKDB are evidenced; the selected 15-table baseline covers 2,410,159 rows with its retained provenance qualifications. Keep `S11_G4_Recovery_20260928_97337` read-only/restricted/Broker-disabled. All seven current typed G4 proofs remain incomplete.

Next is local preparation of the exact bounded SQL/provider/two-export validation packet, not execution. Production stays on isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; no main pull, restart, installation, provider call, activation, publication or automatic chat creation. The old window ended 2026-09-29T09:23:23Z; local preparation needs no window. Rollout and G5 remain separate operator decisions.


Current overlay: read the [resumption handoff](s11_g4_resumption_handoff_20260926.md) and [2026-09-29 local manual-registration implementation](s11_g4_manual_pool_implementation_20260929.md) before interpreting this historical packet. Source implementation is local; installation/provider proofs and rollout/G5 approval remain separate.

## INCIDENT HOLD — 2026-09-26

Timeline correction: the operator places collector execution at approximately 06:45.
The supplied production log explicitly records SQL error 701 (insufficient memory in
resource pool `internal`) and 596 at 06:46:54, followed by connection/scheduler failures.
This is confirmed SQL memory failure closely following the reported collector start;
the collector is a suspected trigger/contributor. Exact resource attribution remains
UNRESOLVED. The screenshot filename and later restart do not date incident onset.
See `collector-0645-timeline-correction-20260926.md` in the observation evidence directory.
Earlier reports/seals remain retained; this correction supersedes their incomplete
onset assessment. Collector withdrawal and the live-operation hold remain in force.

Offline follow-up: the operator confirms the Bot has restarted and is working correctly.
Small synthetic serialization cases passed in local Windows PowerShell5.1; the production
failure is not reproduced. The unguarded final serializer and lack of a hard serialization
resource bound are confirmed collector weaknesses. Existing local logs predate the incident.
See `offline-incident-analysis-20260926.md` in the observation evidence directory for exact
test receipts and the bounded production log/event copies still needed. No live access or
replacement collector was attempted; the hold and withdrawal remain in force.

The operator reports a Bot crash/restart during G4-00H-FOLLOWUP. The attached screenshot
shows ConvertTo-Json failure at collector line102 and an SSMS stack-guard error. Root cause
and event ordering remain UNRESOLVED. The collector/helper are WITHDRAWN; do not execute
earlier run instructions below. Live G4 observations and rollout are on hold pending incident
reconciliation. No replacement collector or retry is approved by earlier observation consent.

See `.codex_artifacts/s11-g4-observations-20260925/INCIDENT-20260926-DO-NOT-RUN.md`.
Preserve logs/events, original scripts, seals and all earlier evidence. The reported restart
invalidates process-continuity assumptions; old bindings remain historical and cannot be
automatically adopted for replacement processes. No G4/G5 gate is satisfied by this failed run.

## Next observation prepared — 2026-09-26

The operator approved preparation of G4-00H-FOLLOWUP. Its exact scripts, hashes, effects,
seven named tasks, four pinned PIDs, 60-second budget, redaction and stop rules are documented
in `.codex_artifacts/s11-g4-observations-20260925/next-observation-plan-20260926.md`.
This follow-up has NOT run. It reads task definitions, launcher/base-Python hashes, installed
package metadata and native process/token metadata; it does not deploy or change permissions.
Its receipt will not itself satisfy the seven typed proofs or bind future process incarnations.

The same plan records the next exact ACL/SQL/deployment/backup/actual-restore work items.
Candidate new development database names are K98_S11_G4_20260926_validation and
K98_S11_G4_20260926_restore; both remain UNRESOLVED for disjointness and approval, not
authorized creation targets. Provider access repair and fresh identity/file/pool metadata are
still unresolved. All earlier receipts/seals remain retained; the follow-up preparation seal
binds this revised packet. No new live observation, rollout or G5 occurred in this preparation.

## Operator host observation reconciled — 2026-09-26

G4-00H-DETAILS-OPERATOR completed on MINI_AMD at 04:46:41Z in 2.63 seconds, with no
reported errors. Original receipt `production-host-20260926T044641506Z.json` and the
dated host reconciliation are retained in `.codex_artifacts/s11-g4-observations-20260925/`.
The new `host-observation-seal-20260926.json` binds this packet revision; earlier seals remain
historical. The collector is no longer pending. No deployment or permission changes occurred.

Observed checkout main points to `abfc3845e9f8b78d70f88bada5a76c454ff32cb8` (production
PR#570); sampled S11 runtime files are absent. This is on-disk evidence, not full clean-tree
or running-build proof. Four Python processes form the parent chain
6500 -> 15996 -> 16220 -> 16332 -> 16348, alternating venv and base Python311 executables.
Exact script roles, native tokens and FILETIME bindings remain UNRESOLVED.

Named tasks now include StartDLBotAfterSQL, DLBotLogRotate, K98 SQL Nightly Schema Export,
Graceful DL_Bot Shutdown and Restart daily in Ready state; RUN_Bot and the sampled other-Bot
tasks are Disabled. Exact arguments/triggers and complete effects remain unobserved. They must
be reconciled with the Agent jobs before approving a maintenance window.

The Bot root and sampled files, including .env, allow Authenticated Users Modify access.
This is a concrete protected-path gap. Plan exact ACLs within the approved shared-account
model; no second Windows account is implied and no permission change is authorized by this
finding. The receipt provides partial hashes/ACLs and confirms observer cwatt's SID, but not
complete host_acl/bot_identity proof. All seven typed records, actual restore, rollout and G5
remain incomplete/unapproved. See the dated reconciliation for exact remaining bindings.

## Approved read-only observation addendum — 2026-09-25

The operator subsequently approved runtime verification, including RDP access to MINI_AMD.
Earlier statements below that no observations are authorized or have occurred are historical.
This approval covers metadata observations only; rollout, provisioning, deployment/restart,
backup/actual restore, provider writes, Git publication and G5 remain unapproved.

The exact observation ledger, saved SQL batches/results, unresolved bindings and operator host
collector are in `.codex_artifacts/s11-g4-observations-20260925/observation-report.md` and its
adjacent receipts. The new `observation-seal.json` binds this packet revision and those files;
earlier packet/amendment seals remain retained historical evidence, not hashes of this revision.

Verified production: mini_AMD / ROK_TRACKER, SQL16.0.1200.5, ONLINE/FULL, compatibility160.
The SQL catalog identifies mini_AMD\cwatt's SID as
S-1-5-21-2970367362-111206357-3835881402-1001; this does not prove the live Bot token.
Three Python SQL sessions report PID16348 and SHEETS_USER. That login is db_owner, which the
new restricted application readiness profile rejects. Do not alter its grants during observation.
Both execution roles are absent. Comparing the 538-entry source inventory to observed objects
and table types gives 480 name/type matches and 58 absent entries, including required new-source
and export coordination objects. Presence does not prove installed definitions/shapes. These are
runtime installation/permission gaps, not permission to restart source implementation.

Enabled backup/prune/maintenance jobs are now part of the inventory; two LOG schedules are
enabled (5 and 15 minutes). Backup history identifies C:\SQL_BACKUP\FULL, DIFF and LOG;
actual restore and prune-retention safety remain unproven. All existing databases/files remain
protected. Development SQL observation found 17 retained application databases plus four system
databases; its complete durable file inventory still needs capture. Nothing was created or reused.

All seven proof records remain incomplete. Host hashes/ACLs/native process tokens, fresh identity
and key metadata, provider access/pools, complete writer exclusion/drain, installed SQL contract
and actual restore remain UNRESOLVED. The shared Windows-account decision stands. Automatic
approval review later blocked provider browsing and a further development SQL capture because
its refresh token was revoked; those actions did not execute. No secrets were requested/read.

## Local implementation amendment — 2026-09-25

The operator explicitly approved local implementation of `S11-G4-AMEND-01`. The amendment is
now authored locally; prior proposal-only/no-code-authorization statements below are historical.
No publication, installation, observed runtime inventory, rollout operation or G5 is authorized.
The same-account model trusts the Bot, supervisor and their account together, including access
to credentials/proof evidence. It does not claim the earlier Bot-inaccessible custody boundary.

The new profile is explicit: trust_model `single_account_application_v1`, supervisor manifest
v3, Bot manifest v2, enrollment outer manifest v2, deployment boundary and all seven records v2,
SQL readiness contract v3/profile `application`. Older separate-account contracts remain
separate for compatibility and retained evidence; adding the new trust model to an old version
is rejected. No old observation/session/origin is upgraded or relabelled automatically.

`process_bindings` contains exact `authority` and `bot` descriptors: pid, created_filetime
(Windows creation FILETIME integer), executable absolute path, sha256 and token_profile
(user_sid, sorted group_sids/privileges including disabled capabilities, elevation_type,
elevated, ui_access). The SIDs must match; the PIDs must differ. Both executable/token/process
incarnations are verified through native retained handles, including client recheck after reply
and server recheck after receiving a request. Mismatch/exit/uncertain reply never triggers retry.
The helper `core/export_process_identity.py` is a bounded shared host primitive, reused by client
and supervisor to avoid divergent authentication logic. It does not discover or launch peers.

Operational prerequisite: exact process bindings must be approved for the actual incarnations
before admission. A controlled launch may establish suspended processes, record their identities,
seal their manifests, then resume them under a later exact G4 packet; no such launcher/operation
has run here. Automatic restart cannot adopt a replacement PID/creation time. A new incarnation
requires a fresh approved binding, closed admission and reconciliation of old work. The final
literal startup/service-manager procedure remains UNRESOLVED until the actual deployment target
and service definitions are observed. Native API behavior remains a G4 evidence gate.

The application SQL profile requires ExportExecutionAuthority membership and **no**
ExportExecutionReader membership: authoritative SQL explicitly DENYs evidence EXECUTEs to
the reader role. Effective capability checks are the bounded union of authority and Bot
coordination permissions; reader-role membership is not the union. Sysadmin/db_owner,
CONTROL/ALTER/IMPERSONATE and unexpected object/column grants remain rejected. No SQL source
change is needed for this profile's capability calculation; exact later provisioning grants
and current installed permissions remain separately reviewed and UNRESOLVED. Both processes
must agree on the complete SQL readiness contract fingerprint and principal.

The application schema constant now matches the 538-entry Git-byte manifest in
`deploy/export_application_schema_source.json`, digest
`e9a6a1042de97e4fd4d7902756375f642a5a960354edb4018207ebc806a68b32`.
The old fixed digest is rejected. This fixes the local source-pin inconsistency, not SQL
installation evidence. Prior receipts and all historical source-byte domains remain retained.

Output decisions are settled: a fresh generated link and equivalent reports within the new
output are acceptable; no separate legacy-style derivative workbooks or existing-file adoption.
Enrollment creates files using the admin's separate Google-owner OAuth profile, then grants
the service account Editor access. This requires no extra Windows account and no grant of
creation rights to the service account. No credentials, OAuth setup or provider action occurred.

Focused offline tests cover the new profile, old-version rejection, seven-record versioning,
process/token drift, wrong/recycled peers, handle cleanup, uncertain replies/no replay, exact
SQL permissions and actual Bot factory wiring. Existing drain/cooldown/protocol/enrollment
regressions are included. Final validation/security receipts are recorded separately; this
authored status does not claim that review or live acceptance has passed.

Packet ID: `S11-G4-20260925-P01`. Status: **DRAFT / NOT EXECUTABLE**.
Prepared 2026-09-25. This is the requested plan-development deliverable, not a rollout approval.
Packet/component SHA-256 values are in the accompanying local `packet-seal.json`; the seal
hashes the packet bytes and attachments, avoiding a self-referential hash in this document.
Any revision needs a new seal and affected-operation approval. Approved operation IDs: **none**.
Latest planning direction: **one Windows account unless a significant need for separation is
demonstrated**. The operator confirms export triggers are Bot uploads or Bot commands only,
with either legacy or new-source export selected for a whole KVK. See the single-account
assessment below. Earlier separate-SID requirements describe the merged implementation; they
are not an approved deployment choice after this clarification. No runtime amendment is yet made.
Approver: Chris Watts (operator-owned acceptance); execution operator: Chris Watts (admin),
operator-confirmed. Abort owner, independent evidence reviewer, UTC window/expiry and operational
evidence directory: **UNRESOLVED**. Subsequent operator clarification names Chris Watts (admin)
as evidence reviewer too; no additional person is requested. This is operator self-review,
not independent-person evidence. Reconcile the earlier independent-review checkpoint explicitly
before operation approval; do not label it independently satisfied.

This revision identifies source precisely and prepares the operation/evidence ledger. It cannot
honestly supply literal executable target commands until target facts and separately approved
observations exist. Every unresolved binding below blocks its operation. Approval of this draft
means planning review only; it cannot approve an unresolved command or future discovered target.

## 1. Verified delivery, not runtime inventory

Read-only GitHub PR/tip checks on 2026-09-25 confirmed:

| Delivery | Final head | Merge / current source |
|---|---|---|
| Mirror #282 | `e517d36b64501992f1ecc1c7540473ce8305bd6c` | Merge `de9cc1a1de1442a252fc373086ef12be5d06d349`, 14:32:03Z; regenerated main `a3db2aa2841d7b1fd7ab88fc8688e23fd7917c50` |
| Production #589 | `c12fdc1295a3c73ce5ca97144c26f32e7889c377` | Main `468d975b47d58e648882de2d96f7f81b6d84efb3`, merged 14:32:45Z |
| SQL closeout #90 | `41301d7544248f30b9db2e0e98ec3fa15fe0243e` | Main `4cd1554dc3d063e323f22350c88df1444cd0ed4b`, merged 14:32:10Z |

Final-head checks returned success: mirror governance/publication-policy; production governance,
publication-policy/quality/gitleaks; SQL validation. All three #282 threads and both #589 threads
are resolved, with no next review-thread page. Final-head reviews are COMMENTED, not a fabricated
APPROVED review decision. Their responses and exact remote file records are retained locally.
The initial sandbox credential failure was followed by a successful read-only approved retry.

The supplied #281/#89/#588 anchors remain historical comparison pins. No reset, fetch, checkout,
pull, publication or bot-machine action was needed. Bot and SQL working trees were clean at entry.
The reported absence of bot-machine updates is **operator context**, not verified process/build
inventory. SQL #90 changes only `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`.

Evidence directory in this development workspace:
`C:/discord_file_downloader/.codex_artifacts/s11-g4-plan-20260925/`.
`delivery-proof.json` compares each of the 44 reviewed Bot paths to current mirror and production
blobs, the production base, both SQL documents, and both S10E archive destinations/source absences.
`source-pins.json` pins production Python/dependency sources and authoritative SQL source files.
Remote filenames, statuses, SHA and `previous_filename` are retained in the three `*-files.json`
files and checked individually. No count-only inclusion assertion is sufficient.

The final retained production patch is
`.codex_artifacts/s11-authority-composition/review589-production-final.patch`, SHA-256
`5cba76f916e6e81a9c3e8897a0e60566064b153cb940f3f8321dc37ada209df1`.
The four corrected restored paths are modifications relative to production #588:
`scripts/run_export_authority.py`, `services/export_execution_authority.py`,
`tests/test_export_authority_launcher.py`, `tests/test_export_execution_authority.py`.
Only `tests/test_export_authority_boundaries.py` remains identical to that base.
The initial five-file restoration receipt is historical, not the release hash inventory.

The two exact S10E archive names remain:

| Destination under `docs/task_packs/archive/` | Reviewed blob | Original path under `docs/task_packs/` |
|---|---|---|
| `Codex Chat Starter - KVK Source Migration S10E Export Operator UX and Rollover.md` | `1166324b1329dddf71ea0dd8d36f2ffb94f79870` | Same basename; absent at current merge |
| `Codex Task Pack - KVK Source Migration S10E Export Operator UX and Rollover.md` | `8164fd5b44ca433c3fe351222bcf60f97c6f2a33` | Same basename; absent at current merge |

Original-base source/destination and reviewed rename proofs remain in
`s11_merged_delivery_manifest.json` and `review589-final-proof.json`; archive source blobs need
not equal edited destinations. Nothing is moved or deleted in this planning task.

## 2. Scope and gap classification

S11 implementation/review is complete. Actual callers, closed factories, authority, enrollment,
SQL evidence APIs, trusted proof issuers and all-writer integration exist. No missing composition
is established. A bounded source-inventory mismatch is identified below; it is not merely
unproven runtime. No refactor, helper or runtime test
change is proposed. Services/DAL retain policy/persistence; commands/views retain authorization
and interaction presentation. S7 design and EndScanID decisions remain settled.

| Gap | Classification | Resolution boundary |
|---|---|---|
| Fixed application-schema source digest predates three delivered SQL procedure corrections | Confirmed source-pin inconsistency; release-manifest blocker | Reconcile exact source inventory/hash contract in separately scoped work before operational manifest approval; no code change authorized here |
| Host/accounts/paths, manifests, identity, service definition, dependency artifact | Configuration/provisioning prerequisites | Named operator facts, then separately approved observations/provisioning |
| Installed SQL bodies/roles/signatures/shapes, transaction/restore results | Unproven runtime | G4-00S, G4-01, G4-02; never infer from source |
| Windows containment/key custody/provider finality/retirement/Discord | Unproven runtime | G4-03 through G4-06 |
| Exact fault injection driver for some native/provider cases | Operation-packet preparation gap | Pin an inert reviewed case driver before approval; do not invent a CLI or weaken gates |
| Observed incompatibility or absent required source discovered later | Potential genuine implementation gap | Stop, document exact evidence and separately scope implementation; no automatic S11 restart |

Local planning Markdown/JSON and the Git-only evidence helper have no application execution,
config, permission, dependency or deployment effect. Security routing: documented skip for this
planning delta; SQL has no change. A later actual runtime/deployment/config delta requires
**Changes, Deep off**, exact immutable Bot target, and separately assessed actual SQL deltas.
Prior source review is retained, not rerun as a repository/deep scan. No predecessor test rerun.

## 3. Target and custody register

Operator clarification: there is **one production Bot and no test Bot**. Local SQL is
`localhost\K98DEV`; existing disposable databases are retained, and a new database may be
planned if needed. This is permission to develop that plan, not to create it. Use established
paths. No new Bot/application registration or test-Bot deployment is in this packet.

### Operator target clarification — 2026-09-25

The operator confirms no deployment to production SQL or production Bot; merges and local pulls
are complete. This is an operator report, not an independently observed installed inventory.
The authority is intended to use the current production Bot host and account. Same-host placement
is compatible with the approved design. Sharing the Windows account with the running Bot is
**not a valid release binding**: `core/export_execution_host.py` rejects equal authority/Bot SIDs,
and `services/export_runtime_composition.py` enforces that distinction in the client. Exact
account/SID placement remains UNRESOLVED until clarified; no account change is performed or
authorized here. The plan must retain a separate nonprivileged Bot identity and authority-private
fresh credentials; the historical account name is not proof of its current token or privileges.

The intended future production `.env` entry is `KVK_DATA_CHANNEL=1549003662024642632`.
This value is operator-supplied, not installed or independently observed. Guild, actor and
admin-role IDs remain UNRESOLVED. No `.env` file was changed by this planning update.

The operator supplied output spreadsheet file ID
`1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0` and grid ID `1683673174`, parsed directly
from the supplied URL without opening it. The operator reports that the sheets service has
Editor access. Exact grantee, owner, permissions and intended output mapping remain unobserved.
Treat this existing file as a protected named output: no clear, adoption as a fresh pool slot,
test mutation or enrollment follows from supplying its link. Its role (legacy destination,
stable index or another output) remains UNRESOLVED; new pool origins and disjoint test resources
must still satisfy the approved enrollment contract. Reported Editor access does not establish
the fresh authority-exclusive custody boundary or authorize changing current sharing.

Rollout operator and evidence reviewer are Chris Watts (admin), per subsequent clarification;
abort owner remains UNRESOLVED. These target facts authorize planning updates only; approved
operation IDs stay empty.

### Legacy export comparison and clarified destination

The operator subsequently identifies the supplied file as the **proposed destination for the
new-source KVK output**, alongside the existing KVK_ALL export, not its replacement. Preserve
the existing export/destination. The earlier question about this file's intended business role
is answered; its physical registration/index/part mapping is still UNRESOLVED. This does not
authorize adopting a pre-existing file into a fresh-origin pool or changing its sharing.

Local source review confirms the legacy path: successful upload processing schedules
`kvk_all_importer._auto_export_kvk`; without the coordinated runtime it invokes
`run_kvk_proc_exports_with_alerts` through `run_blocking_in_thread`. The renderer calls
`KVK.sp_KVK_Get_Exports @KVK_NO`, binds its ten named result sets, opens the configured
`KVK_SHEET_NAME` (runner default `KVK LIST`), and creates/clears/writes/formats/sorts its tabs.
The authoritative SQL definition is `sql_schema/KVK.sp_KVK_Get_Exports.StoredProcedure.sql`.
`gsheet_module.get_gsheet_client` directly loads the service-account file and authorizes gspread;
this legacy path does not switch Windows identities or require a separate authority SID.
This is source evidence, not a claim that the current Bot-machine bytes were observed.

The ten sections are `KVK_Scan_Log`, `KVK_Windows`, `KVK_DKP_Weights`,
`KVK_Player_Windowed`, `KVK_Kingdom_Windowed`, `KVK_Camp_Windowed`, `KVK_Player_Full`,
`KVK_Kingdom_Full`, `KVK_Camp_Full`, and `KVK_Ingest_Negatives`. The alerting wrapper also
invokes additional period/aggregate spreadsheet exports when data exists. These are distinct
from the generic daily sheet_config exports. The new-source generation uses the same ten
section names and adds `ALL_WINDOWS` and `COMPARISONS`; its values, provenance, availability
states and separate overall aggregate follow the new-source contract, not legacy recomputation.
Logical section parity does not prove identical columns, layout or physical file arrangement.

The merged coordinated branch queues `all_kvk` rather than using the direct legacy path.
S11 introduces the distinct Bot/authority SID checks and fresh exclusive credential custody.
The operator explicitly wants the same Windows account for both. Record that as a conflict
with the authored S11 execution contract, not a requirement of the historical KVK_ALL export.
Changing it requires a bounded design assessment of custody, writer exclusion, delayed effects
and retirement proofs; no bypass, account provisioning or source change is authorized by this
comparison. Existing all-writer invariants remain in force while this conflict is unresolved.

### Single-account assessment — operator direction, 2026-09-25

**Scope and recommendation.** Prefer one Windows account on MINI_AMD for the Bot and supervised
export component. Operator-reported triggers are uploads or Bot commands; there is no reported
external export launcher. Legacy KVK_ALL and new-source export are mutually exclusive for a
whole KVK, with distinct retained destinations. This reduces expected overlap but does not
eliminate overlapping commands, queued requests, daily work or work surviving cancellation.
Inventory observations remain separately approved. Do not infer that daily/configuration writer
families disappeared merely because only one KVK source is selected.

No functional requirement to calculate or publish equivalent KVK reports establishes a need
for a second Windows account. There is a significant *security-property* difference: the merged
S11 design excludes the Bot from authority credentials, private proof evidence and authority SQL
capabilities. Under one ordinary shared Windows identity those become part of the same trusted
application boundary. This assessment recommends the simpler deployment direction, but does not
claim equivalent isolation, accepted residual risk or rollout readiness. Admin-authorized input
does not itself prove that application code cannot fail or a previously dispatched call stopped.

**Proposed architecture, not implementation authorization.** Keep the supervised provider worker
and durable coordinator. Treat Bot, coordinator and export worker under the shared account as one
trusted application. Worker separation remains useful for bounded lifetimes, retained handles,
drain and failure accounting; it is not an independent security identity. Preserve the frozen
capture/spool/provenance and fixed proof producers; do not let commands submit arbitrary proof
JSON or caller-supplied termination Booleans. No direct legacy credential fallback when coordinated
mode is enabled. Do not replace the executor with untracked thread calls just to match the older
deployment. A dedicated fresh provider identity on the production machine remains useful for
excluding the historical copied key; it must be described as application custody, not custody
inaccessible to the Bot. Reuse of the copied legacy key is not approved by one-account preference.

| Property | Single-account design disposition | Source dependency / required assessment |
|---|---|---|
| Admin/guild/channel authorization and one fixed source per KVK | Preserve; enforce at durable final action, including commands and restart | Upload routes, command services and source contracts; no source switching by merely changing a channel |
| Queue, immutable A, eligible pending coalescing, daily ordering/fairness, registration-aware intents | Preserve unchanged | Coordination service/DAL; selection per KVK is not a global writer lock |
| Exact request ownership/fence/version, append-only evidence, complete S10C spool/nested ownership | Preserve | Evidence/coordination DAL and authoritative SQL; no fabricated terminal state |
| Provider child termination, no delayed effects, cooldown and no blind retry | Preserve; unknown stays reconciliation even after local child exits | Job Object/retained handle containment, request journal, fixed proof replay, finality checks |
| Fresh credential and retained evidence inaccessible to the Bot | Cannot claim under ordinary shared account; explicitly replace with trusted-application custody assumption | DeploymentBoundary distinct SID, token validation, credential_holders record, private ACL and PrivateEvidenceStore/DPAPI |
| Pipe peer represents an independently trusted authority | SID alone cannot distinguish shared-account processes; pin intended process incarnation and startup relationship | create_private_pipe access mask, authenticated_server, authenticated_peer and client readiness; do not merely permit equal SIDs |
| Restricted SQL reader versus proof issuer | SQL roles remain useful, but shared Windows authentication does not isolate the two processes | ExportExecutionAuthority/ExportExecutionReader grants and caller contracts; assess exact principal design, never broaden grants to make startup pass |
| Seven observations | Retain seven evidence topics; version their meanings for the new trust model | host_acl, bot_identity, identity_issuance, key_inventory, file_access, writer_drain, sql_installation; never pass old exclusive-custody schema using relabelled observations |
| Retirement and reuse | Preserve all proof prerequisites; no automatic relaxation | All-writer coverage, reconciled dispatched outcomes, old-writer termination, private clear/readback, explicit interrupted journal recovery |
| Human review | Chris Watts performs operation review and G5 decision | Separate recorded approval checkpoints, not independent-person review; no second human is requested |

**Affected source scope.** Host/ACL/token/pipe/evidence mechanics belong in
`core/export_execution_host.py`; manifest/client/readiness changes belong in
`services/export_runtime_composition.py`; launcher definitions in `scripts/run_export_authority.py`
and `scripts/enroll_export_output_pool.py`; fixed proof/custody claims in
`services/export_execution_authority.py` and the retirement/rollover evidence services. Assess
protocol/manifest versioning and source pins together. Worker supervision and process identity
checks remain, with exact same-account semantics reviewed. Do not invent a new framework, add
SQL to commands/views, rewrite report calculations or reopen all prior S11 implementation.

**SQL scope.** Read-only inspection of authoritative
`migrations/20260924_001_export_execution_evidence.sql` confirms separate authority/reader roles,
role-checked evidence procedures and restricted direct table mutation. One Windows account does
not by itself prove that tables or CAS procedures need changing. The effective-principal and
permission/readiness contract does require assessment. SQL delta: **UNRESOLVED**, not assumed
zero and not permission to edit SQL. Separate connection credentials would not constitute an
independent security boundary if both are accessible to the same trusted application account.
Retain separate SQL repository review for any actual delta and the known three-file source-pin
reconciliation blocker independently of this account decision.

**Validation plan after explicit implementation approval.** Select focused host, runtime
composition, launcher, authority boundary, protocol and SQL permission tests for changed checks.
Cover exact shared-account process authentication, wrong-process rejection, old manifest rejection,
no direct provider bypass in coordinated mode, captured source selection, complete/incomplete drain,
lost acknowledgment, shared 429/503 cooldown, retained nested ownership and retirement uncertainty.
Retain existing valid evidence; do not rerun predecessors wholesale. Actual native/SQL/provider
cases still require exact approved operation IDs, disjoint targets, backup/actual restore and
budgets. Offline checks cannot prove installed permissions or no delayed provider effects.

**Security routing and approval.** This assessment edits planning Markdown only: documented scan
skip, no runtime/config/permission effect. A future bounded implementation requires Changes,
Deep off on its exact Bot patch and separate assessment of actual SQL deltas. No vulnerability
discovery or full-repository scan is requested. User approval establishes the single-account
planning preference; it does not authorize removing guards, changing permissions or accepting
weaker evidence. Next deliverable is the exact versioned contract/source-change proposal and
residual trust assumptions for review. Only after that review may separately authorized code
changes be made; G4 execution and G5 remain later approvals. No new target facts are needed
from the operator for this local assessment.

Repository recovery supplies these candidate bindings without asking the operator to repeat them:

| Fact | Source and classification |
|---|---|
| Bot host `MINI_AMD`; historical Bot account `MINI_AMD\cwatt` | Production `scripts/Configure-Phase51ImmutableHandoffAcl.ps1` and SQL Phase 5.1 evidence; historical target, current SID/token unobserved |
| Production SQL `MINI_AMD` / `ROK_TRACKER` | **Operator confirmed in this planning task**; Windows authentication is repository guidance and `NT SERVICE\MSSQLSERVER` is historical service evidence; no current installation/privilege attestation |
| Bot root `C:\discord_file_downloader`; Bot interpreter `C:\discord_file_downloader\venv\Scripts\python.exe`; watchdog `run_bot.py`, child `DL_bot.py` | Production runbook and watchdog source; scheduled-task/service name still UNRESOLVED |
| Existing application data/logs/downloads | `C:\discord_file_downloader\data`, `logs`, `downloads`; constants define them relative to source root; preserve their contents |
| Existing lock/queue/shutdown files | `logs\WATCHDOG_LOCK.json`, `logs\BOT_LOCK.json`, `data\live_queue_cache.json` (environment override possible), `logs\last_shutdown_info.json`; observation only, never delete as a planning shortcut |
| Production backup landing path `C:\sql_backup` | SQL promotion guide/deploy default; capacity/SQL ACL/current override must be observed |
| Local K98DEV backup path `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\Backup` | Retained S8A execution record; retain every existing backup, use a new filename only after approved absence check |
| Local development identity `9SX2VF4\K98DEV` / alias `localhost\K98DEV` | Retained S6/S8 evidence plus current operator alias confirmation; current server identity/version is not independently observed |
| Earlier local intake evidence `C:\K98-S8C-Smoke\20260913` | Retained S8C evidence; protected predecessor directory, not a new G4 output location |

Pinned production `.env2` contains masked/example Discord values and a `LAPTOP-CC7BAMBQ` SQL
value; `.env.example` is a template. Neither is accepted as current runtime configuration.
Production `config/sheet_config.json` contains spreadsheet titles/tab labels rather than physical
file/grid IDs; resolve them only through separately approved provider observations. Its Git-byte
SHA-256 is `efc7b247edd34d3adc6a0e40e6d2c2306f2ddf535ab6c74a362e602394899722`.
`repository-target-facts.json` retains the bounded nonsecret extraction; credentials were not output.

Proposed ordinary test database names, on the already reported `localhost\K98DEV`, are
`K98_S11_Disposable_20260925_evidence` and `K98_S11_Disposable_20260925_evidence_restore`.
These are **new proposed names**, not assertions that they exist or are unused. No existing
database will be reused. Proposed backup filename in the established K98DEV backup folder:
`K98_S11_Disposable_20260925_evidence_pre_g4.bak`. Logical file names/data/log paths remain
UNRESOLVED until the approved observation/FILELISTONLY packet. The separate legacy instance
requirement cannot be met by renaming an existing retained database; provisioning that instance
or choosing an already existing isolated compatible instance needs a later exact decision.

New authority custody/spool/journal paths cannot simply inherit the historical shared-key or
application-data ACL. Their exact protected subpaths and owner remain UNRESOLVED; existing
roots guide placement without pretending exclusive custody already exists.

The following are labels, **not invented target names**. Unknown values remain UNRESOLVED.

| Target label | Exact binding required | Current status |
|---|---|---|
| T-HOST | Bot/authority machine hostname/FQDN, OS build, local deployment root | Repository candidate MINI_AMD / C:\discord_file_downloader above; live identity/OS unobserved; one authority on production Bot machine |
| T-DEV | Development hostname and exclusion from new credentials/runtime | UNRESOLVED; workspace path is not machine inventory |
| T-BOT | Windows account/SID, token groups/privileges, SQL login/user, watchdog/task and child incarnation | Historical MINI_AMD\cwatt; current token/SID UNRESOLVED; must be nonprivileged and different from authority |
| T-AUTH | Authority account/SID, service/task name/type, executable/working directory, restart policy, process/boot IDs | Operator intends current production host/account; same-account Bot/authority binding conflicts with distinct-SID contract, final placement UNRESOLVED; no automatic failover or Bot-launched authority |
| T-ADMIN | Trusted Windows, SQL, provider admins and maintenance freeze/custodians | UNRESOLVED |
| T-SQL | Production instance/network identity, database, SQL service SID, login/users/default schema | Operator-confirmed MINI_AMD / ROK_TRACKER; service SID/login/current catalog observation UNRESOLVED; legacy source requires SQL Server 2022 major 16 and dbo resolution |
| T-SQL-META | Version/compatibility/collation, complete application/dynamic objects, migration receipts, signatures, privileges | UNRESOLVED until reviewed observations; no auto-learning expected hashes |
| T-EVIDENCE-DB | Two proposed names above on operator-reported localhost\K98DEV | Absence/isolation UNRESOLVED; both must be disjoint from all retained databases |
| T-LEGACY-INSTANCE | Separate instance containing `K98_S11_Disposable_` in its exact name, database `ROK_TRACKER` | UNRESOLVED; isolated from production and ordinary evidence fixture |
| T-RESTORE | Backup source, COPY_ONLY/CHECKSUM choice, backup filename, hash/owner; new restore name and every physical file | UNRESOLVED; no WITH REPLACE, retained-file overwrite or VERIFYONLY substitute |
| T-STORAGE | Spool, DPAPI evidence/origins, retirement journal, receipts, config/manifests, backups, logs | UNRESOLVED absolute paths, owner/ACL/capacity/recovery custodian; durable and outside Git |
| T-PROVIDER | Google project/account, fresh service-account email/client identity, owner/admin, IAM issuers/impersonators | UNRESOLVED; historical copied key is ineligible for new custody proof |
| T-ENROLL | Owner email, OAuth client/project, consent scope, protected credential reference and creation-plan ID | UNRESOLVED; separate human authorized_user profile, exact `drive.file` scope |
| T-POOL | Pool/account/epoch, registration hash, index and slot file IDs, all grid IDs, aliases, owners/editor/viewer ACL | UNRESOLVED; new origins only, no adoption of S6 retained files |
| T-LEGACY-FILES | all_kvk, scan_data, configuration files/grids/query mapping and aliases | Operator-supplied output file `1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0`, grid `1683673174`; exact role/aliases and remaining IDs UNRESOLVED; preserve this existing file |
| T-DISCORD | Production Bot only: guild/channel/actor/admin-role IDs, command/version, attachments/hashes | Intended KVK_DATA_CHANNEL `1549003662024642632`; remaining bindings UNRESOLVED; no test Bot; synthetic historical IDs 10/20/30 and masked/example .env2 values are not targets |
| T-CASES | Disjoint KVKs/source/period/start/end/UpdateIDs, job/request/stream/preparation/operation/repair IDs | UNRESOLVED; preserve originals, authorize each mutation scope |
| T-BUDGET | Wall-clock/lock/transaction/drain/request/byte/cell/disk budgets, window/expiry, retention | UNRESOLVED; source constants below are not operational approval |

Known context is preserved without repeated product questions: external exports are manually
uploaded by an admin; imports are upload-triggered. No other jobs/manual writers/instances were
reported. Outputs are not edited after upload; players have anyone-with-link Viewer access.
The historical `sheets-service@statsupdate.iam.gserviceaccount.com` key exists on both machines.
Never request key bytes, tokens, passwords or private signing keys. Ask only for nonsecret identity,
path/reference and target facts. Confirm actual inventory only in approved observation operations.

Fresh custody sequence: approve identity/issuers and narrow scope → issue directly into authority
private custody → observe all key IDs/issuance and impersonation capabilities → prove Bot/dev
cannot read/use it → grant only enumerated files → exclude old writers/old identity from S11
files → review records. Creation is not proof of exclusive custody. Do not revoke an old key or
remove access to unrelated retained files as an incidental step. Each changed ACL/key revocation
needs its own exact target/effect/recovery entry. Enrollment is a different protected credential
profile and cannot substitute a service account or broader/cached credentials.

## 3A. Concrete bounded amendment proposal — review required

Proposal ID: `S11-G4-AMEND-01`. State: **LOCAL DESIGN / NO IMPLEMENTATION APPROVAL**.
This supersedes the earlier plan to require two Windows accounts, but does not change merged
source or certify the replacement. Scope is the shared-account execution contract and stale
application-source pin. Output-file adoption is a separate decision below; no implicit expansion.

### Proposed contract changes

1. Use normal supervisor manifest v3, Bot manifest v2, enrollment outer manifest v2 and deployment
   boundary v2 for an explicit `trust_model: single_account_application_v1`. Keep the existing
   `authority_sid` and `bot_sid` bindings but require equality to the observed configured SID for
   this profile. Reject earlier manifests in this new profile rather than silently upgrading them.
   Historical manifest readers/evidence must remain available for retained records; old sessions,
   origins and proofs must never be relabelled as the new model. Unrelated provider request
   protocol/owner/fence/version semantics do not change merely because the outer profile changes.
2. Keep the separately supervised export process and its provider-child Job Objects, retained
   handles, deadlines and fixed proof selectors. One account does not require one process.
   Keep operator-provisioned startup; the Bot must not opportunistically start a replacement
   supervisor after a failed request. A restart requires closed admission and prior-session
   reconciliation. No implementation change to report calculations or import routes is proposed.
3. Replace SID-only server distinction with an exact supervisor-incarnation binding: deployment
   ID/hash, executable path/hash, process creation time and retained process handle. Bind the
   caller incarnation too. PID alone is insufficient. Record the descriptor at approved startup;
   new process identity requires an explicit new binding, never rediscovery/adoption after an
   uncertain request. Check both peers and liveness before send, retaining the authenticated handle
   through the response. The same-account pipe ACL must use a single canonical ACE per SID.
   This prevents accidental/stale-peer use within the trusted application; it does not claim
   resistance to hostile code already executing with that account's powers.
4. Keep path/reparse/source-hash checks, encrypted evidence and immutable byte receipts. Describe
   their protection against other accounts and accidental drift accurately; do not describe them
   as inaccessible or independently authenticated against the Bot. Version all seven observation
   records to bind the trust model. `bot_identity` records the actual token/profile and approved
   privileges; `key_inventory` records application custody and excludes development/other hosts.
   A privileged actual account is not silently certified as restricted: its exact observed profile
   and expanded trust assumption need review before a runtime target is approved. No assertion
   that the current account is privileged or nonprivileged is made here.
5. Keep a fresh production-only Google identity/key to separate the new application boundary
   from the historical key copied to both machines. Keep named provider issuers/admins, sole
   intended editor, protected paths and old-writer exclusion. This does not require another
   Windows account. Fresh key creation/sharing/revocation remain separately approved operations.
6. For the one-account Windows-integrated SQL model, propose SQL readiness contract v3/profile
   `application`. Its bounded permission map is the explicit union of current authority and
   reader capabilities: SELECT where already specified, BOT_COORDINATION_WRITES plus
   AUTHORITY_COORDINATION_WRITES, and the existing authority procedure EXECUTEs. All other
   checked capabilities remain denied. Both processes must identify the same exact SQL
   principal, with matching full application/legacy permission contracts. No db_owner/sysadmin
   or blanket GRANT workaround. The Bot will be technically capable of authority procedure
   calls under this model; fixed application call paths, CAS and journals remain, but independent
   Bot-versus-issuer permission isolation is no longer claimed.
7. Retain existing SQL evidence table constraints, append-only procedure rules and exact CAS.
   No table/procedure rewrite is presently established. Provisioning must separately enumerate
   the minimal role memberships/grants for the new permission map; current installed permissions
   are UNRESOLVED. If the existing procedure/legacy permission rules cannot support the exact
   profile, stop and produce a separately scoped SQL delta. Role grants are live changes even
   when no schema migration is needed. Do not infer a migration from the proposed version number.

### Implementation boundary and verification

| Change unit | Exact candidate paths | Required focused validation |
|---|---|---|
| Shared identity, process peer binding and evidence semantics | core/export_execution_host.py; services/export_runtime_composition.py; scripts/run_export_authority.py; scripts/enroll_export_output_pool.py | Same-account accepted only in explicit profile; wrong SID/process/time/hash rejected; peer exit/PID reuse; conflicting/old manifests; no request replay |
| Permission map and source digest | services/export_execution_dal.py; services/export_runtime_composition.py | Exact union, extra grant denied, metadata incomplete rejected; stale source inventory rejected; own producer connection checked before writes |
| Proof and child integration | services/export_execution_authority.py; scripts/run_export_provider_child.py, only where new profile reaches these paths | Retained handles; fixed selectors; incomplete drain status 1/session retained; uncertain open/close; nested ownership; no caller-authored proof |
| Regression tests | tests/test_export_execution_host.py; tests/test_export_runtime_composition.py; tests/test_export_authority_launcher.py; tests/test_export_authority_boundaries.py; tests/test_export_execution_authority.py; tests/test_export_execution_sql_integration.py | Focused changed-profile tests plus preserved drain/cooldown/CAS cases; live-marked tests remain disabled until separately approved |
| Contract documentation | S7 contract/manifests, this packet, S11 handoff and applicable environment/startup/shutdown references | No stale assertion of Bot-inaccessible custody or independent-person review; all preserved evidence remains linked |

These are an allowed scope proposal, not a promise that every listed file needs edits. Any extra
runtime path or SQL object must have a concrete dependency justification before extending it.
Do not change the generation/selection algorithms, add scheduled exports, relax command/admin
authorization, drop observations, alter 8/16 or 9,000,000-cell bounds, or weaken retirement proofs.
Changes security review (Deep off) must evaluate the actual patch's new shared trust boundary.
Existing raw evidence remains historical; it cannot prove the new profile. Before implementation
approval, review the lost isolation claims, the SQL capability union and exact process binding.
No permission to publish a PR or execute any G4 operation follows from approving this proposal.

## 3B. Source-pin reconciliation result — candidate only

A complete 538-entry candidate inventory has been generated using exact Git blobs from SQL
`4cd1554dc3d063e323f22350c88df1444cd0ed4b`, retaining the prior inventory's object identities and
list order. Canonical digest:
`e9a6a1042de97e4fd4d7902756375f642a5a960354edb4018207ebc806a68b32`.
Artifacts in the packet evidence directory: `application-schema-source-candidate.json`,
`application-source-candidate-blobs.json`, `application-source-candidate-review.json` and the
Git-only builder `prepare_source_candidate.py`. The original inventory is untouched.

Comparison to the retained hashes: 8 exact Git-byte matches, 527 line-ending-only differences,
3 actual content changes (SessionTransition, StreamTransition, OutputEnrollmentTransition).
This differs from the earlier local-working-tree comparison (527 raw matches/8 line-ending-only)
because the hash domain is now explicitly Git bytes. No SQL files were normalized or edited.
The proposed Bot constant change is from
`0fcc6360f17cc6017801b074117b6b7d6fb8ebb0bd808d686971511b350a27d2` to the candidate above,
with an exact retained source manifest and a regression rejecting the old inventory. Review
the hash-domain change explicitly; deployment/raw-file hashes remain separate and must not be
silently treated as equal. If later approved SQL content changes, regenerate/review the candidate.
The candidate is not installed metadata or permission evidence. Current Bot source still rejects
it: **reconciliation is prepared; the release blocker is not fixed until the reviewed code change**.

## 3C. Output parity and physical destination decision

**Operator decision — 2026-09-25:** A newly generated player-facing link is acceptable;
equivalent reports within the new output are sufficient. Separate legacy-style derivative
spreadsheets and adoption of the supplied existing file are not required. These decisions
resolve the two product choices described below; earlier questions are retained as rationale.
The supplied existing file stays untouched and outside the new pool. Exact new index/slot/grid
IDs will come only from later approved creation receipts, never guessed in this planning packet.

**Creation identity clarified from source:** The authored enrollment uses a separate human-owner
OAuth `authorized_user` credential with exactly `https://www.googleapis.com/auth/drive.file`.
The enrollment runner creates private files as that owner, grants the named service account
Editor access, and records original creation and private blank-file verification evidence.
Ordinary exports use the service-account credential. This flow does not depend on granting
file-creation rights to the service account and does not require another Windows account.
It is not a request to manually create files in the browser: such files lack the runner's
required creation-origin records. Do not create them now. A later approved enrollment operation
must bind owner email, OAuth client/project, protected credential reference, exact file count,
source/manifest/plan hashes, budgets and effects. No OAuth token or key bytes should be sent
in chat. Actual owner consent, Google permissions/quota and credential availability are
UNRESOLVED until separately approved setup/observations. Source references are
`scripts/enroll_export_output_pool.py`, `services/export_enrollment_service.py`,
`services/export_runtime_composition.py:enrollment_profile` and
`scripts/run_export_provider_child.py:provider_credentials`.

Confirmed product intent: the supplied spreadsheet is the proposed **new-source KVK destination**;
legacy KVK_ALL remains available for seasons selecting that source. Preserve both independently.

| Report family | Legacy KVK_ALL | Current new-source generation |
|---|---|---|
| Import context | KVK_Scan_Log, KVK_Windows, KVK_DKP_Weights | Same section names with source/endpoint/UpdateID context and availability semantics |
| Window results | KVK_Player_Windowed, KVK_Kingdom_Windowed, KVK_Camp_Windowed | Same section names; new-source facts and supplied aggregates, not legacy SQL recomputation |
| Overall results | KVK_Player_Full, KVK_Kingdom_Full, KVK_Camp_Full | Same section names; separate overall aggregate; not_received until available |
| Diagnostics | KVK_Ingest_Negatives | Same name with explicit exceptional/unavailable fact status; not identical legacy schema |
| Additional views | Separate Pass4, 1st/2nd/3rd Altar, Pass7/8, Great Zig and Pass9 spreadsheets, with per-period/cumulative tabs when data exists | ALL_WINDOWS and COMPARISONS logical tables; source marks comparisons side_by_side_only; identical legacy derivative workbook presentation is not established |
| Publication | Configured primary spreadsheet plus derivative spreadsheets updated in place | Stable index points to a completed generation; private staging and bounded result-part files, DIRECTORY links and generation-specific grids |

Source anchors: gsheet_module.py run_kvk_proc_exports/create_additional_kvk_spreadsheets;
kvk/services/kvk_export_service.py section specs; kvk/services/new_source_export_service.py
generation/compaction/layout/GoogleSheetsTransport; authoritative KVK.sp_KVK_Get_Exports.
No report-parity test or live comparison has been executed in this planning review.

The supplied existing file `1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0`, grid `1683673174`,
cannot currently be declared a valid index or slot: S11 enrollment requires a recorded original
creation and complete private blank-file evidence (`services/export_enrollment_service.py`).
Reported Editor sharing and an empty-looking file would not satisfy that contract. Also, one
fixed grid ID does not bind all generation grids: the exporter creates generation-specific tabs.

Recommended least-change physical plan: a freshly enrolled stable index and bounded part pool,
with the supplied file retained untouched as the requested destination reference until the
operator decides whether a new player-facing link is acceptable. If retaining that exact link
is mandatory, scope a separate existing-file/index enrollment design with observed ownership,
writers, history, backups and explicit adoption evidence; do not fabricate a creation origin or
quietly clear the file. Do not add an automatic redirect or write a link into it during planning.
Exact legacy-style derivative workbook presentation likewise requires explicit parity scope,
not an inference from matching section names. These two product choices need operator input.

## 3D. Observation packet completion and approval boundaries

The literal read-only G4-00S-ID-PROD, G4-00S-NAMES-DEV and G4-00H-BASE statements in section 7
remain the first proposed observations; none has run. Chris Watts is operator and reviewer.
Targets are MINI_AMD/ROK_TRACKER, `localhost\K98DEV`/master and the existing Bot root respectively.
Proposed per-operation limits remain one invocation, 5-second SQL connection/30-second query,
60-second host command deadline, no retry. SQL metadata visibility failure is a failed observation,
not authority to grant access. No business query, credential read, provider call or process control.

Before approval, bind actual observer account, execution host, exact sqlcmd/PowerShell tool paths
and hashes, output location, UTC window/expiry and abort owner. These values remain UNRESOLVED;
the printed commands cannot be approved as an unattended batch. Identify tool/output paths from
operator-known installation facts or an explicitly approved preliminary metadata-only observation.
Do not ask the operator to discover them by unapproved live inspection.

Second observation revision must enumerate exact Bot/supervisor process and scheduled-task
identities, actual token/profile, metadata-only ACLs, dependency versions/hashes and read-only
SQL metadata/permission statements derived from the selected v3 profile. Expected metadata and
permissions must be reviewed independently of the observations; never learn and approve the
same live values automatically. Provider observations remain a separate exact allowlist packet,
limited initially to the supplied file and subsequently approved identity/resources. No provider
request script is executable until project/grantee/owner and operation budget are bound.

Approval sequence: review AMEND-01 and output choices -> separately authorize exact local
implementation -> validate/review immutable Bot and any SQL deltas -> approve exact observations
-> revise/seal rollout targets and recovery actions -> approve individual G4 operation IDs ->
review resulting evidence -> explicit operator G5 decision. This packet remains not executable;
unresolved facts and independent source-pin/output decisions cannot be approved transitively.

## 4. Source/configuration/dependency pins

Release source candidate is production `468d975b47d58e648882de2d96f7f81b6d84efb3` only; mirror
is comparison evidence. SQL source candidate is `4cd1554dc3d063e323f22350c88df1444cd0ed4b`.
`source-pins.json` contains individual Git blob/SHA-256 values and separately labelled local-byte
SHA-256 values. Neither value is an independently observed deployed checksum. CRLF/LF changes
must be accounted for in the reviewed deployment artifact; do not silently normalize raw manifest
hashes. Authority `code_files` inventory must exactly match its protected source map (maximum
4096); archive/test/venv exclusion rules come from the pinned launcher, not an assumed glob.

Source requirements include gspread 6.0.2, google-api-python-client 2.187.0, google-auth 2.43.0,
google-auth-httplib2 0.2.1, google-auth-oauthlib 1.2.2, gspread_asyncio 2.0.0, pyodbc 5.2.0 and
PyYAML 6.0.3. Exact Python build/executable, installed dependency versions, wheel hashes, ODBC
driver/certificate configuration and environment inventory remain UNRESOLVED. A requirements
version pin does not pin downloaded artifact bytes. No pip install or runtime inspection now.

Protected config identities to finalize: Bot manifest v1; normal authority manifest v2;
enrollment manifest v1/profile v1; SQL installation contract v2; legacy SQL contract v1;
application SQL contract v1; export configuration raw hash; runtime registration canonical hash;
deployment/review UUIDs and boundary hash; seven observation raw hashes. Enrollment plan pins
manifest raw bytes and canonical profile; SQL plan digest uses UTF-16LE. Do not conflate these
hash domains. All runtime/config/dependency deployment hashes remain UNRESOLVED until independently
reviewed artifact preparation and subsequent target comparison.

The full application source contract pins 538 schema sources, canonical digest
`0fcc6360f17cc6017801b074117b6b7d6fb8ebb0bd808d686971511b350a27d2` as recorded by S11.
**Planning comparison found this retained inventory is not current for three procedures.**
The production constant `APPLICATION_SCHEMA_SOURCE_HASH` still equals that digest and
`validate_application_installation_contract` requires an exact digest match for `sources`.
Of 538 retained entries, 527 match current raw local bytes, eight match after line-ending
conversion, and three differ under raw/LF/CRLF comparisons:

| SQL source procedure | Current LF source SHA-256 |
|---|---|
| `dbo.usp_ExportExecutionSessionTransition` | `341cfa5b07adafd8294f52c16973e2618098ae9c622e64cc81253a29083731bb` |
| `dbo.usp_ExportExecutionStreamTransition` | `fd62793f2ca5e523afdd00851cace2eea162e253c5a3ed8d8cb5df6d7023de25` |
| `dbo.usp_ExportOutputEnrollmentTransition` | `ce05e66de0153c4c88008d5d94eff6ebce07c2aaf39812d74ed468653c07e179` |

Exact old/new hashes and domains are in `application-inventory-reconciliation.json`. These
procedures carry the delivered role/enrollment/unfinished-stream/terminal-evidence review
corrections. An updated authoritative source list cannot simply replace the old list while the
Bot requires the old digest. This is a **source-manifest sealing blocker**, not proof that a
particular deployed startup has failed. Do not roll SQL back, mislabel the old inventory as current,
or weaken the digest check. Prepare a separately scoped source-pin reconciliation if authorized;
keep this task planning-only. It does not reopen predecessor implementation or authorize a fix.

Expected metadata/permission fingerprints require independent source-derived review;
the observed server cannot declare itself correct by supplying its own expected fingerprint.

## 5. Complete writer boundary and seven observations

| Writer/caller family | Source owner | Observation/exclusion requirement |
|---|---|---|
| Upload-triggered daily scan ingestion/recompute/export and stats delivery | processing_pipeline, standalone procedure/cache helpers, shared ExportRuntime | Pin accepted scan/config/output provenance, ordered daily history/claims, nested ownership and spool |
| Legacy all-KVK import/recompute/automatic and manual exports | kvk_all_importer / bound legacy snapshot and coordination services | One outer SQL admission; no nested self-deadlock, no mutable reread between tabs |
| ProcConfig provider reads/import/configuration refresh | proc_config_import and bound configuration helpers | Budget provider reads before SQL phase; desired config/counterpart authority retained |
| New-source upload/admin/recovery/export/status/rebuild/rollover | existing grouped commands, source services, worker and delivery | Complete UpdateID/vector intent, registration-aware eligibility, exact owner/fence/version |
| Compatibility/test export wrappers | gsheet_module run_single_export/transfer_and_sort/run_kvk_export_test/run_kvk_source_export | No unregistered provider bypass, no incidental manual invocation |
| Authority, provider children, enrollment and proof/recovery issuers | pinned launchers/host/authority and SQL APIs | Same protected authority, retained handles, origins, journals, no direct child start |
| External exporter/uploading admin and output owner | operator-reported external system/manual upload | Freeze admin edits; explicitly record whether access reaches each protected resource |
| Other processes, SQL Agent jobs, tasks/services, scripts, old tokens/keys and admins | No additional writers reported | Actual named observations must establish exclusion; repository search cannot prove absence |

Each observation is a protected typed record plus preserved original output, SHA-256, UTC time,
observer identity, command/source, target and independent reviewer. Bind the same deployment and
review UUIDs, exact source/config and expiry. A proposed value or a Boolean is not observation.

| Record | Required original evidence | Producing operation |
|---|---|---|
| `host_acl` | Host identity; owner/DACL of source, interpreter, manifest/key/evidence paths and all parents; no reparse escape | G4-00H, refreshed after G4-03 |
| `bot_identity` | Actual process token SID/groups/privileges including disabled privileges and deny-only administrators; cannot elevate or read authority key | G4-00H / G4-04N |
| `identity_issuance` | Fresh identity/project/client, key issuance/custody receipt, IAM issuer/impersonator/admin set and approved maintenance boundary | G4-03I |
| `key_inventory` | All key IDs/holders/status and access-capability observations; dev/ordinary Bot exclusion, old identity isolation | G4-00P / G4-03I; metadata only |
| `file_access` | Exact owner/editor/viewer and inherited access per file, aliases/grid identities, protected exclusions, origins | G4-00P / G4-04E |
| `writer_drain` | Admission closure, root/child/session/job identities, complete request catalogue, held/terminated handles, no delayed-effects proof | G4-03D / G4-04D / G4-05 |
| `sql_installation` | Server/database/principal, exact definitions/dependencies/shapes/signatures/grants/roles/migration receipt and effective token permissions | G4-00S / G4-02 |

## 6. SQL dependencies, isolation and recovery

Only observed missing/changed dependencies enter a later approved install list:

1. S8 source/update/complete selection/intent/admin prerequisites.
2. `migrations/20260914_001_shared_export_coordination.sql` — jobs/resources/budget/attempt parts.
3. `migrations/20260914_002_legacy_export_preparation.sql` — preparation/resource/spool provenance.
4. `migrations/20260915_001_kvk_output_pool_rollover.sql` — file/pool/slot/disposition and scoped refs.
5. `migrations/20260915_002_kvk_output_operation_ownership.sql` — operation/resource ownership.
6. `migrations/20260924_001_export_execution_evidence.sql` — session/stream/request/events/proof/origin and APIs.
7. `migrations/20260924_002_export_legacy_module_permissions.sql` — exact root signatures/countersignatures.

Do not blindly replay predecessor migrations against successor shapes. Partial/incompatible
state stops for forward-fix review. Schema snapshots are reference contracts, not an alternate
installer. No backfill, budget seed, registration, receipt mapping or live import is implicit.

S11 roles `ExportExecutionAuthority` and `ExportExecutionReader` require exact effective rights,
membership/owner/reapply checks and no direct evidence mutation or inherited escalation. Legacy
manifest `deploy/export_legacy_module_permission_manifest.json` binds original module bodies and
three signing groups `S11LegacyImport`, `S11LegacyStats`, `S11LegacyTargets`, exact public-only
certificates/signatures (matching Import certificate in master), dbo resolution and module closure.
Session-local `#S11LegacyDeployment` and `#S11LegacySignatures` must contain approved exact inputs.
No signing key, xp_cmdshell enablement, proxy credential, ACL or application membership is created
by that migration; these are separate named provisioning prerequisites/effects if actually needed.

Actual restore must precede install/tests: approve source and immutable backup path → capture
backup metadata/hash/ownership → FILELISTONLY mapping → restore to separately absent database and
new physical files → integrity and original-row/receipt/fence preservation comparison → reviewer
acceptance. VERIFYONLY may supplement this and cannot replace it. Preserve the restored database,
backup and transcripts. Production rollback is not permission to restore over current history.

Ordinary evidence tests require new `K98_S11_Disposable_...` database; legacy-body tests require
the separate isolated instance/ROK_TRACKER above. Provider/native fault cases and Discord cases
need disjoint new pools/files, SQL accounts/IDs and seasons. No retained S6/S8/S10 database or file
is disposable by implication. Test names constrained to S10E naming need their exact existing
gated target/packet; adapting a gate to an S11 name would itself need implementation approval.

## 7. Operation ledger and literal-command boundary

All rows are **NOT APPROVED / NOT RUN**. Each row must acquire literal fully bound commands or
UI actions, target IDs, source/config/evidence hashes, actor, expected effects, numeric budgets,
stop/rollback eligibility and independent approval against the seal before execution. Every
`UNRESOLVED` command is a hard block; prose scope is not an executable operation.

| ID | Exact proposed action/effect | Prerequisites and expected evidence | Timeout/budget; stop/recovery |
|---|---|---|---|
| G4-00H | Read-only inventory on T-HOST/T-DEV: service/task definitions, process incarnation/token, source/config/dependencies and path ACL metadata; never key contents | Named paths/accounts/process read scope; originals for host_acl/bot_identity/key access | UNRESOLVED; drift/unexpected privilege/writer stops, preserve output |
| G4-00S | Read-only catalog/version/login/role/signature/permission/migration/dynamic-shape and active producer inventory on T-SQL | Exact metadata query file/hash and visibility identity UNRESOLVED; compare source-derived contract | UNRESOLVED; opaque/partial metadata or incompatible target stops, no grants to make observation pass |
| G4-00P | Read-only provider identity/IAM/key-metadata/file-permission/grid/alias inventory | Exact identity/file allowlist and API field scope UNRESOLVED; preserve original responses | UNRESOLVED request/read cap; any unknown writer/alias blocks provisioning/admission |
| G4-01B | Backup approved source to T-RESTORE backup file; local hash/metadata retention | Approved path absence, source/owner/capacity, closed writer boundary where required | UNRESOLVED I/O/time budget; failed/uncertain backup retained, no install |
| G4-01R | Actual restore to new absent restore DB with every logical→physical file mapped | G4-01B, independent disjointness/backup review, restore script hash | UNRESOLVED; no overwrite/drop; failed restore stops and preserves files |
| G4-02P | Provision exact restricted SQL users/public certificates/signatures/proxy prerequisites | Observed missing subset only, separate privilege/effect manifest and signatures; backup/restore passed | UNRESOLVED; unexpected role collision/grant stops, no elevated test substitution |
| G4-02I | Install enumerated missing SQL migrations in dependency order, one separately pinned operation per script/target | G4-00S/01R/02P, admission closed and old writers excluded; preservation baseline | UNRESOLVED transaction/lock/wall budget; partial/drift fails closed, forward-fix review |
| G4-02T | Run exact new SQL evidence/ownership/CAS/concurrency/permissions cases on isolated targets | Approved case node IDs, seeds/IDs, real restricted users, actual restore; preserve synthetic rows | UNRESOLVED; independent stale owner/fence/version/NULL and positive control all required |
| G4-03D | Freeze imports/admin mutations, close admission, drain exact old writer roots/children and stop named service/task incarnations | Approved service/task/PID/start-time/SQL-session allowlist; no lease-age inference | UNRESOLVED drain budget; incomplete drain retains claims, separate reconciliation decision |
| G4-03I | Issue fresh provider identity/key directly into authority custody; apply approved path/file/IAM changes | G4-00 observations, named custodians and exact ACL/key effects, old-writer exclusion | UNRESOLVED; no copied legacy key fallback; revoke only separately named newly issued capability if safe |
| G4-03H | Install reviewed source/dependencies/protected manifests and service/task definition with admission closed | Exact artifact and service definition hashes, ACL plan and rollback build; no runtime start implicit | UNRESOLVED; drift stops, preserve previous artifact/state |
| G4-04E | Fresh private output enrollment, then separate exact registration after origin verification | Installed SQL, separate enrollment profile/plan, owner consent, private files and disjoint exclusions | UNRESOLVED request/file cap; create uncertainty blocks replay; created files remain retained |
| G4-04N | Native token/pipe/child containment and startup failure cases on approved isolated resources | Pinned case driver, exact host/SIDs/source, service manager restart policy suppressed for faults | UNRESOLVED; no direct provider child start, retain failed sessions/handles |
| G4-04C | Provider 429/503/shared cooldown and lost-checkpoint cases with exact request IDs | Separately approved bounded fault method; fresh private resources and two caller identities | UNRESOLVED calls/time; no intentional provider overload or mutation retry |
| G4-04D | Shutdown/owned delivery, uncertain open/close, actual-factory budget/transaction mode cases | Exact streams/session versions and fault point, sealed driver; no production-wide failure injection | UNRESOLVED drain/time; nonzero incomplete drain, no release or restart-based certainty |
| G4-04Q | Immutable A / eligible B→C, daily order/fairness, registration wait, nested legacy spool provenance | Disjoint synthetic inputs/jobs/targets; one specified intake per case, SQL/provider receipts | UNRESOLVED jobs/calls/bytes; wrong ordering/provenance or extra work stops |
| G4-05R | Preview exact rollover, close admission, drain/reconcile, terminate old writers, revoke old audience, private clear/readback and audited reuse | Exact old/new season/pool/epoch/disposition/owner/fence/version; fresh proof and no delayed effects | UNRESOLVED requests/time; ambiguity quarantines, never reuse |
| G4-05J | Interrupted retirement journal recovery with nested versioned owner, read-before-clear and fresh post-revocation publication probe | Exact retained journal/origin/request snapshot; separately approved fault point and recovery | UNRESOLVED; missing journal/foreign host/uncertainty stays blocked |
| G4-06D | Production-only Bot deployment/restart under approved watchdog/task; compare observed build/readiness | Accepted SQL/identity/containment evidence and exact compatible rollback; approved deployment diff | UNRESOLVED; no rolling main pull or implicit pip/test/cleanup; readiness failure keeps admission closed |
| G4-06U | Named Discord admin upload/confirmation/export-only/status/rebuild and denied actor/guild/role cases | Exact guild/channel/actors/roles/attachments/seasons plus bounded response expectations | UNRESOLVED uploads/messages/time; unexpected public send or extra import stops |
| G4-06O | Observe exact deployed source/config/process, queue/cooldown/receipt outcomes over approved window | Prior accepted operation evidence; explicit read-only scope and expected natural activity | UNRESOLVED duration/calls; regressions close admission, preserve evidence |
| G5-REVIEW | Operator records accept/reject/defer per gate and overall decision | Evidence complete for exact packet/source/targets, independent review and residual risk record | No automatic pass, execution or activation |

Dependency order: approved G4-00 observations → packet revision and separate review → recovery/
provisioning/install/test stages → native/private-provider cases → controlled deployment and bounded
Discord cases → observation → explicit G5. Inventory can reveal new dependencies; this graph is
not a batch runner. Enrollment and normal authority manifests have different readiness boundaries;
normal runtime cannot start with the enrollment profile or fabricated deployment observations.

Verified launcher syntax, shown only to define later binding (these are **not current commands**):

```text
G4-04E: UNRESOLVED_PYTHON UNRESOLVED_CODE_ROOT/scripts/enroll_export_output_pool.py
        --manifest UNRESOLVED_ENROLLMENT_MANIFEST --plan UNRESOLVED_CREATION_PLAN
        --actor UNRESOLVED_ACTOR --reason UNRESOLVED_REASON
        --authorize-operation S11_CREATE_PRIVATE_OUTPUT_POOL
G4-04N/G4-06D authority: UNRESOLVED_PYTHON UNRESOLVED_CODE_ROOT/scripts/run_export_authority.py
        --manifest UNRESOLVED_AUTHORITY_MANIFEST
```

All other literal operational scripts/actions: **UNRESOLVED pending targets and approved observed
state**, not a nonexistent `--dry-run` or invented admin CLI. SQL install/session-input wrappers,
backup/restore file maps, IAM/ACL operations, task controls and Discord option values must be
rendered into the next packet before their approval. G4-00 query/observation scripts can be
prepared first once the requested nonsecret target facts arrive; creating them grants no execution.

### First observation subpacket: literal read-only statements for later review

These commands are **printed planning text, never executed in this task**. They are separated
from full G4-00 because they cannot alone generate all seven records. Each needs named observer,
approved local execution host, pinned tool executable, evidence output directory, UTC window and
expiry before approval. Output redirects remain unbound until an outside-Git evidence path and
ACL are selected. Proposed read limits: one invocation each, 5-second SQL connect/30-second query,
60-second host command deadline; exceeding the limit stops without a retry. Budgets are proposed
for operator review, not measured guarantees. No provider/Discord request, key read, business
procedure, object write, installation or process control is included.

**G4-00S-ID-PROD**, observer on the approved SQL administrative host, target
`MINI_AMD` / `ROK_TRACKER`; connect through the named read-only metadata identity using Windows
authentication (actual login binding still UNRESOLVED):

```powershell
sqlcmd -S 'MINI_AMD' -d 'ROK_TRACKER' -E -b -l 5 -t 30 -Q "SET NOCOUNT ON; SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS ServerName, CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) AS ProductVersion, DB_NAME() AS DatabaseName, ORIGINAL_LOGIN() AS OriginalLogin, SUSER_SNAME() AS LoginName, USER_NAME() AS DatabaseUser; SELECT name, compatibility_level, collation_name, state_desc, recovery_model_desc FROM sys.databases WHERE name=DB_NAME();"
```

Effects: metadata reads only; evidence is exact server/database/login/version/compatibility/
collation/recovery state, not installed-schema or restricted-token certification. Stop if target
does not match the approved alias resolution or major version 16; record mismatch without edits.

**G4-00S-NAMES-DEV**, on the operator's local development machine, target `localhost\K98DEV` /
`master`; preserve all returned database names as exclusions:

```powershell
sqlcmd -S 'localhost\K98DEV' -d 'master' -E -b -l 5 -t 30 -Q "SET NOCOUNT ON; SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS ServerName, CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) AS ProductVersion; SELECT name, state_desc FROM sys.databases ORDER BY name; SELECT DB_NAME(database_id) AS DatabaseName, name AS LogicalName, physical_name FROM sys.master_files ORDER BY database_id,file_id;"
```

Effects: catalog reads only. Existing proposed DB/file collision blocks creation; no rename,
drop or reuse. File metadata visibility gaps remain explicit. This does not create a database,
backup or restore, inspect business data, or establish current SQL role permissions.

**G4-00H-BASE**, run locally on candidate Bot host `MINI_AMD`, under the named approved observer:

```powershell
hostname
Get-Item -LiteralPath 'C:\discord_file_downloader','C:\discord_file_downloader\venv\Scripts\python.exe','C:\discord_file_downloader\run_bot.py','C:\discord_file_downloader\DL_bot.py' | Select-Object FullName,Attributes,Length,LastWriteTimeUtc
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\discord_file_downloader\venv\Scripts\python.exe','C:\discord_file_downloader\run_bot.py','C:\discord_file_downloader\DL_bot.py'
Get-Acl -LiteralPath 'C:\discord_file_downloader','C:\discord_file_downloader\data','C:\discord_file_downloader\logs','C:\discord_file_downloader\downloads' | Select-Object Path,Owner,Sddl
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" | Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath
```

Effects: filesystem/process metadata reads only; no full command lines or environment values
that might contain secrets. Current observer token is **not** automatically the Bot token.
The full bot_identity record requires a separately pinned native token observation of the actual
Bot incarnation, including disabled privileges; `whoami` as an administrator cannot substitute.
These path reads do not establish authority-private custody or the new seven-record boundary.

Source limits to retain while choosing operational budgets: 2100 ms shared request spacing;
429/503 numeric wait capped at 3600 seconds, HTTP dates bounded using SQL UTC; authority SQL
connection timeout 5 seconds; authority connected pipe timeout 30000 ms. These are not a global
test timeout. Overall drain/maintenance/provider/SQL/disk budgets remain UNRESOLVED; reaching a
budget stops/reconciles rather than terminating ownership or replaying a connected request.

## 8. Required new evidence cases

| Case IDs | Required outcome and concrete source anchor |
|---|---|
| N01–N04 | Wrong/elevatable Bot token rejected; authority child SID/PID authenticated; busy-pipe acquisition bounded before send; connected request/reply loss never replayed. Authority host/protocol/client tests and actual tokens |
| N05–N08 | Child accept/hello/cancel bounded; retained handles after failure; no escaped delayed writer; complete drain closes exact session with status 0, incomplete drain status 1 and session retained. Both launchers |
| N09–N12 | Late import/construction failure after acknowledged open closes only confirmed empty session at acknowledged version; once constructed require successful drain; failed/raising drain retains; uncertain open/close neither closed speculatively nor retried |
| C01–C06 | Exact request-bound 429 and 503 envelopes; numeric/date/missing/invalid Retry-After bounded/fallback; wrong/malformed request envelope rejected; other caller observes durable cooldown; lost cooldown acknowledgment retains dispatch_intent, uncertainty and claims; no success/not_sent invention or provider retry |
| T01–T04 | Actual normal/enrollment factory budget/pool connection transactions; evidence DAL uses its own autocommit connection/procedure transaction; rollback/commit and lost acknowledgments; no SQL transaction across provider I/O |
| S01–S08 | Restricted authority/reader evidence permissions; session stale version plus positive control; concurrent session/close/admission; each stale owner/fence/version/NULL separately; fresh-role collision/exact reapply; prepared/dispatch-intent close refusal; legal terminal append to frozen stream; enrollment preparation replay/ownership rejection |
| L01–L04 | Separate legacy instance: readiness, denied_child_execute, denied_evidence_update, configuration_fallback_rollback under XACT_ABORT off/on with real restricted login. Exactly synthetic ProcConfig_Staging KVK_NO 2147483000 and nine NULL columns; preserve original row/transaction |
| Q01–Q05 | Running A immutable, eligible pending B coalesces to C without lost history/fairness ticket; daily requests remain ordered; missing destination waits with intent retained; all three writer families share account budget/aliases; complete provenance/spool and entered nested children survive cancellation |
| P01–P05 | Fresh enrollment origin/blank/private readback; byte-exact complete publication/readback; lost grant/pointer ack stays uncertain; positive absence only from complete no-dispatch history and expected pointer; damage only after ACL/structure/manifest/pointer match |
| R01–R04 | Rollover closes admission before drain; old-writer termination/no delayed effects before epoch advance; private ACL/clear/full readback before reuse; interrupted journal recovery/nested CAS/fresh post-revocation probe, append-only disposition and receipt preservation |
| D01–D05 | Admin upload both arrival orders/explicit confirmation; normal matched source/endpoint/UpdateID contract; export-only no parser/recompute, confirmed duplicate zero provider work; wrong actor/guild/role denied; startup/shutdown/registration-aware intents and truthful pending/stale status |

These are required observations, not claimed authored executable case selectors. Bind each to an
existing fixture node or reviewed new inert operational driver before approval. Existing authored
SQL anchors are `tests/test_export_execution_sql_integration.py`,
`tests/test_kvk_export_sql_integration.py`, SQL `validation/kvk_source/s11_export_execution_evidence.sql`
and `s11_export_legacy_module_permissions.sql`. The latter is metadata verification; the former
narrow SQL script proves session CAS, not the whole concurrency/provider matrix. Never run the
whole predecessor suite to manufacture these cases. S10C/D/E newly needed transaction coverage
must be selected explicitly with positive controls and disjoint target approval.

Do not enable `K98_S11_SQL_AUTHORIZED` or `K98_S11_LEGACY_SQL_AUTHORIZED` in planning. Their later
approval-file hashes bind target/operations/backup/**actual restore** and restricted principals.
An admin connection substituted for the restricted identity invalidates permission evidence.

## 9. Preserved invariants and exclusions

Fixed season source; supplied kingdom/camp aggregates/DKP and separate overall; frozen B0;
11−10 → 12−10 → final 13−10 → authorized 14−10 with normal configuration authority and retained
counterpart validity, no extra correction command; no guessed UpdateID, timestamp pairing or
silent legacy fallback. Independent daily SCANORDER, targets, claims/history stay independent.
Running A is immutable; only eligible never-started pending work coalesces. Preserve registration-
aware intents, daily order/fairness, complete S10C committed provenance/spool and nested ownership.
Exact owner/fence/version CAS, append-only assignments/dispositions and byte-exact receipts apply.

Capacity preflight: `1 + P + P + max(P,Q) + P + R` total files, including one stable index;
P includes headers/directory and maximum 9,000,000 cells per part; Q is actual quarantine and R
other protected final/referenced parts. At most eight registrations and sixteen slots each.
P=2/Q<=2/R=0 yields nine files as historical recommendation, not a production capacity claim.
Actual P/Q/R/receipt/disk budgets must be measured/planned before writes. Exceeding bounds blocks
before mutation; never truncate receipts or treat uncertain capacity as free.

Retain S6-OPS01, S6-PERF01, S6-CAP01 as OPEN. Preserve both uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c` and their
databases/files/owners/fences/receipts. Historical IDs and complete exclusion sources are in the
S7 contract section 11, release evidence/readiness and archived S6 pack. Their referenced output
IDs are protected exclusions, never candidate pool slots. Expand and independently verify the
complete exclusion list before approving any resource operation; an incomplete list blocks it.

S6 accepted measurement remains 5,806 players × ten periods, 17,831,355 physical cells, two parts,
2248.609 seconds export/readback and 991 export calls; it does not bound the new deployed profile.
S8A six scripts/VERIFYONLY, S8B 50 SQL cases and **actual restore** versus later offline runner
history, and S8C seven local checks remain separate accepted evidence. S8C synthetic actor/guild/
channel and folder transport are not live Discord acceptance. S10A historical restore/execution
does not prove current installation; S10C/D/E/S11 authoring is not provider or installed SQL proof.
Retain every S1–S11 evidence database, raw upload, provider file, backup, journal and recovered
artifact. No cleanup, automatic adoption or predecessor rerun belongs to this plan.

## 10. Stop, reconciliation and rollback

Stop the affected operation on target/source/config/ACL drift, unexpected writer or privilege,
missing source observation, preservation mismatch, unsupported SDK semantics, partial SQL
installation, failed restore, owner/fence/version conflict, request uncertainty, incomplete
termination or exceeded budget. Record last acknowledged version/request/phase, raw receipt,
process/session/handle identities and current admission state before proposing recovery.
No generic automated retry/resume: pre-send acquisition is distinct from a connected request.

Before installation, rollback is continued non-installation and closed admission. Afterwards,
close admission, drain owned delivery, retain uncertain claims, reconcile exact requests and
prove termination/no delayed effects. Preserve SQL history, spools, origins, journals, all receipt
bytes, evidence and prior config/source artifacts. No age/job-state release, generation relabel,
flag-only rollback or re-enabling copied-key legacy writers. Disabling routing can expose old
uncoordinated behavior and is insufficient exclusion.

Compatible serving build and literal rollback service/config actions: UNRESOLVED pending actual
inventory and SQL compatibility. Do not assume #588 is a safe rollback for corrected startup/
cooldown behavior. Additive history normally needs reviewed forward SQL fixes. The authored
legacy permission rollback script requires its own exact eligibility/signature packet and
approval; its existence does not authorize broad revoke/drop or restoring over retained data.
No reverse operation is currently approved. Interrupted retirement always requires explicit
journal recovery, read-before-clear, fresh post-revocation publication proof and audited reuse.

## 11. Approval/evidence ledger and remaining facts

Local planning checks passed: architecture (zero changed application Python), deferred-item
validation of this packet, security routing (zero errors/warnings), exact-path test selection
and diff whitespace. Source/runtime pytest, smoke imports and registration reruns are skipped:
only planning documents changed; the selector's generic smoke/registration recommendation is
not evidence of a runtime delta. No SQL checker/fixture, provider/native scenario or predecessor
was executed. Individual remote file/blob proof passed for 44 mirror entries, 43 production
entries and both SQL documents; 253 retained review/log files kept their bytes, sizes and mtimes.
SQL working tree remains unchanged. These are planning checks, not G4 acceptance evidence.

Per-operation record: packet ID/revision/hash; exact operation/subcase IDs; source/config/script
hashes; target/identity; approver/operator/abort owner; start/expiry UTC; prerequisites reviewed;
literal action and read/write effects; numeric budgets; expected assertion; original evidence
path/hash/time/provenance; actual result/exit status; stop/recovery decision; independent review.
No approval is transitive across changed targets, identities, commands, hashes or effects.

G5 gate record: S6 open gates and uncertainties; actual restore; installed SQL and transactions;
all-writer/key custody; containment/provider finality; cooldown/shutdown; queue fairness/capacity;
rollover/recovery; deployed Discord behavior. Each records accept/reject/defer, limitations,
residual risk, owner and follow-up against exact evidence. Missing mandatory proof stays open.
G5 overall acceptance and activation are explicit separate operator decisions after evidence.

Missing nonsecret facts requested: named hosts/accounts/SIDs/service definitions; SQL production
and isolated targets; backup/restore/protected storage paths; provider project/owner/fresh identity
and selected file/grid/pool IDs; Discord guild/channel/actor/roles and synthetic source/season
targets; operator/abort owner, window/expiry, budgets/retention. Unknown is an acceptable answer.
Do not obtain them by unapproved live observation and do not supply secrets. Samples are not
requested now; a future named case must first explain its precise required shape and purpose.

This new packet stays local and unpublished. Bot planning belongs with future genuine authorized
Bot implementation or explicit publication authorization; no separate Bot docs PR is proposed.
SQL #90's two-document exception is delivered and does not authorize further SQL publication.
