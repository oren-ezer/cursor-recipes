from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.utils.dependencies import _get_current_user_from_token
import logging

logger = logging.getLogger(__name__)

# New lifespan context manager
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup: Application initialization
    logger.info("Lifespan: Initializing application...")
    
    yield  # Application runs here

    # Shutdown: Clean up resources (if any)
    logger.info("Lifespan: Shutting down application...")
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
        # Skip authentication for public endpoints
        public_endpoints = [
            ("/", "GET"),  # Root endpoint
            (f"{settings.API_V1_STR}/users/token", "POST"),  # Login
            (f"{settings.API_V1_STR}/users/register", "POST"),  # Register
            (f"{settings.API_V1_STR}/recipes", "GET"),  # Public recipes list
            (f"{settings.API_V1_STR}/tags", "GET"),  # Public tags list
            (f"{settings.API_V1_STR}/tags/search", "GET"),  # Public tags search
            (f"{settings.API_V1_STR}/tags/popular", "GET"),  # Public popular tags
        ]
        
        # Skip auth for public endpoints (path + method)
        current_endpoint = (request.url.path, request.method)
        if current_endpoint in public_endpoints:
            logger.info(f"Skipping auth for public endpoint: {request.method} {request.url.path}")
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
        
        # Get the current user using a database session
        from src.utils.database_session import engine
        from sqlmodel import Session as SQLModelSession
        from src.services.user_service import UserService
        
        with SQLModelSession(engine) as session:
            user_service = UserService(session)
            user = await _get_current_user_from_token(user_service, token)
            logger.info("User authentication successful")
            request.state.user = user
        
    except HTTPException:
        # Let HTTPExceptions pass through (like 401 Unauthorized)
        request.state.user = None
        return await call_next(request)
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
from src.api.v1.endpoints import users, recipes, admin, tags, ai, llm_config

app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(recipes.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(tags.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(llm_config.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Recipe API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 