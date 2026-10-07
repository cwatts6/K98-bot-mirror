# S11 attempt-part SQL syntax correction — 2026-10-07

The controlled legacy export reached Google: 22 recorded read requests completed
successfully. Job `5c254191-7dd4-469d-b83a-094dcb58c3ad` then stopped with
`ProgrammingError`; no attempt was committed, its stream closed at sequence 22,
and account ownership was released. No provider mutation was recorded. The
health probe's concurrent refusal was expected account contention, not evidence
that these Google reads failed.

The attempt-part INSERT used the reserved SQL Server keyword `RowCount` without
identifier delimiters. The authoritative schema defines `[RowCount]`. A local
read-only compiler reproduction of the actual INSERT reports SQLSTATE `42000`,
SQL error 156 near `RowCount` (plus analyzer error 11501). Quoting `[RowCount]`
compiles successfully with all nine parameters and binds its row-count parameter
as `bigint`. The owned transaction rolls back the preceding attempt INSERT when
the part INSERT fails, consistent with the observed zero-attempt result.

Only that identifier is changed. Values, parameter order, ownership/fences,
transaction boundaries, execution evidence, provider authorization and failure
handling are unchanged. No SQL migration or permission change is required.

`test_export_attempt_sql_syntax.py` invokes the actual DAL method with a captured
cursor, then asks the explicitly selected local SQL Server compiler to describe
the emitted statement against an inline table-variable shape. The compiler
analyzes the batch; it never executes the INSERT or creates persistent objects.
The test is opt-in with `K98_READ_ONLY_SQL_COMPILER=LOCAL_TEMPDB_COMPILE_ONLY` and
uses the fixed development endpoint and `tempdb`, checking both before analysis.
Ordinary CI skips it; local execution establishes the dialect-specific regression.

The failed job remains retained and is not replayed by this patch. Protected
source/runtime pins need renewal after review and merge. Fresh export completion,
the startup stats-cache fallback and G5 activation remain separate acceptance
items; successful preflight reads do not prove completed provider writes.
