from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
import logging
import os
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_supabase_url(postgres_url: str) -> str:
    """Extract Supabase URL from PostgreSQL connection string."""
    try:
        # Extract project ID from the PostgreSQL URL
        match = re.search(r'@db\.([^.]+)\.supabase\.co', postgres_url)
        if match:
            project_id = match.group(1)
            return f"https://{project_id}.supabase.co"
        return None
    except Exception as e:
        logger.error(f"Failed to extract Supabase URL: {str(e)}")
        return None

class Settings(BaseSettings):
    PROJECT_NAME: str = "Recipe API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A web application that allows users to store, manage, and share food recipes"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    DATABASE_URL: str
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    class Config:
        case_sensitive = True
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # If SUPABASE_URL is a PostgreSQL connection string, extract the Supabase URL
        if self.SUPABASE_URL.startswith("postgresql://"):
            logger.info("Detected PostgreSQL connection string. Extracting Supabase URL...")
            extracted_url = extract_supabase_url(self.SUPABASE_URL)
            if extracted_url:
                logger.info(f"Extracted Supabase URL: {extracted_url}")
                self.SUPABASE_URL = extracted_url
            else:
                logger.error("Failed to extract Supabase URL from PostgreSQL connection string")

# Log environment variables
logger.info(f"Environment file exists: {os.path.exists('.env')}")
logger.info(f"Current working directory: {os.getcwd()}")

settings = Settings()

# Log loaded settings
logger.info(f"Loaded SUPABASE_URL: {settings.SUPABASE_URL}")
logger.info(f"Loaded SUPABASE_KEY length: {len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0}")
logger.info(f"Loaded SUPABASE_SERVICE_KEY length: {len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0}") 