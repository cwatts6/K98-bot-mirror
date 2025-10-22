# ⚙️ DevOps Runbook — Deployment, Configuration, and Maintenance

File: `docs/runbook_devops.md`  
Audience: Operators and CI/CD engineers  
Last Updated: 2025-10-19

---

Purpose
- Describe recommended deployment patterns, environment variables, configuration layout, and maintenance procedures for the bot.

Environments
- DEV: local development with test credentials and a dedicated test guild.
- STAGING: pre-prod environment to smoke test updates.
- PROD: production with full watchers and backups.

Recommended deployment approaches
1) Systemd (recommended for Linux)
- Minimal service example (replace placeholders):

```ini
[Unit]
Description=K98 Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/k98-bot
ExecStart=/opt/k98-bot/venv/bin/python DL_bot.py
Restart=on-failure
Environment=WATCHDOG_RUN=1
Environment=DISCORD_BOT_TOKEN=your_token_here

[Install]
WantedBy=multi-user.target
```

- Ensure the service runs under a dedicated user with limited permissions. Use a virtualenv in the project folder.

2) Docker (optional)
- If containerizing, ensure:
  - LOG_DIR and DATA_DIR are mounted as volumes.
  - The container exits with RESTART_EXIT_CODE when a supervised restart is desired.
  - Use healthcheck endpoints to let orchestrators decide restarts.

Environment variables (high-level)
- Required: DISCORD_BOT_TOKEN
- Recommended: WATCHDOG_RUN=1 for production; ADMIN_USER_ID; GUILD_ID for local command sync.
- Logging: LOG_TO_CONSOLE=1 (optional)
- See bot_config.py for the full set of env var names and their types.

Configuration & secrets
- Keep secrets out of the repo. Use a secrets manager or environment variables injected by CI.
- GOOGLE credentials: store in a file referenced by GOOGLE_CREDENTIALS_FILE and ensure file permissions are restricted.

Backups & persistence
- DATA_DIR holds persistent JSON caches (QUEUE_CACHE_FILE, REMINDER_TRACKING_FILE). Regularly back up DATA_DIR to durable storage.
- Log rotation: logging_setup handles file rotation. Keep copies of crash.log for at least 30 days.

CI/CD recommendations
- Use a branch-per-feature flow with PR reviews.
- Before merging to main:
  - Run unit tests and scripts/smoke_imports.py (import smoke).
  - Run static checks and linting.
- Tag releases and maintain a CHANGELOG.md.

Operational runbook snippets
- Restarting:
  - systemctl restart k98-bot
  - After restart, check LOG_DIR/log.txt for heartbeat and admin DM confirmation.
- Releasing:
  - Merge to main
  - Tag release and deploy using CI job that runs smoke imports then restarts service.

Monitoring & alerts
- Monitor:
  - Process uptime & restarts (systemd or orchestrator).
  - crash.log increases in rate.
  - Heartbeat freshness (LOG_DIR/heartbeat.json).
- Alerts:
  - If heartbeat hasn't updated in N minutes, send PagerDuty/alert.
  - On repeated restarts within a short window, prevent restart loop (watchdog should implement backoff).

Security
- Limit admin command access to ADMIN_USER_ID (the code already checks for admin-only modifiers in commands).
- Rotate DISCORD_BOT_TOKEN on suspicion of exposure.
- If using ODBC/DB credentials, follow least privilege patterns.

Suggested additions (missing docs that would help ops)
- sample systemd unit (expand and include restart policies)
- docker-compose example (with volumes for logs and data)
- backup & restore instructions for DATA_DIR and LOG_DIR
- observability playbook (what counts as healthy, thresholds, and alert runbooks)
