from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.supabase_client import get_supabase_client, get_supabase_admin_client  # Import client functions
import logging

logger = logging.getLogger(__name__)

# New lifespan context manager
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup: Initialize Supabase clients
    logger.info("Lifespan: Initializing Supabase clients...")
    try:
        app_instance.state.supabase = get_supabase_client()
        app_instance.state.supabase_admin = get_supabase_admin_client()
        logger.info("Lifespan: Supabase clients initialized and stored in app state.")
    except Exception as e:
        logger.error(f"Lifespan: Failed to initialize Supabase clients: {e}")
        # Optionally re-raise or handle to prevent app startup on critical failure

    yield  # Application runs here

    # Shutdown: Clean up resources (if any)
    logger.info("Lifespan: Shutting down application...")
    # If Supabase clients had explicit close methods, call them here
    # e.g., if hasattr(app_instance.state, 'supabase') and hasattr(app_instance.state.supabase, 'close'):
    #     await app_instance.state.supabase.close()
    logger.info("Lifespan: Application shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan # Added lifespan manager
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generic Exception Handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# HTTPException Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

# Request Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # You can customize the error details further if needed, e.g., by iterating through exc.errors()
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

# Import and include routers
from app.api.v1.endpoints import users, recipes

app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(recipes.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Recipe API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 