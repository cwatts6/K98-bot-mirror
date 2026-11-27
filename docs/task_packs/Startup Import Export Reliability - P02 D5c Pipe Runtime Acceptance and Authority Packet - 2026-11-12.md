# P02 D5c pipe runtime acceptance and authority scheduling packet

## Accepted prerequisite and authorization

The eight existing Windows dependency files passed fixed-path native inventory
adjudication. Receipt `196b659ae9114a299ae6e9420f363b76` has SHA256
`17523613DF2679B6C371DFD8C6967A1B9416BE1807E57FBFE09EFD4C4292F738`.
The full host 1.6050238 seconds consumes two, leaving **1,447 native seconds**;
six seconds of the D5c.4 60-second allocation are consumed. All 21 inputs remain
consumed. No new input, replay, maintenance request/retry or production change.

This implements the already-approved C08 unique local Windows pipe test with an
inert dispatcher. It does not start the authority entry point/service, deploy a
production identity, connect to a provider, install dependencies, grant access,
change SQL/VM settings or consume retained inputs. One fresh test folder on Q:
holds the runner, bundled source, stdout/stderr and an empty fixture directory.
Existing production directories and files are not mutation targets.

## Concrete packet and case order

`scripts/run_p02_d5c_authority_pipe.ps1` borrows the existing exact
`$global:D5bReportSession`, pins the immutable manifest and lineage, checks the
unchanged VM/resources/database/permissions/work records and starts one hidden,
isolated base Python 3.11.9 process. No venv startup, site initialization or `.pth`
execution occurs (`-I -S -B`). Six exact existing pywin32 binaries are hashed on
the guest, then loaded by exact file path; the observed runtime bindings and ten
complete source modules are hash-pinned. The existing pywintypes shim's inspected
ExtensionFileLoader mechanism is used directly for its exact DLL, without a
search/import of the broader site-packages environment. Missing/unloadable files
stop this packet; no installation or fallback follows.

The source modules retain their complete bytes: execution host, process identity,
protocol, snapshot-store class definitions, authority launcher, observation
scheduler, proof-progress definitions, SQL lifecycle/custody/observation helpers.
The launcher module is imported by name, not executed as `__main__`. The two
SQL-DAL dependencies supply exception types only; `_conn`/pyodbc connect refuse.
The inert dispatcher accepts only the fixed labelled messages below. Python
audit containment refuses network/process creation and filesystem mutations;
the selected native APIs create only this test's Windows pipe/event handles.

1. Create a unique `\\.\pipe\K98Export-<uuid>` using the unchanged private-pipe
   creator and its bounded four-instance transport. The current SID and fixture
   PID are the exact local peer. This is a labelled transport adapter, not a
   production Bot-token/profile or shared-account supervisor qualification.
2. Send one deliberately wrong-expected-PID observation. The real peer check
   must refuse before any dispatcher entry or observation admission. Confirm the
   rejected server handle closed and exactly one expected connection diagnostic.
3. Hold one actual scheduler observation, queue one second observation and require
   the third to return `authority_busy`, without calling its dispatcher body.
4. While one is active and one waits, require an inert mutation message and a
   configuration-inspection message to finish on the serial server thread.
   Configuration inspection must not be moved to the observation worker.
5. Release the held observation, verify both original replies in order, send one
   inert stop message and join/drain the server and observation worker.
6. Verify all eight created server handles and seven client handles are closed,
   zero retained I/O/SQL custody, and exact pipe-name absence from Windows.
   The outer observer independently confirms normal exit of the retained process
   handle/birth, an empty fixture directory, unchanged SQL metadata and physical
   SQL-session absence. The process's exit independently ends all its OS handles;
   the pipe-name absence result itself comes from the actor, not a second probe.

Seven fixed requests are planned. A failure before normal stop may send only an
inert cleanup-stop message; it never repeats an observation/mutation workload.
Connection acquisition waits are bounded and occur before a message is sent.
No lost-reply/death schedule is included; those remain D5d. C08 broader caller
policy, C09 identity rights, C10 disabled-isolation and C11 cross-process cases
are not silently closed by this transport fixture.

## Bounds and custody

The exact 30 read-only SQL metadata statements and expected metadata are
unchanged from accepted file-caller qualification. Reserve six SQL connection/
cleanup units plus eight pipe/control units (seven requests and physical owner
join), **44 total**, below 48. One cleanup-stop can only replace an unexecuted
normal stop; it is not an eighth dispatched request. Per-result 512 rows, total
2,048, planned maximum 171, 1 MiB receipt and three-second SQL observation
timeouts remain unchanged. Two SQL connections are sequential; no SQL child in
Python, and the closure observer is excluded while a process/work owner is
unconfirmed. No business SQL, backup dispatch, reports or retained-data mutation.

The actor phase budget is 12 seconds, held observation at most eight seconds,
client I/O/connection acquisition one second, waits/joins two seconds. The outer
guest process limit is 15 seconds with at most three seconds to observe exit of
only its retained owned process after termination. Original guest work/cleanup
ceilings remain 30/42 seconds. Host runner has 45 seconds plus a reduced five-
second stop observation, with a **53-second packet/manual ceiling**, within the
54 Windows seconds remaining. Debit complete host elapsed time rounded up, with
no reset between packets. Stop later Windows cases if their allocation cannot
fit. All disks retain 8 GiB, log below 70%, version store below 512 MiB; VM remains
fixed 8 GiB/four CPUs/zero NIC. No stronger post-start host-memory floor is added.

Corrected `Finish-Runner` ownership is carried forward exactly: unresolved
remote jobs cross the shared control object and retain their owning runner in
the outer console; every host timeout also retains its runner before EndStop.
No forced Stop-Job/Remove-PSSession or foreign process/handle termination. Guest
uncertain process/connection ownership remains in the authenticated session and
blocks the observer/next case. A create-new intent prevents a second invocation.
No automatic retry, ledger reset, evidence deletion or fallback credential.

## Offline preparation and evidence preservation

Six Python tests passed using the complete selected scheduling source and an
in-memory transport: saturation and reply ordering, wrong authentication,
serial configuration/control, exact source/native bindings, compression limits,
external-effect refusal and denied SQL boundaries. They are offline scheduling
evidence, not Windows transport proof. 102 PowerShell 5.1 checks passed: accepted
and remoted receipt validation, 26 malformed variants, unchanged SQL/metadata
helpers, command ledger, corrected outer ownership and closure gates.

The first packet builder stopped at 133,292 bytes above the unchanged 128 KiB
manifest cap. Its source is preserved as `prepare_d5c_authority_pipe_first.py`.
Removing only the unused duplicate `history.source` reduced the manifest to
122,870 bytes. The immutable history already exists on both hosts and its exact
name/hash checks remain; earlier manifests retain the full original bytes.
No row/statement limit, source image, expected state or runtime gate was removed.
The 180,113-byte expanded source envelope remains below 256 KiB and its compressed
envelope below 64 KiB. Runner/stdout/stderr remain capped at 64 KiB.

The initial wrapper draft's separate Add-Type pipe probe was removed before
handoff to avoid compiler/temp-file effects outside the owned test folder.
The actor's real native absence check plus independent retained-process exit
provide distinct evidence; no second namespace probe is claimed. The first
wrapper, manifest and 101-check log remain preserved. Production code is unchanged.

Ruff and focused architecture/deferred/test-selector/security-routing checks
apply. The selector's full bot suite, smoke imports, registration and release
tests are skipped with rationale: this adds only isolated qualification harnesses
and docs; no application, Discord, SQL or release path changes. No old rehearsal,
opt-in native test, live import or process-death test is run during preparation.

Security decision: **Changes**, Deep off, immutable base
`045d08245f7e01dad31d82d7d30b624501cb6d2f` and a review-only head containing four
new harness/test files plus three evidence docs. Review covers exact dependency
loading, pipe identity/ACL, inert dispatch, containment, budgets and custody.
All native activity awaits completed review and a hash-pinned console handoff.

## Remaining acceptance boundary

D5a/b are accepted. This C08 packet is prepared, not native-qualified. D5c's
remaining SQL variants and explicit rights/isolation gaps, C11 cross-process,
D5d failure/restart, D5e balanced cost and D5f final obligation reconciliation
remain. D6 production release and D7/P05 live acceptance remain separate.

## Reviewed native handoff ready

Changes review `d8991e08-d28d-463b-9128-224bb9a9e8f4` completed with seven paths
covered, zero security findings and no concrete handoff blocker. Independent
review covered all four new source/test files and their actual supporting native
transport/scheduling functions. Canonical sealed results were read back. Range:
`045d08245f7e01dad31d82d7d30b624501cb6d2f` to
`fb82c738e977734bdaa20aaf1e46b0628f2e7303`. Measured usage: 3,062,507 total tokens,
3,045,504 cached input tokens. The final six Python tests, 102 PowerShell checks,
Ruff, architecture/deferred/routing and immutable whitespace checks passed.

All seven working files matched the review snapshot before this status appendix.
All ten source images, current actor bytes, receipt lineage and original history
hashes matched; the native intent is absent. Normal HEAD/index and unrelated
changes remain untouched. Final manifest is 122,916 bytes after reconciling its
descriptive deadline and command ledger; the stricter 128 KiB cap is unchanged.
Preparation acceptance: `.codex_artifacts/p025/d5c-authority-pipe-preparation-acceptance.json`.

Ready for one invocation in the existing elevated console:

- Script SHA256: `713531372C6B5EF23ECDADDFAAE7F3F276D5C1C1FD92683EA18A10C3941D3EC5`.
- Manifest SHA256: `4668851a0786d70a9fef5b47f758380e10c1813dc6d8213c607c327e9e97695e`.
- Full host time must be reported and charged rounded up. Stop on any error or
  incomplete result, without retry, installation, permission change or deletion.
  Cancel/report a hang before 53 seconds; keep the console open for adjudication.

No native pipe work has run. **1,447 native seconds**, **54 Windows seconds**,
**21 inputs consumed**, **zero maintenance retries**. This evidence-only appendix
does not change execution; no repeated runtime/security scan is required.

## Native acceptance, 12 November 2026

The subsequent receipt `d5c-authority-pipe-result-316b355fc64441f1877e051106a07939.json`
matches SHA256 `B97242AD2DE507B005225A5BC92B6DD118CFEE26DF56C50F98E6F1EEA9AA3FBC`.
Independent adjudication accepts the bounded private-pipe fixture: the wrong peer
was refused before admission, six authenticated messages followed the expected
queue/control order, and eight server handles and seven client handles closed.
The worker drained, its owned process exited normally, its pipe was absent and
its test folder remained empty. All 30 metadata observations, original history,
completed maintenance and connection cleanup checks passed, with 44 command units
and 109 rows. Ten unchanged source modules and six installed binary pins match.

Full host elapsed time 1.8017681 seconds debits two seconds. The current balance
is **1,445 native seconds, 52 of 60 Windows-test seconds remaining, 21 inputs
consumed, no maintenance retry**. The acceptance is saved separately in
`.codex_artifacts/p025/d5c-authority-pipe-acceptance.json`. This does not prove
production identity provisioning, a cross-process supervisor, lost replies or
process death; those obligations remain distinct. No production change occurred.
