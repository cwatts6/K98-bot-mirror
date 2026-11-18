# P02 failed-readiness retirement correction

## Authority and scope

The operator approved implementation, testing, review management and merge of the
mirror first, followed by an equivalent private production patch once all gates
are green. Deployment is a subsequent, operator-guided sequence. This addendum
extends the [admission settlement correction](P02%20-%20Admission%20Settlement%20Correction%20-%202026-11-18.md);
it does not rewrite the earlier evidence or its original approval boundary.

The supplied 18 November host observations show completed source/seed/start
receipts, missing readiness completion, and the matching successor pair still
alive. Task last-result zero establishes launcher exit only. Protected publication
and live native identities do not establish successful bot admission. The current
active release therefore cannot be closed as verified or replayed to make it green.
The existing updater refuses replacement while that active selection remains.

This correction supplies an explicit, exact-profile administrative retirement in
`Upgrade-K98InstalledUpdater.ps1 -RetireFailedReadiness`. It changes release
selection and installs a reviewed updater. It performs no SQL, provider, bot-source,
task, startup-policy, application restart or business-recovery operation.
The existing admission settlement correction remains the application fix.

## Design challenge and resulting contract

Simply moving `active.json` would leave the old staged runner executable. The
legacy runner already refuses `.amendment-selected.json` under its execution lock
before preflight or member copying. Retirement writes this selection barrier first,
with an explicit `failed_readiness_retirement` kind. It is not a successful
amendment or readiness receipt. The new updater and stage adapter also reject
retired selections and cannot infer a successful closeout from them.

The generated helper pins one private profile and one exact old/new updater pair.
The profile binds the host/account, failed release/work directory, retained
failure-evidence digest, active/prepared/manifest/bindings/request/drain/start
digests, six source/seed/start receipts, current journal and first approved private
main target. No operator-authored hash substitutions or generic force switch are
supported. The failure digest anchors the retained private evidence; it is not a
new health observation. Profiles and production identities remain outside Git.

Before retirement the helper requires:

- Exact source-only source/seed/start/readiness release structure and original
  six receipts; no readiness record, verified closeout or new deployment request.
- The reviewed task, seed, policy, unique successor journal, published plan and
  both manifests, plus the issuer's matching publication binding.
- Three distinct live native process handles with matching creation times and
  executable hashes. The same identities must remain live at the write boundaries.
- Installed private main at the failed release's source target, and all current
  runtime source pins. Fixed Git metadata is read directly; no Git worker starts.
- Existing owner/ACL/ancestor policy, native file identity/hard-link and stream
  checks, bounded reads and the operator plus original release execution locks.

The issuer owns its startup mutex while supervising the running pair. Taking that
mutex would incorrectly reject the required live state. This metadata-only operation
instead holds native process handles and rechecks the task/journal/evidence around
publication. This does not establish business quiescence: the fresh release still
uses its normal drain protocol. A changed incarnation requires review, not rebinding
the profile automatically.

The candidate updater is verified before the first retirement write. Publication
order is selection barrier, protected retirement directory/profile/intent, exact
old-tool archive and new-tool installation, atomic move of the original active
record, then `retired_without_verified_readiness` completion. The original release,
failed admission, staged files and receipts are retained. No `verified.json` is
created. The active record's bytes and old updater are preserved independently.

An incomplete retirement blocks routine updating. Only the same reviewed helper
may finish its outstanding administrative writes after rechecking current evidence.
Interruption after any write or either updater move never authorizes release replay.
A completed helper reports historical completion; it is not a current-health check.
Restoring the retired active pointer is rejected. The first fresh target is pinned
to the reviewed correction; later ordinary releases retain their normal policy.

## Validation and review boundary

Tests cover exact profile and package pinning; retained legacy updater inventories;
wrong/missing/advanced receipts; changed task, journal, policy and issuer publication;
native process creation-time mismatch and exit; actual NTFS stream/hard-link
refusal; loose and packed main refs; source-byte changes; immutable writes;
interruptions after each retirement publication and active-record move; interrupted
updater replacement; pending-retirement and wrong-successor refusal; restored
selection and altered completion/barrier records. Legacy runner tests establish
refusal before preflight/copy. The upgrade harness exercises the real orchestration
with effects substituted; the retirement harness performs real fixture file and
native process operations, substituting production ACL ownership for the ordinary
development account. These are offline tests, not production/native-SQL acceptance.

Intermediate failures remain in the additive local validation record: an unsupported
alternate-stream fixture write, a shell test-argument error, fixture-only module
lookup failure, the newly added helper's legacy-inventory compatibility regression,
and an unnecessary parser dependency in the legacy guard. Fixes retain the existing
legacy guard behavior and represent historical inventories without the new helper.
The earlier broad Windows run's 19 unchanged SQL-checkout CRLF reconstruction
failures remain recorded; the SQL checkout and accepted pins are unchanged.

Security routing is **Changes**, Deep off, over the immutable mirror patch and then
the equivalent private patch. These privileged filesystem/deployment changes require
that review, final-head hosted reviews/checks and no unresolved actionable threads
before merge. SQL has no diff and no new contract, so its separate Changes review
is a documented no-diff skip. No full-codebase audit is selected.

Independent review of the first correction commit found a stale consumer inventory:
the new package included the retirement helper but the normal updater still required
13 members. That would fail closed during fresh preparation. The exact consumer now
requires all 14 members; a regression executes its actual PowerShell block against
the generated payload and rejects missing, substituted or changed helper bytes.
The initial 526 passing tests did not cover this consumer; their result and the
review discovery remain retained. Review of the corrected final head is required.

## Release and verification sequence

1. Finish local validation and the mirror's reviews/checks, then merge it. Apply
   only its reviewed file delta onto private main; complete private reviews/checks
   and merge. Preserve the private history and CI configuration.
2. Rebuild the updater from the final reviewed source. Bind the actual installed
   predecessor manifest and the exact approved private-main successor in the private
   retirement profile. Seal a new delivery directory; retain earlier ZIPs as history.
   Verify generated payload hashes and exact source compatibility offline.
3. Review fresh host, task/journal/native identity and retained-release evidence.
   Obtain the required bounded changed-path/ancestor custody evidence. Preserve
   production flags and all accepted receipts. Drift is a stop/review condition.
4. Run the supplied fixed upgrade helper with the explicit retirement switch.
   Review its completion, archived active hash, original receipts/barrier, installed
   updater hash and unchanged runtime identity before continuing. An interruption
   requires evidence review and only the same administrative helper continuation.
5. Run the normal new updater for a **fresh** release from private main. Use the
   existing SQL/disk/log/version-store prerequisites and normal drain/start sequence.
   Request `/ops graceful_restart` only when that fresh release prompts once.
   The lab VM's 8 GiB available-memory gate is not a production prerequisite.
6. Verify the new release's exact source/seed/start/readiness receipts and private
   target; correlate initial admission settlement to its exact new bot incarnation;
   require independent native/source/SQL checks and final readiness. Review the new
   `verified.json` separately from the old retirement record. Discord online alone
   does not close admission or provider acceptance.

On any unexpected result preserve both histories, installed tool/source and runtime
identity. Do not restore the retired pointer, remove its barrier, rerun the failed
release, manufacture readiness, blindly retry a start, or manually pull/repair the
live checkout. Recovery or a new profile requires an evidence-based review.

## Preserved programme accounting

`Qualification-Completion-v1/adjudication-01.json` remains authoritative: setup 400;
native 563 (grouped 389); Windows 42 (grouped 13); control 0; prior control reserve
32; insertion intents 7; generated reserved 91,244 and remaining 908,756;
historical rows 95 and inputs 21. No refund/reset or new qualification charge.
Offline test counts are separate from these allowances.

E1 stays closed; E2 is retained without replay; E2-E4 remain paused. Observed live
activation flags remain unchanged and do not override that programme pause. P02 D7,
P03 actual blockers, essential P04 corrections, P05 combined acceptance, P01.4/5
natural observations, P03a.2 whole-flow acceptance and P0 remain open. Neither
retirement nor a later deployment proves fresh provider delivery or whole-flow
acceptance. Preserve all original failures and accepted allowances.
