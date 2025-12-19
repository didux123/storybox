"""
Vosk STT for StoryBox IA (Raspberry Pi)

Fast, offline French speech-to-text using Vosk.
This is the production STT solution for the Raspberry Pi.

Features:
- Fast transcription (~2-3s for 5s audio)
- Offline operation
- Small model size (~40MB)
- French language support

Usage:
    from app.stt.vosk_stt import VoskSTT

    stt = VoskSTT()
    audio_file = "/tmp/recording.wav"
    text = stt.transcribe(audio_file)
    print(text)

Author: StoryBox IA Team
Date: 2024-12-19
"""

import wave
import json
from pathlib import Path
from typing import Optional

from app.utils.logger import get_logger, TimingContext, log_metric


logger = get_logger(__name__)


class VoskSTT:
    """
    Vosk STT engine for French transcription

    Uses Vosk small French model for fast offline transcription.
    Optimized for Raspberry Pi.
    """

    def __init__(self, model_path: str = "/home/maxence/models/vosk/vosk-model-small-fr-0.22"):
        """
        Initialize Vosk STT

        Args:
            model_path: Path to Vosk model directory

        Raises:
            ImportError: If vosk is not installed
            FileNotFoundError: If model not found
        """
        self.logger = get_logger(self.__class__.__name__)
        self.model_path = model_path

        # Check model exists
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Vosk model not found: {model_path}")

        # Import vosk (only when class is instantiated)
        try:
            from vosk import Model, KaldiRecognizer
            self.Model = Model
            self.KaldiRecognizer = KaldiRecognizer
        except ImportError:
            raise ImportError(
                "Vosk not installed. Install with: pip install vosk"
            )

        # Load model
        self.logger.info(f"Loading Vosk model from {model_path}")
        self.model = self.Model(model_path)
        self.logger.info("Vosk STT initialized successfully")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio file to text

        Args:
            audio_file: Path to WAV audio file (16kHz, mono)

        Returns:
            Transcribed text or None if transcription failed

        Example:
            >>> stt = VoskSTT()
            >>> text = stt.transcribe("/tmp/recording.wav")
            >>> print(text)
            "Raconte-moi une histoire de pirates"
        """
        if not Path(audio_file).exists():
            self.logger.error(f"Audio file not found: {audio_file}")
            return None

        self.logger.info(f"Transcribing: {audio_file}")

        with TimingContext("stt_transcription", log_metric=True):
            try:
                # Open WAV file
                wf = wave.open(audio_file, "rb")

                # Verify format
                if wf.getnchannels() != 1:
                    self.logger.error("Audio must be mono (1 channel)")
                    return None

                # Create recognizer
                rec = self.KaldiRecognizer(self.model, wf.getframerate())
                rec.SetWords(False)  # We don't need word timestamps

                # Process audio
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    rec.AcceptWaveform(data)

                # Get final result
                result = json.loads(rec.FinalResult())
                transcription = result.get("text", "").strip()

                if transcription:
                    self.logger.info(f"Transcribed {len(transcription)} chars: '{transcription}'")
                    log_metric("stt_chars_transcribed", len(transcription))
                    return transcription
                else:
                    self.logger.warning("No transcription output (empty text)")
                    return None

            except Exception as e:
                self.logger.error(f"Transcription error: {e}", exc_info=True)
                return None

    def is_available(self) -> bool:
        """
        Check if Vosk STT is available

        Returns:
            True if model is loaded and ready
        """
        return self.model is not None


def test_vosk_stt():
    """
    Test function for Vosk STT

    Usage:
        python -m app.stt.vosk_stt
    """
    print("=" * 60)
    print("Vosk STT Test")
    print("=" * 60)

    # Initialize STT
    try:
        stt = VoskSTT()
        print("✓ Vosk STT initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Vosk: {e}")
        return

    # Test with audio file
    test_file = Path("/tmp/test_recording.wav")
    if test_file.exists():
        print(f"\nTranscribing: {test_file}")

        text = stt.transcribe(str(test_file))

        if text:
            print(f"\n✓ Transcription successful:")
            print(f"  '{text}'")
        else:
            print("\n✗ Transcription failed")
    else:
        print(f"\n⚠️  Test file not found: {test_file}")
        print("Record a test file first with:")
        print("  arecord -f S16_LE -r 16000 -c 1 -d 5 /tmp/test_recording.wav")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_vosk_stt()
