"""
Request models for StoryBox API

Pydantic models for API request validation.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class StoryRequest(BaseModel):
    """
    Request model for story generation endpoint

    Attributes:
        prompt: Theme or description of the story
        model: LLM model to use (default: mistral-large-2411)
        model_api_key: API key for the specified model (optional, overrides env)
        output_format: Output format - "text" or "audio"
        num_chapters: Number of chapters to generate (3-10)
        voice_id: TTS voice ID (required if output_format="audio")
        temperature: Generation temperature (0.1-1.0)
        min_words_per_chapter: Minimum words per chapter
        max_words_per_chapter: Maximum words per chapter
    """

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Theme or description of the story"
    )

    model: str = Field(
        default="mistral-large-latest",
        description="LLM model to use (mistral-large-latest, gemini-1.5-flash, gpt-4o-mini, claude-3-5-sonnet-20241022, etc.)"
    )

    model_api_key: Optional[str] = Field(
        default=None,
        description="API key for the specified model (overrides environment variable)"
    )

    output_format: Literal["text", "audio"] = Field(
        default="text",
        description="Output format: 'text' or 'audio'"
    )

    num_chapters: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Number of chapters (3-10)"
    )

    voice_id: Optional[str] = Field(
        default=None,
        description="TTS voice ID (required if output_format='audio')"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Generation temperature (0.1-1.0)"
    )

    min_words_per_chapter: int = Field(
        default=150,
        ge=50,
        le=500,
        description="Minimum words per chapter"
    )

    max_words_per_chapter: int = Field(
        default=300,
        ge=100,
        le=1000,
        description="Maximum words per chapter"
    )

    @validator('voice_id')
    def validate_voice_id_for_audio(cls, v, values):
        """Validate that voice_id is provided when output_format is 'audio'"""
        if values.get('output_format') == 'audio' and not v:
            raise ValueError("voice_id is required when output_format='audio'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Un robot qui découvre les émotions",
                "model": "mistral-large-latest",
                "output_format": "text",
                "num_chapters": 5,
                "temperature": 0.7,
                "min_words_per_chapter": 150,
                "max_words_per_chapter": 300
            }
        }
