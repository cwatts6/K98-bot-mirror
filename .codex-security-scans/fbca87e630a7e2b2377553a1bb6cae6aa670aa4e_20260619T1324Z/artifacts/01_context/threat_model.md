# Repository Threat Model

K98 Bot is a Discord bot that exposes slash commands, interactive views, file/image responses, and SQL-backed game data workflows. Important assets are Discord authorization boundaries, private player/account data, bot tokens and configuration, SQL-backed ranking/report data, generated files sent to Discord, and operator-only workflows.

Primary trust boundaries are Discord users and channels entering command/view callbacks, service and DAL calls crossing into cache or SQL-backed data, generated embeds/images/files crossing back into Discord, and local/operator deployment scripts crossing into production infrastructure.

Attacker-controlled or untrusted inputs include Discord interaction metadata, user IDs, governor names and imported source labels from upstream game/import data, command options, channel context, and any text that may be rendered into Discord messages, embeds, images, or spreadsheet-compatible exports.

Repository-wide invariants: command and view layers must preserve permission/channel gates; private data paths should default to ephemeral responses; SQL/data access should stay in DAL/service layers; generated files must avoid unsafe filesystem behavior and spreadsheet formula injection; user-controlled text must not create unintended Discord mentions or formatting; expensive render/export paths should be bounded and handle failures without leaking data.
