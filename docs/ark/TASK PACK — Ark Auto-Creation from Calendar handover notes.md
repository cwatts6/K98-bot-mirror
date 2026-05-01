# Handover Pack

## 1) Final delivered ownership model

### Source calendar data
Ark auto-create now reads from SQL `dbo.EventInstances` only.

### Match source of truth
Ark runtime match state remains SQL-backed on `dbo.ArkMatches`.

### Lifecycle coordinator
`ArkRegistrationController.ensure_registration_message(...)` remains the required entry point for
initial registration message creation after auto-create.

### Scheduler role
`ark/ark_scheduler.py` now owns Ark auto-create orchestration as part of the existing Ark scheduler
loop, alongside the previously-delivered visibility refresh / reminder responsibilities.

---

## 2) What was delivered

### A) New Ark auto-create service
A new service was added to:

- scan Ark `EventInstances`
- parse title fields
- derive `ArkWeekendDate` from `EndUTC`
- skip invalid, duplicate, or cancelled-existing matches
- create missing `ArkMatches`
- invoke registration lifecycle immediately

### B) SQL lineage on ArkMatches
Ark match lineage fields were added to the delivery model:

- `CalendarInstanceId`
- `CreatedSource`

This allows production operators and later tasks to distinguish:

- manual match creation
- calendar auto-creation

without forking the Ark runtime model.

### C) Manual create alignment
Manual `/ark_create_match` now stamps `CreatedSource = 'manual'` so both creation paths share the
same lineage contract.

### D) Scheduler integration
Auto-create runs from Ark scheduler ownership rather than a separate framework.

### E) Repost regression alignment
`upsert_registration_message(...)` force-repost logic was also aligned with the shared expected
contract during follow-up review hardening.

---

## 3) Confirmed business rules now baked into the implementation

### Match uniqueness
Only one Ark match is allowed for the same:

- `Alliance`
- `ArkWeekendDate`

Multiple Ark events in a weekend are only valid when they are for different alliances.

### Calendar instance stability
`EventInstances.InstanceID` is treated as stable and is persisted for lineage.

### Cancel priority
If an existing Ark match for the same alliance/weekend is already `Cancelled`, scheduler auto-create
must skip it and must not reopen it.

### Weekend date derivation
`ArkWeekendDate` is derived from `EventInstances.EndUTC`.

---

## 4) Variance from original scope

### A) Stronger lineage was added
The original task asked for assessment of lineage fields.

The final delivery includes lineage directly instead of postponing it.

### B) SQL schema artifact is local handoff-style
The schema migration artifact exists in this repo so deployment requirements are explicit.

### C) Query window is implementation-defined
The auto-create service uses a practical scheduler query window for resilience to reruns and brief
scheduler downtime rather than a single-point-in-time query.

---

## 5) What Task 4 and later tasks should assume now

Subsequent Ark tasks should assume:

- manual and auto-created matches are both first-class `ArkMatches` rows
- registration creation must continue to go through `ArkRegistrationController.ensure_registration_message(...)`
- auto-create must not be bypassed by new direct Discord post logic
- cancel flows remain shared and source-agnostic
- lineage is available on ArkMatches for support, audit context, and future admin UX

For future preference / drafting / confirm-publish work this means:

- operate on `MatchId`
- do not branch business logic purely on manual vs auto source unless the feature explicitly needs it
- use lineage for diagnostics and operator context, not as the core behavior split

---

## 6) Remaining work for this task

If code review is accepted, remaining work is essentially operational:

1. apply the ArkMatches lineage schema update in the target SQL environment
2. perform production-like smoke validation of:
   - auto-create
   - registration creation
   - duplicate prevention
   - cancelled-match skip behavior

No further core implementation work is expected for Task 3.

---

## 7) Suggested smoke validation

### SQL / creation
- confirm a future Ark `EventInstances` row exists
- run scheduler
- verify a new `ArkMatches` row is created once
- verify `CalendarInstanceId` and `CreatedSource='calendar_auto'`

### Discord lifecycle
- verify registration message created in the correct registration channel
- verify later scheduler rerun does not duplicate the Ark match

### Cancel compatibility
- cancel the auto-created match manually
- rerun scheduler
- verify the cancelled row is skipped and not reopened

---

## 8) Key risk notes for future work

### A) Do not reintroduce JSON runtime ownership
JSON remains fallback-only in Ark registration state paths.

### B) Do not bypass scheduler/controller separation
Scheduler should remain thin; service/controller layers should own behavior.

### C) Do not weaken the alliance/weekend uniqueness rule accidentally
Later features should not create second same-alliance same-weekend Ark matches unless the product
rule changes explicitly.
