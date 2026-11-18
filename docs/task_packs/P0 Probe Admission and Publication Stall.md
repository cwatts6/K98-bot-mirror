# P0 probe admission and publication stall

## Scope

The operator approved implementation, disposable validation and focused release
packages. This change prevents a confirmed provider-stream admission refusal from
leaving an unused configuration/health-probe ticket in the account queue. It does
not merge, deploy or perform a production repair.

The publication-check stall remains a required P0-F01/F05 task. The supplied logs
show prolonged authority unavailability during publication checking, followed by
recovery. They do not establish whether historical journal verification, provider
pacing, provider execution or another authority operation caused the delay.
Do not repeat the production check merely to reproduce that failure.

## Root cause and change

The locked execution gate previously raised the same generic conflict used for
unattributed or uncertain failures. This escaped the ordinary admission-refusal
path before it could withdraw the never-started health ticket.

The execution gate now distinguishes a successfully observed active provider
stream. Preparation admission returns its ordinary refused result only for that
typed condition, before changing resource ownership. The transaction must finish
successfully before the caller can withdraw its own unused ticket. Query failures,
lost commit acknowledgements and other conflicts still propagate uncertainty.
Settlement/release callers continue to reject an active stream.

Existing guided queue recovery remains available for already stranded tickets.
This preventive change does not infer that old tickets are safe to withdraw.
No age-based expiry, generic exception cleanup, foreign release or write replay
is introduced.

## Layers and contracts

- DAL: typed locked stream observation and refused preparation admission.
- Existing service: exact unstarted-ticket withdrawal; no new UI decision.
- Updater: one complete two-member transition with exact predecessor/target hashes.
- SQL: no migration or permission change. Validate against the authoritative SQL
  repository's reviewed `b663308a` schema used by the installed release profile.

## Required acceptance

1. A health read encountering an active provider stream executes no provider
   request, withdraws only its own never-started ticket, and preserves that stream.
2. Lost transaction acknowledgement and generic conflicts do not trigger withdrawal.
3. Other gate consumers still refuse release while a provider stream is active.
4. Real temporary SQL reproduces the complete refused admission/withdrawal path.
5. The protected updater refuses incomplete or unrelated runtime bundles.
6. Focused tests, project gates, Changes security review (Deep off), exact
   mirror/private promotion parity and protected package rehearsal precede handoff.

## Operator verification

After the reviewed package and normal protected deployment, run `/ops dl_bot_status`.
An ordinary busy account may defer a probe; it must not gain a pending unused
configuration ticket merely because another provider stream was observed.
Use **Review queue blockers** and **Download complete report** to confirm the
queue state. Existing uncertain operations retain their own guided checks.
Do not create a production failure or replay publication to test this fix.

The separate read-only historical publication trace collects bounded stream,
request, proof and recovery-action timestamps. It does not include provider
contents, execute business procedures, contact Google or authorize a repair.
Use its evidence to finish the publication stall fix rather than widening
timeouts or treating stale monitoring as healthy.

## Remaining P0

`P0 Final Recovery Acceptance.md` remains authoritative. Publication verification,
lost-evidence/ownership workflows, interrupted producer/pipeline stages, rollover
qualification and final cross-workflow acceptance all remain mandatory. This
focused preventive release does not complete P0 or move any item to P1.
