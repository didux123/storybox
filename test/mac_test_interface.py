#!/usr/bin/env python3
"""
Mac Test Interface for StoryBox IA

Simple CLI interface to test the complete audio pipeline on Mac:
- Press and hold SPACE to record audio
- Release SPACE to stop recording and process
- System will transcribe, generate plan, create chapter, and play audio

Usage:
    python test/mac_test_interface.py

Requirements:
    pip install keyboard pyaudio

Author: StoryBox IA Team
Date: 2024-12
"""

import os
import sys
import time
import wave
from pathlib import Path

# Set mock mode for Mac
os.environ['MOCK_GPIO'] = 'true'
os.environ['MOCK_AUDIO'] = 'false'  # Use real audio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.config import get_config
from app.utils.logger import setup_logging, get_logger
from app.audio.input import AudioInput
from app.stt.whisper_stt import WhisperSTT
from app.llm.planner import Planner
from app.llm.story_gen import StoryGenerator
from app.tts.piper_tts import PiperTTS


logger = get_logger(__name__)


class MacTestInterface:
    """
    Simple test interface for Mac development

    Allows testing the complete StoryBox pipeline without GPIO hardware.
    """

    def __init__(self):
        """Initialize test interface"""
        print("=" * 60)
        print("StoryBox IA - Mac Test Interface")
        print("=" * 60)

        # Load config
        config = get_config()

        # Setup logging
        setup_logging(
            log_dir="logs",
            log_level="INFO",
            console_output=True
        )

        self.logger = get_logger(self.__class__.__name__)

        # Initialize modules
        print("\n📦 Initializing modules...")

        try:
            print("  → Audio input...")
            self.audio_in = AudioInput(config.audio.input, mock_mode=False)

            print("  → STT (Whisper)...")
            self.stt = WhisperSTT(config.stt)

            print("  → LLM (Planner)...")
            self.planner = Planner(config.llm)

            print("  → LLM (StoryGen)...")
            self.story_gen = StoryGenerator(config.llm)

            print("  → TTS (Piper)...")
            self.tts = PiperTTS(config.tts)

            print("\n✅ All modules initialized successfully!\n")

        except Exception as e:
            print(f"\n❌ Failed to initialize modules: {e}")
            sys.exit(1)

        # Test audio device
        print("🎤 Testing audio device...")
        if not self.audio_in.test_device():
            print("⚠️  Warning: Audio device test failed")
            print("   Make sure a microphone is connected")

    def play_audio(self, audio_bytes: bytes):
        """
        Play audio using PyAudio

        Args:
            audio_bytes: WAV audio data
        """
        try:
            import pyaudio

            # Parse WAV
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # Open WAV file
            wf = wave.open(tmp_path, 'rb')

            # Initialize PyAudio
            p = pyaudio.PyAudio()

            # Open stream
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            # Play audio
            chunk_size = 1024
            data = wf.readframes(chunk_size)

            while data:
                stream.write(data)
                data = wf.readframes(chunk_size)

            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            # Remove temp file
            os.unlink(tmp_path)

        except ImportError:
            self.logger.warning("PyAudio not installed, using afplay instead")
            self._play_audio_afplay(audio_bytes)

    def _play_audio_afplay(self, audio_bytes: bytes):
        """
        Play audio using macOS afplay command

        Args:
            audio_bytes: WAV audio data
        """
        import subprocess
        import tempfile

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Play with afplay
        subprocess.run(['afplay', tmp_path])

        # Cleanup
        os.unlink(tmp_path)

    def run_simple_test(self):
        """
        Run simple keyboard-based test

        Press SPACE to record, release to process.
        """
        try:
            import keyboard
        except ImportError:
            print("\n❌ 'keyboard' package not installed")
            print("Install with: pip install keyboard")
            print("\nNote: You may need to run with sudo on Mac for keyboard access")
            return

        print("\n" + "=" * 60)
        print("🎙️  READY TO TEST")
        print("=" * 60)
        print("\nInstructions:")
        print("  1. Press and HOLD SPACE to start recording")
        print("  2. Speak your story request (e.g., 'une histoire de pirates')")
        print("  3. Release SPACE to stop and process")
        print("  4. Wait for the audio response")
        print("\nPress Ctrl+C to quit")
        print("=" * 60 + "\n")

        recording = False

        def on_space_press(event):
            nonlocal recording
            if event.name == 'space' and not recording:
                recording = True
                print("\n🔴 RECORDING... (speak now)")
                self.audio_in.start_recording()

        def on_space_release(event):
            nonlocal recording
            if event.name == 'space' and recording:
                recording = False
                print("⏹️  Recording stopped\n")

                # Stop recording
                audio_buffer = self.audio_in.stop_recording()

                if not audio_buffer:
                    print("❌ No audio captured")
                    return

                print(f"✅ Captured {audio_buffer.duration:.2f}s audio\n")

                # Process pipeline
                self.process_pipeline(audio_buffer)

        # Register keyboard events
        keyboard.on_press(on_space_press)
        keyboard.on_release(on_space_release)

        # Wait for events
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")

    def run_cli_test(self):
        """
        Run simple CLI test without keyboard library

        Alternative that doesn't require keyboard access.
        """
        print("\n" + "=" * 60)
        print("🎙️  READY TO TEST (CLI Mode)")
        print("=" * 60)
        print("\nInstructions:")
        print("  1. Press ENTER to start recording")
        print("  2. Speak your story request")
        print("  3. Press ENTER again to stop and process")
        print("\nPress Ctrl+C to quit")
        print("=" * 60 + "\n")

        try:
            while True:
                input("Press ENTER to start recording...")

                print("\n🔴 RECORDING... (speak now, press ENTER when done)")
                self.audio_in.start_recording()

                input()  # Wait for second enter
                print("⏹️  Recording stopped\n")

                # Stop recording
                audio_buffer = self.audio_in.stop_recording()

                if not audio_buffer:
                    print("❌ No audio captured")
                    continue

                print(f"✅ Captured {audio_buffer.duration:.2f}s audio\n")

                # Process pipeline
                self.process_pipeline(audio_buffer)

                print("\n" + "-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")

    def process_pipeline(self, audio_buffer):
        """
        Process complete pipeline

        Args:
            audio_buffer: Recorded audio buffer
        """
        try:
            # Save audio
            temp_audio = Path("/tmp/storybox_test_recording.wav")
            self.audio_in.save_wav(audio_buffer, temp_audio)

            # Step 1: Transcribe
            print("📝 Step 1/4: Transcribing audio...")
            transcription = self.stt.transcribe_file(temp_audio)

            if not transcription:
                print("❌ Transcription failed")
                return

            print(f"✅ Transcription: \"{transcription}\"\n")

            # Step 2: Generate plan
            print("📋 Step 2/4: Generating story plan...")
            plan = self.planner.create_plan(transcription, num_chapters=3)  # Only 3 for testing

            if not plan:
                print("❌ Plan generation failed")
                return

            print(f"✅ Generated plan: {plan.theme}")
            print("\nChapters:")
            for chapter in plan.chapters:
                print(f"  {chapter['number']}. {chapter['title']}")
                print(f"     → {chapter['summary']}")

            # Step 3: Generate first chapter
            print(f"\n📖 Step 3/4: Generating chapter 1...")
            chapter_result = None

            for result in self.story_gen.generate_story(plan, min_words=50, max_words=150):
                if result.chapter_num == 1:
                    chapter_result = result
                    break

            if not chapter_result:
                print("❌ Chapter generation failed")
                return

            print(f"✅ Chapter 1 generated ({chapter_result.word_count} words)")
            print(f"\nText preview:")
            print(f"  {chapter_result.text[:200]}...\n")

            # Step 4: Synthesize and play
            print("🔊 Step 4/4: Synthesizing and playing audio...")
            audio_bytes = self.tts.synthesize(chapter_result.text)

            if not audio_bytes:
                print("❌ TTS synthesis failed")
                return

            duration = self.tts.get_audio_duration(audio_bytes)
            print(f"✅ Generated {duration:.1f}s audio")

            print("\n🎵 Playing audio...")
            self.play_audio(audio_bytes)

            print("\n✨ Pipeline complete!")

        except Exception as e:
            print(f"\n❌ Error in pipeline: {e}")
            self.logger.error(f"Pipeline error: {e}", exc_info=True)


def main():
    """Main entry point"""
    # Check for required dependencies
    try:
        import sounddevice
    except ImportError:
        print("❌ 'sounddevice' not installed")
        print("Install with: pip install sounddevice")
        sys.exit(1)

    # Create interface
    interface = MacTestInterface()

    # Check if keyboard is available
    try:
        import keyboard
        use_keyboard = True
    except ImportError:
        use_keyboard = False
        print("\n⚠️  'keyboard' package not installed")
        print("Using simple CLI mode instead\n")

    # Run appropriate test mode
    if use_keyboard and os.geteuid() == 0:
        # Keyboard mode (requires root on Mac)
        interface.run_simple_test()
    else:
        # CLI mode (no special permissions needed)
        if use_keyboard:
            print("\n⚠️  Keyboard mode requires sudo on Mac")
            print("Run with: sudo python test/mac_test_interface.py")
            print("\nUsing CLI mode instead...\n")

        interface.run_cli_test()


if __name__ == "__main__":
    main()
