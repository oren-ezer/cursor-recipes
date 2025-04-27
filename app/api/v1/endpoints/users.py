from fastapi import APIRouter, Depends, HTTPException, status
from app.core.supabase_client import get_supabase_client
from app.core.config import settings
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def read_users_me():
    return {"message": "Current user endpoint"}

@router.get("/test-supabase")
async def test_supabase_connection():
    """
    Test endpoint to verify Supabase connection.
    """
    try:
        # Get the Supabase client
        logger.info("Attempting to get Supabase client...")
        supabase = get_supabase_client()
        
        # Execute a simple query to test the connection
        logger.info("Testing connection with a simple query...")
        response = supabase.from_('test_dummy').select('*').limit(1).execute()
        
        return {
            "status": "success",
            "message": "Successfully connected to Supabase",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Supabase connection error: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to connect to Supabase",
            "error": str(e),
            "config": {
                "supabase_url": settings.SUPABASE_URL,
                "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0,
                "supabase_service_key_length": len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0
            }
        }

@router.get("/config-test")
async def test_config():
    """
    Test endpoint to verify environment variables are loaded correctly.
    """
    return {
        "supabase_url_configured": bool(settings.SUPABASE_URL),
        "supabase_key_configured": bool(settings.SUPABASE_KEY),
        "supabase_service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
        "supabase_url_length": len(settings.SUPABASE_URL) if settings.SUPABASE_URL else 0,
        "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0,
        "supabase_service_key_length": len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0
    }

@router.get("/test-db-connection", summary="Test Database Connection", description="Test the connection to the Supabase database")
async def test_db_connection():
    """
    Test the connection to the Supabase database.
    
    This endpoint attempts to connect to the Supabase database and perform a simple query.
    It returns detailed information about the connection status and any errors that occur.
    """
    try:
        # First, test DNS resolution
        supabase_url = settings.SUPABASE_URL
        parsed_url = urlparse(supabase_url)
        hostname = parsed_url.hostname
        
        logger.info(f"Testing DNS resolution for {hostname}...")
        try:
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"Successfully resolved {hostname} to {ip_address}")
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {hostname}: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to resolve Supabase hostname",
                "error": str(e),
                "details": {
                    "hostname": hostname,
                    "error_type": "DNS_RESOLUTION_FAILED",
                    "error_message": str(e)
                }
            }
        
        # Get the Supabase client
        logger.info("Testing database connection...")
        supabase = get_supabase_client()
        
        # Execute a simple query to test the connection
        logger.info("Testing connection with a simple query...")
        response = supabase.from_('test_dummy').select('*').limit(1).execute()
        
        return {
            "status": "success",
            "message": "Successfully connected to the database",
            "details": {
                "connection": "established",
                "query": "executed successfully",
                "response": response.data,
                "dns_resolution": {
                    "hostname": hostname,
                    "ip_address": ip_address
                }
            }
        }
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to connect to the database",
            "error": str(e),
            "details": {
                "connection": "failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "supabase_url": settings.SUPABASE_URL,
                "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0
            }
        } 