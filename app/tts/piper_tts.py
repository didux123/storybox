"""
Piper TTS Wrapper for StoryBox IA

Handles text-to-speech conversion using Piper neural TTS.
Optimized for Raspberry Pi with French voice models.

Features:
- Streaming audio generation (sentence by sentence)
- Audio post-processing (normalization, compression)
- Memory-efficient for Pi
- Real-time playback support

Usage:
    from app.tts.piper_tts import PiperTTS

    tts = PiperTTS(config.tts)
    audio_data = tts.synthesize("Bonjour, voici une histoire.")
    tts.play_audio(audio_data)

Author: StoryBox IA Team
Date: 2024-12
"""

import subprocess
import tempfile
import wave
import numpy as np
from pathlib import Path
from typing import Optional, Generator
from dataclasses import dataclass

from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import TTSConfig


logger = get_logger(__name__)


@dataclass
class AudioChunk:
    """
    Audio chunk for streaming playback

    Attributes:
        data: PCM audio data (int16)
        sample_rate: Sample rate in Hz
        channels: Number of channels (1=mono, 2=stereo)
    """
    data: np.ndarray
    sample_rate: int
    channels: int


class PiperTTS:
    """
    Piper TTS engine wrapper

    Converts text to natural-sounding French speech using neural TTS.
    Optimized for low-latency streaming on Raspberry Pi.
    """

    def __init__(self, config: TTSConfig):
        """
        Initialize Piper TTS

        Args:
            config: TTS configuration object

        Raises:
            FileNotFoundError: If model files don't exist
            RuntimeError: If piper command not found
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Validate model files exist
        if not Path(config.model_path).exists():
            raise FileNotFoundError(f"Piper model not found: {config.model_path}")

        if not Path(config.config_path).exists():
            raise FileNotFoundError(f"Piper config not found: {config.config_path}")

        # Check if piper command is available
        try:
            subprocess.run(['piper', '--version'], capture_output=True, check=True)
            self.logger.info("Piper TTS initialized successfully")
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError(
                "Piper command not found. Install: pip install piper-tts"
            )

        self.logger.info(f"Loaded model: {Path(config.model_path).name}")
        self.logger.info(f"Sample rate: {config.sample_rate} Hz")
        self.logger.info(f"Speaker ID: {config.speaker_id}")

    def synthesize(self, text: str) -> Optional[bytes]:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech (French)

        Returns:
            WAV audio data as bytes, or None if synthesis failed

        Example:
            >>> tts = PiperTTS(config.tts)
            >>> audio = tts.synthesize("Bonjour le monde!")
            >>> # audio is WAV format bytes
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for synthesis")
            return None

        self.logger.debug(f"Synthesizing: {text[:50]}...")

        with TimingContext("tts_synthesis", log_metric=True):
            try:
                # Use temporary file for output
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_path = tmp_file.name

                # Run Piper command
                cmd = [
                    'piper',
                    '-m', str(self.config.model_path),
                    '-f', tmp_path
                ]

                # Add optional parameters
                if self.config.speaker_id is not None:
                    cmd.extend(['-s', str(self.config.speaker_id)])

                result = subprocess.run(
                    cmd,
                    input=text,
                    text=True,
                    capture_output=True,
                    check=True
                )

                # Read generated WAV file
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()

                # Clean up temp file
                Path(tmp_path).unlink()

                # Log metrics
                audio_size_kb = len(audio_data) / 1024
                self.logger.info(f"Generated {audio_size_kb:.1f} KB audio for {len(text)} chars")
                log_metric("tts_audio_size_kb", audio_size_kb)
                log_metric("tts_chars_synthesized", len(text))

                return audio_data

            except subprocess.CalledProcessError as e:
                self.logger.error(f"Piper synthesis failed: {e.stderr}")
                return None
            except Exception as e:
                self.logger.error(f"TTS synthesis error: {e}", exc_info=True)
                return None

    def synthesize_streaming(self, text: str, sentence_split: bool = True) -> Generator[AudioChunk, None, None]:
        """
        Synthesize speech with streaming (sentence by sentence)

        For long texts, this generates audio incrementally to reduce latency.
        Useful for narrating chapters while generating next sentences.

        Args:
            text: Text to synthesize
            sentence_split: Split by sentences for streaming

        Yields:
            AudioChunk objects with audio data

        Example:
            >>> tts = PiperTTS(config.tts)
            >>> for chunk in tts.synthesize_streaming(long_story):
            ...     play_audio(chunk)  # Play while generating
        """
        if sentence_split:
            # Split into sentences (basic approach)
            sentences = self._split_sentences(text)
        else:
            sentences = [text]

        self.logger.info(f"Streaming synthesis: {len(sentences)} sentences")

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            self.logger.debug(f"Synthesizing sentence {i+1}/{len(sentences)}")

            # Synthesize sentence
            audio_bytes = self.synthesize(sentence)
            if audio_bytes:
                # Convert WAV bytes to AudioChunk
                chunk = self._wav_to_chunk(audio_bytes)
                if chunk:
                    yield chunk

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for streaming

        Uses simple heuristics (., !, ?) to split text.
        More sophisticated splitting could use spaCy or NLTK.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re

        # Split on . ! ? followed by space or newline
        sentences = re.split(r'[.!?]+\s+', text)

        # Filter empty sentences
        return [s.strip() for s in sentences if s.strip()]

    def _wav_to_chunk(self, wav_data: bytes) -> Optional[AudioChunk]:
        """
        Convert WAV bytes to AudioChunk

        Args:
            wav_data: WAV file as bytes

        Returns:
            AudioChunk or None if conversion failed
        """
        try:
            # Write to temp file to read with wave module
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(wav_data)
                tmp_path = tmp.name

            # Read WAV data
            with wave.open(tmp_path, 'rb') as wav:
                sample_rate = wav.getframerate()
                channels = wav.getnchannels()
                frames = wav.readframes(wav.getnframes())

                # Convert to numpy array (int16)
                audio_data = np.frombuffer(frames, dtype=np.int16)

            # Clean up
            Path(tmp_path).unlink()

            return AudioChunk(
                data=audio_data,
                sample_rate=sample_rate,
                channels=channels
            )

        except Exception as e:
            self.logger.error(f"Failed to convert WAV to chunk: {e}")
            return None

    def post_process_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply post-processing to audio

        Applies:
        - Noise gate (remove low-level noise)
        - Compression (even out volume)
        - Normalization (target LUFS level)

        Args:
            audio_data: Raw audio data (int16)

        Returns:
            Processed audio data (int16)

        Note:
            This is a simplified version. For production, consider:
            - Using FFmpeg for professional audio processing
            - Applying these via external tools during model preparation
        """
        # Convert to float for processing
        audio_float = audio_data.astype(np.float32) / 32768.0

        # Noise gate (simple threshold-based)
        threshold = self.config.post_processing.noise_gate_threshold
        threshold_linear = 10 ** (threshold / 20.0)
        audio_float[np.abs(audio_float) < threshold_linear] = 0

        # Simple compression (reduce dynamic range)
        ratio = self.config.post_processing.compressor_ratio
        threshold_comp = 0.5
        above_threshold = np.abs(audio_float) > threshold_comp
        if np.any(above_threshold):
            excess = np.abs(audio_float[above_threshold]) - threshold_comp
            audio_float[above_threshold] = np.sign(audio_float[above_threshold]) * (
                threshold_comp + excess / ratio
            )

        # Normalize to target level (simple peak normalization)
        peak = np.abs(audio_float).max()
        if peak > 0:
            target_peak = 0.9  # Leave some headroom
            audio_float = audio_float * (target_peak / peak)

        # Convert back to int16
        audio_int16 = (audio_float * 32768.0).astype(np.int16)

        return audio_int16

    def save_audio(self, audio_data: bytes, output_path: Path):
        """
        Save audio data to WAV file

        Args:
            audio_data: Audio data (WAV format bytes)
            output_path: Path to save WAV file
        """
        with open(output_path, 'wb') as f:
            f.write(audio_data)

        self.logger.info(f"Saved audio to {output_path}")

    def get_audio_duration(self, audio_data: bytes) -> float:
        """
        Get duration of audio in seconds

        Args:
            audio_data: WAV audio data

        Returns:
            Duration in seconds
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            with wave.open(tmp_path, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate)

            Path(tmp_path).unlink()
            return duration

        except Exception as e:
            self.logger.error(f"Failed to get audio duration: {e}")
            return 0.0


def test_piper_tts():
    """
    Simple test function for Piper TTS

    Run this to verify TTS is working correctly.

    Usage:
        python -m app.tts.piper_tts
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("Piper TTS Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Initialize TTS
    try:
        tts = PiperTTS(config.tts)
        print("✓ TTS initialized")
    except Exception as e:
        print(f"✗ Failed to initialize TTS: {e}")
        return

    # Test synthesis
    test_texts = [
        "Bonjour, je suis la boîte à histoires.",
        "Chapitre premier : Le début de l'aventure.",
        "Il était une fois, dans un petit village, un jeune garçon nommé Lucas."
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        audio = tts.synthesize(text)

        if audio:
            duration = tts.get_audio_duration(audio)
            size_kb = len(audio) / 1024
            print(f"✓ Generated {size_kb:.1f} KB ({duration:.1f}s)")

            # Save to test file
            output_file = Path(f"test_tts_output_{i}.wav")
            tts.save_audio(audio, output_file)
            print(f"  Saved to: {output_file}")
        else:
            print(f"✗ Synthesis failed")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("Play audio: afplay test_tts_output_*.wav")
    print("=" * 60)


if __name__ == "__main__":
    # Run test when module is executed directly
    test_piper_tts()
