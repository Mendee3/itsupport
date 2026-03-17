# PostgreSQL Migration

This app now reads `DATABASE_URL` from the environment. If `DATABASE_URL` is not set, it still falls back to the current SQLite file:

- SQLite fallback: `/opt/itsupport/oncall.db`
- PostgreSQL target: whatever is in `DATABASE_URL`

## Recommended production shape

Use one PostgreSQL server on the intranet host and a separate database for this app, for example:

`itsupport`

Keep `hamtdaa`, `chatbot`, and `itsupport` as separate databases on the same PostgreSQL instance.

## Required environment variables

For migration:

```bash
export SQLITE_SOURCE_DB=/opt/itsupport/oncall.db
export DATABASE_URL='postgresql+psycopg://itsupport_user:REPLACE_ME@127.0.0.1:5432/itsupport'
```

For runtime:

```bash
export DATABASE_URL='postgresql+psycopg://itsupport_user:REPLACE_ME@127.0.0.1:5432/itsupport'
```

## Migration steps

1. Create the PostgreSQL database and user.
2. Install the PostgreSQL driver used by SQLAlchemy if it is not already available.
3. Run the migration script once:

```bash
python3 /opt/itsupport/migrate_to_postgres.py
```

4. Restart the app service with `DATABASE_URL` set to the PostgreSQL connection string.
5. Verify login, engineer list, and assignment pages.
6. Keep the old SQLite file as a rollback backup until production is stable.

## Notes

- The migration script refuses to load into a non-empty PostgreSQL target database.
- IDs are preserved for `user`, `engineer`, and `assignment`.
- PostgreSQL sequences are reset after import so future inserts continue correctly.
