"""Database setup and request-scoped sessions."""

import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


def create_database_engine(database_url: str) -> Engine:
    """Create an engine that also supports local SQLite development."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = create_database_engine(os.getenv("DATABASE_URL", "sqlite:///./patchpilot.db"))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database() -> None:
    """Create the current schema for local development.

    Schema migrations will replace this bootstrap step before production deployment.
    """
    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a transaction scope for an HTTP request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
