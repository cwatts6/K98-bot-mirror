# P02 D3g — final-report maintenance

Implementation, focused qualification, Bot/SQL mirror PRs and review are authorized
by the continuing D3 instruction. Deployment remains held through D4/D5. No production
SQL, provider activity, restart or retained recovery is authorized by this pack.

## Scope and architecture

Preserve report calculations, stage receipts, completion counters and the eight-column
success result. Preserve pre-admission log checks and their existing checkpoint.
Record dashboard and summary maintenance demand in their respective business
transactions, so a later failed report stage cannot erase an earlier committed intent.
Move the optional dashboard SAMPLE25, summary FULLSCAN and completion checkpoint to
the fixed owned maintenance dispatcher. The report-stage guard takes the existing
shared schema guard, including the legacy entry, before changing outputs.

The existing six-row maintenance ledger gains two final-stage generation pairs.
A separate singleton backup ledger coalesces demand; it does not adopt historical
LogBackupTriggerQueue rows whose attempt outcomes are unproven. It retains exact
claim/generation, first failure and unknown state. The Python maintenance DAL holds
the existing physical session guard through one dispatch and exact acknowledgement.
Physical owner absence marks a lost attempt unknown; neither age nor new demand
authorizes replay. A requested job is not a completed backup.

The UPDATE_ALL2 wrapper stops querying, dispatching or waiting after its final success
receipt. Its existing wait arguments remain accepted for compatibility. The shared
backup helper selects one installed route before dispatch; a lost response never
falls through to a second route or ad-hoc backup. Equivalent background upload
callers share that once-only behavior. Equivalent pre-admission log_health dispatch also uses the one-attempt helper; its thresholds, checks and waits remain unchanged.
The legacy queue processing entry returns held evidence without mutating old rows.

## Validation and review plan

Native disposable database checks cover actual upkeep, transactional demand, schema
ownership in both orders, exact backup claim/ack, newer demand, first failure,
unknown physical absence and refusal to replay. Existing reporting continuation
tests retain real stage guards/receipts and explicitly simulated calculations.
Fake-provider tests cover accepted/unknown/pre-dispatch failure and cleanup custody;
they do not contact SQL Agent or perform a backup. Existing updater families remain
immutable, with an exact new family for changed runtime members. Separate Changes
security reviews for Bot and SQL; Deep off. Full stable Bot tests follow the final
slice. No claim of production scale, permissions or backup completion is made.

## Prior slice closure

D3f Bot PR518 merged at aee7d8826b05b669c0ed987792d0b9533c8598a4;
SQL PR146 at 6504865ec34fe1e3d7567d25aa892f7c811a636d. SQL scan
a39627a5-51bd-4752-8ad1-f5a9ccb28027 covered all eleven paths, zero findings:
1,106,157 total tokens (1,102,486 input; 1,097,344 cached; 3,671 output).
These rollout usage windows overlap other scans and must not be summed as billing.
Bot changes were tests/evidence only with a documented security skip. CI/reviews
passed; 127 combined focused checks and 50 post-format/native-history checks passed.

## Remaining qualification

D4 owns installed/manual/legacy entry alignment, permissions/signatures and the
combined updater jump. The installed msdb backup wrapper has no authoritative
definition in this SQL repository and must be verified before enablement; no body
or permissions are guessed here. Old unprocessed queue rows remain reconciliation
evidence. D5 owns scale/cost/headroom qualification. P03 and essential P04 precede
the first normal import/export. No timeout, backup schedule or safety cap is widened.

## Focused qualification

Twelve actual D3g SQL/DAL ownership tests passed using new disposable local databases;
all backup dispatch was simulated. Thirty-three Python receipt/provider/custody tests
and 133 updater/history checks passed. Reporting continuation selection passed 29
checks (including nine earlier upkeep tests), one unrelated test deselected after
recording its failure: the existing changed-exception-chain test expects only
exception_types/observed_utc to differ, but fingerprint now also differs. No runtime
change or assertion relaxation was made for that unrelated failure. The reporting
fixture's already simulated calculations now also isolate Phase 1 display-name
staging; unchanged actual core compilation and source preservation remain separate.

The D3g updater family contains twelve fixed members, six changed including the new
backup DAL. All prior 86 entries retain digest
49752cc86f05563aeb7b04111c050e2730548e0a32654e757b5b24e7d7991d90.
The 232448-byte cap is unchanged. This does not qualify the combined installed jump.
Architecture, deferred-item and security-routing validators passed. SQL D3 custody,
P0 receipt contracts and retained-business equivalence passed. Final security scans,
stable full-suite result and PR review/merge receipts will be recorded at closure.

## Review correction: backup relief eligibility

Independent SQL review identified backup demand coupled to successful low-log
statistics upkeep. Corrected claim eligibility to committed SummaryDueGeneration,
independent of the unchanged <70 percent statistics gate and upkeep outcome.
The physical guard/claim/ACK, optional queue-presence gate and no-replay rules remain.
The initial full-suite run was stopped at roughly 20 percent before editing; its
partial log is retained and is not acceptance evidence. A new stable run is required.
