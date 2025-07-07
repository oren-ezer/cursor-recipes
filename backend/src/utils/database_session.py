from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
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
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """
    Context manager for database session management.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_session_context() as db:
            # Use db session here
            result = db.query(SomeModel).all()
            # Session is automatically committed on successful exit
            # and rolled back on exception
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseSessionManager:
    """
    Database session manager with context manager support.
    
    This class provides a more explicit way to manage database sessions
    with additional control over transaction behavior.
    """
    
    def __init__(self, auto_commit: bool = True, auto_rollback: bool = True):
        """
        Initialize the database session manager.
        
        Args:
            auto_commit: Whether to automatically commit on successful exit
            auto_rollback: Whether to automatically rollback on exceptions
        """
        self.auto_commit = auto_commit
        self.auto_rollback = auto_rollback
        self._session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        """Enter the context and return a database session."""
        self._session = SessionLocal()
        return self._session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and handle session cleanup."""
        if self._session is None:
            return
        
        try:
            if exc_type is None and self.auto_commit:
                # No exception occurred, commit if auto_commit is enabled
                self._session.commit()
            elif exc_type is not None and self.auto_rollback:
                # Exception occurred, rollback if auto_rollback is enabled
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

def get_db_session_manager(auto_commit: bool = True, auto_rollback: bool = True) -> DatabaseSessionManager:
    """
    Get a database session manager instance.
    
    Args:
        auto_commit: Whether to automatically commit on successful exit
        auto_rollback: Whether to automatically rollback on exceptions
        
    Returns:
        DatabaseSessionManager: Database session manager instance
        
    Example:
        with get_db_session_manager() as db:
            # Use db session here
            result = db.query(SomeModel).all()
    """
    return DatabaseSessionManager(auto_commit=auto_commit, auto_rollback=auto_rollback)

 