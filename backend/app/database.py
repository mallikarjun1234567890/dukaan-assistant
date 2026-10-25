"""SQLAlchemy engine and session helpers."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _sqlite_path_from_url(url: str) -> Path | None:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return None
    raw = url[len(prefix) :]
    if raw in {":memory:", ""}:
        return None
    return Path(raw)


def create_db_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        db_path = _sqlite_path_from_url(url)
        if db_path is not None:
            db_path.parent.mkdir(parents=True, exist_ok=True)

    engine_kwargs: dict = {"connect_args": connect_args, "future": True}
    if url.startswith("postgresql"):
        engine_kwargs["pool_pre_ping"] = True
    engine = create_engine(url, **engine_kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _existing_columns(conn, table: str) -> set[str]:
    url = str(engine.url)
    if url.startswith("sqlite"):
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return {row[1] for row in rows}
    rows = conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :table"
        ),
        {"table": table},
    ).fetchall()
    return {row[0] for row in rows}


def ensure_schema_updates() -> None:
    """Add new columns on existing SQLite/Postgres databases without wiping data."""
    url = str(engine.url)
    is_postgres = url.startswith("postgresql")
    timestamp = "TIMESTAMPTZ" if is_postgres else "TIMESTAMP"
    additions = {
        "shops": {
            "phone": "VARCHAR(30) DEFAULT ''",
            "timezone": "VARCHAR(64) DEFAULT 'Asia/Kolkata'",
            "opens_at": "VARCHAR(5) DEFAULT '09:00'",
            "closes_at": "VARCHAR(5) DEFAULT '21:30'",
            "weekly_off": "VARCHAR(20) DEFAULT ''",
            "logo_url": "VARCHAR(500) DEFAULT ''",
            "plan": "VARCHAR(30) DEFAULT 'trial'",
            "trial_started_at": timestamp,
            "trial_ends_at": timestamp,
            "grace_ends_at": timestamp,
            "plan_expires_at": timestamp,
            "paid_at": timestamp,
        },
        "users": {
            "display_name": "VARCHAR(120) DEFAULT ''",
            "avatar_url": "VARCHAR(500) DEFAULT ''",
        },
        "products": {
            "image_url": "VARCHAR(500) DEFAULT ''",
        },
    }
    with engine.begin() as conn:
        for table, columns in additions.items():
            existing = _existing_columns(conn, table)
            if not existing:
                continue
            for name, spec in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {spec}"))
        if is_postgres:
            users_cols = _existing_columns(conn, "users")
            if "shop_id" in users_cols:
                conn.execute(text("ALTER TABLE users ALTER COLUMN shop_id DROP NOT NULL"))


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
