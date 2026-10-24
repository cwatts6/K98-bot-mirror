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
active streams, attempts, containment, replacement work, queued retry decisions,
missing private birth evidence or changed ownership stop recovery.

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
