# P02 D5 custody acceptance and inspector fixture plan — 2026-11-13

D5a and D5b remain accepted. The additional D5d offline packet passed all 38
cases after completed Changes review. D5c and the remaining D5d/D5e/D5f gates
remain open. This is qualification work; it does not deploy P02.

## Accepted offline result

The create-only receipt `d5d-custody-offline/result.json` has SHA256
`8cc88b848ba80f1309711b8e780581a6e5e7912c3415efebdbbf46532f29f9be`.
It records 0.266 seconds, 6,664 diagnostic bytes, seven expected boundary
refusals, 14 dedicated-factory setup cases, six profile cleanup cases, eight
transaction acknowledgement/cleanup cases and three factory-selection cases.
No case failed or remained unexecuted. There were no pending tasks or extra
threads. Independent post-run adjudication verified all 476 preservation hashes,
the six reviewed files and the unchanged ordinary Git HEAD/index.

Changes review `7d316b09-d278-4d60-80e5-a6e609d44fbd` completed before execution
with zero reportable findings. Its target was the six-file immutable range
`c37d6d70b36b789d17102f2f725a91b9ed1e22e2..011518ea31b160221bb260b51dcda68184feed35`,
Deep off. The tool reported 3,312,384 total tokens, including 3,199,744 cached
input tokens. These are service-reported review usage, not native test time.

This result supports D5c C09 and D5d's offline custody requirements. Synthetic
connections cannot prove physical SQL release or process-death/restart behavior.
Four threaded setup cases and broader caller coverage remain explicitly open.
No application/runtime change was required. No old failed pass was repeated.

## Next native setup: four pending inspector records

The operator's current authorization is to complete all D5 tasks while retaining
the existing limits. This new preparation is within that scope. It is not a
repeat of any consumed maintenance, writer, isolation or account test.

The exact proposal is `d5c-inspector-fixture-proposal.json`; the execution packet
is `d5c-inspector-admission-execution-packet.json`. It creates four labelled
`dbo.ExportPreparation` rows on `K98_P025_D5b_20261111` only, under account
`d5c_inspector_20261113` and storage owner `d5c_qualification_only`:

| Label | Intended inspector route | State and evidence |
|---|---|---|
| legacy | Stats, historical and inherited unreceipted inspectors | Pending, no execution receipt; a missing receipt remains an honest hold |
| player_stats_report | Player report inspector | Pending atomic-report request, no execution/capture |
| configuration_import | Configuration-producer inspector | Pending atomic-configuration request, no execution/capture |
| all_kvk | All-KVK capture inspector | Pending request; no committed checkpoint is claimed |

All four have owner NULL, fence 0, version 1, no job, generation, spool or
resource reservation. Their unique identities, request bytes/digests and every
column value are fixed in the proposal. The all-KVK season number is a synthetic
positive value in an unfenced preparation, not a claim about an actual season.
No execution or provider history is fabricated. No producer is invoked.

The authoritative `dbo.ExportPreparation.Table.sql` defines one foreign key,
JobID to ExportJob. All four JobID values are NULL, so these rows require no
dependent fixture, weakened constraint or schema change. The existing captured
catalog pins the installed object ID. Admission requires no enabled trigger or
disabled/untrusted foreign/check constraint. Exact preparation IDs and the
entire new account namespace must be absent under transaction locks.

The transaction inserts each row once, compares all columns before commit,
acknowledges commit, then compares the committed rows. Any failure stops without
retry. An unacknowledged commit remains uncertain even if a rollback is later
acknowledged. Evidence is preserved for read-only diagnosis. A failed check after
acknowledged commit does not claim the committed rows were rolled back.

The original database protection, candidate definitions, permissions, ownership,
maintenance history, backup demand, physical statistics, resources and connection
closure are checked using the established collector. Added checks preserve the
exact existing seven-row fixture and the absence of both removed test users and
the removed test login. Existing evidence is never overwritten or reset.

## Limits, validation and handoff

Before this setup: 1,361 native seconds remain, including the protected
1,000-second later-phase reserve; 50 Windows-test seconds remain. The full host
elapsed time is charged upward to a whole second. This admission has a 60-second
overall ceiling and does not use the Windows-test allocation. Seven fixture rows
already exist; four new rows bring the total to 11 of 64, leaving 53. The consumed
21-input allowance remains unchanged. No maintenance, writer or isolation retry
is restored.

The ledger reserves 45 client commands (including all cleanup/cancellation
branches), below the unchanged 48 limit, and 155 returned rows below 2,048.
The receipt remains limited to 1 MiB. Host/guest identity, fixed VM resources,
zero network adapters, disk reserves, session identity and no active Python
producer are checked before SQL admission. The exact borrowed session is
`D5cResume`, instance `0273a292-0961-4cda-bbce-15de9eaead0e`.

The dedicated Windows PowerShell 5.1 validation passed 446 checks without a VM or
SQL connection. It exercised typed parameters, remoted values, ordering,
preservation of existing helpers/queries, failures at every admission stage,
uncertain commit plus failed rollback and post-commit verification failure.
Changes review of this complete setup packet is required before console handoff.
No native attempt has run at the time this plan is authored.

The follow-up inspector packets will execute the actual DAL inspection methods,
including inherited paths, in both reader-first and owner-first global/account
orders. Each case must observe the reader inside its snapshot before admitting
the competing owner, or establish the owner before starting the reader. Exact
busy refusals at live-owner probes are expected; passive tuple reads and actual
action eligibility are distinct contracts. After release, a fresh inspection
must report the fixed fixture and honest hold/action result. No action is
executed, no preparation changes, and no import/report/provider work is included.
Those follow-up executables require their own bounded ledger, offline checks and
review; this setup script cannot dispatch them automatically.

Season/weight, queue/pool/unowned-hold and remaining action-adapter qualification
still require their separate fixture/caller reconciliation. The four rows above
do not substitute for those tests. D5e still requires balanced measured workload
pairs, and D5f cannot close while required evidence is missing.

This packet introduces no production source or SQL repository change, migration,
new permission, dependency, instrumentation or deferred optimisation. Broad
pytest/application startup and PR/promotion validators are not run: this is a
bounded test packet, not a PR or promotion handoff. SQL schema/parameter alignment
and focused PowerShell validation apply directly; security routing is Changes
on the immutable packet, with Deep off. Existing runtime changes remain intact.
