# KVK Source Migration — Programme Pack

## Current status — S7 approved; S8A pack prepared, 2026-09-12

Chris Watts approved the S7 contract and exact implementation manifests, then authorized
preparation of the next pack and starter. The approved technical direction includes initial
account serialization, durable legacy snapshots with worker affinity where needed, and the
stated quarantine/reserve allowance. Settled S7 decisions are not reopened.

**Next: S8A SQL Foundation, after separate file-implementation authorization.**
[Task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md); [implementation starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md).
Preparation is documentation-only. No S8A SQL/runtime/config implementation, database
execution, Git publication or activation is authorized by this status. Preserve the full
27-path Bot carry-forward union, including both S6 archive move sides and both S7 outputs;
SQL implementation belongs in its own repository and review. Historical status blocks below
retain their original evidence; this latest status supersedes pending S7 review wording.

## Current delivery and next slice — 2026-09-12 post-S6 closeout

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

**Next: S7 Integration Contract and Implementation Planning**, documentation/read-only
scope after explicit S7 approval. Do not rerun predecessors or start later packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](../reference/kvk_source_migration/post_s6_integration_requirements.md); [handoff and exact manifest](../reference/kvk_source_migration/post_s6_handoff_log.md); [S7 pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

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

[Readiness and rollback](../reference/kvk_source_migration/release_readiness_and_rollback.md); [Canonical S6 evidence and delivery](../reference/kvk_source_migration/release_evidence_log.md).


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



## 1. Programme header and execution boundary

| Item | Value |
|---|---|
| Programme | KVK Source Migration |
| Date / version | 2026-09-07 / v1.0 |
| Owner | Chris Watts — KD98 / Kingdom 1198 |
| Context | Whole-KVK source change: player snapshots plus authoritative kingdom/camp totals |
| Bot working copy | `C:\discord_file_downloader` |
| Bot remote supplied by operator | `cwatts6/K98-bot-mirror` |
| SQL working copy | `C:\K98-bot-SQL-Server` |
| SQL remote supplied by operator | `cwatts6/K98-bot-SQL-Server` |
| Current stage | S1–S5B accepted; S6 evidence merged/accepted; S7 integration planning is next |
| One-pass implementation approved | Current documentation refresh only; S7 execution and subsequent implementation require their own approval |
| Runtime, SQL, configuration or deployment changes approved | No new runtime/SQL/live action; local deployment operator-reported, production runtime unverified and activation incomplete |
| Current permitted output | Post-S6 closeout, archive/link repairs, settled requirements and next S7 pack/starter |

The operator reports both working copies and their Git repositories are synced. Codex must verify their actual branches, commit IDs and working-tree state rather than assume a branch name or deployed version. This pack was prepared from the supplied discussion, source assessment and task template; it does **not** certify that the current code or production SQL has already been audited.

**Historical Phase 1 first action (completed; do not repeat):** execute `Codex Task Pack - KVK Source Migration Phase 1 Audit and Validation.md`, produce its evidence-backed outputs, and stop for operator review. Future phases are a planning roadmap, not standing permission to implement them.

## 2. Outcome and scope

Introduce a reversible, source-aware KVK import/reporting route that follows the established KVK workflow where its semantics remain appropriate. Player gains come from supported differences between eligible snapshots. Kingdom/camp values come from the selected authoritative totals report. Preserve the legacy route and historic data while auditing every downstream consumer before changing its source.

The programme covers upload admission and validation, baseline/scan identity, configuration imports, persistence, processing, window selection, caches, reports, Discord commands/embeds/cards, exports, historical comparisons and operational recovery **where current dependency evidence establishes a connection**. It does not presume that every command containing “KVK” or every kingdom-1198 stats feature uses this pipeline.

Avoid a parallel reimplementation of the whole bot. Prefer reuse of proven helpers and reporting interfaces, but do not disguise unlike facts as interchangeable data merely to reuse a table or column.

## 3. Confirmed operator decisions

These are requirements, not questions to ask again. Full provenance and superseded advice are recorded in `docs/reference/kvk_source_migration/decision_and_evidence_register.md`.

| ID | Decision | Required effect |
|---|---|---|
| D01 | Audit first; follow similar logic to the existing KVK import/reporting process. | Trace current semantics before proposing replacements; preserve valid operational conventions. |
| D02 | Keep the existing route available; assess a new import process. | New-source introduction must not retire or corrupt the legacy route. Physical table reuse versus new tables remains open. |
| D03 | Player exports are snapshots. | Resolve the requested window's starting/ending observations and calculate supported differences, not sum repeated snapshots. |
| D04 | Retain all 36 kingdoms for the supplied KVK. | Do not filter to 1198 because it appears in filenames. Future KVK scope must use its approved configuration rather than a universal hard-coded count of 36. |
| D05 | A separately designated baseline workbook is the master player list. | Only its eligible Governor IDs enter new-source player reporting. Later-only governors remain excluded. Do not silently grow the roster. |
| D06 | No starting observation means no calculable player gain. | Never manufacture a zero baseline or report a missing observation as zero activity. Membership and window-endpoint availability are separate checks. |
| D07 | Kingdom and camp imports are authoritative reported totals. | Use the selected report, not an accumulating sum of repeated imports. Do not replace a supplied camp row with summed kingdom rows or replace kingdom totals with the eligible-player sum. |
| D08 | Supplied kingdom/camp DKP is authoritative. | The provider has the exact T4/T5 death split and already calculates DKP. Import its DKP; do not recalculate, infer its split or require the unavailable split to proceed. |
| D09 | Player DKP retains the single total-deaths figure and existing `WeightDeadsZ`. | No `WeightDeadsT4Z` or `WeightDeadsT5Z` additions to `KVK_DKPWeights` for this change. Audit the actual player formula and active configuration. |
| D10 | Death/KP definitions differ between layers. | Preserve total deaths and combined T4+T5 deaths as distinct metrics; player-to-summary DKP equality is not a correctness requirement. |
| D11 | Filename timestamps are always UTC and mark scan start. | No UK local-time/DST conversion; do not substitute upload time, file modification time or scan completion. Exact accepted filename grammar still needs implementation validation. |
| D12 | KVK Windows and Camp Map should remain structurally unaffected. | Reuse existing configuration contracts where possible. Audit contents, identity resolution and consumers; escalate an evidenced incompatibility rather than redesigning these sheets unilaterally. |
| D13 | One or two new Discord upload channels are possible. | Channel topology is not yet selected or authorised for provisioning; it must not substitute for format/scope validation. |

A code audit may show that existing behaviour conflicts with a requirement. Record that conflict with evidence and propose a correction; do not silently reinterpret the requirement to match the current code.

## 4. Evidence status and authority

Authority is deliberately split:

- **Desired behaviour:** the operator decisions above, including the 2026-09-07 clarifications, supersede earlier assessment recommendations.
- **Existing implementation:** current code, SQL definitions, tests and inspected operational evidence at recorded commits. Directory listings and historical task packs are not proof of current behaviour.
- **Source capabilities:** the original workbooks, inspected read-only and identified by hash. Descriptive filenames do not establish kingdom scope or a database scan ID.
- **Historical analysis:** the earlier source assessment and CSVs are leads to reproduce, not already-passed acceptance tests or a current database inventory.

Four source workbooks and the previous analysis are in the companion **private evidence bundle**, separate from repo documentation. Its manifest identifies the original bytes. The master roster workbook has **not** been supplied as part of this pack. Do not designate the Pass-4 starting example as the KVK master roster without operator instruction.

Phase 1 must start and complete all independent repo/source investigations even when that roster or a live SQL connection is unavailable. Mark the affected conclusions blocked; never label missing validation as passed.

## 5. Target processing contracts to validate

### 5.1 Player path

```text
Designated master baseline -> eligible Governor ID roster for this KVK
Selected window            -> required starting and ending observations
New snapshot imports       -> validated source observations
Eligible ID + usable endpoints + supported metric -> measured difference
Measured player differences + applicable existing weights -> player DKP
```

A roster answers **who is eligible**. A window answers **which observations define the period**. Later windows must not silently use the original KVK baseline in place of a missing window start. For closed windows, no unannounced latest/nearest endpoint substitution is acceptable. Codex must document the existing live-window resolver and propose how valid behaviour is retained.

Keep excluded governors out of published player facts and ranks. Retaining the untouched source file and diagnostic rejection counts for audit is not the same as admitting them into the eligible roster. Determine through the audit how exclusions and missing endpoints can use existing diagnostics safely.

A missing ending observation, a failed scan, a counter regression, a duplicate Governor ID and a genuine zero delta are different states. Carry signed power changes where appropriate. Inspect whether existing processing uses endpoint values, first/last observations or extrema, and assess compatibility field by field rather than copying an assumption from the earlier analysis.

### 5.2 Kingdom/camp path

```text
Aggregate workbook -> validate Kingdom Stats and Camp Stats together
                  -> preserve supplied values, DKP and source precision
                  -> associate report with verified KVK / period / scan identity
                  -> selected end-of-window report supplies published totals
```

“Replace the last totals” describes the **active reporting selection**, not permission to discard all previous observations. Assess versioned retention and a selected-report pointer, or equivalent existing mechanisms, to support completed windows, corrections and rollback. Do not add repeated totals or silently apply player-style differencing to aggregates.

Authoritative supplied data still requires structural validation: required fields, parseable values, duplicate keys, membership, tab completeness, unsupported content and clear provenance. Structural checks must not insist that DKP be reproducible from an export that lacks the exact tier-death split.

### 5.3 Window-period question still requiring evidence

The aggregate example's name describes a period beginning 26 August, whereas the supplied player start is 5 September. The operator wants similar logic to the current KVK process. Codex must inspect how the current process interprets windows and confirm whether each new aggregate report represents:

- the requested fighting window; or
- a fixed-baseline cumulative period associated with an end scan; or
- an existing equivalent explicitly represented and labelled by current reporting.

Selecting an end scan alone does not prove that an aggregate report isolates a later fighting window. Trace current behaviour first; ask one precise remaining source-period question only where code/configuration and supplied evidence cannot answer it. Do not reopen the settled UTC or DKP policies. Do not invent subtraction, zeros, additional uploads or a new period scheme as approved requirements.

Existing Baseline/no-fight windows with equal start/end IDs require particular attention. A zero player difference does not justify populating a no-fight aggregate window with unrelated cumulative totals. Establish skip/zero/not-applicable behaviour from current evidence and operator approval.

### 5.4 Timestamp and identity separation

Record scan start in UTC independently of import time. Validate the suffix parser, precision, missing seconds and renamed/reuploaded files. Keep observation identity distinct from content hash, upload/attachment ID, source kind and logical KVK scan ID.

Two independently uploaded sources must not accidentally obtain or share their window identity merely because they arrive consecutively. Conversely, source observations at different times must not be presented as a simultaneous scan without an approved mapping. Explain how both streams can resolve the same logical window using the existing conventions.

## 6. Original programme phases — historical roadmap

| Phase | Scope and deliverable | Exit condition | Execution status |
|---|---|---|---|
| **1 — Audit and validation** | Reproduce earlier findings; inspect both repos; map end-to-end consumers; validate existing window, baseline, timestamp and DKP rules; produce compatibility options and unresolved decisions. | Operator receives evidence-backed audit, exact affected-object manifest, clear limitations and recommended next slice. | **Ready; docs/read-only investigation only.** |
| **2 — Contract and architecture approval** | Settle report-period semantics, baseline onboarding, scan mapping, missing-field behaviour, new/reused persistence, historical policy and source selection. Produce decision records and PR-sized implementation packs. | Architecture approved, then implementation plan separately approved; no phase may self-approve. | Not authorised. |
| **3 — Persistence and new ingestion** | Implement only approved persistence/metadata changes and separate player/aggregate ingestion using established validation/admission. Leave new publication disabled; preserve old importer. | Offline/isolated tests and contract checks pass; idempotency, correction, rollback and source isolation demonstrated. | Planned; split SQL/bot PRs as supported by audit. |
| **4 — Processing and downstream reporting** | Apply approved window/roster rules; publish source-aware datasets through audited DAL/services; adapt every affected report, command, embed/card, export and cache. | Consumer matrix closed; exact and precision-aware checks pass; historical/legacy regressions pass; no unexpected public output. | Planned. |
| **5 — Controlled release and close-out** | Approved deployment sequence, private/shadow evidence, operator smoke, controlled source activation and recovery rehearsal; update runbooks and programme status. | Operator accepts results; legacy fallback limits documented; no unresolved critical data-integrity issue. | Planned. |

The original status column below is historical; the post-S6 amendment and current delivery block govern actual progress. The S1–S6 slices implemented parts of these phases; S7–S11 close integration and release gaps.

The audit may recommend smaller implementation slices or a different ordering. Update this roadmap with rationale after approval. Do not generate speculative migration scripts or runnable later-phase tasks before the relevant decisions are settled.

## 7. Mandatory decision gates

| Gate | Evidence needed | What it permits |
|---|---|---|
| G1 — Audit review | Reproducible findings, current dependency graph, unknowns and source capability matrix. | Approval to refine the architecture; not runtime changes. |
| G2 — Contract / architecture | Proven period semantics, master-roster handling, scan-ID mapping, per-field semantics, persistence and historical decision records. | Approval to prepare the exact implementation plan. |
| G3 — Implementation plan | File/SQL manifests, tests, data migration/backfill boundaries, security routing and rollback per repository. | Only the explicitly approved implementation slice. |
| G4 — Release readiness | Tests, diff review, deployment plan, configuration readiness, privately checked data and rollback evidence. | Only the explicitly approved deployment/promotion actions. |
| G5 — Close-out | Operator smoke and observation outcomes; remaining limitations and ownership recorded. | Programme completion, not legacy deletion. |

An audit can be delivered with a narrowly described missing-evidence item. It cannot pass an affected design/release gate by guessing. Record missing source material separately from repo access, deployment status and actual implementation defects.

## 8. End-to-end audit coverage

Trace in both directions: from each upload writer to its consumers, and from each serving/output object back to its source. Include indirect dependencies such as dynamic SQL, triggers, SQL jobs, scheduled Python tasks, cache refreshes and sheet exporters; classify gaps honestly.

| Layer | Required audit answer |
|---|---|
| Upload routing | Actual listeners/channels, operators/roles, attachment matching, offload/retry behaviour, multiple-attachment handling, accidental dual routing and shared import admission. |
| Parsing | Tabs selected from the legacy workbook, header aliases, snapshot/delta assumptions, numeric/text coercion, missing values, row boundaries and failure reporting. |
| Metadata / roster | Scan registry and sequence ownership, duplicate protection, UTC parser, baseline assignment/roster growth, kingdom/camp attribution and raw retention. |
| Configuration | `KVK_WINDOWS`, `KVK_DKPWeights`, Camp Map, `ProcConfig`, scan-date imports, defaults and refresh triggers; current KVK-16 readiness separately from sheet structure. |
| SQL / processing | Exact tables, keys, constraints, nullability, numeric ranges, computed columns, views, procedures, functions, jobs, transactions and destructive refresh paths. |
| Serving / cache | Outputs, readers/writers, refresh order, key dimensions, versioning, restart behaviour and active versus final results. |
| Consumers | Player/kingdom/camp ranks and reports, embeds/cards/fallbacks, exports/downloads, scheduled posts and historical comparisons. Record real command paths and permissions rather than guessing from names. |
| Adjacent systems | Establish whether `Stats_for_upload`, `/kvk targets`, `/kvk stats`, `/kvk history`, `/stats`, `/me`, notifications or other routes are linked, separate, retired or unresolved. No automatic scope expansion. |
| Operational overlap | Current task packs/deferred work, post-KS4 changes, import-admission/offload work and embed-safety work where present; read actual status rather than reuse dated summaries. |

## 9. Persistence and historical compatibility decision

Do not select a physical design in Phase 1. Compare at least these options with actual schema/consumer evidence:

| Option | What to evaluate |
|---|---|
| Existing storage with explicit source/semantic metadata | Can it represent snapshots, reported totals, missing fields, supplied DKP and source precision without changing legacy meaning? What existing readers or refreshes would break? |
| New raw/staging facts with compatible serving interfaces | Can separate ingestion preserve contracts while keeping one set of reporting services? What migrations, version selectors and operational complexity are necessary? |
| Isolated new-generation reporting storage | Is separation required because old schemas enforce incompatible assumptions? How do history, exports, discoverability and rollback remain clear? |

The recommendation must answer compatibility at **three** levels: whole-KVK historic browsing, comparable metrics across different KVKs, and any proposed splice between old/new observations within the same window. Approval at one level does not authorise the others.

Do not mix old and new endpoints by default. Do not retrofit absent historical tier-death data, heal counts, extrema or total KP with zero. Label non-comparable DKP bases honestly. A rollback may restore legacy behaviour yet be unable to manufacture new-format periods from unavailable legacy input; document that limitation rather than promise uninterrupted historical coverage.

## 10. Acceptance and regression strategy

The implementation plan must allocate tests to owners and exact layers. The following outcomes are required or must have a documented, operator-approved alternative where current contracts differ.

| Scenario | Expected property |
|---|---|
| Same source reuploaded, including renamed file | No duplicate facts or repeated public side effects; content identity and replay policy explicit. |
| Same scan timestamp but changed contents | Explicit correction/version or conflict handling; no silent overwrite. |
| Backdated / out-of-order scan | Deterministic selection; an older arrival does not become latest solely by upload order. |
| Master-roster member with both endpoints | Correct supported differences and player DKP under the approved existing coefficients. |
| Later-only player absent from master | Excluded from published player results and ranks; counted in diagnostics. |
| Master member missing a window endpoint | No fabricated gain or misleading zero; do not substitute another period. |
| Valid signed power loss / counter regression | Valid signed metrics retained; unsupported counter regressions flagged according to approved handling. |
| Authoritative aggregate DKP differs from player-based calculation | Imported DKP remains unchanged and is not rejected for that difference. |
| Supplied camp differs from sum of rounded kingdoms | Supplied camp remains authoritative; comparison diagnostic only. |
| Repeated aggregate reports | Selected totals supersede earlier selection; totals do not accumulate. |
| Final window followed by new imports | Existing final output remains reproducible under its selected version unless explicitly corrected. |
| Open / missing-end / no-fight windows | Existing/approved rules reproduced with explicit period and availability; no unrelated report relabelled. |
| Different KP/deaths definitions; unavailable legacy fields | No silent semantic substitution; labels, exports and null states agree. |
| UTC timestamps around UK DST transitions | Unchanged UTC observation; no local offset applied. |
| Invalid/ambiguous filenames, malformed rows or incomplete tabs | Clear structural failure/diagnostic with no partial publication. |
| Restart, retry, timeout or concurrent two-stream imports | No duplicate write, half-published report, accidental mixed-source cohort or stale successful cache. |
| Unsafe text in filenames, governor names or exports | Path containment, spreadsheet/formula safety, Discord formatting/mention and embed-length protections assessed and retained. |
| Legacy KVK and unrelated kingdom-only output | No changed values/source/coverage from activating the new whole-KVK path. |
| Rollback | Recovery verified for both code and data selection, with limits documented. |

Historical sample counts in the evidence register are diagnostic expectations for the exact files, **not** production master-roster acceptance totals. Full-precision player arithmetic and approximate summary comparisons require different assertions. Preserve provided aggregate text/precision; do not report invented lower-order digits as measured accuracy.

## 11. Security, release and operational boundaries

Phase 1 is a domain/data audit, **not** authorisation for a standard or deep Codex Security codebase scan. Use the current `k98-security-review-routing` skill and explicit per-repository decisions. The Phase-1 task records documented skips for docs-only/no-SQL-diff work; future approved runtime/SQL changes require their own routing, normally diff-focused Changes review with Deep Off under the current repository rules.

Do not connect to or run production imports, write SQL, execute processing procedures, publish Discord messages, refresh external sheets, restart services, provision channels, change permissions or create production PRs under Phase 1. Metadata/data SELECTs are allowed only through an already authorised read-only connection after inspecting the proposed queries. Code access is not database access.

For later phases, determine the actual SQL migration/validation/promotion mechanisms from the SQL repository. Where the approved bot depends on new SQL contracts, plan SQL-first deployment with backward-compatible old-bot operation. The exact commands and release order require evidence; this pack does not assert that named deployment scripts exist.

Preserve uncommitted user work. Do not reset, checkout, pull, merge or push a repo merely to make it match the pack. Do not put source workbooks, identifiable player-level evidence, credentials or private security findings into public Git history. Use redacted/synthetic test fixtures in later code changes where possible.

## 12. Documentation ownership and next action

Active authored documents:

- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration Phase 1 Audit and Validation.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration Phase 1 Audit and Validation.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`

Phase 1 creates its audit outputs under `docs/reference/kvk_source_migration/` as specified in the task. Reconcile the current `docs/task_packs/README.md` and relevant reference index additively after reading them. Capture only genuine out-of-scope non-security debt in the current deferred-optimisation format. Do not overwrite unseen indexes or mark unrelated tasks complete.

The master-baseline workbook is the only known missing file explicitly promised by the operator. Record it as pending and proceed with independent investigation. A later-window aggregate example or report-period explanation may be required if current code and available evidence cannot settle the temporal contract. These items do not justify asking again about 36-kingdom scope, total-deaths player DKP, supplied aggregate DKP or UTC scan-start timestamps.

## 13. Programme change log

| Date | Version | Change |
|---|---|---|
| 2026-09-07 | 1.0 | Initial programme; consolidated confirmed decisions, superseded earlier aggregate-DKP advice, established UTC scan-start contract, Phase-1 read-only audit and explicit later approval gates. No implementation or audit completion claimed. |

## Phase 1 audit delivery — 2026-09-09

Phase 1 local-code/SQL and original-byte audit is delivered for operator review. This dated
entry supersedes the initial ready/pending wording above; G1 is not self-approved and no later
phase is authorized. Both local main branches were inspected: bot `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`,
SQL `fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Pre-existing bot documentation was preserved;
SQL remained unchanged. Local evidence is distinct from deployed state.

- [Audit and claim ledger](../reference/kvk_source_migration/phase_1_audit.md)
- Dependency matrix (`phase_1_dependency_matrix.csv`; local audit artifact, not included in this PR)
- Field compatibility (`phase_1_field_compatibility.csv`; local audit artifact, not included in this PR)
- [Decisions and proposed next slice](../reference/kvk_source_migration/phase_1_decisions_and_next_slice.md)
- [Validation and scope evidence](../reference/kvk_source_migration/phase_1_validation_log.md)

Reproduced source diagnostics are not B0 acceptance. B0 remains absent. Aggregate later-window
period semantics and current deployed SQL/configuration evidence remain open. Current code uses
upload time, growing baseline membership, missing-endpoint fallback and derived aggregate DKP;
these cannot be retained for the new source. Recommend source-specific storage and versioned
publication with shared compatible reporting interfaces, subject to operator review. The next
recommended task is contract/architecture documentation only. No automatic Phase 2 or migration.

## Follow-up decisions and B0 evidence — 2026-09-09

This is the latest status; earlier B0-absent/period-open/direction-pending text is historical.

| ID | Updated status |
|---|---|
| Q02 | Supplied and designated: `KVK_16_Baseline.xlsx`; 5,806 unique eligible governors, all 36 kingdoms; 5,410 have both P1/P2 observations. Shape/identity validated offline; no live import. |
| Q03 | Resolved policy: separate per-fight reports; live revisions supersede earlier values for that fight, followed by its final report. A distinct final whole-KVK report is authoritative overall. Do not sum revisions or substitute fight sums for overall totals. |
| Q06 | Operator agreed separate new-source direction. Detailed physical architecture and implementation remain unapproved. |
| Q04/Q05/Q07 | Technical source identity/revision/finalization contract, deployed evidence and admission/correction workflow remain next-design or readiness tasks. Do not reopen settled source rules. |

B0 SHA-256: `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`.
Exact source location, checks, coverage and limitations are in the audit's B0 follow-up.
B0 has no timestamp in its supplied filename or columns. That does not block membership;
UTC scan-start evidence is needed only before treating it as a numerical starting observation.
The private bundle's original README/manifest still describe the earlier four-file package and
were not rewritten. B0 remains at the supplied private Downloads path, outside Git.

Remaining operator action is review/authorization of the next contract-only task when desired.
Current deployed SQL/configuration evidence remains a technical readiness gap. No automatic Phase 2.

## Phase 2 preparation — 2026-09-09

The operator requested the next task pack and chat starter. Both are prepared; their creation
is not execution or gate approval. The current recommended next action is the bounded Phase 2A
contract/architecture pass, stopping at G2. After explicit architecture approval, Phase 2B may
prepare exact implementation packs for separate G3 approval. This clarifies the Phase-2 roadmap
without skipping either gate or authorizing Phase 3.

- [Phase 2 task pack](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20Phase%202%20Contract%20and%20Architecture.md)
- [Phase 2 chat starter](archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20Phase%202%20Contract%20and%20Architecture.md)

Enough evidence exists to begin design. Optional same-fight live/final revisions and a later-fight
example would strengthen metadata checks; the final overall report can follow when available.
B0 scan-start provenance is needed only before numerical baseline use. Deployed SQL/configuration
verification remains a technical readiness task. No new private evidence or runtime changes here.

## Pass 4 times, source evidence and SQL access — 2026-09-09

Latest update supersedes earlier missing-timestamp language. Operator confirms B0 UTC scan start
2026-08-26 04:07. Pass 4 player observations: start 2026-09-05 15:26, middle 2026-09-06 13:04,
end 2026-09-07 07:21 UTC. Source names/hashes and checks are in the latest Phase-1 audit section.
Start/end values match prior P1/P2, though byte hashes differ; the middle scan is additional evidence.
5,433 eligible start/middle pairs; 5,410 start/end pairs. Missing middle does not prevent final gain.
These are player scans, not aggregate report revisions. Only Pass 4 has occurred; later-fight and
final-overall examples can remain synthetic until available. No request for unavailable later data.

Q04 timestamp provenance for B0 is supplied. Naming is ours to design, not provider-fixed.
Re-export deduplication needs an explicit content-equivalence policy alongside original hashes.
Q05 now has operator attestation that local SQL/config repo is synced with production, plus an
RDP access offer if needed. Local definitions suffice for design; no live rows/jobs independently
queried and no RDP used. Do not confuse this evidence distinction with a blocker to Phase 2.
The Phase-2 task pack/starter have been updated; task execution and architecture approval remain
separate from preparation. No code, SQL or runtime action authorized by this evidence update.


## Phase 2A design delivered for G2 review — 2026-09-09

The operator invoked Phase 2A only. This bounded documentation pass is complete; earlier
prepared/not-executed wording is historical. G2 is **awaiting operator architecture review**,
not self-approved. No Phase 2B implementation packs, runtime/test/SQL changes or live operations.

- [Contract and architecture](../reference/kvk_source_migration/phase_2_contract_and_architecture.md)
- [Synthetic acceptance scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md)
- [Evidence, validation and canonical delivery record](../reference/kvk_source_migration/phase_2_evidence_and_validation_log.md)

A01–A08 recommend explicit source/scan identities, semantic re-export deduplication, B0 attribution,
versioned configuration, frozen finals with explicit corrections and atomic source-aware publication.
Normal reports select one fight; overall selects its separate final report. Windows/Map sheet
structures and daily/kingdom-only systems remain separate and unchanged. S1–S6 are a draft
feasibility sequence only; exact implementation packs belong to Phase 2B after G2 approval.
Local bot/SQL HEADs remain the Phase-1 anchors; 48 indexed source paths have no drift. B0 and
three Pass-4 hashes match prior validation. SQL/config parity is operator-attested; live rows/jobs
were not independently queried and no RDP was needed. Those are readiness gaps, not design blockers.
Separate bot docs-only and SQL no-change security skips apply. Stop at G2.


## Player EndScanID clarification — 2026-09-09; G2 pending

The operator confirmed StartScanID=10 with successive player scans 11/12 giving interim
11−10 then 12−10; EndScanID=13 gives final 13−10. An authorized later EndScanID=14 change
is itself the explicit correction and produces replacement final 14−10 when available, without
an extra correction command. Old publications remain immutable audit/rollback versions. A pending
new endpoint must not make the old result appear final against the new configuration.
Sequential IDs belong to accepted distinct player observations in the separate source/KVK registry;
re-exports, scan-content corrections and aggregate uploads do not advance that player sequence.
Validated event times and explicit mappings still govern period selection, not numeric MAX alone.
Player endpoint changes do not change aggregate report selection or grant weight/map rewrites.

The contract and synthetic cases T68–T70 now record this confirmed behavior. Earlier generic
final-freeze wording is qualified by this authorized endpoint-change workflow. The operator's
conditional willingness to approve was not recorded as overall G2 approval: documentation needed
this update. Phase 2B remains exact implementation planning only after G2; G3 separately permits
implementation. No code/test/SQL edits, imports, live actions or implementation packs here.


## Phase 2B delivery and G2 approval — 2026-09-09

Chris Watts explicitly approved: **“G2 approved, please proceed”.** G2 is approved, including
the EndScanID clarification and scenarios T68–T70. This supersedes earlier G2-pending/no-pack
statements as current status; their historical evidence remains intact. Phase 2B planning is
delivered in the [implementation plan](../reference/kvk_source_migration/phase_2_implementation_plan.md)
and [planning evidence log](../reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md).
Ten bounded task packs and matching starters are prepared. **G3 remains pending per slice; S1 is
the recommended first approval.** No implementation, SQL change, live action, PR or deployment
is authorized by this delivery. S6 prepares readiness evidence and stops at separate G4 approval.


## Historical S4B validation handoff - 2026-09-11

S4B-MP01 component coverage is complete; S4B remains local for review. The [follow-up register](../reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) assigns S5B-REC01 to integration acceptance and S6-OPS01/S6-PERF01/S6-CAP01 to explicit pre-activation evidence. Future packs and starters carry those IDs. Next sequence remains S4B review/closeout, then separately approved S5A, S5B and S6; nothing advances automatically. Include the four additionally updated S5B/S6 pack/starter paths in the eventual S4B documentation handoff alongside all original thirteen documents/fifteen paths.

## Post-S6 delivery amendment — current sequence

The original programme Phase 2 produced the architecture/implementation plan;
its Phase 3 covers ingestion/persistence, Phase 4 downstream consumers, and Phase 5
release. S1–S6 are the later delivery slices across those responsibilities, not a
second sequence to restart at Phase 3. The routing gap belongs to downstream
integration before release. The following slice names are planning identifiers;
none grants runtime or operational approval. S7 will refine/split exact PR boundaries
where evidence warrants, preserving accepted S1–S6 outputs.

| Slice | Required result | Dependency / exit |
|---|---|---|
| S1–S5B | Accepted foundations, adapters, exports, intake and recovery/config integration | Remain delivered/accepted; existing tests are retained at their actual revisions |
| S6 | Accepted synthetic release evidence and documented blockers | Archived as evidence delivery only; OPS01/PERF01/CAP01 and missing public routing are not closed |
| S7 — Integration Contract and Implementation Planning | Complete consumer/caller matrix; fixed-source, pair/correction, queue/recovery and rollover contracts; exact Bot/SQL/test/security manifests | Next bounded documentation slice; use settled S7-D01–D09, stop for design/implementation approval |
| S8 — Season Source and Matched Publication Integration | Durable immutable source choice, validated pair identity/counterpart reuse, atomic eligible publication and export intent; no partial public update | S7-approved manifests; separate SQL and Bot review targets/PRs where schema changes are needed; offline/disposable evidence only when authorized |
| S9 — Public Reader Integration | Every affected ordinary report/card/command/export/cache consumes the fixed source and complete pinned publication; unavailable/stale states and no silent source fallback | S8 contracts; close the complete consumer matrix, including scheduled and indirect callers; routing remains off pending release |
| S10 — Export Coordination and Operator Recovery | Shared conflict protection across three consumers, durable latest-pending queue, safe manual export/rebuild, bounded pool and season rollover | S8/S9 contracts; split queue and operator/rollover PRs if needed after S7 scope; common manual/automatic admission and restart proof |
| S11 — Controlled Release and Acceptance | Integrate new evidence with retained S6 measurements; verify actual deployed SQL/config/consumers, authorize exact activation/rollback and perform operator smoke | S8–S10 accepted plus updated OPS01/PERF01/CAP01; separate exact G4 operations and G5 acceptance |

S7 is not another general source audit: use the existing C01–C65 matrix and exact
implementation as the starting point, and trace the missing connections. It must
identify all affected outputs under D02 while preserving source-independent daily
SCANORDER/claim ownership, authoritative aggregate/overall semantics, frozen B0,
UTC and exact endpoint/deduplication contracts. Do not add general reliability WS1
work unless a concrete required dependency is evidenced and separately scoped.

The S6 benchmark remains 5,806 synthetic players × ten fight periods, two parts,
37m 29s export including full readback (991 export calls; no recorded HTTP errors),
plus 92.281s generation load. The operator accepted it. It is not a load test of the
future shared queue, public consumers or production process. Repeat only affected
scenarios when new implementation justifies it; do not rerun predecessors by default.

### Carried gates after decisions

| Gate | Accepted evidence / settled decision | Remaining work and owner |
|---|---|---|
| S6-OPS01 | Synthetic private recovery, pointer acknowledgment-loss reconciliation, grant uncertainty and safe blocking measured/accepted | S8–S10 implement new state transitions; S11 accepts their interruption/restart/rollback evidence. Retain both uncertain rehearsal publications without blind retry/reclaim. Chris Watts owns exact operational disposition. |
| S6-PERF01 | Benchmark accepted; import-triggered exports normally 1–2/day, peak 2–3/day; no hard duration cap; finish current then latest pending | S7 designs and S10 proves common admission/pacing/fairness across all relevant callers/processes; S11 accepts runtime behavior. No fixed scheduled cadence question remains. |
| S6-CAP01 | Multipart/ACL/receipt/insufficient-slot evidence accepted; no old spreadsheet archive required after KVK; input/publication history retained | S7 sizes active/staging/quarantine/reserve; S10 implements safe rollover and stale-writer fencing; S11 accepts. No retention-horizon question for old spreadsheet archives remains. |
| Public routing prerequisite | PR #272 finding confirmed and documentation corrected | S7 maps all consumers; S8/S9 implement source choice and ordinary-reader selection; S11 verifies deployed behavior. A routing-row update alone is not activation. |

Engineering open items belong in S7 outputs with owners and exact evidence, not as
repeated product questions. The requirements amendment supersedes public partial
publication, mid-KVK source fallback and mandatory old-spreadsheet archival wording.
Independent private input acceptance and historical publication/audit retention remain.
