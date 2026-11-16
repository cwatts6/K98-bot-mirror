# P02 D5c readiness acceptance and global holder packet - 2026-11-12

Status: remaining metadata readiness accepted; next lock-only packet passed
offline checks and completed exact Changes review. D5c/d/e/f remain open.

## Accepted readiness

Receipt `d5c-remaining-readiness-v2-result-c1e726631df445a59b31e9f0a009e60d.json`
matches SHA256 `C822B1CA6CAEBA7AB16A6F1EAB55D46621AA0FF79A6BC1EAF24D9272AB2388DB`.
Independent local adjudication verified all 34 observations and 140 rows,
script/manifest hashes, 30 candidate fingerprints, six maintenance preimages,
permissions, ownership, backup demand, original-database protection, copy files,
paired poststates, session context, resource limits and physical SQL cleanup.
Both connections were disposed; an independent observer found the captured work
session birth absent. Prior accepted receipts and failed V1 hash remain intact.
The acceptance record is `d5c-remaining-readiness-v2-acceptance.json` under p025.

Outer elapsed 0.9680522 seconds debits one, leaving **1,467 native seconds**
(467 of the proposed D5c allocation). **21 inputs remain consumed; no new input**.
Counts cover the same 21 tables; they do not constitute FK dependency closure.
Four named application users lack matching server logins in the copy. Both
existing databases have SNAPSHOT enabled. No authentication, impersonation,
permission mapping, settings change or new database is authorized by these facts.

## Next concrete packet

Case: C01 reader-first global guard foundation plus C07 exact-holder evidence.
Use one owned Python process, one global-holder SQL session, one managed-reader
session and the existing metadata/cleanup observer. No business rows are changed.

1. Verify exact host/VM/session/copy, resources, runtime files, source bundle,
   accepted readiness receipt and existing state preimages.
2. Establish a dedicated holder session identity without acquiring a guard.
3. Enter the unchanged real `recovery_snapshot` helper. Verify SNAPSHOT,
   Shared/Transaction schema guard and absence of the global Session guard.
4. While this reader remains open, acquire the exact global guard Exclusive/
   Session on the holder. A refusal is a failed test, never a retry.
5. Issue one competing global acquisition from the reader. Require exact -1
   and NoLock; only then call unchanged `observe_holder` once using that same
   requester connection. Its diagnostic cursor has a one-second timeout.
6. Require the diagnostic to match the known holder and requester session birth
   and connection identity, with SESSION/X ownership. Missing, ambiguous or
   denied metadata fails the case without guessed attribution. Keep the original
   -1 refusal primary and any diagnostic notes separate.
7. Require managed reader rollback, isolation restoration and physical close.
   Then release the owned global guard once and close the holder. Any uncertain
   reader cleanup stops the explicit release schedule; only owned connection
   cleanup remains. No release/close replay is permitted after uncertainty.
8. Join the owned process, require its reported PID to match the owned handle,
   verify protected poststates and independently require all sessions with the
   unique child application identity absent. Preserve stdout/stderr and receipt.

This does not qualify producer business work, actual maintenance-child overlap,
full inspector variants, account locks, the reverse global arrival order or all
C07 refusal cases. Those remain explicit rows, not inferred from this foundation.
It grants no recovery or mutation authority from an observation.

## Limits, source authority and implementation

The runner reuses the reviewed schema-order wrapper/process custody and six
unchanged source modules. Add only the unchanged
`services/sql_lock_holder_diagnostics.py` source to the pinned bundle. It imports
through an inert services namespace, not the application initializer. Its exact
short resource is supported; long account-name attribution is not substituted.
Authoritative `dbo.usp_RunMaintenance` and the existing holder diagnostic define
the global resource and ownership contracts; neither file is modified.

Same 24 wrapper metadata statements and preimages. Reserve the existing 24 child
command units and 12 rows before launch: total command allocation remains 48.
Expected child work is nine SQL statements/eight rows; original child maxima
12 statements/12 rows remain. One reader factory call, no alternate credentials,
pooling, .pth/site processing or network adapter. Direct verified Python 3.11.9
and existing pyodbc 5.2.0 only. One-MiB receipt, 64-KiB child streams, three-second
normal SQL/one-second holder diagnosis, zero lock wait, 20-second child watchdog,
25-second parent wait and bounded physical join remain unchanged. Manual stop
is before 60 seconds; full elapsed time is charged, including failures/cleanup.

Original data, maintenance claims, first error 15247, failures and consumed input
allowance remain untouched. No maintenance/report/import/backup job, new demand,
fixture row, permission/isolation change, production correction or deployment.
The abandoned unexecuted two-reader draft was retained under p025; this packet
uses one reader to keep the existing child allocation unchanged.

## Offline checks and review route

Six isolated fake-driver regression tests passed, including 12 case variations:
normal identity/holder match with millisecond normalization, wrong identity,
unexpected admission, wrong guard mode, unavailable/ambiguous/wrong holder,
diagnostic close failure, reader close uncertainty and release/holder-close
failure. Every case uses the actual pinned helper code with an inert driver;
no SQL or child process executes. 97 PS5.1 parser/remoting/pin/budget/process/
cleanup checks passed. Ruff initially found import ordering only; pre-lint
source/manifest/wrapper were preserved, imports ordered, pins regenerated and
all targeted checks passed again. No production helper correction occurred.

Architecture, deferred-item and security-routing validators passed; explicit-path
test selector ran. Full pytest, smoke imports, command registration and release
native suggestions are skipped for the bounded isolated test-only packet; no
application entrypoint, deployment or release path is changed.

Security route: Changes, Deep off, exact six new files (runner, wrapper,
manifest, two validators and this plan) against the last reviewed snapshot.
Review includes unchanged helper context and owned cleanup. SQL repository is
read-only authority; no SQL patch or separate SQL review target exists.
After review, one operator-console run is within existing D5 approval; adjudicate
its receipt before further native work. No automated dependent workload follows.

## Review completion and final pins

Changes scan `0cd99783-bd34-4e21-84d3-c75b8f07754f` completed with no findings,
all six files covered; Deep off. Range:
`0a06ce7f71538ad86dd8c71a201835c372aef61f` to
`1833841b99123cc8195ddc56b13f4e5ea7a8b8eb`. Completed sealed result was read back.
Measured review usage: 2,211,438 tokens, including 2,201,344 cached input tokens.

Review identified two stale descriptions in the wrapper (header and intent scope).
They were corrected to describe global admission/exact-holder observation.
An exact comparison against the reviewed Git blob verified only those two text
replacements; behavior, queries, source bundle, manifest and tests are unchanged.
97 PS5.1 checks passed again. A new Changes scan is skipped for this precise
comment/receipt-description-only delta: no runtime, input, permission, SQL or
cleanup control changes. The original reviewed blob remains in the immutable
snapshot; no executed evidence is overwritten.

Final wrapper SHA256:
`73713249B618D64B8A45B7D8F24F846350990FAB4B9701692516E398A8C923AE`.
Manifest SHA256:
`979bfe148f99398f111ff8e8a37b3d0e02bb0ac74d7dd7652b328f1351eae067`.
One operator-console attempt remains pending; no native budget has been spent
since accepted remaining readiness. Current balance remains 1,467 seconds.
