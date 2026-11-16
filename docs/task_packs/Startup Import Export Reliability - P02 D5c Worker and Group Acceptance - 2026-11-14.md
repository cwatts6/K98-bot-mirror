# D5c worker and group approval: accepted offline results

**28/28 behavioral scenarios and seven runner controls passed and are accepted.**
The grouped pass required no operator console step. All 14 worker scenarios and
14 group-membership scenarios ran once in V2. The original attempt stopped before
case 1 because three helper-file pins were missing. Its failed result, intent and
packet are preserved unchanged. A new version added only exact helper pins and
new evidence paths; the test definitions and assertions did not change.

## Evidence and review

- Acceptance: `.codex_artifacts/p025/d5c-worker-groups-acceptance.json`.
- Passed receipt: `.codex_artifacts/p025/d5c-worker-groups-v2/result.json`.
- Failed receipt: `.codex_artifacts/p025/d5c-worker-groups/result.json`.
- V2 packet: `.codex_artifacts/p025/d5c-worker-groups-v2/packet.json`.
- Guarded dependency preflight: `.codex_artifacts/p025/d5c-worker-groups-v2-guarded-preflight.json`.
- Changes review: `6b85b749-96f6-4c18-93dc-8c6a2a8a120b`, completed and sealed;
  range `506ed68b597e566da45dc5ee903f1f139b701b96..ace7c903599f1663a118df2c41e246eef4e95d9a`.
  Four changed files reviewed, plus unchanged tests/supporting code; no candidates
  or operational blockers. Initial review `38b2917b-7be1-4851-a82e-fc4e4b91bda6`
  remains preserved; its static readiness did not predict the missing-pin failure.

The guarded V2 loader preflight verified nine source modules with zero cases and
zero boundary violations. Qualification then passed all 35 exact IDs, seven
expected boundary refusals, no unexpected boundary events, no pending tasks or
extra threads. All 672 preservation pins rehashed unchanged. Combined intent and
result total 7,481 bytes. Qualification elapsed 0.234 seconds, within 300 seconds.
Receipt SHA256: `d20e4b29cb82e368f8c66a17269a9994f728ba7ad911d9b97cd90bd9af3cdc4e`.
Normal Git HEAD and index were preserved while review-only commits were created.

The review service reports cached-context-inclusive token totals of 2,832,963
for the original review and 1,426,645 for V2. These are tool-reported review usage,
not unique new tokens, qualification duration or application cost measurements.

## Findings and proof limits

The original worker prioritizes accepted repairs, deduplicates work, retains busy
and failed observations, isolates cursors by scope, and accounts for bounded
historical sweeps in these inert scenarios. Membership tests refuse empty,
duplicate, foreign, oversized, stale and pending selections. The historical DAL
refuses a changed locked reread after service verification succeeds. The evidence
group DAL reaches labelled inserts on a valid control and unwinds staged work
when the second insert fails in the inert transaction model.

This does not establish actual SQL Server atomicity, successful historical group
approval, physical restart behavior or all final recovery-action boundaries.
There was no runtime correction, SQL/VM execution, provider request or new input.
No production problem was demonstrated by the package failure.

## Balances and continuation

The operator's broader approval covered the one additional offline pass. No limit
extension was needed or applied. Original failed evidence and exhausted native
attempts remain recorded. Balances remain:

- 1,305 native seconds, including the protected 1,000-second later-phase reserve.
- 50 Windows-test seconds.
- 11 of 64 synthetic rows.
- 21 inputs consumed; zero additional inputs used.

G2 is complete. D5c remains **9 of 12 families closed**: C04 season/routing/weights,
C05 queue/pool/holds and C06 remaining effectful recovery safeguards remain open.
The earlier 25 inspector checks, 42 orchestration checks and 46 representative
handler checks remain accepted at their existing proof boundaries. They are not
replayed or counted as proof of every final action route.

Next grouped preparation follows the existing remaining-groups plan: final action
and reconciliation boundaries across the 73 policy routes; season/routing/weights
offline and native checks; and queue/pool/hold checks with exact fixture and
command ledgers. The 73-route list is a coverage inventory, not a promise of 73
new handoffs. No next native execution packet is declared ready by this result.
Use the existing broader approval for required preparation and bounded runs;
record any actual future extension explicitly before use. No deployment is
included. D5d, D5e and D5f obligations remain, followed by separate D6 deployment.

Architecture, deferred-item, security-routing and test-selector PR gates remain
for PR/release handoff, which this packet does not perform. Full pytest and smoke
imports are excluded from the no-startup offline qualification. No runtime helper,
production refactor or deferred optimisation item is introduced. The narrow
Changes review and explicit dependency/preservation checks are complete.
