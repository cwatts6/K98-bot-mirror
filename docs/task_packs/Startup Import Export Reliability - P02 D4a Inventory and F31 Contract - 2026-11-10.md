# P02 D4a inventory and F31 contract

Status: implementation in progress; installed evidence and consumer disposition
remain open. This is a supporting delivery record for the accepted
[D4 scope review](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Scope%20Review%20-%202026-11-10.md).
The operator authorized D4a-e implementation, individual mirror merges, and a
combined private PR through merge readiness. Production merge, installation,
restart, business execution, backup dispatch and recovery are not included.

## Reproducible source inventory

`scripts/p02_d4_inventory.py` reads Git-tracked Python and authoritative SQL files
without importing application modules or connecting to a database. It records
41 reviewed object roots, source definitions or their absence, lexical caller
candidates with exact source hashes and line numbers, repository revisions and
whole-source manifest digests. Bounds are 8192 files per repository, 2 MiB per
file and 128 MiB total per repository. Missing tracked files and paths escaping
the repository refuse collection. Output is created once and is never overwritten.

Run from the Bot checkout, using a new private output filename:

```powershell
.venv/Scripts/python.exe scripts/p02_d4_inventory.py `
  --bot-root C:/discord_file_downloader --sql-root C:/K98-bot-SQL-Server `
  --output .codex_artifacts/p024/d4a-source-census.json
```

Each lexical match requires review: comments, fixtures, dynamic SQL strings and
the generic identifier TEST can match. No matching reference is not proof that a
procedure has no installed, external or manual consumer. Source hashes describe
the actual working-tree bytes; a repository revision alone is not that proof.
The inventory is a root census, not a complete transitive dependency certificate.
The scope-review caller matrix supplies the reviewed business-family mapping.

The initial census at Bot `c4a71a25` / SQL `0ebe0d3f` confirms absent authoritative
definitions for `KS4_UNO_SEQ` and `usp_start_rok_tracker_log_backup`. Their callers
remain included. No fixture definition is substituted for installed evidence.

## Installed metadata collection

`scripts/collect_p02_d4_installed.ps1` is a fixed metadata-only collector for
Windows PowerShell 5.1 on MINI_AMD. It uses local shared memory and the operator's
existing integrated identity, verifies the SQL server/database, and reads only
ROK_TRACKER and msdb metadata. It does not load application configuration or
credentials, invoke business procedures, request backups or change schedules.

It collects root definitions and owners, sequence properties, dependency and
lexical caller candidates, database/object/schema grants, role membership,
signatures, synonyms, and candidate SQL Agent step bindings. Job command bodies
are hashed, not copied. Raw module definitions and principal names stay private.
The receipt includes the collector's own SHA-256 and collection times.

Collector version 2 also records object creation dates, cached procedure execution
statistics with cache times, SQL Server start time, and Query Store configuration
and retained statement activity. These are read-only observations: alteration dates
are not execution dates; cache eviction/recompilation can remove older execution
evidence; Query Store counts are statement observations, not procedure invocation
counts. Missing, unavailable or empty history never establishes non-use.

Version 2 includes all bounded SQL Agent jobs/steps with job IDs, including jobs
without steps. The earlier database/name filter could miss a wrapper that targets
a job only by GUID. Step command bodies remain excluded. The same row/byte/time
bounds apply; exceeding them leaves the section unavailable, not complete.
Verify the receipt's internal version and collector hash, not its filename: naming
an original-collector receipt `v2` does not add these sections. Use a new output
filename on each run; the private receipt is never overwritten.

Limits: five-second connection timeout, three-second statement timeout, zero
row-lock wait, low deadlock priority, 512 rows per query with a 513th-row overflow
sentinel, 1 MiB per cell, 4 MiB aggregate cell data and 8 MiB serialized output.
A sixty-second collection budget is checked at query/row boundaries; an in-flight
bounded connection or statement can finish after that boundary. Partial or denied
sections remain explicitly unavailable. NULL definitions or missing rows under
limited visibility must not be classified as absence.

The receipt file uses CreateNew and an explicit non-inherited ACL for the current
Windows identity and SYSTEM before the first evidence byte. Existing receipts are
never replaced. Copy the script outside the installed application tree and choose
an existing private output directory. Do not commit the resulting JSON or attach
its raw definitions/principals to a public PR.

This collection does **not** establish effective application/backup-principal
permissions, Windows Task Scheduler bindings, manual/external use, complete
dynamic dependencies, exact installed Bot/updater pins or operational health.
Those remain named D4a/b/d inputs. Empty job results do not retire a route.

## F31 supported contract

Until installed/operator evidence explicitly retires a named route, UPDATE_ALL,
its nested UPDATE_RALLY_DATA call and direct Rally calls remain in scope.
The existing CSV and XLSX paths are distinct; F29 XLSX filename/error deduplication
remains P03 and is not closed by F31.

| Boundary | Required behavior and evidence |
| --- | --- |
| Entry and arguments | Preserve the public stats arguments and exact ready-file identity. Record actual legacy configuration, including fixed historical KVK inputs. No silent translation into modern imports or current-season values. |
| Transaction owner | Public entry refuses existing and implicit caller transactions before file or SQL effects. A supported nested Rally core participates in its parent's transaction and never commits, rolls back or archives the parent's work independently. Direct Rally needs its own explicit owner. |
| Independent inputs | Stats and Rally require separate content-bound custody. The KS4 claim is not a Rally claim. Bind immutable bytes, canonical approved location, operation and resulting committed receipt. Same filename/different bytes is a new/conflicting input, never assumed replay eligibility. |
| Missing Rally input | Preserve an explicit optional/missing disposition if that is the supported installed contract. Missing input must not manufacture successful Rally output or a claim to have imported it. Other file errors are failures, not absence. |
| Shared effects | Identify every written output and latest-name table. Serialize against modern writers, final reports, player publication, optional maintenance and metadata readers using the established guard order. Do not assume the KS4 import mutex covers all outputs. |
| Child failure | Original SQL/file failure reaches the caller. PRINT-only errors cannot allow the parent to commit partial work. Cleanup failure must not replace the primary failure. |
| Rollback | Failure after Rally and before parent commit rolls back database effects and preserves the exact input for reviewed continuation. No file deletion or destructive move during the business transaction. |
| Durable commit | The Rally receipt and supported business effects commit atomically with their actual owner. A lost commit acknowledgement is unknown until the exact durable receipt is read; it never authorizes a second import. |
| Post-commit archive | Archive is a separate, content-checked stage. Commit success/archive failure resumes archive only. A replacement file at the old name is never removed. Missing source plus matching archived bytes can reconcile only to the exact committed receipt. |
| Retained/legacy state | Do not invent success for old files, claims or unreceipted outputs. Preserve unknown evidence and require a named disposition. No age-based release, unconditional cleanup or adoption during migration. |

Required failure matrix: direct and nested calls; outer/implicit transaction
refusal; missing input versus file-access failure; child SQL failure; parent failure
after Rally; commit loss; post-commit archive failure; process loss before/after
archive; same-name changed bytes; modern-writer/maintenance/reader overlap in both
orders; denied principals; original-error preservation. Existing XLSX tests and
synthetic sequence definitions cannot stand in for this matrix.

## Validation and remaining closure

The inventory tests cover missing definitions, retained unknown consumers,
non-disclosure of source text, tracked-file selection, missing/escaping files,
file/aggregate limits and manifest drift. Native PowerShell checks cover the wrong
machine, private ACL and no overwrite. Fixed SQL queries were executed against a
new owned local disposable database and read-only local msdb metadata; no job was
invoked. This validates collector mechanics, not production permissions or use.

The inventory slice changes file handling, metadata access and subprocess usage:
its security gate is an exact Bot **Changes** review, Deep off. SQL changes retain
their own separate review target. Required architecture, deferred-item and routing
validators apply. Full Bot tests, application imports and command registration add
no relevant coverage to this standalone collector; use the focused tests here,
then the normal broader gates for runtime/release slices.

Open closure inputs: fresh installed receipt; explicit used/unused/unknown consumer
dispositions; sequence/wrapper source reconciliation; effective runtime identities;
installed scheduler and release tuple. D4a is not complete merely because the
collector passes or the source-only matrix exists. D4b's independent direct-child
correction may proceed while these inputs are collected.
