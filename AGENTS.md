# Codex Repository Instructions

## Required Reading

Before beginning repo work, read the current versions of:

- `README-DEV.md`
- `docs/K98 Bot — Coding Execution Guidelines.md`
- `docs/k98 Bot — Deferred Optimisation Framework.md`
- `docs/K98 Bot — Project Engineering Standards.md`
- `docs/K98 Bot — Skills & Refactor Triggers.md`
- `docs/K98 Bot — Standard Development Initiation Statement.md`
- `docs/K98 Bot — Testing Standards.md`
- `docs/K98 Bot Deferred Optimisation Scoring Model.md`
- `docs/K98 Bot Codex Task Pack Generator.md`

## Working Rules

- Step 1 must always be review/scope only unless explicitly told otherwise.
- Keep changes PR-sized and focused.
- Avoid embedded SQL in command modules.
- Prefer service and DAL layers.
- Preserve existing behaviour unless explicitly changing it.
- Run targeted tests and lint where practical.
- Capture deferred optimisation items clearly.

## Repository / Promotion Model

- `origin` is the scrubbed Codex mirror: `K98-bot-mirror`.
- `production` is the private production repository: `K98-bot`.
- Codex should create branches and PRs against `K98-bot-mirror`.
- Production promotion happens only after local validation.
- Production changes are promoted by pushing the same branch to the `production` remote and opening a PR into `K98-bot/main`.
- The bot machine must deploy only from `K98-bot/main`, never from `K98-bot-mirror`.
