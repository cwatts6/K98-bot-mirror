# D5c replacement action consumers

Prior publication-proof acceptance: 54/73 offline action routes; 19 remain.
This packet exercises six shared action consumers for both job and rollover routes:
isolate, propose, admit verification, finish, discard, activate. Twelve route entries
share six implementations; repeated family cases are not independent branch coverage.

Run one bounded offline pass after the five-file Changes review (Deep off), using
the preserved isolated runner. 143 checks: 136 behavioral cases and seven controls.
300 seconds and 1 MiB combined intent/result. Stop at first failure, preserve every
artifact, correct under a new identity if needed. Existing operator approval covers
corrections and further offline runs. No external input, SQL, native VM, provider,
production modification or permission change is included.

Original action implementations are loaded verbatim. Assertions cover exact action
identity, stale decisions, private receipt readback before persistence, original
verification admission and duplicate suppression, explicit discard, activation
prerequisites and lost acknowledgements. The verification snapshot association and
readback checks are original. The scheduler is synchronous and inert.

Limits: prerequisite containment inspection, registration projection/owners,
proposal verification, activation post-verification, protected plan construction,
private journal eligibility and persistence are modeled seams. Real provider reads,
SQL transactions/CAS/constraints, concurrency, physical storage and complete native
workflow are not proved. Injected persistence failures do not prove rollback.
Verification worker errors preserve an admitted checking state without redispatch;
the worker itself is not exercised. No result certifies business completion.

Route acceptance is limited to these original offline consuming bodies together
with earlier adapter safeguard coverage. It does not close native C04/C05/C06.
If accepted: 66/73 offline action routes, seven remaining.

Preserve 1,260 native seconds, 1,000-second later-stage reserve, 50 Windows-test
seconds, 21 consumed inputs, zero new inputs, 11/64 synthetic rows and all failures.
Production code and the normal Git index/HEAD remain unchanged. SQL definitions
are pinned read-only. No PR/promotion handoff: architecture/deferred/test-selector
and security-routing repository gates are deferred to that separate handoff;
focused guarded execution and frozen Changes review are this packet's gates.
