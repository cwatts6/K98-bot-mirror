core helpers already in the repo check and re-use exitsing functions wherever possible rather than creating duplicates, if new helpers are required consider creating them in the central helpers rather than local
remember our project-wide standards

@cwatts6/k98-bot/files/file_utils.py
@cwatts6/K98-bot-mirror/files/utils.py
@cwatts6/K98-bot-mirror/files/governor_registry.py
@cwatts6/K98-bot-mirror/files/logging_setup.py
@cwatts6/K98-bot-mirror/files/constants.py
@cwatts6/K98-bot-mirror/files/embed_utils.py
@cwatts6/K98-bot-mirror/files/account_picker.py
@cwatts6/K98-bot-mirror/files/bot_helpers.py
@cwatts6/K98-bot-mirror/files/process_utils.py

Project-wide Standards to enforce
Verify event_data_loader.py complies with these:
1.	Timezone standard
o	All datetime usage must use datetime.now(UTC) or datetime.fromisoformat(...).replace(tzinfo=UTC)
2.	fmt_short standard
o	Ensure datetime formatting uses fmt_short() from embed_utils where appropriate.
3.	Logging conventions
o	Must use module-specific loggers
o	Must NOT use logging.basicConfig
o	Must route through PR-2 safe logging handlers where applicable
4.	Startup/Shutdown Guardrails
o	Check for consistency with boot_safety, startup_utils, shutdown handlers, and queue flush logic
5.	Centralisation of logic
o	Look for any logic that belongs in utils, bot_helpers, bot_config, file_utils, embed_utils, utils, process_utils, target_utils, or similar
o	Identify sections that should be refactored into shared abstractions
6.	Async rules
o	No blocking operations inside async functions
o	Correct use of await, cancellation handling, task tracking, separation between sync and async utilities
7.	Interactions with Discord
o	Validate embed creation
o	Check any long-running operations
o	Validate message edits with safe exception handling
