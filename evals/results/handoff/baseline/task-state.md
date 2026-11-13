# Synthetic task notes

Original request: prepare a migration that renames the customer display field. Do not deploy.

Earlier draft: migration_v1.sql prepared, not run. Plan proposed switching all callers immediately.

Latest user correction: keep the old field readable for one release; generate the migration and compatibility notes only. Do not change production or delete records.

Current artifacts: migration_v2.sql and compatibility.md prepared in this fixture directory. Local parser check passed for migration_v2.sql. A database integration test has not run because no disposable database is available. A prior attempt failed with "connection refused" before any SQL executed. No production connection was attempted.

Remaining: inspect the current SQL and caller compatibility notes, then request an available disposable test database if needed. No deployment is authorized.
