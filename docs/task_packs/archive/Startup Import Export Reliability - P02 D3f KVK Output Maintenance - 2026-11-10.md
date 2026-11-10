# P02 D3f: KVK output maintenance

Scope: preserve sp_ExcelOutput_ByKVK calculations, required output table shape,
views and exact final-report receipt. Move its two post-calculation nonunique
output indexes and FULLSCAN after the committed publication. Keep the ranking
child and temporary calculator indexes used by the active business queries;
those are not the post-publication output upkeep being separated here.

One coalesced durable row per canonical KVKFinalReportHeader identity, with typed
positive KVK, exact output object ID/create-date and header revision. No arbitrary
schema/table input and no per-import queue. Preserve claimed identity separately
from newer due identity and immutable first-error evidence. Execute at most one
KVK target per worker invocation, acknowledge that exact target and leave the
aggregate kind pending until every captured-generation target is complete.
Earlier target completion survives a later failure. Failed/unknown work cannot
be automatically replayed or cleared by age. Preserve any existing unique index.

The real output procedure must take the existing maintenance-schema shared
transaction lock before its first mutation, at zero wait. This closes the
standalone producer/maintenance race without inventing another session guard.
Managed producers already exclude maintenance through their snapshot owner;
standalone contention is an explicit pre-mutation refusal, covered natively in
both acquisition orders. Existing transaction/rollback behavior remains.

Native qualification will run actual output calculation/view/receipt children,
multiple KVK targets, repeated/coalesced output recreation, partial completion,
rollback, identity mismatch, failed child/ack, physical exclusion and required
unique-index retention. Exact source preservation plus all affected report/
maintenance/caller tests; separate SQL Changes review and Bot test-only routing.
D4 installed/manual/signing and D5 scale/cost remain. No production action.

Qualification checkpoint:13 native cases execute the actual output calculator,
ranking child, naming view, refreshed output views and exact receipt, using the
authoritative table definitions. Only the documented missing KS4 sequence default
is omitted and SCAN_UNO explicitly supplied. Actual two-KVK output, standalone and
outer rollback/commit, coalesced recreation, unique index retention, failed due
registration, target identity/ack failures, partial completion, unknown attempted
identity and both schema-owner orders pass. 127 combined maintenance/native/caller/
historical-source cases passed in 39.05s with one existing dependency warning.
The first fixture read retained a UTF8 BOM and was corrected to utf-8-sig; an
initial assertion incorrectly excluded SQL's automatic column statistics and now
checks the exact two output indexes plus full sampling of every statistic.

Exact business preservation removes only the post-output index/FULLSCAN block,
then accounts explicitly for the shared schema guard and transactional due call.
Required view/receipt/ranking and legacy index-child sources remain byte unchanged.
All 17 fixed source mutation refusals and immutable P0 receipt checks pass.
Bot has only tests/fixtures/documentation changes; no updater entry or runtime
change. Its Changes scan is skipped for this test-only slice after reviewing
actual files: inert fixed predecessor JSON and mutation/real-SQL tests only,
with no production configuration, permission or installed-admission effect.
SQL uses a separate Changes review, Deep off, before merge.

D3e is merged: Bot mirror 517 at 042231449bfd96f635b97502add8a73b6ba6ee63;
SQL 145 at 2af0a70e268376ae978c4bc8988792c88fd295db. Both CI/code reviews passed;
one newline comment was resolved using Python universal-newline behavior and
passing Windows CI. Formal Changes reviews found zero findings: Bot
cbd742f0-4244-4476-8b49-d97eda014e31 (43 paths, 666242 total tokens; 663527 input,
659968 cached, 2715 output); SQL db6f0ad4-2c97-4e13-8066-394b00519408 (9 paths,
1456138 total; 1450943 input, 1436288 cached, 5195 output). Usage windows overlap and
are not additive costs. D4 must qualify direct/manual helper permissions; the
managed dispatcher enforces all five guards, while earlier direct children
independently check their original four. No claim of direct/manual acceptance.
