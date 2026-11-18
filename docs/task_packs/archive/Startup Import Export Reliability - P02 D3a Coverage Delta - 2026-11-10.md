# P02 D3a bounded coverage review

Reviewed Bot `402151f8c1a63015c2ad5dd02f8599997cba01d6` and SQL
`3dcd9d1f5356a1e2c9022450a1e7f4f555717361` before implementation. Both checkouts
were clean. This is a source coverage assessment, not an exhaustive proof or a
production observation. The failed `d3-lock-baseline.json` remains unchanged.

## Scope and coverage delta

The tracked Python census finds seven acquisition sites in five caller modules:
ordinary/guided player publication, startup readback, Ark team save, two Ark JSON
saves, and tracked views. There are no callers of the path-only release helper.
The governor-session DAL names are unrelated SQL locks. Existing singleton and
SQL custody helpers have different recovery/authority contracts and are not
substitutes for this lock.

Additional evidenced cases:

- `ArkJsonState.save_async` uses `run_blocking_in_thread`, whose cancelled awaiter
  can settle before its actual writer. Use the existing `core.owned_work`
  draining primitive at this caller, including repeated cancellation. Do not
  change every unrelated user of the general telemetry helper.
- Ordinary player-cache publication has the same undrained fallback when neither
  runtime nor startup composition is bound. Make physical drain unconditional.
- Tracked-view synchronous and async wrappers force a successful context exit;
  cleanup can replace the original failure. Pass the real exception to the
  shared owner, including cancellation during acquisition and release.
- Guided publication can commit the replacement before cleanup fails. Preserve
  its bytes and original error; a cleanup exception does not authorize SQL or
  provider replay. Its backup/staging cleanup can also mask a readback failure;
  preserve that first failure in the touched flow.
- Ark's two files are separate atomic writes, not a transaction. Failure of the
  second must preserve the already written first and the old second. Whole-store
  stale-object overwrite and an atomic two-file redesign remain domain follow-up.
- Startup captures bounded bytes under the writer lock. Decode/compare/hash may
  run after release only against those exact bytes; a newer generation is never
  adopted as the original completion. Cover malformed, oversized, truncated,
  mismatched and concurrently replaced data.

## Ownership design and test obligations

Separate acquisition, one body execution and release in `core/`; keep the public
`file_utils.acquire_lock` signature/defaults and yielded path. Use a monotonic
deadline, one immediate attempt for a zero budget, bounded sleeps and no retry of
body failures. Path-only release must refuse, without modifying the filesystem.

On Windows, create a new non-inheritable native handle with delete access and no
delete sharing. Mark that exact handle for deletion only during release and close
it; never close then unlink a pathname. A crash before release retains the old
sentinel. Qualify actual delete/rename refusal and separate-process contention.

POSIX has no portable conditional unlink-by-inode. Use a persistent, versioned
rendezvous file with an open-description `flock`, explicit held/released marker,
and no pathname deletion. Only an exact released marker permits reuse; an old
PID, empty, partial, foreign or crash-held sentinel is not recovered. Local
filesystems and cooperating writers are supported; external removal/replacement
of the rendezvous or its parent is outside the exclusion contract. Still never
delete or overwrite a replacement on release. This internal lock representation
does not migrate cache/state payloads. Tests assert subsequent admission rather
than assuming absence on POSIX. Network filesystem semantics are not qualified.

Cover threads/processes/reentry, aliases, preexisting foreign files/links,
permission and parent errors, partial metadata initialization, wall-clock jumps,
body `FileExistsError`/ordinary error/`BaseException`, missing/replaced paths,
close/disposition uncertainty, successor at close, and cleanup on success/failure.
Retain uncertain owners without blindly retrying a potentially reused handle.
Keep a process-local admission claim through acknowledged physical cleanup, not
merely until the operating-system handle closes. A deterministic close-then-wait
fixture reproduced a successor entering before a lost acknowledgement was
recorded; the local claim now blocks that window and remains fenced on failure.
This is same-process custody, not a promise of cross-process fencing after an
ambiguous physical release. Capture its canonical key once at admission.
Diagnostic logging failures during staging cleanup must also preserve the
original readback failure. Both cases have pre-fix failing regressions.
Caller tests must exercise actual locks and atomic writes with disposable paths.

## Six maintenance boundaries retained

Source reconfirms `UPDATE_ALL2` sampled stats/conditional KS4 upkeep before import
commit; archive follows commit and owns independent custody. `SP_Stats_for_Upload`
FULLSCAN remains before publication commit. KVK output invokes index creation,
FULLSCAN, view refresh and receipt in that order. Required schema/unique indexes
must remain distinct from the two nonunique indexes recreated by
`sp_Create_Excel_For_Kvk_Indexes`.

Configuration has **two invocation contracts**: standalone master/child work and
typed configuration with an enclosing transaction. Child/nested COMMIT does not
commit that outer transaction; child maintenance remains under the parent's
delta mutex acquisition in both paths. Test both, early no-new-row return, stats
failure and optional `DeltaProcessingLog` failure. Per-KVK nested publication is
not an independent commit when called by the typed producer.

Final reporting has separate completed stages and pre-admission headroom, plus
dashboard stats/CHECKPOINT/backup work before the final stage commit. Explicit
post-import `usp_update_stats` already owns the actual session applock around
`sp_updatestats`; retain it alongside Python durable maintenance ownership.
Subsequent D3 slices must test real children, crash between commit/enqueue/claim/
completion, lost acknowledgement, duplicate/concurrent claims, cancellation,
stale ownership, cleanup, backlog/headroom and both reader/writer arrival orders.

No SQL change or execution belongs to D3a. Preserve SQL 3961 history/REBUILD
failure, RCSI off, resource/time/input caps and the consumed 21-input allowance.
D4 final combined updater transition and D5 combined qualification remain open;
deployment stays held until after D5, with P03 actual blockers/essential P04 before
the first standard import/export.

## Validation and review decision

Use helper/native process tests plus all affected cache, startup, Ark and tracked
view suites; then full pytest because this is a cross-domain shared utility.
Run architecture, deferred, selector, security-routing, imports, registration and
lint gates. Authenticate exact protected-source updater changes while preserving
all predecessor transitions. Require Bot Changes security review against this
base and the final candidate, Deep off; no SQL scan for an unchanged SQL tree.
Native Windows and Ubuntu CI exercise platform cases with only pytest installed;
the pure ownership suite bypasses application test fixtures. No renewed implementation approval is
required under the handover. Actual host custody, installation and provider
acceptance are not claimed.
