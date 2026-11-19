# P02 D5c approved isolation refusal packet

## Authority and boundary

The operator approved the bounded isolation test on 2026-11-12 after the
configuration acceptance and isolation exception plan. This packet implements
one OFF / refusal / ON cycle on `K98_P025_D5b_20261111` only. Native execution
has not occurred. No additional approval is required for this exact scope.

The original database, seven labelled fixture rows, original failure evidence,
permissions, ownership, production source, VM isolation and resources are preserved.
No input is consumed: the 21-input allowance remains exhausted. No maintenance,
writer or stale-action retry is available. No provider, import, report, backup,
new fixture, grant, user, impersonation or production deployment is included.

Before execution there are **1,421 native seconds and 50 Windows-test seconds**.
This packet has a 60-host-second ceiling, charged by the rounded-up full host
elapsed time. It consumes no Windows-test allocation and preserves the final
1,000 native seconds for later D5 slices.

## Exact files and pins

- `scripts/run_p02_d5c_isolation_off.ps1`: SHA256
  `9e5386046e67abc9314c773b5a0a3473d1e6a5242577241cb841e96e2e5fbfec`.
- `scripts/p02_d5c_isolation_off.py`: SHA256
  `73b9b4bb727dc979d0c640647104bfdb53abcf938b3a2e224a43f3386d097d93`.
- `.codex_artifacts/p025/d5c-isolation-off-execution-packet.json`: SHA256
  `3f01f13e4cbe088d9fb6159065797fc77c2d955ad98824a8fbf0a97a20228e19`.
- Tests: `tests/test_p02_d5c_isolation_off.py` and
  `tests/validate_p02_d5c_isolation_off.ps1`.

The manifest holds the exact actor, 17 unchanged production modules, pinned
runtime files, accepted receipts and fixed SQL. It is below the unchanged
128 KiB manifest limit. The first offline construction exceeded that cap and
stopped before creating the packet; sharing the fixed state query and removing
unused duplicate expectation fields resolved the size issue without raising a
limit. Original construction evidence and earlier native failures are preserved.

## Execution and restoration

The existing elevated PS5.1 console on 9SX2VF4 supplies `$global:D5bReportSession`
(instance `67caa9aa-5bb2-466c-991d-26ab8e1a2fc6`). Host/VM/guest/server/database
identity, history hashes, source hashes, resources and current protected records
are checked first. A create-once host intent prevents a second invocation.

The existing metadata connection switches to master; no additional control
connection is opened. A bounded state query checks stable SNAPSHOT ON, RCSI OFF,
the existing ALTER capability, no other target sessions or user transactions,
zero control transaction count, implicit transactions OFF, and all seven fixture
rows. It records a SHA256 of their complete ordered contents and versions 4/23/20.
Only the fixed disposable database can appear in either setting statement.

OFF runs once with a three-second statement timeout, followed in the same command
by the state query. The result must be stable OFF. One isolated actor then calls
the actual startup prerequisite and actual configuration reader on a single owned
factory connection. The prerequisite must refuse state zero with its exact error;
the native reader must refuse with SQLSTATE 42000 / code 3952 at the schema guard
or first fixture read. Other errors or unexpected success fail the test.

Reader rollback, isolation restoration, physical close, custody and normal process
exit must be acknowledged. Before ON, another state observation independently
requires no other target sessions or transactions and unchanged fixture content.
The planned ON runs at most once, requires stable ON and unchanged RCSI, then the
control connection returns to the copy for protected poststate checks. The work
connection is disposed before a separate observer verifies captured session
absence and actor-application absence, then closes itself.

If OFF is refused, no second OFF occurs. If its completion is uncertain, only a
read-only observation determines the current state. Stable OFF with confirmed
actor cleanup allows the already-planned restoration; stable ON without an OFF
acknowledgment remains a failed test with a confirmed original setting. Transition
states, missing evidence, foreign activity, uncertain actor cleanup or forced
actor exit prohibit ON. ON failure permits one bounded read-only observation,
never another setting command. Original work and restoration errors are retained
separately. Unconfirmed restoration retains guest option custody and blocks later
work. No SQL session kill, forced transaction rollback, single-user setting or VM
restart is present. Only the harness-owned actor can be terminated by its existing
deadline cleanup; that makes the test fail and does not authorize restoration.

## Bounded accounting

| Reservation | Client-command units |
| --- | ---: |
| Existing metadata and physical closure statements | 23 |
| Outer connection opens/closes and first two failure cancellations | 6 |
| Actor open, SQL, transaction/isolation cleanup and close | 12 |
| Control database switches | 2 |
| State before OFF and before restoration | 2 |
| OFF and ON, each including its state observation | 2 |
| One uncertain-restoration observation | 1 |
| Maximum reservation | 48 |

Success uses at most 47 reserved units; the last observation is failure-only.
Additional failure cancellations beyond the first two are explicitly charged,
never refunded, and refused at the 48-unit ceiling. Such failure paths skip actor
or later metadata work. The extracted read primitive is tested at the ceiling.
At most 144 rows are planned; existing 512-per-result and 2,048-total limits remain.
Receipt is at most 1 MiB, each staged source/output 64 KiB, expanded bundle 320 KiB.
Guest admission stops at 30 seconds, cleanup at 42; the host wrapper retains
unconfirmed work rather than declaring closure at its deadline. All full-host
elapsed time, including failures, is charged. Disk reserves remain 8 GiB, log
below 70%, version store below 512 MiB, VM 8 GiB / four CPUs / no adapters.

## Offline validation and review routing

Six isolated Python tests passed against unchanged actual helper code using an
inert driver. They cover both expected native refusal boundaries, wrong identity,
missing/enabled state, wrong native errors, unexpected reader success and cleanup
uncertainty. 305 PowerShell checks passed without invoking the wrapper's native
body. They exercise cycle ordering, one-attempt limits, foreign activity,
uncertain OFF/ON, transitions, reader failure, missing custody, changed fixture
content, incomplete fields, cancellation accounting and the hard command ceiling.

Ruff, architecture validation (44 files), deferred-item validation (69 documents)
and security-routing validation passed. The selector ran for the four code/test
paths. Its broad pytest/import/command-registration/release recommendations are
skipped: this changes isolated qualification tooling only; no application command,
runtime module, release contract, schema fingerprint or permission repair changes.
Direct inert tests cover the new behavior without starting the bot or SQL.

Authoritative SQL object/column definitions were checked in
`C:\K98-bot-SQL-Server`, including the session and stream tables. That repository
has no changes in this packet and needs no separate diff target.

Security routing is **Changes**, Deep off, limited to these four new code/test
files and this plan in an immutable snapshot based on the prior reviewed packet.
SQL settings, subprocess custody and evidence-file handling require this review.
Review completion and frozen-file identity must be recorded before console
handoff. No application/runtime correction or new deferred item is introduced.

The first immutable Changes review (`be90b067-ad4f-42ae-9266-758eb5d94a7e`,
head `5a1ddd243f82749443f51a8d2fe6607a0591dcd1`) completed with no reportable
security findings but found a qualification correctness blocker before native
execution. A child launch or handle-read failure could leave `started=false`
and bypass both restoration and observer admission. Its original bytes and
review remain preserved in that Git snapshot. This is not native failure evidence.

The corrected packet records `launchAttempted` before Start-Process and `started`
immediately after its return. It explicitly rejects a missing or zero process
handle. Both dependent gates treat uncertain launch as unresolved custody.
Inert tests execute the actual launch fragment with injected startup failure,
an unstarted Process object whose handle is unavailable, and normal return;
no child is launched. An initial test assumption that a missing handle raises
proved false in PS5.1, so explicit validation was added. Both initial offline
test failures remain in the tool record. No command allowance changes. The
corrective three-file diff requires completion of its own exact Changes review
before handoff; the unchanged Python actor/manifest retain their original pins.

After the single run, adjudicate the saved receipt, both refusals, complete option
cycle, fixture hash, protected records, resources and physical cleanup before
accepting this case. D5c and the later D5 slices remain open; D6 release and D7 live
acceptance remain separate.
