# Compatibility draft

For one release, reads use display_name when populated and fall back to name.
Writes must keep both fields synchronized during that release.
Do not remove name or its callers until a later, separately authorized migration.
The SQL has not been executed against a database.
