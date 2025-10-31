"""Database configuration for SQLAlchemy.

This module sets up the SQLAlchemy engine, declarative base, and session factory.
It supports both persistent and in-memory SQLite databases, as well as any
other backend configured via the `DATABASE_URL` environment variable.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")


class Base(DeclarativeBase):
    """Declarative base class for ORM models."""
    pass


def _make_engine(url: str):
    """Create an SQLAlchemy engine depending on the database URL."""
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if url.endswith(":///:memory:"):
            return create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
