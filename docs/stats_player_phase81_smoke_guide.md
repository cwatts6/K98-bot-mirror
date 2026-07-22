# `/stats player` Phase 8.1 Smoke And Performance Guide

Use this guide only after the additive SQL migration is deployed before the dependent bot. Output
must remain private and no command resync is expected.

## Functional smoke

1. Use an approved leadership role in Leadership and an administrator in Leadership/Notify; prove
   an unapproved role/channel is denied. Repeat after opening the view to prove per-interaction
   revalidation.
2. Open a representative recent/dense governor at 90 days. Confirm Overview has four equal Activity
   Index, KVK Index, Presence and Last Active scorecards, exact scan ratio and whole percentage, and
   balanced location/shield and Leadership Review panels. KVK Index includes its kingdom rank;
   CURRENT/STALE/PARTIAL/NO DATA remains separate.
3. Check Last Active fixtures or known source evidence for each of Power, Healed, RSS Gathered,
   RSS Assisted, Helps, Tech Donations, Building Minutes and completed Fort rallies. Exactly 30
   UTC dates old is ACTIVE; 31 is INACTIVE; no qualifying change is Not recorded.
4. Move through 30/90/180/360. Confirm all six Activity metrics remain, Activity has no repeated
   location strip, latest transition wins, and the same attachment is replaced.
5. Confirm KVK shows no more than three distinct latest eligible finalized KVKs side by side. It
   retains all numeric percentages, exemptions, ranks and missing states, and shows no final
   timestamp/state or MET/NOT MET words.
6. Confirm KVK Index is the arithmetic mean of the scoreable latest-three completed KVK scores,
   where each score is `kills target % * 60% + deads target % * 20% + Tanking % * 20%`. Confirm
   the score is uncapped, missing/exempt KVKs are excluded, genuine zero kills/deads/healed makes
   that KVK score zero, and no scoreable KVK remains neutral.
7. Confirm Tanking and its rank are unavailable whenever Healed is zero/missing or legacy Healed
   capture is unavailable. Confirm KP and Deads ranks use descending competition ranking.
8. Confirm Player Record keeps Active Linked Governors unchanged but returns Alias and Alliance
   history only for the selected Governor ID, pages deterministically, preserves leave/return
   episodes, and does not infer Unallied from a missing governor scan.
9. Check one/two/no-KVK, no-data, long Unicode/history, fallback, timeout-disable and cleanup paths.
   Footer must show Data refreshed left and Generated right.
10. Confirm the controls use four page buttons, Timeslice, Active linked governors, then Change
    Player / Previous Page / Next Page / Definitions / Current. Refresh is absent; record paging is
    visible but disabled outside Player Record.

## Bounded performance evidence

The application harness is sequential, does not clear SQL Server caches and refuses to run without
the explicit acknowledgement:

```powershell
.\.venv\Scripts\python.exe scripts\measure_leadership_player_review.py --confirm-read-only --case recent_dense=<ID> --case long_tenure=<ID> --case sparse=<ID> --case high_history=<ID> --output .codex_artifacts\phase81_private\phase81-app-timing.json
```

The JSON is restricted leadership performance evidence and must remain beneath the ignored
`.codex_artifacts\phase81_private` directory. Governor IDs are not written, but anonymous case
labels and row cardinalities still require sanitization before sharing. Join authorization and Discord attachment timings from
the privacy-safe runtime logs by case/run window.

In the authoritative SQL repository, create a private untracked `#Phase81GovernorCases` temp table
with the four named cases and approved IDs in the same SSMS session, then run
`deploy/Measure-Phase81LeadershipPerformance.sql` unchanged. Enable Include Actual Execution Plan
and run once in an approved window. Save raw `.sqlplan`, Messages and Results only below the
repository-ignored `reports/phase81_private` directory; never commit or share them. A shareable
summary must remove IDs, names, row values, location/shield data and plan compiled/runtime parameter
values. Do not clear the plan/buffer cache and do not run concurrently.

For every representative case and statement, record:

- actual versus estimated rows, execution count and returned rows/bytes;
- logical/physical/read-ahead reads, CPU and elapsed time;
- scans/seeks/lookups, residual predicates and conversions;
- sorts/hashes, spills, memory grant requested/granted/used and parallelism;
- statistics last-updated time, sampled rows and table modification count;
- existing index keys/includes, seeks/scans/lookups/updates and lock/latch counters.
- before/after procedure-counter deltas, accepting them only when `PlanBaselineComparable = 1`;
- SQL Server start time and Query Store plan variance, so lifetime DMV counters are not mistaken
  for workload caused by this feature.

Missing-index DMVs are hypotheses only. First test stale/inadequately sampled statistics,
cardinality/query-shape defects, non-sargable predicates, repeated result work and cache/page
granularity. If an index remains justified, compare it with every existing overlapping index and
the source import/write path; prefer consolidation or the narrowest supported change. A table,
index, pre-aggregation or further SQL change requires a separate design approval and SQL PR.

Use this decision order for the next-step recommendation:

1. Isolate the expensive statement and representative case/period from actual plans, IO/time and
   comparable procedure deltas. If SQL is not the dominant stage, improve mapping, render,
   attachment or cache behavior instead.
2. If estimates materially diverge from actual rows, test statistics age/sample quality and data
   skew before proposing an index.
3. If estimates are sound but reads remain high, inspect seek predicates, residual predicates,
   implicit conversions, repeated scans/lookups and returned columns; prefer query refinement or
   narrower result work where it addresses the demonstrated operator.
4. Treat spills or oversized grants as cardinality/query-shape evidence first. Treat lock/latch
   waits as contention evidence, not an automatic indexing signal.
5. Consider an index only when the same access path recurs across representative cases, the actual
   plan shows the exact key/include need, expected read reduction is material, and overlap plus
   import/update cost are quantified against existing indexes.
6. Recommend no SQL object change when warm budgets pass, evidence is case-specific, the plan was
   recompiled during measurement, or the proposed benefit cannot be separated from server-history
   DMV counters.

Proposed starting budget, subject to operator acceptance after the baseline: warm app-cache
transition p95 <= 1.0 s; warm SQL-backed transition p95 <= 2.5 s; cold first load p95 <= 5.0 s;
render/PNG p95 <= 750 ms; attachment replacement p95 <= 1.5 s; no unexplained >10% logical-read
regression and no interaction timeout.

## Rollback

Roll back the bot first. After no deployed bot depends on Last Active, run
`migrations/rollback/20260721_005_add_leadership_player_last_active_rollback.sql`. No table, index
or data rollback exists because this slice adds none.
