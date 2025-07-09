from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlmodel import Session as SQLModelSession
from src.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections after 5 minutes
    echo=False,          # Set to True for SQL query logging in development
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        This dependency automatically handles session lifecycle:
        - Creates a new session for each request
        - Commits changes on successful request completion
        - Rolls back changes on exceptions
        - Ensures session is properly closed
    """
    with SQLModelSession(engine) as session:
        yield session

 