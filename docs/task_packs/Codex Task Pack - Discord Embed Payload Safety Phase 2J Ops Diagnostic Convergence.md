# Phase 2J — Ops Diagnostic Convergence

Status: operator approved retirement-with-guidance on 2026-09-09. The implementation amendment
below supersedes the original first-response stop. Production deployment and smoke remain gated.

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

## Approved implementation amendment — 2026-09-09

The operator approved retirement-with-guidance, not a publishing wrapper or command deletion.
`/ops test_embed` v1.08 keeps zero options, admin AND notify/accepted-thread checks, versioning,
usage and safe private replies. It points to H/I with explicit destinations and distinguishes
fighting appearance/preview receipts from real isolated Pre-KVK admission. It states that no
isolated off-season/Kingdom Summary diagnostic exists. No success/destination claim, seasonal
read, publisher, offload, state write or new session framework is required. Failed defer stops;
response failure/cancellation does not retry. Production and H/I contracts remain unchanged.

Runtime manifest: `commands/admin_cmds.py` only. Test manifest: new
`tests/test_ops_test_embed_retirement.py` only. Docs: this pack, README-DEV, canonical command
reference, diagnostics runbook, deferred register and task-pack README. Tooling/config/dependency/
service/DAL/view/startup/SQL/migration manifests: empty. Remove only now-unused handler imports.

Audit: the handler claimed sent/NOTIFY location unconditionally, while the interface selects
STATS_ALERT for broad-KVK or OFFSEASON_STATS otherwise and first sends KS to OFFSEASON. Test
fighting clears live Pre-KVK state; test Pre-KVK edits/replaces/persists live IDs; off-season test
suppresses ping but can claim live KS CSV keys. Interface returns None and loses outcomes;
fighting send exceptions are also swallowed. Retiring ops access fixes its misleading result and
side effects; other production callers and broader executor fallback remain separate work.

Entry: #260 merged at be6607db and #567 at 00817eca. Verified production main
00817ecafc631887d7dcd2436745413e5df5cf09 and mirror main
8cdbb908d391441c5cc6a75a4101f185268a7cfe. Clean mirror and all Python source match reviewed
06f31a94/d89e606c and production main. Operator shell is clean at 00817eca; 05:55 startup predates
06:28 merges and has no immutable process SHA. Runtime preparation proceeds under explicit
implementation approval; merged-head process/restart proof remains required for deployment
acceptance and is not marked complete by that approval.

Morning evidence: ACTIVE KVK 16 at scan 1120 in the 1090..1202 fighting window, empty reporting
blocks, legacy KVK slots 1/3 then 2/3; summary send logged to 1417194970997330001 without message
ID. Generic success/claims are not KVK receipts because legacy send errors can be swallowed. No
fresh production Pre-KVK reserve/commit/message tuple was supplied. Natural calendar admission
and Phase 2F public-reminder atomic save remain separately pending. Prior KVK 15 smoke/restart/
capture acceptance retains operator-report limits and no exactly-once claim. ProcConfig failure/
false success and generic view timeout remain excluded. No dispatch is forced.

Validation: real Pycord invocation and zero-option serialization of v1.08; recursive group limits
and 25 ops children; original owner/notify/thread gates, private mention-neutral bounded guidance,
failed defer, response failure, cancellation and concurrency. Downstream legacy selector/outcome
values cannot cause dispatch. Regress H/I owner/season/destination, strict payloads, status/restart,
isolation and uncertainty. Run selector, focused/full pytest with log-noise validation, imports,
registration, architecture/deferred/security-routing validators and hooks. Distinguish exact pinned
dependency evidence from installed-environment checks. Final results are recorded at delivery.

Security: Changes only, Deep off, immutable mirror base 8cdbb908 to reviewed implementation head.
Production promotion needs its own immutable range; SQL is a separate no-diff skip. No Codebase
or Deep scan. Smoke/rollback follow the Phase 2J diagnostics runbook: record deployed SHA/restart
and baselines, resync v1.08, verify private guide without stats/state/session effects, rejection
and post-restart behaviour. Use retained H/I sessions directly, never a forced duplicate or
ambiguous retry. Preserve all state/receipts on rollback; prior runtime restores unsafe ops
publication, so operators should continue with H/I. No SQL or state reset.

## Candidate automated validation — 2026-09-09

Focused selector/risk/H/I regression matrix: 271 passed. Full suite with operational log-noise
check: 3485 passed, 2 skipped; production operational logs unchanged. Validation used local
Python 3.11 and exact Pycord commit e4738227b3d22e92d3b0be4c016a4c287bb0fd1e (installed VCS receipt),
filelock 3.20.0. The audioop deprecation warning is from Pycord/Python, not this change.
Initial full-suite failures were the Windows local-venv interpreter gate; corrected by using the
checkout's .venv without changing runtime. No unrelated source fix was included.

Architecture, deferred-item and security-routing validators, import smoke and registration pass.
Black/Ruff and applicable pre-commit checks run on the exact eight-file manifest. Final Changes
security review and operator candidate deployment/smoke remain separate delivery evidence.
