# P02 D5c Windows file acceptance and actual caller packet

## Current evidence and authorized scope

The Windows file-guard foundation passed independent local receipt adjudication.
Receipt `6d714508e6524b8bbcfc8bd3724ffc2b` has SHA256
`B934BF6F5BF93C8F3C576FD8B4168720D22A803292AAAAC09D4265D792D52127`.
Both writer orders, aliases, foreign sentinel preservation, normal process exit,
physical cleanup and unchanged full completed work/cache/protected metadata pass.
This is one-process, independent-registry native evidence. It does not claim
cross-process or whole-C11 completion. The original maintenance error and all
earlier receipts remain immutable.

**1,451 native seconds remain; 21 inputs are consumed; no maintenance retry is
available.** D5c Windows work has consumed two of its allocated 60 seconds.
D5a/b are accepted; D5c/d/e/f remain open. D6 production release and D7/P05 live
acceptance remain separate.

## Architecture and source boundary

The next packet is within the approved D5c actual file-caller scope. It runs one
isolated Python process in one new test directory under the existing Q: volume.
Ten complete current source modules are hash-pinned: `core.file_lock`,
`core.operation_evidence`, `core.operation_timing`, `core.owned_work`, `file_utils`,
`player_stats_cache`, `services.player_stats_startup`, `ark.team_state`,
`ark.state.ark_state` and `services.tracked_view_store`. No source lines are
rewritten, extracted or installed in application directories.

The test adapter replaces data acquisition with one labelled one-row Python
dictionary per cache route and disables the secondary last-KVK producer. All SQL
connection, provider and producer entrypoints exposed by import adapters refuse
on use. Imported producer decorators produce refusing wrappers; they do not
admit work or return an unguarded producer. Only the synchronous cache file-write
critical sections are exercised, not their enclosing live producer/startup flows.
Actual file guards, atomic write/retry implementations, startup verification,
Ark save functions and tracked-view lock/drain/write code stay unchanged.

The constants adapter points every data location, including the import-time
offload-registry read, into the fresh fixture directory. No real application
configuration, SQL/provider module, log handler or retained input is loaded.
The one standard-library async loop initializes its local wakeup mechanism before
the audit barrier; it is subsequently used by the real owned-thread helper and
closed with its executor drained. No application network client is permitted.
The audit barrier refuses network/process creation and filesystem mutation
outside the owned fixture, and records any attempted violation even if a caller
catches it. It validates recursive staging deletion before traversal and each
underlying mutation. No link creation, permission change or unowned cleanup.

## Eight fixed cases

1. Ordinary cache persistence: one inert source request, one actual guarded
   atomic write, exact output readback.
2. Guided cache persistence: one `refresh=False` inert request, existing prior
   bytes, actual staging/backup/publication/readback/owned-staging cleanup and
   receipt digest. No producer or fallback invocation.
3. Startup decode ordering: actual `_verify_completion` captures bytes, releases
   its lock, then a separately owned successor enters during the decode callback.
   The returned digest must certify the captured generation, not the successor.
4. Malformed startup bytes: retain the exact invalid fixture, refuse readback,
   close the guard, then demonstrate a separately scheduled successor can enter.
5. Ark team save: actual save and one atomic write to its test path.
6. Ark state save: actual message/reminder saves, each with its own guard and
   exact expected small JSON outcome.
7. Tracked-view save/read: actual async `locked`, `write`, `snapshot` and owned
   thread drain with one labelled test entry.
8. Path-only release: actual compatibility function must refuse and preserve the
   labelled foreign fixture sentinel byte-for-byte.

For each of the six ordinary/guided/Ark/tracked atomic writes, an observing adapter
first proves the caller's registry admission and requires a second unchanged
guard module with independent registry to be refused by the physical Windows
object. It then delegates to the unchanged atomic writer. Startup's successor
write is separately counted once. Neither guard implementation is mocked in the
native packet. No failure/uncertain-close injection or work replay is included;
those remain D5d. Cross-process contention remains an explicit open C11 row.

## Bounds and evidence

Use only the exact already-authenticated PowerShell session, isolated VM,
disposable database, qualification volume and verified base Python 3.11.9.
Runtime/source/manifest/history/identity/resource checks precede the actor.
The inherited SQL ledger is unchanged: 30 read-only metadata statements plus
six reserved connection/cancellation units, at most 171 rows, within the original
48-unit, 512-per-result and 2,048-total caps. Python adds zero SQL commands.
Before/after source definitions, completed claims, first error, permissions,
ownership, backup demand, physical statistics and original protection must match.
The independent SQL closure observer follows acknowledged actor/work cleanup.

The source envelope is compressed only for bounded transport, not executed from
an unverified archive. Its exact hash is pinned; the actor rejects trailing data,
incomplete compressed streams, expanded content over 256 KiB, wrong expanded hash,
any module-set difference or source hash mismatch before compilation. Each staged
runner/envelope/output remains at most 64 KiB and the whole host manifest remains
within its unchanged 128-KiB cap. The 190,620-byte expanded module map exists only
in memory. Historical descriptive manifest fields not consumed by the wrapper
were omitted; operational statements, gates and old immutable manifests remain.

At completion, exactly seven allowlisted fixture files remain, each at most
64 KiB; no owned lock or staging directory may remain. The wrapper independently
checks names, ordinary-file/reparse status, lengths and SHA256 after normal
exact-process exit. Foreign sentinel remains evidence, never cleanup material.
Source/evidence staging and both process streams remain in the run directory.

Actor work limit 12 seconds; process limit 15; total work/cleanup 30/42;
outer watchdog 45 plus 10; manual stop before 60. Unknown process custody remains
owned and blocks dependent work. Forced termination is failure. The one-MiB
receipt, original 1,800-second aggregate, D5c allocations, disk/log/version-store
reserves, fixed 8-GiB/4-CPU VM and zero adapters remain unchanged. Debit full host
elapsed time rounded up; no new input, import/report/maintenance or backup work.

## Offline validation and review

Six isolated Python tests passed. The integration case runs all eight actual
caller routes with fake lock and drain boundaries; it does not claim native
Windows or thread proof. A deliberately removed actual caller guard is detected.
Other cases reject source/hash/framing/size changes, mutation outside the fixture,
network/process effects and attempted producer/database access.

The first pass found that a fixture producer-decorator stub refused at import,
before any test work. First runner/tests/log are retained as
`d5c-file-callers-first.py`, `d5c-file-callers-first-tests.py` and
`d5c-file-callers-offline-python.txt`. The adapter now allows declaration while
returning an always-refusing producer wrapper; no production guard was relaxed.
The corrected final six tests pass. Formatting/lint fixes also passed Ruff.

104 offline PowerShell 5.1 checks pass: complete parsing, unchanged inherited
safety functions/SQL ledger, exact source/manifest caps and pins, actual JSON and
remoting shapes, missing/changed cases, cleanup/effect counters, path traversal,
duplicate files, wrong digest/length/type and observer custody admission.

Security routing is **Changes**, Deep off, exact Bot test packet/test/documentation
delta from `05133c8876435722ae95bec8aca0284978f08962`. File staging, source transport,
owned processes and receipt custody require review before native handoff. No SQL
repository change; the already-adjudicated fixed SQL statements are identical.
Architecture (two Python files), deferred-item validation (three documents),
security routing (zero errors/warnings) and explicit-path test selection passed.
Immutable whitespace and the completed Changes review are pending. Full application startup, whole pytest/native suites,
Discord registration and deployment checks are skipped because the packet is
isolated file qualification with no production runtime change. No new refactor
or deferred optimisation is warranted; all unproven qualification remains open.

## After this packet

Adjudicate the native receipt before further work. Continue the separate native
cross-process and C08 authority cases; do not infer them from these file callers.
C01 full inspectors/account variants, C04-C06 committed fixture/CAS and native
restricted-rights/disabled-isolation gaps remain. The latter scope exceptions
still require the concrete reserved approvals. D5d/e/f and production release
cannot be marked complete from this packet.

## Reviewed caller handoff ready

Changes review `9d6a8f11-163b-480f-b137-a8c9de36fbf8` completed with zero findings
and all seven changed paths covered. Independent complete source/test review
found no concrete handoff blocker. Immutable range
`05133c8876435722ae95bec8aca0284978f08962` to
`49b9483352046cac7d1ae6b1b15e80acb00b1ba7`; canonical sealed results read back.
Measured usage: 2,333,683 total tokens, 2,321,408 cached input tokens. Whitespace
passed. All seven working files matched that snapshot, all ten bundled source
hashes matched current unchanged source, and the execution intent was absent.
The normal branch/index and unrelated changes remain untouched.

One native invocation is ready under existing approval, using the same elevated
console and `$global:D5bReportSession`:

- Script SHA256: `26A7AA471E4761410A28393C1C19BF54E8DA9FBC21B96D64888EFAAE4019A62B`.
- Manifest SHA256: `e80f459938b7bbacb338f392d8547752dc2523c4e12a4b9b27a5042411865fcb`.

Keep the console open; stop on error/incomplete output, do not retry or delete
evidence, cancel/report a hang before 60 seconds, and report complete host time.
No native caller execution has occurred yet. Balance **1,451 native seconds**,
**21 inputs consumed**, **zero maintenance retries**. This status appendix adds
no executable behavior; no repeated security scan or runtime test is required.

## Native caller acceptance

Receipt `d5c-file-callers-result-f689b965b2594bf1947e2fcc66e6594e.json`
has verified SHA256 `4D707D332E754C771B5D70C5330CC584104EAD495786B10910F7F390F03C5768`.
Independent adjudication accepts all eight caller critical-section cases. The
ordinary/guided cache, Ark team/state and tracked-view writers encountered real
Windows contention while protected. Startup decoded the captured bytes after
releasing protection; its malformed-data case preserved bytes and allowed a
successor only after cleanup. Path-only release preserved the foreign lock file.

All ten bundled source hashes still match source. Six protected writes and one
decode-successor write were observed; the seven final files independently match
the actor's sizes/hashes. The process exited normally, custody is empty, both SQL
connections closed, and the captured session birth is absent. The complete work
ledger, cached execution records, original database protection, ownership,
permissions, definitions, statistics and backup metadata remained unchanged.

The host time of 1.9503936 seconds consumes two seconds: **1,449 native seconds
remain**, with four seconds consumed from the 60-second Windows allocation.
The 21-input allowance remains consumed and no maintenance retry is available.
Acceptance is limited to actual file critical sections with inert data builders
and denied external producers, not complete live startup/import flows.
Cross-process qualification and D5d crash/uncertain-close cases remain open.
Machine-readable acceptance: `.codex_artifacts/p025/d5c-file-callers-acceptance.json`.
This adjudication updates evidence only; it introduces no runtime correction.
