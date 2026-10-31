# Scoped application index metadata correction — 31 October 2026

The isolated native comparison found that two application index catalogue reads
exceeded the existing 15-second statement limit. Their original queries returned
in 19.046 and 19.047 seconds. Resolving the pinned object scope into a statement-local
table variable, then joining catalogue names, returned identical ordered columns
and rows in 0.483 and 0.264 seconds (1,515 and 704 rows). Joins alone still timed out.
These are single-run lab measurements, not a production latency guarantee or proof
of an individual query-plan cause.

The DAL now uses those materialized reads for explicitly scoped application index
metadata and portable index identity. Scope remains one bound JSON parameter;
DISTINCT and NULL filtering preserve IN semantics for duplicate, aliased and missing
objects. SELECT columns, ordering and fingerprints are unchanged. Unscoped and
fixed coordination-contract reads retain their existing queries. The shared local
scope prefix avoids duplicating the preparation logic; separate SELECTs preserve
the independently reviewed output contracts. No new general helper is needed.

No business table, schema, role, credential, connection budget, transaction ownership
or installed updater authority changes. The authoritative SQL repository was checked;
this change reads SQL Server system catalogues and requires no SQL migration. Metadata
visibility still fails closed. Failure propagates without fallback or SQL replay.
The exact successor hash fixture is test-only and cannot authorize installation.

Focused tests cover raw/portable scoped reads, unscoped compatibility, bound empty,
duplicate, missing and hostile-looking scope values, unchanged row/null/order mapping,
visibility refusal and query failure. Existing schema, permission and archive contract
tests remain applicable. Native comparison establishes equality for the lab scope;
fake-cursor tests do not establish SQL Server semantics or query performance.

Before deployment, rebuild the verifier from the final reviewed source and qualify
all archived startup contracts at the unchanged 15-second limit. Continue the installed
updater format bridge, authenticated bootstrap and combined updater/recovery rehearsals.
The final release must pin private-main source, SQL/tool/policy identities and rollback
artifacts. Production deployment remains separately approved against that final packet.

No unrelated refactor or new deferred item is introduced by this narrow correction.
Security routing: Changes review of this Bot patch, Deep off; SQL repository unchanged.
