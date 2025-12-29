"""
API V1 Router

Aggregates all V1 endpoints.
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import health, story

router = APIRouter()

# Include endpoint routers
router.include_router(health.router)
router.include_router(story.router)
