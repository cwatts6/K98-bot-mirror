### Weekly Activity Invalid Cumulative View Retirement

- Area: SQL repo `dbo.vAllianceActivity_WeeklyCumulative`
- Type: cleanup
- Description: Weekly activity validation found that `dbo.vAllianceActivity_WeeklyCumulative` depended on columns no longer exposed by `dbo.vAllianceActivity_WeeklyDelta`, and repository/bot searches found no executable consumer.
- Resolution: SQL migration `20260727_000_retire_vAllianceActivity_WeeklyCumulative.sql` guarded the known definition, dependency graph, permissions, signatures, and extended properties before dropping the invalid view. The migration deliberately uses a forward-fix posture rather than recreating a known invalid definition. Any later reporting need must introduce a new valid contract through a separately reviewed migration.
- Validation: The committed migration contains preconditions, the KingdomScanData4/import mutexes, post-drop verification, and explicit refusal paths for definition drift or discovered consumers. The current SQL expected-state snapshot no longer carries the retired cumulative view.

### PR-Based SQL Promotion Workflow Completed Item

- Area: `C:\K98-bot-SQL-Server` SQL development, deployment, export, drift, and recovery workflow
- Type: architecture
- Description: The former Production schema-export routine could overwrite Git-driven SQL changes by synchronising Production snapshots directly back into the repository's main development line.
- Resolution: The SQL repository now treats Git as the authority for intentional changes, uses reviewed `migrations/` as the deployable source, validates SQL pull requests without Production connectivity, blocks non-`main` deployment by default, records migration/deployment history, checks backup readiness, exports Production schema onto timestamped review branches, and provides drift and nightly-export health tooling. The documented replacement workflow prevents the normal Production export path from writing directly to `main`.
- Validation: `docs/SQL_PROMOTION_GUIDE.md`, `.github/workflows/sql-validation.yml`, `deploy/Deploy-SqlMigration.ps1`, `deploy/Export-ProdSchemaSnapshot.ps1`, `deploy/Invoke-NightlyProdSchemaExport.ps1`, migration history objects, drift checks, and backup-readiness tooling are committed in the SQL repository. Any remaining operator-specific scheduled-task verification is operational maintenance, not unfinished design of the promotion workflow.
