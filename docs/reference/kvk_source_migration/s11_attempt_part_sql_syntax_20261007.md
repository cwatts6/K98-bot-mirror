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
uses local LPC (`lpc:localhost\K98DEV`) and `tempdb`, checking the reported server
identity is `9SX2VF4\K98DEV` and database is `tempdb` before analysis. It is not a
production test: ordinary CI and production test runs skip the compiler case.
A separate offline case always checks the actual emitted DAL column and parameter
binding without connecting to SQL; local compiler execution establishes the
dialect-specific regression. Do not enable the compiler opt-in on MINI_AMD.

The failed job remains retained and is not replayed by this patch. Protected
source/runtime pins need renewal after review and merge. Fresh export completion,
the startup stats-cache fallback and G5 activation remain separate acceptance
items; successful preflight reads do not prove completed provider writes.

## Shared reserved-identifier regression: BACKUP — 2026-11-15

`BACKUP` has the same delimiter requirement as `ROWCOUNT`, including when used
only as a result alias. The D5d catalog continuation finished all 24 native cases,
then its aggregate query failed on `AS backup`. The accepted cases were retained;
a separate read-only accounting packet used `AS [backup]` and completed the final
counts and closure checks. A reporting failure does not authorize replay.

Use `[RowCount]` for the existing column/preview alias and `[backup]` for the
accounting alias. Delimit every alias in new diagnostic count queries, preserve
result names, and bind values separately. PowerShell parsing does not validate
SQL Server grammar. Prepare final receipt/accounting SQL as carefully as workload
SQL, before consuming an intent or any mutation allowance.

The same `tests/test_export_attempt_sql_syntax.py` now includes
`test_postcase_accounting_quotes_reserved_backup_alias`. It extracts the actual
read-only PowerShell accounting query, checks all five delimited aliases, and
rejects bare `backup`/`rowcount` aliases independent of case and spacing. It never
executes a native packet or rewrites the failed packet. This complements the
existing emitted-DAL `[RowCount]` check and the preview alias regression in
`tests/test_kvk_source_window_preview_sql.py`; it does not claim to be a general
T-SQL parser. The existing opt-in compiler restriction above remains unchanged.

Core guidance: [Coding Execution Guidelines, SQL comparison and accounting](../K98%20Bot%20-%20Coding%20Execution%20Guidelines.md#comparing-submitted-sql-with-stored-procedure-definitions).

## Recurrence and enforcement correction — 2026-11-17

The grouped P02 lab preflight emitted `AS RowCount` again. The previous tests
enumerated older query sites, while the new test mocked the cursor and asserted
the invalid SQL text itself. Documentation and those passing assertions did not
enforce the rule across new queries. This was a coverage and review failure.

The broader review corrected three lab sites, an older PreKvK history alias and
an older MGE completion update using a bare `RowCount` column. The runtime changes
only delimit identifiers. The failed attempt and its unsettled accounting remain
preserved; no replay or cleanup is implied.

The new repository-wide lexical gate, automatic packet query inventory, mandatory
offline Microsoft SQL grammar gate and adversarial discovery tests are described
in [Testing Standards](../K98%20Bot%20-%20Testing%20Standards.md#sql-query-inventory-regression-p02-2026-11-17).
The parser checks complete emitted batches, including nested migration module
bodies; it does not establish live schema binding, permissions, execution or
delivery. Retained dynamic statements and incomplete fragments remain explicitly
identified rather than counted as parser passes.
