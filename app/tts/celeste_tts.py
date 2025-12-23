"""
Celeste TTS Module
Provides text-to-speech functionality using Celeste AI (Gradium provider)
"""

import os
import logging
from typing import Optional, BinaryIO
from pathlib import Path
import asyncio
from io import BytesIO

from celeste import create_client, Capability, Provider
from app.utils.config import Config
from app.utils.logger import get_logger


class CelesteTTS:
    """Text-to-Speech using Celeste AI with Gradium provider"""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Celeste TTS

        Args:
            config: Optional configuration object. If None, loads from default.yaml
        """
        self.config = config or Config()
        self.logger = get_logger(__name__)

        # Initialize Celeste client for speech generation
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Celeste client with Gradium provider"""
        try:
            # Create client for speech generation with Gradium
            self.client = create_client(
                Capability.SPEECH_GENERATION,
                Provider.GRADIUM
            )
            self.logger.info("Celeste TTS initialized with Gradium provider")
        except Exception as e:
            self.logger.error(f"Failed to initialize Celeste TTS: {e}", exc_info=True)
            raise

    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        response_format: str = "mp3_44100_128"
    ) -> Optional[bytes]:
        """
        Generate speech audio from text

        Args:
            text: Text to convert to speech
            voice: Gradium voice name (e.g., "Elise", "Alice", "Eva", "Mia")
            response_format: Audio format (e.g., "mp3_44100_128")

        Returns:
            Audio bytes or None if generation failed

        Note:
            Speed parameter is not currently supported due to Celeste/Gradium compatibility issues.
            Future implementation may use Gradium's padding_bonus parameter.

        Example:
            >>> tts = CelesteTTS()
            >>> audio = await tts.generate_speech("Hello world", voice="Elise")
            >>> with open("output.mp3", "wb") as f:
            ...     f.write(audio)
        """
        if not self.client:
            self.logger.error("TTS client not initialized")
            return None

        try:
            self.logger.info(f"Generating speech for {len(text)} characters with voice={voice}")

            # Build parameters for Gradium via Celeste
            params = {
                "text": text,
                "response_format": response_format
            }

            # Add voice if provided
            if voice:
                params["voice"] = voice

            # Generate speech
            response = await self.client.generate(**params)

            # Extract audio bytes from response.content.data
            if hasattr(response, 'content') and hasattr(response.content, 'data'):
                audio_bytes = response.content.data
                self.logger.info(f"Generated {len(audio_bytes)} bytes of audio")
                return audio_bytes
            else:
                self.logger.error("Unexpected response format from Celeste TTS")
                return None

        except Exception as e:
            self.logger.error(f"Speech generation failed: {e}", exc_info=True)
            return None

    async def generate_to_file(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        response_format: str = "mp3_44100_128"
    ) -> bool:
        """
        Generate speech and save to file

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice: Gradium voice name (e.g., "Elise", "Alice")
            response_format: Audio format

        Returns:
            True if successful, False otherwise

        Example:
            >>> tts = CelesteTTS()
            >>> success = await tts.generate_to_file(
            ...     "Hello world",
            ...     "output.mp3",
            ...     voice="Elise"
            ... )
        """
        audio_bytes = await self.generate_speech(text, voice, response_format)

        if not audio_bytes:
            return False

        try:
            # Create parent directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Write audio to file
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)

            self.logger.info(f"Audio saved to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save audio to {output_path}: {e}", exc_info=True)
            return False

    def get_audio_stream(self, audio_bytes: bytes) -> BytesIO:
        """
        Convert audio bytes to a file-like stream for playback

        Args:
            audio_bytes: Audio data in bytes

        Returns:
            BytesIO stream containing the audio

        Example:
            >>> tts = CelesteTTS()
            >>> audio = await tts.generate_speech("Hello")
            >>> stream = tts.get_audio_stream(audio)
            >>> # Can be used with st.audio() in Streamlit
        """
        return BytesIO(audio_bytes)


# Synchronous wrapper for easier use in non-async contexts
def generate_speech_sync(
    text: str,
    voice: Optional[str] = None,
    config: Optional[Config] = None
) -> Optional[bytes]:
    """
    Synchronous wrapper for speech generation

    Args:
        text: Text to convert to speech
        voice: Gradium voice name (e.g., "Elise", "Alice")
        config: Optional configuration

    Returns:
        Audio bytes or None if failed

    Example:
        >>> audio = generate_speech_sync("Hello world", voice="Elise")
    """
    tts = CelesteTTS(config)
    return asyncio.run(tts.generate_speech(text, voice))


def generate_to_file_sync(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    config: Optional[Config] = None
) -> bool:
    """
    Synchronous wrapper for file generation

    Args:
        text: Text to convert to speech
        output_path: Path to save audio
        voice: Gradium voice name (e.g., "Elise", "Alice")
        config: Optional configuration

    Returns:
        True if successful

    Example:
        >>> success = generate_to_file_sync("Hello", "out.mp3", voice="Elise")
    """
    tts = CelesteTTS(config)
    return asyncio.run(tts.generate_to_file(text, output_path, voice))
