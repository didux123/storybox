"""
FastAPI Backend - Main Application

Entry point for the StoryBox API backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.config import settings
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.api.v1.router import router as api_v1_router
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include API routers
app.include_router(api_v1_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler

    Log startup information and initialize resources.
    """
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"API endpoint: {settings.api_prefix}")
    logger.info(f"Documentation: /docs")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Rate limiting: {'enabled' if settings.rate_limit_enabled else 'disabled'}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler

    Clean up resources.
    """
    logger.info(f"Shutting down {settings.api_title}")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    Returns:
        Basic API information
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler

    Catches unhandled exceptions and returns structured error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={
        "path": request.url.path,
        "method": request.method
    })

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "error": {
                "type": type(exc).__name__,
                "details": str(exc)
            }
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting uvicorn server on {settings.host}:{settings.port}")

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower()
    )
