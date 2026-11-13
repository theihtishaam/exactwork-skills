# Migration handoff

## Current scope and authorization

Prepare the migration and compatibility notes only. The latest user correction requires the old `name` field to remain readable for one release. It supersedes the earlier proposal to switch all callers immediately. No deployment, production changes, record deletion, or removal of the old field or its callers is authorized.

## Current artifacts and inspection

- `migration_v2.sql` is the current draft. It adds nullable `customers.display_name VARCHAR(255)` and copies `name` into rows whose `display_name` is null. It preserves `name`; it does not rename or drop it.
- `compatibility.md` requires reads to prefer populated `display_name` and fall back to `name` for one release. Writes must keep both fields synchronized. Removing `name` or its callers requires a later, separately authorized migration.
- Both current drafts were read for this handoff and left unchanged. The SQL performs the initial backfill; ongoing write synchronization is a documented caller requirement, not implemented by this SQL. Caller code was not supplied or verified.
- `migration_v1.sql` is historical and superseded, not the current artifact.

## Verification state

- `task-state.md` reports that a local parser check passed for `migration_v2.sql`; this handoff did not rerun that check.
- No database integration test has run because no disposable database is available. A prior attempt failed with `connection refused` before any SQL executed.
- The SQL has not been executed against a database. No production connection was attempted. Parser success does not establish database compatibility or successful execution.
- This handoff involved file inspection only; no SQL was executed and no browsing or draft modification occurred.

## Next steps

1. Review the inspected drafts for any remaining compatibility questions, including how callers will synchronize writes during the transition. Keep work limited to migration and compatibility documentation.
2. If database validation is needed, request an available disposable test database and establish its engine/version before testing. Record integration results separately from the existing parser result.
3. Do not deploy or connect to production. Keep the old field readable for one release and preserve all records. Any later removal or deployment needs separate authorization.
