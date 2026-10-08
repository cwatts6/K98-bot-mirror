# Phase 1 validation log

Date: 2026-09-09. Docs/read-only audit only; no release or design approval.

## Repository identity and authority

Bot: `C:\discord_file_downloader`, branch `main`, HEAD `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`.
Remotes: origin `https://github.com/cwatts6/K98-bot-mirror.git`; production `https://github.com/cwatts6/K98-bot.git`.
SQL: `C:\K98-bot-SQL-Server`, branch `main`, HEAD `fc0e94ebd2e0a98286069c8a8b71365dd5178657`.
Remote: origin `https://github.com/cwatts6/K98-bot-SQL-Server.git`. Initial SQL status empty.
No pull, fetch, checkout, reset, merge, discard, add, commit, push or PR creation performed.
Remote synchronization and deployed parity were not independently asserted.

Current user instructions authorized all five audit outputs and additive navigation/status updates.
Canonical template and current AGENTS/core reference docs were read. K98 architecture-scope,
SQL-validation, test-selection, PR-review and security-routing were used, with deferred capture
for the specifically evidenced legacy export item and spreadsheet read-only analysis for originals.
No subagents or standard/deep security scan were started.

## Initial bot worktree — not authored by this task

Initial modified/untracked file inventory was captured before documentation edits. SHA-256
checksums were retained in `%TEMP%/kvk-phase1-20260909/bot-before.json` to distinguish this task's
additions from prior work. The programme/register were already untracked and are not newly
invented task inputs. Existing runtime files had no diff.

- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/task_packs/Backlog Priority Assessment - 2026-09-09.md`
- `docs/task_packs/Bot Operational Reliability - Programme Pack.md`
- `docs/task_packs/Bot Operational Reliability Workstream 1 - Design and Manifests.md`
- `docs/task_packs/Codex Chat Starter - Bot Operational Reliability Workstream 1 ProcConfig Import Reliability and Truthful Completion Reporting.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration Phase 1 Audit and Validation.md`
- `docs/task_packs/Codex Chat Starter - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation.md`
- `docs/task_packs/Codex Task Pack - Bot Operational Reliability Workstream 1 ProcConfig Import Reliability and Truthful Completion Reporting.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration Phase 1 Audit and Validation.md`
- `docs/task_packs/Codex Task Pack - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation.md`
- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/Private Inventory Import and Support Sharing - Programme Pack.md`
- `README-DEV.md`
- `docs/reference/archive/deferred_optimisations_resolved.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Codex Chat Starter - Discord Embed Payload Safety Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting.md`
- `docs/task_packs/Codex Task Pack - Discord Embed Payload Safety Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/Codex Chat Starter - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md`
- `docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`
- `docs/task_packs/archive/README.md`

## Task-authored file manifest

New outputs:

- `docs/reference/kvk_source_migration/phase_1_audit.md`: findings, source ledger, local/deployed distinction and processing audit.
- `docs/reference/kvk_source_migration/phase_1_dependency_matrix.csv`: 65 dependency/consumer rows, required 15-column schema.
- `docs/reference/kvk_source_migration/phase_1_field_compatibility.csv`: 165 original-header mappings, required 13-column schema.
- `docs/reference/kvk_source_migration/phase_1_decisions_and_next_slice.md`: design options, recommendation, proposed manifests, tests and rollback limits.
- `docs/reference/kvk_source_migration/phase_1_validation_log.md`: checks and final scope evidence.

Additive updates only:

- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/task_packs/README.md`
- `docs/reference/README.md`
- `docs/reference/deferred_optimisations.md`

SQL modifications: **none**. No runtime, configuration, test fixture, workbook or player-evidence changes.

## Inspection and command record

PowerShell read/search batches used `Get-Content` (including bounded `-TotalCount` and
`Select-Object -Skip/-First` excerpts), `rg -n`, `rg --files`, `Get-ChildItem -Name`, and
`Select-String`. These read commands were not imports or execution of inspected Python/SQL.
The precise code/DDL paths and line ranges are indexed below and in the dependency matrix.
Searches covered KVK/import/scan/export/stats Python filenames, all direct whole-KVK object
references, FROM/JOIN/EXEC calls, registered commands/guards, configuration ranges, cache ownership,
SQL namespace allocation, trigger/job filenames and existing tests. Inspection was adaptive in
both directions, not based solely on matching command names.

| Command/check actually performed | Result |
|---|---|
| `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v` in each repository | Identities above; bot existing docs changes, SQL clean. |
| `git ls-files --modified --others --exclude-standard` + `Get-FileHash -Algorithm SHA256` | Initial per-file preservation baseline saved outside Git. |
| Read bot AGENTS, README-DEV, reference index, seven core/entry documents, task template, programme, Phase-1 pack and register | Scope and delivery shape resolved. Historical assessment directions not adopted. |
| Read private `README_EVIDENCE.md`, manifest, `prior_assessment/ASSESSMENT.md`; list original CSVs | B0 absent, four original roles located, superseded advice retained privately. |
| Read SQL `sql_schema/README.md`, `migrations/README.md`, `docs/SQL_DATA_MIGRATION_GUARDRAILS.md`; search AGENTS/SECURITY | SQL snapshots are reference; reviewed migrations deploy changes. No matching SQL AGENTS/SECURITY files found by scoped searches. Bot root SECURITY applies to bot audit policy. |
| Read active task/deferred indexes, canonical command reference, relevant ENV/diagnostics references and K98 skill checklists | Existing WS1/history/offload debt preserved; current registration used for consumer claims. |
| `rg` direct whole-KVK objects in bot `*.py` and SQL `sql_schema`; follow consumer and orchestration calls | C01–C65; raw/windowed/functions/views readers mapped. No direct bot runtime FightingDataset reader found. |
| `rg` SCAN_Dates/SCAN_DATES in config/export/import modules and SQL snapshots | No active import path found in that scope; historical sheet remains observational. |
| `rg` trigger references and SQL job filenames | No checked-in whole-KVK trigger edge found; job inventory query exists, not executed. Dynamic/deployed/external coverage remains a gap. |
| `load_workspace_dependencies` | Bundled runtime 26.905.11957 located; Python used for openpyxl analysis. |
| Bundled Python `inventory.py` | Four SHA256/size matches; exact sheet/header/key counts and formula types. |
| Bundled Python `reproduce.py` | Set overlap and diagnostic deltas reproduced; 216/216 within unit; corrected case-sensitive camp join, final 21/32 unequal. |
| Bundled Python `compare_prior.py` | 4900 player numeric cells, 36 coverage rows, 85 unmatched ID set, 216 kingdom deltas, 32 camp differences agree. |
| Bundled Python `build_matrices.py`, `update_docs.py` | Authored only named CSV/docs outputs and additive status/index/deferred updates. No imported repo runtime. |
| `python --version`; `Test-Path .venv/Scripts/python.exe` | System Python 3.11.9; repository venv exists. |
| Bundled Python `-B -m pytest ...` initial attempt | Did not run tests: bundled Python has no pytest. No packages installed. |
| Repository venv `-B -m pytest -q --noconftest -p no:cacheprovider tests/test_kvk_all_recompute_sql_contract.py tests/test_kvk_stats_card_sql_contract.py` | **14 passed**, one unknown `asyncio_mode` config warning because plugin autoload was disabled. |

For the successful test command, process-local `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and
`PYTHONDONTWRITEBYTECODE=1` were set. Selected tests read SQL/text only; conftest and pytest cache
were disabled to avoid runtime fixtures and persistent test-state writes. The first attempted
command also named `test_kvk_rankings_finalized_sql_contract.py`; it never ran because pytest was
missing. That file imports runtime services and was excluded from the final read-only selection.
These tests validate **legacy local contracts**, not new-source semantics, deployed SQL or B0.

Exploratory corrections: an initial `.agents` bot search and `stats_cache.py` read referenced
nonexistent paths; the actual cache is `player_stats_cache.py`. A guessed
`dbo.IMPORT_STAGING_FILE.StoredProcedure.sql` was absent; the actual intake is
`dbo.IMPORT_STAGING_PROC_CORE.StoredProcedure.sql`. A PowerShell wildcard passed literally to
`rg` for trigger files was replaced by a `-g` scoped search. Temporary prior-comparison script
initially recursed through its script loader, then used a mismatched KP label; both were corrected
and the successful rerun above is the retained result. These are audit-tool corrections, not
source defects or passing acceptance results.

## Original evidence and reproduction artifacts

Original roles/hashes/ranges and exact arithmetic methods are in `phase_1_audit.md` section 3.
Scripts and non-identifying aggregate JSON summaries are under `%TEMP%/kvk-phase1-20260909`;
original evidence stays under `%LOCALAPPDATA%/K98/kvk-source-migration/evidence`. No original was
resaved, no external workbook content executed, and no public row-level output produced.
Script hashes make the retained method version identifiable (these are temporary audit scripts,
not repository runtime or test changes):

- `inventory.py` SHA256 `aa1210f977dd49fec6e35a7ebab9048491badbe02dfef0a79a34b55d2c6af2fd`
- `reproduce.py` SHA256 `40bc54de940fecb46873045907825020ad849bbc9e4a6006d1b57933d1101d03`
- `compare_prior.py` SHA256 `5aa694f3d25f0dab0fc8bdf791c586bf066e19a8557dbfd58be5523d461462ab`
- `build_matrices.py` SHA256 `f55a11b674fe536baf3128019ee441e0b870a2e8337b22ed4cc0a8f3bff76d09`
- `update_docs.py` SHA256 `3ecbe7c8d456cd877537e713da2626d822af8046b6d6a7ef4bdcc601180484dd`

## Inspected code/DDL evidence manifest

Each path below is repository-relative at its recorded HEAD. The CSV links each claim to exact
symbols/line ranges; full-file entries mean the entire source was used for the relationship.
Ancillary core instructions, tests, DDL and search scopes are described above and in the audit.

| Repository | Path | Source lines |
|---|---|---:|
| Bot | `DL_bot.py` | 1–874 |
| Bot | `admin_helpers.py` | 1–304 |
| Bot | `bot_instance.py` | 1–2176 |
| Bot | `commands/kvk_cmds.py` | 1–653 |
| Bot | `commands/stats_cmds.py` | 1–758 |
| Bot | `daily_KVK_overview_embed.py` | 1–288 |
| Bot | `gsheet_module.py` | 1–3306 |
| Bot | `kvk/dal/kvk_all_import_dal.py` | 1–518 |
| Bot | `kvk/dal/kvk_history_dal.py` | 1–225 |
| Bot | `kvk/dal/kvk_lifecycle_dal.py` | 1–166 |
| Bot | `kvk/dal/kvk_rankings_dal.py` | 1–107 |
| Bot | `kvk/dal/kvk_reporting_dal.py` | 1–269 |
| Bot | `kvk/dal/kvk_stats_card_dal.py` | 1–91 |
| Bot | `kvk/rendering/kvk_rankings_csv.py` | 1–152 |
| Bot | `kvk/services/kvk_all_import_service.py` | 1–237 |
| Bot | `kvk/services/kvk_export_service.py` | 1–363 |
| Bot | `kvk/services/kvk_rankings_service.py` | 1–963 |
| Bot | `kvk/services/kvk_reporting_service.py` | 1–78 |
| Bot | `kvk/services/kvk_stats_card_service.py` | 1–321 |
| Bot | `kvk/target_cache_repository.py` | 1–861 |
| Bot | `kvk_all_importer.py` | 1–162 |
| Bot | `leadership_player_review/dal.py` | 1–649 |
| Bot | `player_self_service/governor_dashboard_dal.py` | 1–138 |
| Bot | `player_self_service/stats_service.py` | 1–562 |
| Bot | `player_stats_cache.py` | 1–1211 |
| Bot | `proc_config_import.py` | 1–1245 |
| Bot | `processing_pipeline.py` | 1–1033 |
| Bot | `services/kvk_all_import_audit_service.py` | 1–251 |
| Bot | `services/kvk_personal_service.py` | 1–54 |
| Bot | `stats_alerts/embeds/kingdom_summary.py` | 1–502 |
| Bot | `stats_alerts/embeds/kvk.py` | 1–558 |
| Bot | `stats_alerts/interface.py` | 1–137 |
| Bot | `upload_routes/kvk_all_route.py` | 1–630 |
| SQL | `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql` | 1–203 |
| SQL | `sql_schema/KVK.sp_KVK_Get_Exports.StoredProcedure.sql` | 1–147 |
| SQL | `sql_schema/KVK.sp_KVK_Ingest_Cleanup.StoredProcedure.sql` | 1–95 |
| SQL | `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql` | 1–480 |
| SQL | `sql_schema/KVK.vw_FightingDataset.View.sql` | 1–36 |
| SQL | `sql_schema/KVK.vw_Player_Overall_KVK_Rank.View.sql` | 1–50 |
| SQL | `sql_schema/dbo.IMPORT_STAGING_PROC_CORE.StoredProcedure.sql` | 1–518 |
| SQL | `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql` | 1–460 |
| SQL | `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql` | 1–988 |
| SQL | `sql_schema/dbo.fn_KVK_Camp_Aggregated.UserDefinedFunction.sql` | 1–40 |
| SQL | `sql_schema/dbo.fn_KVK_Kingdom_Aggregated.UserDefinedFunction.sql` | 1–39 |
| SQL | `sql_schema/dbo.fn_KVK_Player_Aggregated.UserDefinedFunction.sql` | 1–32 |
| SQL | `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql` | 1–693 |
| SQL | `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql` | 1–571 |
| SQL | `sql_schema/dbo.vDaily_PlayerExport.View.sql` | 1–125 |

## Test selection and limitations

Runtime pytest suite, importer smoke, command registration execution, bot startup, actual SQL
procedures, live permission checks and live exports are skipped: Phase 1 changes only documentation
and there is no need to load application/runtime fixtures or execute external side effects.
Static SQL tests above are deliberately narrower. Existing parser/import/upload/audit/reporting,
card/rank/history/cache and export tests were inspected as future regression anchors, not claimed
as run. No migration test can pass before an approved implementation exists.

No live configuration assertion is made. B0 acceptance, active KVK-16 weights/window assignments,
CampMap data, source-period association, deployed schemas/jobs/module drift and external readers
remain unverified. No credentials were read to work around that gap.

## Security decision and final review boundary

Bot: **documented skip** for the exact ten task-authored Markdown/CSV paths above. None changes
runtime, dependencies, permissions, input parsing, SQL execution, config, deployment or persistence.
SQL: **documented skip** for read-only inspection at the SQL HEAD; no task-authored SQL diff.
No standard/deep scan and no Changes scan were launched under this docs-only task.

K98 final-review scope is documentation/evidence quality, privacy, additive preservation and
accurate blockers. It is not architecture approval, migration acceptance or promotion readiness.
Final validator/diff/preservation results are recorded below.

## Final checks and delivery state

| Actual command/check | Result and limit |
|---|---|
| `.venv/Scripts/python.exe -B scripts/validate_architecture_boundaries.py` | Passed; **0 Python files checked** in this documentation-only diff. Not a whole-codebase architecture acceptance. |
| `.venv/Scripts/python.exe -B scripts/validate_deferred_items.py` | Passed; 26 Markdown files validated, including pre-existing documentation. |
| `.venv/Scripts/python.exe -B scripts/select_tests.py` | Completed; recommended smoke imports and command registration. Both deliberately skipped for the read-only/docs-only isolation reasons above. |
| `.venv/Scripts/python.exe -B scripts/validate_codex_security_routing.py` | Passed; 0 errors, 0 warnings. |
| `git diff --check` | Passed. This covers tracked worktree diff; CSV structure and new Markdown links checked separately. |
| `git diff --stat`, `git diff --cached --name-only`, final `git status --short` | No staged files. Overall tracked diff includes pre-existing user edits and must not be attributed to this task. Task manifest remains exactly the ten paths above. |
| SQL `git status --short`, `git rev-parse HEAD`, `git diff --stat` | Clean, unchanged recorded HEAD, no SQL diff. |
| Repository venv `-B %TEMP%/kvk-phase1-20260909/final_check.py` | All 22 initially dirty/untracked files preserve exact original content; appended files preserve original byte prefixes. Previously clean reference index prefix matches HEAD. CSVs: 65 × 15 and 165 × 13, valid shape, unique dependency IDs, valid referenced consumers/source ranges; four new Markdown local links resolve. |
| Bundled Python `-B %TEMP%/kvk-phase1-20260909/privacy_check.py` | All four original SHA-256 hashes unchanged; no original P1/P2 player-ID tokens in the five outputs. Manual output review found no player rows/names. Originals and row-level evidence remain private. |
| `git check-ignore -v` for both delivered CSVs | Existing `.gitignore:93` (`*.csv`) ignores both matrices. They exist and are delivered locally; no ignore-rule edit or staging performed. A future authorized documentation commit must explicitly include these two non-identifying audit CSVs. |

Temporary final-check scripts and `final_checks.json` remain outside the repository. These checks
validate the audit artifacts and preservation boundary, not live SQL, provider period semantics,
master-roster acceptance or migration readiness. No gate is self-approved. Stop for operator review.

## B0 follow-up execution — 2026-09-09

Scope: original-byte inspection of newly supplied B0, comparison with original P1/P2, and additive
Phase-1 evidence/status updates. Both HEADs unchanged from above; SQL clean. No Git synchronization,
staging, runtime/SQL/test edits, real imports or workbook copies into Git. Existing historical
findings preserved. User decisions now settle per-fight replacement reports, separate final overall
report and separate-source direction; no implementation or detailed-design approval inferred.

Changed paths in this follow-up: `phase_1_audit.md`, `decision_and_evidence_register.md`,
`phase_1_decisions_and_next_slice.md`, `phase_1_field_compatibility.csv`, `phase_1_validation_log.md`
(all in this directory), `docs/task_packs/KVK Source Migration - Programme Pack.md`, and
`docs/task_packs/README.md`. Dependency matrix unchanged; source graph did not change.
Field matrix appends 36 B0 rows (201 total, 13 columns); original 165 rows remain historical,
including their then-pending B0 decision text. Latest follow-up sections override earlier status.

Methods/commands: current instructions/template/pack/register/evidence README/security routing read;
`git status --short` and `git rev-parse HEAD` in both repos; bundled dependency lookup;
bundled Python `-B b0_inspect.py`, `-B b0_validate.py` and `-B b0_docs.py` in
`%TEMP%/kvk-phase1-20260909`. Checks use read-only openpyxl with formula-preserving reads and
external links disabled. B0 SHA-256/size/ranges, unique/integral identities, header equality,
kingdom sets, exact three-way membership, endpoint metric availability/deltas and formula counts
are recorded in `b0_validation.json` outside Git. No player names/IDs are emitted in these summaries.
`b0_before.json` records this follow-up's pre-edit hashes and lengths for additive preservation.

Security routing: **Bot documented skip** for these seven documentation/aggregate-CSV paths only;
no executable input-handling, permission, data-access, persistence or deployment behavior changes.
**SQL documented skip:** read-only status at unchanged HEAD, no SQL diff. No scan launched.
Runtime pytest/smoke/command-registration skipped for this evidence-only update; earlier 14-test
result is historical and is not claimed as a rerun. No new deferred optimisation identified.

Follow-up results: repository venv `-B scripts/validate_architecture_boundaries.py` passed
(0 Python files); `validate_deferred_items.py` passed (26 Markdown files); `select_tests.py`
completed and recommended the deliberately skipped runtime smoke/registration checks;
`validate_codex_security_routing.py` passed (0 errors/warnings); `git diff --check` passed.
Bundled Python `-B b0_final_check.py` passed: exactly seven append-only documentation changes,
all captured original byte prefixes preserved, 201-by-13 field CSV including 36 B0 mappings,
B0 hash unchanged, no B0 player-ID tokens in additions, clean SQL and nothing staged.
Both CSV audit outputs remain covered by the existing `*.csv` ignore rule.

## Pass 4 follow-up execution — 2026-09-09

Scope: three supplied private player files, operator-provided baseline/fight timestamps, flexible
naming, SQL/config sync attestation and RDP offer. No live access needed for design; not attempted.
Both branch/HEAD/remotes rechecked unchanged; SQL clean. Workbook contents treated as data only.

Actual checks: bundled Python `-B fight1_inspect.py` and `-B fight1_validate.py`, read-only openpyxl,
original-byte SHA-256, sheet/row/header/formula inventory, positive integral unique IDs, kingdom
counts, complete keyed-cell comparison with original P1/P2, B0 membership and four-interval metric
availability/regression counts. Results in `fight1_inventory.json`/`fight1_validation.json` under
`%TEMP%/kvk-phase1-20260909`; no player rows in those summaries. `fight1_snapshot.py` captures
pre-edit lengths/hashes; `fight1_docs.py` writes documentation only. Searches limited to SQL repo
exports/deploy/docs/migrations and configuration-related snapshots. Read Windows/Weights/Map DDL
and deployment example settings; no credentials or active DB data read. No database tool for this
SQL instance was found among callable capabilities; no alternate connection was guessed.

Nine changed paths: Phase-1 audit, decision register, next-slice document, validation log, field CSV;
programme, task index, and prepared Phase-2 task pack/chat starter. All are additive except targeted
updates to the two newly prepared Phase-2 instruction files to remove obsolete missing-time requests.
Field CSV appends 36 F1M rows (237 total); F1S/F1E share the validated P1/P2 cell-value mappings.
Historical B0 rows' unverified-time wording is superseded by the operator timestamp in this follow-up.
Dependency graph unchanged. Original private inputs and original audit rows are preserved.

Bot security documented skip: these nine documentation/aggregate-CSV paths only, no executable
input handling, permission, persistence, SQL, config or deployment change. SQL documented skip:
no task-authored changes at unchanged HEAD. No scan or new deferred item. Runtime pytest/import
smoke/command registration skipped for evidence/docs-only scope; no historical test result reused
as a new run. Two initial text patches did not match existing wording and failed without changes;
corrected targeted patches succeeded. Validation outcomes follow below.

Follow-up checks passed: architecture validator (0 Python files), deferred validator (28 Markdown
files), explicit-path test selection completed, security-routing validator (0 errors/warnings),
and `git diff --check`. Repository-venv `-B fight1_final_check.py` passed seven append-prefix
preservation checks, all three new source hashes unchanged, 237-by-13 CSV shape with 36 F1M rows,
clean SQL and empty staging. Manual instruction review confirms current times, flexible naming,
player-versus-aggregate distinction and no request for an unavailable later fight. No private rows
were written to repository outputs. The existing `*.csv` ignore rule still applies to both matrices.
