# Codex Task Pack - KVK Target Publication State Separation

> Canonical implementation pack for separating KVK target publication status from the shared
> KVK fighting-state lifecycle.

## 1. Task Header

- Task name: `Separate KVK target publication state from KVK fighting state`
- Date: `2026-08-25`
- Owner/context: `Chris Watts / KD98; follow-up to KVK 16 target output showing DRAFT after matchmaking targets were fixed`
- Task type: `feature`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

For the security-routing decision, also read the active repository `AGENTS.md`, the root and any
applicable nested `SECURITY.md` files, and the `k98-security-review-routing` skill. `SECURITY.md`
supplies policy and threat-model context; it does not select or launch a scan.

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`. At minimum, follow any references it identifies for:

- project engineering and coding execution standards;
- SQL validation and deployment;
- Discord command/output changes;
- testing standards;
- cache and persistence safety;
- deferred optimisation capture;
- PR review and promotion.

Also review these task-specific records where present:

- `docs/task_packs/archive/Codex Task Pack - High Priority KVK State Fix.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History.md`
- the matching chat starter for this task pack;
- current KVK target, state, stats-alert, history, and leadership-review tests.

For SQL-facing work, validate schema, procedures, views, migrations, rollback requirements,
`ProcConfig`, deployment rules, and current production contracts against:

`C:\K98-bot-SQL-Server`

In the SQL repository, read and follow:

- its active `AGENTS.md` and `SECURITY.md` files;
- `docs/SQL_RELEASE_CHECKLIST.md`;
- `docs/SQL_PROMOTION_GUIDE.md`;
- the current migration and rollback conventions;
- the current `sql_schema` definitions for all affected objects.

Do not treat the bot repository's exported SQL snapshots as more authoritative than the SQL
repository.

## 3. Objective

Make `/kvk targets` accurately show whether targets are **Draft**, **Official**, **Historical**, or
**Unverified** based on the target output's persisted source scan, rather than reusing the shared
Pass 4 fighting state. Official targets must be proved as having been successfully produced from
the configured matchmaking scan and must remain fixed as later kingdom scans progress.

Preserve the existing shared KVK fighting-state behaviour for stats alerts, KVK history,
leadership review, and all other consumers. Add a durable SQL publication/provenance contract,
consume it through the bot's DAL/service/cache layers, and update both modern and fallback target
outputs.

## 4. Background

The current shared KVK state is `DRAFT`, `ACTIVE`, or `ENDED`. Its practical meaning is the fighting
lifecycle:

- `DRAFT` before `PASS4_START_SCAN`;
- `ACTIVE` from `PASS4_START_SCAN` through `KVK_END_SCAN`;
- `ENDED` after `KVK_END_SCAN`.

That state is valid for features such as the Pre-KVK versus live-KVK stats alert transition and
historical finalisation. It is not the correct lifecycle for KVK targets.

The target-generation SQL already has a separate business rule:

1. use the configured `MATCHMAKING_SCAN` when it exists and has been imported;
2. otherwise use `DRAFTSCAN`, bounded by the latest available scan;
3. build the target output from the selected scan.

Targets are power-based. Once target generation successfully uses the matchmaking scan, the
player powers and derived targets are fixed for that KVK. Later scans, including the Pass 4 opening,
must not convert or recalculate them from current power.

The current bot loses this distinction:

- `targets_sql_cache.py` copies `get_kvk_context_today()["state"]` into cache `_meta.state` and each
  row's `TargetState`;
- the modern target service reads that cache state into `source_state`;
- the modern card footer renders `State DRAFT`, `State ACTIVE`, or `State ENDED`;
- the legacy/fallback embed maps the same values to Draft, Active, or Ended target wording;
- `_cache_might_be_stale()` primarily treats a `DRAFT` cache as refreshable, coupling cache
  invalidation to the fighting lifecycle;
- the modern payload's `target_state` describes progress/result state, while `source_state`
  describes publication state, creating an avoidable naming collision.

For KVK 16, the observed values were:

```text
MATCHMAKING_SCAN = 1059
MAX(kingdomscandata4.ScanOrder) = 1060
PASS4_START_SCAN = 1087
KVK_END_SCAN = 1197
```

The displayed target values were already fixed from matchmaking scan 1059, but the shared resolver
correctly returned `DRAFT` for the fighting lifecycle because scan 1060 is before Pass 4 scan 1087.
The target output therefore displayed the wrong business meaning even though the shared state
itself was behaving as designed.

A second provenance risk also exists: `dbo.v_TARGETS_FOR_UPLOAD` exposes target rows but does not
currently prove to the bot which KVK and source scan produced those rows. The Python cache stamps
the current KVK context onto the returned rows. A stale or mismatched view could therefore be
mislabelled as current data unless the publication contract is strengthened.

## 5. Scope

### In Scope

#### Target publication domain

- Add a target-specific publication state with these canonical internal values:
  - `DRAFT`
  - `OFFICIAL`
  - `HISTORIC`
  - `UNKNOWN`
- Display `UNKNOWN` to users as **Unverified**, not as Official or Active.
- Define and centralise state resolution, reason codes, validation, and display wording.
- Keep publication state separate from target-progress/result state.
- Rename or compatibly evolve ambiguous model fields so the distinction is explicit:
  - publication state: Draft / Official / Historical / Unknown;
  - progress/result state: complete / target review / no target / exempt / invalid.

#### SQL publication and provenance contract

- Audit the existing target-generation flow in `dbo.sp_TARGETS_MASTER` and all called procedures.
- Add or reuse a durable SQL object that records the successful publication for each KVK.
- Record the actual applied source scan and whether it came from `DRAFTSCAN` or
  `MATCHMAKING_SCAN`.
- Record enough metadata to prove that the bot-facing rows and publication record refer to the same
  KVK and publication.
- Publish metadata only after target generation succeeds and target rows are available.
- Keep the bot-facing rowset and publication metadata transactionally consistent, or provide an
  equivalent single-read consistency guarantee.
- Preserve fixed official targets after matchmaking. Later scan progression must not change the
  official source scan or silently replace the official target set.
- Provide a controlled, logged, versioned exception path only if the audit proves an explicit
  operator republish capability is necessary. It must default to no republish and must not create a
  new player-facing command.
- Add the required dated SQL migration, schema snapshots, validation queries, and rollback posture.

#### Bot DAL, service, cache, and persistence

- Read target publication metadata through a DAL/repository boundary.
- Build a typed publication metadata model and pure resolver.
- Change the target cache identity/signature to use publication provenance rather than the shared
  KVK fighting state.
- Persist publication state, reason, KVK number, source scan, source type, publication timestamp,
  row count, and publication version/signature in cache metadata.
- Preserve atomic cache writes and last-known-good behaviour for transient read failures.
- Prevent an older KVK's cached targets from being presented as the current KVK's targets.
- Refresh Draft targets when a successful Official publication appears.
- Refresh an Official target cache only for a new KVK or an explicitly different publication
  version/signature, not because Pass 4 opens or later scans arrive.
- Derive Historical display state from a proved Official publication plus the unchanged shared KVK
  ended state; do not require target regeneration at KVK end.
- Separate target publication time from cache refresh time in metadata and display.
- Migrate, invalidate, or safely rebuild legacy `PLAYER_TARGETS_CACHE` content at deployment.

#### Discord output

- Update the modern visual target card to show the target publication state clearly.
- Update the legacy/fallback target embed to use the same publication state and wording.
- Display the proved source in concise user-facing language, for example:

```text
DRAFT      Draft targets — based on draft scan 1058 and may change
OFFICIAL   Official targets — fixed from matchmaking scan 1059
HISTORIC   Historical targets — fixed from matchmaking scan 1059
UNKNOWN    Target status unverified — source scan could not be confirmed
```

- Ensure missing, malformed, or legacy state never defaults to Official.
- Preserve existing target values, last-KVK comparisons, account selection, exemptions, command
  permissions, response visibility, and image-to-embed fallback behaviour.
- Keep `/kvk targets` command registration and options unchanged.

#### Regression protection

- Prove the shared KVK fighting state remains unchanged.
- Prove Pre-KVK stats alerts continue until Pass 4 opens.
- Prove live KVK stats alerts still begin at Pass 4, not at matchmaking.
- Prove the daily KVK overview and broad `is_currently_kvk()` window remain based on matchmaking
  through KVK end.
- Prove KVK history and leadership-review finalisation still require the shared state to be Ended.
- Add focused unit, integration, cache, renderer/output-shape, restart/persistence, and SQL smoke
  coverage.

#### Documentation and rollout

- Document the difference between:
  - broad KVK window;
  - fighting state;
  - target publication state.
- Document target publication source-of-truth, cache signature, failure behaviour, deployment order,
  smoke checks, and rollback.
- Update relevant target/KVK operator documentation and indexed references discovered by the audit.
- Use SQL-first deployment, then bot deployment and target-cache rebuild.

### Out of Scope

- Changing target formulas, weights, thresholds, ranking logic, target population, exemption rules,
  or the power snapshot used after matchmaking.
- Changing `resolve_kvk_scan_state()` semantics or redefining the shared KVK `DRAFT`, `ACTIVE`, and
  `ENDED` values.
- Starting live KVK stats alerts at matchmaking.
- Changing daily KVK overview timing, history finalisation, leadership-review finalisation, honor
  import KVK selection, or unrelated KVK commands.
- Creating a new slash command, subcommand, command group, button, permission path, or manual
  player-facing state override.
- Reworking the full KVK lifecycle into one universal state machine.
- Replacing the target-generation procedures or target export format beyond the provenance and
  publication work required here.
- Adding publication metadata columns to the spreadsheet export template unless the audit proves
  that no safer dedicated metadata or bot-facing view contract is practical and the operator
  separately approves that change.
- Broad cleanup of all legacy target code unrelated to publication-state correctness.
- Production deployment before the SQL and bot changes, cache migration, validation, and promotion
  checks are approved.

## 7. Codex Skills To Use

Use these local Codex skills when they apply to the task. The security-routing skill is required,
and selecting it must not itself start a scan.

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Map the shared KVK-state consumers, target-generation SQL, DAL/service/cache boundaries, persistence, deployment order, and approval gates before implementation. |
| `k98-discord-command-feature` | `use` | The existing `/kvk targets` player output, modern image card, fallback embed, warnings, and interaction fallback path change even though command registration does not. |
| `k98-sql-validation` | `use` | The task depends on `ProcConfig`, target procedures, export tables/views, new publication metadata, migrations, rollback, and SQL-backed cache reads. |
| `k98-test-selection` | `use` | Select focused state, SQL contract, cache, renderer, command-flow, persistence, and regression tests, then justify broader gates. |
| `k98-deferred-optimisation-capture` | `use` | Capture genuinely out-of-scope lifecycle, cache, or legacy-target debt found during the audit without expanding this change. |
| `k98-pr-review` | `use` | Required before handoff for architecture, SQL alignment, cache safety, Discord output parity, tests, and deployment readiness. |
| `k98-promotion-check` | `use` | Required before SQL deployment, bot promotion, cache replacement, restart, and production smoke. |
| `k98-security-review-routing` | `use` | Record separate routine diff-focused Changes review decisions for the bot and SQL repositories, both with Deep Off, because runtime persistence and SQL publication behaviour change. |

### Security Review Decision

The decisions below are provisional during audit and must be executed or confirmed against the
final approved diffs. Do not start a standard or deep codebase audit without a separate explicit
operator request.

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| Bot repository | `Changes review` | Final approved bot implementation base..head covering target publication models/services/DAL, cache persistence, renderers, fallback output, migration handling, tests, and docs | `Changes + Deep Off` using `$codex-security:security-diff-scan` | Pending final diff; retain the completed result path and any stable finding IDs before PR handoff |
| SQL repository | `Changes review` | Final approved SQL implementation base..head covering the publication metadata object, target-generation procedure changes, bot-facing view/contract, migration, rollback posture, validation queries, and schema snapshots | `Changes + Deep Off` using `$codex-security:security-diff-scan` | Pending final diff; retain the completed result path and any stable finding IDs before SQL PR handoff |

Security review focus areas:

- provenance or KVK substitution that could make stale rows appear current;
- fail-open state defaults that could label unverified data Official;
- cache poisoning, partial writes, cross-KVK leakage, and restart persistence;
- unsafe dynamic SQL or object-name handling in target-view publication;
- transaction boundaries between target rows, view pointer, and publication metadata;
- unbounded or overbroad SQL reads;
- migration and rollback safety;
- operator republish controls if an override is approved;
- logging that exposes unnecessary player-level target data.

## 8. Mandatory Workflow

1. Perform an audit and scope review only, then stop for approval.
2. Use `k98-security-review-routing` to record the provisional bot and SQL Changes review targets;
   do not launch a standard or deep audit.
3. Present the current and proposed architecture, publication-state contract, SQL contract, cache
   transition matrix, failure semantics, likely files, migration/rollback approach, test selection,
   deployment sequence, and explicit approval questions, then stop.
4. After architecture approval, present a PR-sized implementation plan for the bot and SQL
   repositories, including deployment dependency and exact stop points, then stop.
5. Implement only after approval. Keep bot and SQL changes in separately reviewable Git targets.
6. Validate focused behaviour first, then run selected repository-wide gates in proportion to the
   final diff.
7. Execute the two final diff-focused Changes reviews with Deep Off and record evidence.
8. Complete `k98-pr-review` for each affected repository and resolve findings.
9. Complete `k98-promotion-check`, deploy SQL first, republish/verify current targets, deploy the
   bot, rebuild the target cache, restart, and perform production smoke.

No one-pass execution is approved.

## 9. Audit Requirements

The first Codex response must be audit/scope only and must include all of the following.

### Current-state map

- Every direct consumer of `get_kvk_context_today()["state"]` and
  `resolve_kvk_scan_state()` relevant to this task.
- The broad `is_currently_kvk()` matchmaking-to-end window and its consumers.
- The Pass 4 fighting-open gate and stats-alert routing.
- KVK history and leadership-review finalisation paths.
- The complete `/kvk targets` route, including direct Governor ID, registered-account selection,
  modern card, image failure, legacy/fallback embed, exemptions, and no-target behaviour.
- The target cache build, read, refresh, subprocess, startup/import-pipeline, and file-persistence
  paths.

### SQL target-generation map

- `ProcConfig` keys used by target generation, including `MATCHMAKING_SCAN` and `DRAFTSCAN`.
- The exact source-scan selection logic and actual applied scan.
- All procedures called by `dbo.sp_TARGETS_MASTER`.
- Target output table creation/truncation and the lifecycle of
  `EXCEL_EXPORT_KVK_TARGETS_NN` objects.
- How `dbo.v_TARGETS_FOR_UPLOAD` is created or repointed.
- Every bot or export consumer of `dbo.v_TARGETS_FOR_UPLOAD`.
- Transaction boundaries, failure points, retries, and whether a failed publish can leave target
  rows, view pointer, and metadata inconsistent.
- Whether routine processing reruns official target generation and whether that can change an
  existing official target set.
- Existing SQL objects that could safely own publication metadata before creating a new object.

### Provenance and state contract

- A proposed typed `TargetPublicationMetadata` contract.
- A proposed pure resolver with exact reason codes.
- A transition table covering no publication, Draft publication, Official publication, Pass 4,
  KVK end, new KVK, explicit republish, and SQL/cache failure.
- Exact rules for `DRAFT`, `OFFICIAL`, `HISTORIC`, and `UNKNOWN`.
- Proof that Official is based on persisted successful target-generation provenance, not merely
  `MAX(ScanOrder) >= MATCHMAKING_SCAN`.
- Rules for source scan/type/config mismatch, row-count mismatch, absent metadata, and stale view.

### Cache and restart contract

- Current cache schema and all readers.
- Proposed cache schema and migration strategy.
- Cache signature and refresh rules.
- Atomic-write and last-known-good behaviour.
- Cross-KVK protection.
- Behaviour when SQL is unavailable before and after an Official cache exists.
- Behaviour when a new KVK exists but no target publication exists yet.
- Separation of target publication timestamp from cache refresh timestamp.
- Startup/restart and import-pipeline implications.

### Output and compatibility contract

- Exact modern card and fallback embed wording for all four states.
- How legacy `ACTIVE`/`ENDED` cache values are handled during migration without defaulting to
  Official.
- Field/model rename or compatibility strategy for `target_state` and `source_state`.
- Long-name, missing-data, empty-target, exempt, and image-render failure behaviour.
- Command surface statement confirming neither top-level nor grouped command count changes.

### Required audit delivery

- Audit Summary
- Current KVK State Consumer Map
- Current Target Generation And Publication Map
- Current Cache And Persistence Map
- Proposed Target Publication State Contract
- Proposed SQL Contract And Object Ownership
- Proposed Bot Layer Ownership
- State Transition And Failure Matrix
- Exact Bot And SQL File Manifests
- Migration, Deployment, Smoke, And Rollback Plan
- Focused And Broader Test Selection
- Security Review Routing Targets
- Refactor Findings And Deferred Candidates
- Approval Questions
- Explicit Stop Point

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Shared fighting lifecycle | Keep `kvk_state.py` as the canonical Pass 4/open-window and Ended resolver; do not change its semantics for this task |
| Target publication model | A typed model under `kvk/models/` or the existing target model module, with explicit publication metadata and state |
| Target publication business rules | A pure helper/service under `kvk/services/`; no publication inference in commands, views, or renderers |
| SQL access | A DAL/repository module under `kvk/dal/`; no new direct SQL in commands or Discord views |
| Target cache | `targets_sql_cache.py` remains the cache owner but consumes typed/repository results and uses publication provenance as its identity |
| Player target orchestration | `kvk/services/kvk_targets_card_service.py` composes target rows, publication metadata, progress, warnings, and display context |
| Modern output | `kvk/rendering/kvk_targets_card_renderer.py` renders publication state without calculating it |
| Fallback output | `targets_embed.py` uses the same resolved publication state and wording as the modern card |
| Command/interaction adapters | Existing `commands/kvk_cmds.py`, `commands/kvk_targets_card_posting.py`, and target views remain thin and keep their current command surface |
| SQL publication metadata | Prefer a dedicated SQL table and optional bot-facing view; do not overload the spreadsheet export template without separate approval |
| SQL deployment | A dated idempotent migration, current schema snapshots, validation queries, explicit rollback classification, and SQL-first deployment |
| Operational tooling | Existing cache refresh/import maintenance paths; add tooling only if required for a safe one-time migration or smoke check |
| Documentation | Relevant KVK/target reference and operator docs plus this task pack closeout |
| Tests | Focused tests under `tests/` and SQL smoke/validation evidence in the SQL repository |

The preferred new SQL object name is `dbo.KVK_Target_Publication` if no existing canonical object is
suitable. A preferred bot-facing consistency view name is `dbo.v_KVK_TARGETS_FOR_BOT` if the audit
shows that a single rowset containing both target data and publication provenance is the safest
contract. These are architecture targets, not permission to create duplicates: the audit must first
confirm current schema and consumers.

A suitable publication record should be able to represent at least:

```text
KVK_NO
SourceScanOrder
SourceScanType            -- DRAFTSCAN or MATCHMAKING_SCAN
ConfiguredDraftScan
ConfiguredMatchmakingScan
OutputObjectName
PublishedAtUTC
TargetRowCount
PublicationVersion
```

A content hash may be added only if it is the smallest reliable way to prevent unnecessary version
churn or prove that an Official set changed. Do not add one speculatively without explaining its
cost and use.

## 11. Likely Files

The audit must confirm the exact manifest. Do not modify every reviewed file automatically.

### Review

#### Bot repository

- `kvk_state.py`
- `stats_alerts/kvk_meta.py`
- `stats_alerts/interface.py`
- `daily_KVK_overview_embed.py`
- `targets_sql_cache.py`
- `target_utils.py`
- `targets_embed.py`
- `kvk/models/kvk_targets_card.py`
- `kvk/services/kvk_targets_card_service.py`
- `kvk/dal/kvk_targets_dal.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `commands/kvk_targets_card_posting.py`
- `commands/kvk_cmds.py`
- `ui/views/kvk_personal_views.py`
- `processing_pipeline.py`
- `services/kvk_history_service.py`
- `leadership_player_review/service.py`
- `constants.py`
- relevant startup/cache maintenance modules discovered by search
- `tests/test_kvk_state_open_window.py`
- `tests/test_kvk_targets_card_service.py`
- `tests/test_kvk_targets_card_renderer.py`
- `tests/test_kvk_targets_card_posting.py`
- `tests/test_targets_sql_cache_subproc.py`
- `tests/test_mykvktargets.py`
- relevant processing-pipeline and stats-alert tests
- relevant KVK/target documentation and deferred register

#### SQL repository

- `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql`
- `sql_schema/dbo.sp_Prep_TargetTable.StoredProcedure.sql`
- `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql`
- `sql_schema/dbo.sp_Prep_ExcelOutputTable.StoredProcedure.sql`
- `sql_schema/dbo.sp_Prep_ExcelExportTable.StoredProcedure.sql`
- `sql_schema/dbo.v_TARGETS_FOR_UPLOAD.View.sql`
- `sql_schema/dbo.EXCEL_EXPORT_KVK_TARGETS_TEMPLATE.Table.sql`
- `ProcConfig` schema and all target-related `ProcConfig` consumers
- current migrations and rollback conventions
- `docs/SQL_RELEASE_CHECKLIST.md`
- `docs/SQL_PROMOTION_GUIDE.md`
- deployment validation scripts and CI workflow

### Modify

Likely bot modifications after approval:

- `targets_sql_cache.py`
- `kvk/dal/kvk_targets_dal.py` or a dedicated publication DAL module
- `kvk/models/kvk_targets_card.py`
- `kvk/services/kvk_targets_card_service.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `targets_embed.py`
- focused tests and relevant target/KVK documentation

Likely SQL modifications after approval:

- `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql`
- any approved bot-facing target view definition
- schema snapshots for the approved publication objects
- a dated migration and any approved rollback script

Modify other reviewed files only when the audit proves a required integration or regression change.

### Create

Likely new bot files, subject to the architecture audit:

- `kvk/models/kvk_target_publication.py`
- `kvk/services/kvk_target_publication_service.py`
- `kvk/dal/kvk_target_publication_dal.py`
- `tests/test_kvk_target_publication.py`
- `tests/test_targets_sql_cache_publication.py`

Likely new SQL files, subject to current repository sequencing and schema audit:

- a dated migration under `migrations/` using the next available sequence;
- `sql_schema/dbo.KVK_Target_Publication.Table.sql` if a new table is approved;
- `sql_schema/dbo.v_KVK_TARGETS_FOR_BOT.View.sql` if a new bot-facing view is approved;
- a matching rollback migration only when the SQL release classification is `Rollback: Included`.

Do not create parallel models, services, DALs, or SQL objects when an existing canonical owner can be
safely evolved.

## 12. Implementation Requirements

### A. Preserve the shared KVK state

- Do not change `State = Literal["DRAFT", "ACTIVE", "ENDED"]` or its Pass 4/end semantics for this
  task.
- Do not make shared state `ACTIVE` at matchmaking.
- Do not change the broad matchmaking-to-end `is_currently_kvk()` window.
- Treat current shared-state values as fighting lifecycle values in naming and documentation where
  practical, but do not perform a broad rename unless separately approved.
- Add regression tests proving stats alerts, daily overview, history, and leadership review retain
  their existing boundaries.

### B. Define the target publication state

Use a typed state equivalent to:

```python
TargetPublicationState = Literal["DRAFT", "OFFICIAL", "HISTORIC", "UNKNOWN"]
```

The resolver must be pure and return both state and a stable reason code.

Required semantics:

- `DRAFT`: the persisted successful target publication proves the source type was `DRAFTSCAN`.
- `OFFICIAL`: the persisted successful target publication proves the source type was
  `MATCHMAKING_SCAN`, the actual source scan equals the configured matchmaking scan, the
  publication KVK is the requested/current KVK, and the shared state is not Ended.
- `HISTORIC`: the same proof required for Official exists and the unchanged shared KVK state for
  that KVK is Ended.
- `UNKNOWN`: provenance is absent, malformed, mismatched, inconsistent, legacy-only, or cannot be
  verified safely.

Additional rules:

- `MAX(ScanOrder) >= MATCHMAKING_SCAN` alone is not proof of Official publication.
- A target row existing alone is not proof of Official publication.
- Missing or unknown state must fail closed to `UNKNOWN`.
- Generic `ACTIVE` must not be used as a target-publication synonym.
- Generic `ENDED` may contribute only to deriving `HISTORIC` from an already proved Official
  publication.

Define stable reasons such as:

```text
draft_source_confirmed
matchmaking_source_confirmed
official_publication_kvk_ended
missing_publication_metadata
publication_kvk_mismatch
missing_source_scan
invalid_source_type
matchmaking_scan_mismatch
row_count_mismatch
legacy_cache_unverified
publication_read_failed
```

The final names may vary to match repository conventions, but tests and logs must distinguish these
conditions.

### C. Add a durable SQL publication contract

- First audit for a suitable existing target-publication/audit object.
- If none exists, create an additive, keyed publication table such as
  `dbo.KVK_Target_Publication`.
- Store one current canonical publication record per KVK, or an append-only publication history
  with an unambiguous current-row selector. Explain and test the chosen ownership model.
- Record the actual applied source scan, not merely the configured value.
- Record source type as `DRAFTSCAN` or `MATCHMAKING_SCAN` using a constraint or equivalent
  validation.
- Record the configured draft and matchmaking scans used for validation.
- Record the published KVK, output object, UTC publication time, target row count, and monotonic
  publication version/signature.
- Do not write/advance publication metadata before all required target-generation steps succeed.
- Ensure target rows, bot-facing view pointer, and publication metadata cannot be observed as a
  mismatched successful publication.
- Use a transaction around the final publication step where safe. If DDL or existing procedure
  boundaries require another pattern, document and test an equivalent atomic handoff.
- Do not delete or overwrite a last-known-good Official publication on a failed rebuild.
- Do not mark a Draft row Official merely because the configured matchmaking scan now exists.
- Official publication must be recorded only when the procedure actually used that exact
  matchmaking scan.
- Routine later scans must not change the Official source scan.
- Once Official, routine automated processing must not silently replace the fixed target set. If
  current workflows genuinely require a force-republish path, propose a default-off, operator-only,
  logged and versioned design during audit and obtain approval before adding it.
- Preserve all target formulas and target values except where the same fixed matchmaking source is
  intentionally republished through an approved operator path.
- Keep spreadsheet export schema unchanged unless separately approved.

### D. Provide a consistent bot-facing SQL read

- Prefer one bot-facing query or view that returns target rows together with matching publication
  provenance, or use a transaction/double-check strategy that proves the metadata did not change
  during the read.
- Do not infer the rowset KVK by stamping the latest Python context onto an unproven view.
- Validate that publication KVK, output object/view, row count, and source metadata agree.
- Reject or retain last-known-good data on partial/mismatched publication; do not write a new cache
  labelled Official.
- Keep query results bounded to the target export population.
- Keep all SQL parameterized and outside commands/views.

### E. Introduce typed bot ownership

The bot should expose a typed publication metadata object with fields equivalent to:

```text
kvk_no
source_scan_order
source_scan_type
configured_draft_scan
configured_matchmaking_scan
published_at_utc
target_row_count
publication_version
output_object_name
```

- Put SQL mapping in a DAL/repository module.
- Put validation and state resolution in a pure service/helper.
- Keep renderers and commands free of publication-state calculation.
- Keep modern and legacy output supplied by the same resolved publication state and display copy.
- Avoid circular dependencies between `targets_sql_cache.py` and `kvk/dal/kvk_targets_dal.py`.
- Reuse existing normalization, UTC, atomic JSON, and logging helpers where practical.

### F. Correct the target cache contract

Replace generic fighting-state identity with publication provenance.

A suitable cache metadata shape is:

```json
{
  "generated_at": "cache write timestamp",
  "kvk_no": 16,
  "publication_state": "OFFICIAL",
  "publication_reason": "matchmaking_source_confirmed",
  "target_source_scan": 1059,
  "target_source_type": "MATCHMAKING_SCAN",
  "target_published_at": "SQL publication timestamp",
  "publication_version": 2,
  "target_row_count": 350,
  "configured_matchmaking_scan": 1059,
  "configured_draft_scan": 1058,
  "kvk_fighting_state": "DRAFT",
  "kvk_fighting_state_reason": "max_scan_order_before_pass4_start_scan"
}
```

The diagnostic fighting-state fields are optional and must never control target publication state.

Required cache behaviour:

- Missing cache: load a proved SQL publication and build atomically.
- Draft cache plus new Official publication: refresh and promote.
- Official cache plus later `MAX(ScanOrder)` or Pass 4 transition: do not refresh for that reason.
- Official cache plus same KVK and same publication signature: reuse.
- Official cache plus changed approved publication version/signature: refresh.
- Cache KVK different from current requested KVK: do not serve it as current.
- New current KVK with no publication: return an honest no-current-publication/Unverified outcome;
  do not relabel the previous KVK cache.
- SQL transient failure with a matching proved cache: retain and use the last-known-good cache.
- SQL transient failure with no proved matching cache: fail closed; do not invent Official state.
- Empty or inconsistent SQL rowset: do not replace a valid cache with an empty Official cache.
- Cache writes remain atomic and restart safe.
- Legacy `_meta.state` and row `TargetState` values are migrated or invalidated deliberately.
- Do not default legacy `ACTIVE` or missing state to Official.
- If row-level `TargetState` remains for compatibility, populate it from publication state, not from
  shared KVK state.
- Separate the SQL target publication timestamp from the JSON cache write timestamp in display and
  diagnostics.

### G. Update the target model and service naming

- Replace ambiguous `source_state` with `publication_state` and include publication reason/source
  metadata in the modern payload.
- Rename `target_state` to `progress_state`, or provide an explicitly documented compatibility
  property during migration.
- Do not allow renderer colour/wording decisions to depend on progress state when the intent is
  publication state.
- Preserve complete, target-review, no-target, exempt, and invalid-ID behaviour.
- Preserve last-KVK metric calculations and current target amounts.

### H. Update modern and fallback outputs

Modern card requirements:

- show a clear publication badge or equivalent state label;
- show concise source text for Draft, Official, and Historical states;
- show a visible warning for Unknown/Unverified state;
- display the SQL publication timestamp when useful, not only the cache refresh timestamp;
- retain KVK number, mode, camp, matchmaking power, targets, and last-KVK comparisons;
- fit long governor names and source text within existing renderer safety rules.

Fallback embed requirements:

- use the same canonical labels and source wording;
- map `DRAFT`, `OFFICIAL`, `HISTORIC`, and `UNKNOWN` explicitly;
- use a neutral/warning colour for Unknown;
- never use the current fallback default that treats missing state as Active/Official;
- preserve target fields, last-KVK summary, optional banner, and footer identity.

The warnings tuple or equivalent output contract must be rendered or otherwise surfaced where it
carries publication safety information. Do not calculate a warning and silently discard it.

### I. Preserve command and interaction behaviour

- Top-level command count changes: `neither`.
- Grouped subcommand count changes: `neither`.
- Keep `/kvk targets` path, arguments, decorators, permissions, response visibility, usage tracking,
  account selector, Governor ID lookup, and fallback routing unchanged.
- No command resync should be required unless the audit unexpectedly finds a registration change.
- Do not add direct SQL to `commands/kvk_cmds.py`, `commands/kvk_targets_card_posting.py`, or
  `ui/views/kvk_personal_views.py`.

### J. Logging and observability

Add bounded operational logging for:

- requested/current KVK;
- publication KVK;
- source scan and source type;
- configured draft and matchmaking scans;
- resolved publication state and reason;
- publication version and row count;
- cache hit/refresh/retain/reject decision;
- cross-KVK or metadata mismatch;
- SQL publication/read failure;
- cache migration or rebuild.

Do not log the full player target payload or unnecessary personal data.

### K. SQL migration and deployment requirements

- Create an idempotent migration using the SQL repository's next available naming sequence.
- Update authoritative `sql_schema` files for every changed/created object.
- Declare `DataChange` and rollback classification according to repository rules.
- If rollback is included, provide and validate a matching rollback migration.
- Include pre-deployment and post-deployment validation queries.
- Validate expected row counts and the current KVK source scan.
- Follow `docs/SQL_RELEASE_CHECKLIST.md` and `docs/SQL_PROMOTION_GUIDE.md`.
- Deploy SQL before the bot because the new bot must fail closed without the provenance contract.
- After SQL deployment, run target generation for the current KVK through the approved operational
  path and verify publication metadata before deploying the bot.
- Rebuild or remove `PLAYER_TARGETS_CACHE` through the approved maintenance path after bot
  deployment.
- A command registration resync is not expected.

### L. Documentation and deferred work

- Document the three separate concepts: broad KVK window, fighting state, target publication state.
- Document the source/provenance contract and why matchmaking completion alone is insufficient
  without successful publication evidence.
- Document cache recovery and cross-KVK safeguards.
- Capture only genuinely out-of-scope non-security debt using the structured deferred framework.
- Route suspected security issues through `k98-security-review-routing`; do not classify them as
  normal deferred optimisations.

## 13. Refactor Decisions

Classify audit findings using this starting position:

| Issue | Decision | Reason |
|---|---|---|
| Targets reuse shared Pass 4 fighting state | `fix now` | This is the primary correctness defect and produces misleading Draft output after targets are fixed. |
| Target output lacks durable source-scan provenance | `fix now` | Official state cannot be proved safely and stale view data can be mislabelled. |
| Cache identity depends on generic KVK state | `fix now` | Pass 4 causes irrelevant refresh/state changes and later lifecycle transitions are not modelled correctly. |
| `target_state` versus `source_state` naming collision | `fix now` | The two fields represent different domains and invite repeated misuse. |
| Missing/legacy state defaults to Active in fallback embed | `fix now` | Publication state must fail closed rather than appear Official. |
| Broad KVK lifecycle redesign or global state rename | `defer` | Existing fighting, overview, history, and leadership behaviour is valid and outside this target-specific fix. |
| Full legacy target subsystem rewrite | `defer` | Change only the paths required for publication correctness and output parity. |
| Universal cache framework | `defer` | Use existing atomic/cache helpers; a general framework is not required for this feature. |
| Target formula or exemption redesign | `not applicable` | Product requirement is to preserve the fixed matchmaking target values. |

Any additional deferred item must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`. Security findings remain in the
security workflow and private findings register.

## 14. Testing Requirements

Use `k98-test-selection` before finalising commands. Cover or explicitly justify every category:

- happy path;
- negative path;
- regression;
- permission boundary;
- restart/persistence;
- cache safety;
- format/output shape.

### Publication-state unit matrix

Add tests for at least:

1. persisted `DRAFTSCAN` publication resolves `DRAFT`;
2. current scan passing matchmaking does not promote a still-Draft publication;
3. persisted exact `MATCHMAKING_SCAN` publication resolves `OFFICIAL` before Pass 4;
4. Pass 4 opening leaves the target state `OFFICIAL` and does not alter the publication signature;
5. KVK end derives `HISTORIC` from a proved Official publication;
6. missing metadata resolves `UNKNOWN`;
7. publication KVK mismatch resolves `UNKNOWN`;
8. source scan missing or invalid resolves `UNKNOWN`;
9. source type invalid resolves `UNKNOWN`;
10. matchmaking source scan not equal to configured matchmaking scan resolves `UNKNOWN`;
11. row count or view/publication mismatch is rejected;
12. legacy `ACTIVE`, `ENDED`, or absent cache state does not silently become Official.

### Cache and persistence matrix

Add tests for at least:

- missing cache builds from proved Draft metadata;
- Draft cache promotes when Official metadata appears;
- Official cache is reused when only generic KVK state or max scan changes;
- an approved publication-version change refreshes the cache;
- a new KVK invalidates current use of the previous KVK cache;
- transient SQL failure retains a matching last-known-good proved cache;
- transient SQL failure without a matching proved cache fails closed;
- empty/malformed SQL data does not replace a valid cache;
- atomic temp-file replacement remains intact;
- subprocess summary includes publication state/signature without emitting the full cache;
- restart reads the same publication state and source metadata;
- publication timestamp and cache-write timestamp remain distinct.

### Service and rendering matrix

Add or update tests for:

- modern payload field naming and compatibility;
- Draft, Official, Historical, and Unverified modern card output;
- Draft warning and Unverified warning visibility;
- Official source wording with matchmaking scan;
- Historical source wording;
- fallback embed state, colour, header, and footer parity;
- missing state does not default to Official;
- long governor name and footer/source fitting;
- exempt, no-target, no-target-values, invalid-ID, and image-render failure paths;
- target values and last-KVK comparisons remain unchanged.

### Shared-state regressions

Keep or add tests proving:

- before Pass 4, shared state remains `DRAFT`;
- at Pass 4, shared state becomes `ACTIVE`;
- after known end scan, shared state becomes `ENDED`;
- `KVK_END_SCAN = NULL` remains an open-ended active fighting window after Pass 4;
- stats-alert routing remains Pre-KVK before Pass 4 and live KVK after Pass 4;
- daily KVK overview broad window remains matchmaking-to-end;
- history and leadership review finalisation still require Ended/output-complete evidence.

### SQL validation and smoke

Provide pre/post queries and evidence for at least:

- Draft generation records actual applied `DRAFTSCAN`;
- Official generation records the exact configured `MATCHMAKING_SCAN`;
- successful publication records target row count and version;
- failed generation does not advance or corrupt the last-known-good publication;
- bot-facing rows and publication metadata agree on KVK and publication;
- routine later scan progression does not change Official source scan;
- any approved force republish is default-off, logged, and increments version;
- migration is idempotent;
- rollback classification and script are valid;
- current KVK smoke shows the expected Official publication.

### Baseline bot commands

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
```

Likely focused bot tests, adjusted to the final manifest:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_target_publication.py tests\test_targets_sql_cache_publication.py tests\test_kvk_targets_card_service.py tests\test_kvk_targets_card_renderer.py tests\test_kvk_targets_card_posting.py tests\test_targets_sql_cache_subproc.py tests\test_mykvktargets.py tests\test_kvk_state_open_window.py
```

For the final runtime/persistence change, also run unless `k98-test-selection` records a precise
reason not to:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

`validate_command_registration.py` and command-inventory tests may be skipped only if the final diff
contains no command registration/decorator/import-surface change and the skip is recorded. If any
such change appears, run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
```

### Baseline SQL validation

From `C:\K98-bot-SQL-Server`, use the repository's approved environment and run:

```powershell
.\deploy\Validate-SqlRepo.ps1
```

Also require:

- SQL PR GitHub Actions validation;
- migration validation-only review through the documented deployment workflow;
- changed migration/rollback parser and SQLFluff advisory review;
- pre/post publication smoke queries;
- post-deployment drift check through `deploy/Invoke-DriftCheck.ps1`;
- separate SQL Changes security review with Deep Off.

Before PR handoff, complete both Security Review Decision rows with actual base/head targets and
retained evidence.

## 15. Acceptance Criteria

- [ ] `/kvk targets` no longer uses shared Pass 4 fighting state to decide Draft versus Official.
- [ ] The shared KVK state resolver and all non-target consumers retain their existing behaviour.
- [ ] A typed target publication state exists with `DRAFT`, `OFFICIAL`, `HISTORIC`, and `UNKNOWN`.
- [ ] Official state is proved from persisted successful use of the exact configured matchmaking
  scan.
- [ ] Current max scan passing matchmaking is not by itself treated as publication proof.
- [ ] SQL records the actual target source scan, source type, KVK, publication timestamp, row count,
  and version/signature.
- [ ] Target rows, view pointer/bot-facing rowset, and publication metadata cannot be accepted in a
  mismatched successful state.
- [ ] A failed target rebuild does not destroy or advance the last-known-good publication.
- [ ] Routine later scans and Pass 4 do not change the Official target source or publication state.
- [ ] Official targets remain fixed unless an explicitly approved, logged, versioned operator
  republish occurs.
- [ ] Historical state is derived only from a proved Official publication plus unchanged KVK Ended
  evidence.
- [ ] Missing, malformed, mismatched, or legacy-only provenance resolves Unverified and never
  defaults to Official.
- [ ] Cache identity uses publication provenance rather than generic KVK state.
- [ ] Draft-to-Official, new-KVK, approved-republish, SQL-failure, empty-rowset, and restart paths are
  tested.
- [ ] A previous KVK's cache cannot be presented as the current KVK's targets.
- [ ] Atomic cache writes and last-known-good safety are preserved.
- [ ] Target publication time and cache refresh time are distinct.
- [ ] Modern card and fallback embed show equivalent publication state and source wording.
- [ ] Draft and Unverified warnings are visible to the player.
- [ ] Modern payload naming distinguishes publication state from progress/result state.
- [ ] Target values, formulas, exemptions, comparisons, command permissions, command path, and
  response visibility remain unchanged.
- [ ] Top-level and grouped command counts are unchanged.
- [ ] No new direct SQL exists in commands or Discord views.
- [ ] Logging records bounded publication/cache decisions without dumping player target data.
- [ ] Relevant documentation explains broad KVK window, fighting state, and target publication
  state separately.
- [ ] SQL migration, schema snapshots, rollback posture, validation queries, and deployment order
  follow SQL repository standards.
- [ ] SQL is deployed and current target publication verified before the bot is deployed.
- [ ] Legacy target cache is deliberately rebuilt or migrated during deployment.
- [ ] Focused and selected full validation passed or exceptions are precisely documented.
- [ ] A precise bot Changes review and SQL Changes review were completed against final base/head
  targets with Deep Off.
- [ ] No standard or deep codebase audit was started without an explicit operator request.
- [ ] `k98-pr-review` and `k98-promotion-check` completed before production promotion.
- [ ] Any non-security out-of-scope debt is captured structurally; security findings are tracked
  separately.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Publication State And Provenance Contract
8. Cache Migration And Persistence Behaviour
9. Refactor Findings
10. Test Plan And Results
11. Security Review Decision And Evidence
12. Deployment Steps And Smoke Results
13. Rollback Posture
14. Deferred Optimisations

The delivery must explicitly state:

- whether a new SQL publication table and/or bot-facing view was created;
- the final publication metadata schema;
- the exact cache signature and state transition rules;
- how the current KVK was republished/verified;
- whether any force-republish capability was added;
- why shared KVK state consumers were unaffected;
- the final bot and SQL base/head security-review targets and evidence paths.

## 17. PR Summary Template

```md
## Summary

- Separate KVK target publication status from the shared Pass 4 fighting lifecycle.
- Prove Draft versus Official target state from persisted target-generation source metadata.
- Preserve fixed matchmaking targets, shared KVK state consumers, and existing `/kvk targets`
  command behaviour.

## Changes

- Add a durable SQL target-publication/provenance contract and consistent bot-facing read.
- Add typed Draft, Official, Historical, and Unknown target-publication resolution.
- Change target-cache identity and refresh rules to use publication provenance.
- Update modern and fallback target output with matching state/source wording and fail-closed
  Unverified behaviour.
- Add cache migration, regression coverage, deployment documentation, and SQL-first rollout checks.

## Tests

- Bot architecture, deferred-item, selected-test, security-routing, focused target/cache/state,
  smoke-import, pre-commit, and selected/full pytest gates recorded in the PR.
- SQL repository validation, migration validation-only review, publication smoke queries, CI, and
  drift check recorded in the SQL PR/deployment evidence.

## Security Review

- Bot decision: `Changes review`.
- Bot target: final approved bot base..head covering publication state, DAL/service/cache,
  renderers, fallback output, migration handling, tests, and docs.
- Bot expected setup: `Changes + Deep Off`.
- Bot evidence: replace the pending entry with the retained completed scan result before handoff.
- SQL decision: `Changes review`.
- SQL target: final approved SQL base..head covering publication metadata, target publication
  procedure/view contract, migration, rollback posture, tests/queries, and schema snapshots.
- SQL expected setup: `Changes + Deep Off`.
- SQL evidence: replace the pending entry with the retained completed scan result before handoff.

## Deferred Optimisations

- Record only structured, genuinely out-of-scope lifecycle/cache/legacy-target items discovered by
  the audit; otherwise state `None`.

## Risk / Rollback

- Primary risk is publishing or caching target rows with mismatched KVK/source provenance, or
  accidentally changing stats-alert/history behaviour by modifying shared KVK state.
- Deploy SQL first and make the bot fail closed when provenance is unavailable.
- Roll back the bot to the previous release and restore/rebuild the prior target cache if necessary.
- Follow the SQL migration's declared rollback or forward-fix plan; additive metadata objects may
  remain in place if reverting them would be riskier than leaving them unused.
```
