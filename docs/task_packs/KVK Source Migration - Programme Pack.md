# KVK Source Migration — Programme Pack

## Current KVK delivery status - 2026-09-10

**S1 is accepted and merged** through mirror PR #263 and production PR #570. Its archived
200-test smoke and restart/startup evidence remain historical S1 results.

**S2A is complete, operator accepted and merged.** SQL [PR #78](https://github.com/cwatts6/K98-bot-SQL-Server/pull/78)
merged as `845a25fe66b1d2365fb38720390b4dadf50baa67`; mirror
[PR #264](https://github.com/cwatts6/K98-bot-mirror/pull/264) merged as
`9fc0255dbaa0cbcb80c63c563657dad90bd5bcec` on 2026-09-10. Review fixes passed 401 static
assertions and 96 disposable SQL rejection cases, with twelve-table rollback verified.

**S2B is complete, accepted and merged:** SQL #79, mirror #265 and private bot #572
merged on 2026-09-10. Final validation passed 265 static assertions and 144 disposable SQL
rejections with 25-table rollback; the seven-file review-fix Changes scan found zero issues.
**S3A is implemented and validated; review/merge closeout is pending.** Mirror PR #266 and
private bot PR #573 were both verified open on 2026-09-10; neither is recorded as merged.
Do not restart S3A implementation. Complete S3A review/acceptance and repository merge gates,
then request separate **S3B Acceptance and Atomic Publication G3** with its approved disposable
SQL integration target. S3B is not authorized by S3A delivery or by this handoff.
The operator confirms local pulls completed; no changes were pulled to the bot machine.
Repository merges do not establish production SQL deployment or source activation.
Do not repeat S1/S2A/S2B/S3A as unstarted slices. The [local SQL development reference](../reference/local_sql_development.md) records the reusable K98DEV
instance, retained S2A evidence database and per-slice target authorization requirements.
No production SQL deployment, bot-machine update/restart or source activation is part of this
handoff. Earlier pending/preparation/review-in-progress wording below is historical.

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
| Current stage | S1/S2A/S2B merged; S3A implemented, review/merge pending; S3B G3 remains separate |
| One-pass implementation approved | S1/S2A/S2B delivered; no successor approval |
| Runtime, SQL, configuration or deployment changes approved | S2B SQL and named disposable validation completed; no production deployment or activation |
| Current permitted output | S3A review/acceptance and merge closeout; S3B implementation requires separate G3 |

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

## 6. Programme phases

| Phase | Scope and deliverable | Exit condition | Execution status |
|---|---|---|---|
| **1 — Audit and validation** | Reproduce earlier findings; inspect both repos; map end-to-end consumers; validate existing window, baseline, timestamp and DKP rules; produce compatibility options and unresolved decisions. | Operator receives evidence-backed audit, exact affected-object manifest, clear limitations and recommended next slice. | **Ready; docs/read-only investigation only.** |
| **2 — Contract and architecture approval** | Settle report-period semantics, baseline onboarding, scan mapping, missing-field behaviour, new/reused persistence, historical policy and source selection. Produce decision records and PR-sized implementation packs. | Architecture approved, then implementation plan separately approved; no phase may self-approve. | Not authorised. |
| **3 — Persistence and new ingestion** | Implement only approved persistence/metadata changes and separate player/aggregate ingestion using established validation/admission. Leave new publication disabled; preserve old importer. | Offline/isolated tests and contract checks pass; idempotency, correction, rollback and source isolation demonstrated. | Planned; split SQL/bot PRs as supported by audit. |
| **4 — Processing and downstream reporting** | Apply approved window/roster rules; publish source-aware datasets through audited DAL/services; adapt every affected report, command, embed/card, export and cache. | Consumer matrix closed; exact and precision-aware checks pass; historical/legacy regressions pass; no unexpected public output. | Planned. |
| **5 — Controlled release and close-out** | Approved deployment sequence, private/shadow evidence, operator smoke, controlled source activation and recovery rehearsal; update runbooks and programme status. | Operator accepts results; legacy fallback limits documented; no unresolved critical data-integrity issue. | Planned. |

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
