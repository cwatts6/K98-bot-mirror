Begin Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.
Use docs/task_packs/Codex Task Pack - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md.

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
