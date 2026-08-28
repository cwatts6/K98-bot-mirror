# KVK Target Publication Contract

> Deployment status: Phase 1 deployed and operator accepted on 2026-08-26 through mirror PR #235,
> production PR #542, and SQL PR #73. The import-path transaction follow-up was deployed through
> mirror PR #236 and production PR #543. Production metadata/source/row-count checks and bot cache
> rebuild smoke passed.

KVK target publication is separate from the shared KVK fighting lifecycle and the broader KVK
window. These concepts must not be used as aliases:

| Concept | States or boundary | Owner | Purpose |
| --- | --- | --- | --- |
| Broad KVK window | matchmaking through configured KVK end | `kvk_state.py` window helpers | Determines whether a KVK is current for broad feature routing. |
| Fighting lifecycle | `DRAFT -> ACTIVE -> ENDED` | `kvk_state.py` | Starts `ACTIVE` at Pass 4 and drives stats alerts, daily overview, history, and leadership review. |
| Target publication | `DRAFT -> OFFICIAL -> HISTORIC`, otherwise `UNKNOWN` | SQL publication contract plus target publication service | Describes the proven source of the displayed target rows. |

The shared fighting resolver remains unchanged. Matchmaking completion does not make the shared KVK
state Active.

## Publication proof

`dbo.sp_TARGETS_MASTER` publishes an immutable row snapshot and its provenance in one transaction.
`dbo.KVK_Target_Publication` records the KVK, actual applied scan, source type, configured draft and
matchmaking scans, UTC publication time, row count, output object, monotonic version, and signature.
`dbo.KVK_Target_Publication_Row` owns the matching row snapshot. The bot reads both through
`dbo.v_KVK_TARGETS_FOR_BOT` with an explicit KVK parameter.

The bot resolves:

- `DRAFT` only when a successful publication proves `DRAFTSCAN` and its applied scan is at or below
  the configured draft scan;
- `OFFICIAL` only when a successful publication proves `MATCHMAKING_SCAN` and the actual scan equals
  the exact configured matchmaking scan;
- `HISTORIC` only when the same Official proof exists and the unchanged shared fighting state is
  `ENDED`;
- `UNKNOWN` (displayed as **Unverified**) when metadata is missing, malformed, inconsistent,
  cross-KVK, legacy-only, or cannot be read safely.

`MAX(ScanOrder) >= MATCHMAKING_SCAN`, an existing target row, legacy `ACTIVE`, and a missing state are
never proof of Official publication.

## Cache and recovery

The JSON cache uses schema version 2 and identity `(kvk_no, publication_version,
publication_signature)`. It stores SQL publication time separately from cache-write time. Row-level
`TargetState` is retained only as a compatibility field and is populated from target publication
state.

- A missing or legacy cache is rebuilt only from a verified SQL publication.
- A Draft cache is polled and promoted when a new Official identity appears. Command-path metadata
  polling is durably bounded across bot and maintenance processes to once per verified publication
  identity per 60 seconds; explicit maintenance refreshes bypass that hot-read cadence while still
  joining the same single-flight coordination. The poll deadline survives restart.
- An Official cache is not rewritten because later scans arrive or Pass 4 begins.
- KVK end projects a verified Official cache as Historical without changing the fixed rows.
- A previous-KVK cache is never served as the current KVK.
- Each command binds one resolved KVK context through cache validation and refresh, so a rollover
  cannot combine a new-KVK target row with the previous KVK label.
- A matching verified current-KVK cache is last-known-good during a transient SQL failure.
- Missing proof, an empty/mismatched rowset, or a SQL failure without matching last-known-good data
  fails closed as Unverified.
- Writes use atomic replacement. A cross-process write lock covers the final disk-version check and
  replacement, so a lower or conflicting publication version cannot overwrite a newer valid cache
  already on disk.
- Cache reads and refreshes are owned by `kvk/target_cache_repository.py`. Refreshes expose the
  typed outcomes `REUSED`, `REFRESHED`, `RETAINED_LAST_KNOWN_GOOD`, `REJECTED_MISMATCH`,
  `UNAVAILABLE`, and `FAILED_CLOSED`; `targets_sql_cache.py` remains a compatibility façade.
- Cross-process refresh ownership uses a 60-second lease in
  `player_targets_cache.json.coordination.json`. A live follower with matching last-known-good
  data returns immediately; a cold follower waits no more than five seconds. A proven dead owner
  is reclaimed immediately, an uncertain or hung owner is reclaimable after lease expiry, and a
  late owner cannot commit after losing its token. The lock is never held during SQL reads.

Routine SQL processing does not replace an existing Official publication. An operator force
republish is default-off, requires an explicit reason, and creates a new version/signature.

The import pipeline invokes `dbo.sp_TARGETS_MASTER` through a temporary autocommit boundary because
the procedure owns its publication transaction. The caller restores its previous connection
autocommit setting after success or failure; it must not wrap this procedure in an outer
transaction.

## Deployment order

Deploy and verify the SQL migration first. Republish the current KVK through the approved explicit
operator path when required, then verify the view's KVK, exact source scan/type, row count, output
object, version, and signature. Only after that proof exists should the bot be deployed and the
target cache rebuilt. No command registration sync is required.

## Phase 2 quality programme

Phase 2 does not reopen the publication model or target formulas. It incrementally improves the
bot-side target architecture by introducing typed target rows, making the typed service the single
retrieval/presentation-input path, extracting target-specific cache repository ownership with
proved refresh outcomes and cross-process coordination, and making the shared Pass 4 state
terminology explicit without changing its thresholds. Phases 2A through 2D are deployed and
operator accepted. Phase 2E moves the existing lifecycle SQL execution and row mapping into the
narrow `kvk/dal/kvk_lifecycle_dal.py` boundary while retaining the `kvk_state.py` public façade,
pure fighting resolver, query semantics, thresholds, result shapes, logging, and fallback behavior.
See
`docs/task_packs/Codex Task Pack - KVK Targets Quality Phase 2.md`.
