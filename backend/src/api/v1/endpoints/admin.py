from fastapi import APIRouter, Request
from src.core.config import settings
from src.utils.db import Database
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admins", tags=["admins"])

@router.get("/test-supabase")
async def test_supabase_connection(request: Request):
    """
    Test endpoint to verify Supabase connection from app state.
    """
    try:
        # Test connection by executing a simple query
        logger.info("Testing connection with a simple query...")
        users = Database.select("users", limit=1)
        
        return {
            "status": "success",
            "message": "Successfully connected to Supabase via Database utility",
            "data": users
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
async def test_db_connection(request: Request):
    """
    Test the connection to the Supabase database via Database utility.
    
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
        
        # Test database connection via Database utility
        logger.info("Testing database connection via Database utility...")
        users = Database.select("users", limit=1)
        
        return {
            "status": "success",
            "message": "Successfully connected to the database via Database utility",
            "details": {
                "connection": "established",
                "query": "executed successfully",
                "response": users,
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