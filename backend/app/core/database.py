from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine_options: dict = {}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
if settings.database_url == "sqlite://":
    engine_options["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_source_columns() -> None:
    """Keep the local prototype database compatible with nullable Source additions.

    A migration framework is intentionally deferred for this one-week MVP.
    """
    if not settings.database_url.startswith("sqlite"):
        return
    if "sources" not in inspect(engine).get_table_names():
        return

    existing_columns = {column["name"] for column in inspect(engine).get_columns("sources")}
    additions = {
        "collector_id": "VARCHAR(255)",
        "extraction_description": "VARCHAR(500)",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing_columns:
                connection.execute(text(f"ALTER TABLE sources ADD COLUMN {name} {definition}"))
