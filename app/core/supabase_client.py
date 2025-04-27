from supabase import create_client, Client
from app.core.config import settings
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instances
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    """
    global _supabase_client
    if _supabase_client is None:
        try:
            logger.info(f"Initializing Supabase client with URL: {settings.SUPABASE_URL}")
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    return _supabase_client

def get_supabase_admin_client() -> Client:
    """
    Get the Supabase admin client instance with service role key.
    Use this for operations that require admin privileges.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        try:
            logger.info(f"Initializing Supabase admin client with URL: {settings.SUPABASE_URL}")
            _supabase_admin_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase admin client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {str(e)}")
            raise
    return _supabase_admin_client 