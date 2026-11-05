# Stranded legacy export recovery

This is a separate, reviewed administrator recovery packet for a running legacy
export whose original authority could not commit stream closure or record the
worker failure. The ordinary updater correctly refuses its open stream. An
ordinary restart is not a repair: job-held resources also prevent startup.

The packet runs alongside the installed source, from an administrator-protected
directory. It does not modify installed Python, manifests, startup tasks, flags,
imports, reports, output files or spreadsheet URLs. It makes no Google request.
Its source must be reviewed and tested before the operator receives a packet.
The generic implementation contains no production operation identifiers; those
belong in the private, checksummed `recovery-target.json`.

## Safety boundary

The launcher requires elevated Windows PowerShell 5.1 on MINI_AMD under the
installed deployment account. It verifies packet hashes, protected startup gate,
policy, current publication and manifest, the pinned Python launcher, and all
installed application source before importing it. Both original process handles
remain pinned and live throughout recovery. An external process does not
impersonate the Bot or bypass the process-authenticated authority pipe.

Inspection requires exactly the reviewed legacy job, owner, fence, versions,
stream, session, child and request sequence. Registered destination membership,
configuration hash, resources and session principal/manifest must agree. Other
active streams, conflicting attempts, containment, replacement work, queued retry decisions,
unproven writer identity or changed ownership stop recovery.

The deployed legacy mutation path did not persist `host_birth`; the historical
birth reader remains strict. A packet explicitly pinned to
`live_custody=authority_handles_v1` can instead inspect an exact resources-only
legacy scope through the original authority's live Windows handles. This is a
separate `live_writer_custody/1` review record, never a reconstructed birth or a
change to `ScopeJson`. Malformed or present-but-invalid birth bindings still stop.

Live custody pins the original authority, exact child command line and parent,
process creation time, executable hash, token, machine and the unique private
containment Job actually held by that authority. Inspection duplicates query-only
Job handles. Apply reobserves the exact reviewed identity before retaining query
and termination rights; it cannot substitute a new process with the same PID.
The collector is bounded and fails closed if native Windows observations are
unavailable, the original child has exited, or any identity is ambiguous.

An original `private_started` attempt is expected once legacy mutation begins.
Inspection accepts at most that first, unverified attempt with its original
owner/fence, version, input hash, manifest and exact registered output parts.
Retries, additional attempts, publication evidence, changed parts or ownership
remain conflicts. The full attempt and part rows are bound into the review token
and checked again under the existing ownership locks before settlement.
Settlement retains those rows and their immutable fields, marking the attempt
uncertain and its parts quarantined through the existing failure transition.
Resume accepts only that exact versioned transition and its saved failure intent.

A corrected packet uses a new protected directory. When it names a previous
packet or packets, every named protected journal must remain present and have no Apply
intent. A previous Apply intent stops the corrected packet for evidence review;
replacing a packet is never permission to reset an in-progress recovery.

Apply uses existing SQL freeze/close procedures and the existing conservative
worker failure transition. No schema, permission or SQL module change is needed.
After a successful freeze, the helper stops only the authenticated private named
writer job. Positive process-handle termination and an empty job, including any
contained descendants, must be observed. It records private closure evidence,
seals request membership, and runs the existing private request/event verifier.
It then marks the job uncertain and retains all reservations and original input.
It never reports successful delivery or automatically performs legacy closeout.

## Operator sequence

1. Keep the current Bot running. Download the reviewed packet to MINI_AMD;
   verify its independently supplied checksum and extract it outside the Bot
   source directory.
2. Run `Invoke-K98StrandedExportRecovery.ps1 -Action Inspect -PacketSHA256 <provided hash>`.
   Return the `RECOVERY_REVIEW_READY` result, including its review token, for
   checking. Inspection writes only its private local review file.
3. Run the same script with `-Action Apply`, the same packet hash and
   `-ReviewToken <verified inspection token>`. This is the explicitly authorized
   writer-stop and bookkeeping operation. Expected result:
   `CLOSURE_VERIFIED_CLOSEOUT_REQUIRED`, `outcome=unconfirmed`,
   `reservations_released=false`, `provider_requests=0`.
4. In the existing Recovery centre, recheck the exact export. Review and confirm
   **Allow next export** only when the action is offered for the same registered
   destinations. This abandons the obsolete partial export, retains history and
   permits a later export to the unchanged URLs. It does not certify delivery.
5. Download a fresh complete recovery report and run the bounded blocked-export
   metadata collector again. Verify the writer is closed, original reservations
   are released through the recorded closeout, and no other execution blocks
   deployment before running the ordinary updater.
6. Resume the normal protected updater. Request its graceful restart only when
   prompted. Complete deployment verification before a new import/export.

All stages stop on conflicting or missing evidence. Preserve the entire protected
packet directory and any partial journal; do not delete it, edit receipts, clear
SQL rows, substitute another stream, force a restart or repeat the import.
An acknowledged or lost-acknowledgement transition is reconciled against exact
SQL readback and the immutable local journal. The same reviewed Apply may resume
only that intent. A different inspection token is never a reset mechanism.
A crash before positive termination evidence is durably retained may require
further evidence review; absence of a PID is not a closure receipt.
For live custody this boundary is explicit: an interruption after termination
but before saving its positive receipt remains stopped with a frozen stream.
A saved receipt must match the complete reviewed process incarnation and custody
hash; resume rechecks the empty named Job without reopening a PID. No receipt is
fabricated from an exited child. Keep the original Bot and authority running.
Temporary query handles can extend a Job's lifetime if its original owner exits
concurrently; inspection closes its own copies promptly and never closes an
original authority handle.

## Acceptance and limits

Tests cover identity/scope refusals, actual Windows named-job containment and
termination, damaged private request evidence, unchanged reservations, and lost
acknowledgements at freeze, close and failure recording. Disposable SQL exercises
the real procedure/ownership transitions. Those tests are not production proof.

The old in-memory authority may report an unresolved local closure during later
shutdown because the administrator tool owns the new receipt. The installed
issuer still requires positive original-process termination and independently
verifies the durable closed stream and released claims before accepting handoff.
No session is closed by this tool, and no provider child is adopted for execution.

P0 closeout remains separate: retain the accepted import/report and timing/cache
receipts, resolve current incidents without replay, validate one genuine new
import/export to every registered destination, and map the receipts to F01–F05
in `docs/task_packs/P0 Coordinated Completion.md`, including any outstanding
natural rollover acceptance. Preserve the full deferred P1 scope.
