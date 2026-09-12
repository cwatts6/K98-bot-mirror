# KVK Source Migration — Phase 2A evidence and validation log

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

[Settled requirements](post_s6_integration_requirements.md); [handoff and exact manifest](post_s6_handoff_log.md); [S7 pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

2026-09-09. Bounded documentation delivery; **G2 awaiting operator architecture review**.
The current request authorizes design outputs and additive navigation/status only. No attached
document grants permission for Phase 2B, implementation or live operations.

## 1. Summary

Delivered [contract and architecture](phase_2_contract_and_architecture.md) and
[synthetic acceptance scenarios](phase_2_acceptance_scenarios.md). Recommendations A01–A08
resolve identity, source storage, fixed roster, precision, revisions/finals, publication, consumers,
caches, operator journey and realistic rollback. T01–T67 are proposed future tests, not executed
acceptance of code. Draft S1–S6 sequence is a feasibility outline, not implementation packs.

## 2. File Manifest

All task writes are Markdown under `C:\discord_file_downloader`. Exact seven-path manifest:

| Path relative to bot root | Task action |
|---|---|
| `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` | New design |
| `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` | New synthetic scenarios |
| `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` | New evidence/delivery log |
| `docs/task_packs/KVK Source Migration - Programme Pack.md` | Append current Phase 2A delivery/gate status |
| `docs/reference/kvk_source_migration/decision_and_evidence_register.md` | Append proposed A01–A08 and updated Q dispositions |
| `docs/task_packs/README.md` | Append navigation/status |
| `docs/reference/README.md` | Append navigation/status |

## 3. New Files

The three named Phase-2 outputs above. No other repository files created. Temporary snapshots
and check results are under `%TEMP%/kvk-phase2a-20260909`, outside Git, with no player rows.
The existing Phase-1 CSVs remain unchanged and ignored by the existing `*.csv` rule; any future
authorized documentation commit must deliberately include them. No staging performed here.

## 4. Modified Files and preservation

Only the four append-only status/navigation documents in the manifest. Their original byte
prefixes are protected by pre-edit SHA-256/length snapshots, alongside 1,498 initial tracked,
untracked and Phase-1 evidence files in temporary `before.json`. This distinguishes task changes
from the substantial pre-existing bot documentation work; the aggregate Git diff is not this task.
No README-DEV, Phase-1 output, task pack/starter, deferred register or unrelated document is changed.

Initial tracked modifications: README-DEV.md; reference README; active/resolved deferred registers;
the two Phase-2L ProcConfig task/starter files; task index; archived Phase-2K task/starter and
Embed Safety Audit Findings; archive index. Initial untracked documentation includes the Phase-1
directory, migration programme and Phase-1/2 task/starter pairs, backlog assessment, reliability
programme/WS1 design/task/starter, and private-inventory programme/task/starter. These all predate
this pass. No initial runtime diff. Final preservation checks compare every captured file,
requiring unchanged bytes except the four authorized appended prefixes.

## 5. SQL Changes and repository evidence

**None.** SQL was inspected read-only and stays clean. No connection, RDP, credential discovery,
query of live rows/jobs, migration, DML or procedure execution. Bot runtime/config/test files also
unchanged. No pull/fetch, checkout/reset, merge, staging, commit, push, PR or deployment.

| Working copy | Branch / local HEAD | Configured remotes / initial status |
|---|---|---|
| `C:\discord_file_downloader` | main / `1a3a5de3d2e9f349c276725f6271ef19a7517c4f` | origin `https://github.com/cwatts6/K98-bot-mirror.git`; production `https://github.com/cwatts6/K98-bot.git`; pre-existing docs above |
| `C:\K98-bot-SQL-Server` | main / `fc0e94ebd2e0a98286069c8a8b71365dd5178657` | origin `https://github.com/cwatts6/K98-bot-SQL-Server.git`; clean |

Commands: `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v`
in both copies. No fresh remote-ref/network check; configured remote identity is not remote parity.
SQL root/nested AGENTS.md and SECURITY.md were not found in scoped hidden-file enumeration.
An explicit root AGENTS.md read returned not-found; no SQL-specific instruction was invented.
Bot root AGENTS/SECURITY and required references govern this design; SQL snapshot/migration READMEs
and SQL_DATA_MIGRATION_GUARDRAILS were read. Snapshots are evidence, not deployable migrations.

Operator confirms SQL/config repo synced with production. Record this as **operator-attested
parity**, sufficient for design; no independent live configuration rows, module hashes, Agent jobs
or external reader inventory was queried. README-DEV's prior production-head/restart record is
historical operator evidence, not a fresh process check by this pass. No RDP needed or attempted.

### Focused drift checks

All 48 distinct source paths from C01–C65 match local HEAD bytes after CRLF/LF normalization;
both HEADs equal Phase-1 anchors. Temporary `source_drift.json` retains each path/hash/result.
This confirms static source continuity, not live SQL parity. Matrix shapes read as 65×15 and
237×13; B0/F1M follow-ups are included. The Phase-1 audit, both matrices, decisions/next slice
and validation log were read with latest superseding updates.

| Contract rechecked | Current local evidence and implication |
|---|---|
| Legacy intake/time | `upload_routes/kvk_all_route.py:397` passes message.created_at; `kvk/services/kvk_all_import_service.py:72` requires Full Data. New source needs separate parser and UTC metadata. |
| Commit boundaries | `kvk/dal/kvk_all_import_dal.py:335`, `:486`, `:491` separate stage/ingest/recompute commits. Accepted facts and publication/delivery must have distinct durable outcomes. |
| Whole-KVK allocation/baseline | SQL `KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql:76` duplicate time/hash, `:84` MAX+1, `:144` growing baseline. New event/roster semantics cannot reuse them unchanged. |
| Recompute | SQL `KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql:44` deletes outputs, `:169` full outer join, `:180` fallback, `:251` power gate, `:261` Full branch. New exact endpoint, null/zero and frozen-final behavior requires separate calculation/publication. |
| Source DDL | SQL `KVK.KVK_Scan`, `KVK_AllPlayers_Raw`, `KVK_AllPlayers_Stage`, `KVK_Player_Baseline`, `KVK_Windows`, `KVK_CampMap`, `KVK_DKPWeights` and three `KVK_*_Windowed` Table snapshots: existing identity, bigint/nullability, int/tinyint constraints and FLOAT incompatibilities retained from Phase 1; key contracts directly rechecked. |
| Readers | `kvk/dal/kvk_reporting_dal.py:80`, `:114`, `:146`, `:189`, `:225` recalculate DKP and/or sum; SQL fn_KVK_*_Aggregated definitions remain legacy. Must bypass for new authoritative aggregates. |
| Export | SQL `KVK.sp_KVK_Get_Exports.StoredProcedure.sql:37` caps end to MAX scan; `gsheet_module.py:1939` generic numeric sums, `:2888` zero-fill pivot. New-source adapter must use selected periods/availability. |
| Mixed card | `kvk/dal/kvk_stats_card_dal.py:11` reads Windowed/Full and overall rank separately from main personal stats. Source/period context needs explicit separation. |
| Config | `proc_config_import.py:640`–`:642` unchanged sheet ranges; `:843`/`:883`/`:916` replace KVK partitions, `:1070` targets postcommit. Snapshot configuration, do not assume effective game time or refresh completion. |
| Daily namespace | SQL `dbo.IMPORT_STAGING_PROC_CORE.StoredProcedure.sql:211`–`:231` global KS4/KS5/receipt MAX allocation. New whole-KVK mapping must not touch it. |

References are repository-relative at the HEADs above; full source edge references remain in the
unchanged Phase-1 matrix. Proposed KVK.Source* names in the contract are new design entities,
not claims that those objects exist. Static dynamic SQL/trigger/job conclusions are carried forward
at Phase-1 scope: no new dependency rediscovery justified by unchanged source. Deployed/external
readers remain unverified; static absence never proves deployed absence.

### Private source evidence

Read `%LOCALAPPDATA%\K98\kvk-source-migration\evidence\README_EVIDENCE.md` first. It predates B0;
its missing-B0/period wording is historical. No private workbook or player row was published.
This pass rehashed the four designated Downloads files without opening/resaving workbooks.

| Role | Fresh SHA-256 / outcome | Previously validated Phase-1 evidence carried forward |
|---|---|---|
| B0 | `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`, match | 5,806 eligible, 36 kingdoms; operator time 2026-08-26 04:07 UTC |
| F1S | `331b224592c34d3968cb9c69dd5b55e536daea3b9323289d45bad381270afcb6`, match | 5,729 rows; 2026-09-05 15:26 UTC; keyed cells equal P1 despite byte difference |
| F1M | `1a736a749ce16ef1842f621cf8994045b19ec4726412b20bc6e97bb498c2b660`, match | 5,724 rows; 2026-09-06 13:04 UTC; 5,433 eligible start/middle pairs |
| F1E | `fb80119717b1cc3eb399dc5c81683ffd7f4f502568d0f630603981374b2e4486`, match | 5,720 rows; 2026-09-07 07:21 UTC; keyed cells equal P2; 5,410 eligible start/end pairs |

The source filenames, ranges, original P1/P2/A1/L1 hashes and methods are in the
[Phase-1 audit](phase_1_audit.md). Workbook shape/coverage/formula counts and re-export cell equality
were **not independently recalculated in Phase 2A**. Fresh file hashes bind this design to those
validated originals. No production DKP calculated; active coefficient values remain unqueried.
One eligible player has start/end but no middle; final gains must not require all three scans.
A1 is not certified as a Pass-4 revision. Live/final aggregates and later fights use synthetic
cases; only Pass 4 has occurred. Final overall evidence may follow when it exists.

## 6. Helpers Reused

None changed or executed as application helpers. Proposed reuse only: `core/interaction_safety.py`
safe_defer and permission/response patterns; canonical embed limits/packing; existing export section
binder mechanics; ImportAudit observability; RAW Sheets writes and CSV text escaping. Symbol/source
checks confirm locations, not drop-in compatibility. Existing legacy timestamp, coercion/fallback,
DKP recompute, summation and duplicate identity are deliberately not the new source's authority.

## 7. Refactor Findings

No runtime refactor. Source-specific extraction, reader selection and availability are part of
future migration scope. The known generic legacy export grouping/summing issue already has a
structured entry in `docs/reference/deferred_optimisations.md`; do not duplicate it. ProcConfig
WS1 owns its reliability design; no prerequisite implementation is proved for this design pass.
No new unrelated vulnerability/debt finding or risk acceptance made.

Skills applied: architecture-scope; SQL-validation; test-selection; security-review-routing;
PR-review for documentation-only final review; discord-command-feature for the proposed operator
journey/permissions. No implementation or broader security audit follows from using those skills.
No subagents used. Spreadsheets skill not needed: no new cell inspection or workbook analysis,
only hashes and the already validated Phase-1 source evidence.

## 8. Test Plan and actual document checks

Runtime pytest, SQL tests, imports, command registration execution, full pre-commit, application
startup, real cache/export/Discord actions are skipped: only Markdown is authored. Full hooks can
rewrite pre-existing files and run application checks; read-only checks cover this task's text.
No historical passing suite is presented as a fresh result. T01–T67 define future parser/service,
disposable-SQL, permission, concurrency, cache and consumer acceptance; none is executed code.

Actual safe check results are appended below after artifact review. Test selector recommendations
are recommendations, not evidence that application smoke or command registration ran.

## 9. Security Review Decision and Evidence

| Repository / target | Decision | Evidence / scope |
|---|---|---|
| Bot, exactly the seven Markdown paths in section 2 | **Documented skip** | Design and additive status only; no executable parser, permissions, SQL/data access, network, config, dependency, persistence or deployment behavior changes. Privacy and preservation checks cover task additions. |
| SQL, unchanged main at `fc0e94ebd2e0a98286069c8a8b71365dd5178657` | **Documented skip** | Read-only definition inspection; no task-authored or pre-existing SQL changes. |

Expected scan setup: not applicable. No Changes, standard or deep scan run. Future bot/SQL
implementation needs separate routing at exact targets, normally Changes with Deep off; this
skip is not security approval of an unimplemented architecture.

## 10. Deployment Steps

None executed or authorized. No executable migration/import/implementation packs prepared.
Architecture describes future ordering and rollback feasibility only. SQL verdict is design
compatibility reviewed, **not deployable SQL acceptance**. Production rows/jobs/readers, schema
migration evidence, approved configuration and isolated implementation tests remain later gates.
No secrets searched or access inferred from the RDP offer.

## 11. Deferred Optimisations and review stop

No new items; existing legacy-export and WS1 debt stays separately owned. No deferred register
change. Review artifact scope, current evidence and proposed choices at G2; do not treat this
documentation review as architecture approval or permission to prepare Phase 2B packs.

Recommended review decision: A01–A08 in the contract, especially B0 attribution/starting power,
partial-live stream display with frozen finals, and the private intake/correction journey.
Independent live rows/jobs and optional aggregate samples can follow at their dependent readiness
gates. **Stop at G2 for Chris Watts's architecture review.**

## Final document validation and review results

| Actual check | Result / boundary |
|---|---|
| Repository venv `-B scripts/validate_architecture_boundaries.py` | Passed, 0 Python files checked; docs-only scope, not whole-repo architecture acceptance. |
| Repository venv `-B scripts/validate_deferred_items.py` | Passed, 31 Markdown files checked, including pre-existing docs. |
| Repository venv `-B scripts/select_tests.py` with the seven exact manifest paths | Completed; recommends smoke imports and command registration. Both deliberately skipped for docs-only isolation; no runtime behavior changed. |
| Repository venv `-B scripts/validate_codex_security_routing.py` | Passed, 0 errors, 0 warnings. |
| `git diff --check` | Passed for tracked worktree changes, which include pre-existing work. New files/additions checked separately. |
| Offline document preservation/link/shape check via repository venv `-B` | Passed: 1,498 captured files preserved, four exact append prefixes, exactly three new files; 21 new local links resolve, 67 unique ordered scenario IDs and eight design decision IDs. UTF-8 decode, no trailing whitespace/conflict markers, paired fences, final newlines and size limits passed. |
| Worked synthetic arithmetic | Independently checked live DKP 1,000 and final DKP 1,800 using literal arithmetic; no application import or runtime test. |
| SQL status and bot staging | SQL clean; bot staging empty. No SQL task changes, no code/test/config writes. |
| Manual document review | New examples are synthetic; no real player rows/names/IDs, private workbooks, credentials or security findings copied. Current user decisions, field distinctions, all consumer groups and G2 stop checked. |

The first inventory comparison reported one existing Unicode-named archived task file as new
because the initial non-NUL Git listing used incompatible filename decoding. Rerun used `git
ls-files -z` with UTF-8; that tracked file had empty path status and matched HEAD after CRLF/LF
normalization. It was not edited or incorporated into task scope. This correction is check-tool
evidence, not a repository defect. Two unmatched documentation patch attempts failed before
changes; corrected targeted editing completed the intended clarification. Final review clarified
the observation discriminator/selected revision, numeric-formula field rejection, and atomic
routing/period selection. No change to settled source policy or task scope.

Review verdict: documentation packet complete for G2 consideration, with no remaining internal
blocking document finding identified. This is neither merge/release approval nor proof that the
proposed implementation works. Residual limits: active KVK-16 weights/mappings and deployed
rows/jobs/readers are not independently queried; semantic digest and transaction contracts are
proposals; real aggregate revision samples remain optional. No later fight or final report requested.


## EndScanID clarification follow-up — 2026-09-09

Scope: confirmed player-window behavior only. Targeted changes to contract and acceptance scenarios;
append-only programme/register/index/log updates. Same seven-path manifest as section 2; all files
already existed before this follow-up. Scenarios now total 70; prior 67-case validation is historical.
No new files, runtime/tests, SQL, helpers, deployments or deferred items. The user confirmed the
endpoint policy; conditional willingness to approve after no necessary updates is not G2 approval.
No Phase 2B work performed. Next eligible task after G2 is exact implementation planning for G3.

A02/A05 now describe sequential accepted player scan identities and an authorized EndScanID change
as the explicit correction. Normal interim reporting remains available with blank/pending end;
final calculation uses the exact configured end, and an updated unavailable end is pending rather
than falsely final. Metadata/re-export/UTC guards remain; observation-content and aggregate-final
corrections retain their separate controls. T68-T70 exercise 10→11/12→13→14 and recovery.

Both HEADs unchanged; SQL clean on entry. Current core documents match their previously read
versions by SHA-256. Pre-edit snapshot captures 1,502 files in the temporary endpoint-followup
folder. Bot documented security skip for precisely these seven Markdown changes: no executable,
config, permission, SQL, parsing, network or persistence behavior changed. SQL separate no-change
skip at the same recorded HEAD. No scan. Runtime pytest/smoke/registration remain deliberately
skipped for documentation-only scope; safe check results follow.

Follow-up checks passed: architecture (0 Python files), deferred items (31 Markdown files),
security routing (0 errors/warnings), explicit seven-path test selection and git diff --check.
Offline preservation check passed across 1,502 captured files: exactly seven authorized changes,
five original append prefixes preserved, all other captured files unchanged. Links/text hygiene
and 70 ordered unique scenario IDs passed; SQL clean and staging empty. Selector recommends
runtime smoke/registration, deliberately skipped as above. These are documentation checks only.


## Phase 2B delivery and G2 approval — 2026-09-09

Chris Watts explicitly approved: **“G2 approved, please proceed”.** G2 is approved, including
the EndScanID clarification and scenarios T68–T70. This supersedes earlier G2-pending/no-pack
statements as current status; their historical evidence remains intact. Phase 2B planning is
delivered in the [implementation plan](phase_2_implementation_plan.md)
and [planning evidence log](phase_2b_evidence_and_validation_log.md).
Ten bounded task packs and matching starters are prepared. **G3 remains pending per slice; S1 is
the recommended first approval.** No implementation, SQL change, live action, PR or deployment
is authorized by this delivery. S6 prepares readiness evidence and stops at separate G4 approval.
