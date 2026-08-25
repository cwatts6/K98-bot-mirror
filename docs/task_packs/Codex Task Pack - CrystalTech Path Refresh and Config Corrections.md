# Codex Task Pack — CrystalTech Path Refresh and Config Corrections

## 1. Task Header

- Task name: `CrystalTech Path Refresh and Config Corrections`
- Date: `2026-08-25`
- Owner/context: `Chris Watts — latest in-game CrystalTech path changes and correction of known config defects`
- Task type: `bug fix / configuration data update`
- One-pass approved: `yes`
- One-pass basis: The operator requested a PR-ready, super-simple deployment task after the source JSON and workbook had been reviewed and the implementation contract below was locked.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `SECURITY.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also review:

- `docs/reference/Promotion Guide.md`
- `docs/templates/Codex Task Pack Template.md`
- `config/crystaltech_paths.v1.json`
- `crystaltech_config.py`
- `crystaltech_service.py`
- `commands/admin_cmds.py`
- `tests/test_crystaltech_service.py`
- `assets/crystaltech/`

No SQL-facing work is included. Do not open or modify `C:\K98-bot-SQL-Server` unless an unexpected SQL dependency is discovered and reported.

## 3. Objective

Update the production CrystalTech path configuration to the reviewed latest in-game path data, correct all known UID/name/level/image defects in the approved change set, and deliver a focused PR that is safe to promote and deploy.

Keep the implementation configuration-led. Do not change CrystalTech command behaviour, loader/service architecture, SQL, assets, player progress, or Discord command registration.

## 4. Background

The operator supplied:

- the current production JSON exported from `config/crystaltech_paths.v1.json`
- an Excel review workbook containing the intended new path data
- confirmation that the existing `/crystaltech validate` command can be run after deployment

The supplied original is byte-for-byte the current mirror file:

- file size: `118200`
- Git blob SHA-1: `cd36a2402714c2e862ebd1e98b13444a854c43e9`
- SHA-256: `cdf57b8db36517e4de125e0db44f5b9f3b133072ca6d1bda82f55888cc1dd21f`

The raw workbook was not safe to export unchanged. Review found:

- 12 of 16 recorded original audit issues resolved
- four recorded original issues still unresolved
- two duplicate/missing step-order pairs
- one incorrect `Path_Order`
- two newly copied `Special Concoction II` naming defects
- stale audit counts and stale `updated_at_utc`

A corrected workbook and reviewed JSON candidate are supplied with this task:

- `crystaltech_paths_review_corrected.xlsx`
- `crystaltech_paths.v1.proposed.json`
- candidate SHA-256: `59daed30ae758a0b86f7d83168dd1b30519d27b3bfcabe6341d975dc76bb0bca`

Use the proposed JSON as the implementation source. The workbook and review report are evidence/supporting material; they are not runtime files.

## 5. Scope

### In Scope

- Replace the contents of `config/crystaltech_paths.v1.json` with the reviewed proposed candidate.
- Preserve schema version `1.0`, locales, common blocks, path metadata, path order, and key shape.
- Refresh `meta.updated_at_utc` to the actual UTC implementation/commit time in the existing ISO-8601 `Z` format.
- Preserve `meta.effective_from_kvk = 14`, `uid_namespacing`, and `includes_removed`.
- Deliver exactly eight paths and 404 path steps.
- Preserve all existing step UIDs except the one explicitly removed below.
- Apply the additions, removal, ordering, name, target-level, image, and cost changes encoded in the proposed candidate.
- Add focused regression coverage for the production config data contract.
- Run the existing local validator before PR handoff.
- Run the existing post-deployment `/crystaltech validate` command as a deployment verification step.
- Create a focused branch, commit, push, and PR against `K98-bot-mirror/main`.

### Out of Scope

- No changes to `crystaltech_config.py`, `crystaltech_service.py`, command handlers, Discord views, or command registration unless a genuine blocker is found and explicitly reported before scope expansion.
- No SQL changes.
- No asset additions, removals, or image-file edits.
- Do not update any archive, copy, broken, old, output, or experimental CrystalTech JSON files under `config/`.
- Do not reset, migrate, rewrite, or delete runtime CrystalTech player progress.
- Do not invoke `/crystaltech admin_reset`.
- Do not alter the four pre-existing consistency groups listed under Refactor Decisions without separate operator approval.
- Do not merge, promote, or deploy the PR; hand it back ready for operator review and deployment.

## 6. Source Data Contract

### Path Counts and Crystal-Cost Totals

| Path | Steps | Total crystal cost |
|---|---:|---:|
| `f2p_low_infantry` | 43 | 47,997,500 |
| `f2p_low_archers` | 42 | 47,997,500 |
| `f2p_low_cavalry` | 44 | 53,357,500 |
| `f2p_low_siege` | 51 | 64,189,500 |
| `mid_high_infantry` | 54 | 59,097,500 |
| `mid_high_archer` | 54 | 59,097,500 |
| `mid_high_cavalry` | 54 | 58,001,500 |
| `mid_high_siege` | 62 | 67,726,500 |

Aggregate path steps: `404`.

### Added Step UIDs

- `f2p_low_infantry__swift_marching_ii_lv8`
- `f2p_low_infantry__cultural_exchange_lv15`
- `f2p_low_infantry__swift_marching_iii_lv10`
- `f2p_low_infantry__special_concoction_ii_lv3`
- `f2p_low_archer__cultural_exchange_lv15`
- `f2p_low_archer__fleet_of_foot_iii_lv10`
- `f2p_low_archer__special_concoction_ii_lv3`
- `f2p_low_cavalry__cultural_exchange_lv15`
- `f2p_low_cavalry__swift_steeds_iii_lv10`
- `f2p_low_cavalry__special_concoction_ii_lv3`
- `f2p_low_siege__cultural_exchange_lv15`
- `f2p_low_siege__reinforced_axles_iii_lv10`
- `f2p_low_siege__special_concoction_ii_lv3`
- `f2p_low_siege__siege_expert_lv4`

### Removed Step UID

- `f2p_low_siege__siege_expert_lv2`

Do not add an automatic progress migration for the removed UID. Before deployment handoff, state clearly that existing runtime progress was not inspected in the scrubbed mirror and must not be reset automatically.

### Locked Semantic Corrections

The final JSON must satisfy all of these:

- every F2P `Karaku Reports` display name is capitalised exactly as `Karaku Reports`
- `f2p_low_cavalry__special_concoction_ii_lv2` name is `Special Concoction II`
- `f2p_low_cavalry__special_concoction_ii_lv3` name is `Special Concoction II`
- `f2p_low_siege__special_concoction_ii_lv2` name is `Special Concoction II`
- `f2p_low_siege__special_concoction_ii_lv3` name is `Special Concoction II`
- `f2p_low_siege__reinforced_axles_i_lv3` name is `Reinforced Axles I`
- `f2p_low_siege__reinforced_axles_i_lv5` name is `Reinforced Axles I`
- F2P Iron Infantry steps use `iron_infantry.png`
- `mid_high_cavalry__fleet_of_foot_ii_lv10` name is `Fleet of Foot II`
- `mid_high_siege__siege_provisions_lv10` target level is 10
- `mid_high_siege__reinforced_axles_iii_lv10` target level is 10
- all `_lvN` suffixes match `target_level`
- no new image filename is introduced; the final candidate uses the same 31 distinct image filenames as the original

### Locked Array Ordering

JSON arrays are the runtime order. Preserve the order in the supplied proposed candidate exactly.

Particular regression-sensitive positions:

- `f2p_low_archers` is a contiguous 42-step list; `cultural_exchange_lv15` is followed by `larger_camps_lv5`
- `f2p_low_cavalry__cultural_exchange_lv15` belongs to the cavalry path at position 32
- `f2p_low_siege` is a contiguous 51-step list; `siege_provisions_lv10` is followed by `reinforced_axles_iii_lv5`
- no `Step_Order` or `Path_Order` helper fields are written into runtime JSON

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Perform a concise config-only scope check before editing. One-pass execution is approved, so no approval stop is required unless scope expands. |
| `k98-discord-command-feature` | `not applicable` | No command, interaction, permission, view, or registration change. |
| `k98-sql-validation` | `not applicable` | No SQL dependency or contract change. |
| `k98-test-selection` | `use` | Select focused config tests plus repository baseline gates. |
| `k98-deferred-optimisation-capture` | `use if needed` | Capture only genuinely out-of-scope non-security findings; do not expand this PR. |
| `k98-pr-review` | `use` | Review the final diff and PR handoff. |
| `k98-promotion-check` | `use` | Produce promotion/deployment handoff evidence; do not perform production deployment. |
| `k98-security-review-routing` | `use` | Route this runtime configuration/deployment change to a diff-focused Changes review. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `K98-bot-mirror` | `Changes review` | final `origin/main...HEAD` diff, expected to contain only `config/crystaltech_paths.v1.json`, the focused test, and task-pack documentation if committed | `Changes + Deep Off` using `$codex-security:security-diff-scan` | retain scan result or explicit no-finding evidence in the handoff |

Reason: this PR changes checked-in runtime configuration and deployment behaviour, so a documented skip does not meet the repository template's skip rule. Do not run a standard or deep codebase audit.

## 8. Mandatory Workflow

One-pass implementation is approved for the locked scope:

1. Read required repository guidance.
2. Create a branch from current `main`, suggested name: `fix/crystaltech-path-refresh-2026-08`.
3. Audit the current production config, candidate hash, loader/validator entry points, and current tests.
4. Confirm the current production file is the expected Git blob before overwriting it.
5. Copy the reviewed candidate content into `config/crystaltech_paths.v1.json`.
6. Refresh only `meta.updated_at_utc` to the actual implementation UTC timestamp.
7. Add focused production-config regression tests.
8. Run validation and focused tests.
9. Inspect the final Git diff for accidental changes, archive-file edits, key loss, path/step omissions, or formatting churn.
10. Run `k98-pr-review`.
11. Run the selected diff-focused Codex Security Changes review with Deep Off.
12. Commit, push, and create/update a PR against `K98-bot-mirror/main`.
13. Return the complete handoff. Do not merge or deploy.

Stop and report before continuing only if:

- the current production config no longer matches the reviewed source
- the proposed candidate hash differs
- a runtime-code, SQL, asset, schema, or progress migration appears necessary
- the existing validator reports an issue that requires changing scope
- existing production progress evidence shows the removed UID requires an operator-approved migration

## 9. Audit Requirements

Confirm and record:

- current branch and clean working tree
- current `config/crystaltech_paths.v1.json` Git blob/hash
- the config loader and validator paths
- the CLI validator syntax
- `/crystaltech validate` and `/crystaltech reload` already exist and require no command change
- no distinct image filename is added or removed
- no archive/copy JSON file is touched
- no SQL or command registration change is required
- whether any tracked test already validates the production config
- restart/cache behaviour: a bot restart loads the new config; `/crystaltech reload` is only needed if deployment does not restart the process
- no automatic progress reset or migration is performed

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Runtime config | `config/crystaltech_paths.v1.json` |
| Config loading/validation | existing `crystaltech_config.py`; review only |
| Runtime cache/reload | existing `crystaltech_service.py` and `/crystaltech reload`; review only |
| Discord validation command | existing `/crystaltech validate`; review only |
| Assets | existing `assets/crystaltech/`; validate only |
| Focused tests | `tests/test_crystaltech_config_data.py` or the nearest existing CrystalTech config test module |
| SQL | not applicable |
| Command registration | unchanged |

## 11. Likely Files

### Review

- `AGENTS.md`
- `README-DEV.md`
- `SECURITY.md`
- `docs/reference/README.md`
- `docs/reference/Promotion Guide.md`
- `config/crystaltech_paths.v1.json`
- `crystaltech_config.py`
- `crystaltech_service.py`
- `commands/admin_cmds.py`
- `assets/crystaltech/`
- `tests/test_crystaltech_service.py`

### Modify

- `config/crystaltech_paths.v1.json`

### Create or Modify for Regression Coverage

- `tests/test_crystaltech_config_data.py` if no suitable existing config-data test exists

### Do Not Modify

- `config/crystaltech_paths.v1 - Copy.json`
- `config/crystaltech_paths.v1 - archive1.json`
- `config/crystaltech_paths.v1_broken.json`
- `config/crystaltech_paths.v1_old.json`
- `config/crystaltech_paths.v1_out.json`
- `config/crystaltech_paths.v1highinf.json`
- `config/crystaltech_paths.v1path6.json`
- runtime progress/state files
- commands, services, assets, SQL, or registration references

## 12. Implementation Requirements

- Treat `crystaltech_paths.v1.proposed.json` as the approved data source.
- Do not regenerate from the uncorrected workbook.
- Preserve JSON readability and existing indentation/key ordering.
- Avoid unrelated formatting churn.
- Keep all numeric values as JSON integers.
- Keep `includes` arrays and common blocks unchanged.
- Preserve all path IDs, groups, display labels, troop types, and path order.
- Update `updated_at_utc`; do not change `effective_from_kvk`.
- Add a focused test that loads the real production config through `load_and_validate_config`.
- The test must fail with useful output if the validation report is not OK.
- The test must assert:
  - exact path IDs and order
  - exact path step counts
  - exact crystal-cost totals
  - unique path step UIDs
  - required added UIDs are present
  - the removed siege-expert level-2 UID is absent
  - the locked semantic corrections above
  - every `_lvN` suffix matches `target_level`
  - the expected regression-sensitive array ordering
- Do not change the validator implementation merely to make the new data pass.
- If a validator warning/error reveals a genuine data defect, fix the JSON data and document it.
- Keep command surface count and behaviour unchanged; command registration validation may be skipped with a precise no-command-change reason.
- Preserve restart safety; no progress reset.

## 13. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Four original audit findings left unresolved in the raw workbook | `fix now` | Required for UID/name consistency. |
| Two copied level-3 Special Concoction II naming defects | `fix now` | New rows must not repeat the old defect. |
| Duplicate/missing Excel step orders and cavalry path-order typo | `fix now` | Required for deterministic round-trip evidence; runtime JSON order is supplied in the corrected candidate. |
| Stale workbook audit counts and metadata | `fix now` | Corrected evidence and runtime freshness metadata are required. |
| Existing validator does not check semantic UID/name correspondence | `fix now through focused regression test` | Avoid changing runtime validator architecture for a data-only PR. |
| F2P Swift Steeds I image mismatch pattern | `defer / preserve` | Pre-existing and not authorised by supplied workbook data. |
| F2P Swift Marching III image mismatch pattern | `defer / preserve` | Pre-existing and not authorised by supplied workbook data. |
| F2P siege Improved Projectiles I image mismatch pattern | `defer / preserve` | Pre-existing and not authorised by supplied workbook data. |
| Mid/High `Archers Focus` spelling variant | `defer / preserve` | In-game authoritative spelling is not established by supplied sources. |
| Archive/copy JSON proliferation | `out of scope` | Do not mix cleanup into the production-data PR. |

Any deferred item added to repository documentation must use the required structured format. Do not create deferred entries merely to restate the four preserved source-data warnings unless repository guidance requires it.

## 14. Testing Requirements

### Required Data and Validator Checks

```powershell
.\.venv\Scripts\python.exe -m json.tool .\config\crystaltech_paths.v1.json > $null
.\.venv\Scripts\python.exe -m crystaltech_config --config .\config\crystaltech_paths.v1.json --assets .\assets\crystaltech
.\.venv\Scripts\python.exe -m pytest -q tests\test_crystaltech_config_data.py
```

Also run the nearest existing CrystalTech tests selected by `k98-test-selection`, including:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_crystaltech_service.py
```

### Repository Gates

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run broader tests only if selected by repository guidance or if focused checks reveal a wider dependency. Do not expand scope to unrelated pre-existing failures; report them.

### Manual Diff Checks

- only expected files changed
- eight paths and 404 path steps
- four unchanged common-block steps
- exact counts and totals from the source contract
- no duplicate path IDs or step UIDs
- no new/removed distinct image filename
- no accidental helper columns such as `Path_Order`, `Step_Order`, review status, or notes in JSON
- only `updated_at_utc` differs in metadata
- no archive/copy config file changed

### Post-Deployment Verification for Operator Handoff

After the operator promotes and deploys from `K98-bot/main`:

1. Confirm the bot restarted cleanly and CrystalTech config loaded without startup errors.
2. Run `/crystaltech validate`.
3. Expect a green/OK validation report with no errors or warnings.
4. Run `/crystaltech reload` only if the deployment did not restart the bot or the old config remains cached.
5. Run `/crystaltech validate` again after any reload.
6. Smoke-test `/mykvkcrystaltech` through at least one F2P and one Mid/High path, confirming the new step sequence renders and can advance without UID errors.
7. Do not run `/crystaltech admin_reset`.
8. If validation fails, revert the single production config commit, restart/reload, and validate again.

## 15. Acceptance Criteria

- [ ] The production JSON is based on the reviewed candidate with matching source hash before timestamp refresh.
- [ ] `schema_version`, locales, common blocks, path metadata, path IDs, and path order are preserved.
- [ ] `updated_at_utc` is refreshed; other metadata is unchanged.
- [ ] Exactly eight paths and 404 path steps are present.
- [ ] Exact path counts and crystal-cost totals match the locked contract.
- [ ] All 14 added UIDs are present and the one removed UID is absent.
- [ ] All 16 original audit findings are resolved.
- [ ] All five newly detected workbook defects are resolved.
- [ ] No helper/review columns leak into JSON.
- [ ] No new image filename is introduced and all referenced assets pass the existing validator.
- [ ] Production-config regression tests pass.
- [ ] Existing CrystalTech service tests pass.
- [ ] Required repository validation gates pass or unrelated failures are documented.
- [ ] No commands, SQL, assets, progress, or archive/copy configs changed.
- [ ] Diff-focused Codex Security Changes review ran against the final base/head with Deep Off.
- [ ] `k98-pr-review` and promotion handoff are complete.
- [ ] PR includes clear risk and rollback instructions.
- [ ] Operator deployment verification lists `/crystaltech validate` and explicitly prohibits automatic reset.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. Source-Contract Reconciliation
6. SQL Changes
7. Commands / UI Changes
8. Helpers Reused
9. Refactor Findings
10. Test Plan and Results
11. Security Review Decision and Evidence
12. PR Link and Commit
13. Deployment / Rollback Steps
14. Deferred Optimisations

State explicitly:

- no SQL changes
- no command or UI changes
- no progress migration/reset
- no asset changes
- no archive/copy JSON changes

## 17. PR Summary Template

```md
## Summary

- Refresh the production CrystalTech paths to the reviewed latest in-game data.
- Resolve all known audit and round-trip defects in the approved change set.
- Add focused production-config regression coverage.

## Changes

- Updated `config/crystaltech_paths.v1.json` from 391 to 404 path steps.
- Added 14 step UIDs and removed the superseded siege-expert level-2 UID.
- Corrected UID/name/image/target-level/cost/order data per the locked review contract.
- Refreshed `meta.updated_at_utc`.
- Added focused config-data validation tests.

## Tests

- `python -m json.tool config/crystaltech_paths.v1.json`
- `python -m crystaltech_config --config config/crystaltech_paths.v1.json --assets assets/crystaltech`
- `python -m pytest -q tests/test_crystaltech_config_data.py`
- `python -m pytest -q tests/test_crystaltech_service.py`
- repository validation gates and pre-commit

## Security Review

- Decision: `Changes review`
- Repository / target: `K98-bot-mirror origin/main...HEAD`
- Expected setup / execution: `Changes + Deep Off`
- Evidence: `<completed diff-scan result>`

## Deferred Optimisations

- Preserved the documented pre-existing image/spelling consistency warnings because the supplied source did not authorise those changes.

## Risk / Rollback

- Risk is limited to CrystalTech path data, ordering, and progress-UID compatibility.
- No automatic progress reset or migration is included.
- Roll back by reverting the config commit, restarting/reloading the bot, and running `/crystaltech validate`.
```
