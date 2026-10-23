"""Database engine and session management for SQLAlchemy ORM."""

from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.config import DBSettings
from app.db.models import Base


def create_db_engine(settings: DBSettings, echo: bool = False) -> Engine:
    """Create a configured SQLAlchemy Engine from DBSettings.

    Configures connection pooling, recycling, and pre-ping to handle AWS RDS
    private subnet connection lifecycles and idle drops.
    """
    url = settings.get_connection_url()

    # Apply production-ready connection pool options for MySQL / network databases
    kwargs = {
        "echo": echo,
    }
    if not url.startswith("sqlite"):
        kwargs.update(
            {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
            }
        )

    return create_engine(url, **kwargs)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a configured thread-safe session factory bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine: Engine) -> None:
    """Initialize database tables defined in Base metadata."""
    Base.metadata.create_all(bind=engine)
