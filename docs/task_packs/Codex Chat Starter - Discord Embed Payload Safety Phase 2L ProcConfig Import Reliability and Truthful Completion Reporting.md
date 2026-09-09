# Chat starter — Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting

Begin Discord Embed Payload Safety Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting.
Use docs/task_packs/Codex Task Pack - Discord Embed Payload Safety Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting.md.

First response audit/scope and architecture ONLY. Phase 2L is selected; runtime/test/SQL implementation
is not yet approved. Produce the complete design and exact manifests, then stop for approval.

Phase 2K is delivered, tested and operator-smoke accepted on production candidate
36208765bf7200fa6855f3892e6b32d43b23bccf (mirror 2d892cefcfdfa0a8263efe69997bf292503b23aa).
Verify mirror #262/production #569 merges, final main/deployed SHA, clean worktree and associated
restart first; these final checks were left to the operator. Read archived Phase 2K pack/starter,
updated original embed audit and active/resolved deferred registers. Preserve Phase 2J removal,
H/I sessions/defaults, Phase 2K delivery/claim semantics and no-automatic-retry behavior.

The repeated ProcConfig HY000 connection-busy error while restoring autocommit after
sp_TARGETS_MASTER was observed again at 2026-09-09 11:46:51, followed by worker success and
ProcImport=True. Trace the full path: all direct/admin/startup/pipeline callers, maintenance/callable
workers, run_step/offload/fallbacks, native returns, exit/envelope parsing, reports/manifests,
telemetry, downstream side effects and cleanup. Inspect source-of-truth SQL and nested result sets;
sp_TARGETS_MASTER rejects ambient transactions. No guessed schema or transaction workaround.

Design one complete fix covering resource lifetime and truthful end-to-end outcomes, including
partial committed work, unknown target completion, cleanup/artifact failure, cancellation/timeout
and exactly one backend execution once work may have entered. No automatic replay/recovery protocol.
Give safe/fix-now/defer/not-runtime findings, helper reuse, exact runtime/test/doc manifests,
separately gated SQL manifest, risk/selector tests, Changes-only/Deep-off review, natural smoke
and bounded rollback. No runtime/test changes or live SQL/calendar/state mutation during this audit.

Natural Pre-KVK (~two months away), off-season production observations and Phase 2F public-save
evidence remain independent follow-ups, not blockers to accepted Phase 2K smoke. Keep broader
executor, lifecycle, DM/JSON and durable dispatch-policy work separately captured.
