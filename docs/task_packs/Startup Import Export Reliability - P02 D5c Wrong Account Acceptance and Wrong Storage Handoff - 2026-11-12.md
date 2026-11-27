# P02 D5c wrong-account acceptance and wrong-storage handoff

Receipt `d5c-scope-refusal-result-9f88c6bc1768467e934f72d17cd05b19.json` matches
SHA256 `f0718e9818b7296038c86b436b97fe16e87ff1a9462e87339a42c97b217df15a`.
Saved-file adjudication accepted every expected observation, source/manifest and
lineage pin, exact refusal arguments, resource check and physical cleanup.
The receipt contains 44 command units, 107 rows and 24,399 bytes, with no errors.

The actual target reader used the existing administrator identity on the exact
disposable copy. One factory call and the first preparation fetch produced no
data for `d5c_foreign_account_20261112` with the correct storage owner. The actual
DAL raised SourceConflict. No target payload, downstream resource/stream read,
fallback, second call or mutation occurred. Actor accounting is eleven units,
three statements and one identity row.

Administrator evidence independently correlates actor PID 3172, SQL session 55,
the exact login SID and connection birth, and application
`P02D5cScope_192a04a54d874a06a5c4aa5e2a83a7e2`. Rollback, isolation restoration,
cursor/connection closure and process exit are acknowledged. Both administrator
connections closed and no work-birth or actor-application session remains.
The temporary restricted account remains absent. All seven fixture rows and
protected metadata, permissions, original failures and completed work remain
unchanged.

Host elapsed **1.2784727 seconds** debits two: **1,404 native seconds and
50 Windows-test seconds remain; 21 inputs consumed, zero new inputs**. The
WrongAccount attempt is consumed and cannot repeat. Saved acceptance:
`.codex_artifacts/p025/d5c-scope-wrongaccount-acceptance.json`.

## Next already-authorized step

Use the unchanged reviewed packet with **Stage WrongStorage**, once, in the same
elevated Windows PowerShell 5.1 console holding `$global:D5bReportSession`.
Its host intent is absent at handoff. Guest admission requires the verified first
case and unused WrongStorage allowance. It uses the correct account and the
deliberately wrong storage owner `d5c_foreign_storage_20261112`, requiring the same
first-fetch refusal and cleanup without data or permission changes.

- Wrapper SHA256: `27c500106ba963b16e9bec663d48a6611c0e19c771359cf266dbf3ffc29f8afb`.
- Manifest SHA256: `2270541476c3a6b1b1c0f010e04caf550a56d46cd01166ab37f5f8f26abb99d2`.
- Existing sealed Changes review: `19434870-53fe-413d-806c-3a1967704910`.
- Maximum 60 host seconds, 48 units, 142 planned rows and all existing caps.
- Return summary, ReceiptPath and full HostPacketElapsedSeconds. Stop on failure
  without retry; cancel/report a hang before 60 seconds and keep the console open.

Preserve the 1,000-second later-phase reserve, original evidence and every prior
no-retry boundary. The fixed 1,286-second packet lower bound remains conservative;
the exact current balance is 1,404. No new account, fixture, producer, import,
report, maintenance, backup, provider request, isolation or permission change.

This turn adjudicates saved evidence and records the handoff only. Executable
bytes remain identical to the completed review and tests. No fresh native test,
application/startup import or security discovery applies. Documentation checks
and explicit test selection are recorded separately; no deployment is implied.
D5c and later D5 slices remain open.

Validation passed: saved-receipt adjudication; architecture (52 Python files),
deferred documentation (91 files), and security routing (zero warnings/errors).
The explicit selector recommended smoke imports, command registration and four
release/schema/permission-repair suites. These are skipped because this change
only records accepted evidence and the unchanged handoff: no application,
release identity, schema, registration or permission-repair code changed.
