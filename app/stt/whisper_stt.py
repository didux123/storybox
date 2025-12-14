"""
Whisper STT Wrapper for StoryBox IA

Handles speech-to-text transcription using whisper.cpp.
Optimized for French language recognition on Raspberry Pi.

Features:
- Fast transcription with quantized models
- Multi-threading support for Pi
- VAD (Voice Activity Detection) optional
- Audio preprocessing (normalization, noise reduction)

Usage:
    from app.stt.whisper_stt import WhisperSTT

    stt = WhisperSTT(config.stt)
    text = stt.transcribe_file("recording.wav")
    print(f"Transcribed: {text}")

Author: StoryBox IA Team
Date: 2024-12
"""

import subprocess
import tempfile
import wave
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import STTConfig


logger = get_logger(__name__)


class WhisperSTT:
    """
    Whisper Speech-to-Text engine wrapper

    Transcribes French speech to text using whisper.cpp.
    Optimized for low-latency inference on Raspberry Pi.
    """

    def __init__(self, config: STTConfig, whisper_bin_path: Optional[Path] = None):
        """
        Initialize Whisper STT

        Args:
            config: STT configuration object
            whisper_bin_path: Optional custom path to whisper-cli binary
                              Defaults to checking common locations

        Raises:
            FileNotFoundError: If model or binary not found
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Validate model exists
        if not Path(config.model_path).exists():
            raise FileNotFoundError(f"Whisper model not found: {config.model_path}")

        # Find whisper-cli binary
        self.whisper_bin = self._find_whisper_binary(whisper_bin_path)

        self.logger.info("Whisper STT initialized successfully")
        self.logger.info(f"Binary: {self.whisper_bin}")
        self.logger.info(f"Model: {Path(config.model_path).name}")
        self.logger.info(f"Language: {config.language}")
        self.logger.info(f"Threads: {config.threads}")

    def _find_whisper_binary(self, custom_path: Optional[Path] = None) -> Path:
        """
        Find whisper-cli binary

        Checks (in order):
        1. Custom path if provided
        2. Project bin/ directory
        3. /tmp/whisper.cpp/build/bin (Mac development)
        4. System PATH

        Args:
            custom_path: Optional custom binary path

        Returns:
            Path to whisper-cli binary

        Raises:
            FileNotFoundError: If binary not found
        """
        if custom_path and custom_path.exists():
            return custom_path

        # Common locations
        search_paths = [
            # Project bin (after deployment)
            Path(__file__).parent.parent.parent / "bin" / "whisper-cli",
            # Mac development location
            Path("/tmp/whisper.cpp/build/bin/whisper-cli"),
            # Raspberry Pi build location
            Path.home() / "projects" / "storybox" / "bin" / "whisper-cli",
        ]

        for path in search_paths:
            if path.exists() and path.is_file():
                self.logger.info(f"Found whisper-cli at: {path}")
                return path

        # Try system PATH
        try:
            result = subprocess.run(
                ['which', 'whisper-cli'],
                capture_output=True,
                text=True,
                check=True
            )
            path = Path(result.stdout.strip())
            if path.exists():
                return path
        except subprocess.CalledProcessError:
            pass

        raise FileNotFoundError(
            "whisper-cli not found. Compile whisper.cpp or specify whisper_bin_path. "
            "See docs/MAC_DEVELOPMENT.md or docs/RASPBERRY_PI_SETUP.md"
        )

    def transcribe_file(self, audio_path: Path) -> Optional[str]:
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file (WAV, 16kHz mono recommended)

        Returns:
            Transcribed text or None if transcription failed

        Example:
            >>> stt = WhisperSTT(config.stt)
            >>> text = stt.transcribe_file(Path("recording.wav"))
            >>> print(text)
            "Raconte-moi une histoire sur les pirates."
        """
        if not audio_path.exists():
            self.logger.error(f"Audio file not found: {audio_path}")
            return None

        self.logger.info(f"Transcribing: {audio_path.name}")

        with TimingContext("stt_transcription", log_metric=True):
            try:
                # Build whisper command
                cmd = [
                    str(self.whisper_bin),
                    '-m', str(self.config.model_path),
                    '-l', self.config.language,
                    '-t', str(self.config.threads),
                    '-f', str(audio_path),
                    '--no-timestamps',  # We only need text, not timestamps
                    '--output-txt',     # Output plain text
                ]

                # Run whisper
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Parse output - whisper-cli writes to stdout
                # Look for the transcribed text (usually after "...")
                output_lines = result.stdout.strip().split('\n')

                # Find transcription (filter out progress/status lines)
                transcription = None
                for line in reversed(output_lines):
                    # Skip empty lines and progress indicators
                    if line.strip() and not line.startswith('['):
                        transcription = line.strip()
                        break

                if transcription:
                    self.logger.info(f"Transcribed: {transcription}")
                    log_metric("stt_chars_transcribed", len(transcription))
                    return transcription
                else:
                    self.logger.warning("No transcription found in output")
                    return None

            except subprocess.CalledProcessError as e:
                self.logger.error(f"Whisper transcription failed: {e.stderr}")
                return None
            except Exception as e:
                self.logger.error(f"STT transcription error: {e}", exc_info=True)
                return None

    def transcribe_array(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio from numpy array

        Args:
            audio_data: Audio data as numpy array (int16 or float32)
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text or None if failed

        Example:
            >>> import sounddevice as sd
            >>> recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
            >>> sd.wait()
            >>> text = stt.transcribe_array(recording[:, 0])
        """
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Write WAV file
            self._write_wav(tmp_path, audio_data, sample_rate)

            # Transcribe
            text = self.transcribe_file(tmp_path)

            return text

        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

    def _write_wav(self, output_path: Path, audio_data: np.ndarray, sample_rate: int):
        """
        Write audio data to WAV file

        Args:
            output_path: Output WAV file path
            audio_data: Audio data (int16 or float32)
            sample_rate: Sample rate in Hz
        """
        # Ensure int16 format
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            # Convert float to int16
            audio_data = (audio_data * 32767).astype(np.int16)
        elif audio_data.dtype != np.int16:
            audio_data = audio_data.astype(np.int16)

        # Write WAV
        with wave.open(str(output_path), 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            wav.writeframes(audio_data.tobytes())

    def preprocess_audio(
        self,
        audio_data: np.ndarray,
        normalize: bool = True,
        noise_reduce: bool = False
    ) -> np.ndarray:
        """
        Preprocess audio before transcription

        Applies:
        - Normalization (increase volume to optimal level)
        - Optional noise reduction (simple high-pass filter)

        Args:
            audio_data: Raw audio data (int16 or float32)
            normalize: Normalize audio level
            noise_reduce: Apply simple noise reduction

        Returns:
            Preprocessed audio data (int16)
        """
        # Convert to float for processing
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            audio_float = audio_data.astype(np.float32)

        # Normalize
        if normalize:
            peak = np.abs(audio_float).max()
            if peak > 0:
                # Normalize to 0.9 peak (leave headroom)
                audio_float = audio_float * (0.9 / peak)

        # Simple noise reduction (high-pass filter)
        if noise_reduce:
            # Very basic: subtract low-frequency component
            # For production, use scipy.signal or FFmpeg
            from scipy import signal
            # High-pass filter at 80 Hz
            sos = signal.butter(4, 80, 'hp', fs=16000, output='sos')
            audio_float = signal.sosfilt(sos, audio_float)

        # Convert back to int16
        audio_int16 = (audio_float * 32767).astype(np.int16)

        return audio_int16

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages

        Returns:
            List of language codes (ISO 639-1)
        """
        # Whisper supports many languages
        # Full list: https://github.com/openai/whisper#available-models-and-languages
        return [
            'fr',  # French (primary for StoryBox)
            'en',  # English
            'es',  # Spanish
            'de',  # German
            'it',  # Italian
            # ... many more
        ]

    def benchmark(self, audio_path: Path) -> Dict[str, Any]:
        """
        Benchmark transcription performance

        Measures:
        - Transcription time
        - Real-time factor (RTF = transcription_time / audio_duration)
        - Chars per second

        Args:
            audio_path: Audio file to benchmark

        Returns:
            Dictionary with benchmark results
        """
        import time

        # Get audio duration
        with wave.open(str(audio_path), 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            audio_duration = frames / float(rate)

        # Transcribe and measure time
        start_time = time.time()
        text = self.transcribe_file(audio_path)
        transcription_time = time.time() - start_time

        # Calculate metrics
        rtf = transcription_time / audio_duration if audio_duration > 0 else 0
        chars_per_second = len(text) / transcription_time if text and transcription_time > 0 else 0

        results = {
            'audio_duration_s': audio_duration,
            'transcription_time_s': transcription_time,
            'rtf': rtf,
            'text_length': len(text) if text else 0,
            'chars_per_second': chars_per_second,
            'transcribed_text': text
        }

        self.logger.info(f"Benchmark results: RTF={rtf:.2f}, {chars_per_second:.1f} chars/s")

        return results


def test_whisper_stt():
    """
    Simple test function for Whisper STT

    Run this to verify STT is working correctly.

    Usage:
        python -m app.stt.whisper_stt
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("Whisper STT Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Initialize STT
    try:
        stt = WhisperSTT(config.stt)
        print("✓ STT initialized")
    except Exception as e:
        print(f"✗ Failed to initialize STT: {e}")
        return

    # Check for test audio files
    test_audio_dir = Path("test/audio_samples")
    if not test_audio_dir.exists():
        print(f"\n✗ Test audio directory not found: {test_audio_dir}")
        print("Run: python test/scripts/test_tts.py first to generate test audio")
        return

    # Test transcription
    test_files = list(test_audio_dir.glob("*.wav"))
    if not test_files:
        print(f"\n✗ No test audio files found in {test_audio_dir}")
        return

    print(f"\nFound {len(test_files)} test audio files")

    for audio_file in test_files[:3]:  # Test first 3 files
        print(f"\n--- Testing: {audio_file.name} ---")

        # Benchmark transcription
        results = stt.benchmark(audio_file)

        print(f"Audio duration: {results['audio_duration_s']:.2f}s")
        print(f"Transcription time: {results['transcription_time_s']:.2f}s")
        print(f"RTF: {results['rtf']:.2f} (lower is better, <1.0 is real-time)")
        print(f"Transcribed ({results['text_length']} chars):")
        print(f"  \"{results['transcribed_text']}\"")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run test when module is executed directly
    test_whisper_stt()
