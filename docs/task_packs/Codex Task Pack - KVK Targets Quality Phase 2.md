# Codex Task Pack - KVK Targets Quality Phase 2

> Active deferred-optimisation programme for completing the bot-side KVK targets architecture
> after the deployed target-publication separation.

## 1. Task Header

- Task name: `KVK Targets Quality Phase 2`
- Date: `2026-08-26`
- Owner/context: `Chris Watts / KD98; approved Phase 1 deferred optimisations`
- Task type: `deferred optimisation batch`
- One-pass approved: `no`
- Delivery shape: `approval-gated Phase 2A, 2B, 2C, 2D, and 2E slices`

## 2. Required Reading

Before audit or implementation, read the current versions of:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- all core references routed by that index
- `docs/kvk/target_publication_contract.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Target Publication State Separation.md`
- `docs/task_packs/archive/Codex Chat Starter - KVK Target Publication State Separation.md`
- `docs/reference/K98 Bot Deferred Optimisation Scoring Model.md`
- the active bot and SQL `SECURITY.md` files

For SQL-facing review, read the active SQL repository instructions and validate the deployed
contract against `C:\K98-bot-SQL-Server`, including:

- `sql_schema/dbo.KVK_Target_Publication.Table.sql`
- `sql_schema/dbo.KVK_Target_Publication_Row.Table.sql`
- `sql_schema/dbo.v_KVK_TARGETS_FOR_BOT.View.sql`
- `sql_schema/dbo.v_TARGETS_FOR_UPLOAD.View.sql`
- `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql`
- `migrations/20260825_001_kvk_target_publication_provenance.sql`
- current SQL release, promotion, migration, validation, and rollback guidance

Do not infer the deployed SQL row shape from Python dictionaries.

## 3. Deployed Phase 1 Baseline

Phase 1 was deployed and operator accepted on 2026-08-26:

- mirror PR #235;
- production PR #542;
- SQL PR #73;
- import-path transaction follow-up in mirror PR #236 and production PR #543.

Production checks passed for the SQL objects, configured and actual source scan/type, publication
row count, output object, publication version/signature, current publication, cache rebuild, and
Discord output. `dbo.sp_TARGETS_MASTER` owns its publication transaction; the import caller uses a
temporary autocommit boundary and restores the prior connection setting.

The following Phase 1 contracts are fixed inputs to Phase 2:

- shared fighting state remains `DRAFT -> ACTIVE -> ENDED`, with `ACTIVE` starting at Pass 4;
- target publication remains `DRAFT -> OFFICIAL -> HISTORIC`, otherwise `UNKNOWN`/Unverified;
- Official requires persisted successful use of the exact configured matchmaking scan;
- target rows, metadata, version/signature, row count, and output object remain consistent;
- Official targets do not silently republish during routine processing;
- cache identity remains publication provenance, with atomic writes, cross-KVK rejection,
  no-downgrade behavior, and matching last-known-good safety;
- target formulas, values, exemptions, command behavior, permissions, visibility, selection, and
  fallback behavior remain unchanged.

### 3.1 Operator Decisions Recorded On 2026-08-27

- Phase 2A architecture and implementation are approved.
- Phase 2A includes a separate SQL-repository companion PR that changes only
  `dbo.EXEMPT_FROM_STATS.GovernorID` from `float NOT NULL` to `bigint NOT NULL`, with a guarded
  migration, matching schema snapshot, included rollback, independent validation, and a separate
  SQL `Changes + Deep Off` review.
- Production inspection found 55 exemption rows, zero bigint conversion failures, zero fractional
  or out-of-range Governor IDs, zero bigint round-trip mismatches, and one existing
  non-conflicting duplicate GovernorID/KVK group. The duplicate is preserved; no key, unique
  constraint, index, exemption value, KVK value, formula, or procedure rule is changed.
- The operator confirmed that, after Phase 1 deployment, production targets automatically
  transitioned from Draft to Official successfully. This operator-attested live transition
  satisfies the Phase 2C production-evidence prerequisite. Phase 2C implementation still requires
  its own architecture and implementation approval.
- Phase 2A was promoted through mirror PR #237, SQL PR #74, and production PR #544. The operator
  accepted the production Discord smoke on 2026-08-27 after the cache remained schema version 2,
  retained the matching Official KVK 16 publication identity, and exposed all 350 expected rows.
- Phase 2B architecture and its exact bot-only implementation manifest were separately approved on
  2026-08-27. This approval does not approve Phase 2C or Phase 2D implementation.
- The final Phase 2B bot working-tree diff completed its required `Changes + Deep Off` security
  review with zero reportable findings. The SQL repository remained review-only with no diff, so
  the Phase 2B SQL security decision is a documented skip.
- Phase 2B was merged, deployed, and operator accepted on 2026-08-27. Discord smoke passed numeric
  lookup, account selection, fuzzy lookup, public view, exemption, and last-KVK comparison paths.
- Phase 2C architecture, 60-second refresh lease, five-second cold-follower bound, durable Draft
  poll coordination, crash recovery, and exact bot-only manifest were approved on 2026-08-27.
  This approval does not approve Phase 2D.
- Phase 2C was merged through mirror PR #239 and production PR #546, deployed, smoke tested, and
  operator accepted on 2026-08-27 with clear logs. Its final bot `Changes + Deep Off` review
  completed with full coverage and zero reportable findings; the SQL repository remained
  unchanged and was a documented security-review skip.
- Phase 2D architecture and its exact bot-only compatibility manifest were approved on 2026-08-27.
  Phase 2D implementation does not approve Phase 2E automatically.
- Phase 2D was merged through mirror PR #240 and production PR #547, deployed, smoke tested, and
  operator accepted on 2026-08-27. Its exact operational lifecycle log remained compatible.
- The operator promoted the proposed `kvk_state.py` SQL-read extraction into a separately gated
  Phase 2E. Phase 2E requires its own post-Phase-2D architecture audit and implementation approval.
- Phase 2E architecture and its exact bot-only DAL extraction manifest were approved on 2026-08-27.
  The approved implementation retains all public helpers, state values, reasons, warnings, query
  semantics, broad-window behavior, and consumer contracts.

## 4. Objective

Finish the target-specific architecture work deferred from Phase 1 so every target row has one
typed contract, every modern and compatibility output uses one service-owned retrieval and
presentation-input path, cache refresh has one target-domain repository boundary with explicit
outcomes and proved cross-process coordination, and the shared Pass 4 lifecycle is named clearly
enough that it cannot be mistaken for publication state again.

Deliver this as small, reversible slices. Do not turn Phase 2 into a universal cache framework,
rewrite the target formulas, or alter the player command surface.

## 5. Source Deferred Items

These items have been promoted from `docs/reference/deferred_optimisations.md` into this active
pack. Keep their disposition visible until their corresponding slice is deployed and accepted.

### Deferred Optimisation
- Area: `target_utils.py`, `targets_embed.py`, `commands/kvk_targets_card_posting.py`, `kvk/services/kvk_targets_card_service.py`
- Type: architecture
- Description: The modern targets card now has typed publication ownership, but the legacy ID/name lookup and fallback path still duplicates retrieval, last-KVK attachment, response routing, and presentation logic in a large compatibility module. That duplication makes publication-safe output parity harder to maintain.
- Suggested Fix: Make the typed target card service the single target retrieval and presentation-input path for both numeric and name lookups, reduce `target_utils.py` to compatibility routing, and move legacy embed construction onto the same payload and canonical publication display contract while preserving command arguments, selectors, visibility, exemptions, and response behavior.
- Impact: high
- Risk: medium
- Dependencies: Phase 1 target publication deployment and smoke testing complete; retain focused numeric/name lookup, selector, exemption, modern-card, and fallback tests throughout the extraction.

### Deferred Optimisation
- Area: `targets_sql_cache.py`, target maintenance subprocesses, cache refresh orchestration
- Type: architecture
- Description: The target publication cache is atomic, version guarded, cross-KVK safe, and last-known-good aware. Draft hot-read metadata polling is bounded within one process, and a narrow cross-process critical section makes the final disk-version comparison and replacement monotonic, but SQL metadata/rowset fetches can still duplicate across processes and the implementation remains a target-specific root module rather than a reusable single-flight cache repository contract.
- Suggested Fix: Extract a target-domain cache repository with one validated snapshot read API, explicit refresh outcomes, durable poll coordination, and tested cross-process single-flight behavior. Preserve publication identity, last-known-good, fail-closed, subprocess-summary, and no-downgrade behavior before considering any reusable cache abstraction.
- Impact: medium
- Risk: high
- Dependencies: Satisfied by the operator-attested successful production Draft-to-Official
  transition observed after Phase 1 deployment; retain SQL publication version/signature
  monotonicity and atomic JSON replacement.

### Deferred Optimisation
- Area: target row dictionaries in `kvk/dal/kvk_target_publication_dal.py`, `targets_sql_cache.py`, `kvk/services/kvk_targets_card_service.py`, and `target_utils.py`
- Type: refactor
- Description: Publication metadata is typed, while target rows still cross DAL, cache, services, and compatibility output as variant-key dictionaries. Repeated key coercion remains necessary and can hide schema drift or accidental target-value transformations.
- Suggested Fix: Introduce an immutable typed target-row model at the DAL boundary, define explicit cache serialization/deserialization, and confine legacy key aliases to one compatibility adapter. Prove byte-equivalent target values and unchanged exemption and last-KVK calculations with contract fixtures before removing dictionary variants.
- Impact: medium
- Risk: medium
- Dependencies: Phase 1 SQL and bot contracts deployed; capture representative production row shapes without personal data; preserve existing target formula outputs exactly.

### Deferred Optimisation
- Area: shared `kvk_state.py` terminology and KVK lifecycle consumers
- Type: consistency
- Description: The shared `DRAFT`, `ACTIVE`, and `ENDED` resolver correctly represents the Pass 4 fighting lifecycle, but its generic naming previously encouraged target publication consumers to reuse it for unrelated domain state.
- Suggested Fix: Audit all shared-state consumers and consider a compatibility-preserving rename to explicit fighting-lifecycle terminology in a dedicated cross-feature task. Keep resolver thresholds and behavior unchanged, document adapters, and migrate stats alerts, daily overview, history, and leadership review only with full lifecycle regression coverage.
- Impact: medium
- Risk: high
- Dependencies: Target publication separation deployed and stable; separate architecture approval because this affects multiple production lifecycle consumers.

## 6. Candidate Scoring And Batch Rationale

Scoring uses `Priority Score = (Impact + Frequency + Risk Reduction) - Effort`.

| Candidate | Impact | Frequency | Risk reduction | Effort | Score | Decision |
|---|---:|---:|---:|---:|---:|---|
| Immutable typed target-row boundary | 3 | 5 | 3 | 3 | 8 | Phase 2A foundation |
| One service-owned retrieval/presentation-input path | 4 | 4 | 4 | 4 | 8 | Phase 2B after typed rows |
| Target-domain cache repository and cross-process single-flight | 3 | 4 | 4 | 4 | 7 | Phase 2C implementation approved |
| Explicit fighting-lifecycle terminology | 3 | 4 | 3 | 4 | 6 | Phase 2D, isolated due blast radius |
| Extract lifecycle SQL reads behind a KVK DAL | 3 | 4 | 3 | 2 | 8 | Phase 2E after Phase 2D acceptance |

The first three items form one coherent target-data ownership chain. The terminology item scores
lower but remains in this programme because it directly reduces the risk of repeating the defect
that caused Phase 1. It must remain a separate slice because it crosses stats alerts, daily
overview, history, and leadership review. The SQL-read extraction is a separate final slice so the
terminology adapters can be deployed and proved before data-access ownership moves.

Excluded from this batch:

- a universal cache framework: no second proven consumer justifies it;
- a wholesale legacy target rewrite: Phase 2 removes proved duplication incrementally;
- target formula, threshold, exemption, or population redesign: product behavior is fixed;
- command retirement or registration changes: separate command-governance work;
- SQL target-generation redesign or performance tuning: Phase 1 SQL is deployed and verified;
- changing fighting-state thresholds or broad KVK-window semantics: explicitly prohibited.

## 7. Approved Slice Model

### Phase 2A - Immutable Target Row Contract

Introduce one immutable typed target-row model at the SQL DAL boundary. Define explicit cache
serialization/deserialization and a single compatibility adapter for legacy key aliases. Remove
variant-key coercion from downstream services where the typed contract makes it unnecessary.

Phase 2A must:

- map the exact `dbo.v_KVK_TARGETS_FOR_BOT` row shape;
- begin from an audit-confirmed model equivalent to `governor_id`, `governor_name`, `power`,
  `dkp_target`, `kill_target`, `deads_target`, `min_kill_target`, `target_rank`, and `kvk_no`, without
  adding fields not present in the authoritative contract;
- distinguish required, optional, nullable, integer, decimal, text, and UTC fields explicitly;
- retain all current target values without rounding or formula changes;
- retain current cache schema compatibility unless the audit proves a schema bump is required;
- retain dictionary output only at named compatibility boundaries;
- include sanitized contract fixtures and round-trip tests;
- avoid changing command, renderer, target-publication SQL object, or cache-refresh behavior;
- deliver the separately approved `dbo.EXEMPT_FROM_STATS.GovernorID bigint NOT NULL` companion
  migration without changing exemption rows, rules, consumers, indexes, constraints, or KVK types.

### Phase 2B - Single Retrieval And Presentation-Input Path

Make `kvk/services/kvk_targets_card_service.py`, or an audit-approved target service beside it, the
single owner of target retrieval, last-KVK attachment, exemption/no-target resolution,
publication display input, and renderer-independent payload construction for numeric and name
lookups.

Phase 2B must:

- reduce `target_utils.py` to lookup/autocomplete/interaction compatibility routing;
- move remaining target SQL reads out of `target_utils.py` into the target DAL and move stable
  nested Discord selector/view classes into the established `ui/views/` boundary where the audit
  proves this can be done without interaction drift;
- make modern card and fallback embed consume the same typed payload and canonical publication
  display contract;
- remove duplicate last-KVK and target-value mapping where behavior is proved equivalent;
- preserve account selection, name autocomplete, direct Governor ID, exemptions, missing-target,
  invalid-ID, image failure, and fallback behavior;
- preserve public/ephemeral response choices and all decorators;
- keep Discord types out of the service and SQL out of commands/views;
- remove compatibility code only after focused tests prove no remaining caller needs it.

### Phase 2C - Target Cache Repository And Single-Flight Coordination

Extract the target-specific cache implementation from the root compatibility module into a
target-domain repository/cache boundary with one validated snapshot read API and explicit refresh
outcomes.

Phase 2C must not start until the audit records either:

- one real production Draft-to-Official transition under the Phase 1 cache contract; or
- operator approval of a bounded substitute evidence plan when a real transition is not available.

This evidence gate is satisfied: on 2026-08-27 the operator attested that the deployed Phase 1
system automatically transitioned production targets from Draft to Official successfully.

Phase 2C must:

- keep `targets_sql_cache.py` as a thin compatibility façade until all callers are migrated;
- define typed outcomes such as reused, refreshed, retained last-known-good, rejected mismatch,
  unavailable, and failed closed;
- prevent duplicate SQL metadata/rowset fetches across processes through a bounded durable
  coordination mechanism;
- never hold a cross-process lock across unbounded work without an expiry/recovery contract;
- preserve publication identity, monotonic version/signature, no downgrade, cross-KVK rejection,
  atomic replacement, empty-rowset protection, and last-known-good semantics;
- preserve explicit maintenance refresh and subprocess summary behavior;
- avoid a generic cache abstraction until another proven consumer exists;
- include crash, stale-lock, timeout, concurrent refresh, restart, and rollback tests.

Approved Phase 2C implementation manifest:

- create `kvk/models/kvk_target_cache.py`;
- create `kvk/target_cache_repository.py`;
- create `tests/test_kvk_target_cache_repository.py`;
- create `tests/test_targets_sql_cache_subproc.py`;
- modify `targets_sql_cache.py`, `target_utils.py`, `kvk/dal/kvk_targets_dal.py`,
  `tests/test_targets_sql_cache_publication.py`, `tests/test_target_utils_governor_lookup.py`,
  `README-DEV.md`, `docs/kvk/target_publication_contract.md`, and this task pack;
- review only the publication DAL/service, card service, processing/import handoff, atomic-write,
  maintenance-worker, process-identity, command, view, renderer, and fallback paths;
- create, modify, or delete no SQL file, migration, command registration, configuration, startup
  hook, renderer, or Phase 2D fighting-lifecycle consumer.

### Phase 2D - Explicit Fighting-Lifecycle Terminology

Audit and, only after separate architecture approval, introduce compatibility-preserving names
that make the shared resolver's Pass 4 fighting meaning explicit.

Phase 2D must:

- keep the persisted/runtime values `DRAFT`, `ACTIVE`, and `ENDED` unchanged;
- keep matchmaking, Pass 4, and end thresholds unchanged;
- keep `is_currently_kvk()` broad-window behavior unchanged;
- preserve existing public helpers through documented adapters during migration;
- migrate consumers in small, reviewable groups if a single rename is too broad;
- prove Pre-KVK stats alerts continue until Pass 4 and live alerts begin at Pass 4;
- prove daily overview timing, history finalisation, and leadership-review finalisation are
  unchanged;
- avoid importing target publication terminology into the shared lifecycle module;
- stop without implementation if the audit finds the rename cost exceeds its safety benefit and
  present a documentation/type-alias alternative for approval.

Approved Phase 2D implementation manifest:

- modify `kvk_state.py`, `stats_alerts/kvk_meta.py`, `services/kvk_history_service.py`,
  `leadership_player_review/service.py`, `kvk/services/kvk_targets_card_service.py`,
  `kvk/target_cache_repository.py`, focused lifecycle/target tests, `README-DEV.md`,
  `docs/kvk/target_publication_contract.md`, and this task pack;
- create `tests/test_stats_alerts_fighting_lifecycle.py` and
  `tests/test_daily_kvk_overview_lifecycle.py`;
- preserve `State`, `resolve_kvk_scan_state()`, and `get_kvk_context_today()` as documented
  compatibility adapters while making explicit fighting names canonical;
- review only broad-window, command, import, publication, renderer, registration, SQL, and
  persistence paths not requiring a compatibility handoff;
- create, modify, or delete no SQL file, migration, command registration, cache schema, renderer,
  configuration, or player target rule.

### Phase 2E - KVK Lifecycle DAL Extraction

After Phase 2D is deployed and accepted, audit and separately approve extracting the SQL reads from
`kvk_state.py` into a narrow KVK lifecycle DAL while leaving the public compatibility façade and
pure fighting resolver in place.

Phase 2E must:

- preserve the exact `dbo.KVK_Details`, `dbo.ProcConfig`, and `dbo.KingdomScanData4` queries,
  parameters, retry/connection helpers, integer/date coercion, warnings, and fallback order unless
  a separately approved finding proves a correction is required;
- preserve every fighting value, reason code, Pass 4/end boundary, broad-window rule, returned
  context/detail shape, and Phase 2D compatibility adapter;
- place SQL execution and row mapping under `kvk/dal/` without adding a general lifecycle or cache
  framework;
- introduce no SQL repository change unless a new exact finding receives separate approval;
- include DAL mapping/failure tests plus the complete Phase 2D lifecycle regression suite;
- remain blocked until Phase 2D deployment and operator smoke are accepted and its architecture
  and exact PR-sized manifest receive separate approval.

Approved Phase 2E implementation manifest:

- create `kvk/dal/kvk_lifecycle_dal.py` and `tests/test_kvk_lifecycle_dal.py`;
- modify `kvk_state.py`, `tests/test_kvk_state_open_window.py`, `README-DEV.md`,
  `docs/kvk/target_publication_contract.md`, and this task pack;
- review only stats-alert, daily-overview, history, leadership-review, target service/cache,
  honor-import, admin/stats, command-registration, and complete Phase 2D lifecycle consumers;
- create, modify, or delete no SQL file, migration, command, renderer, cache schema, configuration,
  fighting value, reason, threshold, or player target rule.

## 8. Scope

### In Scope

- the four promoted deferred items and only the compatibility cleanup needed to complete them;
- typed target row mapping, serialization, adapters, and fixtures;
- service/DAL/cache ownership improvements;
- modern/fallback payload parity and bounded Discord smoke;
- target-specific concurrency and restart safety;
- compatibility-preserving fighting-lifecycle terminology;
- a separately gated KVK lifecycle DAL extraction after Phase 2D acceptance;
- focused and broad regression coverage;
- documentation, deferred-register closeout, deployment, smoke, and rollback evidence.

### Out Of Scope

- any target calculation, source population, weight, cap, threshold, exemption, or spreadsheet
  export change;
- changing the Phase 1 SQL publication schema, procedure semantics, force-republish control, or
  publication-state resolver without a new finding and explicit approval;
- changing `/kvk targets` arguments, options, decorators, permissions, channels, visibility,
  account-selection UX, command path, or registration;
- adding a slash command, operator command, button, select, or modal;
- changing shared fighting-state values or thresholds;
- redesigning stats alerts, daily overview, history, or leadership review;
- a generic repository/cache framework or unrelated KVK cleanup;
- SQL writes during audit;
- production changes before the applicable slice is reviewed and approved.

## 9. Skills To Use

| Skill | Decision | Purpose |
|---|---|---|
| `k98-architecture-scope` | use | Audit layer ownership, compatibility boundaries, caches, persistence, slice dependencies, and approval gates. |
| `k98-discord-command-feature` | use | Preserve the existing `/kvk targets` interaction, visibility, renderer, and fallback behavior while consolidating internals. |
| `k98-sql-validation` | use | Revalidate the exact deployed view/table/procedure/result shape before typed mapping or cache work; SQL modification is not assumed. |
| `k98-test-selection` | use | Select focused and broad tests per slice, including cache/restart/concurrency risks. |
| `k98-deferred-optimisation-capture` | use | Close the four promoted items and capture only genuinely new, out-of-scope non-security debt. |
| `k98-pr-review` | use | Review each completed slice independently before handoff. |
| `k98-promotion-check` | use | Verify promotion, deployment, cache compatibility, smoke, and rollback per slice. |
| `k98-security-review-routing` | use | Record the docs-only preparation skip and final per-repository slice decisions; never start a standard or deep audit. |

## 10. Security Review Decision

This task-pack preparation is a documented skip: only Markdown planning, delivery-status, archive,
and deferred-register files change; no runtime, SQL, config, dependency, permission, input,
network, filesystem, deployment, or persistence behavior changes.

Provisional runtime-slice decisions:

| Repository | Decision | Target | Expected setup | Evidence |
|---|---|---|---|---|
| Bot | Changes review | Each final approved Phase 2A/2B/2C/2D/2E base..head separately | `Changes + Deep Off` with `$codex-security:security-diff-scan` | Phase 2B and Phase 2C completed separately with zero reportable findings |
| SQL | Changes review for the approved Phase 2A companion migration; documented skip for later slices while SQL remains unchanged | SQL working-tree diff against `b26c19c5ff4ce9f123f24201fc17fbf8c342f87e` | `Changes + Deep Off` with `$codex-security:security-diff-scan` | Migration, rollback, schema snapshot, validation, and final scan artifacts |

The Phase 2A SQL companion is separately approved and uses its own SQL Git target and SQL Changes
review with `Changes + Deep Off`. Any additional SQL change still requires fresh approval. Do not
combine bot and SQL Git histories. A standard or deep codebase audit is not approved.

Security focus for runtime diffs:

- cross-KVK or cross-publication substitution;
- malformed cache deserialization or fail-open defaults;
- lock expiry/recovery and denial-of-service risk;
- SQL result-shape confusion;
- public/private output regressions;
- logs containing unnecessary player-level data;
- subprocess or maintenance-path behavior.

## 11. Mandatory Workflow And Approval Gates

1. Audit both repositories and the deployed Phase 1 contracts. Make no edits in the first
   response.
2. Return every item in the Step 1 Required Output and stop for approval.
3. After audit approval, present the final target architecture and exact Phase 2A PR-sized plan;
   stop for approval.
4. Implement and validate Phase 2A only.
5. Run separate bot and SQL Changes reviews with Deep Off, complete `k98-pr-review` for both Git
   targets, prepare the companion PRs, and stop for merge/promotion approval.
6. Complete promotion, deployment, and operator smoke before starting Phase 2B.
7. Repeat the approval/review/promotion cycle independently for Phase 2B, Phase 2C, Phase 2D, and
   Phase 2E.
8. Treat the Phase 2C production-transition evidence gate as satisfied by the operator-attested
   successful live Draft-to-Official transition; do not start implementation without separate
   Phase 2C approval.
9. Phase 2D implementation approval was recorded on 2026-08-27.
10. Do not start Phase 2E implementation until Phase 2D is deployed and accepted and Phase 2E has
    its own architecture and exact-manifest approval.
11. Close the programme only after all accepted slices are deployed, smoke tested, documented, and
    removed from the active deferred backlog.

No one-pass implementation is approved. Approval of this pack does not approve all slice diffs in
advance.

## 12. Step 1 Required Output

Return:

1. Phase 1 Deployed Baseline And Contract Verification
2. Current `/kvk targets` Numeric, Name, Account-Selection, Modern, And Fallback Route Map
3. Duplicate Retrieval, Last-KVK, Exemption, Response, And Presentation Responsibility Map
4. Current SQL Row Shape And Every Dictionary Key/Alias Variant
5. Current Typed Publication Metadata And Untyped Target-Row Boundary Map
6. Current Cache API, Callers, Processes, Locks, Polling, Persistence, And Restart Map
7. Current SQL Metadata/Rowset Fetch Concurrency And Failure Map
8. Current Shared Fighting-State Consumer Map
9. Proposed Immutable `TargetRow` Contract And Serialization/Compatibility Rules
10. Proposed Single Service-Owned Retrieval And Presentation-Input Contract
11. Proposed Target Cache Repository API And Explicit Refresh Outcomes
12. Cross-Process Single-Flight, Lock Expiry, Crash Recovery, And Failure Matrix
13. Proposed Fighting-Lifecycle Naming And Compatibility Plan
14. Exact Phase 2A/2B/2C/2D/2E Review, Modify, Create, And Delete Manifests
15. Candidate Scores, Dependencies, Exclusions, And Recommended Slice Order
16. Focused, Broader, Manual, Concurrency, Restart, And Output-Parity Test Selection
17. Provisional Bot And SQL Security Decisions And Exact Targets
18. Per-Slice Deployment, Cache Compatibility, Smoke, And Rollback Plan
19. Refactor Findings And Structured New Deferred Candidates
20. Approval Questions
21. Explicit Stop Point

The audit must specifically answer:

- which exact dictionary variants exist and which are genuine compatibility requirements;
- whether typed rows should enter the cache directly or be serialized at a narrower boundary;
- whether cache schema version 2 can remain compatible;
- which layer should own exemption and last-KVK attachment;
- how both numeric and name lookups will reach the same service without changing interaction flow;
- which fallback embed builder remains canonical and which duplicate can be retired;
- how cache single-flight works across the main bot, maintenance subprocesses, and concurrent
  command requests;
- how abandoned/stale coordination state recovers without allowing version downgrade;
- whether a real Draft-to-Official production transition has been observed;
- whether Phase 2C must remain blocked pending that evidence;
- which `kvk_state.py` names are ambiguous and every consumer affected by a compatibility rename;
- why shared fighting thresholds and all non-target timing remain unchanged;
- why no SQL modification is expected, or the exact new finding requiring separate approval;
- why command registration and command count remain unchanged.

## 13. Architecture Targets

| Concern | Target ownership |
|---|---|
| SQL target/publication rows | Existing deployed SQL Phase 1 objects; review-only unless separately approved |
| SQL mapping | `kvk/dal/kvk_target_publication_dal.py` |
| Immutable target row | New or audit-approved model under `kvk/models/` |
| Publication metadata/state | Existing `kvk/models/kvk_target_publication.py` and `kvk/services/kvk_target_publication_service.py` |
| Target payload orchestration | `kvk/services/kvk_targets_card_service.py` or one adjacent target service chosen during audit |
| Cache implementation | Target-domain repository/cache module under `kvk/`; no universal framework |
| Root compatibility | Thin `targets_sql_cache.py` and `target_utils.py` façades only while callers migrate |
| Modern output | Existing card renderer/posting path consumes the canonical payload |
| Fallback output | One canonical embed adapter consumes the same payload |
| Interaction/account selection | Existing command/view adapters unchanged except thin service handoff |
| Shared fighting lifecycle | `kvk_state.py`, with compatible explicit naming and unchanged semantics |
| Tests | Focused model/DAL/service/cache/output/state tests under `tests/` |

## 14. Expected File Manifest

The Step 1 audit must replace this expected manifest with exact per-slice manifests before any
implementation.

### Bot Review

- `target_utils.py`
- `targets_sql_cache.py`
- `targets_embed.py`
- `proc_config_import.py`
- `commands/kvk_cmds.py`
- `commands/kvk_targets_card_posting.py`
- `ui/views/kvk_personal_views.py`
- `account_picker.py`
- `kvk/dal/kvk_target_publication_dal.py`
- `kvk/dal/kvk_targets_dal.py`
- `kvk/models/kvk_target_publication.py`
- `kvk/models/kvk_targets_card.py`
- `kvk/services/kvk_target_publication_service.py`
- `kvk/services/kvk_targets_card_service.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `kvk_state.py`
- all fighting-state consumers found by `rg`
- all focused target/cache/state tests
- `docs/kvk/target_publication_contract.md`
- `docs/reference/deferred_optimisations.md`
- this task pack and its chat starter

### Expected Phase 2A Modify/Create

- modify `kvk/dal/kvk_target_publication_dal.py`
- modify `targets_sql_cache.py`
- modify `kvk/services/kvk_targets_card_service.py`
- modify `target_utils.py` only for the typed compatibility adapter needed by this slice
- create `kvk/models/kvk_target_row.py`, unless the audit proves an existing model is the better
  canonical owner
- create or update focused typed-row contract tests

### Expected Phase 2B Modify

- `target_utils.py`
- `targets_embed.py`
- `commands/kvk_targets_card_posting.py`
- `kvk/services/kvk_targets_card_service.py`
- `kvk/models/kvk_targets_card.py` only if the canonical payload must evolve compatibly
- focused lookup, service, embed, renderer, posting, account-selection, and fallback tests

### Expected Phase 2C Modify/Create

- create one target-domain cache repository/cache module under `kvk/`, exact path chosen during
  audit
- reduce `targets_sql_cache.py` to a compatibility façade
- update target DAL/service and maintenance/import callers only where required
- update `proc_config_import.py` only if the handoff changes; preserve its autocommit restoration
- create focused cache-repository, concurrency, subprocess, crash, restart, and compatibility tests

### Expected Phase 2D Modify

- `kvk_state.py`
- only the exact stats-alert, daily-overview, history, leadership-review, target diagnostic, and
  tests/docs consumers proved by search
- no SQL files

### Expected Phase 2E Modify/Create

- create a narrow lifecycle DAL under `kvk/dal/`, exact name chosen by the Phase 2E audit;
- modify `kvk_state.py` only to delegate its existing SQL reads and row mapping while retaining the
  Phase 2D public façade and pure resolver;
- add focused DAL mapping, missing/malformed row, SQL failure, ProcConfig fallback, and compatibility
  tests;
- review all Phase 2D consumers and tests; modify them only if required to preserve injection or
  monkeypatch boundaries;
- create, modify, or delete no SQL file, migration, command, renderer, cache schema, config, or
  state value.

### Phase 2A SQL Companion Modify/Create

- create
  `migrations/20260827_001_standardize_exempt_from_stats_governor_id_bigint.sql`;
- create
  `migrations/rollback/20260827_001_standardize_exempt_from_stats_governor_id_bigint_rollback.sql`;
- modify `sql_schema/dbo.EXEMPT_FROM_STATS.Table.sql`;
- review-only: `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql`,
  `sql_schema/dbo.sp_Prep_TargetTable.StoredProcedure.sql`,
  `sql_schema/dbo.sp_Prep_ExcelExportTable.StoredProcedure.sql`, and
  `sql_schema/dbo.usp_GetLeadershipPlayerKvkHistory.StoredProcedure.sql`;
- no procedure, view, index, constraint, data-row, `KVK_NO`, `Exempt`, or `ProcConfig` change.

### Remaining SQL Review Only

- `sql_schema/dbo.KVK_Target_Publication.Table.sql`
- `sql_schema/dbo.KVK_Target_Publication_Row.Table.sql`
- `sql_schema/dbo.v_KVK_TARGETS_FOR_BOT.View.sql`
- `sql_schema/dbo.v_TARGETS_FOR_UPLOAD.View.sql`
- `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql`
- `migrations/20260825_001_kvk_target_publication_provenance.sql`

After the approved Phase 2A companion, the expected SQL modify/create/delete manifest for Phase
2B, 2C, 2D, and 2E remains `none`. Any additional proposed SQL change requires a fresh exact
manifest, migration/rollback plan, separate approval, separate PR, and SQL Changes review.

## 15. Invariants And Failure Rules

- Missing or malformed publication proof remains Unverified, never Official.
- Typed parsing fails closed at the DAL/cache boundary; renderers do not guess.
- Compatibility aliases cannot override canonical typed values.
- Serialization and deserialization are deterministic and round-trip without target-value change.
- A previous KVK never becomes the requested current KVK through a compatibility adapter.
- An Official cache never downgrades because another process fetched older Draft metadata.
- A failed, empty, mismatched, or partial refresh never replaces a matching last-known-good cache.
- Single-flight coordination has a bounded wait and recoverable stale-owner path.
- Routine later scans and Pass 4 do not refresh or republish Official targets.
- A service or renderer failure retains the existing image-to-embed fallback behavior.
- Fighting state remains Draft before Pass 4, Active from Pass 4, and Ended after KVK end.
- Publication state and progress state remain distinct typed concepts.
- No compatibility path may silently reintroduce shared fighting state as publication state.

## 16. Test Selection

Use `k98-test-selection` for each final diff. At minimum, consider and record happy, negative,
regression, permission, restart/persistence, cache-safety, concurrency, and output-shape coverage.

### Phase 2A Focus

- exact SQL-row-to-model mapping;
- nullable/malformed/extra/missing columns;
- legacy alias compatibility at one boundary;
- cache round-trip and schema compatibility;
- exact integer/decimal/target values and exemption fields;
- publication row-count and KVK consistency.

Likely focused files:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_target_publication_dal.py tests\test_kvk_targets_card_service.py tests\test_targets_sql_cache_publication.py tests\test_target_utils_result_unwrap.py
```

### Phase 2B Focus

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_target_utils_governor_lookup.py tests\test_mykvktargets.py tests\test_kvk_targets_card_service.py tests\test_kvk_targets_card_posting.py tests\test_kvk_targets_card_renderer.py tests\test_targets_embed_publication.py
```

Cover direct ID, name, autocomplete/selection, registered accounts, exempt, invalid, no-target,
Draft, Official, Historical, Unverified, image success, image failure, embed fallback, and current
visibility/permission behavior.

### Phase 2C Focus

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_targets_sql_cache_publication.py tests\test_kvk_target_publication_dal.py tests\test_proc_config_import_phase2.py
```

Add deterministic multi-process/concurrent tests for one fetch, version race, stale coordination,
owner crash, timeout, explicit maintenance refresh, restart, empty rowset, SQL failure, matching
last-known-good, cross-KVK rejection, and fail-closed no-cache behavior.

### Phase 2D Focus

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_state_open_window.py tests\test_stats_alerts_state.py tests\test_kvk_history_service.py tests\test_leadership_player_review.py tests\test_kvk_target_publication.py
```

Also run `tests/test_stats_alerts_fighting_lifecycle.py`,
`tests/test_daily_kvk_overview_lifecycle.py`, `tests/test_kvk_targets_card_service.py`,
`tests/test_kvk_target_cache_repository.py`, and `tests/test_targets_sql_cache_publication.py`.

### Phase 2E Focus

Reuse the complete Phase 2D focus and add the exact DAL test file approved by the Phase 2E audit.
Cover exact query ownership, named/positional row mapping, malformed and absent KVK details,
ProcConfig fallback, maximum-scan failure, connection failure, and unchanged adapter outputs.

### Per-PR Gates

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run `scripts/analyse_pytest_log_noise.py` for the broad validation/promotion gate. Command
registration is expected to remain unchanged, but the validator provides deterministic proof.
When renderer layout, fonts, or wording change, render and inspect representative Draft, Official,
Historical, Unverified, long-name, and fallback samples. If no renderer change occurs in a slice,
record why visual regeneration is unnecessary.

## 17. Deployment, Smoke, And Rollback

Phase 2B, 2C, 2D, and 2E are expected to be bot-only and may deploy against the already verified Phase
1 SQL contract. Phase 2A also has the approved `EXEMPT_FROM_STATS.GovernorID` SQL companion. For
every slice:

1. revalidate the exact deployed SQL contract used by the bot;
2. complete focused and broad bot validation;
3. complete the bot Changes review with Deep Off and `k98-pr-review`;
4. promote the reviewed branch to the private production repository;
5. complete `k98-promotion-check`;
6. deploy only from production `main`;
7. preserve or deliberately migrate the current cache as specified by the slice;
8. smoke direct-ID and account-selection `/kvk targets`, modern image, fallback embed, publication
   state/source wording, target values, and a negative path;
9. confirm imports can still run `dbo.sp_TARGETS_MASTER` with restored autocommit behavior;
10. retain enough logs to prove cache decision and publication identity without player payloads.

For Phase 2A, deploy and verify the approved SQL migration first, then deploy the bot. The bot is
compatible with both the old float and new bigint column, but SQL-first keeps the intended
standardisation order explicit. Never deploy a bot that depends on an undeployed SQL contract.

Rollback is per slice:

- revert the bot to the previous production commit;
- retain the existing Phase 1 SQL publication objects;
- preserve a valid matching cache unless the slice explicitly changed its schema;
- if cache compatibility changed, keep the documented old/new cache backup and rebuild path;
- do not roll back by relabelling unverified data or republishing Official targets;
- if a SQL change was separately approved, follow its independent migration rollback/forward-fix
  classification.

## 18. Acceptance Criteria

- [ ] Every target row crosses the primary DAL/service boundary as one immutable typed model.
- [ ] Legacy row aliases exist only in one named compatibility adapter.
- [ ] Cache serialization/deserialization is explicit, deterministic, and regression tested.
- [ ] Target formulas and values are unchanged byte-for-byte or value-for-value as appropriate.
- [ ] Numeric and name lookup use the same service-owned retrieval and presentation-input path.
- [ ] Exemption, last-KVK, no-target, and progress ownership is unambiguous.
- [ ] Modern card and fallback embed use the same payload and canonical publication display copy.
- [ ] `target_utils.py` and `targets_sql_cache.py` are thin compatibility façades or their retained
  responsibilities are explicitly justified.
- [ ] Cache refresh exposes typed outcomes and one validated snapshot API.
- [ ] Cross-process fetch coordination is bounded, crash recoverable, and deterministic.
- [ ] Publication identity, atomic replacement, no downgrade, cross-KVK rejection,
  last-known-good, and fail-closed behavior are preserved.
- [x] Phase 2C evidence prerequisite is satisfied by the operator-attested successful production
  Draft-to-Official transition observed after Phase 1 deployment.
- [ ] Shared state terminology communicates fighting-lifecycle meaning without changing values or
  thresholds.
- [ ] Stats alerts, daily overview, history, and leadership review retain their Phase 1 behavior.
- [ ] Phase 2E moves lifecycle SQL reads behind a narrow DAL without changing queries, fallback,
  mappings, values, reasons, thresholds, or public helpers.
- [ ] `/kvk targets` arguments, decorators, permissions, channel, visibility, account selection,
  command counts, and registration are unchanged.
- [ ] No new direct SQL exists in commands or views.
- [ ] SQL changes remain limited to the separately audited and approved Phase 2A
  `EXEMPT_FROM_STATS.GovernorID` companion migration.
- [ ] Focused, full, cache/restart/concurrency, output, and manual smoke evidence is recorded.
- [ ] Each runtime slice has a separate bot Changes review with Deep Off.
- [ ] No standard or deep codebase audit is started without explicit operator request.
- [ ] The four source deferred items are closed only after their slices are deployed and accepted;
  the operator-promoted Phase 2E is closed only after its independent deployment and smoke.
- [ ] Any new non-security debt is captured structurally; security findings remain in the private
  security workflow.

## 19. Required Delivery Output Per Slice

1. Summary
2. Exact File Manifest
3. Architecture And Compatibility Decisions
4. SQL Contract Validation And SQL Change Status
5. Helpers Reused
6. Target Row/Service/Cache/State Contract Changes As Applicable
7. Refactor Findings
8. Test Selection And Results
9. Security Review Decision, Exact Target, And Evidence
10. Deployment, Cache, Smoke, And Rollback Results
11. Deferred Item Disposition
12. Next Slice Readiness Or Blocker

For the first Phase 2 implementation PR, include the local Phase 1 deployment documentation,
archived Phase 1 pack/starter, this Phase 2 pack/starter, and deferred-register promotion changes.

## 20. Explicit Stop Point

The first response to this task is audit and scope only. Do not edit code, SQL, migrations, tests,
or documentation. Stop after the Step 1 Required Output and wait for approval. Do not interpret
approval of one slice as approval of the next, including Phase 2D approval as Phase 2E approval.

## 21. PR Summary Template

```md
## Summary

- Deliver KVK Targets Quality Phase 2<slice> without changing target values or the command surface.
- Preserve the deployed Phase 1 publication, cache-safety, and shared fighting-lifecycle contracts.

## Changes

- <typed-row, service consolidation, cache repository, or terminology changes for this slice>
- Include the local Phase 1 deployment and Phase 2 planning documentation in the first Phase 2 PR.

## Tests

- <focused commands and results>
- <broad gates and results>
- <manual/production smoke plan or result>

## Security Review

- Bot decision: `Changes review`.
- Bot target: `<exact base..head>`.
- Setup: `Changes + Deep Off`.
- Evidence: `<retained result>`.
- SQL decision: `documented skip` when review-only and unchanged; otherwise record the separately
  approved SQL `Changes + Deep Off` target and evidence.

## Deferred Optimisations

- <source item closed, retained pending later slice, or new structured item>

## Risk / Rollback

- <slice-specific compatibility, cache, deployment, and rollback statement>
```
