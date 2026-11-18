# P0 existing URL export recovery

## Approved scope

Preserve existing spreadsheet URLs. An obsolete partial legacy export may be
abandoned after independently verifying every original execution stream and
request, so the next normal scan can publish to the same files. Do not rerun a
committed import or reporting stage. The next scan has not been imported and is
reserved for operator acceptance after deployment. No automatic merge or deploy.

## Architecture and SQL review

The current isolation decision keeps immutable target records and disables the
old stream, but also prohibits subsequent writers to those files. Add a durable
legacy-export closeout receipt and an effective-target view. Historical containment
rows remain unchanged; only a verified closeout makes their target restriction
inactive. Old streams and attempts remain disabled and historical outcomes remain
partial, never confirmed delivery. Restrict this to registered scan_data/all_kvk
exports; new-source pools and rollover remain outside this correction.

The URLs have not changed: recovery lifts a write restriction, not a URL mapping.
Only ordinary legacy job mutations and exact configuration preparation probes
may use targets released by this receipt. Queue selection, locked admission,
stream opening, request preparation/dispatch and later closeout bind the release
to the original receipt's account. A missing account retains the restriction;
destination mutexes remain global for each physical file. The global active-target
view is diagnostic inventory, not an account-specific authorization decision.
Queue selection, locked admission,
stream creation and request dispatch preserve permanent target history for
managed pools, rollover and enrollment. Managed publication proof rules remain
unchanged. A subsequent failed legacy export uses the same evidence-based
closeout rather than attempting another containment row or replacement URLs.
An uncertain export with no execution stream retains its existing unstarted-work
recovery option; it cannot enter the closed-stream closeout path.

The private authority verifies original child closure and complete typed request
and response journals. For an already-contained stream, retrieve the authenticated
pre-containment stream from its retained private decision and verify that original
closure. Missing private evidence, unknown dispatched requests, live streams,
changed registrations, competing ownership or replacement work prevent closeout.
SQL independently checks exact owners, versions, complete membership, terminal
request events and action identity under account/resource locks. Repeat clicks
and lost replies read the same receipt, never dispatch work again.

Services own evidence validation and operator decisions; DAL and reviewed SQL
procedures own persistence. Existing recovery UI, actor checks, private evidence
store, identity/digest helpers and request verifier are reused. No SQL in views or
commands. The operator action is “Allow next export”; it does not publish data.

## Validation and review

Test successful partial writes, unknown and missing request events, damaged
private closure, stale confirmation, foreign custody, competing work, restart,
lost acknowledgement, immutable history and subsequent same-target admission.
Run real disposable SQL tests including restricted application/authority roles,
all required repository validators, focused regression tests and private-checkout
validation. Run separate exact-target Changes security reviews for bot/private
and SQL changes, Deep off. Package through the protected updater, SQL before
source/startup, and rehearse without touching production.

## Acceptance boundary

Implementation, deployment, recovery and provider acceptance remain separate.
After deploying, use the confirmed recovery action, verify the old export remains
abandoned and its URLs available, then import the next genuine scan once. Require
its import/report receipts and verified delivery to all existing destinations.
Preserve all F01–F05 obligations and the full subsequent P1 programme. Do not
repeat the accepted KVK16 timing check or treat monitor health as export proof.


## Refresh after credential recovery

The r14 coordinated release starts from private source
`c349802b51686d649d3beeac43e7ef61b3b7f825`. It preserves the deployed
credential correction and terminal-containment startup reconciliation. The updater
must retain the live protected credential identity and source bindings; archived
pre-rotation seed metadata is not a deployment input. The source policy rejects
the earlier predecessor rather than silently widening the permitted transition.
SQL closeout commit `8de56c762921a23585e368f9c5d342e2dbe47e48` is unchanged.
The previous mirror PR was closed during mirror scrubbing; publish only the
reviewed file delta on the new scrubbed main, never private Git history.
