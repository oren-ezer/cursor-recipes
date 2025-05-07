from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.supabase_client import get_supabase_client, get_supabase_admin_client  # Import client functions
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
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

# Startup event handler
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Supabase clients...")
    try:
        app.state.supabase = get_supabase_client()  # Store regular client
        app.state.supabase_admin = get_supabase_admin_client() # Store admin client
        logger.info("Supabase clients initialized and stored in app state.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase clients during startup: {e}")
        # Depending on the application's needs, you might want to raise the exception
        # or handle it differently (e.g., prevent the app from starting).

# Shutdown event handler (optional, as Supabase client doesn't strictly require explicit closing)
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    # If the Supabase client had a close method, you would call it here:
    # if hasattr(app.state, 'supabase') and hasattr(app.state.supabase, 'close'):
    #     await app.state.supabase.close()
    # if hasattr(app.state, 'supabase_admin') and hasattr(app.state.supabase_admin, 'close'):
    #     await app.state.supabase_admin.close()
    logger.info("Application shutdown complete.")

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