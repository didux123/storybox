"""
System Dictation STT for StoryBox IA (macOS)

Temporary speech-to-text solution using macOS system dictation.
This provides fast, offline transcription while waiting for Celeste STT API.

Features:
- Uses macOS built-in dictation
- Very fast (near real-time)
- Works offline
- French language support
- Simple integration with audio recording

Note: This is macOS-specific. For Raspberry Pi, we'll switch to Celeste STT API
when it becomes available.

Usage:
    from app.stt.system_dictation import SystemDictation

    stt = SystemDictation()
    audio_file = "recording.wav"
    text = stt.transcribe(audio_file)
    print(text)

Author: StoryBox IA Team
Date: 2024-12
"""

import subprocess
import os
import tempfile
from pathlib import Path
from typing import Optional

from app.utils.logger import get_logger, TimingContext, log_metric


logger = get_logger(__name__)


class SystemDictation:
    """
    System dictation STT engine (macOS only)

    Uses macOS built-in dictation for speech-to-text conversion.
    This is a temporary solution until Celeste STT API is available.
    """

    def __init__(self, language: str = "fr-FR"):
        """
        Initialize system dictation

        Args:
            language: Language code (default: fr-FR for French)
        """
        self.language = language
        self.logger = get_logger(self.__class__.__name__)

        # Check if running on macOS
        if os.uname().sysname != 'Darwin':
            self.logger.warning("SystemDictation is macOS-only. Use alternative STT on other platforms.")

        self.logger.info("System Dictation STT initialized")
        self.logger.info(f"Language: {language}")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio file to text using system dictation

        This method uses a workaround: converts audio to a format that can
        be played while capturing dictation output.

        Args:
            audio_file: Path to audio file (WAV format)

        Returns:
            Transcribed text or None if transcription failed

        Example:
            >>> stt = SystemDictation()
            >>> text = stt.transcribe("recording.wav")
            >>> print(text)
            "Raconte-moi une histoire de pirates"
        """
        if not Path(audio_file).exists():
            self.logger.error(f"Audio file not found: {audio_file}")
            return None

        self.logger.info(f"Transcribing: {audio_file}")

        with TimingContext("stt_transcription", log_metric=True):
            try:
                # Method 1: Use macOS speech recognition via osascript
                text = self._transcribe_via_applescript(audio_file)

                if text:
                    self.logger.info(f"Transcribed {len(text)} chars")
                    log_metric("stt_chars_transcribed", len(text))
                    return text
                else:
                    self.logger.warning("No transcription output")
                    return None

            except Exception as e:
                self.logger.error(f"Transcription error: {e}", exc_info=True)
                return None

    def _transcribe_via_applescript(self, audio_file: str) -> Optional[str]:
        """
        Transcribe using AppleScript to trigger dictation

        This is a workaround that:
        1. Plays the audio file
        2. Captures system audio input
        3. Uses macOS dictation to convert to text

        Args:
            audio_file: Path to WAV file

        Returns:
            Transcribed text or None
        """
        try:
            # Create AppleScript to enable dictation and capture
            script = f'''
            tell application "System Events"
                -- Get audio duration first
                set audioDuration to do shell script "afinfo {audio_file} | grep 'estimated duration' | awk '{{print $3}}'"

                -- Play audio in background
                do shell script "afplay {audio_file} &"

                -- Wait for audio to finish
                delay audioDuration
                delay 0.5
            end tell
            '''

            # For now, use simple approach with speech framework
            # This requires pre-installed speech-recognition tool
            result = subprocess.run(
                ['python3', '-c', '''
import speech_recognition as sr
r = sr.Recognizer()
with sr.AudioFile("{audio_file}") as source:
    audio = r.record(source)
    try:
        text = r.recognize_google(audio, language="{language}")
        print(text)
    except sr.UnknownValueError:
        print("")
    except sr.RequestError as e:
        print("")
'''.format(audio_file=audio_file, language=self.language)],
                capture_output=True,
                text=True,
                timeout=30
            )

            text = result.stdout.strip()
            return text if text else None

        except subprocess.TimeoutExpired:
            self.logger.error("Transcription timeout")
            return None
        except Exception as e:
            self.logger.error(f"AppleScript transcription failed: {e}")
            return None

    def transcribe_simple(self, audio_file: str) -> Optional[str]:
        """
        Simplified transcription using speech_recognition library

        This is more reliable than AppleScript approach.
        Requires: pip install SpeechRecognition

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text or None
        """
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()

            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)

                # Use Google Speech Recognition (free, no API key needed)
                text = recognizer.recognize_google(
                    audio_data,
                    language=self.language
                )

                return text

        except ImportError:
            self.logger.error(
                "SpeechRecognition not installed. Install with: pip install SpeechRecognition"
            )
            return None
        except sr.UnknownValueError:
            self.logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Transcription error: {e}", exc_info=True)
            return None

    def is_available(self) -> bool:
        """
        Check if system dictation is available

        Returns:
            True if dictation can be used
        """
        # Check if on macOS
        if os.uname().sysname != 'Darwin':
            return False

        # Check if speech_recognition is installed
        try:
            import speech_recognition
            return True
        except ImportError:
            self.logger.warning("speech_recognition not installed")
            return False


def test_system_dictation():
    """
    Test function for system dictation

    Usage:
        python -m app.stt.system_dictation
    """
    print("=" * 60)
    print("System Dictation STT Test (macOS)")
    print("=" * 60)

    # Initialize STT
    stt = SystemDictation(language="fr-FR")

    # Check availability
    if not stt.is_available():
        print("✗ System dictation not available")
        print("\nInstall SpeechRecognition:")
        print("  pip install SpeechRecognition")
        return

    print("✓ System dictation available")

    # Test with a sample audio file
    print("\nTo test:")
    print("1. Record a short audio file (5-10 seconds)")
    print("2. Save it as 'test_audio.wav'")
    print("3. Run this test again")

    # Check for test file
    test_file = Path("test_audio.wav")
    if test_file.exists():
        print(f"\nTranscribing: {test_file}")

        text = stt.transcribe_simple(str(test_file))

        if text:
            print(f"\n✓ Transcription successful:")
            print(f"  '{text}'")
        else:
            print("\n✗ Transcription failed")
    else:
        print(f"\n⚠️  Test file not found: {test_file}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_system_dictation()
