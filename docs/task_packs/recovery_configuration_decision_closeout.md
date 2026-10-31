# Configuration read decision closeout

## Scope and problem

A typed configuration import withdrawn before read admission already has a guided
continuation owner. After an admin keeps the prior configuration, that owner can
verify the decision while the older configuration-read and queue incidents still
ask the private authority about reservation membership. This incorrectly presents
an empty withdrawn reservation set as a mismatch with installed configuration.

Route these two views to the typed continuation. Routing is not proof: the owning
DAL must freshly verify the exact original request, withdrawal fence, absence of
execution/ownership, and complete durable decision. Existing incident status is
never evidence. No provider call, new approval, configuration publication or
reservation release is introduced.

## Acceptance and guided verification

- Before a decision, both views stay open and link to the one existing guided
  configuration decision, including original input and configuration information.
- After a verified keep-prior decision, both close on Recheck or monitor refresh,
  including after restart. The report retains the original read identity and
  explicitly says no fresh publication or cache refresh is certified.
- A valid child continuation keeps its existing owning-domain verification.
- Changed hashes/fences, incomplete decisions and unavailable verification cannot
  close the incident. Reads with execution/membership still require authority.
- Untyped historical reads retain their existing guided queue closeout.
- No schema, installed updater or authority-policy change is required.

## Validation and review

Use disposable SQL tests for configuration-read continuation, configuration
continuation, queue admission and recovery monitor regressions. Check Ruff,
architecture, deferred items, test selection, security routing, smoke imports and
command registration. SQL objects are unchanged; validate the existing fixture
contracts against the SQL source repository and deployed recovery schema.

Security routing: Changes scan for the immutable mirror and production diffs;
Deep off. Review decision proof, domain routing and scope boundaries.

## Remaining mandatory P0b scope

The current captured outputs still need their guided keep/queue decisions. Genuine
configuration membership conflicts, exhausted admission recovery, monitor
diagnostics, still-needed outputs, unknown-write replacement and remaining
producer/rollover recovery workflows are not waived by closing these duplicate
views. This is an interim fix, not completion of P0b.
