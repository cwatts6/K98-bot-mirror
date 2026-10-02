# Security Policy and Engineering Context

## Reporting a Vulnerability

Do not disclose suspected vulnerabilities through a public issue, discussion, or pull request.

Report them through: **GitHub private vulnerability reporting for this repository**.

Include the affected component, revision, reproduction conditions, realistic impact, and any evidence that can be shared safely. Do not include production credentials, personal data, or live secrets.

Expected response targets:

- acknowledgement: **within 3 business days**
- initial triage: **within 7 business days**
- coordinated disclosure approach: **Please report vulnerabilities privately and allow a reasonable remediation period before public disclosure. Disclosure timing will be agreed case by case.**

## System Purpose and Deployment Context

This repository is the scrubbed Codex development mirror for the K98 Discord bot. The production bot is promoted through the authorised production repository and deployment workflow; this mirror must not be treated as a production deployment source.

The application processes Discord interactions and attachments, reads and writes SQL-backed state, maintains restart-sensitive workflow state, produces user-facing reports, and may call configured external services.

## Security-Relevant Entry Points

- Discord slash commands, buttons, selects, modals, messages, and attachments
- administrative and operator-only workflows
- uploaded spreadsheet, CSV, image, and other supported file inputs
- SQL queries, stored procedures, imports, exports, and cache refreshes
- environment variables, runtime configuration, diagnostics, and logging
- outbound HTTP/API calls and user-influenced destinations
- startup, shutdown, schedulers, rehydration, and persistent views
- filesystem/cache/state operations and report generation
- dependency, promotion, and deployment changes

## Trust Boundaries

- untrusted Discord user input to bot command and interaction handlers
- Discord identities, guild membership, linked accounts, and administrative roles
- uploaded file content and filenames to parser/import services
- bot service process to SQL Server through configured credentials and permissions
- bot process to external APIs or network destinations
- scrubbed mirror repository to the private production promotion path
- persisted SQL/cache state to rehydrated runtime actions after restart

## Security Invariants

- Permission, ownership, guild, and linked-account checks occur before privileged reads or mutations and are revalidated at the final action boundary when state can change.
- Public, ephemeral, direct-message, and private-account visibility is explicit and tested; one user or guild must not receive another user's protected data.
- SQL values are parameterised. Any non-parameterisable identifier is selected through a narrow allowlist, not raw user input.
- Uploaded files are constrained by supported type, size, location, and parser behavior. User-controlled names or archive contents must not create arbitrary filesystem access or path traversal.
- User-influenced outbound destinations are constrained to approved schemes and hosts where applicable; redirects and callbacks do not bypass destination controls.
- Secrets, tokens, connection strings, private file contents, and sensitive personal data are not committed, displayed, or written to logs.
- Subprocesses and command execution do not interpolate untrusted input into a shell command.
- Critical authorization and workflow state survives restart without widening privileges, duplicating privileged actions, or acting on stale identity/ownership data.
- Production deployment occurs only through the authorised production repository, branch, validation, and rollback process.
- Security controls fail closed when identity, permission, configuration, or authoritative state cannot be established.

## Reportable Security Findings

A finding is normally reportable when a realistic path exists to one or more of the following:

- authentication, authorization, ownership, role, guild, or account-boundary bypass
- SQL, command, template, expression, or other injection
- path traversal, arbitrary file read/write, unsafe archive extraction, or unsafe upload processing
- server-side request forgery, unsafe redirect/destination control, or unintended external callback
- exposure of secrets, tokens, protected user data, private reports, or cross-user/cross-guild information
- arbitrary code or command execution, unsafe deserialization, or dependency behavior reachable in this deployment
- modification or corruption of authoritative security, identity, or workflow state
- bypass of the authorised promotion/deployment boundary
- repeatable denial of service with realistic access and material operational impact

Severity must consider production reachability, required privileges, affected users/data, persistence, available compensating controls, and whether exploitation crosses a trust boundary.

## Normally Non-Reportable Without Additional Evidence

- style-only or generic best-practice observations with no plausible attack path or material impact
- findings limited to test fixtures, inert examples, generated artifacts, or unreachable development-only code when repository evidence proves they cannot affect deployment
- the absence of secrets from this scrubbed mirror by itself
- duplicate reports of the same stable finding, unless the new report adds a distinct affected location, attack path, or materially different impact
- performance or reliability issues with no security consequence

These are not blanket exclusions. Evidence of production reachability or a trust-boundary impact makes the issue reviewable.

## Codex Security Guidance

This file supplies policy context only. It does not select a scan type.

- Routine PR, commit, branch, and working-tree reviews use the K98 routing skill and, when required, `$codex-security:security-diff-scan`.
- Standard or deep codebase scans require an explicit operator request for that broader audit.
- Existing captured findings are triaged without launching discovery again.
- Unresolved finding details, accepted-risk records, owners, and target dates remain in the private security workflow, not this public file.

## Validation Guidance

Use focused tests for the affected security boundary and the repository's standard validation gates. Common checks include:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/validate_codex_security_routing.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

Add targeted negative tests for permissions, ownership, malformed input, uploads/paths, SQL construction, output visibility, network destinations, log redaction, subprocesses, and restart-sensitive state when relevant.

## Policy Ownership and Review

- policy owner: **K98 Repository Maintainer**
- technical security owner: **Chris Watts**
- last reviewed: **2026-07-16**
- next scheduled review: **Quarterly, or after a material security or architecture change**
- accepted-risk register location: **Private K98 Security Findings Register**
