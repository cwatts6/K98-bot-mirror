# KVK Source Migration S9A — Public Routing and Availability

## Current status — S10B merged and locally pulled; S10C scope next, 2026-09-14

S10B mirror #278 and production #585 are merged; local pulls are complete.
**No changes have been pulled to the bot machine.** Repository delivery is not deployment or activation.
Bot main/origin main: `8ae66da6e12b53781c5df0d46a8ee79314cecead`; production/main:
`40c2e48111ebbe44d58d71269dea63a6dd9388b7`. SQL #85 remains accepted at
`3776dfa6b0892a8800d236fdf111c4d2f93c3813`; no S10B SQL delta.
Final retained offline validation: **4,433 passed / 66 skipped**; review fixes are in both repositories.
See [S10B closeout and exact S10C documentation manifest](../../reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md) for exact delivery/content proof and evidence boundaries.

Next: **S10C Legacy and Scan Export Adapters, initial review/scope only**: [task pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md).
Completed S10B pack/starter are archived; retained runbooks, databases, files and evidence stay available.
Every pending Bot document and both S10B archive move sides must accompany the eventual S10C Bot implementation PR.
Verify exact filename AND previous_filename or exact merged/absent-at-base proof; counts alone are insufficient.
No standalone documentation PR or repository mixing. The two pending SQL documents stay in the next authorized SQL PR.

Preserve S6-OPS01/PERF01/CAP01 and both uncertain publications. S8A six scripts, S8B 50-case/actual-restore
and offline-runner evidence, and S8C seven local checks remain distinct. No new live Discord evidence is claimed.
This closeout authorizes no S10C implementation, Git publication, SQL/provider/Discord execution, real imports/exports,
bot-machine pull/restart/deployment, activation, predecessor rerun or automatic new task.
Earlier dated statuses and approvals below are historical; settled acceptance and grouping stay settled.

> Historical handoff: **S9B repository-delivered; not deployed**. See [S9B closeout / S10A scope and exact documentation carry-forward](../../reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md).
> Retained evidence and historical approvals below remain intact; no predecessor rerun or live operation is authorized.

> Archived 2026-09-14 after merged mirror #276, production #583 and SQL #83.
> This document preserves the S9A scope, approvals and execution/review history.
> Current authority: [S9A closeout](../../reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md) and [S9B scope pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S9B%20Stats%20Target%20Card%20Context%20and%20Admin%20Dispatch.md).
> Earlier prospective instructions below are historical, not renewed authorization.


## Authority and required reading

Prepared 2026-09-13 for initial review/scope only. S8C implementation and code review are delivered
through merged mirror #275, production #582 and SQL #82; local pulls are complete. No S9A
implementation, new task, SQL execution, activation or deployment is authorized by this pack.
Read current AGENTS/core references, [S8C closeout](../../reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md),
[approved S7 contract/consumer matrix](../../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md),
[exact manifests](../../reference/kvk_source_migration/integration_implementation_manifests.md),
[architecture/EndScanID amendment](../../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
[acceptance scenarios](../../reference/kvk_source_migration/phase_2_acceptance_scenarios.md), and retained S6 evidence.
Read authoritative SQL definitions and repository guidance in C:/K98-bot-SQL-Server, without connecting.
Read the archived S8C pack for the approved season, pairing and post-use configuration decisions.
S8C disposable SQL and automated folder smoke passed; the operator completed all seven local
walkthrough checks on 2026-09-14. Read the [execution and operator evidence](../../reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md).
This does not claim live Discord acceptance, bot-machine delivery or production activation.

## Objective and exact initial boundary

Wire ordinary reporting/dispatch callers to fixed-source, complete-selection routing and explicit
availability/cache context. SourceRouting.Enabled alone is insufficient. Trace normal calls without
injected providers, not only isolated routing tests. Preserve legacy behavior for legacy seasons;
a disabled/unavailable new-source season must not silently fall back to legacy or mix source blocks.
S9B owns stats/target cards and grouped admin dispatch. S10 owns coordinated exports/recovery/rollover.
No new top-level command, provider execution or source activation belongs to this scope.

The approved S7 S9A manifest is exactly 20 paths. Validate current existence and callers before
implementation; any additional runtime/test/SQL path needs an explicit scope amendment.
The already completed S8C smoke adapter and tests listed below are approved delivery carry-forward,
separate from these 20 new S9A implementation paths; do not treat them as missing scope approval.

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/dal/source_routing_dal.py` |
| Bot | Create | `kvk/services/source_routing_service.py` |
| Bot | Create | `tests/test_kvk_public_routing.py` |
| Bot | Create | `tests/test_kvk_source_independent_consumers.py` |
| Bot | Modify | `kvk/models/source_integration.py` |
| Bot | Modify | `kvk/dal/new_source_reporting_dal.py` |
| Bot | Modify | `kvk/dal/kvk_reporting_dal.py` |
| Bot | Modify | `kvk/services/kvk_reporting_service.py` |
| Bot | Modify | `kvk/services/new_source_reporting_service.py` |
| Bot | Modify | `stats_alerts/allkingdoms.py` |
| Bot | Modify | `stats_alerts/embeds/kvk.py` |
| Bot | Modify | `stats_alerts/kvk_diagnostics.py` |
| Bot | Modify | `stats_alerts/kvk_diagnostic_sessions.py` |
| Bot | Modify | `tests/test_kvk_reporting_service.py` |
| Bot | Modify | `tests/test_kvk_source_reporting.py` |
| Bot | Modify | `tests/test_kvk_source_reporting_models.py` |
| Bot | Modify | `tests/test_kvk_embed.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostics.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostic_lifecycle.py` |
| Bot | Modify | `tests/test_stats_alerts_fighting_lifecycle.py` |

## Required behavior and review risks

Preserve fixed season source, immutable season assignment, complete matched UpdateID, explicit
counterpart attestation, sealed input/CAS checks and atomic complete selection/full-vector intent.
Public status must distinguish first-pair waiting, previous complete output, desired configuration
pending and current/final availability. A failed second side retains the previous complete result;
desired end 14 must not label old end 13 as current final. Key caches and diagnostics by authoritative
source/season/update/configuration/roster identity so mixed/stale blocks cannot appear current.
Preserve B0, UTC starts, semantic deduplication, exact 11−10/12−10/13−10 then approved 14−10,
no-fight rules, independent supplied aggregates/DKP and separate overall. Retain unused valid scans;
later within-season endpoint assignment can use them. Preserve daily SCANORDER, daily/independent
consumers, targets and historical outputs. Review every applicable C01–C65/N01–N12 consumer entry;
do not silently move S9B/S10-owned work into S9A. Never fabricate unattended counterpart authority.
Retain legacy admission through ingest/recompute and locked source admission before artifact writes.

## Tests, SQL and security

Scope S7-T02, T06 and S9A's T16 consumer cases. Cover ordinary legacy/new/unavailable/disabled/
capability paths, first pair waiting, failed second side, changed desired endpoints, stale cache,
diagnostics lifecycle, permission boundaries and restart/readback. Run manifested tests and relevant
S8B/S8C regressions; architecture, deferred, security-routing, exact-path selector, imports, command
registration and configured lint/type hooks. Use full offline pytest/log-noise validation for handoff.
SQL implications must be assessed independently against actual schema. No SQL schema delta is
pre-approved. S8C's disposable fixture/five opt-in SQL cases and local operator walkthrough passed;
retain that dated evidence without repeating acceptance. Live Discord coverage remains separate,
and S9A scope work does not authorize connecting to a database.
Use k98-architecture-scope, k98-sql-validation and k98-test-selection. Before runtime review, use
k98-security-review-routing then security-diff-scan at the exact Bot target: Changes, Deep off.
Any SQL delta needs its own decision/target. This preparation has a Markdown-only security skip;
no standard/deep audit or automatic task is selected.

## Mandatory delivery and approval output

**Delivery decision approved by the operator on 2026-09-14:** publish the pending S8C closeout,
smoke tooling and operator acceptance documentation as part of the S9A slice. Do not create a
standalone S8C documentation/smoke-tool PR. This is approval of delivery grouping, not authorization
to implement S9A or create/publish PRs now.

The eventual separately authorized S9A Bot PR must include the complete union of:

- The exact 20 S9A implementation paths above and any separately approved scope amendments.
- All **38 physical Bot paths** in the [S8C closeout manifest](../../reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md):
  36 documentation paths plus the two already completed smoke-tool/test paths below. The manifest
  includes this S9A pack/starter, both sides of both S8C archive moves, smoke evidence and work instruction.
- Any further S9A closeout outputs explicitly added to the exact delivery manifest during the slice.

Explicit S8C smoke carry-forward (already included in the 38 paths, not additional counts):

| Purpose | Bot path |
|---|---|
| Local console adapter | `scripts/smoke_kvk_source_intake.py` |
| Offline adapter boundary tests | `tests/test_kvk_source_folder_smoke.py` |
| SQL/folder smoke execution and operator acceptance | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` |
| Approved smoke plan | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_plan.md` |
| Completed operator work instruction | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` |

At this checkpoint the 20 and 38 sets do not overlap: **58 physical Bot paths** before further
approved amendments. Reconcile by exact path, not count alone. Verify actual GitHub `filename`
AND `previous_filename`; any omission needs specific merged commit/blob proof. Preserve the
retained local databases, originals and transcripts; reference them in documentation, do not add
those external artifacts to Git.

In the same S9A delivery cycle, carry `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md` in a
**separate SQL-repository PR**, alongside any independently approved S9A SQL changes. These two
SQL documentation paths must never enter the Bot PR. Their inclusion does not authorize a schema
change or database execution. If already merged by then, retain exact path and merge/blob proof.

Return exact scope, caller/schema/cache risks, helper reuse/refactor decisions, tests, unresolved
runtime evidence and implementation plan for approval. Do not re-ask approved S7/S8C product choices
or predecessor acceptance. Preserve pending work and all retained evidence; no stage/commit/push/PR/
merge/pull/fetch/reset, SQL/provider/Discord execution, bot-machine operation, restart or activation.

## Approved implementation and offline handoff — 2026-09-14

The operator approved the scoped implementation with "agreed please proceed", then requested
repair of the historical-preview regression and security artifact finalization. This supersedes
the initial scope-only restriction for the 20 runtime/test paths above and local validation only.
It does not authorize Git publication, SQL/provider/Discord execution, real imports/exports,
deployment, activation, bot-machine operations or a new task. No scope amendment was required.

### Implemented behavior and scope

- Ordinary all-kingdom reporting, preview and fighting dispatch resolve the explicit season choice.
  Legacy seasons retain their block shape. New-source seasons require enabled, compatible routing
  and a complete matched UpdateID/publication selection. Component selection alone is insufficient.
- The public DAL verifies source, season, period, choice, sealed input hash, publication and update
  linkage, configuration and roster, player result digest/count and supplied aggregate completeness.
  Existing authoritative player/DKP/aggregate/overall formatting is reused. No recomputation from
  rounded aggregate display strings or substitution of player sums was added.
- Availability distinguishes missing/disabled/unsupported authority, first-pair waiting, current
  output and previous complete output during pending updates/configuration. Desired end 14 does
  not relabel the retained end 13 publication as current final. Pending updates are scoped to the
  desired configuration and current BaseUpdateID, excluding obsolete branches.
- A frozen read identity includes source/season/routing/capability, period, update/publication,
  public selection version, selected/desired configuration, roster and pending-update versions.
  Saved preview manifests pin that identity, validate it on restart and refuse retargeting. Actions
  recheck current authority before the existing durable send boundary; status remains read-only.
- SQL metadata remains the ordinary season authority. Missing metadata does not invoke Sheets or
  dispatch. Explicit historical seasons retain nullable display dates and omit latest-season honor.
- Existing admission locks, grouped commands, daily claims and independent consumers remain owned
  by their existing services. B0, UTC starts, daily SCANORDER, exact endpoint chains, unused retained
  scans, movable within-season windows, CAS/sealed inputs and explicit counterpart attestation are
  unchanged. No S9B cards/admin dispatch, S10 exports, new top-level command or activation was added.

### Performance and robustness assessment

Only small authority rows are read while holding the season-first routing lock. Immutable result
loading, digest verification and rendering occur after that transaction closes; the ordinary-call
test asserts this separation. The public reader reuses the existing report formatter and immutable
metadata helpers. No shared report cache was introduced: fresh SQL authority prevents stale routing
or availability from surviving a configuration/selection change. The complete cache identity is
explicit for any later measured cache implementation; independent KS4/target/history caches are not
rekeyed or invalidated by this slice.

This improves lock discipline and failure handling but does not establish a production speedup.
The representative offline complete read uses three sequential connections (authority, immutable
rows, metadata), plus the action authority recheck when sending. Player digest work remains linear
in result size. SQL latency, execution plans, concurrency and capacity require separately authorized
measurement. S6-PERF01 and S6-CAP01 remain open; no benchmark or database evidence was replaced.

### Validation and security evidence

- Final full offline/log-isolation run: **4,289 passed, 62 skipped**, 176.32 seconds. Production
  operational logs unchanged. Includes S8B/S8C offline regressions without executing opt-in SQL.
- Historical-preview and diagnostic focused regression run: **43 passed**. The first full run
  exposed a nullable historical display-date regression; it was corrected in the manifested embed
  file without expanding the path scope. Final full suite has no failures.
- Architecture, deferred-item and security-routing validators, exact-path test selector, import
  smoke and command registration passed. Registration remains **36 top-level / 101 grouped**.
  Black and Ruff passed for all 20 S9A paths; the final embed correction passed both again.
  Pyright with the repository interpreter passed with zero errors and zero warnings. Read-only
  hygiene checks covered the entire pending union. Staged-only gitleaks is not claimed: both indexes
  intentionally remain empty, and publication/commit hooks remain a later authorized delivery gate.
- Original Changes review `a60fe364-ac2e-4a6f-b8be-df072ac03a45` was recovered and completed after
  correcting invalid coverage-field names in the semantic draft. The failed finalization attempt
  remains historical evidence; it was not treated as a successful scan or silently replaced.
- Final corrected-patch Changes review `8ef160c4-f5ae-4004-b88e-04e808f38f1b`: **zero findings**, all
  12 source files reviewed with supporting tests/docs, Deep off, baseline
  `b6e45293348ece7b562e29c0451a8c3a7dbe2550`, snapshot digest
  `c73a554e5f800a037145665bf69859bb7738c0ac6eb7665734f502b62a9f48bc`.
  Canonical report retained locally at
  `C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-F9Gfoa/discord_file_downloader/b6e45293348ece7b562e29c0451a8c3a7dbe2550_20260914T085013Z_pbte5wr_/report.md`.
  Daybreak access was granted (Daybreak Blue). Workbench-reported usage: 1,285,753 total tokens,
  including 1,274,624 cached input tokens; this is telemetry, not a billing calculation.
  This post-scan evidence addendum changes Markdown only; reviewed Python is unchanged.
- SQL independently receives a documentation-only security skip: the exact pending paths remain
  `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`; no SQL/config/permission definition changed.
  SQL-facing reads were checked against the authoritative repository, with no schema amendment or
  SQL execution. Live SQL/provider/Discord acceptance and production performance are not claimed.

### Exact delivery and retained evidence

Final local reconciliation checked exact names: the 20-path implementation set and complete
38-path carry-forward set are disjoint and equal all **58 physical pending Bot paths**, including
both sides of both archive moves. Bot HEAD/main/origin main remains
`b6e45293348ece7b562e29c0451a8c3a7dbe2550`; production/main remains
`afac4118db4bca282c8d12ea3d121701ae2da3c0`; SQL HEAD/main/origin main remains
`3c1b5ceaa7a686bc594ca8637d0a1569030d66c4`. Both indexes are empty. Nothing was staged, committed,
pushed, fetched, pulled, reset, merged or published. Eventual separately authorized PR delivery must
still verify GitHub `filename` AND `previous_filename`, or retain specific merged-content proof;
this local reconciliation is not remote PR proof. SQL's two documentation paths remain separate.

The S8C seven-check operator acceptance and disposable smoke remain distinct from live Discord;
S8B accepted smoke/50-case/actual-restore evidence and offline runner history remain distinct from
S8A six-script evidence. S6-OPS01/PERF01/CAP01, both uncertain publications and all retained
databases, originals, backups and external evidence are preserved. No predecessor execution was
repeated. The next delivery or operational action requires its own authorization.

## PR review follow-up — 2026-09-14

The operator subsequently authorized PR creation and action/replies/resolution for review comments.
Bot mirror PR #276 and separate SQL documentation PR #83 are open for review; earlier uncommitted
statements above describe the prior local checkpoint, not their present publication status.

Bot review comment 4003710837 correctly identified that the empty-data guard also skipped explicit
legacy-source reports carrying provenance. The guard now preserves empty legacy sends while still
blocking routing/new-source unavailability and retaining the fresh authority check before send.
The ordinary dispatch regression reproduced the failure before the fix and verifies two legacy
embeds, the existing mention behavior and one daily claim; disabled new-source output remains blocked.
Focused regression tests: **82 passed**. Full offline/log-isolation run: **4,290 passed, 62 skipped**,
179.54 seconds; production operational logs unchanged. Architecture, deferred-item, security-routing,
selector, imports and registration checks passed; command surface remains 36 top-level / 101 grouped.

Narrow Changes review `72bb84e5-f375-4bc8-9399-87079602b116` completed with **zero findings**, Deep off,
against Bot PR head `a3ca95b8cc3041c8a495e4f7fad0c2abbefbe6b2`; reviewed snapshot digest
`6593f363c8aae88119c7f540ae2cb5cd4abcc811db4a6ed4d834eb394842612c`.
The one changed runtime file and its regression test were reviewed with supporting authority checks.
This evidence-only Markdown addendum follows the scan; reviewed Python is unchanged. Daybreak was
granted (Daybreak Blue); workbench telemetry reports 1,327,607 total tokens, including 1,269,248 cached
input tokens. Canonical artifacts remain under the local scan directory ending
`a3ca95b8cc3041c8a495e4f7fad0c2abbefbe6b2_20260914T091637Z_7a0xz9fz`.

SQL review comments 4003671388 and 4003671443 are addressed in the existing two SQL documentation
paths: the unrun statement is explicitly scoped to the original repository-delivery checkpoint and
links to the later disposable-execution addendum. Publication wording now records SQL PR #83.
The static documentation-path check and staged hygiene/secrets checks passed; the independent
documentation-only security skip remains applicable. No SQL or predecessor execution occurred.
The Bot58/SQL2 exact delivery manifests and all operational/retained-evidence boundaries remain intact.
