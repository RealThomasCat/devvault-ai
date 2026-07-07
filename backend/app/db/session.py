from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Connection = actual wire/socket connection to DB
# Engine = DB access system + pool (reusable collection of DB connections)
# Session = one unit of DB work in your app code (like a transaction)

# Create the SQLAlchemy DB engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True, # Checks if the pooled DB connection is alive before using it
)

# Create a reusable session factory
# When we need DB work, call SessionLocal() to create a DB session.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False, # Don't automatically flush changes to the DB before queries
    expire_on_commit=False, # Don't expire objects after commit, so they can still be used after the session is closed
)

# flush = push pending changes to DB inside current transaction
# commit = finalize transaction permanently
# rollback = undo current transaction

# Dependency function to get a DB session for FastAPI endpoints
# When a function containes yield, it becomes a generator function.
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal() # Create a new DB session

    # Yield the session to the caller (route handler), and ensure it is closed after use
    try:
        yield db
    finally:
        db.close()