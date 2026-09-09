# Phase 2J — Ops Diagnostic Convergence

Status: proposed next scope; first response audit/architecture only. Stop for operator approval
before runtime or test implementation. This preparation is documentation-only and does not approve
retaining, replacing or removing a command.

## Entry gate and accepted baseline

Read the archived Phase 2I task pack and delivery evidence first. Verify mirror #260 and production
#567 merge states, final main heads, clean branch/worktree, source parity with reviewed runtime
heads 06f31a94 / d89e606c, actual bot-machine deployed head and restart evidence. The operator owns
merges and final verification; never infer a deployed SHA from an unversioned startup log. Confirm
Phase 1–2I source and registration, including v1.06 historical selection and existing v1/v2 sessions.

Collect the 2026-09-09 morning natural production run if available: actual seasonal selector,
eligibility/guard result, admission/receipt where supported, message identity and associated state.
A generic success log, skip, diagnostic edit or absent data is not fresh dispatch proof. If evidence
is unavailable, retain a named pending observation; do not force dispatch or fabricate calendar/SQL
data. Track Phase 2F natural public save separately. This gate checks evidence before new design;
do not silently mark pending deployment verification complete.

## Scope and source leads

Audit `/ops test_embed` in commands/admin_cmds.py and every downstream route of
send_stats_update_embed, including active fighting and off-season/Pre-KVK selection. Current source
passes is_test=True and emits an unconditional success response after the awaited call; verify the
actual return, exception and destination contracts before classifying defects. Trace all sends,
edits, mention policies, guards, caches, state files, locks, returns, offloads and exception handling.
Compare the accepted Phase 2H real isolated reservation diagnostic and Phase 2I appearance preview.
Do not assume fighting-KVK shares Pre-KVK reservation semantics.

Determine whether the old command is worth keeping: compare retirement with clear routing guidance,
a compatibility wrapper delegating to existing safe diagnostics, and a narrowly justified replacement.
Recommend one approach after tracing coverage and gaps; avoid a third competing session framework.
Keep `/ops` at or below 25 children (currently 25). Prove real Pycord invocation and serialized
options, nested group limits and existing permission/version/usage contracts. Do not add a child as
a workaround. Do not redesign embed appearance or broaden the audit to unrelated diagnostics.

## Architecture and contracts to propose

Commands own authorization, explicit validated destination and private responses; services own
orchestration and truthful outcomes; DAL/store code owns reads, durable sessions and receipts.
Reuse established helpers. If publication is retained, disable mentions, bind owner/guild/channel,
use isolated state and define run/status, identity, historical selection compatibility, reopening,
retention/capacity/offline cleanup, permissions, cancellation/drain and uncertainty without retry.
Preserve Phase 2H sessions and both versions of Phase 2I sessions, including selected-KVK binding
and honor omission. Do not migrate or retarget existing evidence. State exactly which route proves
appearance and which exercises real admission/receipt; reservation extensions require a separate gate.
Audit once-only offload entry and failure propagation in the touched route only.

## First-response deliverables

Produce safe / fix-now / defer / not-runtime findings with exact source traces; retain/replace/retire
comparison and recommended command contract; layer ownership and helper reuse; exact runtime/test/
tooling/docs manifest with inspected-only files separated; separately gated SQL manifest (expected
empty). Any proposed bot-side SQL/DAL change requires authoritative validation against
C:\K98-bot-SQL-Server and explicit approval. No SQL/schema/ProcConfig/calendar changes are authorized.

Define selector/risk tests: active/off-season/missing data, guarded/unavailable/failed/uncertain
returns, false success/destination claims, rejected owner/destination/revoked permissions, mentions,
payload aggregate limits, no live-state mutation, concurrency/restart and cancellation/offload counts.
Use real Pycord invocation/serialization and regression coverage of existing Phase 2H/2I diagnostics.
Locate exact tests with scripts/select_tests.py after defining the manifest; justify focused/full,
log-noise/import/registration and architecture/deferred/security-routing checks. Future runtime diffs
use Changes-only, Deep off, immutable separate mirror/production ranges; SQL is a separate no-diff
skip unless explicitly changed. No Codebase or Deep scan is authorized.

## Operator smoke and rollback to finalize after approval

Capture production and existing diagnostic baselines, record deployed SHA/restart, invoke the
approved command only to an explicit safe destination, and retain outcome/token/message/receipt.
Check read-only status, unchanged message identity on edit and after restart, ownership/revoked
permissions, truthful no-data/guarded outcomes and state isolation without deliberate live failures.
Do not force duplicate sends or retry ambiguous publication. If retiring the command, verify removal
or approved guidance behavior and existing diagnostics directly. Rollback must preserve stored
sessions/receipts and handle command-schema resync; no reset/purge/live state swapping.

## Exclusions and acceptance boundary

No global monkeypatch, live state swapping, forced duplicates, production eligibility bypass,
calendar/SQL changes or appearance redesign. Singleton/public-child lifecycle, generic view timeout,
DM/broad JSON redesign, Stats/KVK History executor audits and ProcConfig error/false-success repair
remain separately scoped. Do not conflate the touched command's success reporting with a broad
logging rewrite. Diagnostics cannot prove exactly-once or every live failure mode.

The first response ends after scope and architecture for approval. Do not implement commands or tests.
