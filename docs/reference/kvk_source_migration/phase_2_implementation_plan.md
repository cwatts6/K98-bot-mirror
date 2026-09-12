# KVK Source Migration — Phase 2B implementation plan

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

[Readiness and rollback](release_readiness_and_rollback.md); [Canonical S6 evidence and delivery](release_evidence_log.md).


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



2026-09-09. **G2 approved by Chris Watts: “G2 approved, please proceed”.** This approves
the architecture including the confirmed EndScanID workflow. It authorizes this planning pass,
not implementation. **S1/S2A/S2B subsequently received G3 and were accepted; remaining slices require separate G3.** Earlier G2-pending and
no-pack-authoring statements are historical and superseded only to this extent.

Authority: [approved architecture](phase_2_contract_and_architecture.md), including its EndScanID
clarification; [70 acceptance scenarios](phase_2_acceptance_scenarios.md); [decision register](decision_and_evidence_register.md).
This plan fixes implementation boundaries and interfaces; it does not create runtime modules,
SQL, migrations, fixtures, channels or running tasks. [Planning evidence](phase_2b_evidence_and_validation_log.md)
records actual checks rather than future test results.

## 1. Delivery order and per-slice gates

Each row has its own canonical task pack and matching chat starter. A pack is a specification,
not standing authorization. G3 approval must name the slice. Finish and review one bounded diff
before advancing. S2/S3/S4/S5 from G2 are split to keep SQL, calculations, consumer and interaction
changes reviewable; approved semantics are unchanged. No cross-repository combined security target.

| Slice | Boundary | Required predecessors | G3 readiness |
|---|---|---|---|
| S1 | Offline schema, metadata, parser and semantic digest | G2 | Accepted and merged; see current status above |
| S2A | SQL observation/artifact/roster/report facts and constraints | S1 contract accepted | Complete, accepted and merged; disposable SQL validation passed |
| S2B | SQL config/publication/routing/delivery state and constraints | S2A | Complete, accepted and merged; 265 static / 144 disposable rejections passed |
| S3A | Pure player/window calculations and report DTOs | S1 | Can follow S1 independently of SQL deployment |
| S3B | DAL acceptance, CAS publication and config-request services | S2A/S2B/S3A | Disposable SQL integration; no live activation |
| S4A | Shared report/card/diagnostic adapters | S3B | Complete, smoke accepted and merged; routing disabled |
| S4B | Generation-bound exports and destination receipts | S3B/S4A | Private fake destinations first; no real exports through G3 alone |
| S5A | Private intake and one grouped admin control | S1/S3B/S4A/S4B | Disabled defaults; no channel provisioning or imports yet |
| S5B | Config transaction hook and startup/recovery integration | S3B/S4B/S5A | EndScanID transaction/recovery tests; source disabled |
| S6 | Readiness packet, isolated rehearsal and controlled release gates | All prior slices reviewed | Evidence preparation only until separate G4 authorization |

Preferred linear order is the displayed order; S3A may run earlier if separately approved.
No automatic delegation or new Codex task creation. All implementation branches target the bot
mirror or the SQL repository, never bot production directly; no Git synchronization is authorized
by this plan. Execution must preserve existing dirty work and use a separately authorized isolated
branch/worktree when needed. Each pack records its actual start/end hashes, not an invented future SHA.

## 2. Fixed behavior carried into every pack

1. SourceKey `snapshot_report_v1`, explicit KVK/period/event UTC identity; UTC scan start never
   upload/file/local time. Daily SCANORDER and legacy KVK_Scan remain different namespaces.
2. B0 fixes eligible IDs and kingdom attribution; no growing roster. Both correct endpoints are
   needed per player metric. Missing is unavailable; zero requires valid equal values. Power
   deltas may be negative; counter regression blocks that metric and dependent calculations.
3. Player DKP uses X*T4 + Y*T5 + Z*total deaths and an explicitly frozen coefficient version.
   DKP does not require positive B0 power; power ratios do. No new tier-death weights.
4. Normal fight scans 10→11→12 give interim 11−10 then 12−10. EndScanID=13 yields 13−10;
   authorized EndScanID=14 change yields replacement 14−10 when available, with no second
   correction command. Pending configuration is visible; old 13 is not final against 14.
5. New distinct accepted player events allocate sequential IDs atomically. Byte/semantic re-exports,
   observation revisions and aggregate uploads do not consume another player ID. Larger IDs
   do not prove later event time. No intermediate observation requirement for final gain.
6. Supplied kingdom/camp metrics and DKP are authority. Both tabs publish together. Live revisions
   supersede; no sums, player rollups, hidden formula requirement or inferred tier deaths.
7. Overall aggregate uses its separate final report. No default running-total mode or fight sum.
   Player overall is B0 numerical observation to the selected endpoint, independently labelled.
8. Publications retain exact input/config revisions. EndScanID updates are authorized endpoint
   corrections; unrelated weight/map/roster changes and source-content corrections do not receive
   automatic historical-rewrite authority. Final aggregate corrections remain explicit.
9. Source isolation, legacy compatibility, independent kingdom-only systems, versioned caches,
   retained receipts and daily claim ownership remain binding. No activation by upload alone.

## 3. S1 offline contracts and concrete parser limits

Public interfaces to implement in S1 (signatures are design notation, not code to execute):

| Interface | Input → output / invariant |
|---|---|
| parse_filename_metadata | basename string → partial metadata or typed ambiguity; strict UTC date validation, optional download suffix, no filesystem access |
| validate_source_metadata | candidate metadata + explicit operator overrides + scope → immutable validated metadata or errors; supplied identity/time conflicts require confirmation |
| parse_player_workbook | XLSX bytes + metadata + ParseLimits → PreparedPlayerObservation; no SQL, roster mutation, imports, paths, Discord or application config |
| parse_aggregate_workbook | XLSX bytes + metadata + immutable kingdom/camp mapping + ParseLimits → PreparedAggregateReport containing both tabs or a rejected result |
| semantic_digest_v1 | validated typed rows + schema version → SHA-256 and canonical version; source identity comparison remains a separate operation |

Use stdlib dataclasses/enums, Decimal, hashlib, zipfile and the already pinned openpyxl 3.1.5.
No new dependency or pandas requirement for the new parser. Explicit immutable tuples/maps;
no mutable DataFrame as the canonical contract. Existing package __init__ modules are inert and
need no eager exports. No importer/service import that loads constants, connections or Discord.

`ParseLimits` defaults: maximum compressed bytes 20 MiB; total advertised and actually read
uncompressed bytes 250 MiB; per-entry bytes 100 MiB; at most 2,000 ZIP members; total and
per-entry compression ratio at most 200:1; at most 50,000 keyed player rows, 512 kingdom rows,
8 camps, 64 columns, 2,000,000 populated cells and 32,767 characters per source cell. Count actual
iterated cells/bytes rather than trusting worksheet dimensions/ZIP declarations. Normal schema
still requires exactly the recognized 36 player headers or both aggregate tabs. Scope counts
come from the passed configuration, not a global 36-kingdom hardcode. Oversized optional cell
content is rejected before storing; bounded display labels follow the approved field dictionary.
These protective limits exceed supplied sample sizes but require measured tests; exceeding a limit
returns an actionable rejection, never silent truncation or weakened fallback.

Reject encrypted, corrupt, duplicate-member or traversal-shaped ZIP entries; do not extract to
disk. Reject macro-enabled packages and DTD/entity declarations. Disable external workbook links;
do not follow relationships to external resources. Read-only/formula-preserving openpyxl; close
every handle on success/failure. Formula identities reject, formula player metrics unavailable,
formula aggregate required metrics reject both tabs, formula optional text unavailable. Raw
formula text is inert private evidence included in the typed digest, never evaluated. Reject
precision-lost Excel numeric IDs; positive text integers up to bigint maximum remain valid.

Digest v1 canonical format is length-prefixed UTF-8 fields with explicit cell-type tags, row keys,
sheet/header identifiers and schema version; sorted by numeric entity key. Normalize numeric
1/1.0, nulls and line endings only as approved. Preserve text case/codepoints and formula type.
Aggregate raw token plus unit is part of identity; format-only ZIP changes and row order are not.
Unknown data cannot disappear through deduplication. Include a deterministic golden **synthetic**
digest vector so future changes require a version bump. Original artifact hash is always separate.

Known raw-only player profile fields remain raw; optional fractional average values are retained
as invalid/unavailable under v1's integral contract, not rounded or exported as new semantics.
No real workbook or player CSV committed. Build fixture bytes in memory with openpyxl and
synthetic identities; no source workbook modification even during later authorized verification.

## 4. Exact proposed SQL object ownership

All names below are proposed new objects under KVK, absent from the inspected snapshots. SQL
repo changes belong only to S2A/S2B. No legacy tables/procedures/views/functions or ProcConfig rows
are altered by those slices. New DAL transactions in S3B own SQL execution; no new stored
procedures/UDTs or permission grants are required by this design. Do not create a second SQL
calculation implementation. Schema constraints enforce identity/shape; DAL enforces selection
transitions with transactions and row locks. Application principal has no public write route.

Each listed table maps to exactly `sql_schema/KVK.<Name>.Table.sql` in its owning pack.
UUID = uniqueidentifier; UTC = datetime2(0) with precision enum; hash = binary(32);
source strings use an explicit case-sensitive collation compatible with the target server.
Include KVK_NO/SourceKey in composite unique keys referenced by cross-table FKs so a valid UUID
cannot link a different season/source. Positive integer versions and finite decimal ranges follow
the approved field dictionary. Never implement cross-season integrity solely in Python.

| Slice / table | Required key, state and payload |
|---|---|
| S2A SourceArtifact | PK ArtifactHash; ByteCount bigint; generated private relative storage key, no user path authority; created UTC |
| S2A SourceImportAttempt | PK AttemptID; unique guild/message/attachment/action replay key (bounded strings), ArtifactHash FK, actor/provenance, source/KVK, status and safe diagnostic summary |
| S2A SourceObservation | PK ObservationID; unique source/KVK/time/precision/discriminator; SelectedRevisionID nullable during atomic creation, SelectionVersion; matching observation/revision composite FK |
| S2A SourceObservationRevision | PK RevisionID; unique observation/revision number; semantic hash/version, artifact FK, supersedes reference, schema/metadata and acceptance state |
| S2A SourcePlayerSnapshot | PK RevisionID/GovernorID; B0-independent observed kingdom/name; dedicated nullable bigint counters, raw-only bounded profile payload, field status map; no row duplicates |
| S2A SourceLogicalScan | PK source/KVK/LogicalScanID; unique source/KVK/ObservationID; next ID serialized in DAL under source/KVK range lock; int exhaustion rejects |
| S2A SourceRoster | PK RosterID; unique source/KVK/version; designated B0 RevisionID, scope/member digest, approval provenance |
| S2A SourceRosterMember | PK RosterID/GovernorID; B0 kingdom and nullable B0 power; positive identity, exact roster FK |
| S2A SourceAggregateReport | PK ReportID; unique source/KVK/PeriodKey; period kind, selected revision/version; period FK deferred to S2B migration |
| S2A SourceAggregateRevision | PK RevisionID; unique report/revision; artifact/digest/schema; declared coverage bounds/as-of, live/final/corrected-final and supersedes/provenance |
| S2A SourceKingdomReportRow | PK RevisionID/Kingdom; CampID; eight required decimal(38,6) metrics and eight raw/unit pairs, mapping provenance |
| S2A SourceCampReportRow | PK RevisionID/CampID; eight required metric/raw/unit pairs, display label; source camps never computed from kingdom rows |
| S2B SourceConfigVersion | PK ConfigVersionID; source/KVK/version, component digests, approved weight/map/roster references, source import provenance, immutable once selected |
| S2B SourceWindowConfig | PK ConfigVersionID/WindowName; existing Windows column shape plus PeriodKey; unique period key per version; exact bounds and display labels |
| S2B SourceCampConfig | PK ConfigVersionID/Kingdom; CampID 1..8/name; normalized camp-key uniqueness within a version, complete scope validation |
| S2B SourceWeightConfig | PK ConfigVersionID; X/Y/Z decimal(38,12), original round-trip strings and EffectiveFromUTC; no implicit latest row |
| S2B SourcePeriod | PK PeriodID; unique source/KVK/PeriodKey, kind and declared bounds; S2B adds matching source/KVK/period FK to aggregate family |
| S2B SourceScanBinding | PK ConfigVersionID/LogicalScanID; exact existing observation/scan FK; historical bindings immutable |
| S2B SourceConfigRequest | PK RequestID; unique source/KVK/PeriodID/config-content hash/base-config version; old/new endpoint snapshot, origin/import actor or system identity, requested/pending/applied/rejected status and applied publication reference |
| S2B SourcePublication | PK PublicationID; unique source/KVK/PeriodID/generation; exact roster/config/calculation/input revision FKs, stream availability/finality, counts/digest; building/complete state |
| S2B SourcePlayerResult | PK PublicationID/GovernorID; nullable measured fields, DKP decimal(38,6), statuses and metric ranks/cohort sizes; aggregate rows remain immutable revision references |
| S2B SourceSelection | PK source/KVK/PeriodID; PublicationID and monotonic SelectionVersion; same-scope FK, never points at another period |
| S2B SourceRouting | PK KVK_NO; SourceKey, DisplayPeriodID, Enabled default false, RoutingVersion, approved capabilities version; no default activation |
| S2B SourceAction | PK ActionID; immutable actor/provenance, expected version, old/new selected identities, reason/type and UTC |
| S2B SourceDelivery | PK publication/destination-kind/destination-ID; state pending/claimed/confirmed/failed/uncertain, receipt, attempt count, owner/fence, timestamps; no secrets |

S2A must allow empty foundation installation without a period table; before S2B, there is no
operational importer and nothing is activated. S2B validates existing foundation references
before adding its FK. No silent orphan cleanup or data backfill. Same-observation/revision
circular FK uses nullable pointer during the transaction then required service validation at
commit; no intermediate row is public. Status checks alone do not prove row-set completeness:
selection DAL verifies manifest hash/counts in the same lock-protected transaction.

Config/raw-only field state may use bounded JSON text with ISJSON checks if database compatibility
supports the existing SQL JSON conventions; numeric serving fields and keys remain typed columns.
S2B final/corrected-final publication requires terminal components; `final_unavailable` requires
an explicit nonempty reason. Result eligibility also binds the member's `b0_kingdom`; S3A/S3B
must preserve these accepted storage contracts.
Choose dedicated raw/unit columns for the eight aggregate metrics, not an opaque FLOAT payload.
Counter/status field names map one-to-one from S1 schema; physical snake_case names remain fixed
in the S2 snapshots and S3 DAL. Do not expand legacy Windowed to fit them.

Indexes: natural uniqueness above; observation revision/governor; report/as-of; publication/kingdom
and camp for player ranking; delivery state/time; config-request state/time. Add no speculative
global KS4 index. Test same-season FK rejection and concurrent allocation using real disposable SQL.

### Migration naming and rollback

Merged migration paths are `migrations/20260909_001_kvk_source_observation_facts.sql` (S2A)
and `migrations/20260910_001_kvk_source_publication_state.sql` (S2B). The original provisional
S2B date/sequence was corrected before authoring; merged filenames must remain unchanged. SQL convention uses the **actual creation date** and next
available sequence: if implemented later or occupied, update that one manifest entry before
authoring and retain the final name permanently after merge. This controlled date allocation is
not permission to change object scope. Both use RequiresBackup Yes, RiskLevel Medium,
TransactionMode Auto, DataChange No, Rollback Manual and no rollback script: retain additive
objects and disable source. No destructive downgrade claim. Record dependencies in headers.

S2A/S2B add static contract validators and disposable-database fixture scripts listed in their
packs. Production deployment uses reviewed migrations, never snapshots. Existing
`deploy/Validate-SqlRepo.ps1` writes a validation log; do not call it during this read-only SQL
planning pass. `Deploy-SqlMigration.ps1 -ValidationOnly` is not assumed offline/read-only: its
source queries/writes deployment evidence and can touch the database. Never invoke its default
production server/database accidentally. Later test harnesses require explicit server/database
arguments and refuse production identities; no credential search or guessed connection.

## 5. Cross-slice service/transaction contract

`PreparedPlayerObservation`, `PreparedAggregateReport`, `ValidatedSourceMetadata`, `MetricValue`
and `ParseLimits` belong to S1. `WindowInputSelection`, `PlayerPeriodResult`, `ReportSnapshotV2`
belong to S3A. Results are immutable with explicit statuses; Decimal JSON values use strings.
S3B public methods accept these types and caller-provided authorized context, never Discord objects.

| Operation / owner | Required boundary and outcome |
|---|---|
| persist_artifact / S3B artifact store | Generated content-addressed path under configured private root; bounded exclusive temp write + flush/atomic replacement + hash verification before SQL FK. Existing different bytes conflict. No path from source filename; orphan files retained safely. |
| accept_observation / S3B import DAL | One transaction inserts facts/revision/attempt outcome and allocates scan binding only for a new event. Unique replay/digest/version checks handle races. No connection auto-retry after uncertain commit without reading durable outcome. |
| accept_aggregate / S3B import DAL | Both tabs and revision accepted together; sequential revision history, explicit as-of/finality policy; reject incomplete tables. No scan ID allocation. |
| snapshot_endpoint_request / S3B config DAL | Caller-owned transaction: read prior desired/selected endpoint and imported validated Windows; insert idempotent request with provenance. Never commit/rollback caller's connection. Initial weight/map/roster onboarding remains separately approved. |
| calculate_period / S3A | Exact immutable inputs, nullable metric results, frozen B0/weights/map; no DB/clock or implicit latest selection. |
| build_candidate / S3B publication service | Exact revision/config snapshot; building data invisible; durable completion digest/count after validation. Pure calculation reused, not reimplemented in SQL. |
| select_publication / S3B DAL | Short transaction, consistent lock order routing→period selection→config request; compare expected routing/config/input/selection versions, validate candidate complete, change pointer and append action/delivery intents atomically. Lost CAS rebuilds, never blindly overwrites. |
| load_snapshot / S3B reporting DAL | Resolve desired config, routing and publication in one transaction, then immutable facts. Pending desired EndScanID carried as pending; old result cannot claim current final. |
| claim_delivery / S4B DAL | Durable claim/fence per destination, serialize writes, verify current selected generation before publishing discoverable manifest; uncertain external write remains reconcilable. No TTL alone permits a duplicate Discord send. |

Proposed SourceSelection implementation includes SourceKey in its PK; SourceRouting chooses
which source is active for the KVK. This makes the architecture's source-aware period selection
concrete without changing legacy source ownership. Disabled routing returns legacy through old
callers; explicit new-source diagnostics can inspect disabled candidates privately without activation.

### Durable EndScanID flow without a WS1 prerequisite

S5B adds a narrowly feature-gated hook **before the existing transactional config commit** at
`proc_config_import.py` around line 927. It calls S3B's DAL using the same cursor/connection to
record endpoint-change requests. No separate commit. If the config transaction rolls back, so
does the request. If config commits but later targets/autocommit/reporting fails, the request
survives and recovery does not depend on the final function return or best-effort ImportAudit.
The nontransactional branch does not import Windows/Map/Weights and must not manufacture requests.

Capture the authorized import invocation identity where available; otherwise record scheduled
system identity and imported sheet/config digest, never invent the human editor. Production
approval must establish authorized sheet editors/import paths. Endpoint request validates new
Start/End against selected source and keeps approved weight/map/roster components pinned. Only
EndScanID change is automatic final replacement authority. Start changes, roster changes or
weight/map changes remain explicit reviewed config actions. Exact request idempotency includes
base config so 13→14→13 is a new action, not suppressed as an old content replay.
S2B PR review clarified that the replay key also includes PeriodID: one imported configuration
transition may create independent fight/overall requests, while same-period retries deduplicate.

S5B startup worker resumes pending requests; normal accepted scan triggers also wake it. Missing
14 is pending with usable interim displayed, not failed or falsely final; arrival of 14 completes
the request once. Unchanged repeated config import produces no request/generation. Recovery uses
DB state and checks capability/schema before enabling any new-source mode. The hook is off by
default and cannot silently proceed enabled when required SQL is absent. WS1's generic resource,
offload/replay and overall completion fixes remain separate; no broad ProcConfig refactor allowed.

## 6. Consumer closure and release capabilities

S4A owns C15–C28/C35–C43: twelve reporting blocks, whole-KVK rank context, admin diagnostics,
isolated previews and source-aware rendering. Legacy SQL functions/views stay untouched and
new-source adapters bypass their summation/recalculation. The mixed stats card preserves daily
metrics and labels/suppresses independent whole-KVK context. S4B owns C29–C34, export sections,
ALL_WINDOWS/comparisons, RAW/CSV precision and partial remote export receipts. S5B owns C61/C65
integration and C27/C28 delivery wakeup coordination, not daily lifecycle policy.

C44–C60 and C63 remain regression boundaries: daily KS4 stats/cache, targets, finalized history,
rankings, /me, /stats player, standalone kingdom summaries, calendar and daily scan allocation.
C62 cleanup cannot delete new accepted history. The existing C64 escaping convention may be
reused without changing independent rankings behavior. No personal data fixture in public Git.

One `ReportSnapshotV2` per request, with requested/selected config versions, source/period,
stream times/finality, availability and exact publication. Reuse named block keys, not old default
zero normalization. No new-source consumer may return bare legacy output implying wrong basis.
Final aggregate missing means not_received, even when player overall exists. ALL_WINDOWS never
computes overall by adding fights. Exports create private versioned output and update a manifest
only after all intended sections verify; old incomplete tabs cannot be represented as current.

S5A implements one proposed `/kvk_admin source` grouped command with action choices
status, resume, accept, finalize, correct, configure. `configure` onboards explicit immutable
source/config versions, not general settings or live activation. No activation action is exposed
until S6's G4-approved operational path is separately specified. Uploader can accept a normal live
candidate in the private intake; only existing admins can finalize/correct/configure. Bind receipt
to actor/guild/source and revalidate permissions per action. One top-level group unchanged;
canonical command table/grouped count updated and actual registration checks required later.

Source capability flags proposed in `bot_config.py`, implemented only in S5A/S5B:
`KVK_SOURCE_INTAKE_ENABLED=false`, `KVK_SOURCE_RECOVERY_ENABLED=false`,
`KVK_SOURCE_CHANNEL_ID=0`, `KVK_SOURCE_UPLOADER_ROLE_IDS=[]`, and private
`KVK_SOURCE_ARTIFACT_ROOT` unset until configured. Disabled must not require credentials or a
new SQL connection at startup. Public source routing is SQL SourceRouting.Enabled, independently
off; processing/private intake capability does not activate serving. S6 verifies all consumer
capabilities before activation. No live values appear in these packs.

## 7. Verification and operational gates

S1 unit tests cover T01–T20 and parsing parts of T63; source fixtures remain synthetic.
S2A constraints cover T13/T17/T46/T50 and identity portions of T68; S2B covers FK/version/selection
foundations for T43/T45/T47–T54/T65. S3A covers T21–T40/T67–T70 semantics. S3B exercises
actual transactions T01/T04/T07/T41–T54/T65/T68–T70, including concurrent connections and
crash/uncertain commit recovery. S4A covers T35–T40/T52/T55/T60–T62/T67/T70; S4B covers
T16/T55–T59/T63/T65–T67. S5A covers permission/admission T01/T09–T19/T41–T45/T54/T64;
S5B covers end-to-end T48–T54/T59/T68–T70 and no reset of daily claims. S6 rehearses real
configuration mapping, private receipt/export evidence, recovery and rollback under G4 only.
Every T01–T70 case has an owner; repeated cross-layer coverage is intentional.

All implementation slices run architecture/deferred/security-routing validators and test selector,
focused tests and justified broader tests. Full pytest and log-noise check are expected for
S4/S5 cross-cutting integrations; S1 may justify focused-only because no runtime registration or
existing behavior changes. Tests must not load live app state or write operational logs. SQL
static regex tests are insufficient proof of transactional correctness; disposable SQL tests
must run or the affected integration gate remains pending. Do not substitute production tests.

Each future bot/runtime or SQL diff goes through k98-security-review-routing then Changes review
at actual base/head or exact authored patch, Deep off. If unrelated dirty files exist, materialize
an immutable task-only patch/manifest; never review or stage unrelated user work. Bot and SQL
review separately. This Phase 2B authoring has separate bot docs-only and SQL no-change skips.

Before G4, gather redacted live configuration rows (not player rows), exact source mappings,
schema/module/migration-history parity, active relevant jobs/external readers, authorized sheet
editors and channel/role state, deployed bot SHA and recoverable backups/receipts. Local SQL/config
parity is operator-attested; independent live evidence is not claimed. None blocks S1. No RDP or
credential search needed now. Optional aggregate revision samples can follow; do not ask for an
unoccurred later fight or wait for final overall.

Rollback per phase: undeployed S1/S3 pure modules can be reverted; additive SQL remains disabled
and retained; serving rollback chooses an older verified publication using a new selection version,
flushes dependent caches and reconciles deliveries. Legacy fallback only with retained matching
legacy data. Old-bot downgrade must first disable unsupported new serving/writers. No table drops,
history reconstruction, message retraction or exactly-once external guarantee. S6 owns concrete
environment-specific release/rollback receipts after G4; no default-server deployment command here.

## 8. G3 decision and next action

Historical planning recommendation (superseded by current status): approve **S1 only** first. Its manifest is self-contained: schema/models/parser/metadata/
digest modules plus synthetic tests, no SQL or runtime wiring. Current baseline has pinned
openpyxl and inert kvk package entrypoints, so no dependency/config migration is needed.

G2 approval is recorded; implementation has not begun. Later slices have exact planned manifests
and explicit dependencies, but their G3 approval and any required live/disposable-environment
evidence are separate. **Stop for G3 review; do not execute a task pack merely because it exists.**

## 9. Exact implementation packs and approval starters

| Slice | Task pack | Approval starter |
|---|---|---|
| S1 | [Offline Source Validation](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S1%20Offline%20Source%20Validation.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S1%20Offline%20Source%20Validation.md) |
| S2A | [SQL Observation Facts](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S2A%20SQL%20Observation%20Facts.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S2A%20SQL%20Observation%20Facts.md) |
| S2B | [SQL Publication State](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S2B%20SQL%20Publication%20State.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S2B%20SQL%20Publication%20State.md) |
| S3A | [Player Window Calculations](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3A%20Player%20Window%20Calculations.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S3A%20Player%20Window%20Calculations.md) |
| S3B | [Acceptance and Atomic Publication](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3B%20Acceptance%20and%20Atomic%20Publication.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S3B%20Acceptance%20and%20Atomic%20Publication.md) |
| S4A | [Shared Reports and Cards](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md) |
| S4B | [Versioned Exports and Delivery](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4B%20Versioned%20Exports%20and%20Delivery.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S4B%20Versioned%20Exports%20and%20Delivery.md) |
| S5A (accepted, merged; archived) | [Private Intake and Admin Controls](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5A%20Private%20Intake%20and%20Admin%20Controls.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S5A%20Private%20Intake%20and%20Admin%20Controls.md) |
| S5B (accepted, merged; archived) | [Endpoint Config and Recovery Integration](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md) | [Starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md) |
| S6 | [Release Readiness and Controlled Activation](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md) | [Starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md) |

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


<a id="s4b-follow-ups"></a>
## S4B validation follow-ups - 2026-09-11

Operator-approved follow-up: record the remaining work and complete the synthetic multi-period delivery test now. This register supersedes earlier generic S4B gap lists only as stated below. S4B is accepted and merged, with routing disabled and no bot-machine deployment. Phase ownership is explicit; an open item is not acceptance or permission to execute a later slice. Chris Watts owns operational acceptance and approval; the named slice implementer owns its evidence.

| ID | Owner / gate | Status and required closure evidence |
| --- | --- | --- |
| S4B-MP01 | S4B implementer; closeout review | Completed in `tests/test_kvk_source_delivery.py::test_multi_period_delivery_uses_changed_anchor_and_deduplicates`, parameterized for either fight changing. Real generation loader, delivery orchestration, DAL claim decision and Google adapter compose over synthetic SQL I/O and fake Google storage. Proves changed anchor, unchanged-anchor rejection before remote calls, monotonic fence, both fight outputs, unchanged period preservation, missing-overall status, remote manifest/pointer and receipt reload deduplication. This is not a real SQL/Google multi-period or process-restart measurement. |
| S5B-REC01 | S5B implementer; S5B acceptance | Closed 2026-09-12. Operator accepted and merged (#271/#578); caller/lifecycle recovery, committed-config/return-error recovery, endpoint-chain and later-publication attribution validated. Final focused suite: 186 passed including five disposable SQL cases. See archived S5B delivery; no live operational rehearsal is implied. |
| S6-OPS01 | S6 readiness author; operator-approved isolated rehearsal before activation | Open. Prepare exact disposable process/database/file targets and interruption points during private writes, audience grants and pointer publication. After separate operational authorization, record real process exit/restart, durable phase/owner/fence/receipt, actual file ACL/manifests/index and repeated-delivery outcome. Private recovery must quarantine prior targets; publication uncertainty must remain blocked or reconcile from terminal evidence. Never infer absence from time or one missing read. |
| S6-PERF01 | S6 readiness author; operator-approved load rehearsal before activation | Open. Establish an operator-approved acceptable export duration/cadence and request budget, then measure representative synthetic player/period volumes, all multipart writes/readbacks, API counts, bytes/cells, 429/503 behavior and end-to-end duration. Include the quota shared by other processes/machines using the service account without invoking production operations. A local partition-sizing pass or process-local pacer alone cannot close this item. |
| S6-CAP01 | S6 readiness author; destination provisioning/rollback review before activation | Open. Size current/staging plus retained final/referenced generations and recovery quarantine. The measured nine files are an initial allowance, not a lifetime cap. Verify provisioned exact IDs/owner/SA Editor/canShare and intended Viewer audience. Exercise receipt-capacity exhaustion (nvarchar(1024)), insufficient slots and a safe new-destination path. Do not truncate evidence, reuse quarantined/final files, or silently widen schema. Any needed code/schema change requires a bounded separately approved manifest. |

Accepted S5B caller integration references S4B-MP01; its distinct worker/transaction evidence closes S5B-REC01. S6 must carry S6-OPS01/S6-PERF01/S6-CAP01 into `release_readiness_and_rollback.md` and `release_evidence_log.md` when those planned files are authored. They remain activation blockers until measured and accepted. S6 G3 prepares documentation only; separate G4/exact-operation approval is required to execute a rehearsal. Recording this register does not execute S5A, S5B or S6.

Evidence is retained in the S4B pack's latest dated appendix. Keep statuses, measured results, exact tested revisions/targets and operator acceptance together; do not replace an unmeasured result with a test count. Source routing and intake/recovery defaults remain off.
