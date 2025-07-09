from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.config import settings
from src.utils.dependencies import get_database_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admins", tags=["admins"])

@router.get("/config-test")
async def test_config():
    """
    Test endpoint to verify environment variables are loaded correctly.
    """
    return {
        "database_url_configured": bool(settings.DATABASE_URL),
        "database_url": settings.DATABASE_URL,
        "database_url_length": len(settings.DATABASE_URL) if settings.DATABASE_URL else 0,
        "supabase_url_configured": bool(settings.SUPABASE_URL),
        "supabase_url": settings.SUPABASE_URL,
        "supabase_key_configured": bool(settings.SUPABASE_KEY),
        "supabase_service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
        "supabase_url_length": len(settings.SUPABASE_URL) if settings.SUPABASE_URL else 0,
        "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0,
        "supabase_service_key_length": len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0
    }

@router.get("/test-setup")
async def test_setup():
    """
    Test endpoint to verify SQLModel setup without database connection.
    """
    try:
        # Test that we can import and use SQLModel components
        from sqlmodel import SQLModel
        from src.models.user import User
        from src.models.recipe import Recipe
        
        return {
            "status": "success",
            "message": "SQLModel setup is working correctly",
            "details": {
                "sqlmodel_imported": True,
                "user_model_imported": True,
                "recipe_model_imported": True,
                "database_url_configured": bool(settings.DATABASE_URL),
                "database_url_length": len(settings.DATABASE_URL) if settings.DATABASE_URL else 0
            }
        }
    except Exception as e:
        logger.error(f"Setup test error: {str(e)}")
        return {
            "status": "error",
            "message": "SQLModel setup has issues",
            "error": str(e)
        }

@router.get("/test-db-connection")
async def test_db_connection(
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    Test if a database connection can be established using SQLModel/Session.
    """
    try:
        logger.info("Testing database connection...")
        
        # Simple connection test - just try to execute a basic query
        db.execute(text("SELECT 1"))
        
        return {
            "status": "success",
            "message": "Database connection established successfully",
            "connection_method": "SQLModel/Session"
        }
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to establish database connection",
            "error": str(e),
            "error_type": type(e).__name__
        }