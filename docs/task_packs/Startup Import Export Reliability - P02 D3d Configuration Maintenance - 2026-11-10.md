# P02 D3d: configuration maintenance
- CREATE_DELTA_TABLES Step6 upkeep and Step7 optional DeltaProcessingLog move after the business boundary. Preserve all delta calculations, required inserts, target-publication identity and sp_TARGETS_MASTER typed outer-transaction validation. Record due metrics before the existing nested COMMIT; it must remain invisible/rollback-able until the actual outer commit.
- Keep 168-hour and 5000-row eligibility, existing index page/fragmentation thresholds and MAXDOP2. A fixed singleton configuration summary coalesces row totals, last batch/scan and large-batch generation; no unbounded queue. With DeltaProcessingLog present, retain its maintenance-history evaluation and account for coalesced prior batches. With it absent, only qualifying individual >=5000-row batches request upkeep. D4 seeds exact installed history; optional log access must not determine business success.
- Configuration child runs under existing actual maintenance ownership. All maintenance also acquires the existing DeltaPreprocessing mutex with zero wait before claim, preserving producer order (snapshot then delta), covering standalone delta callers. Bot DAL must explicitly release/verify that fourth session guard before pooling.
- Persist configuration row/large-batch acknowledgements with exact main claim completion in one short owned transaction. Newer due metrics remain pending; failed/unknown work cannot automatically replay. Optional timing log failures are recorded separately from upkeep outcome; do not relabel committed configuration or successful upkeep due to log failure. Index maintenance errors must no longer be swallowed as success.
- Native tests compile actual CREATE_DELTA_TABLES and child against authoritative disposable tables; exercise standalone/nested commit+rollback, no-new-row path, real upkeep, eligibility with/without optional log, log failure, mutex order/competing maintenance and exact acknowledgement/new generation. No synthetic COMMIT is accepted as proof of typed outer publication.
- Separate Bot/SQL Changes review, focused existing configuration caller/contract/updater tests. No changes to backup policy, grants, installed source allowlists or production. D4 manual/installed/signing and D5 cost remain. Approved all-D3 instruction covers implementation.

Implementation and qualification checkpoint:

D3c is merged in Bot mirror PR 515 (2d1103df) and SQL PR 143 (faddbd12). D3d
preserves the complete delta business prefix and unchanged sp_TARGETS_MASTER
source. Only transactional maintenance registration is added before the existing
COMMIT; all calculations/inserts and outer transaction semantics remain intact.
The optional worker holds the existing delta mutex before claim, releases it in
reverse order, and verifies the fourth session guard before returning a pooled
connection. The short summary/main completion acknowledgement is atomic.

The fixed singleton summary coalesces rows and qualifying individual large-batch
generations. With the optional log present, coalesced prior batches contribute
to the unchanged 168-hour/5000-row eligibility. Without it, small batches do not
combine into a newly qualifying large batch. Optional log failure preserves
UpkeepCompletedGeneration and UpkeepDisposition, records FirstLogErrorNumber,
and leaves the overall packet failed without automatic replay; committed
configuration is not relabelled. Dynamic index identifiers are quoted, catalog
selection is limited to dbo, and the local cursor closes on child failure.

Native tests passed 18 configuration cases: actual standalone/nested delta
commit/rollback, no-new-rows, real child statistics and >1000-page fragmented-index
rebuild, thresholds/coalescing with and without the log, failed log and failed
completion acknowledgement, real child failure and cursor cleanup. The combined
maintenance/native/Python selection passed 67 cases. Six existing typed-parent
contract cases also passed (that parent fixture uses a nested child stub); these
are separate evidence from the actual delta child tests, not a claim of full
production target-publication execution. 132 focused updater cases passed.

The KS4 table source references KS4_UNO_SEQ, but the authoritative repository has
no sequence definition. The owned fixture omits only that default and supplies
explicit SCAN_UNO values; no sequence contract was guessed. D4 must reconcile
that installed dependency. All actual delta table columns/indexes and procedure
business statements otherwise come from authoritative sources. No retained
server/database settings, provider work or production data were changed.

The updater family has eight members, one changed; all 84 predecessors retain
digest 67b4604add045e736faff4ed7598db5c6c5d2bbde112878961dbd558e2d4c493.
There are 85 entries, with the byte bound and combined-jump refusal unchanged.
Source/mutation checks authenticate eleven SQL candidates; historical contracts
remain immutable. Separate Bot/SQL Changes review and PR review remain required.
D3e-g, D4 installed/manual/signing compatibility and D5 combined cost remain open.
