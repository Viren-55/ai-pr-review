"""Database configuration and connection management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databases import Database
from models import Base
import os
from typing import AsyncGenerator

# Database URL - can be configured via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./code_review.db")

# For async operations
database = Database(DATABASE_URL)

# For sync operations (useful for migrations)
if DATABASE_URL.startswith("sqlite"):
    # SQLite settings
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL settings
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_database() -> AsyncGenerator[Database, None]:
    """Get async database connection."""
    try:
        yield database
    finally:
        pass