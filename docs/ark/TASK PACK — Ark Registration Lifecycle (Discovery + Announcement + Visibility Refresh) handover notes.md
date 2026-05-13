Handover Pack
1) Discovery / Current-State Mapping baseline
Ark modules involved
The Ark registration lifecycle touched these main modules:

commands/ark_cmds.py for create flow and new force-announce command. 

ark/registration_flow.py for lifecycle orchestration, SQL-first state resolution, JSON fallback migration, tracker updates, and announcement control. 

ark/registration_messages.py for Discord message edit/repost/recreate behavior. 

ark/ark_scheduler.py for daily visibility refresh orchestration. 

ark/dal/ark_dal.py for SQL persistence helpers. 

ark/state/ark_state.py for legacy JSON fallback parsing. 

Previous ownership before this task
Before the lifecycle refactor, registration posting ownership was split:

/ark_create_match directly posted the registration message in the command layer,

registration refreshes lived in registration_flow.py,

message refs were operationally tied to JSON,

and the scheduler posted a daily reminder message instead of refreshing the active registration post.
That split is now reduced by routing create/repost/refresh through the controller path. 

2) Final delivered ownership model
Source of truth
For registration lifecycle state, the intended source of truth is now SQL on ArkMatches, specifically:

RegistrationChannelId

RegistrationMessageId

AnnouncementSent

AnnouncementSentAtUtc

LastRegistrationRefreshAtUtc. 

Lifecycle coordinator
ArkRegistrationController.ensure_registration_message(...) is the central path for:

initial post,

standard refresh,

force repost,

first-post-only announcement suppression,

SQL persistence,

one-way JSON fallback migration,

and tracked-view state updates. 

Discord message helper
upsert_registration_message(...) remains the Discord-specific low-level helper that:

edits in place,

reposts when forced,

recreates missing messages,

and updates in-memory/ref state passed to it. 

Scheduler role
The Ark scheduler now handles visibility maintenance at daily 20:00 UTC by invoking registration lifecycle refresh/repost logic rather than sending a reminder message. 

3) What was delivered
Registration lifecycle persistence
DAL helpers were added for registration message state, announcement tracking, and refresh timestamps. 

First-post-only announcement behavior
The controller calculates should_announce so that automatic announcements only happen when:

announcement is requested, and

either it is the first automatic announce or an explicit force-announce is requested. 

Manual admin override
/ark_force_announce was added so leadership can explicitly repost the active registration with @everyone. 

Daily visibility refresh
The scheduler now uses dedupe + controller-driven repost logic during the 20:00 UTC daily window. 

JSON migration fallback
Legacy JSON shapes with top-level numeric keys are accepted and can be migrated into SQL-backed behavior. 

SQL migration artifact
A migration script was added locally to capture the schema work required on ArkMatches. 

4) Deviations from original scope
A) confirmation_updates was not migrated to SQL
This task did not move confirmation_updates into SQL. That remains outside the delivered scope, consistent with the earlier recommendation to avoid migrating it blindly until its long-term ownership is decided. The existing JSON state loader still carries that field. 

B) SQL migration file exists in this repo as a handoff artifact
The engineering standards prefer SQL schema changes in the SQL Server repo, but the implementation includes a local sql_schema/ migration file so deployment requirements are explicit and handoff-ready. 

C) Daily refresh is implemented through the existing reminder dedupe mechanism
Rather than inventing a separate dedupe store, the daily visibility refresh reuses Ark reminder-state dedupe timing in the scheduler. This is a practical implementation decision that still satisfies the “do not run both systems together” requirement by replacing the old daily registration reminder path. 

5) What subsequent tasks should assume now
Registration lifecycle state
Future Ark tasks should assume:

registration message refs are intended to be SQL-backed on ArkMatches,

JSON registration refs are fallback/migration-only,

create/repost/refresh should go through ArkRegistrationController.ensure_registration_message(...). 

Command-layer expectation
Commands should stay thin and call Ark lifecycle logic rather than performing direct Discord post orchestration themselves. /ark_create_match and /ark_force_announce now follow that pattern. 

Scheduler expectation
There is now a registration visibility refresh path at 20:00 UTC, so later Ark tasks should not reintroduce a parallel daily registration reminder flow. 

6) Test/hardening notes
Follow-up regressions already addressed
The follow-up review/test issues were resolved in the test suite by:

aligning confirmation-view expectations with show_result_actions, 

fixing scheduler refresh assertions to correctly capture controller calls, 

stabilizing the missing-message recreation test with a controlled simulated NotFound path. 
