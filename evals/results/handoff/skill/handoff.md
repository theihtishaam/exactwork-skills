# Handoff

## Target and constraints

Prepare a customer display-field migration and compatibility notes only. The latest user correction requires the old field to remain readable for **one release**. It supersedes the earlier plan to switch all callers immediately. Do not deploy, change production, delete records, or remove `name` or its callers; removal needs a later, separately authorized migration.

## Current state and evidence

- [migration_v2.sql](migration_v2.sql) is the current prepared draft. It adds `customers.display_name VARCHAR(255)` and copies `name` into `display_name` where the latter is `NULL`. It preserves `name`.
- [compatibility.md](compatibility.md) requires reads to prefer populated `display_name` and fall back to `name`, with writes keeping both fields synchronized during the transition release. The SQL only adds and backfills the column; it does not implement ongoing write synchronization. Caller changes are not evidenced by these artifacts.
- [task-state.md](task-state.md) reports that the local parser check passed for `migration_v2.sql`. This is a recorded result, not a check rerun during this handoff.
- Database integration testing has **not run**: no disposable database is available. A prior attempt failed with **"connection refused" before any SQL executed**. No production connection was attempted. The SQL has not been executed against a database.
- The earlier `migration_v1.sql` was prepared but not run; it is historical, not the current draft. This handoff inspected only the three supplied files and left both drafts unchanged. No SQL was executed and no browsing occurred.

## Next

Read the linked artifacts and confirm they have not changed. Review whether the draft SQL and compatibility plan meet the one-release read fallback and synchronized-write requirements. If database verification is needed, request an available disposable test database; do not treat the parser result as integration verification or deployment readiness. No deployment is authorized.
