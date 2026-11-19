# P02 native qualification acceptance and release handoff

## Decision

The remaining grouped native qualification is accepted from the preserved case
receipts plus the successful completion-only run. This closes the native lab
gate; it does not mark production ready, D7 complete, or provider delivery proved.
No VM or production action was performed during this offline adjudication.

The original failed aggregate-summary receipt remains failed and unchanged.
The completion collector correctly left QualificationAccepted false for this
independent review. Acceptance is recorded separately, never by editing receipts.

## Evidence

All paths below are under `.codex_artifacts/p02-native-qualification/`.

| Record | SHA256 |
| --- | --- |
| Qualification-Completion-v1/run-01/result.json | 66bccd4f681147f00b4e13c2b6d1b1b1ad9175c7fd51f8e6cebecfdc59c4004a |
| Qualification-Completion-v1/adjudication-01.json | 10a971d8fe864f216aa8038a3d14441650ac11cf4684c3b827b2ae1ca55e251a |
| Restored-Qualification-v1/run-01/result.json (preserved failure) | 32c5339828bd92e9fbbebd950259ed6501277a17bda7d77c46216ea46986e926 |
| Restored-Verify-v2/adjudication-01.json (reused acceptance) | ae360da5923839f472477ea25c25fafc5b4f7a1b59386ca9409cade2091c0054 |

The offline adjudicator verified 15 packet members and 58 bundle members across
the original and completion runs. It reapplied the actual contract comparator
to four retained observation groups and the fresh three-contract verification.
It checked digests, process retirement and successful exits, final source and
resource comparisons, both captured files, and accounting. Historical record
preservation is attested by the pinned final checker against its retained
in-memory baseline; it is not presented as a second independent raw-history diff.

## What the evidence proves

- Real atomic publication and capture succeeded with deferred indexes. The
  strict policy refused the same valid deferred state; the corrected policy
  accepted it, while missing integration evidence still caused refusal.
- Both shared-helper transaction states are covered by the earlier accepted
  native verification. Snapshot refusal preserved the caller transaction.
- The exact schema guard excluded an observer, and the real maintenance worker
  separately completed KVK16 generation 2. These are separate proofs, not a claim
  of simultaneous real-worker/observer overlap.
- Lost acquisition and release acknowledgements closed SQL admission and retained
  custody without close, commit or rollback. Exact fault connections were closed
  through the reviewed lab procedure.
- A distinct subsequent writer completed and the first capture remained intact.
  Both capture files were independently hashed (145,917 bytes each).
- Fresh verification passed all three contracts. Final source facts and unrelated
  resources matched; expected delta outcomes and capture metadata matched.
  The failed child was retired, verifier and administrator exited successfully,
  and the administrator connection closed.

Lab Windows administrator privileges and the accepted lab migration-history
projection are not production policy. SQL/startup contract verification is not
a full Discord startup, fresh scan import or provider delivery acceptance run.

## Preserved accounting

Completion charged setup 2 and native 23, with zero Windows fault seconds,
control attempts or generated rows. All earlier failures remain charged. No refund
is taken from the prior 32-control reservation despite seven observed insertion
intents. Generated reservation remains 91,244; historical 95 rows and 21 inputs
remain consumed.

Remaining: setup 400; native 563 (grouped 389); Windows fault 42 (grouped 13);
control attempts 0; generated rows 908,756. These balances are not permission
for another run. No additional lab run is needed for this qualification gate.

## Concrete release handoff

GitHub was read during this review: mirror PR540 remains open at
`7cd75a5d7d05b167715086b4867fd8ccc510a9ce`; private PR745 remains open at
`2c2da85dfc8044b0f11cf86deee24579d21ab021`. Neither is merged. Their earlier
heads do not contain the locally corrected shared transaction-state helper.
Do not deploy those earlier heads as if they were the qualified candidate.

1. Finish source delivery of the reviewed corrections: reconcile the qualified
   helper and SQL inventory changes with the mirror/private PRs, updater source
   transitions and tests. Preserve historical transition hashes; bind new source
   identities through the supported transition process. Include the acceptance
   record and relevant regression coverage. Recheck the final diff, review
   dispositions and hosted checks before the already-authorized source merges.
2. Pin the exact private main merge SHA and updater package. The qualified helper
   SHA256 is `1e87fba0ab8b6d35311799dd00b8ce66d9925a950cf3a516c526ee2770c99260`.
   Compare the final candidate with qualified source and assess any differences;
   do not infer equivalence from a branch name.
3. Prepare the fresh MINI_AMD read-only readiness packet for that release,
   including installed updater identity, source/seed/SQL identities, retained
   ownership and changed paths/ancestor permissions. Historical host evidence is
   reusable context, not fresh readiness. No production credential or connection
   policy is inherited from the lab.
4. After readiness review, upgrade the updater and deploy through its normal
   prompted restart flow. Review deployment receipts before separately resuming
   E2-E4. A later normal acceptance run uses fresh user-generated input through
   Discord and the standard registered destinations.

No collector rerun, restoration, migration replay or recovery is part of this
handoff. Existing accepted evidence, failed reviews and allowances stay intact.
