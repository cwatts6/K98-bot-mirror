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

Status: design/source implementation in progress; no D3b acceptance claim yet.
