# D5c pipeline retention group

Scope: offline qualification of processing_pipeline/retain_stage across all seven
pipeline stages. Existing approval covers preparation, review and one bounded
pass. No operator console action is required. The latest restart receipt is
accepted, leaving 1,260 native seconds including the 1,000-second reserve;
Windows tests retain 50 seconds; 21 inputs remain consumed; fixtures remain 11/64.
The pre-group countdown is 22/73 routes accepted, 51 remaining.

The original ProcessingPipelineRecovery and PipelineReceiptDAL bodies run through
the established isolated AST loader and original serialization, identity, mutex,
token, compare-and-swap and review-snapshot helpers. An inert SQL transport checks
the fixed query shapes, bindings, transaction ownership and resulting records.
No project startup, SQL driver, VM, business worker, input file or provider is used.

The matrix contains 147 behavioral scenarios (21 per stage) and seven runner
controls. It covers not-started/running/unconfirmed predecessors, prior decision
history, stale and changed evidence, account/storage scope, missing stage,
registration change, worker exclusion, lost compare-and-swap, final-boundary
version/association changes, actor refusal, UTF-16 history limit, and durable
reconciliation. Successful retention must preserve the original operation and
previous outcome in history, mark only the chosen stage skipped, increment its
version exactly once, leave every other stage and retained owner untouched, and
never dispatch business work. Reconciliation must add no second write.

Linked-producer result adoption and actual stage continuation are separate routes.
The retention fixture starts without linked producers; a late association must
invalidate the final evidence snapshot. It does not prove native transaction
isolation, physical connection cleanup, or every independent producer validator.
Acceptance must state this boundary; no native/family closure follows from the
offline result alone.

SQL contracts were checked against the authoritative ProcessingPipelineRun and
ProcessingPipelineStage definitions, including exact stage/state sets, unique
operation identities, version constraint and UTF-16 JSON limits. SQL sources and
application runtime remain unchanged. No new production abstraction or deferred
runtime correction is introduced.

The unchanged runner limits are 300 seconds and 1 MiB combined intent/result;
exclusive creation, first failure stops, exact source/evidence pins, no network,
SQL/provider import, subprocess, unlisted write or new worker thread. The current
1260-second native balance is carried through without spending it offline.
All earlier failed and accepted packets remain pinned. Independent Changes review
(Deep off) must complete before the pass. Any related correction gets a new
preserved packet identity under the user's existing additional-pass approval.

Targeted bounded runner checks are selected. Full pytest, application smoke imports
and command-registration tests are skipped because they invoke unrelated startup
and cannot supply the native evidence this offline packet explicitly excludes.
There is no PR, promotion or deployment in this scope.
