# Database Session Management

This document describes the database session management utilities available for SQLModel/SQLAlchemy operations.

## Overview

The database session utilities provide multiple ways to manage SQLModel/SQLAlchemy database sessions with automatic transaction handling and proper resource cleanup.

## Available Utilities

### 1. FastAPI Dependency (`get_database_session`)

**Location**: `src/utils/dependencies.py`

**Usage**: For FastAPI endpoints

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from src.utils.dependencies import get_database_session

@app.get("/recipes/")
def get_recipes(db: Session = Depends(get_database_session)):
    # Use db session here
    # Session is automatically committed on success, rolled back on exception
    pass
```

### 2. Context Manager (`get_db_session_context`)

**Location**: `src/utils/database_session.py`

**Usage**: For utility functions and service layers

```python
from src.utils.database_session import get_db_session_context

def get_user_recipes(user_id: int):
    with get_db_session_context() as db:
        # Use db session here
        # Session is automatically committed on success, rolled back on exception
        return db.exec(select(Recipe).where(Recipe.user_id == user_id)).all()
```

### 3. DatabaseSessionManager Class

**Location**: `src/utils/database_session.py`

**Usage**: For more control over transaction behavior

```python
from src.utils.database_session import get_db_session_manager

def create_recipe(recipe_data: dict):
    with get_db_session_manager(auto_commit=True, auto_rollback=True) as db:
        # Use db session here
        # Customizable commit/rollback behavior
        recipe = Recipe(**recipe_data)
        db.add(recipe)
        return recipe
```



## Best Practices

### 1. Use FastAPI Dependencies for Endpoints

```python
@app.post("/recipes/")
def create_recipe(
    recipe: RecipeCreate,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    db_recipe = Recipe(**recipe.dict(), user_id=current_user.id)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe
```

### 2. Use Context Managers for Service Functions

```python
def create_recipe_service(recipe_data: dict, user_id: int) -> Recipe:
    with get_db_session_context() as db:
        recipe = Recipe(**recipe_data, user_id=user_id)
        db.add(recipe)
        db.flush()  # Get ID without committing
        db.refresh(recipe)  # Refresh to get generated fields
        return recipe
```

### 3. Use DatabaseSessionManager for Complex Transactions

```python
def transfer_recipe_ownership(recipe_id: int, from_user_id: int, to_user_id: int) -> bool:
    with get_db_session_manager(auto_commit=True, auto_rollback=True) as db:
        # Multiple operations in a single transaction
        recipe = db.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
        if not recipe or recipe.user_id != from_user_id:
            return False
        
        recipe.user_id = to_user_id
        db.add(recipe)
        return True  # Auto-committed on success
```

## Configuration

The database engine is configured in `src/utils/database_session.py` with the following settings:

- **Pool Pre-ping**: Enabled for connection health checks
- **Pool Recycle**: 300 seconds (5 minutes)
- **Echo**: Disabled (set to `True` for SQL query logging in development)

## Error Handling

All session utilities include automatic error handling:

- **Success**: Changes are automatically committed
- **Exception**: Changes are automatically rolled back
- **Cleanup**: Sessions are always properly closed

## Migration from Supabase Client

When migrating from Supabase client operations to SQLModel:

1. **Replace Supabase queries** with SQLModel ORM operations
2. **Use session utilities** instead of direct client calls
3. **Leverage SQLModel relationships** for complex queries
4. **Use transactions** for multi-step operations

## Database Schema Management

**Note**: This project uses Alembic migrations for all database schema operations. 
The database session utilities do not handle table creation or schema changes.
Use `alembic` commands for database migrations.

## Examples

See `src/utils/database_examples.py` for comprehensive examples of all usage patterns. 