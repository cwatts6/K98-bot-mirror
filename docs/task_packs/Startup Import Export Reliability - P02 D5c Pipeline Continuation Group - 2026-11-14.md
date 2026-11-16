# D5c pipeline continuation group

Existing approval covers preparation, review, one bounded offline pass and related
test-only corrections. No additional approval or PowerShell execution is needed.
Current countdown is 23/73 final-action routes accepted, 50 remaining; 25/25
inspectors and 9/12 D5c families are accepted. This packet targets one route,
`processing_pipeline/continue_stage`, with all six eligible stages together.

## Scope and design

Reuse the accepted retention fixture and original pipeline service/DAL bodies.
Load the original continuation context, stage lifecycle, guard, start, observe,
serialization and reconciliation bodies. Replace only the thread transport with
direct calls and business worker/result observation with explicit inert probes.
No actual import, maintenance, report, export, cache or provider work is admitted.
The original `_run`, strict business workers and outcome validators are not
qualified by these probes; their source/native proof remains separate.

The runner invokes this group's cases synchronously outside its existing bounded
offline event loop, so original synchronous recovery can drive the original
asynchronous stage lifecycle without nesting an event loop. It uses the same
network/native/import/thread/file restrictions and exclusive attempt receipts.
Seven safety controls exercise those boundaries before behavior cases.

The 135 behavior cases cover 22 scenarios across six stages and three explicit
refusals: import cannot continue; export cannot continue without its producer;
configuration-only publication cannot be dispatched as pipeline export.
The stage scenarios include success, retained history, stale token/version/scope,
changed configuration, live worker, late competing state, wrong actor, history
overflow, failed decision/start CAS, changed registration/action after the saved
decision, worker failure, observation contention/loss and exact reconciliation.
Assertions inspect saved operation/version/history, exact selected worker count,
no early dispatch, untouched other stages and owner, and logical resource cleanup.

The authoritative ProcessingPipelineRun and ProcessingPipelineStage SQL definitions
were read before fixture implementation: seven stages, five states, positive
versions, unique operations and 32,768-byte UTF-16 decision/evidence limits.
Existing source snapshot/association validation remains loaded and exercised.
No schema, DAL, application or production file changes are included.

## Review and validation

Security decision: Changes review, Deep off, exact isolated five-file snapshot.
Review the test, runner adaptation, preparer, packet and this plan before running.
Original source and SQL pins are included. Independent review must address event
loop ownership, exact mutation routing, effect exclusion and history preservation.

The explicit test selection is the 142-check bounded runner rather than broad
pytest/application imports, which would bypass this qualification's startup and
effect boundaries. Selector recommendations for a changed test normally include
the full suite and smoke/registration checks; those and PR-wide architecture,
deferred and security-routing validators remain separate PR-readiness work.
No new runtime helper, refactor or unrelated optimisation is introduced. Accepted
test bodies are reused without modifying their original evidence.

## Limits and acceptance

300 seconds and 1 MiB combined intent/result; stop on first failure, no automatic
retry of an existing attempt. Any correction gets separate immutable evidence.
1260 native seconds remain, including the protected 1000-second reserve;
50 Windows-test seconds, 21 consumed inputs and 11/64 synthetic rows are unchanged.
This offline group uses zero native seconds, inputs or synthetic database rows.

Passing cases support the named continuation orchestration route in an inert
model. They do not establish real worker effects, native scheduling, physical SQL
cleanup, linked producer verification/adoption or cancellation-drain timing.
`verify_stage`, native C04/C05 and remaining C06 checks stay open. Update the
countdown only after receipt adjudication, preserving the accepted restart state
and retained canonical owner without replay.
