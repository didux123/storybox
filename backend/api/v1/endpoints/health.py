"""
Health check endpoint
"""

from fastapi import APIRouter
from backend.models.response import HealthResponse
from backend import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns:
        HealthResponse with status and version
    """
    return HealthResponse(
        status="healthy",
        version=__version__
    )
