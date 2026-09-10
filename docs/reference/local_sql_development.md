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

## S2B repository closeout — 2026-09-10

S2B SQL #79, mirror #265 and private bot #572 are merged. Both local repositories were pulled
by the operator; the bot machine was not updated. Repository merge is not production SQL
execution. Preserve both evidence databases. S3A uses pure offline tests and requires no SQL
connection, database rebuild, bot restart or source activation.


## S3A merged closeout and S3B handoff — 2026-09-10

GitHub readback confirms mirror #266 merged at 11:28:48 UTC as
`3154997fa2dfc124da75ee35dca79463c3196a43`, and private bot #573 at 11:29:18 UTC as
`140fc89765b1d6ec8418ac6f6d039e575419c29e`. The synchronized local mirror main is
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`; SQL main is
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both local repos were clean at documentation
entry. Operator confirms local pulls complete, with no bot-machine pull or restart.

Operator smoke on mirror `d5cf27613e54047efb856f4bc3777ee6923fa14e` passed 77 tests in
3.10s, operational logs unchanged, and command registration 36/100 without drift or duplicates.
The prior implementation/regression results (260 tests) and separate completed production/mirror
Changes reviews remain in the archived S3A pack; those are historical runs, not newly rerun here.
S3A runtime/test contents matched the production candidate. Repository merge is not deployment.

S3A pack and starter are archived with repaired links. All predecessor evidence is retained.
Start S3B in a new chat using its refreshed pack/starter only with explicit S3B G3 approval and
an explicitly named disposable SQL integration target. Existing S2A/S2B evidence databases are
retained and not authorized for reuse/rebuild by this handoff. The bot machine need not be updated
for S3B local development. No SQL connection, service start, production action or successor
implementation occurred in this documentation closeout.

These documentation edits, including untracked archive destinations, remain pending for the
separately authorized S3B PR. Its pack contains the full carried-forward manifest and requires
both sides of renames, repaired links and preservation checks. No commit/push/PR is performed
by this closeout. Security routing: exact Markdown-only skip (status, evidence, links and archive
moves; no runtime/config/permission/data-access effect), plus separate SQL no-change skip.
