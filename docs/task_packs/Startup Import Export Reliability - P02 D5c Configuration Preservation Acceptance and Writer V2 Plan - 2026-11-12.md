# P02 D5c configuration preservation acceptance and writer V2 plan

## Accepted follow-up

Receipt `d5c-config-poststate-result-1e972b0cb330453191643ed14ac4635c.json`, SHA256
`20cd1cffb94286866bd6275d5a71249d99b4be5117dfaff8a385eb1f8405eb6c`, passes independent
Python adjudication against all expected row dictionaries, the original admission
and failed writer prestate. All seven fixture rows retain their exact original
values; preparation/resource versions are 3/22/19. Protected ownership, permission,
ledger, backup, original-database protection, candidate images and statistics
remain unchanged. Both resource samples pass; both SQL connections disposed and
the absence query includes the failed writer application. No workload ran.

All 24 metadata and five fixture reads are present: 35 reserved client/control
units, 109 actual rows. Host 1.8149599 seconds debits two. **1,433 native seconds,
50 Windows-test seconds, 174 configuration-scope seconds and 116 later-test seconds
remain.** Seven of 64 fixture rows are consumed; 21 inputs stay consumed, with no
maintenance retry. The final 1,000 native seconds remain reserved for later slices.
The earlier writer receipt remains failed; this later observation does not create
its missing rollback acknowledgement or prove configuration consistency.

## Proposed additional attempt

One additional writer-first invocation requires operator approval because the
first invocation was consumed. It uses the same seven-row fixture, unchanged
production `ConfigPreparationRecoveryDAL.target_data`, same disposable database,
same pinned Python/pyodbc and 17 full source modules. It creates no new row and
commits no change. The original actor/wrapper/manifest/intent/failure remain intact.

Versioned files are `scripts/p02_d5c_config_writer_first_v2.py` and
`scripts/run_p02_d5c_config_writer_first_v2.ps1`, with
`.codex_artifacts/p025/d5c-config-writer-first-v2-execution-packet.json`.
This is test-only tooling, not a production runtime correction.

The writer's unparameterized identity batch validates exact server, database ID,
name, login, transaction and implicit-transaction state before BEGIN. It returns
the exact session birth and active transaction state. The subsequent parameterized
update checks transaction count one and changes only the exact three approved
versions to 4/23/20. The unchanged actual reader must still see committed 3/22/19
and the full expected preparation/resources/stream identity.

One separate parameterless rollback batch verifies zero transaction count and
zero transaction state. A parameterized read then verifies restored 3/22/19.
No prepared data batch changes transaction nesting. Values in data predicates
remain parameterized; no interpolation of external input or permission change.
The begin attempt is recorded before dispatch so cleanup also runs after a late
identity-result failure. Wrong identity never admits the reader or data change.

Every writer statement records execute/fetch/drain stages and accumulated rows
before returning. A late error preserves those rows without treating them as an
acknowledged result. The wrapper reports child failure before enforcing success
totals. It still refuses any error, incomplete rollback, missing stage, wrong
identity, mixed tuple, duplicate/missing result or uncertain process/connection
cleanup. Neither error 266 nor unknown outcomes are suppressed. One rollback only;
no retry loop. A failed rollback skips restoration reads and retains the error.

## Unchanged ceilings and observation equivalence

The extra rollback control fits the existing **48-unit ceiling** by combining
the existing outer setup text and identity SELECT into one metadata call. Their
SQL text and all other metadata observations are preserved. Reservation is:
23 metadata calls, six outer open/close/cancel controls, 13 reader calls/controls,
and six writer calls/controls. The actor's 19 units include nine SQL calls and
12 result rows; the packet retains its 149-row planned maximum and global
2,048-row/512-per-result/1-MiB receipt ceilings.

The redundant seven-row proposal is omitted from the V2 manifest to retain the
128-KiB manifest ceiling. Its original proposal hash, authoritative SQL source
hashes, accepted admission/poststate receipts and exact reader target remain
pinned. No evidence is deleted and no expected value is weakened. The compressed
full-module bundle is unchanged. No installation or dependency update is needed.

Existing 3-second SQL timeout, zero lock wait, 20-second actor watchdog, 25-second
parent wait, 30-second work, 42-second cleanup and outer 45+10-second limits remain.
Manual ceiling is 60 seconds within the 116-second later-test allocation. This is
SQL qualification and does not debit the Windows file/IPC allocation. Only the
owned process may be terminated on deadline; forced exit never counts as success.
The observer waits for confirmed work disposal and child join, then proves all
sessions under the exact attempt application are absent. Unknown custody blocks
dependent work. No VM, isolation, permission, original database or retained-input
change is included.

## Offline validation and review

Eleven isolated Python tests pass using inert drivers and the actual pinned DAL.
They cover old/mixed/dirty tuples, identities, guard/change/rollback/close failures,
source framing/startup, GUID case, parameterless controls and parameterized data,
and late errors at all four writer drain points with retained rows and no replay.
198 PowerShell checks pass for inherited controls, source and lineage pins,
23-call entry gate, merged observation text, 48-unit accounting, remoted evidence,
incomplete stages, primary error precedence and physical-closure admission.

Architecture and Ruff checks cover the two Python files. The selector is run;
full application pytest, smoke imports, command registration and release tests
are skipped because no application, Discord, deployment or production source
changes occur. Offline fake execution is not native qualification. Security
routing is **Changes review, Deep off** for the four versioned source/test files
and this plan, with the original failed and accepted evidence as context. SQL
source is read-only; there is no separate SQL Git delta.

## Decision and continuation

Review completed on 12 November 2026: Changes scan
`0262a070-e3f8-4700-bd2b-3ec78228fdac`, Deep off, sealed and read back with zero
findings. All five snapshot files were byte-verified against
`33934116cc71c3d71a8104ae0294fbb5a6c4f16d`; an independent reviewer found no concrete
execution blocker across the four source/test files and pinned manifest/DAL.
This paragraph records the completed review after the immutable snapshot.
The offline preparation acceptance is
`.codex_artifacts/p025/d5c-config-writer-first-v2-preparation-acceptance.json`.
Wrapper SHA256 is
`2658a943e90f99b998fb9c66e8e61a6832f04fc8b0c056f3903e6c77ffce5e17`;
manifest SHA256 is
`6a5db18f6e8f8ab1c772520bd10fc792c9567da6556ad46905241656ae83d54d`.
Original failed bytes remain pinned and unchanged. V2 execution intent is absent;
the additional attempt is not yet approved. Review-reported usage was 2,088,626
tokens; this is review telemetry, not native-time or input consumption.

After completed review, request exactly one additional writer-first attempt under
the unchanged limits. No console execution before approval. If it succeeds,
adjudicate the full raw records, actual reader result, restoration, protected
metadata and physical cleanup. Only then prepare the already-scoped reader-first
committed transition and stale-action refusal. If it fails, preserve its receipt
and stop; no automatic repeat or reset. D5c/d/e/f and separate deployment approval
remain open. Synthetic session/stream history is not proof of provider activity.
