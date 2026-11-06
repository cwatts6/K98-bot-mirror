# MGE release bindings and Windows rehearsal

The descriptor selects only the bounded MGE profile at SQL commit
`9344a37656b034dd43867435e7c039ed20ae1c5e`, with profile SHA256
`8fea59034c0ac0d14cfb6f72e03a3eda9c823648ec2c0fead6cd208bd4312bb0`.
Its permitted installed Bot predecessor is
`2c31de42eb91cf6b7f9f61f3aaf3efc3597c4ea6`, established by approved read-only
installed reference and receipt inspection. SQL PR 136 must merge with that
commit retained in main before this descriptor is released. Source merges do
not install the updater, prepare a package on production, apply SQL or restart.

Production SQL observations at 15:24 and 15:28 UTC on 29 October match the profile:
database collation `Latin1_General_CI_AS`, tempdb collation
`SQL_Latin1_General_CP1_CI_AS`, compatibility 160, exact prerequisite hashes/statuses,
absent finalisation table, bigint parent EventId columns and varchar(20) event
status. Metadata visibility is available; no enabled server/database DDL or ledger
triggers and no MGE parent/result-import triggers were observed. A checksummed,
undamaged full backup is recorded at 01:00:17. These are observations, not a
production preflight result or proof that the backup can be restored. Deployment
must recheck current state. Private evidence export hashes are
`fa1e103e99d349ef3c541b9c18234fc918c807ce63ce949bf753890945330749`
and `eb8701554d12126e4ef2b358c083636784d30dc177698c0b19a86ce15c2fb981`.

## Isolated Windows rehearsal scope for separate approval

Run Windows PowerShell 5.1 on the development PC with a real administrative token.
The current Codex shell is not elevated. User authentication/UAC must be completed
by the operator. Never substitute production as the rehearsal host.

The existing scripts create fresh GUID-suffixed fixture directories beneath
`C:\ProgramData` and retain their files and result receipts:

| Script | Fresh fixture prefix | Effects |
|---|---|---|
| `scripts/Test-K98UpdateCustodyNative.ps1` | `K98-Updater-Rehearsal-` | Synthetic file creation and replacement; application-owner, inheritance, metadata, content and write-permission refusal checks. No SQL, Git, task or Bot calls. |
| `scripts/Test-K98ReadinessCloseoutNative.ps1` | `K98-Readiness-Rehearsal-` | Synthetic immutable intent and atomic closeout records; overwrite and untrusted-write refusal. No SQL, task or process calls. |
| `scripts/Test-K98ReleaseNative.ps1` | `K98ReleaseRehearsal-` | Protected control files, one owned PowerShell child that exits zero, and one disabled scratch scheduled task with the same GUID name. The scratch task is unregistered in finally; it is never started. |

The first two scripts authenticate the current library's LF-normalized bytes before
loading it: SHA256
`03a00255e5cd53cffb900ba2ebb2fcb59935029d16eac7f819ff4b188520f0ab`.
The library itself is unchanged. Old script pins referred to previous libraries
and would refuse before fixture creation. This correction does not change the
historical incident-specific readiness-closeout package or its authority.

Review and bind the exact committed script hashes before execution. Preserve all
receipts, including failures; never alter ancestor permissions or retry an unknown
effect blindly. Record actual host, user/owner SID, elevation, interpreter and
fixture paths. No production installation, preparation, SQL write, Bot start or
cleanup is included in this rehearsal scope.

These three scripts provide partial U05/U11 evidence only. They do not establish
the complete U05 adversarial filesystem matrix, U06 contract compatibility or
U07-U13 actual combined drain/SQL/source/seed/start interruption and resume.
Those require a separately bound full fixture and genuine stage evidence. The
existing N00-N16 SQL results and mocked orchestration are retained as separate
evidence and must not be relabelled as end-to-end qualification.
