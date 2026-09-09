# Codex Task Pack — KVK Source Migration Phase 1 Audit and Validation

## 1. Task header

| Item | Value |
|---|---|
| Task name | KVK Source Migration Phase 1 Audit and Validation |
| Date | 2026-09-07 |
| Owner/context | Chris Watts; whole-KVK source migration; companion programme v1.0 |
| Task type | Documentation and read-only engineering/data audit |
| One-pass approved | **No — Phase 1 does not authorise later stages.** |
| Runtime / SQL implementation approved | **No** |
| Status | Ready for Codex to execute the defined audit and documentation scope |
| Bot repo | `C:\discord_file_downloader` — operator-supplied remote `cwatts6/K98-bot-mirror` |
| SQL repo | `C:\K98-bot-SQL-Server` — operator-supplied remote `cwatts6/K98-bot-SQL-Server` |

Complete the independent investigations and audit documents in this task without repeatedly requesting permission for read-only repo inspection. Stop after the evidence-backed audit and proposed next slice. An unresolved input blocks only the conclusions depending on it; it must not trigger guessed implementation or an empty audit handoff.

## 2. Required reading

Read the bot repository's `AGENTS.md`, `README-DEV.md` and `docs/reference/README.md`, then the conditional references required by that index. Read the SQL repository's applicable `AGENTS.md`, root guidance and schema/migration/validation guidance discovered there. Resolve the current canonical task template from the bot repository; compare it with this pack before executing.

Read the following programme documents:

- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`

For security routing, read root and applicable nested `SECURITY.md` files and `k98-security-review-routing`. A policy file or routing skill does not itself authorise a discovery scan.

Read current active task-pack/deferred indexes and then only relevant KVK, import, source-state, export and SQL items. Do not assume older programme status from conversation history is current. Read `canonical_command_reference.md` where present to aid discovery, but use registered code plus tests to establish actual current consumers.

Private inputs default to `%LOCALAPPDATA%\K98\kvk-source-migration\evidence`. Read that directory's `README_EVIDENCE.md` before the historical assessment. The operator may provide another explicit location; record it without putting sensitive source data into Git. Do not scan the user's whole drive for missing files or credentials.

## 3. Objective

Establish exactly how the current whole-KVK import and reporting system works, validate the supplied source findings and settled requirements, and provide a defensible migration recommendation with explicit remaining decisions.

The deliverable must show the path from file intake to every affected SQL object, service, cache, report, command, embed/card and export. It must identify what can be reused, what cannot be represented safely, and which conclusions remain unverified. It must not implement the migration.

## 4. Background and controlling decisions

The previous source assessment compared a legacy multi-sheet KVK workbook, two new all-kingdom player snapshots and a new kingdom/camp totals workbook. Current bot/SQL implementation was not verified. Later operator clarifications override several recommendations in that earlier document.

Confirmed rules to carry forward:

- Use existing KVK workflow logic where compatible; preserve the legacy import route while assessing a separate new-source route.
- Include all 36 kingdoms for this KVK, not just 1198.
- A **separately designated master-baseline workbook** controls eligible Governor IDs. Later-only governors are ignored in published player results.
- Eligibility is not a substitute for the requested window's starting observation. No start means no calculable gain; never use zero or another period silently.
- Player DKP continues with total-deaths differences and the existing single `WeightDeadsZ`; no extra tier-death weight columns.
- Kingdom and camp totals, including DKP, are authoritative as supplied. The provider has an unexportable exact tier-death split. Do not recalculate DKP or insist on obtaining that split/formula as a prerequisite.
- Retain both total deaths and combined T4+T5 deaths where supplied. Do not require detail and summary DKP to reconcile exactly.
- Filename timestamps are **UTC scan start**. The legacy importer is believed to use the same convention; verify that belief without reopening the required new-source convention.
- KVK Windows and Camp Map should keep their existing structures. Validate identities, contents and compatibility.
- Table design, aggregate-period interpretation, precise scan association, live-window rules and channel topology are not yet approved.

Use decision IDs D01–D13 in the programme. Mark conflicting earlier advice as superseded rather than silently retaining it in the plan.

## 5. Scope

### In scope

Read-only code/schema/test/configuration-source inspection; reproducible local workbook checks; current dependency and field-compatibility mapping; safe existing offline tests where useful; documentation of evidence, constraints, options and proposed next slice; additive programme/index updates scoped to this work.

Already authorised, bounded read-only database checks may supplement the repo audit. Record connection/environment evidence separately, without secrets. When unavailable, audit the checked-in definitions and state clearly that deployed SQL parity and live configuration have not been verified.

### Out of scope

Runtime code edits; new importer code; parser patches; migrations/DDL/DML; test-fixture/code changes; executing processing procedures; starting the bot; import replays against real services; configuration-sheet edits; cache refresh/rebuild; Discord posts/channels/permission changes; external export refreshes; production PRs, deployment, restarts, merges or pushes; legacy retirement; standard/deep security scans.

Do not repair bugs as part of discovering them. An urgent defect may be escalated with evidence for a separate approved fix. Do not introduce a general upload queue, new command family, unrelated `/me` redesign or broad SQL refactor under this audit.

## 7. Codex skills to use

Section 6 from the canonical template is omitted because this task does not originate from a deferred-optimisation item.

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | Use | Required for source/consumer boundaries, reuse, SQL dependencies and approval gates. |
| `k98-discord-command-feature` | Not applicable for implementation | No command or interaction changes permitted. Inspect its guidance if needed to inventory permissions, payloads and consumer risks. |
| `k98-sql-validation` | Use | Validate every schema/procedure/view/configuration assertion against the SQL repo and separately label any live evidence. |
| `k98-test-selection` | Use | Select safe offline checks and justify skips; discover script flags from current files. |
| `k98-deferred-optimisation-capture` | Use when findings warrant | Capture unrelated non-security debt structurally; not a route for suppressing security findings. |
| `k98-pr-review` | Use | Review final audit/docs scope, evidence quality, manifests and unresolved gaps before handoff. |
| `k98-promotion-check` | Not applicable | No promotion or deployment in Phase 1. Identify later sequencing requirements in the plan only. |
| `k98-security-review-routing` | Use | Record and verify the per-repository documented-skip decisions below. Selecting the skill does not launch a scan. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| Bot — `C:\discord_file_downloader` | **Documented skip** | Only the authored/updated programme, audit, decision/register and relevant index/deferred Markdown/CSV documentation; exact final paths and diff recorded at close-out. | Not applicable — no scan under the docs-only task. | Scope permits no runtime, configuration, dependencies, permissions, input processing, data access, deployment or persistence changes. Confirm final diff and no private raw evidence staged. Record files inspected; not yet executed. |
| SQL — `C:\K98-bot-SQL-Server` | **Documented skip** | Read-only inspection; no authorised SQL-repo modifications. Record inspected paths/commit and before/after working-tree comparison. | Not applicable — no scan. | No task-authored SQL/runtime/deployment diff is allowed. Preserve any pre-existing user changes; confirm at close-out. Not yet executed. |

If the task-authored diff no longer meets these conditions, stop and rescope; do not retain an unjustified skip. A later approved implementation receives a new security decision per repository, normally Changes review against verified base/head with Deep Off according to current policy. This functional/data audit is not an explicit request for a standard or deep codebase security scan.

## 8. Mandatory workflow

1. Record local repo identity, HEAD, branch, tracked/untracked work and accessible evidence. Read applicable instructions; resolve any instruction conflict without changing branches or user work.
2. Record the provisional security routing and an audit plan constrained to this task. Do not ask the operator again about settled requirements.
3. Execute the source, code, SQL and consumer investigations below. Keep a claim ledger with source locations and clear verified/unverified/superseded labels. Continue independent work when an input is missing.
4. Produce the required audit documents and CSV matrices. Separate observations, inferences, recommendations and operator decisions.
5. Present the architecture options and a proposed next slice. Update the programme's actual status without marking implementation approved.
6. Run safe documentation/evidence validation, review final diffs and confirm the security skips with exact evidence.
7. **Stop for operator approval.** Do not turn the recommendation into implementation, close a decision on the operator's behalf or auto-continue to Phase 2.

Later architecture validation, implementation planning and implementation remain separate approval checkpoints, as in the canonical template.

## 9. Audit requirements

### 9.1 Repo and deployment grounding

Use the supplied local roots. Inspect `git status --short`, current branch, HEAD and remotes; avoid recording credential-bearing remote URLs. Record whether working-tree changes affect audited facts. Do not run a destructive reset, checkout, pull or merge to obtain a clean tree.

Current local code proves the checked-out version, not necessarily the deployed process. Inspect deployment markers/history only where available and safe. Record production-version parity as verified, operator-reported or unknown. Treat current post-KS4 structure as an audit subject; do not rely on old schema notes.

### 9.2 Source validation and reproduction

Locate the four named source files in the private evidence bundle, verify their hashes against the manifest and inspect them without modifying them. A different hash is a different sample version, not an automatic finding that either version is wrong.

Reproduce the earlier workbook sheet/header inventory, row counts, kingdom coverage, uniqueness, overlap and diagnostic deltas. Verify abbreviated text versus numeric values, stray cells, nullable fields and reported DKP. Preserve private row-level checks outside Git; publish only the summary necessary for the audit.

Specifically validate the preliminary findings in the evidence register: 5,729 and 5,720 source players; 5,682 matched IDs; 47 start-only and 38 end-only; 36 kingdoms; 4 supplied camps; different total-KP/T4+T5-KP and Acclaim/Highest-Acclaim fields; combined rather than separate tier deaths; additional cells below the kingdom table; legacy healed/min/max/first-last fields. Do not label diagnostic intersections as the master-eligible cohort.

The starting Pass-4 file is **not designated as the master roster**. If the actual master file is absent, record `master roster not supplied` and finish every other audit section. Do not ask for backfills of later-only governors: the operator's eligibility exclusion policy is settled. Any roster correction is a separately governed future decision.

The legacy and new sample periods differ. No same-period old/new parity claim is possible from these examples alone. Explain what a later shadow comparison can prove and what additional data it would require, without blocking independent investigation.

### 9.3 Upload-to-persistence trace

Discover actual listener/routes/manual paths, channel settings and dispatch rules. Map attachment handling, saving, validation, import admission, offload/workers, failure/retry, transaction boundaries, notifications and cleanup.

Establish which legacy tabs actually drive player and aggregate rows. Do not assume all four tabs are used. Trace headers and fallback aliases to each staging/raw destination. Identify sums, minima/maxima, counter differences, first/last capture rules and any dropping/zero-fill behaviour.

Check every scheduled/manual reprocessing or rollback route. Identify duplicate/retry protection, filename versus content identity, renamed files, partial workbook failure, repeated side effects, multi-file/multi-tab consistency and cross-KVK protection. Record any shared helper or current deferred work relevant to the new routes; do not broaden this task to fix it.

### 9.4 Scan, baseline and window trace

Find the actual owners of `ScanID`, `SCANORDER`, timestamps, import IDs and sequence allocation. Trace `KVK_WINDOWS` start/end resolution, active-window effective ends, finalisation, correction/reprocessing and no-fight windows. Establish which IDs reset per KVK and which are global, with code/schema evidence.

Inspect filename parsing and storage: UTC versus naive/local conversion, scan start versus completion, timestamp truncation, seconds precision and upload-time fallbacks. The required convention is UTC scan start even if the current code differs.

Find current roster/baseline creation, missing-player handling, kingdom/camp attribution and membership changes. Explain how the designated master whitelist can coexist with per-window endpoints without using the wrong baseline. Check players absent from only an ending scan and those missing an intermediate scan.

Explain how two independent new import types would attach to one logical window/end identity without reusing accidental sequential IDs or equating near-but-different source times. Prefer the smallest compatible adaptation of existing logic; document options rather than invent a registry in code.

Trace existing aggregate window semantics before requesting further period clarification. Resolve or explicitly isolate the question of fixed-baseline cumulative totals versus individual-window totals. Inspect equal start/end windows and multi-window totals for duplication/overlap risk. Do not assume additive windows or automatic aggregate subtraction.

### 9.5 SQL/configuration and data semantics

For each relevant SQL object, record exact name/type/path, writers/readers, key/grain, data types, nullability, defaults, computed columns, indexes/constraints, dynamic dependencies and refresh behaviour. Include jobs, triggers, functions, orchestration and external consumers where available. Static dependency searches alone do not prove that dynamic SQL or external jobs have no consumers.

Inspect KVK-list import mapping, DKP weights, window/camp configuration, scan-date inputs and `ProcConfig`. Earlier missing-KVK-16 findings were observations of a source sheet, not proof of deployed SQL absence. Establish actual configuration source and version; classify unobservable runtime values as unknown. Do not insert defaults or reuse older KVK weights merely to make a proposed calculation run.

Trace every player and aggregate DKP calculation and any downstream recomputation. Identify places where authoritative supplied DKP would be overwritten, computed columns would conflict, or shared rollups currently sum player DKP. Check whether whole-KVK DKP, progress ratios, rank order and historical comparisons assume one universal death basis.

Map total KP, T4/T5 kill-equivalent KP, total deaths, combined tier deaths, healed, current/Highest Acclaim, power and extrema individually. Identify unsupported old fields and decide only whether they require a future explicit policy: unavailable, omitted, renamed, independently sourced or non-comparable. Do not backfill missing with zero or fabricate T4/T5 deaths.

### 9.6 Complete downstream consumer trace

For each affected output, name the exact entry point, function/class, SQL/data dependency, source kind, grain, metric formula, refresh trigger, cache key/persistence, permission/visibility, renderer/exporter and test coverage. Work backwards from serving objects as well as forwards from import writers.

Include actual player/kingdom/camp results, leaderboards, performance/progress, rankings, comparisons, historical views, embeds/cards/fallbacks, report generation, file exports, Google Sheets exports where implemented, scheduled posts and notifications. Explicitly classify possibly adjacent `Stats_for_upload`, `/kvk targets`, `/kvk stats`, `/kvk history`, `/stats` and `/me` paths as linked, independent, retired or unresolved, with evidence. Do not call all of them affected by name alone.

Identify raw counters used as gains, different KP bases conflated in labels, display of unavailable values as zero, ratios dividing different measures, precision-sensitive ranks/ties, message/field length assumptions and spreadsheet text/formula safety. Do not import a provider-derived metric into a field with a different established meaning.

Check caches and publication for source/KVK/window collisions, partial stream refreshes, stale/final selection, restarts and reprocessing. A report may expose different source times only if that behaviour is deliberately represented, not by an accidental mixed refresh.

### 9.7 Compatibility recommendation and next slice

Compare existing-table extension, separate raw/staging with shared serving contracts, and isolated new-generation storage using the discovered constraints and reader/writer graph. Recommend one with tradeoffs; **do not approve or implement it**.

Assess historical coexistence, cross-KVK comparisons and any same-window legacy/new endpoint splice separately. Explain exactly what legacy fallback can and cannot recover when new source data cannot be transformed into the old contract.

Produce a proposed PR-sized implementation sequence, exact candidate bot/SQL file manifests, isolated validation/shadow approach, configuration readiness checklist and deployment/rollback outline. Obtain any truly remaining operator decisions after presenting the completed independent work, rather than turning every code-resolvable point into a question.

## 10. Architecture targets

No target implementation is selected during Phase 1. Validate existing layer ownership against repository standards: thin Discord commands/views; services for calculation and selection; repositories/DAL for data access; SQL definitions in the SQL repository; shared helpers reused where semantically correct.

Document direct SQL in commands/views, duplicate business logic, restart-unsafe state, weak validation/logging, dead paths and test gaps. These are findings, not permission to refactor. Separate new-source semantics from source-selection/read APIs so that a recommendation does not require duplicating every consumer unnecessarily.

## 11. File manifest

### Review

The current instructions/indexes in section 2; both repos' actual import/processing/SQL/configuration/consumer/test files discovered by section 9; the four private input workbooks; the earlier assessment and CSVs as non-authoritative leads. Record exact paths/functions/object names and line ranges in the completed audit.

### Modify — documentation only

- `docs/task_packs/KVK Source Migration - Programme Pack.md`: record actual Phase-1 status, evidence links and proposed roadmap refinements, not implementation approval.
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`: mark reproduced/corrected/superseded claims, with evidence and date.
- Current `docs/task_packs/README.md` and applicable reference index, **after reading**, only to add/update this programme's navigation/status.
- Current deferred-optimisation document only for verified unrelated non-security debt, using the canonical structure and preserving existing entries.

### Create — Phase-1 audit deliverables

| Path under `docs/reference/kvk_source_migration/` | Required contents |
|---|---|
| `phase_1_audit.md` | Executive conclusion; exact repo identities; evidence/claim ledger; source reproduction; current processing/window/roster/timestamp rules; key risks; decisions and limitations. |
| `phase_1_dependency_matrix.csv` | One row per discovered dependency edge or consumer. Columns: `ID,Repository,EntryPoint,WriterOrReader,UpstreamObject,DownstreamObject,SourceKind,EntityGrain,PeriodRule,Metrics,RefreshAndCache,Visibility,Evidence,Impact,Status`. |
| `phase_1_field_compatibility.csv` | One row per source-to-serving metric mapping. Columns: `SourceFileRole,Sheet,Header,CurrentFieldOrObject,EntityGrain,TemporalMeaning,Precision,MissingPolicy,CalculationOrSelection,Compatibility,ConsumerIDs,Evidence,DecisionNeeded`. |
| `phase_1_decisions_and_next_slice.md` | Settled versus unresolved decisions; option comparison and recommended design; historical compatibility; proposed exact file/SQL manifests; staged test/deployment/rollback outline; next task scope; explicit stop point. |
| `phase_1_validation_log.md` | Checks run, versions/commits/hashes, selected commands/results, skips, limitations, docs-only final diff and per-repo security skip evidence. |

Do not prepopulate these outputs with invented results. Sanitize formula-leading cells in human-facing CSVs; use IDs/synthetic examples or private companion evidence rather than public player-level records. Temporary analysis scripts/raw outputs may live outside Git; record enough method detail to reproduce the findings.

**SQL repo creates/modifications:** none authorised. Do not create migration scripts during the audit.

## 12. Implementation requirements for this audit

Only documentation is implemented in this task. No command registration/count, runtime helper, persistence, restart, permissions or public output changes are permitted. Do not mark a suspected consumer independent without investigating its full dependency path.

Use evidence forms such as `repo @ commit : path : line range / symbol` or `input hash : sheet : range : check method`. Runtime/deployed evidence must name its environment and read date. A spreadsheet fetched earlier is not a current DB record. Distinguish inaccessible, not found, not applicable and verified absent.

Preserve source bytes and raw-value meaning; do not re-save original workbooks or run embedded/external content. Existing tests must not contact production services. Do not dump environment variables, connection strings, tokens, player datasets or sensitive security details into audit docs.

## 13. Refactor and issue decisions

Classify discovered non-security issues as `within proposed migration`, `separate fix proposed`, `defer` or `not applicable`; give evidence, impact, risk and dependency. **No runtime fix-now classification grants Phase-1 permission to edit code.**

Use `docs/reference/K98 Bot - Deferred Optimisation Framework.md` where current. Suspected or confirmed security findings go to the private security findings workflow with stable identifiers, not the public deferred list. Do not perform unrelated discovery scans or risk acceptance under this task.

## 14. Testing and validation requirements

Select checks with `k98-test-selection`. First inspect scripts and test isolation. Existing architecture/deferred/security-routing/doc validators may be appropriate; commands and flags must come from the current repo. Typical template references include `scripts/validate_architecture_boundaries.py`, `scripts/validate_deferred_items.py`, `scripts/select_tests.py` and `scripts/validate_codex_security_routing.py`; their existence and safe invocation are to be verified, not assumed.

Do not run the application, import workers or SQL procedures as an exploratory smoke test. A full runtime suite, command registration test or import smoke may be skipped for docs-only changes with a precise reason, or run only after proving offline isolation. Avoid auto-fixing formatters that modify unrelated files.

| Category | Phase-1 evidence required |
|---|---|
| Happy/negative/source | Reproduced input inventory and diagnostic arithmetic; missing/duplicate/malformed cases identified. |
| Regression | Existing legacy/new/adjacent test coverage mapped; gaps and future tests named. No false same-period parity claim. |
| Permissions | Actual upload/report access and visibility traced; no live permission changes. |
| Restart/persistence/cache | Current state/refresh semantics evidenced; no restart or state mutation. |
| Format/output | Source and consumer metric meaning, precision, nulls, exports and embed limits audited; no generated public posts. |
| Documentation | Links, filenames, CSV schema, references, requirement IDs, status/gates and absence of stale superseded advice checked. |
| Privacy/security | No raw source workbooks or sensitive audit rows staged; documented skips match the final bot and SQL diffs. |

Log every command actually run with result or short artifact reference. Never claim proposed tests passed. The fact that no code changed is not evidence that the new source will work in the existing importer.

## 15. Acceptance criteria

- [ ] Both repos identified by actual path, branch and HEAD; pre-existing user changes preserved and deployment parity labelled separately.
- [ ] D01–D13 retained; UTC scan-start, supplied aggregate DKP, one player death weight and baseline whitelist are not re-asked as unresolved choices.
- [ ] Every earlier claim is reproduced, corrected, superseded or explicitly unverified; original hashes and methods recorded.
- [ ] Master roster availability recorded; no Pass-4 file silently substituted; eligible-roster membership and window endpoint coverage kept separate.
- [ ] Actual import-to-consumer graph includes writers/readers, config, SQL refreshes, caches, reports, commands, embeds/cards and exports; unresolved dynamic/external edges are visible.
- [ ] Scan-ID namespaces, filename parser, window selection, no-fight/final/live rules and aggregate-period ambiguity are resolved or narrowly evidenced as open.
- [ ] DKP recomputation/rollup assumptions and total-KP versus T4/T5-KP uses are traced to specific consumers.
- [ ] Field and table compatibility options are based on current DDL/readers, not speculative object names; historic coexistence and same-window mixing considered separately.
- [ ] Current KVK-16 config readiness is distinguished from earlier source-sheet observations; no defaults/configuration changes made.
- [ ] Proposed next slice, test plan, candidate manifests, deployment and realistic rollback limits are delivered without self-approval.
- [ ] Required audit outputs and additive index updates complete, with honest blockers and no unsupported completion claims.
- [ ] Safe selected checks run or skips justified; no real import, SQL mutation, public export/post or runtime change.
- [ ] Final docs-only/no-SQL-change security skips evidenced; no standard/deep scan started; private data and unrelated changes not staged.
- [ ] Codex stops for operator review before architecture approval or implementation.

## 16. Required delivery output

Use the canonical delivery shape, with audit-specific details:

1. **Summary:** confirmed findings, contradictions and what is still blocked.
2. **File Manifest:** exact inspected and authored paths, plus both commit IDs.
3. **New Files:** the five audit outputs and purpose.
4. **Modified Files:** programme/register/index changes only; unrelated work untouched.
5. **SQL Changes:** explicitly **none**; separate checked-in schema evidence from deployed-state verification.
6. **Helpers Reused:** no runtime helper changes; identify proposed reuse and semantic limitations.
7. **Refactor Findings:** evidence-backed recommendations; no implementation.
8. **Test Plan:** checks actually run, results, skips and later implementation coverage.
9. **Security Review Decision and Evidence:** separate documented skips, exact diffs/inspected files, privacy check.
10. **Deployment Steps:** **no Phase-1 deployment**; proposed later sequence and rollback limits only.
11. **Deferred Optimisations:** structured non-security items or none; security findings separately handled.

Then state **remaining operator decisions**, **recommended next task** and **explicit stop point**. Keep the number of questions small and only ask what repo/source inspection cannot settle. Complete independent work before asking them.

## 17. Proposed docs-only PR summary

This is a summary shape for the eventual audit handoff, not permission to create or merge a PR automatically.

```md
## Summary

Phase-1 evidence validation and end-to-end dependency audit for KVK Source Migration.
No migration implementation or release is included.

## Changes

Programme status, decision/evidence register, source/consumer compatibility matrices,
audit findings, validation log and proposed next slice. Exact changed paths are in the handoff.

## Tests

List only checks actually executed and their results; explain skipped runtime checks.
Record unavailable master-baseline or deployed-state evidence explicitly.

## Security Review

Bot: documented skip for verified docs-only changes; list final inspected paths and evidence.
SQL: documented skip for read-only inspection/no task-authored changes; record HEAD/status.
No standard/deep codebase scan. No raw/private source data committed.

## Deferred Optimisations

Reference only evidenced non-security out-of-scope items, or state none.

## Risk / Rollback

No runtime or SQL behaviour changed. Any approved reversal is limited to this task's
documentation diff; preserve pre-existing user changes. Implementation remains gated.
```
