from src.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Testing configuration...")
    logger.info(f"SUPABASE_URL: {settings.SUPABASE_URL}")
    logger.info(f"SUPABASE_KEY length: {len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0}")
    logger.info(f"SUPABASE_SERVICE_KEY length: {len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0}")
    logger.info(f"DATABASE_URL: {settings.DATABASE_URL}")

if __name__ == "__main__":
    main() 