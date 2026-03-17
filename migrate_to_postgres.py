import os
import sqlite3
from contextlib import closing

from sqlalchemy import create_engine, text

from app import create_app, db
from app.models import Assignment, Engineer, User


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def load_sqlite_rows(source_db: str):
    with closing(sqlite3.connect(source_db)) as conn:
        conn.row_factory = sqlite3.Row
        users = conn.execute(
            """
            SELECT id, username, password_hash, is_admin, active, created_at
            FROM user
            ORDER BY id
            """
        ).fetchall()
        engineers = conn.execute(
            """
            SELECT id, first_name, phone, email, active, created_at
            FROM engineer
            ORDER BY id
            """
        ).fetchall()
        assignments = conn.execute(
            """
            SELECT id, date, engineer_id, created_by_user_id, created_at
            FROM assignment
            ORDER BY id
            """
        ).fetchall()
    return users, engineers, assignments


def ensure_empty_target():
    counts = {
        "user": db.session.query(User.id).count(),
        "engineer": db.session.query(Engineer.id).count(),
        "assignment": db.session.query(Assignment.id).count(),
    }
    non_empty = {name: count for name, count in counts.items() if count}
    if non_empty:
        details = ", ".join(f"{name}={count}" for name, count in non_empty.items())
        raise SystemExit(f"Target database is not empty: {details}")


def reset_postgres_sequences():
    db.session.execute(text("SELECT setval(pg_get_serial_sequence('user', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM \"user\""))
    db.session.execute(text("SELECT setval(pg_get_serial_sequence('engineer', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM engineer"))
    db.session.execute(text("SELECT setval(pg_get_serial_sequence('assignment', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM assignment"))
    db.session.commit()


def main():
    source_db = require_env("SQLITE_SOURCE_DB")
    target_url = normalize_database_url(require_env("DATABASE_URL"))
    os.environ["DATABASE_URL"] = target_url

    if not os.path.exists(source_db):
        raise SystemExit(f"SQLite source DB not found: {source_db}")

    # Validate that the target URL is reachable before touching app state.
    engine = create_engine(target_url)
    with engine.connect():
        pass

    users, engineers, assignments = load_sqlite_rows(source_db)

    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_empty_target()

        for row in users:
            db.session.add(User(
                id=row["id"],
                username=row["username"],
                password_hash=row["password_hash"],
                is_admin=bool(row["is_admin"]),
                active=bool(row["active"]),
                created_at=row["created_at"],
            ))

        for row in engineers:
            db.session.add(Engineer(
                id=row["id"],
                first_name=row["first_name"],
                phone=row["phone"],
                email=row["email"],
                active=bool(row["active"]),
                created_at=row["created_at"],
            ))

        for row in assignments:
            db.session.add(Assignment(
                id=row["id"],
                date=row["date"],
                engineer_id=row["engineer_id"],
                created_by_user_id=row["created_by_user_id"],
                created_at=row["created_at"],
            ))

        db.session.commit()
        reset_postgres_sequences()

        print(f"Migrated users: {len(users)}")
        print(f"Migrated engineers: {len(engineers)}")
        print(f"Migrated assignments: {len(assignments)}")


if __name__ == "__main__":
    main()
