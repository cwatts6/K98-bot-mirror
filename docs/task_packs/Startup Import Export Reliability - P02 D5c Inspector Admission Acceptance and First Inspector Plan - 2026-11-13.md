# P02 D5c inspector admission acceptance and first inspector plan

The four-record admission is accepted. D5 remains qualification work; no
production deployment or runtime correction is included.

## Receipt acceptance

Receipt `d5c-inspector-admission-result-4d4bd51105114ed8a8a630569398d915.json`
has SHA256 `ea045c383175d845ad41b049cf5ac85dba30704140fa46b921bc9cb12959163b`.
Independent adjudication verified the exact four rows before commit and after
acknowledged commit, existing seven-row fingerprint, original history,
permissions, completed work, candidate definitions, resources and both SQL
connection closures. It used 44 commands and returned 121 rows. The acceptance
record is `d5c-inspector-admission-acceptance.json` in `.codex_artifacts/p025`.

Full host elapsed time was 1.1434976 seconds, charged as two seconds. There are
1,359 native seconds remaining, including the protected 1,000-second later-phase
reserve; 50 Windows-test seconds remain. Eleven of 64 synthetic rows are now
committed. The 21-input allowance remains consumed. Admission must not repeat.

## Next packet: one full Stats inspector, global owner first

`run_p02_d5c_stats_inspector_owner.ps1` and its pinned execution packet run one
fresh, isolated Python actor on the existing disposable database. The actor
acquires the existing global application lock on its own transaction, invokes
the actual `StatsImportOutcomeDAL.inspect` once for the labelled legacy test
preparation, and requires `ImportExecutionActive` with the exact active-producer
message. It then verifies acknowledged reader cleanup, proves the owner still
holds its lock, releases only that owned transaction and closes the owner.
The independent outer observer checks that the work and actor SQL sessions are
absent. An unexpected result or uncertain cleanup fails the packet, without
replay or forced session termination.

This is one named C01 case. It does not establish other inspector routes,
reverse arrival orders, fresh-after-release observations or action eligibility.
Missing execution history must never be represented as successful execution.

All application modules are unchanged, bundled in full and hash pinned. The
actor permits only the exact identity, lock, snapshot and three data-read SQL
shapes required by this call. It invokes no producer, parser, import, report,
maintenance, backup, provider request or recovery mutation. It adds no rows and
changes no permissions or settings. The original database remains protected.

The preservation observation retains the original permission fingerprint and
adds the seven-row fingerprint, all four new row values and temporary-account
absence. The exact proposal remains independently hash pinned. Its duplicate
row array is omitted from the compact manifest to retain the existing 128 KiB
manifest bound. The proposal and SQL predicates preserve the complete values.

Command reservation remains 48: 22 outer metadata commands, six outer control
operations and 20 actor operations. The previous closure setup is combined
with its existing identity query without removing either operation. All SQL
texts and observations otherwise retain their established bounds. The actor
expects nine SQL calls and six returned rows, including lock acknowledgements;
the full actual-source inert test verifies these counts. The total 2,048-row,
1 MiB receipt, fixed resources, 60-second packet, source expansion and process
deadlines remain unchanged. No new input is read or consumed.

## Offline preparation and review

Ten isolated Python tests passed, executing the full bundled inspector against
inert connections. They cover expected refusal, failed acquisition/identity,
incorrect account, unexpected availability, owner loss, cleanup uncertainty,
native error preservation and rejection of unlisted SQL. The initial fake
cursor omitted column metadata for an empty SELECT; the test double was
corrected to match the driver contract. No production code changed.

237 Windows PowerShell 5.1 checks passed for parsing, remoted result shapes,
negative evidence, exact pins, preservation, custody, deadlines and budgets.
Preparation also corrected an inherited proposal filename and duplicate
manifest data before native handoff. No native attempt has occurred.

The first frozen review (range ending `50188745ad34c489bedcf8e0b9c121f31a1c6a49`,
scan `575ed4ee-454a-4803-ac30-d927767f717f`) found no security candidate but
blocked native handoff: ordinary SQL text equality can ignore trailing spaces
and some case changes. That original packet remains preserved in its Git tree.
The correction fingerprints every non-null text column using SHA-256 over its
stored bytes: ASCII for the fixed varchar constants, UTF-16LE for nvarchar,
matching the authoritative schema. Null and typed nontext predicates stay
unchanged. Two regression tests verify all text predicates against the proposal
and reject case/padding changes. The resulting manifest is 130,048 bytes;
command, row and size limits are unchanged. The actor itself is unchanged.

Security routing: Changes review of this packet's immutable focused Git range,
Deep off. The packet touches SQL observation, file staging and process custody;
review must complete before handoff. Bot source is bundled unchanged and SQL
schema/source pins are verified against the authoritative SQL repository.
No SQL repository patch is included.

Full pytest, broad smoke imports and command registration are deferred because
this is an isolated qualification harness, not an application deployment;
importing application startup is outside this pass. Test selection is evaluated
for explicit packet paths. Repository validators are run where compatible with
the isolated interpreter and any limitations are recorded separately.

## Remaining work

D5a and D5b remain accepted. D5c still has partial inspector coverage (C01),
season/weight consistency (C04), remaining queue/pool observations (C05),
action/caller checks (C06) and broader caller/custody evidence (C09). The named
passive status-card, health Refresh and report checks are reconciled separately.
D5d has its accepted 38-case offline pass but physical failure/restart coverage
remains open. D5e and D5f remain open. No percentage of deployment readiness is
claimed from the number of checks. Existing consumed one-attempt allowances
remain consumed; this packet is a distinct check within current authorization.
