# P01.6 render scheduling correction

## Problem and resulting behavior

P01.6 inserted an event-loop Task turn before submitting image work to the dedicated
executor. A busy loop could consume most of the unchanged 3.5-second render deadline
before the executor received the job. Submit the bounded render immediately, preserving
the two-worker admission limit and physical completion ownership. The native future
owns settlement even if its observer Task is cancelled before entry or cannot be created;
shutdown explicitly drains that future. SQL workers, cache keys, authorization rechecks,
data deadlines and fallback content remain unchanged.

The existing observed interaction wrappers already acknowledge Stats actions. Remove
their duplicate inner acknowledgement attempts; preserve the wrapper and its ephemeral
behavior. This does not repair the older swallowed-acknowledgement/10015 failure path.

## Evidence and qualification

A controlled comparison used a 2.6-second loop stall and a 1.2-second renderer. The
pre-P01.6 and corrected paths submitted immediately and completed observation around
2.6 seconds; deployed P01.6 submitted after the stall and exceeded its 3.5-second
deadline. This demonstrates the scheduling regression, not the sole production cause.
Tests cover immediate submission/context, two-worker bounds, cancellation before owner
entry, Task allocation failure, executor rejection and physical drain. Existing tests
cover late results, permissions, invalidation, transitions and shutdown. The acknowledgement
regression test covers command/page entry and mode/period/scope changes.

Retain final test, lint, architecture, deferred-item, command-registration, smoke-import,
operational-log-isolation and Changes security-review receipts with the release handoff.
Local qualification and merges are distinct from host readiness and live acceptance.

The expanded focused run passed 1,815 tests, including historical updater transitions,
render ownership, shutdown, Stats views and application compatibility; the log-noise
wrapper confirmed operational logs unchanged. Seven native Windows updater suites
passed 233 checks. Full-suite and final private-head CI results belong in the release
handoff, not inferred from these focused runs.

Changes security reviews `34620890-7181-4302-b1b9-d9190c95257e` (runtime correction)
and `9b3bef99-62ae-4ac4-988e-04da42cd08c1` (exact updater transition) completed with
no findings. The subsequent delta from mirror `80483d3` changes only documentation,
eleven historical test inventory counts, the test-only source-hash assertion bridge,
and its negative tests. Runtime/updater bytes are unchanged; the bridge has no
production imports and still rejects unreviewed source bytes before mapping historical
hashes. A further security scan is skipped for this test/documentation-only delta.
Historical prefix digest assertions remain unchanged. Retain final mirror/private
preimage and postimage equivalence with the two immutable Changes review targets.

## Production findings and remaining limits

- Two observed fresh Personal Stats procedure calls took about 55 ms and 1.215 seconds;
  the slower call used about 59 ms CPU. A later 60-second passive capture sampled a
  Personal Stats request repeatedly in `ASYNC_NETWORK_IO`: CPU stayed at 189 ms while
  elapsed time rose from 305 to 1,066 ms and the current wait grew to 848 ms, with no
  blocking session. This establishes result-consumption backpressure in that request,
  not its precise client/transport cause or every earlier delay. Existing recovery CPU
  contention is a plausible contributor, not a proven complete explanation.
  `data_ms` includes authorization, connection/worker/cleanup and aggregation work and
  must not be labelled pure SQL time. Do not close the SQL investigation on this evidence.
- Sampled recovery checks repeatedly decoded/reconstructed retained snapshots in code
  predating P01.6. Production SDK 2.6.1 also omits explicit empty attachment lists, which
  explains a previous image remaining above a new fallback. These and the older failed
  acknowledgement handling are captured in the deferred backlog for after P01-P05.
- No active KVK and final KVK data dated 29 September are expected. Calendar reminders
  remain separate; arming the loop or refreshing the pinned calendar is not dispatch proof.

## Deployment and rollback

This is a Bot-only source correction plus its exact installed updater transition.
No SQL migration, dependency install, application configuration change, import/export
replay or activation change is needed. Keep the already installed
Personal Stats procedure and index. Mirror review/merge precedes patch-based private
promotion/review/merge. Release from private main only.

Before handoff, verify exact source compatibility from installed
`8032f740b12159ee6b721649580eeb656e26e1d6`, final-head checks and fresh host custody
for every changed file and ancestor. Upgrade the updater using the generated exact
old/new-manifest installer; its new transition authenticates all 22 P01.6 members and
retains the 66 historical transitions unchanged. Verify all installed checksums before
using PrepareOnly. The older installed updater correctly refuses this source delta.
Use the upgraded updater's PrepareOnly
step; require the intended target, predecessor and all startup SQL contracts. Then, only
after the operator proceeds, use normal deployment and request graceful restart once
when prompted. Verify source/seed/start/readiness and Discord online before feature checks.

Validate one action at a time: fresh `/me stats`; Overview/Activity/Combat; change period;
Accounts to Stats; repeat a warm request. Capture telemetry and any failure at the same
time. Exercise another linked account and a longer period where available. Separate
render time, delivery time and data time; retain fallback/old-SDK limitations explicitly.
Do not declare all render timeouts or Accounts errors resolved based on this scheduling fix.

If a new release-related regression appears, stop acceptance and preserve receipts/logs.
The normal updater has no one-command reverse switch for this transition. Recovery must
first establish the completed release stage; do not blindly resume a completed deployment.
The rollback route is a separately reviewed forward revert of the affected Bot behavior
onto private main, with an exact reverse transition, matching source/startup policy and
physical drain. That reverse package must be prepared and qualified before it is run;
the present package does not authorize arbitrary reverse hashes.
The fallback baseline is the corrective startup-contract release above, not the earlier
broken startup-contract version. Do not reset live Git, force-stop processes or roll back
the SQL rewrite/index as part of this Bot correction. No cache or retained-work cleanup is
required. Production deployment remains separate from the authorized merges.
