# P02 D5c global holder acceptance and reverse order - 2026-11-12

Status: reader-first global admission and known-holder diagnostic accepted.
Reverse-order lock-only packet passed offline checks and completed Changes review;
one operator-console attempt is ready, with native acceptance still pending.
D5c/d/e/f remain open. No additional workload or permission scope is implied.

## Accepted evidence

Receipt `d5c-global-holder-evidence-result-1c86690a682448d5b8b1007a0dc7699e.json`
matches SHA256 `92E488B770D96F71AF9388B839DC40C737047848053B17BDC68BF9111AE579BE`.
Independent adjudication verified all 24 wrapper observations, paired protected
state/resource checks, seven unchanged source hashes and exact child identity.
Global grant was 0/Exclusive; the competing requester returned -1/NoLock.
The unchanged diagnostic identified holder session 54, connection
`E544FFE9-E3D9-4036-936B-B8CDD61D3FC6`, distinct from requester session 55,
connection `0AADE84C-861F-4215-8E4F-450E4E0C0544`; both birth times matched.
It reported SESSION/X ownership and retained the original refusal without notes.

All 17 acknowledged reader events ended in rollback, isolation restoration,
cursor close and connection close. Global release returned 0/NoLock. PID 1664
joined normally, without forced termination; both actor sessions were absent in
the independent observation. Wrapper actuals: 24 statements/29 rows; child:
nine statements/eight rows. Reserved totals remained 48 commands/41 rows.
Acceptance is retained in `d5c-global-holder-evidence-acceptance.json` under p025.
Host elapsed 1.9337892 seconds debits two, leaving **1,465 native seconds** and
465 of the proposed D5c allocation. **21 inputs remain consumed; zero new inputs**.

## Next concrete case

Use the same isolated copy, authenticated console, pinned runtime and unchanged
managed-reader helper. Establish one exact global Exclusive/Session owner first;
require acknowledged acquisition before the reader factory is called. Enter the
managed reader once, requiring SNAPSHOT, Shared/Transaction schema ownership and
NoLock for the global Session guard. A global owner must not block that reader.
Require reader rollback/restoration/close before one explicit owned global release
and holder close. Independently verify process completion, protected poststates
and absence of both actor sessions. No retry or dependent workload follows.

The previous native holder diagnostic is not repeated: this packet covers reverse
arrival order only. Full inspectors, account/season/action-time cases, actual
maintenance-child overlap, rights and disabled-isolation proof remain separate.
No maintenance, report, import, backup, synthetic fixture, grant, impersonation,
SQL setting or production change occurs. All original evidence is preserved.

## Source, tests and bounds

New test-only runner/wrapper/manifest reuse the reviewed forward-order packet.
The exact global grant block moves before reader entry; optional holder diagnosis
is removed, leaving the original six pinned helper modules. Authoritative
`dbo.usp_RunMaintenance` retains the same global resource/Exclusive/Session
contract. No Bot or SQL production source is changed; no refactor is needed.
Accepted forward receipt and remaining-readiness receipt are pinned.

All 24 wrapper statements/preimages/runtime bindings and child limits remain:
24 child command units/12 rows reserved before launch, total 48 commands;
12 child SQL statements maximum, expected seven statements/six rows. Same fixed
8-GiB/four-CPU/zero-NIC VM, disk/log/version-store limits, one-MiB receipt,
three-second SQL, zero lock wait, 20-second watchdog, 25-second parent wait and
bounded process join. Stop/report a hang before 60 seconds; charge full host
elapsed time including failures and cleanup against 1,465 seconds.

Six isolated fake-driver tests (seven case variations) passed, with explicit
factory-time assertion that the global guard was already acquired. Tests cover
wrong identity, refused grant before reader entry, wrong reader ownership,
uncertain close and release/holder-close failure without replay. 96 PS5.1
parser/remoting/pin/process/budget/cleanup checks and Ruff passed.
Architecture/deferred/security-routing checks and the explicit-path test selector
passed (19 Python files, 44 Markdown files, zero routing errors or warnings).
Full pytest, application smoke/command registration and release-native suites
are skipped for this bounded test-only packet: no application/release behavior
changes, and their startup is outside this offline selection.

Security route: Changes, Deep off, six new files against the last reviewed
global-holder snapshot, including both validators and this plan. SQL repository
remains read-only source authority; there is no SQL patch target. Once review
completes, the single operator-console run is within existing D5 approval.
Native acceptance still requires its actual receipt; source success alone is
not evidence that this reverse-order case passed.

## Final review and handoff

Changes scan `6a04bce3-e4a2-4edc-8ff8-a5d3b6b706dd` completed with zero findings
and all six files covered, including independent full wrapper/PS validator review.
Immutable range: `1833841b99123cc8195ddc56b13f4e5ea7a8b8eb` to
`9dfc244baa46b61108e5353a04605a40dc994c52`; Deep remained off. The final draft
was saved successfully before completion; completed sealed coverage was read.
Measured usage: 1,677,691 total tokens, including 1,579,136 cached input tokens.
The inherited manifest status string and runner schema comment are descriptive
only; executable ordering, qualification field and acceptance checks explicitly
require global owner first. They do not change the reviewed execution contract.

Final operator pins:

- `scripts/run_p02_d5c_global_owner_first.ps1` SHA256
  `8D7B51258BAB745C66320E4C97DF0B864BF3FF224DBC8EBB668A6244C0F4AAB6`.
- `.codex_artifacts/p025/d5c-global-owner-first-execution-packet.json` SHA256
  `469742c57ba7847c4ef9799ad5855ac2398e249c6e2441d1ad774b80ff79df53`.

All six source files matched the review snapshot before this status-only addition.
No execution intent/result existed at handoff. This documentation-only review
record adds no executable change and does not require another Changes scan.
Use the existing D5bReports console session, one attempt only, retain full host
elapsed time, stop on incomplete/error and review the receipt before continuing.
