"""
Story generation endpoint
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.models.request import StoryRequest
from backend.models.response import StoryResponse
from backend.services.story_service import StoryService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/generate-story", response_model=StoryResponse, tags=["Story"])
async def generate_story(request: StoryRequest):
    """
    Generate a story based on the provided prompt

    Args:
        request: StoryRequest with generation parameters

    Returns:
        StoryResponse with generated story or error

    Raises:
        HTTPException: If validation fails (handled by Pydantic)

    Example request:
        ```json
        {
            "prompt": "Un robot qui découvre les émotions",
            "model": "mistral-large-2411",
            "output_format": "text",
            "num_chapters": 5,
            "temperature": 0.7
        }
        ```

    Example response (success):
        ```json
        {
            "status": "success",
            "message": "Story generated successfully",
            "data": {
                "story_id": "uuid",
                "theme": "Un robot qui découvre les émotions",
                "chapters": [...],
                "output": "text or base64_audio",
                "format": "text",
                "metadata": {
                    "model": "mistral-large-2411",
                    "tokens_total": 1650,
                    "duration": 8.5,
                    "cost": 0.0025
                }
            }
        }
        ```
    """
    logger.info(f"Received story generation request", extra={
        "prompt": request.prompt,
        "model": request.model,
        "output_format": request.output_format,
        "num_chapters": request.num_chapters
    })

    try:
        # Initialize service and generate story
        service = StoryService()
        response = await service.generate_story(request)

        # Log result
        if response.status == "success":
            logger.info("Story generated successfully", extra={
                "story_id": response.data.story_id if response.data else None,
                "duration": response.data.metadata.duration if response.data else None
            })
        else:
            logger.warning("Story generation returned error", extra={
                "error": response.error
            })

        return response

    except Exception as e:
        logger.error(f"Unexpected error in endpoint: {e}", exc_info=True)

        # Return error response
        return StoryResponse(
            status="error",
            message="Internal server error",
            error={
                "type": "InternalServerError",
                "details": str(e)
            }
        )
