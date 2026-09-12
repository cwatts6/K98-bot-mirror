# Codex Task Pack — KVK Source Migration Phase 2 Contract and Architecture

**Archived completed record - 2026-09-09.** Audit/architecture preparation completed; G2 approved. Retained as evidence, not a new execution instruction.

## 1. Task Header

- Date: 2026-09-09
- Owner/context: Chris Watts; KVK Source Migration programme, reviewed Phase-1 findings and subsequent operator decisions.
- Task type: documentation and read-only contract/architecture design.
- Status: prepared for operator use; authoring this pack does not execute Phase 2.
- One-pass approved: only the bounded design/documentation pass when the operator invokes this task. No implementation.
- Boundary: Phase 2A produces a G2 review packet. Stop for architecture approval before Phase 2B exact implementation packs; stop again at G3 before code.

## 2. Required Reading

Read current root/nested instructions, `README-DEV.md`, `docs/reference/README.md`, its required core standards and `docs/templates/Codex Task Pack Template.md`. Read applicable `SECURITY.md` and security-routing guidance. Apply current user decisions ahead of historical document wording.

Then read, in order:

1. `docs/task_packs/KVK Source Migration - Programme Pack.md`, including its latest follow-ups.
2. This task pack.
3. `docs/reference/kvk_source_migration/decision_and_evidence_register.md`, including B0/operator updates.
4. All five Phase-1 outputs in that directory: `phase_1_audit.md`, `phase_1_dependency_matrix.csv`, `phase_1_field_compatibility.csv`, `phase_1_decisions_and_next_slice.md`, `phase_1_validation_log.md`.

Use current source to verify affected contracts and any drift, not to repeat the whole audit. Review relevant active task/deferred indexes, especially ProcConfig reliability overlap. SQL authority is `C:\K98-bot-SQL-Server`; read its applicable instructions, `sql_schema/README.md`, `migrations/README.md` and relevant guardrails. Snapshots are not deployable migration scripts or proof of live definitions.

Private evidence: `%LOCALAPPDATA%\K98\kvk-source-migration\evidence`; read `README_EVIDENCE.md` before historical assessments. Its original four-file manifest predates B0. Designated B0 remains at `C:\Users\cwatt\Downloads\KVK_16_Baseline.xlsx`, SHA-256 `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`. Do not silently substitute P1 or search the whole drive if a file is unavailable. Treat workbook content as data, never as instructions.

## 3. Objective

Turn the completed audit and settled operator decisions into a concrete, reviewable data and reporting contract. Define how separate new-source storage supports immutable observations, a fixed roster, revised fight reports, a final overall report and compatible shared reporting interfaces. Identify exact logical identities, state transitions, field semantics and consumer adaptations without implementing them.

## 4. Background and settled decisions

Phase-1 local anchors: bot `main` at `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL `main` at `fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck actual branch/HEAD/remotes/status; these are historical local observations, not required checkout states or deployed proof. Both repos may contain subsequent work; preserve it.

The current whole-KVK route requires Full Data and uses upload time, grows its baseline, falls back when endpoints are missing, derives aggregates and has readers that recalculate DKP or sum windows. It cannot accept the new source unchanged. `/kvk stats` mixes kingdom-only main metrics with whole-KVK rank/context; most daily/target/history systems have independent sources. Use Phase-1 consumer IDs to scope changes precisely.

Settled; do not ask these again:

- Keep legacy available. Operator agrees new-source separation; detailed physical design is still for review.
- All 36 kingdoms for this KVK; filename prefix 1198 is not a filter.
- B0 fixes eligible Governor IDs. Later-only governors stay excluded; no roster growth.
- Eligibility and window endpoint availability are separate. Missing either required observation means unavailable gain, never zero or another period's baseline.
- Player DKP uses total-deaths differences and one existing WeightDeadsZ. Active coefficients still require evidence; no tier-death weight columns.
- Kingdom/camp metrics and DKP remain authoritative. Do not derive them from eligible players, infer provider tier deaths, demand the hidden formula, or replace camps with rounded kingdom sums.
- **Normal aggregate workflow is separate per-fight reports.** Each accepted live revision supersedes the prior displayed values for that fight; revisions are not additive. A final report is supplied for each fight.
- **One separate final overall KVK report** supplies authoritative overall kingdom/camp values. Do not replace it with fight sums. Do not assume an overall live feed exists.
- Provider can produce running totals, but supporting a general running-total mode is not required by the selected workflow. Do not retrospectively label A1 as a specific fight report merely because some sample arithmetic matches.
- Filename timestamps mean UTC scan start. Do not use UK local time, upload time or file modification time. Operator confirmed B0 scan start as **2026-08-26 04:07 UTC**; retain this explicit provenance alongside its unchanged file hash. Existing filenames are examples, not fixed provider grammar: Phase 2 should propose a practical naming/metadata workflow.
- Keep KVK Windows and Camp Map sheet structures unchanged; propose explicit sidecar identity/mapping where needed.

B0 validation: 5,806 unique eligible governors, 36 kingdoms, 5,410 with both sample endpoints, 45 start-only, 7 end-only, 344 neither. Of 5,682 original matched sample players, 272 are outsiders. Those are exact-file evidence, not universal importer constants or deployment acceptance totals.

Only one fight has occurred: Pass 4. Newly supplied player files under `C:\Users\cwatt\Downloads`:

| Role | Filename | Operator-confirmed UTC scan start |
|---|---|---|
| F1S: Pass 4 start | `auto_pass_lvl4_before_2026-09-05_1526 (1).xlsx` | 2026-09-05 15:26 |
| F1M: Pass 4 middle | `pass_4_scan2_2026-09-06_1304.xlsx` | 2026-09-06 13:04 |
| F1E: Pass 4 end | `end_of_zone_5_2026-09-07_0721 (1).xlsx` | 2026-09-07 07:21 |

All three contain player `Scan` sheets, not kingdom/camp aggregate revisions. The latest audit
follow-up records hashes and validation. F1S/F1E match all P1/P2 keyed cell values despite different
binary hashes. F1M adds a real live-player endpoint: 5,433 eligible start/middle pairs versus 5,410
start/end pairs. One eligible player has start/end but no middle observation; final gain remains
calculable. Never require intermediate coverage or replace a missing fight start with the middle.

The operator confirms the local SQL/config repository is synced with production and offers RDP
if needed. Treat this as operator-attested parity; local source is sufficient for design. Actual
active configuration rows/jobs remain independently unqueried. No RDP or live DB session is
required just to begin the task, and access capability must not be assumed from that offer alone.

## 5. Scope and evidence readiness

In scope: bounded source/DDL drift checks, contract design, synthetic worked examples, evidence inventory, architecture decisions, a consumer adaptation map, a draft slice sequence and documentation validation. Complete independent design despite missing operational evidence.

Out of scope: code/test-fixture edits; parser implementation; SQL files/migrations/DML; real imports, processing procedures, cache refreshes, external exports, Discord changes, restarts, PRs, merges, pushes, deployment or source activation. No credential discovery or new DB connection. Read-only DB access only if already authorized, with bounded reviewed queries; otherwise record the gap. No standard/deep security scan.

| Evidence | Timing / effect |
|---|---|
| Phase-1 audit plus designated B0 | Available; sufficient to start design. Recheck hashes if using originals. Missing local access blocks only fresh reproduction. |
| Two live revisions and the final report for the same fight, preferably original filenames | Valuable during design to validate available report identity/as-of/final metadata. Not a prerequisite: propose an explicit metadata contract and label examples synthetic if absent. |
| Report for a later fight | Not yet available because only Pass 4 has occurred. Use synthetic later-fight cases; no repeated request or design blocker. |
| B0 original UTC scan-start provenance | Supplied by operator: 2026-08-26 04:07 UTC. Timestamp evidence gap closed; numerical baseline/overall selection is still a contract decision, not automatic publication. |
| Final overall report | Validate when available; do not wait for KVK completion to design. Use synthetic examples meanwhile. |
| Current deployed definitions, active KVK-16 Windows/Map/Weights/Details, source versions and jobs/readers | Technical readiness evidence before dependent implementation/release sign-off. Specify a minimal redacted evidence request; local DDL alone cannot close it. |
| Channel/role and operator correction preferences | Propose a concrete, simple journey during design. Provisioning and permission changes remain outside scope. |

## 7. Codex Skills To Use

Canonical section 6 is omitted: this task does not originate from deferred items.

| Skill | Decision |
|---|---|
| k98-architecture-scope | Use for contract boundaries, ownership and gates. Invoking this docs-only task authorizes its bounded design outputs, not runtime work. |
| k98-sql-validation | Use read-only for existing constraints and proposed identity/type compatibility. |
| k98-test-selection | Use for document checks and risk-based future acceptance cases. |
| k98-security-review-routing | Use; separate documented skips below. |
| k98-discord-command-feature | Conditional design review of admission/finalization visibility and permissions; no commands implemented. |
| k98-deferred-optimisation-capture | Conditional for newly evidenced unrelated non-security debt; avoid duplicating Phase-1 entries. |
| k98-pr-review | Use for final documentation/manifest review; no PR creation. |
| k98-promotion-check | Not applicable: no promotion/deployment task. |
| Spreadsheets | Conditional read-only source inspection if additional samples are supplied; no workbook authoring. |

### Security Review Decision

| Repository | Decision | Target / evidence | Expected setup |
|---|---|---|---|
| Bot | Documented skip | Exact output/update Markdown paths in section 11; no runtime, config, dependencies, permissions, parser, data-access, network or persistence behavior changes. Record final diff scope and privacy checks. | Not applicable; no scan. |
| SQL | Documented skip | Read-only definitions at newly recorded HEAD and unchanged task scope; no authored SQL diff. Distinguish pre-existing changes if any. | Not applicable; no scan. |

Re-evaluate if scope changes; do not use this skip to authorize later implementation. Future bot and SQL slices require separate routing, normally Changes review at exact revisions with Deep off.

## 8. Mandatory Workflow

1. Verify both repos without syncing/resetting; capture pre-existing changes. State scope and check Phase-1 evidence drift.
2. Carry forward settled operator decisions and identify only evidence-dependent design gaps. Resolve technical choices through evidence and recommendations, not a list of unanswered engineering questions.
3. Complete the contract, architecture, synthetic scenarios and proposed boundaries in one documentation pass when this task is invoked. Draft read-only evidence requests if live state is missing; do not stall independent design.
4. Validate artifacts, update programme/register/index additively, and present a short decision packet in plain English with recommended options and consequences.
5. **Stop at G2 for architecture review.** Do not self-approve. Only after explicit architecture approval may Phase 2B prepare exact executable implementation packs/chat starters. G3 separately authorizes the particular implementation slice.

## 9. Focused Audit Requirements

Use C01–C65 and original field mappings as anchors. Recheck changed or contract-critical writers/readers: legacy admission/parser, whole-KVK scan allocation, baseline/window recompute, reporting DKP reads, export summation, mixed stats card, config import and refresh/publication boundaries. Preserve independent KS4/SCANORDER, STATS_FOR_UPLOAD, EXCEL_FOR_KVK, targets/history sources.

Validate existing KVK Scan, Windows, CampMap, Weights, Raw/Baseline/Windowed DDL and ingest/recompute/export procedures against SQL source. Classify dynamic SQL, deployed jobs and external consumers as verified, not found in stated scope or unverified; never equate static absence with deployed absence. Do not redo the entire audit absent material drift.

## 10. Contract and Architecture Targets

The contract must include all of the following, with concrete examples and resolved recommendations:

1. **Identity:** separate content hash, import attempt, player observation, aggregate report/revision, KVK, fight, logical endpoint, roster version and selected publication. Define exact namespace ownership and keys. Whole-KVK ScanID and daily SCANORDER are distinct; no allocation based solely on upload order or timestamp proximity.
2. **Metadata:** propose an operator-friendly UTC filename/metadata convention, precision, handling of existing names and download suffixes, and how KVK/fight/as-of/final are identified without changing Windows/Map sheet columns. Naming is not fixed by the provider. Never make upload time a scan-time fallback. Define deterministic older/newer/corrected selection, including delayed uploads. Account for the observed different-byte/same-cell-value re-exports: retain original byte hashes and propose a versioned normalized-content comparison with explicit semantic rules, not automatic correction based solely on binary hash changes.
3. **Roster/players:** B0 membership frozen; roster corrections require an explicit reviewed policy. Choose player attribution and starting-power/weight-version rules. Both valid fight endpoints required per metric. Preserve signed power; distinguish absent/invalid/regressed/zero. Separate numerical overall-baseline use from eligibility.
4. **Aggregate revisions:** model live, final, correction and selected revision states. Each accepted same-fight report replaces selection, not sums. Same content renamed is idempotent; changed bytes for the same report are a correction/conflict, not an automatic new fight. Specify authorization and audit trail for finalization/reopening/correcting finals; recommend explicit correction of a final. Later or backdated arrivals must not silently replace finals.
5. **Overall report:** separate period identity and selection from fights. Preserve supplied overall kingdom and camp values/DKP. Define truthful unavailable display before the final overall report exists; no fabricated overall total from fights or players.
6. **Atomicity/recovery:** kingdom and camp tabs validated/published together; immutable import evidence, transactions, concurrent imports, crash recovery, candidate versus selected data, and retry of downstream side effects. Distinguish persisted facts, publication selection and external delivery success.
7. **Fields/precision:** complete dictionary of types/ranges, nullability, units, raw abbreviated text, expanded Decimal values and displayed precision. Total KP versus tier KP and total versus combined tier deaths remain distinct. Never demand unavailable provider precision. Cover formula-typed Alliance, nulls, zero VIP and unkeyed A1 tail. Proposed parser behavior must not evaluate embedded content.
8. **Storage/interfaces:** separate source-specific facts and versioned publication, with shared reporting interfaces where compatible. Propose logical entities, exact candidate names/keys/types and transaction boundaries in Markdown; label proposals rather than existing objects. No executable DDL or migration files. Explain how legacy recompute cannot overwrite new publications.
9. **Serving:** map each affected Phase-1 consumer to source/period/availability/DKP/rank behavior and an owning layer. Eliminate aggregate DKP recomputation and inappropriate window summation for this source. Define live/final/no-fight and mismatched player/aggregate as-of presentation. Reports must use a coherent selected publication while preserving each stream's actual timestamp.
10. **Caches/history/rollback:** version cache keys and invalidation, request-held payloads, refresh ordering and daily send claims. Preserve historic sources and forbid implicit mixed-source endpoints. A fallback requires actual retained legacy observations; it cannot recover missing history/precision or retract delivered exports/messages. Coordinate code, SQL selection and caches.
11. **Operator journey:** simple upload/validation feedback, choosing fight, replacing live report, finalizing and correcting a final. Propose channel topology and least-privilege roles without provisioning them. No new top-level command assumed; disclose any proposed command surface change and relevant future governance.

Commands/views own permission checks and presentation; services own business rules and publication; DAL owns SQL and transactions. Reuse safe existing helpers after checking semantics. Avoid adding a second domain implementation into DL_bot.py or gsheet_module.py.

## 11. Likely Files and Required Outputs

Review the sources indexed by Phase 1 and relevant current SQL definitions. Do not treat candidate filenames from Phase 1 as approved implementation manifests.

Create only these design outputs in the bot repo:

- `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md`: full contract, proposed entities/interfaces, state transitions, consumer map, decisions with rationale, and G2 review questions.
- `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md`: synthetic input/selected-state/output expectations with explicit failure and retry cases; no real player rows.
- `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md`: source commits, drift/evidence manifest, optional missing inputs, actual checks and final per-repo skips.

Additively update programme, decision register, `docs/task_packs/README.md` and `docs/reference/README.md`. Update `docs/reference/deferred_optimisations.md` only for a genuinely new structured item. Do not rewrite original audit evidence, private workbooks/manifests or unrelated user work. SQL writes: none.

## 12. Design Delivery Requirements

Produce precise documentation, not runnable importer/persistence code. Include a draft PR-sized sequence and dependencies to show feasibility; do not author exact implementation packs or migrations before G2 approval. Prefer the first future slice to be pure offline source validation/models if the reviewed architecture supports that boundary. Distinguish proposed, operator-approved and verified implemented behavior everywhere.

Use synthetic identities in examples. Preserve original private bytes; source reads disable external links and do not evaluate formulas. Do not copy player evidence, credentials or private security findings into Git. Known numeric samples are diagnostic, not a requirement for eligible-player versus aggregate equality.

## 13. Refactor Decisions

Within future migration: isolate new parsing/publication, correct source-specific aggregate readers and window selection, and provide explicit availability. No runtime fix in Phase 2A. Existing legacy export grouping/summation debt and ProcConfig reliability remain separate unless a necessary dependency is evidenced and presented for approval. Capture only newly found unrelated non-security debt using the canonical structure; route security findings separately.

## 14. Testing Requirements

Run the current safe document gates or precisely justify skips:

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe -B scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe -B scripts\select_tests.py
.\.venv\Scripts\python.exe -B scripts\validate_codex_security_routing.py
git diff --check
```

Check links, manifests, decision consistency, required scenario coverage, additive preservation, private-data exclusion and unchanged SQL. Runtime pytest, bot/import smoke and command registration may be skipped for documentation-only work; do not import application fixtures merely for design validation. Log actual results separately from future test plans.

Required synthetic scenarios: eligible/both endpoints; outsider/both; eligible missing start/end/neither; zero versus signed decline/regression; duplicate/renamed/reordered imports; live revision A then B (display B only); final then delayed live; corrected final; later fight with independent period; final overall unequal to fight sums; camps unequal to kingdoms; DKP unequal to player totals; incomplete tabs; unknown/ambiguous camp; malformed/absent timestamps and UTC/DST; precision ties; no-fight; mismatched stream timestamps; crash/concurrent imports; unchanged legacy; partial external export and rollback. Allocate future parser, DAL, SQL, reporting, permission, persistence, cache and format tests to owners; do not claim unimplemented tests pass.

## 15. Acceptance Criteria

- [ ] Current repos/evidence drift recorded; original user work and private bytes preserved.
- [ ] Latest B0 and operator decisions supersede historical missing/open claims without erasing evidence.
- [ ] Identities, immutable revisions, live/final/correction transitions and final overall selection are explicit.
- [ ] Window/Map structures preserved; namespace/metadata proposal is concrete and does not guess deployed assignments.
- [ ] Roster eligibility, endpoint availability, DKP authority and precision remain separate and correctly represented.
- [ ] Proposed storage, transactions, consumer changes, caches/history/rollback are reviewable and grounded in current constraints.
- [ ] Synthetic scenarios specify observable results and remaining evidence limitations.
- [ ] Optional samples/deployed evidence do not stall independent design or become false acceptance.
- [ ] Checks/skips and exact document manifest recorded; no runtime/SQL/external changes or scan launched.
- [ ] Operator receives a small recommended decision set; G2/G3 not self-approved; execution stops before implementation packs/code.

## 16. Required Delivery Output

Use the canonical eleven parts: Summary; File Manifest; New Files; Modified Files; SQL Changes
(none); Helpers Reused (proposed only); Refactor Findings; Test Plan (actual checks versus future
coverage); Security Review Decision and Evidence (separate skips); Deployment Steps (none);
Deferred Optimisations (new items or none).

End with a plain-English design summary, the few remaining operator choices with recommendations,
evidence that can follow later, and the explicit **G2 stop point**. The proposed next task is Phase 2B
implementation planning only after architecture approval. Do not create or dispatch a new task.

## 17. Proposed PR Summary Shape

For a later authorized docs PR: describe the new-source contract and synthetic acceptance scenarios,
the exact documentation manifest, actual checks/skips and evidence limits. State that no runtime,
SQL, permissions or deployment changed, no private source rows were committed, and architecture
still requires operator review. Reversal affects only this task's documentation additions and must
preserve pre-existing work. This section does not authorize creating a PR.

## Pack preparation evidence — 2026-09-09

This records preparation of the pack/starter, not execution of the design task. Authored paths:
the two Phase-2 task-pack/chat-starter Markdown files, plus additive updates to the programme,
decision register and task index. No runtime, SQL, helpers, permissions or restart behavior changed;
no new deferred item. Bot security documented skip for exactly these five documentation paths;
SQL documented skip for no changes. No scan, PR, staging or deployment performed.

Repository venv checks: architecture validator passed (0 Python files), deferred validator passed
(28 Markdown files), explicit-path test selection completed, security-routing validator passed
(0 errors/warnings), and `git diff --check` passed. Runtime smoke/registration/pytest skipped because
only task instructions and navigation changed. Offline `phase2_pack_check.py` checked canonical
sections, new navigation links, original prefixes of all three appended files, clean SQL and empty
staging; passed. Preparation scripts/hashes are in `%TEMP%/kvk-phase1-20260909`, outside Git.
The first link-check filter also selected an unrelated pre-existing Phase-2H index link and failed;
it was narrowed to this task's new KVK Phase-2 links and rerun successfully. No unrelated link edited.
The three design outputs named in section 11 have not yet been created or approved.
