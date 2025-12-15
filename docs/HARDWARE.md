# StoryBox IA - Hardware Setup Guide

Complete guide for connecting audio hardware to the Raspberry Pi 4B.

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Microphone Setup](#microphone-setup)
3. [Speaker/Amplifier Setup](#speakeramplifier-setup)
4. [GPIO Button and LED Setup](#gpio-button-and-led-setup)
5. [Audio Configuration (ALSA)](#audio-configuration-alsa)
6. [Testing Procedures](#testing-procedures)
7. [Troubleshooting](#troubleshooting)

---

## Hardware Overview

### Bill of Materials (BOM)

| Component | Recommended Option | Alternative Option | Price (€) |
|-----------|-------------------|-------------------|-----------|
| **Microphone** | USB Microphone | I2S MEMS (INMP441) | 10-30 |
| **Speaker** | USB Speaker/Amplifier | I2S DAC HAT + Speaker | 15-50 |
| **Button** | Arcade button (momentary) | Tactile button | 2-5 |
| **LEDs** | 3x 5mm LEDs (RGB) | NeoPixel strip | 1-10 |
| **Resistors** | 3x 220Ω (for LEDs) | - | 1 |
| **Power Supply** | 5V 3A USB-C | - | 10 |
| **SD Card** | 32GB Class 10 | 64GB+ for more logs | 10 |

**Total Cost:** ~50-100€ depending on choices

---

## Microphone Setup

### Option 1: USB Microphone (RECOMMENDED)

**Pros:**
- Plug-and-play (no wiring needed)
- Built-in ADC (Analog-to-Digital Converter)
- Better noise isolation
- Easier to replace or upgrade

**Cons:**
- Requires USB port
- Slightly higher power consumption

#### Recommended USB Microphones

1. **TONOR TC30** (~15€)
   - USB plug-and-play
   - Good speech recognition quality
   - Cardioid pattern (reduces background noise)

2. **Blue Snowball iCE** (~50€)
   - Professional quality
   - Excellent for voice capture
   - Heavy/bulky for portable projects

3. **Generic USB microphone** (~10€)
   - Search for "USB microphone conference" or "USB lavalier microphone"
   - Sufficient for STT if sample rate ≥16kHz

#### Wiring/Connection

```
┌──────────────┐
│ Raspberry Pi │
│              │
│   USB Port   ├──────> USB Microphone
│              │
└──────────────┘
```

**No wiring required!** Just plug into any USB port.

#### Software Configuration

After plugging in, verify detection:

```bash
# List audio input devices
arecord -l

# Expected output:
# card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
```

Update `.env` to use USB microphone:

```bash
AUDIO_INPUT_DEVICE=hw:1,0  # Card 1, Device 0
```

---

### Option 2: I2S MEMS Microphone (ADVANCED)

**Pros:**
- No USB port required
- Lower latency
- Smaller form factor
- Can use multiple microphones

**Cons:**
- Requires soldering/wiring
- More complex software setup
- Potential noise from Pi circuitry

#### Recommended I2S Microphones

1. **INMP441** (~5€)
   - I2S digital MEMS microphone
   - 24-bit resolution
   - Good SNR (61 dB)

2. **SPH0645** (Adafruit) (~10€)
   - Similar to INMP441
   - Well-documented by Adafruit

#### Wiring Diagram: INMP441 to Raspberry Pi

```
INMP441 Pin     Raspberry Pi Pin         GPIO/Function
-----------     --------------------     -------------
VDD         →   Pin 1  (3.3V)            Power
GND         →   Pin 6  (GND)             Ground
SD          →   Pin 38 (GPIO 20)         I2S Data In (DOUT)
WS          →   Pin 35 (GPIO 19)         I2S Frame Sync (LRCLK)
SCK         →   Pin 12 (GPIO 18)         I2S Bit Clock (BCLK)
L/R         →   GND (for left channel)   Channel Select


Raspberry Pi 4B GPIO Pinout (relevant pins):
┌─────────────────────────────────┐
│  1  3.3V        ●  ●  5V    2   │
│  3              ●  ●  5V    4   │
│  5              ●  ●  GND   6   │  ← Ground
│  7              ●  ●       8    │
│  9  GND         ●  ●       10   │
│ 11              ●  ● GPIO18 12  │  ← I2S BCK
│ 13              ●  ●  GND  14   │
│ 15              ●  ●       16   │
│ 17  3.3V        ●  ●       18   │
│ 19              ●  ●  GND  20   │
│ 21              ●  ●       22   │
│ 23              ●  ●       24   │
│ 25  GND         ●  ●       26   │
│ 27              ●  ●       28   │
│ 29              ●  ●  GND  30   │
│ 31              ●  ●       32   │
│ 33              ●  ●       34   │
│ 35 GPIO19       ●  ●       36   │  ← I2S LRCLK
│ 37              ●  ● GPIO20 38  │  ← I2S DIN
│ 39  GND         ●  ●       40   │
└─────────────────────────────────┘
```

#### Software Configuration (I2S)

1. **Enable I2S in `/boot/config.txt`:**

```bash
sudo nano /boot/config.txt

# Add the following line:
dtoverlay=i2s-mmap
dtoverlay=googlevoicehat-soundcard
```

2. **Reboot:**

```bash
sudo reboot
```

3. **Verify I2S device:**

```bash
arecord -l

# Expected output:
# card 0: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar], device 0
```

4. **Update `.env`:**

```bash
AUDIO_INPUT_DEVICE=hw:0,0
```

---

## Speaker/Amplifier Setup

### Option 1: USB Speaker (RECOMMENDED)

**Pros:**
- Plug-and-play
- Built-in amplifier
- No wiring needed
- Volume control via ALSA

**Cons:**
- Requires USB port
- May need external power for loud volumes

#### Recommended USB Speakers

1. **Generic USB Speaker** (~15€)
   - Search for "USB computer speaker" or "USB mini speaker"
   - Ensure it works with Linux (most do)

2. **Creative Pebble V2** (~25€)
   - USB-powered
   - Good audio quality
   - 8W RMS

3. **Logitech S150** (~20€)
   - USB digital speaker
   - Compact and affordable

#### Wiring/Connection

```
┌──────────────┐
│ Raspberry Pi │
│              │
│   USB Port   ├──────> USB Speaker
│              │
└──────────────┘
```

**No wiring required!**

#### Software Configuration

```bash
# List audio output devices
aplay -l

# Expected output:
# card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]
```

Update `.env`:

```bash
AUDIO_OUTPUT_DEVICE=hw:2,0
```

---

### Option 2: I2S DAC HAT + Passive Speaker (BETTER QUALITY)

**Pros:**
- Superior audio quality
- No USB ports required
- Lower latency
- Can drive higher power speakers

**Cons:**
- More expensive
- Requires HAT installation
- More complex setup

#### Recommended I2S DAC HATs

1. **HiFiBerry DAC+ Standard** (~35€)
   - High-quality 24-bit/192kHz DAC
   - 3.5mm stereo output
   - Well-supported in Linux

2. **Adafruit I2S 3W Stereo Speaker Bonnet** (~15€)
   - Built-in 3W amplifier
   - Terminal blocks for speakers
   - Integrated volume control

3. **Justboom DAC HAT** (~30€)
   - Professional audio quality
   - RCA outputs

#### Wiring: HiFiBerry DAC+ HAT

**HAT Installation:**

```
1. Power off Raspberry Pi
2. Align HAT with GPIO header (40 pins)
3. Gently press down until fully seated
4. Secure with standoffs (if provided)

┌────────────────────┐
│   HiFiBerry DAC+   │
│   ┌──────────┐     │
│   │3.5mm Jack│     │  ← Connect passive speaker or headphones
│   └──────────┘     │
└─────┬──────────────┘
      │ GPIO Header (40-pin)
      ↓
┌─────────────────────┐
│   Raspberry Pi 4B   │
└─────────────────────┘
```

**Speaker Connection (if using Adafruit Bonnet with amplifier):**

```
Adafruit Bonnet Terminal Blocks:

[L+] [L-]    [R+] [R-]
  ↓    ↓       ↓    ↓
Left Speaker  Right Speaker
(4Ω-8Ω,       (4Ω-8Ω,
 3W max)       3W max)
```

#### Software Configuration (I2S DAC HAT)

1. **Disable onboard audio and enable I2S in `/boot/config.txt`:**

```bash
sudo nano /boot/config.txt

# Comment out or remove:
# dtparam=audio=on

# Add (for HiFiBerry DAC+):
dtoverlay=hifiberry-dacplus
```

For Adafruit Bonnet:
```bash
dtoverlay=hifiberry-dac
```

2. **Reboot:**

```bash
sudo reboot
```

3. **Verify device:**

```bash
aplay -l

# Expected output:
# card 0: sndrpihifiberry [snd_rpi_hifiberry_dacplus], device 0
```

4. **Update `.env`:**

```bash
AUDIO_OUTPUT_DEVICE=hw:0,0
```

---

### Option 3: 3.5mm Analog Output + Amplifier (BUDGET OPTION)

**Pros:**
- Uses built-in audio jack
- Very cheap
- Simple setup

**Cons:**
- Poor audio quality (noisy)
- Low volume without amplifier
- Not recommended for production

#### Setup

1. Connect 3.5mm speaker to Raspberry Pi audio jack
2. Enable analog audio in `/boot/config.txt`:

```bash
dtparam=audio=on
```

3. Force 3.5mm output:

```bash
sudo raspi-config
# → System Options → Audio → Headphones
```

4. Update `.env`:

```bash
AUDIO_OUTPUT_DEVICE=hw:0,0  # bcm2835 Headphones
```

**Note:** This option is **not recommended** due to poor audio quality and noise.

---

## GPIO Button and LED Setup

### GPIO Pin Assignments

From `configs/default.yaml`:

```yaml
gpio:
  button_pin: 17        # Hold-to-talk button
  led_pin_idle: 22      # Green LED (Idle state)
  led_pin_active: 23    # Blue LED (Processing state)
  led_pin_error: 24     # Red LED (Error state)
  debounce_ms: 50       # Button debounce time
```

### Wiring Diagram

```
Button Wiring (Normally Open Momentary):
┌───────────┐
│           │
│  Button   │
│  ┌─────┐  │
│  │     │  │
└──┴─────┴──┘
   │     │
   │     └─────> GPIO 17 (Pin 11)
   │
   └───────────> GND (Pin 9)


LED Wiring (with current-limiting resistors):
┌──────────────────────────────────────────┐
│         Raspberry Pi GPIO                │
│                                          │
│  GPIO 22 (Pin 15) ──┬──[220Ω]──┬─(+)Green LED(-)─┬── GND (Pin 14)
│  GPIO 23 (Pin 16) ──┼──[220Ω]──┼─(+)Blue LED(-)──┤
│  GPIO 24 (Pin 18) ──┴──[220Ω]──┴─(+)Red LED(-)───┘
│                                          │
└──────────────────────────────────────────┘

LED Polarity:
  Longer leg (+) → Resistor → GPIO
  Shorter leg (-) → GND
```

### Physical Layout

```
Raspberry Pi 4B GPIO (Top View):
┌─────────────────────────────────┐
│  1  3.3V        ●  ●  5V    2   │
│  3              ●  ●  5V    4   │
│  5              ●  ●  GND   6   │
│  7              ●  ●       8    │
│  9  GND         ●  ●       10   │  ← Button GND
│ 11 GPIO17       ●  ●       12   │  ← Button Signal
│ 13              ●  ●  GND  14   │  ← LEDs GND
│ 15 GPIO22       ●  ●       16   │  ← Green LED (Idle)
│ 17  3.3V        ●  ● GPIO23 18  │  ← Blue LED (Active)
│ 19              ●  ●  GND  20   │
│ 21              ●  ●       22   │
│ 23              ●  ● GPIO24 24  │  ← Red LED (Error)
│ 25  GND         ●  ●       26   │
│ ...                             │
└─────────────────────────────────┘
```

### Button Types

1. **Arcade Button (Recommended)** (~3€)
   - Large, easy to press
   - Satisfying tactile feedback
   - Durable (100k+ presses)
   - Available in colors

2. **Tactile Push Button** (~1€)
   - Compact
   - PCB-mountable
   - Lower tactile feedback

3. **Capacitive Touch Sensor** (~5€)
   - No moving parts
   - Modern look
   - More complex wiring

### LED Options

1. **Standard 5mm LEDs** (~0.50€)
   - Simple, cheap
   - Easy to wire
   - Recommended for beginners

2. **NeoPixel Strip (WS2812B)** (~10€)
   - RGB addressable LEDs
   - Fancier animations possible
   - Requires `rpi_ws281x` library
   - Single data wire

---

## Rotary Encoder for Volume Control (Optional)

### Overview

A rotary encoder allows hardware volume control without software intervention.
User can adjust speaker volume by rotating the knob during narration.

**Recommended:** KY-040 Rotary Encoder (~3€)

### Features

- Clockwise rotation: Increase volume
- Counter-clockwise rotation: Decrease volume
- Push button: Mute/unmute (optional)
- 20 detents per revolution
- 5V compatible

### Wiring Diagram: KY-040 to Raspberry Pi

```
KY-040 Pin      Raspberry Pi Pin         GPIO/Function
----------      --------------------     -------------
GND         →   Pin 6  (GND)             Ground
+           →   Pin 1  (3.3V)            Power
SW          →   Pin 13 (GPIO 27)         Switch (optional mute)
DT          →   Pin 29 (GPIO 5)          Encoder Data
CLK         →   Pin 31 (GPIO 6)          Encoder Clock


Raspberry Pi 4B GPIO (relevant pins):
┌─────────────────────────────────┐
│  1  3.3V        ●  ●  5V    2   │  ← Encoder power
│  3              ●  ●  5V    4   │
│  5              ●  ●  GND   6   │  ← Encoder GND
│  7              ●  ●       8    │
│  9  GND         ●  ●       10   │
│ 11 GPIO17       ●  ●       12   │  (Button)
│ 13 GPIO27       ●  ●  GND  14   │  ← Encoder SW
│ ...                             │
│ 29 GPIO5        ●  ●       30   │  ← Encoder DT
│ 31 GPIO6        ●  ●       32   │  ← Encoder CLK
│ ...                             │
└─────────────────────────────────┘
```

### GPIO Pin Configuration

Add to `configs/default.yaml`:

```yaml
gpio:
  button_pin: 17
  led_pin_idle: 22
  led_pin_active: 23
  led_pin_error: 24

  # Rotary encoder (optional)
  encoder_clk_pin: 6      # Encoder clock signal
  encoder_dt_pin: 5       # Encoder data signal
  encoder_sw_pin: 27      # Encoder switch (mute button)

  debounce_ms: 50
```

### Software Implementation

Create `app/gpio/encoder.py`:

```python
import RPi.GPIO as GPIO
from typing import Callable, Optional

class RotaryEncoder:
    """
    Rotary encoder for volume control

    Usage:
        encoder = RotaryEncoder(clk_pin=6, dt_pin=5, sw_pin=27)
        encoder.on_clockwise(lambda: increase_volume())
        encoder.on_counter_clockwise(lambda: decrease_volume())
        encoder.on_button_press(lambda: toggle_mute())
        encoder.start()
    """

    def __init__(self, clk_pin: int, dt_pin: int, sw_pin: Optional[int] = None):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        if sw_pin:
            GPIO.setup(sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Callbacks
        self.clockwise_callback = None
        self.counter_clockwise_callback = None
        self.button_callback = None

        # State
        self.last_clk = GPIO.input(clk_pin)

    def on_clockwise(self, callback: Callable):
        """Register callback for clockwise rotation"""
        self.clockwise_callback = callback

    def on_counter_clockwise(self, callback: Callable):
        """Register callback for counter-clockwise rotation"""
        self.counter_clockwise_callback = callback

    def on_button_press(self, callback: Callable):
        """Register callback for button press"""
        self.button_callback = callback

    def _rotation_callback(self, channel):
        """Handle rotation interrupt"""
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)

        if clk_state != self.last_clk:
            if dt_state != clk_state:
                # Clockwise
                if self.clockwise_callback:
                    self.clockwise_callback()
            else:
                # Counter-clockwise
                if self.counter_clockwise_callback:
                    self.counter_clockwise_callback()

        self.last_clk = clk_state

    def _button_callback(self, channel):
        """Handle button press interrupt"""
        if self.button_callback:
            self.button_callback()

    def start(self):
        """Start encoder monitoring"""
        # Add event detection for rotation
        GPIO.add_event_detect(
            self.clk_pin,
            GPIO.BOTH,
            callback=self._rotation_callback,
            bouncetime=2
        )

        # Add event detection for button
        if self.sw_pin:
            GPIO.add_event_detect(
                self.sw_pin,
                GPIO.FALLING,
                callback=self._button_callback,
                bouncetime=300
            )

    def cleanup(self):
        """Cleanup GPIO"""
        GPIO.cleanup([self.clk_pin, self.dt_pin])
        if self.sw_pin:
            GPIO.cleanup(self.sw_pin)
```

### Volume Control with ALSA

Integrate encoder with ALSA volume control:

```python
import subprocess

class VolumeController:
    """Control system volume via ALSA"""

    def __init__(self, control_name='Speaker', step=5):
        self.control_name = control_name
        self.step = step  # Volume step (%)
        self.muted = False

    def increase(self):
        """Increase volume by step"""
        subprocess.run(['amixer', 'set', self.control_name, f'{self.step}%+'])

    def decrease(self):
        """Decrease volume by step"""
        subprocess.run(['amixer', 'set', self.control_name, f'{self.step}%-'])

    def toggle_mute(self):
        """Toggle mute"""
        if self.muted:
            subprocess.run(['amixer', 'set', self.control_name, 'unmute'])
        else:
            subprocess.run(['amixer', 'set', self.control_name, 'mute'])
        self.muted = not self.muted

    def get_volume(self) -> int:
        """Get current volume (0-100)"""
        result = subprocess.run(
            ['amixer', 'get', self.control_name],
            capture_output=True,
            text=True
        )
        # Parse output: [75%]
        import re
        match = re.search(r'\[(\d+)%\]', result.stdout)
        return int(match.group(1)) if match else 50
```

### Usage in Main Application

Add to `app/main.py`:

```python
from app.gpio.encoder import RotaryEncoder, VolumeController

class StoryBoxApp:
    def _init_modules(self):
        # ... existing modules ...

        # Volume control (optional)
        if hasattr(self.config.gpio, 'encoder_clk_pin'):
            self.logger.info("→ GPIO (Volume Encoder)...")
            self.encoder = RotaryEncoder(
                clk_pin=self.config.gpio.encoder_clk_pin,
                dt_pin=self.config.gpio.encoder_dt_pin,
                sw_pin=self.config.gpio.encoder_sw_pin
            )
            self.volume = VolumeController(step=5)

            # Register callbacks
            self.encoder.on_clockwise(self.volume.increase)
            self.encoder.on_counter_clockwise(self.volume.decrease)
            self.encoder.on_button_press(self.volume.toggle_mute)

            self.encoder.start()
```

### Testing

Test encoder functionality:

```bash
# On Pi
python3 << 'EOF'
from app.gpio.encoder import RotaryEncoder, VolumeController

encoder = RotaryEncoder(clk_pin=6, dt_pin=5, sw_pin=27)
volume = VolumeController()

encoder.on_clockwise(lambda: print(f"Volume UP → {volume.get_volume()}%"))
encoder.on_counter_clockwise(lambda: print(f"Volume DOWN → {volume.get_volume()}%"))
encoder.on_button_press(lambda: print("MUTE toggled"))

encoder.start()

print("Rotate encoder to test (Ctrl+C to exit)")
try:
    import time
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    encoder.cleanup()
EOF
```

**Expected output:**
```
Rotate encoder to test (Ctrl+C to exit)
Volume UP → 65%
Volume UP → 70%
Volume DOWN → 65%
MUTE toggled
```

### Alternative: Software Volume Control

If rotary encoder is not available, implement software volume control via button:

- **Short press (≤0.5s):** Pause/resume narration
- **Medium press (0.5-2s):** Cycle volume (Low → Medium → High)
- **Long press (≥3s):** Shutdown

---

## Audio Configuration (ALSA)

### Setting Default Audio Devices

Create/edit `~/.asoundrc`:

```bash
nano ~/.asoundrc
```

**For USB Microphone (Card 1) + USB Speaker (Card 2):**

```conf
pcm.!default {
    type asym
    playback.pcm "hw:2,0"   # USB Speaker
    capture.pcm "hw:1,0"    # USB Microphone
}

ctl.!default {
    type hw
    card 2
}
```

**For I2S Microphone (Card 0) + HiFiBerry DAC (Card 0):**

```conf
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
```

### Volume Control

```bash
# List controls
amixer scontrols

# Set microphone capture level (0-100%)
amixer set 'Mic' 80%

# Set speaker volume
amixer set 'Speaker' 70%

# Unmute
amixer set 'Speaker' unmute
```

### Test Commands

**Test Microphone (Record 5 seconds):**

```bash
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_recording.wav
```

**Test Speaker (Play WAV file):**

```bash
aplay -D hw:2,0 test_recording.wav
```

---

## Testing Procedures

### 1. Audio Loopback Test

Test microphone → speaker pipeline:

```bash
# Record 5 seconds
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav

# Play back
aplay -D hw:2,0 test.wav
```

**Expected:** Clear audio playback of your voice.

### 2. STT Test

Test speech recognition:

```bash
# Activate virtual environment
source .venv/bin/activate

# Record audio
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_stt.wav

# Transcribe
python -m app.stt.whisper_stt
# (Manually test with test_stt.wav)
```

### 3. TTS Test

Test speech synthesis:

```bash
python -m app.tts.piper_tts
# Should generate test_tts_output_*.wav files

# Play
aplay -D hw:2,0 test_tts_output_1.wav
```

### 4. GPIO Button Test

Test button input:

```bash
# On Pi (with button wired to GPIO 17):
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

BUTTON_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Press button (Ctrl+C to exit)...")
try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Button pressed!")
            time.sleep(0.5)
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
EOF
```

### 5. GPIO LED Test

Test LED outputs:

```bash
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

LED_PINS = [22, 23, 24]  # Green, Blue, Red
GPIO.setmode(GPIO.BCM)
for pin in LED_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

print("Testing LEDs...")
for i in range(3):
    for pin in LED_PINS:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(pin, GPIO.LOW)

GPIO.cleanup()
print("Done!")
EOF
```

---

## Troubleshooting

### Microphone Issues

**Problem:** `arecord -l` shows no devices

**Solutions:**
- Check USB connection
- Try different USB port
- Check `lsusb` to verify device is detected
- Reboot Pi

**Problem:** Audio is very quiet

**Solutions:**
```bash
# Increase capture volume
amixer set 'Mic' 100%

# Check input level with VU meter
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -V mono test.wav
```

**Problem:** Lots of background noise

**Solutions:**
- Use a better quality USB microphone
- Enable noise reduction in STT preprocessing
- Move Pi away from fan/power supply
- Use shielded USB cable

### Speaker Issues

**Problem:** No sound output

**Solutions:**
```bash
# Check device is detected
aplay -l

# Test with known-good audio file
speaker-test -D hw:2,0 -c 2

# Unmute and increase volume
amixer set 'Speaker' unmute
amixer set 'Speaker' 80%
```

**Problem:** Crackling/distorted audio

**Solutions:**
- Reduce volume: `amixer set 'Speaker' 60%`
- Use better power supply (5V 3A recommended)
- Check for USB power issues (use powered USB hub if needed)

### GPIO Issues

**Problem:** Button not working

**Solutions:**
- Verify wiring with multimeter
- Test continuity when button pressed
- Check pin number (BCM vs Board numbering)
- Add external pull-up resistor (10kΩ) if internal pull-up insufficient

**Problem:** LEDs not lighting up

**Solutions:**
- Check polarity (longer leg is positive)
- Verify resistor value (220Ω for 3.3V GPIO)
- Test LED with multimeter/battery
- Check GPIO pin isn't in use by another service

### I2S Issues

**Problem:** I2S device not showing up

**Solutions:**
```bash
# Check device tree overlays are loaded
vcgencmd get_config dtoverlay

# Should show: hifiberry-dacplus (or similar)

# Verify I2S is enabled
dmesg | grep i2s
```

**Problem:** I2S audio has clicking/popping

**Solutions:**
```bash
# Increase buffer size in /etc/asound.conf
pcm.!default {
    type hw
    card 0
    period_size 1024
    buffer_size 4096
}
```

---

## Power Considerations

### Power Budget

| Component | Current Draw | Notes |
|-----------|--------------|-------|
| Raspberry Pi 4B | 600-1200 mA | Depends on CPU load |
| USB Microphone | 50-100 mA | Minimal |
| USB Speaker | 200-500 mA | Depends on volume |
| LEDs (3x) | 60 mA | 20mA each at full brightness |
| GPIO Button | <1 mA | Negligible |
| **Total** | **~1-2A** | Peak during audio playback |

### Recommended Power Supply

- **5V 3A USB-C Power Supply** (official Raspberry Pi PSU recommended)
- Ensure cable is high quality (low resistance)
- For high-power USB speakers, consider powered USB hub

### Power Optimization

```bash
# Disable HDMI (saves ~25mA)
sudo /opt/vc/bin/tvservice -o

# Reduce LED brightness in code
GPIO.PWM(led_pin, 100)  # 100 Hz frequency
pwm.start(50)  # 50% duty cycle (half brightness)
```

---

## Recommended Hardware Combinations

### Budget Setup (~40€)

- Generic USB Microphone (~10€)
- Generic USB Speaker (~15€)
- Arcade Button (~3€)
- 3x LEDs + Resistors (~2€)
- Raspberry Pi 4B 4GB (~50€, already owned)

**Pros:** Simple, plug-and-play, easy to assemble

### Premium Setup (~120€)

- Blue Snowball iCE USB Microphone (~50€)
- HiFiBerry DAC+ HAT (~35€)
- Passive Bookshelf Speaker 4Ω (~25€)
- Illuminated Arcade Button (~10€)
- Raspberry Pi 4B 8GB (~80€, already owned)

**Pros:** Excellent audio quality, professional results

### Portable/Embedded Setup (~60€)

- I2S MEMS Microphone (INMP441) (~5€)
- Adafruit I2S 3W Speaker Bonnet (~15€)
- 2x 4Ω 3W Speakers (~15€)
- Tactile Button (~1€)
- 3x LEDs + Resistors (~2€)
- Raspberry Pi 4B 4GB + Battery HAT (~70€)

**Pros:** Compact, no USB cables, battery-powered option

---

## Next Steps

1. **Purchase hardware** based on your budget and requirements
2. **Wire GPIO components** following diagrams above
3. **Test audio devices** using commands in Testing Procedures
4. **Update `.env`** with correct device identifiers
5. **Run integration tests** (see `docs/MODULES.md`)
6. **Proceed to `app/audio/input.py` implementation**

For software setup, see:
- `docs/RASPBERRY_PI_SETUP.md` - Complete Pi software installation
- `docs/MAC_DEVELOPMENT.md` - Local development with mocks
- `docs/MODULES.md` - API documentation for all modules

---

## References

- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [HiFiBerry Documentation](https://www.hifiberry.com/docs/)
- [Adafruit I2S Guide](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout)
- [ALSA Documentation](https://www.alsa-project.org/wiki/Main_Page)
- [RPi.GPIO Documentation](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/)
