"""
GPIO Button Handler for StoryBox IA

Handles hold-to-talk button with debouncing and event detection.
Supports both real GPIO (Pi) and mock mode (Mac development).

Features:
- Hold-to-talk detection (press and release)
- Short press detection (pause/resume)
- Long press detection (≥3s for shutdown)
- Debouncing (50ms default)
- Mock mode for Mac development

Usage:
    from app.gpio.button import Button

    button = Button(pin=17, debounce_ms=50)
    button.on_press(lambda: print("Button pressed!"))
    button.on_release(lambda: print("Button released!"))
    button.start()

Author: StoryBox IA Team
Date: 2024-12
"""

import os
import time
import threading
from typing import Optional, Callable
from enum import Enum

from app.utils.logger import get_logger, log_metric
from app.utils.config import GPIOConfig


logger = get_logger(__name__)


class ButtonEvent(Enum):
    """Button event types"""
    PRESS = "press"              # Button pressed down
    RELEASE = "release"          # Button released
    SHORT_PRESS = "short_press"  # Short press (pause/resume)
    LONG_PRESS = "long_press"    # Long press (≥3s shutdown)
    HOLD = "hold"                # Button held down


class Button:
    """
    GPIO button handler

    Handles button events with debouncing and event detection.
    Supports mock mode for development without GPIO hardware.
    """

    def __init__(
        self,
        pin: int,
        debounce_ms: int = 50,
        long_press_duration_s: float = 3.0,
        mock_mode: Optional[bool] = None
    ):
        """
        Initialize button handler

        Args:
            pin: GPIO pin number (BCM numbering)
            debounce_ms: Debounce time in milliseconds
            long_press_duration_s: Duration for long press detection
            mock_mode: Force mock mode (auto-detect if None)
        """
        self.pin = pin
        self.debounce_ms = debounce_ms
        self.long_press_duration = long_press_duration_s
        self.logger = get_logger(self.__class__.__name__)

        # Auto-detect mock mode
        if mock_mode is None:
            self.mock_mode = os.getenv('MOCK_GPIO', 'false').lower() == 'true'
        else:
            self.mock_mode = mock_mode

        # Event callbacks
        self.callbacks = {
            ButtonEvent.PRESS: [],
            ButtonEvent.RELEASE: [],
            ButtonEvent.SHORT_PRESS: [],
            ButtonEvent.LONG_PRESS: [],
            ButtonEvent.HOLD: [],
        }

        # Button state
        self.is_pressed = False
        self.press_start_time = None
        self.last_event_time = 0

        # Threading
        self.running = False
        self.poll_thread = None

        # Initialize GPIO
        if not self.mock_mode:
            self._init_gpio()
        else:
            self.logger.info("Mock mode enabled - button simulation active")

        self.logger.info(f"Button initialized on pin {pin} (mock: {self.mock_mode})")

    def _init_gpio(self):
        """Initialize GPIO hardware (Pi only)"""
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO

            # Setup GPIO
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setup(
                self.pin,
                self.GPIO.IN,
                pull_up_down=self.GPIO.PUD_UP  # Pull-up resistor (active low)
            )

            self.logger.info(f"GPIO initialized for pin {self.pin}")

        except ImportError:
            raise RuntimeError(
                "RPi.GPIO not available. Install with: pip install RPi.GPIO\n"
                "Or use MOCK_GPIO=true for testing without hardware"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GPIO: {e}")

    def on_press(self, callback: Callable[[], None]):
        """
        Register callback for button press event

        Args:
            callback: Function to call when button is pressed
        """
        self.callbacks[ButtonEvent.PRESS].append(callback)

    def on_release(self, callback: Callable[[], None]):
        """
        Register callback for button release event

        Args:
            callback: Function to call when button is released
        """
        self.callbacks[ButtonEvent.RELEASE].append(callback)

    def on_short_press(self, callback: Callable[[], None]):
        """
        Register callback for short press event

        Short press = press and release quickly (< long press duration)

        Args:
            callback: Function to call on short press
        """
        self.callbacks[ButtonEvent.SHORT_PRESS].append(callback)

    def on_long_press(self, callback: Callable[[], None]):
        """
        Register callback for long press event

        Long press = button held for ≥3 seconds

        Args:
            callback: Function to call on long press
        """
        self.callbacks[ButtonEvent.LONG_PRESS].append(callback)

    def on_hold(self, callback: Callable[[], None]):
        """
        Register callback for button hold event

        Called periodically while button is held down.

        Args:
            callback: Function to call while button is held
        """
        self.callbacks[ButtonEvent.HOLD].append(callback)

    def _fire_event(self, event: ButtonEvent):
        """
        Fire event callbacks

        Args:
            event: Button event type
        """
        self.logger.debug(f"Button event: {event.value}")

        for callback in self.callbacks[event]:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Callback error for {event.value}: {e}", exc_info=True)

    def _read_pin(self) -> bool:
        """
        Read button state from pin

        Returns:
            True if button is pressed, False otherwise
        """
        if self.mock_mode:
            # Mock mode: read from stdin or return False
            # In real usage, this would be controlled by test scripts
            return False
        else:
            # Read GPIO pin (active low, so invert)
            return self.GPIO.input(self.pin) == self.GPIO.LOW

    def _poll_loop(self):
        """
        Button polling loop (runs in separate thread)
        """
        self.logger.info("Button polling started")

        while self.running:
            # Read button state
            button_pressed = self._read_pin()

            # Debouncing
            current_time = time.time()
            time_since_last_event = (current_time - self.last_event_time) * 1000

            if time_since_last_event < self.debounce_ms:
                time.sleep(0.001)  # 1ms sleep
                continue

            # State changed?
            if button_pressed and not self.is_pressed:
                # Button pressed
                self.is_pressed = True
                self.press_start_time = current_time
                self.last_event_time = current_time

                self._fire_event(ButtonEvent.PRESS)

                log_metric("button_press_count", 1)

            elif not button_pressed and self.is_pressed:
                # Button released
                self.is_pressed = False
                press_duration = current_time - self.press_start_time
                self.last_event_time = current_time

                self._fire_event(ButtonEvent.RELEASE)

                # Determine press type
                if press_duration >= self.long_press_duration:
                    self._fire_event(ButtonEvent.LONG_PRESS)
                    log_metric("button_long_press_count", 1)
                else:
                    self._fire_event(ButtonEvent.SHORT_PRESS)
                    log_metric("button_short_press_count", 1)

                log_metric("button_press_duration_s", press_duration)

            elif button_pressed and self.is_pressed:
                # Button held
                hold_duration = current_time - self.press_start_time

                # Check for long press threshold
                if hold_duration >= self.long_press_duration:
                    # Fire hold event periodically (every 0.5s)
                    if int(hold_duration * 2) != int((hold_duration - 0.01) * 2):
                        self._fire_event(ButtonEvent.HOLD)

            # Sleep to reduce CPU usage
            time.sleep(0.01)  # 10ms poll rate

        self.logger.info("Button polling stopped")

    def start(self):
        """Start button monitoring"""
        if self.running:
            self.logger.warning("Button already running")
            return

        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

        self.logger.info("Button monitoring started")

    def stop(self):
        """Stop button monitoring"""
        if not self.running:
            return

        self.running = False

        if self.poll_thread:
            self.poll_thread.join(timeout=1.0)

        self.logger.info("Button monitoring stopped")

    def simulate_press(self, duration: float = 0.5):
        """
        Simulate button press (mock mode only)

        Args:
            duration: Press duration in seconds
        """
        if not self.mock_mode:
            self.logger.warning("simulate_press only works in mock mode")
            return

        self.logger.info(f"Simulating button press ({duration}s)")

        # Simulate press
        self.is_pressed = True
        self.press_start_time = time.time()
        self._fire_event(ButtonEvent.PRESS)

        # Wait
        time.sleep(duration)

        # Simulate release
        self.is_pressed = False
        self._fire_event(ButtonEvent.RELEASE)

        if duration >= self.long_press_duration:
            self._fire_event(ButtonEvent.LONG_PRESS)
        else:
            self._fire_event(ButtonEvent.SHORT_PRESS)

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop()

        if not self.mock_mode and hasattr(self, 'GPIO'):
            try:
                self.GPIO.cleanup(self.pin)
                self.logger.info("GPIO cleaned up")
            except Exception as e:
                self.logger.error(f"GPIO cleanup error: {e}")

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()


def test_button():
    """
    Test function for button handler

    Usage:
        # With real GPIO (Pi):
        python -m app.gpio.button

        # With mock GPIO (Mac):
        MOCK_GPIO=true python -m app.gpio.button
    """
    print("=" * 60)
    print("Button Test")
    print("=" * 60)

    # Check mock mode
    mock_mode = os.getenv('MOCK_GPIO', 'false').lower() == 'true'

    if mock_mode:
        print("\n⚠️  MOCK_GPIO mode enabled")
        print("Simulating button presses...")
    else:
        print("\nUsing real GPIO hardware")
        print("Press the button! (Ctrl+C to exit)")

    # Initialize button
    try:
        button = Button(pin=17, debounce_ms=50, long_press_duration_s=3.0)
        print(f"✓ Button initialized on pin 17 (mock: {mock_mode})")
    except Exception as e:
        print(f"✗ Failed to initialize button: {e}")
        return

    # Register callbacks
    def on_press():
        print("🔵 Button PRESSED")

    def on_release():
        print("⚪ Button RELEASED")

    def on_short_press():
        print("⚡ SHORT PRESS detected")

    def on_long_press():
        print("🔴 LONG PRESS detected (≥3s)")

    def on_hold():
        print("⏳ Button HELD...")

    button.on_press(on_press)
    button.on_release(on_release)
    button.on_short_press(on_short_press)
    button.on_long_press(on_long_press)
    button.on_hold(on_hold)

    # Start monitoring
    button.start()

    if mock_mode:
        # Simulate button presses
        print("\n--- Test 1: Short Press (0.5s) ---")
        button.simulate_press(duration=0.5)
        time.sleep(1)

        print("\n--- Test 2: Medium Press (2s) ---")
        button.simulate_press(duration=2.0)
        time.sleep(1)

        print("\n--- Test 3: Long Press (4s) ---")
        button.simulate_press(duration=4.0)

        print("\n✓ Mock tests complete")

    else:
        # Wait for real button presses
        try:
            print("\nPress button to test (Ctrl+C to exit)...")
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nStopping...")

    # Cleanup
    button.stop()
    button.cleanup()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_button()
