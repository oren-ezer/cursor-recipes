from supabase import create_client, Client
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: Global client instances (_supabase_client, _supabase_admin_client) are removed
# as the client is now managed via app.state

def get_supabase_client() -> Client:
    """
    Create and return a new Supabase client instance.
    This function is typically called once during application startup.
    """
    try:
        logger.info(f"Creating Supabase client with URL: {settings.SUPABASE_URL}")
        client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
        logger.info("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise

def get_supabase_admin_client() -> Client:
    """
    Create and return a new Supabase admin client instance with service role key.
    This function is typically called once during application startup.
    """
    try:
        logger.info(f"Creating Supabase admin client with URL: {settings.SUPABASE_URL}")
        admin_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY
        )
        logger.info("Supabase admin client created successfully")
        return admin_client
    except Exception as e:
        logger.error(f"Failed to create Supabase admin client: {str(e)}")
        raise 