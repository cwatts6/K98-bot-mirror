# Codex Security Review Routing

This reference defines scan selection for K98 work. `SECURITY.md` supplies policy context; it does not launch or select scans.

## Routine Git-Backed Changes

Use `k98-security-review-routing`. Select either a precise documented skip or:

```text
Use $codex-security:security-diff-scan to review the changes from <base> to <head> for security regressions. Review changed source-like files and directly supporting code only. Do not broaden this into a repository-wide or deep scan.
```

Confirm `Scan type: Changes`, the correct base/head or uncommitted patch, and Deep off.

## Explicit Standard Audit

<!-- codex-security-routing: allow-standard reason="documents the explicitly requested standard codebase audit workflow" -->
Use `$codex-security:security-scan` only when the operator explicitly requests a repository-wide or scoped-folder audit.

## Explicit Deep Audit

<!-- codex-security-routing: allow-deep reason="documents the explicitly requested deep codebase audit workflow" -->
Use `$codex-security:deep-security-scan` only when the operator explicitly requests a deep, exhaustive, or multi-pass audit. Never use it for a PR, commit, branch range, or working-tree patch.

## Existing Findings

Use `$codex-security:triage-finding` against the captured findings and recorded revision. Do not start discovery again merely to reproduce a known backlog.

Use `$codex-security:fix-finding` for one accepted finding, or one tightly related root-cause family, and review the resulting Git diff afterward.

## Cross-Repository Work

Resolve and review the bot and SQL repository Git targets separately. Retain both sets of evidence and assess deployment order after the reviews.
