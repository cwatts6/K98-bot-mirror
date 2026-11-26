# P02 verification catalog cost and cleanup correction

## Scope and diagnosis

Approved: implement, test, review and merge mirror first, then the identical
private patch after green gates. MINI_AMD remains running. Preserve both failed
releases, every original receipt, verifier packet and refusal. No restart,
release replay, recovery, provider probe, SQL migration or VM action is included.
This follows the [rotation correction](P02%20-%20Rotated%20Startup%20Verification%20-%202026-11-19.md).

The rotation-aware reader successfully recovered the pinned startup interval.
The subsequent standalone SQL attempt refused with OperationalError and no
statement identity. Its exact failing statement is therefore still unknown.
Manual application-scope diagnostics independently reproduced HYT00 at the
three-second driver bound in detailed foreign keys, foreign-key identity and
key-constraint identity. The original column query completed but had little
timing margin. Export and legacy read groups completed. These observations do
not establish the cancelled attempt's execution plan or blocking owner.

Four manually tested candidate queries then completed all 23 application and
lifecycle reads in 10.016 seconds (11.109 seconds for the diagnostic). All seven
baseline comparisons passed, retaining exactly the two already approved deferred
KVK index projections. Column candidate and original returned identical ordered
bytes across 4,999 rows. This is one unlocked native observation, not a benchmark,
consistent snapshot, proof of non-interference or production acceptance.

The separate precondition diagnostic falsely required XACT_STATE() = 0. Its
observed transaction count 0 / state 1 failed that invented requirement, while
NoLock / NoLock / READ COMMITTED satisfied the actual schema guard. Retain that
failed diagnostic as evidence; do not introduce its assertion into the verifier.
No lock was acquired by that diagnostic and no transaction repair is warranted.

Offline reproduction also found that an exhausted observation budget blocked
the required schema-lock release. This is a demonstrated code defect, not an
observed explanation of the production refusal. The three-second standalone
budget and delayed/full-scope verification cases were not adequately qualified
when the earlier verifier reused the contract readers. Keep that programme gap
explicit; do not close it merely because a rewritten query is faster once.

## Correction and boundaries

Materialize the pinned object scope once per affected statement. Retain the
foreign-key and key-constraint SELECTs, joins, columns and ordering. Columns use
joined object/schema names with the same catalog fields and binary ordering.
The four statements exactly match the manually observed candidates. Fixed
export and unscoped application reads retain their existing SQL. No expected
contract, fingerprint, permission, maintenance projection or retention comparison
is relaxed. Existing scoped application callers share the corrected reader.

The standalone connection owner keeps three-second driver calls, zero lock wait,
45-second observation admission and 256 normal statements. An explicit cleanup
method can perform only the fixed schema release, once, after that cursor has
acknowledged acquisition. It remains available after observation expiry. Lost
acquisition or release acknowledgements retain custody and refuse acceptance;
there is no guessed release, repeated close or retry. Ordinary runtime cursors
keep their existing release path. Fetch and final checks refuse expired reads.

Receipts add bounded phase, ordinal, SQL digest, execute/fetch client timings and
sanitized SQLSTATE/native codes. Preserve first failure separately from final
cleanup uncertainty. They contain no SQL text, parameters or driver prose.
The sealed contract archive carries the corrected reader and cleanup adapter;
the running bot's source and startup policy are not replaced. Append one exact
source transition for future normal updates, preserving all 94 historical
families. A source merge does not authorize a normal updater run.

The schema observation still briefly owns an Exclusive session application lock.
Publishers use Shared transaction ownership on the same resource. Zero wait
avoids queueing the verifier, but does not prove that publishers cannot defer
while it observes. Keep that limitation and require acknowledged release.

## Validation and release handoff

Regression gates cover native candidate digests, parameterized dispatch,
unscoped/export compatibility, deadline and statement exhaustion while locked,
late acquisition acknowledgement, fetch expiry, unknown acquisition/release,
single cleanup, first-failure retention and redaction. Existing contract,
archive, identity, retained-work, rotated-log and PowerShell 5.1 packet fixtures
remain required. Include updater transition/inventory, architecture, deferred,
security-routing, test selection, imports, SQL identifiers, registration, lint,
formatting and log hygiene. Preserve failed local test results separately from
corrected runs. Run the full suite locally before mirror merge: the mirror has
only a path-filtered command-governance workflow for this source snapshot.
Require all configured hosted checks and hosted reviews on each final head,
including the private repository's full Quality workflow before private merge.

Security review: Changes, Deep off, immutable mirror and private ranges. The
embedded SQL and file/receipt boundaries are in the Bot review. The authoritative
SQL repository has no changes; no separate SQL diff or deployment is required.

1. Complete mirror review/checks and merge. Promote the same patch onto private
   main; compare changed blobs and complete private review/checks before merging.
2. Build a separately named version-2 verifier from merged private source and
   the reviewed profile. Preserve previous packets and receipts unchanged.
3. Review fresh passive source/receipt/process identities before handing over
   the exact new script and hash. Do not invoke Update-K98 or graceful_restart.
4. The operator performs one bounded verification only after that checkpoint.
   Review pending/refused/accepted evidence before any further action. Do not
   replay failures or raise limits to manufacture acceptance. Online Discord
   status alone does not certify SQL contracts or import/export/provider work.

## Preserved programme accounting

Setup 400; native 563 (grouped 389); Windows 42 (grouped 13); control 0; reserve
32; insertion intents 7; generated reserved 91,244, remaining 908,756; historical
rows 95, inputs 21. Offline tests neither consume nor refund these. E1 closed,
E2 retained, E2-E4 paused; three activation flags unchanged. P02 D7, P03 blockers,
essential P04 corrections, P05 acceptance, P01.4/5 natural checks, P03a.2 whole-flow
acceptance and P0 remain open.
