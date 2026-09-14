# Codex Chat Starter - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation

## Delivery closure and Phase 2H handoff — 2026-09-08

**Phase 2G is complete as an implementation and bounded-validation delivery, by explicit operator
acceptance. Full live Pre-KVK validation is carried forward to Phase 2H; it is not claimed complete.**
This status supersedes preparation and intermediate status statements in this historical record.

Mirror PR #258 and production PR #565 were both OPEN when this closure was prepared. Reviewed
runtime heads are mirror `bd99ea1421286ddb152f7729e11de664116d7e47` and production
`fea2767f52f345450225bcdf0c1f03f3d5e3dc4c`; their Python trees match. Documentation closeout commits
follow these heads. Operator merges, final production-main source verification and bot-machine
deployed-head verification remain pending. Supplied restart logs contain no immutable Git head;
they cannot prove deployment of the final merged source. Codex has not merged or deployed either PR.

Delivered: durable reserve/start/accept/commit/release, conservative uncertain-send retention,
receipt recovery, off-season coordination, generation/CAS fencing, bounded Windows CSV replacement
retries and off-loop fighting/stale-reference invalidation. Phase 1–2F payload, permission,
visibility, mention, eligibility, edit/test and executor contracts remain preserved.

Final validation: full **3314 passed, 2 skipped**, production log-noise pass; **91** focused tests
with pinned filelock 3.20.0; **67** production focused tests; strengthened lifecycle assertions
passed separately (**3**). Pre-commit, architecture/deferred/security-routing validators, selector,
smoke imports and registration (36 primary / 100 grouped) passed. Full suite evidence transfers
through verified Python-tree identity; it was not independently rerun in production.

Changes-only / Deep-off security: mirror full scan `43cd6ae2-7ea7-40b1-89e2-c916b16b79f1`
through `fd93202f`, mirror delta `90ad6945-fded-4367-b915-ee5964414523` through `bd99ea14`, and
separate production scan `eba7b5b2-73ad-4b39-8e64-263362802657` for `d9321328..fea2767f`
completed with zero reportable findings and no deferred candidates. The final documentation-only
delta changes no executable, configuration, dependency, SQL, permission or persistence control;
an additional security scan and pytest run are skipped for that delta, with documentation/hooks
and routing validators required. SQL manifest remains empty; authoritative repo was clean at
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`.

Operator log evidence, 2026-09-08 09:16:40–09:22:06 (timestamps as supplied):

- Graceful shutdown drained queues, persisted state and cancelled registered tasks. Full startup
  completed at 09:17:05; reminder/live-event views reattached and command registration was unchanged.
- At 09:21:50 the normal fighting KVK route skipped Kingdom Summary (already sent) and KVK
  publication (daily cap). The generic subsequent “sent successfully” line is not a send receipt.
- No `[DISPATCH] Reserved` / `Committed` evidence appears. Fresh Pre-KVK/off-season ownership,
  matching CSV/journal/message references and restart-after-commit remain unobserved live.
- ProcConfig failed at 09:20:17 while restoring `conn.autocommit` with pending SQL results;
  later success reporting masked that failure. This unchanged pipeline is separate work.
- Tracked-view rehydration timed out after 10 seconds; remaining generic tracked views are
  unverified. Google Sheets 503 recovered on retry. Neither is silently counted as a clean pass.

Phase 2H owns an admin-only, mention-neutral, explicitly targeted diagnostic using the real
reservation flow and isolated durable journal/CSV/message state. Existing `is_test=True` bypasses
cannot establish reservation admission and still touch shared message state. The diagnostic must
support receipt inspection, repeat/guard/edit and restart verification without changing production
calendar data or weakening eligibility. Natural production calendar routing stays a distinct gate;
an isolated diagnostic cannot prove every live scheduling, contention or uncertain-send scenario.

Rollout/rollback requirements remain binding: stop all writers; back up CSV, message state and
journal together; no mixed versions; reconcile accepted/uncertain receipts before downgrade and
keep dispatch stopped if outcomes remain unknown. No exactly-once, cross-host or TTL-stealing claim.
The separate Phase 2F next-natural-public-save observation remains pending unless new evidence proves it.


Historical starter below is retained for provenance, not execution. Use the Phase 2H starter.


Status: implementation approved 2026-09-08. Original audit starter below is historical.
Continue from active pack section 15: finish final hooks, immutable bot Changes-only/Deep-off
review and mirror delivery. No SQL change. Natural smoke and production promotion remain gated;
do not repeat the already approved design gate.

## Copy/Paste Starter

```markdown
Begin Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation.

Use:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation.md

Historical evidence:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.md
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

Phase 2F candidate delivery and operator smoke succeeded through mirror PR #257 and production
PR #564. Both awaited operator merges and final production-main verification at preparation.
Revalidate those states, final bot-machine verification, branch/head/worktree and Phase 1-2F source
presence before implementation. Do not assume archived candidate acceptance proves final deployment.

First response is audit/scope and architecture planning only. Map Pre-KVK scheduled/manual/test
dispatch, edit/fresh-send branches, off-season guards, CSV/state producers, locks, offloads,
exceptions, shutdown and restart. Prove coroutine/thread/process overlap and distinguish the
nonexclusive singleton metadata check from actual ownership. Establish deterministic or production
evidence without forcing live duplicates or mentions.

Compare current post-success claim with reservation alternatives. Define reserve/commit/release,
uncertain-send reconciliation, owner checks, lock contention, UTC rollover, stale recovery,
persistence compatibility and rollback. No exactly-once claim without proof. Preserve Phase 1-2F
payloads, permissions, visibility, eligibility, mentions, identity, timing and executor semantics.
Do not silently select a sidecar, schema migration or SQL.

Produce safe/fix now/defer/not runtime findings, exact runtime/test/docs and separately gated SQL
manifest, selector/risk-based tests, bot Changes-only/Deep-off routing, SQL no-diff criteria, natural
smoke and approval questions. Keep singleton repair, public child-task lifecycle, DM redesign,
broad JSON consolidation and Stats/KVK History executor audits separate. Explain any hard dependency.

Stop for approval after the first response. Do not edit runtime code or tests.
```
