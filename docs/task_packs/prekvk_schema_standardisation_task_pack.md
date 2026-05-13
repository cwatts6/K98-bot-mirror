# Codex Task Pack — PreKvK Import Schema Standardisation & Reporting Retention

## Task Summary

The PreKvK ranking file format has changed. This task is not a simple importer patch: it is a schema standardisation and reporting compatibility task.

The new workbook provides separate Stage I, Stage II, Stage III, and Total PreKvK points directly. The current implementation imports only a single cumulative points value and `prekvk_stats.py` derives phase rankings from scan-window deltas. The goal is to update the import and supporting SQL/model logic so `prekvk_stats.py` continues to return the same logical reporting blocks:

- `overall`
- `p1`
- `p2`
- `p3`

…but now sourced from the new direct file columns rather than inferred scan-window deltas.

## Required Reading

Read these before making changes:

1. `K98 Bot Standard Development Initiation Statement.md`
2. `K98 Bot - Project Engineering Standards.md`
3. `K98 Bot - Coding Execution Guidelines.md`
4. `K98 Bot - Testing Standards.md`
5. `K98 Bot - Skills & Refactor Triggers.md`
6. `k98 Bot - Deferred Optimisation Framework.md`
7. Current implementation files:
   - `prekvk_importer.py`
   - `stats_alerts/prekvk_stats.py`
   - `stats_alerts/embeds/prekvk.py`
   - `DL_bot.py`
   - `sql_schema/dbo.sp_Build_Prekvk_And_Honor_Rankings.StoredProcedure.sql`
   - `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql`
8. Example workbook:
   - `/downloads/PreKvK_sample_file/PreKvK_Rankings_C13164_2026-05-08.xlsx`

## Mandatory Working Method

Follow the project initiation rules.

Stop after Step 1 audit unless explicitly approved to continue.

This task pack defines the intended scope, but Codex must still perform an audit first.

---

# Step 1 — Audit First

## Audit Objectives

Confirm:

1. Exact new workbook schema.
2. Existing importer assumptions.
3. Existing SQL table shape for:
   - `dbo.PreKvk_Scan`
   - `dbo.PreKvk_Scores`
   - any indexes/constraints/triggers
4. Existing reporting expectations from:
   - `stats_alerts/prekvk_stats.py`
   - `stats_alerts/embeds/prekvk.py`
5. How `DL_bot.py` routes PreKvK uploads.
6. Whether existing tests cover PreKvK import/reporting.
7. Whether old-format imports must remain compatible.

## Known Starting Findings

The new workbook appears to include:

- `Rank`
- `Name`
- `Governor ID`
- `KD`
- `Stage I Points`
- `Stage II Points`
- `Stage III Points`
- `Total Points`

The current importer expects:

- `GovernorID` or `governor_id`
- `Name`
- a single column beginning with `Prekvk`

The current reporting helper returns:

```python
{
    "overall": [],
    "p1": [],
    "p2": [],
    "p3": [],
}
```

That public shape must be retained.

---

# Scope

## In Scope

### Phase 1 — Import compatibility and canonical mapping

Update PreKvK import to support the new workbook schema.

Canonical fields should be:

| Source Column | Canonical Field |
|---|---|
| Rank | SourceRank |
| Name | GovernorName |
| Governor ID | GovernorID |
| KD | KingdomID |
| Stage I Points | Stage1Points |
| Stage II Points | Stage2Points |
| Stage III Points | Stage3Points |
| Total Points | TotalPoints |

Importer must:

- Accept the new sheet name, likely `Pre-KvK Rankings`.
- Retain safe fallback behaviour for workbook sheet selection.
- Validate required columns.
- Validate `GovernorID`.
- Validate duplicate `GovernorID` rows.
- Convert points safely to integers.
- Trim governor names.
- Log import phase failures clearly.
- Emit telemetry consistently with existing PreKvK import telemetry style.
- Preserve hash-based duplicate file protection.
- Preserve SQL headroom preflight behaviour from `DL_bot.py`.

### Phase 2 — SQL storage standardisation

Update SQL storage so PreKvK imported rows can store:

- `KVK_NO`
- `ScanID`
- `GovernorID`
- `GovernorName`
- `KingdomID`
- `SourceRank`
- `Stage1Points`
- `Stage2Points`
- `Stage3Points`
- `TotalPoints`

Implementation options:

1. Alter `dbo.PreKvk_Scores` to add new nullable columns, keeping existing `Points` populated as `TotalPoints`.
2. Or create a replacement normalised table/view layer if that is cleaner.

Preferred approach unless audit finds a blocker:

- Add new columns to `dbo.PreKvk_Scores`.
- Continue populating existing `Points` with `TotalPoints` for backward compatibility.
- Add/update indexes to support:
  - latest scan per KVK
  - top total points
  - top stage points
  - governor lookup per KVK

### Phase 3 — Ranking refresh logic

Update `dbo.sp_Build_Prekvk_And_Honor_Rankings`.

It must continue producing existing fields:

- `MaxPreKvkPoints`
- `PreKvk_Rank`

It should also support direct stage values/ranks, either in `dbo.PreKvk_Scores_Ranked` or via a separate supporting object:

- `Stage1Points`
- `Stage1Rank`
- `Stage2Points`
- `Stage2Rank`
- `Stage3Points`
- `Stage3Rank`

Rules:

- Overall ranking uses `TotalPoints` / existing `Points`.
- Stage rankings use direct stage columns.
- Ranking should be per `KVK_NO`.
- Tie-breaker should remain stable, using points desc then `GovernorID` asc unless there is a better existing project convention.
- Honor ranking logic should not be changed unless required by dependency.

### Phase 4 — Preserve `prekvk_stats.py` reporting contract

Update `stats_alerts/prekvk_stats.py`.

The function:

```python
load_prekvk_top3(kvk_no: int, limit: int = 3) -> dict
```

must keep returning:

```python
{
    "overall": [{"Name": str, "Points": int}, ...],
    "p1": [{"Name": str, "Points": int}, ...],
    "p2": [{"Name": str, "Points": int}, ...],
    "p3": [{"Name": str, "Points": int}, ...],
}
```

Mapping:

- `overall` = Total Points / overall PreKvK score
- `p1` = Stage I Points
- `p2` = Stage II Points
- `p3` = Stage III Points

Do not require a new PreKvK report in this task.

The existing embed should continue to work without changing its public behaviour, unless minor label fixes are needed.

Fix any incorrect previous-KVK phase mapping discovered during audit.

---

# Explicitly Out of Scope

## Phase 5 — KVK Excel output

Do not change final KVK Excel output in this task.

Do not add new PreKvK stage columns to `sp_ExcelOutput_ByKVK`.

Do not change exported Google Sheet / Excel output shape.

Existing `MaxPreKvkPoints` and `PreKvkRank` compatibility should remain if already used.

## Separate Future Task — PreKvK report

Do not build a new standalone PreKvK report in this task.

Capture as deferred optimisation:

- New PreKvK report command/output
- Possible admin-facing import history
- Possible historic comparison report
- Possible per-stage Top N configurable report

---

# Files Likely to Modify

## Python

- `prekvk_importer.py`
- `stats_alerts/prekvk_stats.py`
- `stats_alerts/embeds/prekvk.py`
- `DL_bot.py`

## SQL

- SQL migration/script for `dbo.PreKvk_Scores` schema changes
- `sql_schema/dbo.sp_Build_Prekvk_And_Honor_Rankings.StoredProcedure.sql`

## Tests

Add or update tests under:

- `tests/`

Possible test files:

- `tests/test_prekvk_importer.py`
- `tests/test_prekvk_stats.py`

Do not rely on archived tests.

---

# Implementation Requirements

## Importer

Importer must support:

1. New schema workbook.
2. Clear validation errors.
3. Duplicate GovernorID rejection.
4. Hash duplicate skip.
5. Empty/invalid workbook rejection.
6. Numeric conversion for all stage and total point columns.
7. Name trimming and null handling.
8. Logging with phase names.
9. Telemetry for:
   - start
   - success
   - failed validation
   - duplicate skip
   - database failure

## Upload routing

Update `DL_bot.py` PreKvK file acceptance.

Current exact filename matching is too strict.

Accepted files should include:

- `1198_prekvk.xlsx` for legacy/manual compatibility
- `PreKvK_Rankings_*.xlsx`
- Case-insensitive `.xlsx`

Reject unrelated files clearly.

## SQL

SQL changes must be safe for existing data.

Migration should:

- Add nullable columns if missing.
- Avoid destructive drops of core import data.
- Preserve existing `Points` column as total score compatibility.
- Add indexes conditionally.
- Avoid breaking old rows where stage columns are null.

Ranking procedure should:

- Keep current overall ranking compatibility.
- Add stage rankings without breaking downstream joins.
- Avoid changing honor ranking behaviour.

## Reporting

`prekvk_stats.py` must:

- Keep the same return contract.
- Prefer direct stage columns.
- Handle older rows with null stage columns gracefully.
- Return empty lists rather than raising if data is missing.
- Respect `limit`.
- Use parameterised SQL.
- Avoid direct SQL duplication where practical.

---

# Validation / Acceptance Criteria

## Import acceptance

Given the new workbook:

- Import succeeds.
- Rows imported count matches valid governor rows.
- `GovernorID`, `GovernorName`, `KingdomID`, `SourceRank`, `Stage1Points`, `Stage2Points`, `Stage3Points`, and `TotalPoints` are stored.
- Existing `Points` is populated with `TotalPoints`.

## Reporting acceptance

`load_prekvk_top3(kvk_no, 3)` returns:

- `overall` from total points.
- `p1` from Stage I points.
- `p2` from Stage II points.
- `p3` from Stage III points.

Existing PreKvK embed remains functional.

## Backward compatibility

- Existing old-format PreKvK rows do not break reporting.
- Existing `MaxPreKvkPoints` and `PreKvkRank` continue to exist.
- Honor ranking remains unchanged.

## Negative tests

Must cover:

- Missing required columns.
- Duplicate GovernorID.
- Empty workbook/no valid rows.
- Non-numeric point values.
- Duplicate file hash.
- Unknown filename rejection in upload route, if route tests are practical.

## Regression tests

Must cover:

- Existing `load_prekvk_top3` dictionary shape.
- Limit handling.
- Null stage value handling.
- Old data compatibility where only `Points` exists.

---

# Testing Commands

Use project-standard commands:

```powershell
cd C:\discord_file_downloader
.\.venv\Scripts\Activate.ps1
python -m pre_commit run -a
python -m pytest -q tests
git diff --check
```

Do not run pytest against archive folders.

---

# Deployment Notes

Likely deployment order:

1. Apply SQL schema migration.
2. Deploy updated stored procedure:
   - `dbo.sp_Build_Prekvk_And_Honor_Rankings`
3. Deploy Python code.
4. Restart bot via normal watchdog process.
5. Upload new PreKvK workbook to configured PreKvK channel.
6. Confirm:
   - import success embed
   - rows imported
   - `prekvk_stats.py` output
   - PreKvK stats embed refresh

---

# Deferred Optimisations

## Deferred Optimisation
- Area: PreKvK reporting
- Type: feature
- Description: Build a standalone PreKvK report using the new stage-level data.
- Suggested Fix: Create a separate task for a PreKvK report command/embed once import/schema stabilisation is complete.
- Impact: medium
- Risk: low

## Deferred Optimisation
- Area: Import diagnostics
- Type: observability
- Description: Rejected/corrected import diagnostics are useful but not required for this schema update.
- Suggested Fix: Add an admin-facing import history/diagnostics view covering accepted, rejected, duplicate, and failed PreKvK uploads.
- Impact: medium
- Risk: low

## Deferred Optimisation
- Area: Historic data migration
- Type: data migration
- Description: Historic PreKvK imports may only contain total points, not stage-level values.
- Suggested Fix: Decide separately whether old imports should be backfilled, left as total-only, or marked as legacy.
- Impact: low
- Risk: medium

## Deferred Optimisation
- Area: Import routing architecture
- Type: architecture
- Description: `DL_bot.py` still contains direct upload-routing logic for PreKvK.
- Suggested Fix: Move PreKvK upload route into a dedicated importer/router service in a future refactor.
- Impact: medium
- Risk: medium

## Deferred Optimisation
- Area: Configurable report limits
- Type: feature
- Description: `load_prekvk_top3` supports a limit, but reporting may later want configurable Top N values.
- Suggested Fix: Add configurable PreKvK report limits only when the standalone report is built.
- Impact: low
- Risk: low

---

# Required Codex Output

Codex must provide:

1. Audit findings.
2. Confirmed implementation plan.
3. File manifest.
4. SQL changes.
5. Test plan.
6. Deployment steps.
7. Structured deferred optimisations.
8. Codex review summary after implementation.

Do not implement Phase 5.

Do not create the standalone PreKvK report in this task.
