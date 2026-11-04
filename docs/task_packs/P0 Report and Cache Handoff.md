# P0 report and cache handoff

## Scope

The supplied production report confirms a verified fresh SQL report while the
overall report/cache continuation still awaits its separate cache approval.
These are different records. The resolved SQL card omitted navigation back to
the unfinished parent, making a valid two-step workflow look contradictory.

The parent now states that SQL verification is step 1 of 2 and that local cache
verification remains. Its child link is labelled **Review SQL report step**.
Cache-only child reports with a validated saved parent expose **Return to report
and cache**, including when resolved. Opening that link rechecks admin access and
loads the parent's current state; it never starts a calculation or cache rebuild.
An already completed parent remains completed when opened from an old child card.

Services own the saved-parent link and explanation. The existing view handles
private navigation and permission rechecks. No SQL query, schema, cache writer,
settlement rule, provider call, or automatic approval is changed. RequestJson
and the validated producer parent contract remain the existing persistence path.
No new helper or refactor is required.

## Verification

1. Open the existing **Fresh player report and cache** incident.
2. If it says step 1 is complete, choose **Refresh local player cache** and
   confirm once. Do not repeat **Build fresh player report**.
3. Recheck for `report_and_cache_verified`, with cache row count, KVK, original
   source scan time and verification time. A new cache timestamp does not imply
   a new imported scan.
4. Open **Review SQL report step**, then **Return to report and cache**. It must
   show the same current parent, including its completed state after step 3.
5. Reopen the recovery centre to refresh its list; previously sent Discord
   messages are snapshots and are not a live incident count.
6. Fresh publication remains separate: **Check published outputs**, select the
   retained publication, **Check published output**, confirm once, and Recheck
   while it runs. A green historical delivery card or healthy access probe is
   not a fresh content-verification result. Retain the final report and any
   saved diagnostic on failure; do not retry an uncertain write.

## Validation and release

Risk-based validation covers the real temporary-SQL report/capture/cache chain,
lost replies, recreated views, completed-parent navigation, denied access and
unrelated resolved links. Existing cache safety and publication tests remain in
the selected regression set. Architecture, deferred-item, test selection,
security routing, formatting and command/import checks are required.

Security route: **Changes**, Deep off, separate mirror/private patches. Changes
touch privileged navigation and the exact installed updater transition. No
codebase scan is requested. The updater accepts only the complete three-file
handoff transition at pinned before/after hashes.

## Remaining mandatory P0

[P0 Final Recovery Acceptance](P0%20Final%20Recovery%20Acceptance.md) remains the
complete checklist. This handoff fixes navigation; it does not close fresh
publication diagnosis/acceptance, all-copy-loss and ownership conflict recovery,
remaining interrupted producer stages, rollover qualification, or the full
failure-during-repair and natural production acceptance matrix. Nothing moves
to P1. The next fresh publication result must be assessed independently.
