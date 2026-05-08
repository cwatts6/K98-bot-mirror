```markdown
# 🩺 Diagnostics Runbook — Tracing Errors, Crashes, and Performance

File: `docs/runbook_diagnostics.md`  
Audience: Developers & on-call maintainers  
Last Updated: 2025-10-19

---

Purpose
- How to triage errors, find root causes, recover from crashes, and gather runtime metrics for the K98 bot.
- Example invocations and upload options for uploading diagnostics to S3 or an artifact endpoint.

Top-level artifacts to inspect
- LOG_DIR/log.txt — Info+ application log
- LOG_DIR/error_log.txt — Warning+ and operational errors
- LOG_DIR/crash.log — Unhandled exceptions and tracebacks
- DATA_DIR/LAST_SHUTDOWN_INFO.json — summary of last clean shutdown
- DATA_DIR/QUEUE_CACHE_FILE — live queue snapshot (see constants.QUEUE_CACHE_FILE)
- constants.COMMAND_CACHE_FILE — stored command signatures

Collecting diagnostics (example invocations)
- Collect only (archive written locally):
  - python scripts/collect_diagnostics.py -o /tmp/k98-diagnostics.tar.gz

- Collect and upload to S3 (preferred when you have an AWS bucket):
  - python scripts/collect_diagnostics.py --include-logs --upload --s3-bucket my-bucket --s3-prefix diagnostics/k98/
  - or rely on env vars:
    - export DIAGNOSTICS_S3_BUCKET=my-bucket
    - export DIAGNOSTICS_S3_PREFIX=diagnostics/k98/
    - python scripts/collect_diagnostics.py --include-logs --upload

- Collect and upload to an artifact HTTP endpoint:
  - python scripts/collect_diagnostics.py --upload --artifact-url https://artifacts.example.com/upload --artifact-token "TOKEN"
  - or set env vars:
    - export ARTIFACT_UPLOAD_URL=https://artifacts.example.com/upload
    - export ARTIFACT_UPLOAD_TOKEN=__TOKEN__
    - python scripts/collect_diagnostics.py --upload

Notes:
- The script will always include a head+tail excerpt of the main logs to keep attachments bounded; use --include-logs to include full log files.
- Uploading requires either boto3 (for S3) or requests (for HTTP). The script will report a clear error if a chosen upload method lacks the library.

Configuration & environment variables (uploader)
- DIAGNOSTICS_S3_BUCKET — default S3 bucket name used by the script (optional)
- DIAGNOSTICS_S3_PREFIX — optional key prefix path for uploads
- ARTIFACT_UPLOAD_URL — HTTP endpoint to POST the artifact to
- ARTIFACT_UPLOAD_TOKEN — bearer token used for HTTP upload Authorization header

Security notes
- Keep upload endpoints and tokens private. Use IAM roles for EC2/ECS tasks when possible rather than static AWS credentials.
- The script redacts sensitive environment variables when creating env.txt inside the archive.

When and how to share the archive
- Share the created tar.gz with the on-call team or attach it to an incident ticket.
- If uploading to an internal artifact store, include the returned artifact URL in the incident ticket.

Suggested improvements (future work)
- Add automatic upload to the team's incident tracker or ticketing system.
- Integrate with S3 lifecycle rules and retention policies for diagnostics archives.
- Provide an automated "collect on failure" hook in the watchdog to capture diagnostics when the bot crashes.

For quick reference:
- Run smoke imports: python scripts/smoke_imports.py
- Collect diagnostics: python scripts/collect_diagnostics.py -o /tmp/diag.tar.gz
- Upload to S3: python scripts/collect_diagnostics.py --upload --s3-bucket my-bucket

```
