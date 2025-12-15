"""
Main Application for StoryBox IA

Orchestrates all modules and manages the complete storytelling pipeline.

Pipeline:
1. IDLE: Wait for button press
2. LISTENING: Record audio while button held
3. PROCESSING: Transcribe audio + Generate story plan
4. GENERATING: Generate chapter text
5. NARRATING: Synthesize and play audio
6. Loop steps 4-5 for all chapters
7. Return to IDLE

Usage:
    # On Pi (real hardware):
    python -m app.main

    # On Mac (mock mode):
    MOCK_GPIO=true MOCK_AUDIO=true python -m app.main

Author: StoryBox IA Team
Date: 2024-12
"""

import sys
import signal
import time
from pathlib import Path

from app.utils.config import get_config
from app.utils.logger import setup_logging, get_logger, log_system_info, get_metrics_summary
from app.audio.input import AudioInput
from app.stt.whisper_stt import WhisperSTT
from app.llm.planner import Planner
from app.llm.story_gen import StoryGenerator
from app.tts.piper_tts import PiperTTS
from app.gpio.button import Button
from app.gpio.led import LEDController
from app.state.machine import StateMachine, State, Event


logger = get_logger(__name__)


class StoryBoxApp:
    """
    Main StoryBox IA application

    Coordinates all modules and handles the complete storytelling pipeline.
    """

    def __init__(self):
        """Initialize application"""
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("=" * 60)
        self.logger.info("StoryBox IA - Starting")
        self.logger.info("=" * 60)

        # Load configuration
        self.config = get_config()

        # Log system info
        log_system_info()

        # Initialize modules
        self._init_modules()

        # Create state machine
        self.state_machine = StateMachine(self.config)

        # Register state handlers
        self._register_handlers()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("StoryBox IA initialized successfully")

    def _init_modules(self):
        """Initialize all application modules"""
        self.logger.info("Initializing modules...")

        try:
            # Audio input
            self.logger.info("→ Audio input...")
            self.audio_in = AudioInput(self.config.audio.input)

            # STT
            self.logger.info("→ STT (Whisper)...")
            self.stt = WhisperSTT(self.config.stt)

            # LLM modules
            self.logger.info("→ LLM (Planner)...")
            self.planner = Planner(self.config.llm)

            self.logger.info("→ LLM (StoryGen)...")
            self.story_gen = StoryGenerator(self.config.llm)

            # TTS
            self.logger.info("→ TTS (Piper)...")
            self.tts = PiperTTS(self.config.tts)

            # GPIO
            self.logger.info("→ GPIO (Button)...")
            self.button = Button(
                pin=self.config.gpio.button_pin,
                debounce_ms=self.config.gpio.debounce_ms,
                long_press_duration_s=3.0
            )

            self.logger.info("→ GPIO (LEDs)...")
            self.leds = LEDController(
                idle_pin=self.config.gpio.led_pin_idle,
                active_pin=self.config.gpio.led_pin_active,
                error_pin=self.config.gpio.led_pin_error
            )

            self.logger.info("✓ All modules initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize modules: {e}", exc_info=True)
            raise

    def _register_handlers(self):
        """Register state machine handlers"""
        self.logger.info("Registering state handlers...")

        # State entry handlers (LED updates)
        for state in State:
            def create_entry_handler(s):
                def handler(ctx):
                    led_state = self.state_machine.get_led_state()
                    self.leds.set_state(led_state)
                return handler

            self.state_machine.register_entry_handler(state, create_entry_handler(state))

        # State handlers
        self.state_machine.register_state_handler(State.IDLE, self._handle_idle)
        self.state_machine.register_state_handler(State.LISTENING, self._handle_listening)
        self.state_machine.register_state_handler(State.PROCESSING, self._handle_processing)
        self.state_machine.register_state_handler(State.GENERATING, self._handle_generating)
        self.state_machine.register_state_handler(State.NARRATING, self._handle_narrating)
        self.state_machine.register_state_handler(State.ERROR, self._handle_error)

        # Button event handlers
        self.button.on_press(self._on_button_press)
        self.button.on_release(self._on_button_release)
        self.button.on_long_press(self._on_button_long_press)

        self.logger.info("✓ State handlers registered")

    def _handle_idle(self, context):
        """Handle IDLE state"""
        # Just wait for button press (handled by button callbacks)
        time.sleep(0.1)
        return None

    def _handle_listening(self, context):
        """Handle LISTENING state"""
        # Audio recording is managed by button press/release
        # Just wait for release
        time.sleep(0.1)
        return None

    def _handle_processing(self, context):
        """Handle PROCESSING state - STT + Plan generation"""
        self.logger.info("=== Processing: STT + Plan Generation ===")

        try:
            # Get audio buffer
            if not context.audio_buffer:
                raise RuntimeError("No audio buffer available")

            # Save audio to temp file
            temp_audio = Path("/tmp/storybox_recording.wav")
            self.audio_in.save_wav(context.audio_buffer, temp_audio)

            # Transcribe
            self.logger.info("Step 1/2: Transcribing audio...")
            transcription = self.stt.transcribe_file(temp_audio)

            if not transcription:
                raise RuntimeError("STT failed - no transcription")

            self.logger.info(f"Transcription: '{transcription}'")
            context.transcribed_text = transcription

            # Generate plan
            self.logger.info("Step 2/2: Generating story plan...")
            plan = self.planner.create_plan(transcription)

            if not plan:
                raise RuntimeError("Plan generation failed")

            self.logger.info(f"Plan: {len(plan.chapters)} chapters")
            context.story_plan = plan
            context.current_chapter = 0

            # Success - transition to generating
            return Event.PLAN_READY

        except Exception as e:
            self.logger.error(f"Processing failed: {e}", exc_info=True)
            return Event.ERROR_OCCURRED

    def _handle_generating(self, context):
        """Handle GENERATING state - Chapter generation"""
        if not context.story_plan:
            return Event.ERROR_OCCURRED

        context.current_chapter += 1
        chapter_num = context.current_chapter

        if chapter_num > len(context.story_plan.chapters):
            # All chapters done
            self.logger.info("Story generation complete!")
            return Event.STORY_COMPLETE

        self.logger.info(f"=== Generating Chapter {chapter_num}/{len(context.story_plan.chapters)} ===")

        try:
            # Generate chapter
            chapter_result = None

            for result in self.story_gen.generate_story(
                context.story_plan,
                min_words=self.config.story.chapter_min_words,
                max_words=self.config.story.chapter_max_words
            ):
                if result.chapter_num == chapter_num:
                    chapter_result = result
                    break

            if not chapter_result:
                raise RuntimeError(f"Failed to generate chapter {chapter_num}")

            self.logger.info(f"Chapter {chapter_num}: {chapter_result.word_count} words")
            context.chapter_text = chapter_result.text

            return Event.CHAPTER_READY

        except Exception as e:
            self.logger.error(f"Chapter generation failed: {e}", exc_info=True)
            return Event.ERROR_OCCURRED

    def _handle_narrating(self, context):
        """Handle NARRATING state - TTS playback"""
        if not context.chapter_text:
            return Event.ERROR_OCCURRED

        self.logger.info(f"=== Narrating Chapter {context.current_chapter} ===")

        try:
            # Synthesize audio
            audio_bytes = self.tts.synthesize(context.chapter_text)

            if not audio_bytes:
                raise RuntimeError("TTS synthesis failed")

            # Get duration
            duration = self.tts.get_audio_duration(audio_bytes)
            self.logger.info(f"Audio duration: {duration:.1f}s")

            # Save audio (optional - for debugging)
            if self.config.logging.level == "DEBUG":
                output_path = Path(f"/tmp/chapter_{context.current_chapter}.wav")
                self.tts.save_audio(audio_bytes, output_path)

            # Play audio
            # TODO: Implement audio playback (using pygame, pyaudio, or aplay)
            # For now, just simulate playback with sleep
            self.logger.info("Playing audio...")
            time.sleep(duration)

            # Check if more chapters
            if context.current_chapter < len(context.story_plan.chapters):
                return Event.AUDIO_PLAYBACK_DONE
            else:
                return Event.STORY_COMPLETE

        except Exception as e:
            self.logger.error(f"Narration failed: {e}", exc_info=True)
            return Event.ERROR_OCCURRED

    def _handle_error(self, context):
        """Handle ERROR state"""
        self.logger.error(f"Error state: {context.error_message}")

        # Increment error count
        context.error_count += 1

        # Wait before retry
        time.sleep(2)

        # Retry logic
        if context.error_count < 3:
            self.logger.info(f"Retrying (attempt {context.error_count}/3)...")
            context.error_count = 0
            return Event.RETRY_REQUESTED
        else:
            # Too many errors, return to idle
            self.logger.error("Too many errors, returning to idle")
            context.error_count = 0
            context.error_message = None
            self.state_machine.transition_to(State.IDLE)
            return None

    def _on_button_press(self):
        """Button press callback"""
        self.logger.info("Button pressed")

        if self.state_machine.current_state == State.IDLE:
            # Start recording
            self.audio_in.start_recording()
            self.state_machine.post_event(Event.BUTTON_PRESS)

    def _on_button_release(self):
        """Button release callback"""
        self.logger.info("Button released")

        if self.state_machine.current_state == State.LISTENING:
            # Stop recording
            audio_buffer = self.audio_in.stop_recording()

            if audio_buffer:
                self.state_machine.context.audio_buffer = audio_buffer
                self.state_machine.post_event(Event.BUTTON_RELEASE)
            else:
                self.logger.error("No audio captured")
                self.state_machine.post_event(Event.ERROR_OCCURRED)

    def _on_button_long_press(self):
        """Long press callback (shutdown)"""
        self.logger.info("Long press detected - initiating shutdown")
        self.state_machine.post_event(Event.BUTTON_LONG_PRESS)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum} - shutting down...")
        self.shutdown()

    def run(self):
        """Run main application loop"""
        self.logger.info("Starting StoryBox IA...")

        try:
            # Start button monitoring
            self.button.start()

            # Run state machine
            self.state_machine.run()

        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)

        finally:
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down StoryBox IA...")

        try:
            # Stop state machine
            if hasattr(self, 'state_machine'):
                self.state_machine.stop()

            # Stop button
            if hasattr(self, 'button'):
                self.button.stop()

            # Cleanup LEDs
            if hasattr(self, 'leds'):
                self.leds.cleanup()

            # Log final metrics
            metrics = get_metrics_summary()
            self.logger.info("Final metrics:")
            for metric, values in metrics.get('metrics', {}).items():
                self.logger.info(f"  {metric}: avg={values.get('avg', 0):.2f}")

        except Exception as e:
            self.logger.error(f"Shutdown error: {e}", exc_info=True)

        self.logger.info("StoryBox IA stopped")
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    # Setup logging
    config = get_config()
    setup_logging(
        log_dir=config.logging.log_dir,
        log_level=config.logging.level,
        max_bytes=config.logging.max_log_size_mb * 1024 * 1024,
        backup_count=3
    )

    logger = get_logger(__name__)

    try:
        # Create and run application
        app = StoryBoxApp()
        app.run()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
