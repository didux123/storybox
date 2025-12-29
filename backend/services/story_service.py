"""
Story Service - Business logic for story generation

Orchestrates LLM, TTS, and STT modules to generate stories.
"""

import asyncio
import base64
import time
import uuid
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.llm.celeste_llm import CelesteLLM, StoryPlan
from app.tts.gradium_tts import GradiumTTS
from app.utils.config import get_config, LLMConfig
from app.utils.logger import get_logger

from backend.models.request import StoryRequest
from backend.models.response import StoryResponse, StoryData, StoryMetadata, ChapterInfo

logger = get_logger(__name__)


class StoryService:
    """
    Service for story generation and narration

    Handles the complete pipeline:
    1. Generate story plan using LLM
    2. Generate chapters with cumulative context
    3. (Optional) Generate audio narration using TTS
    """

    def __init__(self):
        """Initialize story service with default config"""
        self.config = get_config()
        self.logger = logger

    async def generate_story(self, request: StoryRequest) -> StoryResponse:
        """
        Generate a complete story based on request parameters

        Args:
            request: StoryRequest with generation parameters

        Returns:
            StoryResponse with story data or error

        Workflow:
            1. Initialize LLM with specified model
            2. Generate story plan
            3. Generate all chapters
            4. (If output_format=audio) Generate TTS narration
            5. Return response with metadata
        """
        start_time = time.time()
        story_id = str(uuid.uuid4())

        try:
            self.logger.info(f"Starting story generation: {story_id}", extra={
                "story_id": story_id,
                "prompt": request.prompt,
                "model": request.model,
                "num_chapters": request.num_chapters,
                "output_format": request.output_format
            })

            # Step 1: Initialize LLM with model-specific config
            llm_config = self._create_llm_config(request)
            llm = CelesteLLM(llm_config)

            # Step 2: Generate story plan
            self.logger.info(f"Generating story plan for: {request.prompt}")
            plan = await llm.generate_story_plan(
                theme=request.prompt,
                num_chapters=request.num_chapters,
                temperature=request.temperature
            )

            if not plan:
                raise ValueError("Failed to generate story plan")

            # Step 3: Generate all chapters
            self.logger.info(f"Generating {request.num_chapters} chapters")
            chapters_text = []
            cumulative_context = ""

            for chapter_num in range(1, request.num_chapters + 1):
                chapter_text = await llm.generate_chapter(
                    plan=plan,
                    chapter_num=chapter_num,
                    cumulative_context=cumulative_context,
                    min_words=request.min_words_per_chapter,
                    max_words=request.max_words_per_chapter,
                    temperature=request.temperature
                )

                if not chapter_text:
                    raise ValueError(f"Failed to generate chapter {chapter_num}")

                chapters_text.append(chapter_text)

                # Update cumulative context
                summary = plan.chapters[chapter_num - 1].get('summary', '')
                cumulative_context += f" Chapitre {chapter_num}: {summary}"

                self.logger.info(f"Chapter {chapter_num}/{request.num_chapters} generated")

            # Step 4: Combine chapters
            full_story_text = "\n\n".join([
                f"**Chapitre {i+1}: {plan.chapters[i]['title']}**\n\n{text}"
                for i, text in enumerate(chapters_text)
            ])

            # Step 5: Generate audio if requested
            output = full_story_text
            if request.output_format == "audio":
                self.logger.info("Generating TTS narration")
                output = await self._generate_audio(full_story_text, request.voice_id)

            # Step 6: Calculate metrics
            duration = time.time() - start_time
            metadata = self._calculate_metadata(
                model=request.model,
                text_input=request.prompt,
                text_output=full_story_text,
                duration=duration
            )

            # Step 7: Build response
            chapters_info = [
                ChapterInfo(
                    number=ch['number'],
                    title=ch['title'],
                    summary=ch['summary']
                )
                for ch in plan.chapters
            ]

            story_data = StoryData(
                story_id=story_id,
                theme=plan.theme,
                chapters=chapters_info,
                output=output,
                format=request.output_format,
                metadata=metadata
            )

            self.logger.info(f"Story generation completed: {story_id}", extra={
                "story_id": story_id,
                "duration": duration,
                "tokens": metadata.tokens_total,
                "cost": metadata.cost
            })

            return StoryResponse(
                status="success",
                message="Story generated successfully",
                data=story_data
            )

        except Exception as e:
            self.logger.error(f"Story generation failed: {story_id}", exc_info=True, extra={
                "story_id": story_id,
                "error": str(e)
            })

            return StoryResponse(
                status="error",
                message=f"Story generation failed: {str(e)}",
                error={
                    "type": type(e).__name__,
                    "details": str(e),
                    "story_id": story_id
                }
            )

    def _create_llm_config(self, request: StoryRequest) -> LLMConfig:
        """
        Create LLM config from request parameters

        Args:
            request: StoryRequest

        Returns:
            LLMConfig with model and temperature
        """
        # Use default config as base
        config = self.config.llm

        # Override model if specified
        config.model_path = request.model
        config.temperature = request.temperature

        # TODO: Handle model_api_key if provided (override env var)
        # This would require modifying how Celeste is initialized

        return config

    async def _generate_audio(self, text: str, voice_id: Optional[str] = None) -> str:
        """
        Generate TTS audio from text

        Args:
            text: Text to narrate
            voice_id: Optional voice ID

        Returns:
            Base64-encoded audio (WAV)

        Raises:
            ValueError: If TTS generation fails
        """
        try:
            tts = GradiumTTS(self.config)

            if not tts.client:
                raise ValueError("TTS client not initialized (GRADIUM_API_KEY missing)")

            # Generate audio bytes
            audio_bytes = await tts.generate_speech(
                text=text,
                voice_id=voice_id,
                output_format="wav",
                padding_bonus=0.0
            )

            if not audio_bytes:
                raise ValueError("TTS generation returned empty audio")

            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            self.logger.info("TTS audio generated successfully", extra={
                "audio_size_bytes": len(audio_bytes),
                "voice_id": voice_id
            })

            return audio_base64

        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}", exc_info=True)
            raise

    def _calculate_metadata(
        self,
        model: str,
        text_input: str,
        text_output: str,
        duration: float
    ) -> StoryMetadata:
        """
        Calculate generation metadata (tokens, cost)

        Args:
            model: Model ID used
            text_input: Input text (prompt)
            text_output: Generated text
            duration: Generation duration in seconds

        Returns:
            StoryMetadata with tokens and cost estimation
        """
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        tokens_input = len(text_input) // 4
        tokens_output = len(text_output) // 4
        tokens_total = tokens_input + tokens_output

        # Estimate cost based on model pricing
        cost = self._estimate_cost(model, tokens_input, tokens_output)

        return StoryMetadata(
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            duration=round(duration, 2),
            cost=round(cost, 6)
        )

    def _estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """
        Estimate generation cost based on model pricing

        Args:
            model: Model ID
            tokens_input: Input tokens
            tokens_output: Output tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing per 1M tokens (input, output)
        pricing = {
            "gemini-1.5-flash": (0.075, 0.30),
            "gemini-1.5-pro": (1.25, 5.00),
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (2.50, 10.00),
            "claude-3-5-sonnet-20241022": (3.00, 15.00),
            "claude-3-5-haiku-20241022": (0.80, 4.00),
            "mistral-large-2411": (2.00, 6.00),
            "mistral-small-2409": (0.20, 0.60)
        }

        input_price, output_price = pricing.get(model, (1.0, 3.0))  # Default fallback

        cost_input = (tokens_input / 1_000_000) * input_price
        cost_output = (tokens_output / 1_000_000) * output_price

        return cost_input + cost_output
