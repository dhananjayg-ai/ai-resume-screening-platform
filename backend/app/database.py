"""SQLAlchemy engine, session factory, declarative base, and the get_db dependency."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# SQLite requires this connect arg when used from multiple threads (FastAPI does).
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

    # Ensure the directory for a sqlite file path exists.
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.isdir(db_dir):
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
