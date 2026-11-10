# D3b durable maintenance ownership

The operator authorized continuing D3b–g, merging each focused mirror PR and
creating/reviewing the combined private Bot PR. Deployment remains held until
after D5. D3a mirror PR 513 merged at
`1e001aad3aa5cee340280acce3a7b0753173162d`; its final review correction confines
cleanup failure handling to the current operation, including callers entered
inside an already handled exception.

## Scope and architecture

Use the existing explicit post-import invocation, pipeline stage receipts,
physical thread drain and SQL snapshot writer guard. Add six fixed coalesced
SQL maintenance records, one for each accepted D3 boundary. The business
transaction records due work; a separate autocommit SQL worker owns its claim
and executes fixed children. No general scheduler, timer, expiry or unowned
background task is introduced. Bot orchestration belongs in services and SQL
execution in a focused DAL; retain the existing file_utils facade.

Only pending work is automatically claimable. A crash after claim leaves running
evidence; after acquiring that same now-free SQL guard, an observer may classify
it unknown but must not execute it again. Failed/unknown claims require exact
reviewed reconciliation, not an age-based reset. Due work arriving during a
claim increments the generation and remains pending after that claim completes.
The six-row bound is independent of the number of imports. First failure and
current state are separate. Recording due work participates in the business
transaction; rollback removes the obligation as well as the business change.

The existing import admission resource checks remain mandatory. Optional worker
admission also requires known log use below 70 percent and a free actual SQL
writer guard. Full qualification retains the 8 GiB host-memory/disk floors and
version store below 512 MiB. No limit or timeout is widened.

D3c–g supply real maintenance children and atomically place due records at their
business boundaries. D3g also owns backup queue claim/acknowledgement and removal
of post-success backup waits. SQL 3961 raw-history/index-rebuild overlap remains
open until actual reader/maintenance exclusion is qualified in both arrival
orders. Metadata SNAPSHOT observations must remain independent of producer
admission. D4 owns final installed/signing/source compatibility, D5 the combined
qualification. These source changes do not authorize an installation.

## Validation plan and review routing

Native disposable SQL tests: due/rollback, exact same-request deduplication,
concurrent worker refusal, generation arriving during claim, real child failure,
crash after claim and completion acknowledgement loss, retained first failure,
both producer/maintenance arrival orders and bounded state. Bot regressions:
complete result consumption, finite receipt validation, cleanup uncertainty,
first-error preservation and cancellation drain. Run architecture, deferred,
selector, security-routing and updater predecessor checks. Separate Bot and SQL
Changes reviews are required; Deep remains off. Local qualification artifacts
must distinguish real children from inert fixture fault injection.

## Coverage corrections before merge

The first nine native cases passed, but the caller/connection review identified
two related gaps. A fresh-process native test with the production-default ODBC
pool reproduced retained SQL session locks after `close()` returned. The original
fixture disabled pooling, so its passing close checks were insufficient. The DAL
now verifies a clean initial session, explicitly acknowledges rollback/guard
release on that still-owned session, and only then closes the handles. Unknown
release retains the open connection/cursor and closes admission. Existing foreign
session ownership is never released. New native cases keep the pooled worker
process alive after both success and child failure and prove competing admission.
The failed baseline remains in the local D3b qualification artifacts.

The Phase52 recovery adapter discarded the new normal-return receipt, allowing
its generic callable worker to label outstanding maintenance successful. It now
raises a bounded outstanding-maintenance error while retaining the committed SQL
receipt. Tests cover complete, pending, running, failed and unknown receipts and
the final recovery-completion marker. No recovery operation was executed.

The caller census also checked existing import-capture and legacy snapshot guard
cleanup: these already verify explicit release and retain uncertainty. Broader
manual/recovery disposition remains D4/P03; this slice does not assert that a
pooled close proves physical release elsewhere. The D3b updater family includes
the recovery adapter and retains all 82 predecessor definitions unchanged.

Initial immutable Changes reviews covered Bot `f333a225` (scan
`3b77917f-3726-41e4-8307-b55437fa3102`) and SQL `48dc44ad` (scan
`d305e947-8e39-4f05-b290-16991aeaee71`) with zero security findings. Both retain
the concrete reliability corrections above; a security result is not D3b
acceptance. The final correction requires its own exact-diff review and checks.

Status: corrections and final validation in progress; no D3b acceptance claim yet.
