# P02 D5c restricted finish acceptance and scope refusal plan

## Accepted restricted-account result

Saved receipt `d5c-restricted-sequence-result-50b5e00f79ff406db8d1306d96651c27.json`
matches SHA256 `c9d85d15ac9e7b27b5d85acb6450779384abb7edf91ff76f4f72f5f488566ea7`.
The saved-file adjudicator verifies the frozen wrapper and manifest, lineage,
nineteen current source images, exact fixture, protected metadata, resources,
session identities, actor result and physical cleanup. There are no recorded
errors. The packet used 48 command units, 110 rows and 27,093 receipt bytes.

The actual reader authenticated as the exact temporary login/user
`P02_D5c_Reader_20261112`, SID `9e6e525705d72892284a4ea90005affd`, on the disposable
copy. Its first data query failed with ProgrammingError, SQLSTATE 42000, native
229. One factory call used eleven command units, three SQL statements and one
identity row. No target payload, resource/stream read, fallback or retry occurred.
The administrator independently correlated SQL session 53 and its connection
birth with owned process 2064 and application
`P02D5cRestricted_ba02391455ca4f2ab324c2f0d1782d25`.

Rollback, restored read-committed isolation, physical connection closure and
process exit were acknowledged. DENY, disable, drop-user and drop-login each have
acknowledged results. The final principal query proves both exact names absent;
the final session observation finds no actor/login or original work connection.
Both administrator connections closed. The 799 original permissions match
SHA256 `3a1048abe7ef3e76fe49b05a4de65970aabc86d2470c450f4ab8ea741dc85301`.
The seven fixture rows match
`308abe68ae0efada2bda217282b0e14c03824026b377c93084df7f9d4783042e`.
Original protection, ownership, work/history, candidate definitions, statistics
and backup metadata remain unchanged. No secret was read from guest state.

Whole host elapsed **1.6754424 seconds** debits two: **1,406 native seconds,
50 Windows-test seconds remain; 21 inputs consumed, zero new inputs**. The
restricted scope has 173 unused seconds, but its four packets and one positive/
one denied call are consumed: unused time does not authorize another account,
recreation or retry. No account cleanup remains outstanding for this scope.
Acceptance: `.codex_artifacts/p025/d5c-restricted-finish-acceptance.json`.

## Overall reconciliation

D5a and D5b remain accepted. D5c is partial; D5d failure/restart schedules, D5e
balanced cost pairs and D5f final reconciliation remain open. Production has not
received P02; D6 is a separate release decision. P03 actual blockers and essential
P04 corrections still precede the first normal import/export.

The new saved-file register
`.codex_artifacts/p025/d5c-post-rights-progress-reconciliation.json` binds the
acceptance artifacts for twelve D5c families. It preserves distinctions between
accepted named cases, broader caller gaps and later-phase work. It supplements
the original obligation register; it does not replace it or overwrite the older
offline coverage snapshot. Its C01-C12 labels refer to the D5c case matrix, not
the programme's separately numbered C01-C16 source-family register.

Remaining D5c work includes full inspector variants; season/weights consistency;
queue/pool/unowned-hold observations; adapter-specific and out-of-count action
boundaries; attribution variants; and remaining identity/factory cases. Existing
offline coverage is not proof of all native callers. The accepted configuration,
maintenance, isolation and file cases must not be repeated to refresh evidence.
The final 1,000 native seconds remain reserved for later slices. Seven of the
64 permitted fixture rows are used; further committed rows still require a
separate exact proposal and approval.

## Next concrete preparation: two foreign-scope refusals

Existing approval to complete D5 includes these read-only cases. No new account,
permission change, committed row or retry exception is required. This is the
source plan, not a reviewed executable handoff. Prepare and review both cases
before issuing the first native command; do not run an old script as a substitute.

Use unchanged `ConfigPreparationRecoveryDAL.target_data` and `recovery_snapshot`
with the existing authenticated test administrator factory, pooling off. This
tests application scope filtering; it does not repeat restricted SQL permission
testing or claim another principal was exercised. Reuse the pinned Python/ODBC
bundle and the existing seven-row fixture, preparation
`7afa9c30-00b0-5626-a866-604e921dfd35`.

| Case | Account argument | Storage-owner argument | Required result |
| --- | --- | --- | --- |
| WrongAccount | `d5c_foreign_account_20261112` | `d5c_qualification_only` | SourceConflict at the first preparation fetch; no target or downstream reads |
| WrongStorage | `d5c_config_20261112` | `d5c_foreign_storage_20261112` | Same refusal with the correct account and wrong storage owner |

The deliberate argument strings name no new principal or fixture. Validate the
accepted fixture's real account/storage values before each case. The exact
preparation primary key and parameterized account/storage predicates scope the
query; do not enumerate unrelated accounts to prove absence. An empty first
fetch is required. An unexpected row, permission error, other exception or
returned target fails the case, even if cleanup succeeds.

For each case use one fresh owned process, one factory call and one actual DAL
call. Capture the correct server/database/login, actor PID/application and SQL
connection birth before dispatch. Observe the unmodified query parameters and
first empty fetch; forbid resource/stream reads and commits, and retain rollback,
isolation restoration, cursor/connection closure and process-exit evidence.
No monkeypatch may manufacture the expected data or SourceConflict. Instrument
only accounting, query allowlisting and physical ownership. The original failure
must remain primary if cleanup also fails.

Separate one-shot packets permit adjudication between cases. Stop dependent work
on any failure or uncertain custody; no automatic second case or retry. Each has
a proposed 60-second ceiling, at most 48 command units, 512 rows/result, 2,048
total rows, 1 MiB receipt, 128 KiB manifest and existing actor/source caps. Use
the reviewed common preservation collector and full original permission
fingerprint now that the temporary account is gone. Before handoff, enumerate
every identity, observation, actor, cancellation and closure unit and enforce
the exact total offline; this plan does not assert an unbuilt packet fits.
At most 120 seconds for the two cases leaves 1,286 native seconds, preserving
the 1,000-second later-phase reserve. Windows-test allocation is unchanged.

## Architecture, source validation and tests

Source review confirms `target_data` filters PreparationID, AccountKey,
StorageOwner and ConsumerKind before reading resources or streams. The
authoritative `C:/K98-bot-SQL-Server/sql_schema/dbo.ExportPreparation.Table.sql`
confirms the uniqueidentifier primary key and non-null varchar(128) binary-
collated account/storage columns. No guessed schema, migration or SQL repository
change is needed. `tests/test_config_preparation_recovery_sql.py` supplies the
existing foreign-account assertion; its native setup must not run here.

Tooling belongs in scripts/tests, reusing accepted managed-reader loading,
custody, process handshake and preservation patterns. No command/view/service/
core runtime correction is proposed. The restricted-account wrapper remains
immutable; do not reset its stage intents or reuse its guest secret state.
No new deferred optimisation or unrelated refactor is justified.

Offline tests must establish exact distinct argument cases, correct authenticated
identity, first-query empty result, SourceConflict preservation, rejection of
unexpected success, downstream-read/commit denial, one factory/call, physical
cleanup, unknown-custody stops, all command/row/time bounds and two independent
one-shot intents. Validate actual PS5.1 parsing/remoting shapes. Freeze the
complete new executable/manifest/test set and complete a Bot Changes review,
Deep off, before native handoff. Existing SQL source remains unchanged, so no
SQL-repository diff review is introduced.

This turn only adjudicates saved evidence and writes the continuation plan and
register. Fresh security discovery, application pytest, startup imports and
command-registration execution are skipped: no executable native packet,
application source, configuration, dependency or permission changed. Run the
documentation architecture/deferred/security-routing checks and explicit test
selection; record results below. No native operation was performed this turn.

Validation: saved-receipt adjudication passed; architecture checked 50 Python
files, deferred validation checked 88 Markdown files, and security routing
reported zero warnings/errors. The explicit selector recommended smoke imports,
command registration and four release/schema/permission-repair suites. Those
are skipped for this saved-evidence and prose-only change: no release identity,
schema, permission repair, command registration or application import changed.
The new scope-refusal executable and its focused tests are not yet implemented
or reviewed; no new native handoff is ready from this plan alone.
