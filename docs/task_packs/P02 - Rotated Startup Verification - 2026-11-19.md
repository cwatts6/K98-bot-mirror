# P02 verification after startup-log rotation

## Scope and retained failure

Approved: offline implementation, tests, reviews and mirror-first then identical
private promotion once green. Keep MINI_AMD running. No restart, release replay,
recovery, provider probe, VM action or SQL migration. Preserve both failed
releases, original receipts and the first verifier packet/refusal. This extends
the [running-release verification contract](P02%20-%20Running%20Release%20Verification%20-%202026-11-18.md).

The first standalone attempt matched original receipts/process identities, then
refused because current log length was below the saved startup offset. It stopped
before SQL verification and acceptance. The supplied archive contains the exact
successor admission, login and completed startup. Its tail plus the supplied
current log contain 807,967 bytes, including four ObservationBusy warnings. This
is historical evidence, not fresh SQL, process or provider acceptance.

## Cause and programme learning

This was a missed delayed-verification case. Private history dates current-log
selection to fb9f6646 (9 October); admission reader ea50db82 (18 November) also
used current log plus saved offset. Standalone correction 541f7000 reused that
assumption without testing overnight rotation. The logger already rotated;
rotation was not introduced here. The scrubbed mirror snapshot cannot establish
these origins. Refusal prevented unsupported acceptance, but the missed case
created another operator blocker. It does not establish a new bot failure.

Add delayed verification, generation identity, rotation while reading, later
negative evidence and pre-SQL failure retention to the regression contract. The
ordinary updater keeps its current-log refusal: this patch supports only the
separate verifier. Do not infer rotated-log support or replay authority for the
ordinary updater. Exclusive SQL observer contention remains separately open;
the original refusal does not prove the holder. Supplied gateway lag, missing
board warnings and long monitoring cycles are also not closed by this correction.

## Design and limits

Profile version 2 pins reviewed generation SHA256, byte length and original
startup offset. A sealed standard-library reader serves PowerShell readiness and
Python admission. Inspect only log.txt and at most five numbered predecessors,
stopping at the exact hash anchor. Every newer suffix must exist. Timestamps or
length alone never select the start generation. Read its tail, then every newer
generation in order. Preserve later explicit admission failures and unknown
coordinator errors; exact ObservationBusy remains degraded. The same packet's
admission parser requires exactly one matching PID/birth/manifest success, also
at the final PowerShell boundary.

Each capture has an 8 MiB aggregate read budget, including full-generation hashes
and the current-prefix recheck. Five suffixes is a name limit, not a promise five
full logs fit. Missing/aged-out anchors, overflow, partial records, invalid UTF-8,
links/reparse objects, changed native identity, archive mutation or rewritten
current prefix refuse without retry. Read handles share read/write/delete so they
do not prevent logger rotation. Rotation during capture invalidates observation.
Appends beyond the captured boundary are allowed; subsequent captures include
them. This is bounded observation, not an atomic snapshot of future output.

All existing protected custody, source, native process, journal, SQL contracts,
retained ownership and cleanup checks remain. Capture before/after SQL and at the
final wrapper check. Compact startup-observation receipts retain identities,
hashes, bounds and failures without raw log text. Acceptance links its final
observation hash. Original stage receipts stay unchanged and provider delivery
remains unverified. No installed source, updater, task or old packet is replaced.

## Validation and delivery

Tests cover no/one/multiple rotations, missing/wrong anchors, gaps, incomplete
records, invalid UTF-8, rewriting, Windows share-delete rotation, archive changes,
hardlinks, strict profile types and aggregate read limits. Cover old-runtime
exclusions, later failure, duplicate/wrong admission and failure after SQL.
Exercise the isolated reader with real admission parsing, PowerShell 5.1 result
validation/receipt retention and complete generated-packet parsing. Private log
replay is offline only; logs and profiles never enter Git. Preserve intermediate
test failures separately from passing reruns.

Include installed-contract archive, admission, reader-registry and inventory
regressions, architecture/deferred/security-routing/selector checks, imports,
command registration, formatting and log hygiene. Require full hosted CI and
completed hosted reviews for each final head. Security: Changes, Deep off,
immutable mirror base/head and corresponding private range. SQL review is a
no-diff skip; no SQL permissions, queries, contracts or migrations change.

1. Review/merge mirror, then apply the same patch onto private main. Verify
   changed blobs and packet dependencies, complete private gates and merge.
2. Build a separately named version-2 delivery from merged private source and
   reviewed anchor/profile; preserve the old delivery unchanged.
3. Review fresh passive custody, process and receipt evidence before supplying
   the exact script/hash for one operator verification. Never invoke the updater
   or graceful restart. Existing approved SQL verification stays single-attempt.
4. Preserve and review any refusal, pending outcome or acceptance before another
   action. Missing history/rotation does not authorize retry, log restoration,
   evidence editing, replay or reduced proof. Promotion is not deployment.

## Preserved programme accounting

Setup 400; native 563 (grouped 389); Windows 42 (grouped 13); control 0; reserve
32; insertion intents 7; generated reserved 91,244, remaining 908,756; historical
rows 95, inputs 21. Offline tests neither consume nor refund these. E1 closed,
E2 retained, E2-E4 paused; three activation flags unchanged. P02 D7, P03 blockers,
essential P04 corrections, P05 acceptance, P01.4/5 natural checks, P03a.2 whole-flow
acceptance and P0 remain open.
