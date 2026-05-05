# K98 Deferred Optimisation Scoring Model

## Purpose
Prioritise deferred optimisation items consistently so the highest-value batches are selected first.

This model is not a substitute for judgement. It is a decision aid.

## Scoring Fields

Each deferred item receives four scores from 1–5.

## 1. Impact

How much benefit if fixed?

| Score | Meaning |
|------|---------|
| 1 | Cosmetic or minor clarity improvement |
| 2 | Small maintainability improvement |
| 3 | Noticeable maintainability, reliability, or UX improvement |
| 4 | Significant performance, reliability, or architecture improvement |
| 5 | Critical reliability, operational, or architectural improvement |

## 2. Frequency

How often is the affected path used or touched?

| Score | Meaning |
|------|---------|
| 1 | Rarely used / unlikely to be touched |
| 2 | Occasional use |
| 3 | Regular use |
| 4 | High-use command, service, or workflow |
| 5 | Core workflow / high concurrency / frequent production path |

## 3. Risk Reduction

How much risk does fixing it remove?

| Score | Meaning |
|------|---------|
| 1 | Minimal risk reduction |
| 2 | Reduces minor confusion or duplication |
| 3 | Reduces moderate bug or maintenance risk |
| 4 | Reduces meaningful production/support risk |
| 5 | Reduces major restart, data, operational, or correctness risk |

## 4. Effort

How hard is it to fix?

| Score | Meaning |
|------|---------|
| 1 | Very small, low-risk change |
| 2 | Small focused change |
| 3 | Moderate refactor |
| 4 | Large cross-module refactor |
| 5 | Major redesign or migration |

## Priority Score

Use:

```text
Priority Score = (Impact + Frequency + Risk Reduction) - Effort
Recommendation Bands
Score	Recommendation
10–14	Prioritise soon
7–9	Good batch candidate
4–6	Keep in backlog
1–3	Low priority
<=0	Do not action unless bundled with related work
Tie-Breakers

When scores are close, prioritise items that:

unblock future refactors
reduce direct SQL in commands/views
reduce duplicate helpers
improve restart safety
affect high-use Discord commands
improve testability
Batch Selection Rules

A good optimisation batch should usually include:

3–7 related items
one clear subsystem/theme
mostly low/medium risk items
at least one measurable outcome

Avoid batches that:

mix unrelated subsystems
combine too many high-risk changes
require unclear architecture decisions
cannot be tested meaningfully
Example
Item	Impact	Frequency	Risk Reduction	Effort	Score	Recommendation
Registry load TTL cache	4	4	3	2	9	Good batch candidate
Remove SQL from telemetry command	4	3	4	3	8	Good batch candidate
Remove dead legacy view	3	2	2	2	5	Keep in backlog
Full registry SQL migration	5	4	5	5	9	Good candidate, but split first
Required Use

When preparing a Deferred → Codex Task Pack:

score each candidate item
explain exclusions
group related items
do not rely on score alone
include final batch rationale
