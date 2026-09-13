# KVK Source Migration S6 release readiness and rollback

## Current status — S7/S8A complete and merged; S8B next, 2026-09-13

S7's approved contract/manifests and S8A's SQL foundation are complete and merged.
The operator confirms successful smoke acceptance and local pulls; **no changes have
been pulled to the bot machine**. Retained S8A evidence includes six successful disposable
scripts; the later runner input fix has offline validation only. No fresh post-merge
SQL run, production runtime deployment or activation is claimed.

**Next: start S8B Bot Source and Matched Update Services in a new chat, review/scope first.**
Use the [S8B pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).
Read the [canonical closeout, merge evidence and exact S8B carry-forward manifest](s8a_closeout_and_s8b_handoff.md).
Do not reopen settled S7 decisions or repeat S8A implementation. Further SQL execution
requires exact target/backup/row-preview/operation approval; S8B implementation needs its
own approval after scope review. Public routing remains S9 work; SourceRouting.Enabled
alone does not implement it. S6-OPS01/PERF01/CAP01, both uncertain publications and all
retained databases/files remain preserved. Earlier dated sections are historical evidence.

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

**S7/S8A are complete and merged; S8B is next.**
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
