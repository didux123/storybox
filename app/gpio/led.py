"""
GPIO LED Controller for StoryBox IA

Manages LED status indicators with patterns for different states.
Supports both real GPIO (Pi) and mock mode (Mac development).

Features:
- Multi-LED control (Idle, Active, Error states)
- LED patterns (solid, blinking, breathing, pulsing)
- PWM support for brightness control
- Mock mode for Mac development

Usage:
    from app.gpio.led import LEDController, LEDState

    leds = LEDController(idle_pin=22, active_pin=23, error_pin=24)
    leds.set_state(LEDState.IDLE)      # Green LED solid
    leds.set_state(LEDState.PROCESSING) # Blue LED pulsing
    leds.set_state(LEDState.ERROR)     # Red LED blinking

Author: StoryBox IA Team
Date: 2024-12
"""

import os
import time
import threading
import math
from typing import Optional
from enum import Enum

from app.utils.logger import get_logger
from app.utils.config import GPIOConfig


logger = get_logger(__name__)


class LEDState(Enum):
    """LED state patterns"""
    OFF = "off"                    # All LEDs off
    IDLE = "idle"                  # Green LED solid (ready)
    LISTENING = "listening"        # Green LED breathing (recording)
    PROCESSING = "processing"      # Blue LED pulsing (generating)
    NARRATING = "narrating"        # Blue LED solid (speaking)
    ERROR = "error"                # Red LED blinking (error)


class LEDPattern(Enum):
    """LED animation patterns"""
    SOLID = "solid"                # Always on
    BLINK = "blink"                # On/off at regular intervals
    BREATHING = "breathing"        # Smooth fade in/out (slow)
    PULSE = "pulse"                # Fast pulse (heartbeat)


class LEDController:
    """
    LED controller for status indication

    Manages 3 LEDs (idle/active/error) with various patterns.
    Supports mock mode for development without GPIO hardware.
    """

    def __init__(
        self,
        idle_pin: int,
        active_pin: int,
        error_pin: int,
        mock_mode: Optional[bool] = None
    ):
        """
        Initialize LED controller

        Args:
            idle_pin: GPIO pin for idle/ready LED (green)
            active_pin: GPIO pin for active/processing LED (blue)
            error_pin: GPIO pin for error LED (red)
            mock_mode: Force mock mode (auto-detect if None)
        """
        self.idle_pin = idle_pin
        self.active_pin = active_pin
        self.error_pin = error_pin
        self.logger = get_logger(self.__class__.__name__)

        # Auto-detect mock mode
        if mock_mode is None:
            self.mock_mode = os.getenv('MOCK_GPIO', 'false').lower() == 'true'
        else:
            self.mock_mode = mock_mode

        # Current state
        self.current_state = LEDState.OFF
        self.current_brightness = {
            idle_pin: 0.0,
            active_pin: 0.0,
            error_pin: 0.0
        }

        # Animation thread
        self.running = False
        self.animation_thread = None

        # Initialize GPIO
        if not self.mock_mode:
            self._init_gpio()
        else:
            self.logger.info("Mock mode enabled - LED simulation active")

        self.logger.info(
            f"LEDs initialized: idle={idle_pin}, active={active_pin}, error={error_pin} "
            f"(mock: {self.mock_mode})"
        )

    def _init_gpio(self):
        """Initialize GPIO hardware (Pi only)"""
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO

            # Setup GPIO
            self.GPIO.setmode(self.GPIO.BCM)

            # Setup LED pins as outputs
            for pin in [self.idle_pin, self.active_pin, self.error_pin]:
                self.GPIO.setup(pin, self.GPIO.OUT)
                self.GPIO.output(pin, self.GPIO.LOW)

            # Setup PWM for brightness control (100 Hz frequency)
            self.pwm = {
                self.idle_pin: self.GPIO.PWM(self.idle_pin, 100),
                self.active_pin: self.GPIO.PWM(self.active_pin, 100),
                self.error_pin: self.GPIO.PWM(self.error_pin, 100)
            }

            # Start PWM at 0% duty cycle
            for pwm in self.pwm.values():
                pwm.start(0)

            self.logger.info("GPIO initialized for LEDs")

        except ImportError:
            raise RuntimeError(
                "RPi.GPIO not available. Install with: pip install RPi.GPIO\n"
                "Or use MOCK_GPIO=true for testing without hardware"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GPIO: {e}")

    def set_state(self, state: LEDState):
        """
        Set LED state with appropriate pattern

        Args:
            state: LED state to set

        Example:
            >>> leds.set_state(LEDState.IDLE)      # Green solid
            >>> leds.set_state(LEDState.PROCESSING) # Blue pulsing
        """
        if state == self.current_state:
            return

        self.logger.info(f"LED state: {self.current_state.value} → {state.value}")
        self.current_state = state

        # Stop previous animation
        self.stop_animation()

        # Set pattern for new state
        if state == LEDState.OFF:
            self._set_all_off()

        elif state == LEDState.IDLE:
            self._set_pattern(self.idle_pin, LEDPattern.SOLID, brightness=0.3)

        elif state == LEDState.LISTENING:
            self._set_pattern(self.idle_pin, LEDPattern.BREATHING)

        elif state == LEDState.PROCESSING:
            self._set_pattern(self.active_pin, LEDPattern.PULSE)

        elif state == LEDState.NARRATING:
            self._set_pattern(self.active_pin, LEDPattern.SOLID, brightness=0.5)

        elif state == LEDState.ERROR:
            self._set_pattern(self.error_pin, LEDPattern.BLINK)

    def _set_all_off(self):
        """Turn off all LEDs"""
        for pin in [self.idle_pin, self.active_pin, self.error_pin]:
            self._set_led(pin, 0.0)

    def _set_led(self, pin: int, brightness: float):
        """
        Set LED brightness

        Args:
            pin: GPIO pin number
            brightness: Brightness level (0.0 to 1.0)
        """
        brightness = max(0.0, min(1.0, brightness))  # Clamp to 0-1
        self.current_brightness[pin] = brightness

        if self.mock_mode:
            # Mock mode: just print
            if brightness > 0:
                self.logger.debug(f"LED {pin}: {'█' * int(brightness * 10)}")
        else:
            # Real GPIO: set PWM duty cycle
            duty_cycle = brightness * 100
            self.pwm[pin].ChangeDutyCycle(duty_cycle)

    def _set_pattern(
        self,
        pin: int,
        pattern: LEDPattern,
        brightness: float = 1.0,
        speed: float = 1.0
    ):
        """
        Set LED animation pattern

        Args:
            pin: GPIO pin number
            pattern: Animation pattern
            brightness: Maximum brightness (0.0 to 1.0)
            speed: Animation speed multiplier
        """
        # Turn off other LEDs
        for p in [self.idle_pin, self.active_pin, self.error_pin]:
            if p != pin:
                self._set_led(p, 0.0)

        # Start animation
        if pattern == LEDPattern.SOLID:
            self._set_led(pin, brightness)

        elif pattern == LEDPattern.BLINK:
            self.start_animation(lambda t: self._blink_animation(pin, t, brightness, speed))

        elif pattern == LEDPattern.BREATHING:
            self.start_animation(lambda t: self._breathing_animation(pin, t, brightness, speed))

        elif pattern == LEDPattern.PULSE:
            self.start_animation(lambda t: self._pulse_animation(pin, t, brightness, speed))

    def _blink_animation(self, pin: int, elapsed: float, brightness: float, speed: float):
        """Blinking animation (on/off)"""
        cycle_duration = 1.0 / speed  # 1 second per cycle at speed=1.0
        phase = (elapsed % cycle_duration) / cycle_duration

        if phase < 0.5:
            self._set_led(pin, brightness)
        else:
            self._set_led(pin, 0.0)

    def _breathing_animation(self, pin: int, elapsed: float, brightness: float, speed: float):
        """Breathing animation (smooth sine wave)"""
        cycle_duration = 2.0 / speed  # 2 seconds per cycle at speed=1.0
        phase = (elapsed % cycle_duration) / cycle_duration

        # Sine wave (0 to 1 to 0)
        value = (math.sin(phase * 2 * math.pi - math.pi / 2) + 1) / 2
        self._set_led(pin, value * brightness)

    def _pulse_animation(self, pin: int, elapsed: float, brightness: float, speed: float):
        """Pulse animation (fast heartbeat)"""
        cycle_duration = 1.0 / speed  # 1 second per cycle at speed=1.0
        phase = (elapsed % cycle_duration) / cycle_duration

        # Two quick pulses
        if phase < 0.15:
            value = 1.0
        elif phase < 0.30:
            value = 0.0
        elif phase < 0.45:
            value = 1.0
        else:
            value = 0.0

        self._set_led(pin, value * brightness)

    def start_animation(self, animation_func):
        """
        Start LED animation

        Args:
            animation_func: Function(elapsed_time) to call for animation
        """
        self.stop_animation()

        self.running = True
        self.animation_func = animation_func
        self.animation_start_time = time.time()

        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()

    def _animation_loop(self):
        """Animation loop (runs in separate thread)"""
        while self.running:
            elapsed = time.time() - self.animation_start_time

            try:
                self.animation_func(elapsed)
            except Exception as e:
                self.logger.error(f"Animation error: {e}", exc_info=True)
                break

            time.sleep(0.05)  # 20 FPS

    def stop_animation(self):
        """Stop current LED animation"""
        if not self.running:
            return

        self.running = False

        if self.animation_thread:
            self.animation_thread.join(timeout=0.5)

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_animation()
        self._set_all_off()

        if not self.mock_mode and hasattr(self, 'GPIO'):
            try:
                # Stop PWM
                for pwm in self.pwm.values():
                    pwm.stop()

                # Cleanup GPIO
                self.GPIO.cleanup([self.idle_pin, self.active_pin, self.error_pin])
                self.logger.info("GPIO cleaned up")
            except Exception as e:
                self.logger.error(f"GPIO cleanup error: {e}")

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()


def test_led_controller():
    """
    Test function for LED controller

    Usage:
        # With real GPIO (Pi):
        python -m app.gpio.led

        # With mock GPIO (Mac):
        MOCK_GPIO=true python -m app.gpio.led
    """
    print("=" * 60)
    print("LED Controller Test")
    print("=" * 60)

    # Check mock mode
    mock_mode = os.getenv('MOCK_GPIO', 'false').lower() == 'true'

    if mock_mode:
        print("\n⚠️  MOCK_GPIO mode enabled")
        print("Simulating LED patterns...")
    else:
        print("\nUsing real GPIO hardware")

    # Initialize LED controller
    try:
        leds = LEDController(
            idle_pin=22,    # Green LED
            active_pin=23,  # Blue LED
            error_pin=24    # Red LED
        )
        print("✓ LED controller initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # Test each state
    states_to_test = [
        (LEDState.IDLE, "IDLE (Green solid)", 2),
        (LEDState.LISTENING, "LISTENING (Green breathing)", 4),
        (LEDState.PROCESSING, "PROCESSING (Blue pulsing)", 4),
        (LEDState.NARRATING, "NARRATING (Blue solid)", 2),
        (LEDState.ERROR, "ERROR (Red blinking)", 3),
        (LEDState.OFF, "OFF (All LEDs off)", 1),
    ]

    for state, description, duration in states_to_test:
        print(f"\n--- {description} ---")
        leds.set_state(state)
        time.sleep(duration)

    # Cleanup
    leds.cleanup()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_led_controller()
