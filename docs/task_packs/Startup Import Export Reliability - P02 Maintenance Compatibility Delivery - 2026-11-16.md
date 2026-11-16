# P02 maintenance compatibility correction

## Problem and decision

P02 deliberately moved KVK output indexes and FULLSCAN statistics maintenance
after atomic publication. The application schema guard still required both
indexes immediately. A valid published output could therefore prevent startup,
writer admission and the update preflight needed to correct the guard. Keep
deferred maintenance; align the consumers with the producer's valid post-states.

This correction does not complete an import, capture, maintenance or export.
The earlier failed collection/review attempts and E2 action remain evidence.
E1's closed configuration attempt remains closed. E2 and E3–E4 remain held for
separate receipt review and authorization. No host operation is authorized by
this document.

## Contract and ownership

The explicit `p02_kvk_deferred_indexes_v1` policy is an opt-in field on the
existing version 3 application contract. Old contracts remain strict. The
approved complete metadata and permission hashes, source definitions, dependency
scope and enumerated dynamic output inventory do not change. New seasons are not
automatically enrolled.

Only the exact nonunique, unfiltered, ascending single-column Gov_ID and KVK_NO
indexes of an enumerated KVK output may be absent. Any present index must retain
its exact approved definition. Canonicalize the actual metadata first; project
only proved absent maintenance indexes into the comparison shape. The result
must equal the independently pinned baseline. Retain the raw observation and
its digest separately; never replace a receipt with the projected shape.

Missing indexes require a current OUTPUT_COMPLETE header, matching table object
ID/creation time, matching due header revision, season and outstanding target and
aggregate generations. Pending, failed and unknown labels alone are not proof:
the observation must exclude live publication and maintenance. Indexed legacy
baselines need no invented ledger. Both indexes present do not prove FULLSCAN
or maintenance completion. Wrong definitions, unrelated metadata or permission
drift, completed-but-missing indexes and unsupported evidence remain refusals.

One DAL path reads metadata and maintenance evidence under a zero-wait session
Exclusive `K98:maintenance-schema:v1` lock. Existing producers hold Shared
transaction ownership and maintenance holds Exclusive session ownership. The
observation requires READ COMMITTED and no pre-existing ownership; it never
upgrades a lock or changes the caller's transaction or isolation. It does not
take the global writer lock: actual producer verification can use a different
connection from the outer writer admission owner and would otherwise self-block.
Acquisition refusal does not retry. Lost acquisition/release acknowledgement
retains connection custody and closes further SQL admission; callers must not
close retained handles. The helper performs no business SQL or ledger updates.

Startup, writer admission, the actual producer cursor and the packaged update
verifier use the same classifier and collection path. The updater archive keeps
the previously corrected core imports. The D6 resource-scope correction and SQL
release pins are unchanged. A closed continuation now links the latest closed
attempt and explicitly avoids claiming publication/capture/export success.

## Delivery boundary

The source-only repair is pinned to private predecessor
`729ece15c2dd665906525a4a457667d53516e805`, the existing three protected startup
contracts and SQL commit `8a7aace75c55a6d17c9051edef9026dc25355af8`.
The exact four-member source transition binds both new helpers, runtime
composition and continuation diagnostics. Every historical transition is retained.
The only seed amendment is the reviewed policy and review identity; unchanged
metadata/permission/source pins are checked. Any added SQL or recovery seed work
is refused. The new sealed verifier validates the exact candidate policy during
preflight and successor readiness; it does not adopt observed hashes.

No SQL migration, schema repair, index creation, maintenance replay or new grant
is included. The SQL source-of-truth definitions were checked for both ledgers,
header identity, producer lock ownership and worker generation/partial completion.
The worker's existing multi-target completion handling remains valid.

## Regression and review requirements

Grouped tests cover the real shared comparator and snapshot DAL, actual producer
entry point, zero/one/two indexes, multiple seasons, pending/failed/unknown,
indexed legacy state, malformed/stale identity and generations, permissions,
definitions and unrelated drift. Ownership tests cover busy acquisition,
unknown cleanup, no retries and no transaction changes. Delivery tests cover the
complete source/seed/start/readiness packet, exact predecessor refusal, archive
imports and rejection of additional SQL/recovery work. Continuation tests prove
the closed attempt remains linked without dispatch or a success claim.

Run the full offline pytest suite with native SQL/Windows fault opt-ins disabled,
log isolation, lint, architecture/deferred/security-routing validators, test
selection, smoke imports and command registration. Record failures separately;
do not overwrite earlier attempts. Review the final immutable Changes diff with
Deep disabled. Mirror and private promotion targets require separate evidence.

Native G1/G4/G5 proof remains a separate release gate: exercise actual publication
with deferred maintenance through the guard, capture and next writer, and verify
native lock/cursor behavior. Offline fixtures cannot prove this. Reuse approved
fixtures within remaining allowances; freeze case count, cleanup and time bounds
before requesting execution. Do not create another database or consume rows,
inputs or fault-test time without an approved allocation.

## Deployment and verification sequence — held

1. Complete mirror review, CI and Changes review; prepare the same patch on a
   branch based on private main. Resolve review threads with evidence and check
   the final private diff. Merge neither repository as part of this task.
2. Complete the bounded native qualification gate. After approved source merges,
   bind a release packet to the exact private merge SHA and current installed
   updater manifest. Recheck predecessor/source/seed/SQL identities. A changed
   predecessor requires review, not an edited constant or guessed transition.
3. Obtain fresh read-only custody evidence for every changed path and existing
   ancestor, including documentation directories. Historical ACL checks do not
   establish current readiness. Review the concrete pinned host packet before
   authorizing its execution.
4. Upgrade the installed updater with its exact old/new manifest package, then
   use the normal protected updater from private main. Require preflight of all
   three contracts and the reviewed policy before drain. Follow its one graceful
   restart instruction. Never manually edit the startup seed or switch source.
5. Review source/seed/start/readiness receipts and raw schema/lifecycle evidence,
   then check again after the normal background configuration publication. Verify
   permissions and source pins remain exact, valid deferred indexes are accepted,
   maintenance remains accurately pending, and no duplicate publication occurs.
6. Pause for receipt adjudication. Only then separately approve the next E2
   action and subsequent E3–E4 work. The later normal acceptance run uses a new
   user-generated scan through Discord and the standard output destinations.

On any surfaced failure, preserve all files and stop. No host rerun or recovery
is implied. Rolling source back to the strict predecessor while retaining the
new policy or deferred database state is not a supported rollback. Retain the
failed update and use a separately reviewed forward correction; never create
indexes or replay a producer to make a guard green.

Remaining recorded allowances are 774 native seconds and 49 Windows fault-test
seconds, with zero additional input/row/database/backup allocation. This offline
correction spends none of those allowances and does not reset D7 acceptance.
