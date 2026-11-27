# P03a pre-incarnation startup correction

This bounded recovery handles the P03a.2 issuer evidence-custody failure at
private target `3d702510229460f740d66708fe64e00959f54838`. It is not a general
restart, rollback or uncertain-work retry. The ordinary updater deliberately
refuses to repeat a start whose outcome is unconfirmed.

## Preconditions and ownership

The operator supplies a generated, independently hashed package on MINI_AMD,
using elevated Windows PowerShell 5.1 under the existing deployment account.
The packager binds the exact original release, work directory, manifest,
bindings, five original receipt hashes, original start request, installed source
adapter and corrected private-main target. All paths and identifiers are bounded.

Before any source change, the recovery rechecks the retained original drain,
native PID/birth identities, closed prior SQL session/version, retained claims,
absence of provider streams and absence of any open authority session. It also
requires empty failed-incarnation history and no remaining Python/bot/startup
process. A refusal preserves everything and requires evidence review.

The script holds the existing operator/release locks, disables the exact reviewed
scheduled task and acquires the same host startup mutex. An abandoned mutex is
not outcome proof: the fresh native/SQL/ownership checks still run after acquisition.
The task remains disabled on a failure before the new start.

## Separate correction, immutable original

`scripts/package_k98_startup_correction.py` embeds the validated profile, the
reviewed tool payload and `prepare_k98_startup_correction.py` into the fixed
`Recover-K98StartupEvidence.ps1` template. It also builds the subsequent normal
updater upgrade pair against the retained installed-tool manifest.

`Inspect` performs bounded checks and returns `STARTUP_CORRECTION_REVIEW_READY`.
It takes existing coordination locks but does not install, disable, start or
change production files. For an already-selected correction it reports that
selection without claiming current startup readiness.

`Apply` creates a protected correction directory and authenticates the exact
private-main target. It uses the normal preparer to derive an unused candidate,
then writes a separate packet with these reviewed adjustments:

- Preserve the original release ID for its actual drain/ownership lineage.
- Preserve the last actual predecessor policy/journal/session. The failed empty
  history never becomes an invented predecessor incarnation.
- Use a fresh successor seed/history and the exact corrected issuer hash.
- Preserve activation flags, SQL contracts and original historical observations.
- Use a separate recovery backup ref; retain the original before-update ref.
- Record correction source/seed/start/readiness intents and receipts separately.

An amendment-selection marker prevents the old runner from resuming its superseded
failed start. Original bindings, source/seed receipts, start intent and failed
history remain unchanged. There is no ACL widening, forced session/claim closure,
provider replay or SQL migration.

Source custody uses the same bounded existing-file preparation as normal updater
preflight, after drain/exclusion and before source intent. Source and seed then
use the existing pinned adapter's verifiers and continuation rules.

Immediately before the one new start, the recovery repeats the quiet-state checks
and releases its startup mutex. The scheduled task and operator lock still exclude
cooperating deployment callers; the issuer takes its normal startup mutex. A saved
start intent never permits another `ApplyStart`. A resumed command verifies the
existing result and either completes bookkeeping or refuses.

Only verified source, seed, native/SQL successor and Discord startup readiness
permit a separate `STARTUP_CORRECTION_VERIFIED` closeout and removal of the exact
old active-update pointer. It does not write a false success receipt for the failed
original release. `provider_delivery_verified` remains false.

## Qualification and remaining acceptance

`tests/test_startup_correction.py` exercises exact-profile rejection, complete
normal packet generation/lineage transformation, unchanged original inputs,
Windows PowerShell 5.1 parsing, whole Inspect and Apply/resume paths, uncertain
start refusal, source uncertainty and delayed readiness. Native named-mutex
contention and abandonment run with an explicit surrogate account/local namespace.

The full-orchestrator fixtures substitute SQL/task/source-adapter and filesystem
custody boundaries. They prove orchestration/receipt behavior, not an elevated
MINI_AMD rehearsal. Existing source/seed adapter and native custody tests remain
required. The corrected issuer has its own real ACL-guard regression coverage.

Production acceptance requires the exact generated package's Inspect and Apply
outputs, verified closeout and the current bot startup evidence. Fresh P03a.2
business behavior and provider delivery require their own evidence. Never restart
or repeat an import/export merely to refresh acceptance evidence.

## Interruption boundary

Keep the package, transcript and all retained directories. The same Apply command
verifies completed stages and resumes only the adapter's proven safe continuation.
An uncertain source apply before the target commit, or any unconfirmed start after
intent, deliberately stops for reconciliation. Do not delete intents, amend hashes,
run the scheduled task manually, reset Git or rerun the old deployment packet.

The operator handoff must provide actual merged target/package hashes and
copy-and-paste commands; this protocol document alone is not an executable packet.
