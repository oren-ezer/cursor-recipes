from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.core.supabase_client import get_supabase_client, get_supabase_admin_client  # Import client functions
from src.utils.dependencies import get_current_user
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
        raise e

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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    try:
        # Skip authentication for login and register endpoints
        if request.url.path in [f"{settings.API_V1_STR}/users/token", f"{settings.API_V1_STR}/users/register"]:
            logger.info(f"Skipping auth for path: {request.url.path}")
            return await call_next(request)
            
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        logger.info(f"Auth header: {auth_header}")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("No valid auth header found")
            request.state.user = None
            return await call_next(request)
            
        # Extract the token
        token = auth_header.split(" ")[1]
        logger.info(f"Token extracted: {token[:10]}...")
        
        # Get the current user
        user = await get_current_user(token)
        logger.info(f"User authenticated: {user.get('email') if user else 'None'}")
        request.state.user = user
        
    except Exception as e:
        logger.error(f"Auth middleware error: {str(e)}", exc_info=True)
        request.state.user = None
        
    return await call_next(request)

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
from src.api.v1.endpoints import users, recipes

app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(recipes.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Recipe API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 