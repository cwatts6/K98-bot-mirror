# Handover Pack

## 1) Final delivered ownership model

### Preference source of truth
Ark team preferences are now SQL-backed on `dbo.ArkTeamPreferences`.

### Scope of preference state
Preferences are stored globally by `GovernorID`, not by `MatchId` and not by specific Ark weekend.

### Validation source
Governor validation reuses the existing SQL-backed governor cache path already used elsewhere in the
Ark subsystem.

### Lifecycle separation
The preference system is intentionally independent from Ark match lifecycle ownership on
`dbo.ArkMatches`.

---

## 2) What was delivered

### A) New Ark preference service
A new service was added at:

- `ark/ark_preference_service.py`

Responsibilities delivered:

- validate `GovernorID`
- normalize preferred team input
- create/update/reactivate preferences
- soft-clear preferences
- retrieve single preference
- retrieve bulk active preferences
- log mutations and invalid attempts

### B) DAL extensions
The Ark DAL now includes SQL helpers for preference persistence:

- `upsert_team_preference(...)`
- `get_team_preference(...)`
- `list_active_team_preferences(...)`
- `clear_team_preference(...)`

### C) Admin command support
Leadership/admin command support was added in `commands/ark_cmds.py`:

- `/ark_set_preference`
- `/ark_clear_preference`

### D) SQL schema delivery
A table contract was delivered for:

- `dbo.ArkTeamPreferences`

with active-state indexing for bulk lookup support.

### E) Test coverage
Focused tests were added for:

- service validation
- create/update/clear behavior
- bulk lookup shape
- command-name presence

---

## 3) Confirmed business rules now baked into the implementation

### Preferences are global, not per match
A governor has at most one preference row, keyed by `GovernorID`.

### Preferences are best effort
The preference expresses a desired draft team, not a guaranteed assignment.

### Soft delete is the removal model
Clear operations set `IsActive = 0` instead of deleting the row.

### Unknown governors must be rejected
Preference writes must only be allowed for governors that resolve via the shared governor data path.

### Team values are constrained
Only team values `1` and `2` are considered valid.

---

## 4) Variance from original scope

### A) SQL schema artifact is local handoff-style
The schema artifact exists in this repo under `sql_schema/` so the delivery contract is explicit,
even though canonical schema ownership still belongs in the SQL Server repo.

### B) Command test was made encoding-safe
The command presence test now reads the source file using explicit UTF-8 so it is stable on Windows
hosts where the default text encoding is not UTF-8.

### C) Test compatibility shim added for `datetime.UTC`
A small compatibility shim was used in tests for environments that do not expose `datetime.UTC`
by default.

---

## 5) What Task 5 should assume now

Task 5 — Draft Allocation Engine should assume:

- preference data lives in `dbo.ArkTeamPreferences`
- only active rows (`IsActive = 1`) should influence drafting
- preferences are not match-scoped and should be applied as global defaults
- drafting should consume preferences via service/DAL access rather than reimplementing SQL
- preference-first assignment must still allow balancing logic to override when needed
- Ark match source-of-truth remains `dbo.ArkMatches`
- drafting must continue to operate on `MatchId`
- business logic must not split on manual vs calendar-auto-created match unless explicitly required

Recommended preference input contract for Task 5:

- call `get_all_active_preferences()` once per draft build
- treat the result as a `GovernorID -> PreferredTeam` map
- apply preference-first allocation before balancing remaining players

---

## 6) Current status / remaining work

Core implementation is complete.

Per latest follow-up status:

- SQL has been deployed
- automated pytest coverage is passing

Remaining work is operational:

1. deploy the bot code to the runtime environment
2. restart the bot
3. execute Discord smoke tests for the new commands
4. confirm command registration and permissions in the intended guild/channel

No additional core implementation is required for Task 4 unless smoke testing reveals an issue.

---

## 7) Suggested Discord smoke validation

### Command success path
- run `/ark_set_preference` for a known governor with team `1`
- confirm success response
- verify row exists and is active in SQL

### Update path
- rerun `/ark_set_preference` for the same governor with team `2`
- verify the same row is updated rather than duplicated

### Clear path
- run `/ark_clear_preference`
- verify the row remains present but `IsActive = 0`

### Validation path
- run `/ark_set_preference` with an invalid governor ID
- confirm a clear rejection message is returned

### Integration safety
- confirm no effect on Ark match creation, registration posting, or reminder flows

---

## 8) Key risk notes for Task 5

### A) Do not couple preferences to ArkMatches lifecycle
Preferences should remain global defaults; do not create per-match preference rows unless scope is
explicitly changed.

### B) Do not duplicate governor validation logic
Continue to reuse the shared governor cache/data path.

### C) Do not treat preference as hard assignment
Balancing logic must still be allowed to override preference-first allocation when needed.

### D) Do not branch on manual vs auto-created match source
Task 3 established shared Ark match ownership on `ArkMatches`; keep drafting source-agnostic.
