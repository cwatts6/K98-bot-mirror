# Archived — Phase 2K delivered and smoke accepted

## Accepted Phase 2K delivery — 2026-09-09

This acceptance supersedes earlier local-only, pending-smoke and implementation-approval statements below.
Chris Watts explicitly accepted smoke testing as complete. Delivered and tested on production PR
candidate `36208765bf7200fa6855f3892e6b32d43b23bccf`; mirror runtime head
`2d892cefcfdfa0a8263efe69997bf292503b23aa`. Mirror #262 and production #569 remain open.
The operator will merge both and perform final main/deployed-SHA, clean-checkout and restart
verification. Documentation-only closeout commits follow the tested heads; do not label them as
the already-running revision or claim final-main deployment.

Operator evidence: clean `git status --short` at the candidate SHA, graceful restart at 11:41:57,
ready at 11:42:10 and full startup completed at 11:42:15 (attached log timestamps).
Registration remained 36 primary / 100 grouped / 24 ops with unchanged command cache.

Natural production processing at 11:48:30 selected ACTIVE KVK16 / scan1122 with `test=False`.
Fighting recorded `sent/acknowledged`, positive actual message/channel/guild identity and
`claim=confirmed`; requested and actual destinations matched. KS independently recorded
`skipped/already_sent`. The adapter and processing caller logged the same correlation and receipt,
not two sends. Empty/unavailable fighting data still produced the existing report.
Exact message, correlation and session identifiers are retained in private operator evidence.

The isolated Pre-KVK session sent at 11:47:02 UTC, committed receipt/projections, retained the
committed attempt on read-only status at 11:47:58, then edited the same message at 11:48:13.
Fresh-admission blocking was reported as a read-only observation. This session proves isolated
send/status/edit behavior, not natural seasonal admission or a post-session restart test.
No live failure injection or forced duplicate was required.

Final production validation: 3514 passed, 2 skipped; promoted hooks/whitespace passed.
Mirror log-noise validation: 3512 passed, 2 skipped before two extra offline load-failure cases;
operational logs unchanged; final focused suite 31 passed. Both review rounds were addressed
and resolved. Full security scan `9884a327-68c2-48ff-9ff9-f548bec39b88` and follow-up
`cf1d3cfe-2fee-4f4f-b66e-cb947e1beba4` retain complete coverage and no findings, Changes only,
Deep off. Snapshot/test/documentation deltas and promotion equivalence are detailed below/in PRs.

Natural Pre-KVK (about two months away), off-season production observations and Phase 2F's next
natural public-save evidence remain separately tracked follow-ups, not blockers to this acceptance.
ProcConfig failed again at 11:46:51 while restoring autocommit, followed by false completion
reporting. That issue is selected for Phase 2L; it does not invalidate the Discord receipts.

Next: Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting, audit/design first.
No Phase 2L runtime/test/SQL implementation is approved by this closeout.


## Historical pack / starter (superseded where noted)

Begin Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.
Use docs/task_packs/archive/Codex Task Pack - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md.

Combined design and implementation approved 2026-09-09. Local implementation is tested;
continue from the task pack's current implementation record, preserving existing work. Do not
repeat the historical design-approval gate. Full pytest passed (3508/2 skipped). Fresh Changes-only,
Deep-off scan 9884a327-68c2-48ff-9ff9-f548bec39b88 is sealed with complete coverage and zero findings.
The earlier partial-coverage artifact remains historical; use the fresh receipt in the pack.
No production deployment is authorized by this starter.

Scope revision agreed 2026-09-09: capture receipts across fighting, standalone
KS, Pre-KVK and daily/weekly off-season; correct fighting claims so only a confirmed send receipt
consumes a success slot. Read the revised combined design in the pack.
This supersedes the initial fighting/KS-only proposal and preservation of claims after swallowed
send errors. Preserve separate delivery/bookkeeping and partial attempts, including failed edits
before existing production fallback. Unknown fighting delivery gets no success claim or automatic
retry; a later independent natural invocation can still publish. No durable fighting fence is added.

Phase 2J removal is delivered and operator-smoke accepted. Verify mirror #261/production #568
merges, final main/deployed SHA, restart and clean worktree first; those final checks were left to
the operator. Read the archived Phase 2J pack, updated original embed payload audit and active/
resolved deferred registers. Do not reopen removal or change existing H/I sessions/defaults.

Historical initial brief (completed; implementation approval above supersedes its stop gate):
first response audit/scope and architecture ONLY. Trace every seasonal-interface/direct-adapter
caller, including admin_helpers and honor/Pre-KVK upload routes, KS-first side effects, actual
destinations, guards/claims, sends/edits, returns, swallowed exceptions, state/locks and offloads.
The 07:16 natural ACTIVE KVK16/scan1121 route and legacy 2/3 claim do not prove message receipt.
Propose truthful sent/edited/skipped/failed/unknown outcomes with actual identity where available,
including partial KS/primary results. Preview receipts are not production admission. Preserve
production empty-data behaviour, mentions, cap value and existing prechecks. The explicitly proposed
eligibility change is no fighting success claim without receipt. Preserve existing KS claim timing,
Pre-KVK/off-season reservations and no-new-automatic-retry semantics.

Produce safe/fix-now/defer/not-runtime findings, exact manifests, separately gated SQL manifest,
helper reuse, selector/risk tests, Changes-only/Deep-off routing, natural smoke and bounded rollback.
Do not introduce durable reservations, retry/recovery protocol, new commands, SQL/calendar mutation,
live state swapping, global monkeypatch, forced duplicates or appearance redesign. Keep ProcConfig,
executor audits and lifecycle/DM/JSON work separately captured. Natural Pre-KVK admission and
Phase 2F public-save evidence remain pending. Stop for design approval; no runtime/test implementation.
