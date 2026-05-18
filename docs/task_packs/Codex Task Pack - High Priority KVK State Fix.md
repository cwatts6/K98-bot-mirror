# Codex Task Pack — High Priority KVK State Fix

## 1. Task Header

- Task name: `Fix active KVK state when KVK_END_SCAN is not yet known`
- Date: `2026-05-18`
- Owner/context: `Production incident: stats_alerts and targets still showing Pre-KVK after fighting opened`
- Task type: `bug fix`
- One-pass approved: `yes`

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the conditional references defined by `docs/reference/README.md`.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

Fix the production KVK-state logic so the bot correctly treats the current KVK as fighting/active when `PASS4_START_SCAN` has been reached, even if `KVK_END_SCAN` is still `NULL`.

This must correct both:
- `stats_alerts` choosing the wrong Pre-KVK embed.
- `/mykvktargets` / targets cache marking targets as Pre-KVK instead of Active.

## 4. Background

Production data confirms the current KVK is fighting:

```sql
KVK_NO = 15
KVK_NAME = Tides
MATCHMAKING_SCAN = 837
PASS4_START_SCAN = 866
KVK_END_SCAN = NULL
FIGHTING_START_DATE = 2026-05-17
MaxScanOrder = 875

Current behaviour is wrong because the state logic requires KVK_END_SCAN to be an integer. Since the current KVK end scan is not known yet, the bot treats fighting as closed and falls back to Pre-KVK.

Expected fighting condition:

MaxScanOrder >= PASS4_START_SCAN
AND (
    KVK_END_SCAN IS NULL
    OR MaxScanOrder <= KVK_END_SCAN
)
5. Scope
In Scope
Review and fix KVK-state detection used by:
stats_alerts/kvk_meta.py
kvk_state.py
targets_sql_cache.py
target_utils.py
target embed state handling where relevant
Allow active/fighting KVK state when KVK_END_SCAN is NULL.
Preserve historical KVK behaviour where KVK_END_SCAN is populated.
Ensure target cache is refreshed or invalidated after state correction.
Add or update focused tests for:
fighting open with KVK_END_SCAN = NULL
fighting open with known end scan
not fighting before PASS4_START_SCAN
ended when MaxScanOrder > KVK_END_SCAN
invalid/missing PASS4_START_SCAN
Add operational logging that clearly reports:
kvk_no
matchmaking_scan
pass4_start_scan
kvk_end_scan
max_scan_order
resolved state
Out of Scope
Visual redesign of stats alerts or target embeds.
Changing target formulas.
Changing KVK sheet import process unless a schema/cache mismatch is found.
Broad KVK-state service refactor beyond what is needed to fix the incident.
6. Codex Skills To Use
Skill	Decision	Notes
k98-architecture-scope	use	Confirm affected modules and avoid over-refactor.
k98-discord-command-feature	use	Targets and stats alerts are Discord-facing embed flows.
k98-sql-validation	use	Logic depends on dbo.KVK_Details, scan data, and SQL-backed target cache.
k98-test-selection	use	Select focused regression tests and any required smoke tests.
k98-deferred-optimisation-capture	use	Capture any wider duplicated KVK-state logic as deferred work if not fixed now.
k98-pr-review	use	Required before handoff due to production-impacting state logic.
k98-promotion-check	use	Required before production deployment.
7. Mandatory Workflow

Proceed in one pass because this is a high-priority production fix.

Do not stop after audit unless a dangerous ambiguity is found.

8. Audit Requirements

Review:

stats_alerts/kvk_meta.py
stats_alerts/interface.py
kvk_state.py
targets_sql_cache.py
target_utils.py
targets_embed.py
tests covering KVK state, targets cache, and stats alerts
SQL repo definition for dbo.KVK_Details
any existing docs or references for KVK state naming

Identify every place that assumes:

KVK_END_SCAN is not None

or equivalent SQL/Python logic.

9. Architecture Targets
Keep Discord interaction code thin.
Keep KVK-state resolution in shared service/helper logic.
Avoid duplicating scan-window logic in multiple embed modules.
Do not add direct SQL to commands/views.
Prefer a reusable function such as:
is_scan_within_open_window(start_scan, end_scan, max_scan_order)

or an equivalent existing helper if already present.

10. Likely Files
Review
stats_alerts/kvk_meta.py
stats_alerts/interface.py
kvk_state.py
targets_sql_cache.py
target_utils.py
targets_embed.py
tests/
SQL repo: C:\K98-bot-SQL-Server
Modify

Likely:

stats_alerts/kvk_meta.py
kvk_state.py
targets_sql_cache.py
focused tests
Create

Only create new helper/test files if this keeps the fix cleaner.

11. Implementation Requirements
Required logic change

The fighting-open check must support unknown end scan:

if not isinstance(pass4_scan, int) or pass4_scan <= 0:
    return False

if end_scan is not None:
    if not isinstance(end_scan, int) or end_scan <= 0 or end_scan < pass4_scan:
        return False

return max_scan_order >= pass4_scan and (
    end_scan is None or max_scan_order <= end_scan
)

Apply equivalent logic wherever KVK state is resolved.

Target cache requirement

After fixing state logic:

Ensure refresh_targets_cache() writes the corrected active/fighting state.
Ensure stale cache does not keep old Pre-KVK state after deploy.
Add a deployment step to refresh or delete PLAYER_TARGETS_CACHE.
Logging requirement

Add one clear info/debug log when resolving KVK state, including:

kvk_no
matchmaking_scan
pass4_start_scan
kvk_end_scan
max_scan_order
resolved_state
reason
12. Refactor Decisions
Issue	Decision	Reason
KVK_END_SCAN = NULL causes fighting state to fail	fix now	Production incident.
stats_alerts and targets appear to use separate KVK-state paths	fix minimal/shared logic now if safe; otherwise defer broader consolidation	Need incident fix without risky redesign.
Missing target cache invalidation after state change	fix now	Targets can remain wrong after code fix.
Broader KVK-state service consolidation	defer if too large	Capture as deferred optimisation unless small and safe.
13. Testing Requirements

Run targeted tests first, then selected project checks.

Add/update tests for these scenarios:

PASS4_START_SCAN = 866, KVK_END_SCAN = NULL, MaxScanOrder = 875
expected: fighting/open/active
PASS4_START_SCAN = 866, KVK_END_SCAN = 900, MaxScanOrder = 875
expected: fighting/open/active
PASS4_START_SCAN = 866, KVK_END_SCAN = NULL, MaxScanOrder = 850
expected: not fighting / Pre-KVK
PASS4_START_SCAN = 866, KVK_END_SCAN = 900, MaxScanOrder = 901
expected: ended/not active
PASS4_START_SCAN = NULL
expected: not fighting unless an existing date fallback deliberately supports active state

Suggested commands:

.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -q tests -k "kvk or target or stats_alert"
.\.venv\Scripts\python.exe scripts\smoke_imports.py

If touched by command registration or broader imports:

.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
14. Acceptance Criteria
 Stats alerts resolve KVK 15 as fighting when MaxScanOrder = 875, PASS4_START_SCAN = 866, and KVK_END_SCAN = NULL.
 Stats alerts no longer post/edit the Pre-KVK embed once fighting has opened.
 Targets cache writes TargetState as active/fighting for the same scenario.
 Target embeds no longer show Draft/Pre-KVK state for KVK 15 after cache refresh.
 Historical completed KVKs with populated KVK_END_SCAN still resolve correctly.
 Tests cover KVK_END_SCAN = NULL.
 Deployment notes include refreshing/deleting PLAYER_TARGETS_CACHE.
 Any broader duplicated KVK-state design issue is captured as a deferred optimisation if not fully fixed.
15. Deployment Steps
Deploy code to bot machine using normal promotion process.
Stop bot.
Refresh or remove stale targets cache:
# Option A: delete cache and let bot rebuild
Remove-Item <PLAYER_TARGETS_CACHE_PATH> -ErrorAction SilentlyContinue

or run the project’s existing target-cache refresh command/script if available.

Start bot.
Confirm logs show KVK 15 resolved as fighting/active.
Trigger or wait for stats alert path.
Test /mykvktargets against a known GovernorID with targets.
Confirm target embed state is Active/Official, not Draft/Pre-KVK.
16. Required Delivery Output

Return:

Summary
File Manifest
Modified Files
SQL Changes
Cache / State Handling
Tests Added or Updated
Validation Commands Run
Deployment Steps
Deferred Optimisations
17. PR Summary Template
## Summary

- Fix KVK fighting-state detection when `KVK_END_SCAN` is not yet populated.
- Correct stats alert and target-cache behaviour for active KVKs with open-ended scan windows.

## Changes

- Allow fighting/open KVK state when `MaxScanOrder >= PASS4_START_SCAN` and `KVK_END_SCAN` is `NULL`.
- Preserve completed-KVK handling when `KVK_END_SCAN` is populated.
- Add regression coverage for open-ended KVK scan windows.
- Document target-cache refresh requirement for deployment.

## Tests

- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "kvk or target or stats_alert"`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`

## Deferred Optimisations

- Capture broader KVK-state consolidation if duplicate logic remains after the incident fix.

## Risk / Rollback

- Risk is medium because KVK-state resolution affects stats alerts and target embeds.
- Rollback by reverting this PR and restoring previous cache, but preferred fix is to correct `KVK_END_SCAN` once known and keep open-ended handling in place.
