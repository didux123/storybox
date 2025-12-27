"""
Gradium STT Module
Provides speech-to-text functionality using Gradium API directly
"""

import os
import logging
from typing import Optional, AsyncIterator
from pathlib import Path
import asyncio

import gradium
from app.utils.config import Config
from app.utils.logger import get_logger


class GradiumSTT:
    """Speech-to-Text using Gradium API directly"""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Gradium STT

        Args:
            config: Optional configuration object. If None, loads from default.yaml
        """
        self.config = config or Config()
        self.logger = get_logger(__name__)

        # Get API key from environment
        api_key = os.getenv('GRADIUM_API_KEY')
        if not api_key:
            self.logger.warning("GRADIUM_API_KEY not found in environment")
            api_key = None

        # Initialize Gradium client
        self.client = gradium.client.GradiumClient(api_key=api_key) if api_key else None

        if self.client:
            self.logger.info("Gradium STT initialized successfully")
        else:
            self.logger.error("Failed to initialize Gradium STT: No API key")

    async def transcribe(
        self,
        audio_data: bytes,
        input_format: str = "wav",
        model_name: str = "default"
    ) -> Optional[str]:
        """
        Transcribe audio to text

        Args:
            audio_data: Audio data in bytes
            input_format: Audio format ("wav", "pcm", "opus")
            model_name: STT model to use (default: "default")

        Returns:
            Transcribed text or None if transcription failed

        Example:
            >>> stt = GradiumSTT()
            >>> with open("audio.wav", "rb") as f:
            ...     audio_data = f.read()
            >>> text = await stt.transcribe(audio_data)
            >>> print(text)
        """
        if not self.client:
            self.logger.error("STT client not initialized (missing API key)")
            return None

        try:
            self.logger.info(f"Transcribing {len(audio_data)} bytes of audio (format: {input_format})")

            # Create async generator for audio chunks
            async def audio_generator():
                # For simplicity, send the whole audio at once
                # In production, you might want to chunk it
                chunk_size = 1920  # 80ms at 24kHz for PCM
                for i in range(0, len(audio_data), chunk_size):
                    yield audio_data[i:i + chunk_size]
                    await asyncio.sleep(0)  # Yield control

            # Setup parameters for Gradium STT
            setup = {
                "model_name": model_name,
                "input_format": input_format
            }

            # Create STT stream
            stream = await gradium.speech.stt_stream(
                self.client,
                setup=setup,
                audio=audio_generator()
            )

            # Collect all transcribed text
            transcribed_text = []
            async for message in stream.iter_text():
                if message.text:
                    transcribed_text.append(message.text)
                    self.logger.debug(f"Received text: {message.text}")

            # Join all text segments
            full_text = " ".join(transcribed_text).strip()

            if full_text:
                self.logger.info(f"Transcription successful: {len(full_text)} characters")
                return full_text
            else:
                self.logger.warning("No text was transcribed")
                return None

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}", exc_info=True)
            return None

    async def transcribe_file(
        self,
        audio_path: str,
        input_format: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file
            input_format: Audio format (auto-detected from extension if None)

        Returns:
            Transcribed text or None if transcription failed

        Example:
            >>> stt = GradiumSTT()
            >>> text = await stt.transcribe_file("recording.wav")
            >>> print(text)
        """
        try:
            # Auto-detect format from file extension if not provided
            if input_format is None:
                ext = Path(audio_path).suffix.lower()
                format_map = {
                    ".wav": "wav",
                    ".pcm": "pcm",
                    ".opus": "opus",
                    ".ogg": "opus"
                }
                input_format = format_map.get(ext, "wav")

            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            self.logger.info(f"Transcribing file: {audio_path} ({input_format})")

            # Transcribe
            return await self.transcribe(audio_data, input_format)

        except Exception as e:
            self.logger.error(f"Failed to transcribe file {audio_path}: {e}", exc_info=True)
            return None


# Synchronous wrapper for easier use in non-async contexts
def transcribe_sync(
    audio_data: bytes,
    input_format: str = "wav",
    config: Optional[Config] = None
) -> Optional[str]:
    """
    Synchronous wrapper for transcription

    Args:
        audio_data: Audio data in bytes
        input_format: Audio format
        config: Optional configuration

    Returns:
        Transcribed text or None if failed

    Example:
        >>> with open("audio.wav", "rb") as f:
        ...     audio_data = f.read()
        >>> text = transcribe_sync(audio_data)
    """
    stt = GradiumSTT(config)
    return asyncio.run(stt.transcribe(audio_data, input_format))


def transcribe_file_sync(
    audio_path: str,
    input_format: Optional[str] = None,
    config: Optional[Config] = None
) -> Optional[str]:
    """
    Synchronous wrapper for file transcription

    Args:
        audio_path: Path to audio file
        input_format: Audio format (auto-detected if None)
        config: Optional configuration

    Returns:
        Transcribed text or None if failed

    Example:
        >>> text = transcribe_file_sync("recording.wav")
    """
    stt = GradiumSTT(config)
    return asyncio.run(stt.transcribe_file(audio_path, input_format))
