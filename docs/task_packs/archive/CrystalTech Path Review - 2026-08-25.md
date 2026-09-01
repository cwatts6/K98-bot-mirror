# CrystalTech Path Review — 2026-08-25

## Final delivery update

**Delivered and operator accepted on 2026-08-25.** Mirror PR #234 and production PR #541 are ready
for manual merge. The approved 404-step candidate was implemented, then reconciled with the
operator's updated corrected workbook through 11 authorised value-only corrections: seven image
mappings across the Swift Steeds I, Swift Marching III, and Improved Projectiles I groups, plus
four Mid/High labels standardised to the in-game spelling `Archer's Focus`.

The original proposed JSON is retained unchanged as provenance with SHA-256
`59daed30ae758a0b86f7d83168dd1b30519d27b3bfcabe6341d975dc76bb0bca`. The final runtime JSON,
including its implementation timestamp and the 11 follow-up corrections, has SHA-256
`a3da2af3e6330d009df2258767e9ba6d073bbc43b9f279da84f60b5ebc5f4e2b` and Git blob SHA-1
`7e836e744a29b3ca45ae6bcae8e83b5d72c8ba33`. Counts, crystal-cost totals, UIDs, ordering, schema,
and non-timestamp metadata remain exactly as reviewed. The updated corrected workbook SHA-256 is
`b21a9bb491443acdfab141b3038f9b8d566cba18bdb4bee2af7abfa4f0cb9c5b`.

Operator smoke passed `/crystaltech validate`, `/crystaltech reload`, two-user multi-step
progression, and account reset/restart-path behaviour. The clean-rollover deployment precondition
was satisfied with no extant CrystalTech progress. The historical review below records the initial
source assessment; its pre-existing-warning disposition is superseded by the final follow-up
section near the end of this document.

## Executive verdict

The supplied workbook **cannot be deployed unchanged**.

- It resolves **12 of the 16** findings recorded on its `Audit` sheet.
- **Four original findings remain unresolved.**
- It introduces/preserves **five new round-trip defects**: two duplicate/missing step-order pairs, one incorrect path order, and two copied `Special Concoction II` naming errors.
- Its `Audit` counts still describe the original 391-step file even though the edited `Steps` sheet contains 404 path steps.
- Its `meta.updated_at_utc` remains `2025-10-07T17:58:03Z`.

A corrected workbook and a deployment candidate JSON have been produced. The corrected candidate resolves all 16 recorded original findings, fixes the five workbook defects, refreshes metadata, and passes the structural/data checks described below.

## Source identity

- Uploaded original JSON size: **118,200 bytes**
- Uploaded original Git blob SHA-1: `cd36a2402714c2e862ebd1e98b13444a854c43e9`
- This exactly matches the current `config/crystaltech_paths.v1.json` blob published on `K98-bot-mirror/main`.
- Uploaded original SHA-256: `cdf57b8db36517e4de125e0db44f5b9f3b133072ca6d1bda82f55888cc1dd21f`
- Supplied workbook SHA-256: `fd3e54476209520286adbbc2e53c5aa551a9d2b1e994a1512fd94e520bbaa34a`

## Original audit resolution

| Original audit finding | Result in supplied workbook | Final corrected candidate |
|---|---|---|
| `f2p_low_infantry__karaku_reports_lv15` — Capitalisation differs from other Karaku Reports entries | Resolved | Resolved |
| `f2p_low_infantry__special_concoction_ii_lv2` — UID indicates Special Concoction II but display name says I | Resolved | Resolved |
| `f2p_low_archer__karaku_reports_lv15` — Capitalisation differs from other Karaku Reports entries | Resolved | Resolved |
| `f2p_low_archer__iron_infantry_lv5` — Iron Infantry step uses archers_focus image filename | Resolved | Resolved |
| `f2p_low_archer__special_concoction_ii_lv2` — UID indicates Special Concoction II but display name says I | Resolved | Resolved |
| `f2p_low_cavalry__karaku_reports_lv15` — Capitalisation differs from other Karaku Reports entries | Resolved | Resolved |
| `f2p_low_cavalry__iron_infantry_lv5` — Iron Infantry step uses archers_focus image filename | Resolved | Resolved |
| `f2p_low_cavalry__special_concoction_ii_lv2` — UID indicates Special Concoction II but display name says I | **Unresolved** — name='Special Concoction I' | Resolved |
| `f2p_low_siege__reinforced_axles_i_lv3` — UID indicates Reinforced Axles I but display name says II | **Unresolved** — name='Reinforced Axles II' | Resolved |
| `f2p_low_siege__reinforced_axles_i_lv5` — UID indicates Reinforced Axles I but display name says II | **Unresolved** — name='Reinforced Axles II' | Resolved |
| `f2p_low_siege__karaku_reports_lv15` — Capitalisation differs from other Karaku Reports entries | Resolved | Resolved |
| `f2p_low_siege__iron_infantry_lv5` — Iron Infantry step uses archers_focus image filename | Resolved | Resolved |
| `f2p_low_siege__special_concoction_ii_lv2` — UID indicates Special Concoction II but display name says I | **Unresolved** — name='Special Concoction I' | Resolved |
| `mid_high_cavalry__fleet_of_foot_ii_lv10` — UID indicates Fleet of Foot II but display name says III | Resolved | Resolved |
| `mid_high_siege__siege_provisions_lv10` — UID level suffix does not match target_level | Resolved | Resolved |
| `mid_high_siege__reinforced_axles_iii_lv10` — UID level suffix does not match target_level | Resolved | Resolved |

**Supplied workbook result:** 12 resolved, 4 unresolved.

The four unresolved original findings are:

1. `f2p_low_cavalry__special_concoction_ii_lv2` still says `Special Concoction I`.
2. `f2p_low_siege__reinforced_axles_i_lv3` still says `Reinforced Axles II`.
3. `f2p_low_siege__reinforced_axles_i_lv5` still says `Reinforced Axles II`.
4. `f2p_low_siege__special_concoction_ii_lv2` still says `Special Concoction I`.

## New workbook defects

| Location | Defect introduced/present in supplied workbook | Correction |
|---|---|---|
| `f2p_low_archers` | Duplicate `Step_Order = 31`; no step 42 | Renumbered physical sequence to 1–42 |
| `f2p_low_siege` | Duplicate `Step_Order = 42`; no step 41 | Renumbered physical sequence to 1–51 |
| `f2p_low_cavalry__cultural_exchange_lv15` | `Path_Order = 2` although cavalry is path 3 | Corrected to path order 3 |
| `f2p_low_cavalry__special_concoction_ii_lv3` | New UID says II; name says I | Name corrected to `Special Concoction II` |
| `f2p_low_siege__special_concoction_ii_lv3` | New UID says II; name says I | Name corrected to `Special Concoction II` |

## Data-change summary

The edited workbook contains **404** path steps versus **391** in the original: **14 additions and one removal**.

### Added step UIDs

- `f2p_low_infantry__swift_marching_ii_lv8`
- `f2p_low_infantry__cultural_exchange_lv15`
- `f2p_low_infantry__swift_marching_iii_lv10`
- `f2p_low_infantry__special_concoction_ii_lv3`
- `f2p_low_archer__cultural_exchange_lv15`
- `f2p_low_archer__fleet_of_foot_iii_lv10`
- `f2p_low_archer__special_concoction_ii_lv3`
- `f2p_low_cavalry__cultural_exchange_lv15`
- `f2p_low_cavalry__swift_steeds_iii_lv10`
- `f2p_low_cavalry__special_concoction_ii_lv3`
- `f2p_low_siege__cultural_exchange_lv15`
- `f2p_low_siege__reinforced_axles_iii_lv10`
- `f2p_low_siege__special_concoction_ii_lv3`
- `f2p_low_siege__siege_expert_lv4`

### Removed step UID

- `f2p_low_siege__siege_expert_lv2`

### Path counts and crystal-cost totals

| Path | Original steps | Reviewed steps | Delta | Original cost | Reviewed cost | Cost delta |
|---|---:|---:|---:|---:|---:|---:|
| `f2p_low_infantry` | 39 | 43 | +4 | 46,376,720 | 47,997,500 | +1,620,780 |
| `f2p_low_archers` | 39 | 42 | +3 | 44,931,090 | 47,997,500 | +3,066,410 |
| `f2p_low_cavalry` | 41 | 44 | +3 | 51,469,790 | 53,357,500 | +1,887,710 |
| `f2p_low_siege` | 48 | 51 | +3 | 59,453,380 | 64,189,500 | +4,736,120 |
| `mid_high_infantry` | 54 | 54 | +0 | 59,022,500 | 59,097,500 | +75,000 |
| `mid_high_archer` | 54 | 54 | +0 | 59,097,500 | 59,097,500 | +0 |
| `mid_high_cavalry` | 54 | 54 | +0 | 58,001,500 | 58,001,500 | +0 |
| `mid_high_siege` | 62 | 62 | +0 | 67,651,500 | 67,726,500 | +75,000 |

Aggregate crystal-cost increase across all eight paths: **11,461,020**.

## Corrected candidate validation

The corrected candidate `crystaltech_paths.v1.proposed.json` passed these checks:

- valid JSON and unchanged schema version `1.0`
- root key shape preserved
- eight unique paths in the original order
- 404 path steps and four unchanged common-block steps
- unique `path_id` values
- globally unique path-step UIDs
- all required step fields present
- step types restricted to `building` or `research`
- non-empty `en-GB` names
- integer, non-negative target levels and crystal costs
- every `_lvN` UID suffix matches `target_level`
- exact reviewed path counts and crystal totals
- all 16 original audit findings resolved
- all five newly detected workbook defects corrected
- no image filename was introduced or removed; the candidate uses the same 31 image filenames as the original
- corrected workbook step order is contiguous from 1 to N for every path
- no spreadsheet formula-error tokens were found in the corrected workbook

Candidate SHA-256: `59daed30ae758a0b86f7d83168dd1b30519d27b3bfcabe6341d975dc76bb0bca`.

## Existing validator coverage

The repository validator checks JSON loading, required fields, path/step UID uniqueness, includes, allowed types, i18n name structure, integer/non-negative levels and costs, asset existence, and flattened list numbering. It does **not** prove that a display name corresponds semantically to its UID, nor can it detect duplicate `Step_Order` values in the Excel source because those columns are not part of the runtime JSON.

The PR task therefore requires both the existing validator and focused data-contract regression assertions.

## Follow-up consistency warning resolution

The operator supplied an updated corrected workbook and explicitly approved resolving all four
warning groups in the same PR. The final runtime config and focused tests now lock these values:

| Warning group | Final resolution | Affected values |
|---|---|---:|
| F2P `Swift Steeds I` image mismatch | `swift_steeds.png` | 2 |
| F2P `Swift Marching III` image mismatch | `swift_marching.png` | 3 |
| F2P siege `Improved Projectiles I` image mismatch | `improved_projectiles.png` | 2 |
| Mid/High `Archers Focus` spelling variant | `Archer's Focus` | 4 |

These 11 changes do not alter counts, costs, UIDs, order, or the image-filename set. No known
source consistency warning from this review remains unresolved.

## Corrected artifacts

- `crystaltech_paths_review_corrected.xlsx`
- `crystaltech_paths.v1.proposed.json`
- `crystaltech_paths.v1.proposed.diff`
