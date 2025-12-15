"""
State Machine for StoryBox IA

Manages application state transitions and event handling.
Coordinates all modules (audio, STT, LLM, TTS, GPIO).

States:
- IDLE: Waiting for button press
- LISTENING: Recording audio (button held)
- PROCESSING: Transcribing and generating plan
- GENERATING: Generating story chapters
- NARRATING: Playing TTS audio
- ERROR: Error state with recovery

Usage:
    from app.state.machine import StateMachine, State

    machine = StateMachine(config)
    machine.start()  # Runs until shutdown

Author: StoryBox IA Team
Date: 2024-12
"""

from enum import Enum
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
import time

from app.utils.logger import get_logger, log_metric
from app.gpio.led import LEDState


logger = get_logger(__name__)


class State(Enum):
    """Application states"""
    IDLE = "idle"                    # Waiting for user input
    LISTENING = "listening"          # Recording audio
    PROCESSING = "processing"        # STT + Plan generation
    GENERATING = "generating"        # Chapter generation
    NARRATING = "narrating"          # TTS playback
    ERROR = "error"                  # Error state
    SHUTDOWN = "shutdown"            # Graceful shutdown


class Event(Enum):
    """State machine events"""
    BUTTON_PRESS = "button_press"
    BUTTON_RELEASE = "button_release"
    BUTTON_LONG_PRESS = "button_long_press"
    AUDIO_READY = "audio_ready"
    TRANSCRIPTION_READY = "transcription_ready"
    PLAN_READY = "plan_ready"
    CHAPTER_READY = "chapter_ready"
    AUDIO_PLAYBACK_DONE = "audio_playback_done"
    STORY_COMPLETE = "story_complete"
    ERROR_OCCURRED = "error_occurred"
    RETRY_REQUESTED = "retry_requested"


@dataclass
class StateContext:
    """
    Context data passed between states

    Contains all data needed for state transitions.
    """
    # Audio
    audio_buffer: Optional[Any] = None

    # STT
    transcribed_text: Optional[str] = None

    # Story generation
    story_plan: Optional[Any] = None
    current_chapter: int = 0
    chapter_text: Optional[str] = None
    chapter_audio: Optional[bytes] = None

    # Error handling
    error_message: Optional[str] = None
    error_count: int = 0
    previous_state: Optional[State] = None


class StateMachine:
    """
    Main application state machine

    Coordinates all modules and manages state transitions.
    """

    def __init__(self, config):
        """
        Initialize state machine

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Current state
        self.current_state = State.IDLE
        self.context = StateContext()

        # State handlers
        self.state_handlers: Dict[State, Callable] = {}
        self.state_entry_handlers: Dict[State, Callable] = {}
        self.state_exit_handlers: Dict[State, Callable] = {}

        # Event queue (simplified - real implementation would use threading.Queue)
        self.event_queue = []

        # Running flag
        self.running = False

        self.logger.info("State machine initialized")

    def register_state_handler(self, state: State, handler: Callable):
        """
        Register handler for state

        Handler is called continuously while in this state.

        Args:
            state: State to handle
            handler: Function(context) -> Optional[Event]
        """
        self.state_handlers[state] = handler

    def register_entry_handler(self, state: State, handler: Callable):
        """
        Register entry handler for state

        Called once when entering state.

        Args:
            state: State to handle
            handler: Function(context) -> None
        """
        self.state_entry_handlers[state] = handler

    def register_exit_handler(self, state: State, handler: Callable):
        """
        Register exit handler for state

        Called once when leaving state.

        Args:
            state: State to handle
            handler: Function(context) -> None
        """
        self.state_exit_handlers[state] = handler

    def post_event(self, event: Event, data: Optional[Dict[str, Any]] = None):
        """
        Post event to state machine

        Args:
            event: Event to post
            data: Optional event data
        """
        self.logger.debug(f"Event: {event.value}")
        self.event_queue.append((event, data or {}))

    def transition_to(self, new_state: State):
        """
        Transition to new state

        Calls exit handler for current state and entry handler for new state.

        Args:
            new_state: State to transition to
        """
        if new_state == self.current_state:
            return

        old_state = self.current_state

        self.logger.info(f"State transition: {old_state.value} → {new_state.value}")

        # Call exit handler
        if old_state in self.state_exit_handlers:
            try:
                self.state_exit_handlers[old_state](self.context)
            except Exception as e:
                self.logger.error(f"Exit handler error for {old_state.value}: {e}", exc_info=True)

        # Update state
        self.current_state = new_state

        # Log metric
        log_metric(f"state_transition_to_{new_state.value}", 1)

        # Call entry handler
        if new_state in self.state_entry_handlers:
            try:
                self.state_entry_handlers[new_state](self.context)
            except Exception as e:
                self.logger.error(f"Entry handler error for {new_state.value}: {e}", exc_info=True)
                # Transition to error state
                self.context.error_message = str(e)
                self.context.previous_state = old_state
                self.transition_to(State.ERROR)

    def _process_events(self):
        """Process pending events"""
        while self.event_queue:
            event, data = self.event_queue.pop(0)

            # Handle event based on current state
            next_state = self._handle_event(event, data)

            if next_state:
                self.transition_to(next_state)

    def _handle_event(self, event: Event, data: Dict[str, Any]) -> Optional[State]:
        """
        Handle event in current state

        Args:
            event: Event to handle
            data: Event data

        Returns:
            Next state or None to stay in current state
        """
        current = self.current_state

        # Global events (handled in any state)
        if event == Event.BUTTON_LONG_PRESS:
            self.logger.info("Long press detected - shutting down")
            return State.SHUTDOWN

        if event == Event.ERROR_OCCURRED:
            self.context.error_message = data.get('error', 'Unknown error')
            self.context.previous_state = current
            return State.ERROR

        # State-specific event handling
        if current == State.IDLE:
            if event == Event.BUTTON_PRESS:
                return State.LISTENING

        elif current == State.LISTENING:
            if event == Event.BUTTON_RELEASE:
                return State.PROCESSING

        elif current == State.PROCESSING:
            if event == Event.PLAN_READY:
                self.context.story_plan = data.get('plan')
                return State.GENERATING

        elif current == State.GENERATING:
            if event == Event.CHAPTER_READY:
                self.context.chapter_text = data.get('chapter_text')
                return State.NARRATING

        elif current == State.NARRATING:
            if event == Event.AUDIO_PLAYBACK_DONE:
                # Check if more chapters
                if self.context.current_chapter < len(self.context.story_plan.chapters):
                    return State.GENERATING
                else:
                    # Story complete
                    return State.IDLE

            if event == Event.STORY_COMPLETE:
                return State.IDLE

        elif current == State.ERROR:
            if event == Event.RETRY_REQUESTED:
                # Return to previous state
                if self.context.previous_state:
                    return self.context.previous_state
                else:
                    return State.IDLE

        return None

    def run(self):
        """
        Main state machine loop

        Runs until shutdown requested.
        """
        self.running = True
        self.logger.info("State machine started")

        # Start in IDLE state
        self.transition_to(State.IDLE)

        while self.running and self.current_state != State.SHUTDOWN:
            # Process events
            self._process_events()

            # Run state handler
            if self.current_state in self.state_handlers:
                try:
                    # Handler can return an event to process
                    event = self.state_handlers[self.current_state](self.context)
                    if event:
                        self.post_event(event)
                except Exception as e:
                    self.logger.error(
                        f"State handler error in {self.current_state.value}: {e}",
                        exc_info=True
                    )
                    self.post_event(Event.ERROR_OCCURRED, {'error': str(e)})

            # Small sleep to prevent CPU spinning
            time.sleep(0.1)

        self.logger.info("State machine stopped")

    def stop(self):
        """Stop state machine"""
        self.running = False

    def get_led_state(self) -> LEDState:
        """
        Get LED state for current application state

        Returns:
            LEDState corresponding to current state
        """
        state_to_led = {
            State.IDLE: LEDState.IDLE,
            State.LISTENING: LEDState.LISTENING,
            State.PROCESSING: LEDState.PROCESSING,
            State.GENERATING: LEDState.PROCESSING,
            State.NARRATING: LEDState.NARRATING,
            State.ERROR: LEDState.ERROR,
            State.SHUTDOWN: LEDState.OFF,
        }

        return state_to_led.get(self.current_state, LEDState.IDLE)


def test_state_machine():
    """
    Test function for state machine

    Usage:
        python -m app.state.machine
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("State Machine Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Create state machine
    machine = StateMachine(config)
    print("✓ State machine created")

    # Register handlers
    def idle_handler(context):
        print("  [IDLE] Waiting for input...")
        time.sleep(1)
        # Simulate button press
        return Event.BUTTON_PRESS

    def listening_handler(context):
        print("  [LISTENING] Recording...")
        time.sleep(2)
        # Simulate button release
        return Event.BUTTON_RELEASE

    def processing_handler(context):
        print("  [PROCESSING] Transcribing and generating plan...")
        time.sleep(2)
        # Simulate plan ready
        return Event.PLAN_READY

    def generating_handler(context):
        print("  [GENERATING] Generating chapter...")
        time.sleep(2)
        # Simulate chapter ready
        return Event.CHAPTER_READY

    def narrating_handler(context):
        print("  [NARRATING] Playing audio...")
        time.sleep(2)
        # Simulate story complete
        return Event.STORY_COMPLETE

    def error_handler(context):
        print(f"  [ERROR] {context.error_message}")
        time.sleep(2)
        # Simulate retry
        return Event.RETRY_REQUESTED

    # Register handlers
    machine.register_state_handler(State.IDLE, idle_handler)
    machine.register_state_handler(State.LISTENING, listening_handler)
    machine.register_state_handler(State.PROCESSING, processing_handler)
    machine.register_state_handler(State.GENERATING, generating_handler)
    machine.register_state_handler(State.NARRATING, narrating_handler)
    machine.register_state_handler(State.ERROR, error_handler)

    # Entry/exit handlers
    machine.register_entry_handler(
        State.IDLE,
        lambda ctx: print("→ Entered IDLE state")
    )

    machine.register_exit_handler(
        State.IDLE,
        lambda ctx: print("← Exiting IDLE state")
    )

    print("\n--- Running State Machine (10s test) ---\n")

    # Run for 10 seconds
    import threading

    def run_machine():
        machine.run()

    thread = threading.Thread(target=run_machine, daemon=True)
    thread.start()

    # Let it run for 10 seconds
    time.sleep(10)

    # Stop
    machine.stop()
    thread.join(timeout=2)

    print("\n✓ State machine test complete")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_state_machine()
