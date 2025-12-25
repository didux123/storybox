"""
Gradium TTS Module
Provides text-to-speech functionality using Gradium API directly
"""

import os
import logging
from typing import Optional
from pathlib import Path
import asyncio
from io import BytesIO

import gradium
from app.utils.config import Config
from app.utils.logger import get_logger


class GradiumTTS:
    """Text-to-Speech using Gradium API directly"""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Gradium TTS

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
            self.logger.info("Gradium TTS initialized successfully")
        else:
            self.logger.error("Failed to initialize Gradium TTS: No API key")

    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_format: str = "wav",
        padding_bonus: float = 0.0
    ) -> Optional[bytes]:
        """
        Generate speech audio from text

        Args:
            text: Text to convert to speech
            voice_id: Gradium voice ID (e.g., "YTpq7expH9539ERJ" for Emma)
                     or voice name (e.g., "Emma", "Elise", "Alice")
            output_format: Audio format ("wav", "pcm", "opus")
            padding_bonus: Speed control (-4.0 to 4.0)
                          Negative = faster, Positive = slower, 0.0 = normal

        Returns:
            Audio bytes or None if generation failed

        Example:
            >>> tts = GradiumTTS()
            >>> audio = await tts.generate_speech("Hello world", voice_id="YTpq7expH9539ERJ")
            >>> with open("output.wav", "wb") as f:
            ...     f.write(audio)
        """
        if not self.client:
            self.logger.error("TTS client not initialized (missing API key)")
            return None

        try:
            self.logger.info(f"Generating speech for {len(text)} characters with voice={voice_id}, padding_bonus={padding_bonus}")

            # Build setup parameters
            setup = {
                "output_format": output_format
            }

            # Add voice_id if provided
            if voice_id:
                setup["voice_id"] = voice_id

            # Add padding_bonus if not default
            if padding_bonus != 0.0:
                setup["json_config"] = {"padding_bonus": padding_bonus}

            # Generate speech using Gradium API
            result = await gradium.speech.tts(
                self.client,
                setup=setup,
                text=text
            )

            # Extract audio bytes
            audio_bytes = result.raw_data
            self.logger.info(f"Generated {len(audio_bytes)} bytes of audio")
            return audio_bytes

        except Exception as e:
            self.logger.error(f"Speech generation failed: {e}", exc_info=True)
            return None

    async def generate_to_file(
        self,
        text: str,
        output_path: str,
        voice_id: Optional[str] = None,
        output_format: str = "wav",
        padding_bonus: float = 0.0
    ) -> bool:
        """
        Generate speech and save to file

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice_id: Gradium voice ID
            output_format: Audio format
            padding_bonus: Speed control

        Returns:
            True if successful, False otherwise

        Example:
            >>> tts = GradiumTTS()
            >>> success = await tts.generate_to_file(
            ...     "Hello world",
            ...     "output.wav",
            ...     voice_id="YTpq7expH9539ERJ"
            ... )
        """
        audio_bytes = await self.generate_speech(text, voice_id, output_format, padding_bonus)

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
            >>> tts = GradiumTTS()
            >>> audio = await tts.generate_speech("Hello")
            >>> stream = tts.get_audio_stream(audio)
            >>> # Can be used with st.audio() in Streamlit
        """
        return BytesIO(audio_bytes)


# Synchronous wrapper for easier use in non-async contexts
def generate_speech_sync(
    text: str,
    voice_id: Optional[str] = None,
    padding_bonus: float = 0.0,
    config: Optional[Config] = None
) -> Optional[bytes]:
    """
    Synchronous wrapper for speech generation

    Args:
        text: Text to convert to speech
        voice_id: Gradium voice ID or name
        padding_bonus: Speed control
        config: Optional configuration

    Returns:
        Audio bytes or None if failed

    Example:
        >>> audio = generate_speech_sync("Hello world", voice_id="YTpq7expH9539ERJ")
    """
    tts = GradiumTTS(config)
    return asyncio.run(tts.generate_speech(text, voice_id, padding_bonus=padding_bonus))


def generate_to_file_sync(
    text: str,
    output_path: str,
    voice_id: Optional[str] = None,
    padding_bonus: float = 0.0,
    config: Optional[Config] = None
) -> bool:
    """
    Synchronous wrapper for file generation

    Args:
        text: Text to convert to speech
        output_path: Path to save audio
        voice_id: Gradium voice ID or name
        padding_bonus: Speed control
        config: Optional configuration

    Returns:
        True if successful

    Example:
        >>> success = generate_to_file_sync("Hello", "out.wav", voice_id="YTpq7expH9539ERJ")
    """
    tts = GradiumTTS(config)
    return asyncio.run(tts.generate_to_file(text, output_path, voice_id, padding_bonus=padding_bonus))
