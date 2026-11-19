# P02 D5c fresh inspector acceptance and reader-first plan

## Accepted fresh read

Receipt `d5c-stats-fresh-result-583d902088dd401094662e98d97e554b.json`, SHA256
`ee8e94d60355e75739a0542dc4ef7bcf6ba3cb853c7390d579715d98a3a19b97`, is accepted.
The actual full Stats inspector returned the exact approved preparation, no
execution or resource records, and an honest hold because execution evidence
is absent. All three lock-availability observations were one. The raw token
document was independently checked before driver values were normalized.
Rollback, isolation restoration, process exit and independent SQL connection
absence were confirmed. Both preservation observations passed, including all
eleven test rows, original history, completed work, permissions, ownership,
candidate definitions, statistics and absence of the removed test accounts.

The receipt recorded 43 operations and 107 returned rows, no errors. Host elapsed
1.1939754 seconds is charged as two seconds. The acceptance record is
`d5c-stats-fresh-acceptance.json`. Remaining native time is 1,353 seconds including
the protected 1,000-second later-phase reserve; Windows-test time is 50 seconds.
Eleven of 64 synthetic rows and all 21 retained inputs remain consumed.

## Next distinct schedule

Run the unchanged actual `StatsImportOutcomeDAL.inspect` once on the same labelled
preparation. The managed snapshot reader starts first and fetches its exact
preparation. Only after that acknowledged fetch does the test connection wrapper
open a separate connection and acquire the existing global lock. The real
inspector then continues its remaining queries and must refuse with the exact
`ImportExecutionActive` result before selecting an action.

The scheduling hook is confined to the qualification driver wrapper. It neither
replaces the inspector nor alters its SQL, guards or snapshot profile. It requires
the exact preparation ID and an established snapshot, permits one holder only,
and verifies distinct SQL session births. The holder must remain exclusive after
reader rollback, isolation restoration and physical closure. Only then may its
owned transaction roll back and close. Uncertain reader cleanup blocks holder
release and fails the packet. The independent observer must confirm session
absence. Monotonic timestamps may be equal at native clock resolution; actual
fetch/acquisition acknowledgements and control flow establish the order.

This is a new reader-first ordering, not a repeat of either accepted owner-first
case or the fresh read. It invokes no recovery action. No new rows, inputs,
imports, reports, maintenance, backup dispatch, provider requests, permissions,
isolation settings or VM settings are included.

## Bounds and exact preservation

Reserve 47 client operations: 21 metadata, six outer control/cleanup operations,
20 actor operations including nine SQL statements and six returned rows.
The unchanged caps are 48 operations, 2,048 rows and 1 MiB receipt. Planned rows
are 111. The execution manifest is 131,048 bytes under the 131,072-byte cap.
The whole packet has a 60-second ceiling, a 20-second actor watchdog, and the
existing bounded outer wait/cancellation and custody rules. No retry is included.

The fresh packet's 21 observations are retained. Its two composite permission
observations preserve all byte-exact text fingerprints and independently require
zero other user sessions on the disposable copy. Original receipt/source pins,
eleven exact fixture rows, SQL schema pins and seventeen runtime module pins
remain unchanged. Production and the original database are not modified.

## Offline validation and review route

Fourteen isolated Python tests passed with the actual bundled inspector and inert
connections. They exercise real query order, wrong preparation/target, acquisition
refusal, identity/setup failure before holder creation, retained native failure
causes, unknown reader cleanup, lost owner, holder cleanup, SQL allowlist and
source/text fingerprints. 247 Windows PowerShell 5.1 checks passed for parsing,
remoting, evidence ordering, missing/changed evidence, full accounting and pins.

The first draft exceeded the manifest cap by 40 bytes and stopped before manifest
creation. Only its purpose description was shortened. One initial offline test
wrongly expected a holder after earlier reader setup failure; it now requires no
holder and retains the native-cause and uncertain-custody assertions. The failures
are preserved in `d5c-stats-reader-first-global-preparation-failures.json`.
No native attempt occurred and no runtime correction was made.

Route security review to Changes, Deep off, on the immutable seven-file packet:
actor, wrapper, builder, manifest, two tests and this plan. Independent review and
repository architecture, deferred-item, security-routing and explicit test-selector
checks precede the console handoff. Full pytest, application imports, Discord
registration and release checks are skipped for this isolated qualification-only
packet; they would introduce unrelated startup work and are not deployment proof.

## Remaining D5c scope

Seven of twelve named groups are closed: C02 schema, C03 maintenance guards,
C07 attribution, C08 authority channel, C10 isolation, C11 files and C12 passive
presentation. Five remain partial: C01 full inspectors and arrival orders,
C04 season/weight consistency, C05 queue/pool and missing-evidence behavior,
C06 recovery actions including effectful Refresh, and C09 remaining connection
factories and uncertain-cleanup callers. This count is not a time percentage.
D5a and D5b remain accepted; D5d physical-failure coverage, D5e balanced comparisons
and D5f final acceptance remain. D6 production deployment remains separate and
unauthorized. No old consumed attempt is made available by this plan.
