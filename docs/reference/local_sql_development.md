# Local SQL development environment

## Purpose and boundary

Use this permanent local SQL Server instance for explicitly approved development and disposable
integration tests. It is independent of the production SQL server. It is not a replicated mirror
and does not contain a production data copy. Authoritative SQL definitions remain in
`C:/K98-bot-SQL-Server`; database contents are test evidence, not the schema source of truth.

## Verified setup — 2026-09-09

| Setting | Value |
|---|---|
| Local server | `9SX2VF4\K98DEV` |
| Local connection alias | `localhost\K98DEV` |
| Engine | SQL Server 2022 Developer, 64-bit |
| Version | `16.0.1200.5` (KB5122771), matched to operator-supplied production version |
| Authentication | Windows Authentication; installing Windows user added as SQL administrator |
| Server collation | `SQL_Latin1_General_CP1_CI_AS` |
| Development database collation | `Latin1_General_CI_AS` |
| Database compatibility | `160` |
| SQL max server memory | `8192 MB`, configured and active; host has 32 GB RAM |
| Service | `SQL Server (K98DEV)` / `MSSQL$K98DEV`, Manual startup |
| Client | SSMS installed separately; local connection uses Trust server certificate |

The instance was patched and the PC restarted before the final version verification. Microsoft
signature and published update SHA-256 were checked. These are dated setup facts; verify the
current instance/database before each execution. Read-only service check on 2026-09-10 found
`MSSQL$K98DEV` stopped, with Manual startup unchanged.

## Starting a local session

1. Open SQL Server Configuration Manager, select SQL Server Services and start only
   SQL Server (K98DEV) if stopped. No production service or bot restart is involved.
2. In SSMS, connect to `localhost\K98DEV` using Windows Authentication. Trust server certificate
   is a setting for this local development connection; it is not a production connection policy.
3. Verify `SERVERPROPERTY('ServerName')`, `SERVERPROPERTY('ProductVersion')`, `DB_NAME()`, database
   collation and compatibility against the explicitly authorized target before executing SQL.

SQLCMD is available at
`C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/170/Tools/Binn/SQLCMD.EXE`.
Prior local runs used explicit `-S lpc:localhost\K98DEV`, Windows authentication `-E`, `-C`, a
named database `-d` and fail-on-error `-b`. No password or production connection string is needed.
The agent sandbox could not authenticate; approved elevated local tool calls worked. This is
execution-environment behavior, not permission to search for credentials or alter security config.

## Retained S2A evidence database

`K98_S2A_Disposable_20260909` on the server above was explicitly authorized for S2A only. It has
the revised twelve S2A tables, 18 enabled/trusted foreign keys and 89 enabled/trusted CHECK
constraints. Last independent readback after the review fixes found zero rows in every table.
The fixture passed 96 expected rejection cases and positive correction/status checks, with full
rollback; the static validator passed 401 assertions. No production data was imported.

Retain this database as S2A evidence unless its rebuild/removal is separately within an approved
test operation. It is not an automatically authorized target for S2B or later slices.

## Retained S2B evidence — 2026-09-10

The operator authorized `9SX2VF4\K98DEV` and `K98_S2B_Disposable_20260910` for S2B.
Creation with compatibility 160 and `Latin1_General_CI_AS`, accepted S2A prerequisite
installation and migration `20260910_001_kvk_source_publication_state.sql` passed.
The service was already running at execution; no start or restart occurred.
Initial validation passed 131 rejection cases; the S2B PR review revision passed 144, with
265 static assertions and full 25-table rollback. The reviewed migration was retested by
transactionally replacing only verified-empty S2B tables in this same authorized database.
The accepted S2A migration and separate S2A evidence database were preserved. Independent
readback found 25 empty tables, 47 trusted/enabled FKs and 165 trusted/enabled CHECKs.
The separate S2A evidence database remained unchanged. Both databases are retained.

## Future slices

The instance can be reused; each slice must explicitly name and authorize its disposable database.
S2B authorization and completed execution are recorded above; neither retained evidence database
is automatically authorized for a later slice or destructive rebuild.
Use synthetic fixtures and the accepted S2A migration as prerequisites; installing prerequisites
in a fresh test database does not reopen S2A implementation or automatically execute another pack.

Keep migrations/fixtures in their owning slice's exact SQL manifest. Recheck migration date and
sequence at authoring time; the proposal in a prepared task pack is not an allocated slot.
Production deployment, real imports/exports, Discord actions and source activation remain separate.
