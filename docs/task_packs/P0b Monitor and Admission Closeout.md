# P0b monitor and saved-admission closeout

## Delivery boundary

This focused release improves diagnosis of startup and recovery checks and adds a
guided terminal decision for saved stats imports that never entered SQL. It is
not completion of P0b. A clear incident list is not proof of import/export health.

## Included acceptance criteria

- Active SQL checks remain waiting in discovery, existing incidents and accepted
  repairs. They do not become a monitor outage solely because the executor is busy.
- Genuine check failures retain bounded call-site frames and stage, without raw
  exception text, source lines, credentials or local variables. Existing incident
  diagnoses survive restart. Repeated identical failure checks do not continually
  increase incident revisions; successful reinspection clears the diagnosis.
- The complete private report includes current-cycle check diagnostics and bounded
  startup observations. Startup deadline expiry drains the worker and reports an
  unconfirmed outcome unless the coroutine supplies a completion result. It never
  starts a duplicate worker or grants permission to replay work.
- Missing first-successor publication is reported as waiting only after the
  protected parent directory passes custody checks. Missing evidence is never
  accepted as a verified start; existing malformed or unprotected files fail closed.
- SQL stage admission recovery shows the original filename, retained input, date,
  rank/seed and configuration comparison in one short decision summary. Full
  settings and links remain available as technical details.
- **Cancel saved import** requires fresh evidence that the original and all
  continuations never entered SQL. It preserves the saved input and refusal history,
  records a fenced permanent decision, and verifies independently after lost replies
  or restart. Other operations' reservations are untouched. Active or SQL-registered
  work cannot use this cancellation. Stale confirmations cannot apply.
- Existing **Cancel unstarted reservation** and **Resume saved SQL stage** remain
  separate decisions. Canceling a reservation alone does not discard a saved input.

## Operator verification after deployment

1. Run `/ops dl_bot_status`, then **Download complete report**. Inspect monitor
   checks and startup observations. A busy check may wait; genuine failures must
   show their stage and bounded diagnostic. Startup observations are not business
   receipts and must not be used to justify replaying an import.
2. For an existing **SQL stage admission recovery** incident, review the identified
   saved input. Resume only if still needed; cancel only if no longer needed. Do not
   create an artificial production failure for this check.
3. If canceling, use **Cancel saved import**, review the summary, then confirm.
   Recheck must show resolved / `saved_stage_cancelled`. The complete report retains
   the original refusal and verified repair action. If evidence changed, reopen
   the incident and review the new diagnosis rather than reusing the old button.
4. Let a normal monitor cycle finish, then export the complete report. Confirm no
   pending action remains for the completed repair and that other live work still
   has its own ownership and outcome. Discord online is separate from fresh
   import/export health evidence.

## Deployment and rollback

No SQL migration, dependencies, activation flags or runtime configuration changes.
Existing ExportPreparation generation JSON and counters and RecoveryIncident
evidence store the new records. Validate their contracts against the SQL repository.
Install the matching updater upgrade before deploying the reviewed private-main
source. The exact eleven-member `monitor_admission_closeout_v1` transition is
required; arbitrary subsets or hash substitutions are refused. Use the normal
protected updater and one coordinated restart. Keep receipts and the old updater.
Rollback must preserve cancellation markers and use a reviewed forward-compatible
package; an old recovery adapter must not reinterpret a cancellation as a refusal.

## Required remaining P0b work

These remain mandatory delivery/acceptance work, not deferred optimisations:

- Genuine configuration/ownership conflicts: show original and installed membership,
  explain the blocking proof, and offer only the verified repair that matches it.
- Interrupted configuration, report and aggregate producers: cover every durable
  admission/execution phase with guided closure, continuation or evidence collection;
  no unknown write may become an age-based release.
- Still-needed historical captures and failed/unknown provider writes: complete
  replacement/delivery/retirement decisions with original input and configuration,
  independent verification, restart/lost-reply handling and ownership preservation.
- Rollover and cross-workflow held access: close the coverage matrix with executable
  guided actions for recoverable cases and actionable evidence collection for cases
  requiring admin verification, rather than manual SQL recipes.
- Final P0 acceptance: all supported failure families exercised, reports complete,
  notifications bounded, natural admission and provider outcomes independently
  verified. A successful startup or zero current incidents is insufficient.

## Validation and review

Targeted tests cover cancellation, lost acknowledgement, restart, mutated evidence,
active execution refusal, unchanged foreign ownership, private diagnostic persistence,
deadline drain and protected publication waiting. Full-suite, architecture, deferred
item, test selection, security-routing, smoke and command-registration results are
retained in release evidence. Codex Security uses **Changes**, the exact base/head
of each Git history, with Deep scan off. No repository-wide scan is this release gate.
