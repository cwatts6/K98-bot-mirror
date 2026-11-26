# P02 D5c metadata observation acceptance and dev restart handoff

## Current checkpoint

The operator needs to restart the development machine soon. The read-only
follow-up is accepted from its saved receipt; no new native workload was started
while preparing this handoff. At the captured observation there was no Python
qualification process or other copy session, both collector SQL connections closed,
and the exact work-session birth was absent. The evidence is saved on the host.
This is a qualification stopping point, not completed account cleanup or D5c closure.
No restart, VM shutdown or subsequent state has been executed or observed here.

Accepted receipt:
`d5c-metadata-setup-observation-result-219fbf6683d449b5b717d9f00733fc0a.json`,
SHA256 `f781075b13c4f722f16781bdcbb5e831c9587eaf93bd308c0e24538f2abe26cc`.
Local adjudication:
`.codex_artifacts/p025/d5c-metadata-setup-observation-acceptance.json`.
It verified every manifest observation, all preserved receipt hashes, exact
principal identity, the original accounts and permissions, seven fixture rows,
completed maintenance and original failure history, ownership, definitions,
statistics, backup demand, resources and physical connection cleanup.

The first Setup failure remains immutable and incomplete. Its CREATE was
acknowledged; do not repeat it. The restricted metadata diagnostic never ran.
The temporary database user still exists and must not be silently abandoned.

## Exact remaining test user

- Database: `K98_P025_D5b_20261111`, ID 8, created `2026-11-11 17:00:42.830`.
- User: `P02_D5c_Metadata_20261112`, ID 15, created `2026-11-12T22:02:45.210`.
- SID: `0105000000000009030000008D895FA507D33D40B5926264219625EB`.
- Type S, authentication NONE; same-name server-principal count zero.
- Zero role memberships, owned schemas and owned objects.
- Only recorded direct permission: DATABASE CONNECT, class 0, major/minor 0,
  grantee 15, grantor 1, type `CO  `, state G/GRANT.
- That tuple was identical before/after. All other permissions retain fingerprint
  `3a1048abe7ef3e76fe49b05a4de65970aabc86d2470c450f4ab8ea741dc85301`.
- Existing database-user fingerprint:
  `c522f0a5fc6c76e27984d13cb86cb33e2d6cbb60c74a2e2ac87c60c2cdfa8329`.
- Existing server-principal fingerprint:
  `c658d12beb02354b11d8c8ecae9248c637e64590cc1547a4894b55d12ce95bc`.

The failed packet expected a 32-hex SID and zero direct permissions. Native evidence
shows a 56-hex SID and the exact CONNECT tuple above. The follow-up does not alter
those rights. No account reset, revocation, ownership change, new login or new user
is needed to correct the test harness assumptions. Any corrected diagnostic still
must prove its actual restricted identity and lack of metadata rights before the
single unused test is accepted.

## Resume sequence after the operator restart

1. Reopen elevated Windows PowerShell 5.1 on host `9SX2VF4`. Revalidate the exact VM
   `2ac1b401-7076-4965-af71-de36ee0f9f9c` / `K98-MGE-Qualification-20261029`, four
   CPUs, static 8 GiB, zero network adapters, approved original and Q: disks, and
   resource reserves. Do not infer Running or automatically change resources.
2. Establish a fresh authenticated guest session. The prior console variable
   `$global:D5bReportSession` and session ID `67caa9aa-5bb2-466c-991d-26ab8e1a2fc6`
   are historical after restart and must not be treated as a new connection.
   Credentials remain local. Capture the new session identity before preparing a
   handoff pinned to it. No old packet is suitable for blind rerun.
3. Revalidate the existing database/user using the saved birth identity and both
   receipts. Session-local `D5cMetadataState` is not durable evidence. Its identity
   was null after failure; the old guest/host owned-user files were never written.
   Do not fabricate successful Setup, recreate the user or use name-only cleanup.
4. Prepare one corrected existing-user continuation, including diagnostic and exact
   cleanup, under the remaining account scope. Preserve original executables. Fix
   the SID assumption in PowerShell, Python and regression fixtures together;
   require the exact observed CONNECT tuple, not an arbitrary permission count.
   Bind identity from hash-verified receipts, save custody before later eligibility
   assertions, and retain no-SQL-after-uncertain-custody rules.
5. Complete offline tests and frozen Changes review of the complete continuation
   before any native handoff. Run the still-unused diagnostic once only after
   current identity, permissions, session and resource checks pass. Then remove
   only the exact recorded user under the already-approved cleanup scope and prove
   original permissions/accounts restored. Stop on uncertainty; no CREATE retry.
6. Continue the remaining D5c groups and later slices. Preserve accepted pre-restart
   evidence; do not rerun completed tests merely because volatile caches vanished.
   An ordinary development-machine restart is not itself D5d fault-test evidence.

Existing approvals carry forward; this handoff does not request a new account or
permission exception. Any scope expansion or exhausted allowance still needs its
own concrete plan. No diagnostic/native correction is handed off before review.

## Remaining work, in plain language

D5a readiness and D5b maintenance/report qualification were accepted. D5c has
accepted many coordination, file-protection, configuration and access cases, but
it is not one or two checks from completion. The latest recorded partly-open
groups are:

- C01: complete inspector behaviour.
- C04: season and weighting configuration consistency.
- C05: queue/pool and work without a verified owner.
- C06: adapter-specific action/count boundaries.
- C07: this restricted-metadata diagnostic and temporary-user cleanup.
- C09: remaining connection-factory and identity routes.
- C12: full presentation integration.

These groups differ in size; no defensible percentage or short completion ETA is
established. D5d fault/restart/lost-acknowledgement tests, D5e balanced cost checks
and D5f final evidence/release readiness follow. D6 deployment authorization is
separate; no P02 production deployment occurred in these lab checks.

## Limits and validation

The follow-up's full host time was 2.2320448 seconds, charged as three seconds.
Remaining: 1,393 native seconds; 175 seconds in this account scope; 50 Windows-test
seconds. The later-phase reserve stays 1,000 seconds. All 21 inputs remain consumed,
with zero new inputs. Seven of the 64 fixture rows were used; the unused balance
is not blanket permission for new fixtures. No maintenance, writer or isolation
retry is available. Per-packet, statement, row, byte, process, memory, CPU, disk and
network-isolation limits are unchanged. Reboot wall time is not represented as a
new qualification run or a replenishment of any allowance.

This turn only adjudicates local immutable evidence and writes derived acceptance
and restart documentation. No production source, SQL, VM or executable native
packet changed. Security Changes scan is skipped for this bookkeeping-only delta;
the reviewed observer remains byte-identical. Architecture and deferred/routing
validation apply; full pytest, imports, Discord registration and native tests are
skipped because there is no corresponding runtime change. The source-only
continuation plan is not an executable correction or native test acceptance.
