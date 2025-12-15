"""
Audio Input Module for StoryBox IA

Handles microphone capture with hold-to-talk functionality.
Optimized for Raspberry Pi with USB or I2S microphones.

Features:
- Hold-to-talk recording (start on press, stop on release)
- Configurable buffer management (max duration limit)
- WAV file export for STT processing
- Mock mode for Mac development (load from file)
- Audio quality validation

Usage:
    from app.audio.input import AudioInput

    audio_in = AudioInput(config.audio.input)
    audio_in.start_recording()
    # ... hold button ...
    audio_data = audio_in.stop_recording()
    audio_in.save_wav(audio_data, "recording.wav")

Author: StoryBox IA Team
Date: 2024-12
"""

import os
import wave
import time
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import AudioInputConfig


logger = get_logger(__name__)


@dataclass
class AudioBuffer:
    """
    Audio buffer for recording

    Attributes:
        data: PCM audio data (int16)
        sample_rate: Sample rate in Hz
        channels: Number of channels (1=mono)
        duration: Duration in seconds
    """
    data: np.ndarray
    sample_rate: int
    channels: int

    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        return len(self.data) / (self.sample_rate * self.channels)

    @property
    def size_bytes(self) -> int:
        """Get size in bytes"""
        return self.data.nbytes


class AudioInput:
    """
    Audio input handler for StoryBox IA

    Captures audio from microphone with hold-to-talk functionality.
    Supports both real hardware (Pi) and mock mode (Mac).
    """

    def __init__(self, config: AudioInputConfig, mock_mode: Optional[bool] = None):
        """
        Initialize audio input

        Args:
            config: Audio input configuration
            mock_mode: Force mock mode (auto-detect if None)

        Raises:
            RuntimeError: If audio device cannot be opened
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Auto-detect mock mode (Mac development)
        if mock_mode is None:
            self.mock_mode = os.getenv('MOCK_AUDIO', 'false').lower() == 'true'
        else:
            self.mock_mode = mock_mode

        # Recording state
        self.is_recording = False
        self.recording_buffer = []
        self.start_time = None

        # Initialize audio system
        if not self.mock_mode:
            self._init_audio_device()
        else:
            self.logger.info("Mock mode enabled - audio will be loaded from files")

        self.logger.info("Audio input initialized successfully")
        self.logger.info(f"Sample rate: {config.sample_rate} Hz")
        self.logger.info(f"Channels: {config.channels}")
        self.logger.info(f"Device: {config.device or 'default'}")
        self.logger.info(f"Mock mode: {self.mock_mode}")

    def _init_audio_device(self):
        """
        Initialize audio device (Pi only)

        Uses sounddevice for audio capture.

        Raises:
            RuntimeError: If device cannot be opened
        """
        try:
            import sounddevice as sd
            self.sd = sd

            # Set default device if specified (ignore "default" string)
            if self.config.device and self.config.device != "default":
                self.sd.default.device = self.config.device

            # Test device availability
            devices = self.sd.query_devices()
            self.logger.debug(f"Available audio devices: {devices}")

            # Get input device info
            input_device = self.sd.query_devices(kind='input')
            self.logger.info(f"Using input device: {input_device['name']}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize audio device: {e}")

    def start_recording(self):
        """
        Start recording audio

        Should be called when hold-to-talk button is pressed.
        Clears any previous recording buffer.
        """
        if self.is_recording:
            self.logger.warning("Already recording, stopping previous recording")
            self.stop_recording()

        self.logger.info("Starting audio recording")

        # Reset buffer
        self.recording_buffer = []
        self.start_time = time.time()
        self.is_recording = True

        if not self.mock_mode:
            self._start_stream()
        else:
            self.logger.debug("Mock mode - recording simulation started")

    def _start_stream(self):
        """Start audio stream (Pi only)"""
        import sounddevice as sd

        # Audio callback
        def audio_callback(indata, frames, time_info, status):
            if status:
                self.logger.warning(f"Audio stream status: {status}")

            if self.is_recording:
                # Copy audio data to buffer
                audio_chunk = indata.copy()
                self.recording_buffer.append(audio_chunk)

                # Check max duration
                current_duration = len(self.recording_buffer) * frames / self.config.sample_rate
                if current_duration >= self.config.max_duration_s:
                    self.logger.warning(f"Max recording duration reached ({self.config.max_duration_s}s)")
                    self.stop_recording()

        # Start stream
        self.stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype='int16',
            callback=audio_callback,
            blocksize=int(self.config.sample_rate * 0.1)  # 100ms blocks
        )
        self.stream.start()
        self.logger.debug("Audio stream started")

    def stop_recording(self) -> Optional[AudioBuffer]:
        """
        Stop recording and return audio buffer

        Should be called when hold-to-talk button is released.

        Returns:
            AudioBuffer with recorded audio or None if no audio captured

        Example:
            >>> audio_in.start_recording()
            >>> time.sleep(3)  # Record for 3 seconds
            >>> buffer = audio_in.stop_recording()
            >>> print(f"Recorded {buffer.duration:.1f}s")
        """
        if not self.is_recording:
            self.logger.warning("Not recording, nothing to stop")
            return None

        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0

        self.logger.info(f"Stopping audio recording (duration: {duration:.2f}s)")

        if not self.mock_mode:
            self._stop_stream()

        # Process buffer
        if not self.recording_buffer:
            self.logger.warning("No audio data captured")
            return None

        # Concatenate audio chunks
        if not self.mock_mode:
            audio_data = np.concatenate(self.recording_buffer, axis=0)

            # Flatten if multi-channel
            if audio_data.ndim > 1:
                audio_data = audio_data[:, 0]  # Take first channel
        else:
            # Mock mode - return empty buffer (will be loaded from file later)
            audio_data = np.zeros(int(duration * self.config.sample_rate), dtype=np.int16)

        # Create buffer
        buffer = AudioBuffer(
            data=audio_data,
            sample_rate=self.config.sample_rate,
            channels=self.config.channels
        )

        # Log metrics
        log_metric("audio_recording_duration_s", buffer.duration)
        log_metric("audio_recording_size_bytes", buffer.size_bytes)

        self.logger.info(f"Captured {buffer.duration:.2f}s audio ({buffer.size_bytes} bytes)")

        # Validate audio quality
        self._validate_audio(buffer)

        return buffer

    def _stop_stream(self):
        """Stop audio stream (Pi only)"""
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            self.logger.debug("Audio stream stopped")

    def _validate_audio(self, buffer: AudioBuffer):
        """
        Validate audio quality

        Checks for:
        - Minimum duration
        - Silence detection (too quiet)
        - Clipping detection (too loud)

        Args:
            buffer: Audio buffer to validate
        """
        # Check minimum duration
        min_duration = 0.5  # 500ms
        if buffer.duration < min_duration:
            self.logger.warning(f"Audio too short: {buffer.duration:.2f}s (min: {min_duration}s)")

        # Convert to float for analysis
        audio_float = buffer.data.astype(np.float32) / 32768.0

        # Check for silence (RMS < -40dB)
        rms = np.sqrt(np.mean(audio_float ** 2))
        rms_db = 20 * np.log10(rms) if rms > 0 else -100

        if rms_db < -40:
            self.logger.warning(f"Audio very quiet (RMS: {rms_db:.1f}dB) - check microphone gain")

        # Check for clipping (>95% of max value)
        peak = np.abs(audio_float).max()
        if peak > 0.95:
            self.logger.warning(f"Audio clipping detected (peak: {peak:.2f}) - reduce microphone gain")

        # Log quality metrics
        self.logger.debug(f"Audio quality - RMS: {rms_db:.1f}dB, Peak: {peak:.2f}")

    def save_wav(self, buffer: AudioBuffer, output_path: Path) -> Path:
        """
        Save audio buffer to WAV file

        Args:
            buffer: Audio buffer to save
            output_path: Path to output WAV file

        Returns:
            Path to saved file

        Example:
            >>> buffer = audio_in.stop_recording()
            >>> audio_in.save_wav(buffer, Path("recording.wav"))
        """
        with wave.open(str(output_path), 'wb') as wav:
            wav.setnchannels(buffer.channels)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(buffer.sample_rate)
            wav.writeframes(buffer.data.tobytes())

        self.logger.info(f"Saved audio to {output_path}")
        return output_path

    def load_wav(self, input_path: Path) -> Optional[AudioBuffer]:
        """
        Load audio from WAV file (for testing/mock mode)

        Args:
            input_path: Path to WAV file

        Returns:
            AudioBuffer or None if file cannot be loaded

        Example:
            >>> buffer = audio_in.load_wav(Path("test_recording.wav"))
            >>> print(f"Loaded {buffer.duration:.1f}s")
        """
        if not input_path.exists():
            self.logger.error(f"Audio file not found: {input_path}")
            return None

        try:
            with wave.open(str(input_path), 'rb') as wav:
                sample_rate = wav.getframerate()
                channels = wav.getnchannels()
                frames = wav.readframes(wav.getnframes())

                # Convert to numpy array
                audio_data = np.frombuffer(frames, dtype=np.int16)

                # Handle multi-channel
                if channels > 1:
                    audio_data = audio_data.reshape(-1, channels)
                    audio_data = audio_data[:, 0]  # Take first channel

            buffer = AudioBuffer(
                data=audio_data,
                sample_rate=sample_rate,
                channels=1  # Always mono after extraction
            )

            self.logger.info(f"Loaded {buffer.duration:.2f}s audio from {input_path}")
            return buffer

        except Exception as e:
            self.logger.error(f"Failed to load audio: {e}", exc_info=True)
            return None

    def test_device(self) -> bool:
        """
        Test audio device by recording a short sample

        Records 1 second of audio and checks if data is captured.

        Returns:
            True if device is working, False otherwise

        Example:
            >>> if audio_in.test_device():
            ...     print("Microphone working!")
        """
        if self.mock_mode:
            self.logger.info("Mock mode - skipping device test")
            return True

        self.logger.info("Testing audio device...")

        try:
            self.start_recording()
            time.sleep(1.0)  # Record 1 second
            buffer = self.stop_recording()

            if buffer and buffer.duration >= 0.9:
                self.logger.info("Audio device test: PASS")
                return True
            else:
                self.logger.error("Audio device test: FAIL (no data captured)")
                return False

        except Exception as e:
            self.logger.error(f"Audio device test: FAIL ({e})")
            return False

    def get_device_list(self) -> list:
        """
        Get list of available audio input devices

        Returns:
            List of device info dictionaries
        """
        if self.mock_mode:
            return [{"name": "Mock Audio Device", "index": 0}]

        try:
            import sounddevice as sd
            devices = sd.query_devices()

            # Filter input devices
            input_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })

            return input_devices

        except Exception as e:
            self.logger.error(f"Failed to query devices: {e}")
            return []

    def __del__(self):
        """Cleanup on destruction"""
        if self.is_recording:
            self.stop_recording()


def test_audio_input():
    """
    Test function for audio input module

    Run this to verify audio capture is working.

    Usage:
        python -m app.audio.input
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("Audio Input Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Check if mock mode
    mock_mode = os.getenv('MOCK_AUDIO', 'false').lower() == 'true'

    if mock_mode:
        print("\n⚠️  MOCK_AUDIO mode enabled")
        print("Testing with mock audio files...")

        # Initialize with mock mode
        try:
            audio_in = AudioInput(config.audio.input, mock_mode=True)
            print("✓ Audio input initialized (mock mode)")
        except Exception as e:
            print(f"✗ Failed to initialize: {e}")
            return

        # Test loading audio file
        print("\n--- Test: Load WAV file ---")
        test_files = list(Path("test/audio_samples").glob("*.wav"))

        if test_files:
            test_file = test_files[0]
            buffer = audio_in.load_wav(test_file)

            if buffer:
                print(f"✓ Loaded {buffer.duration:.2f}s audio")
                print(f"  Sample rate: {buffer.sample_rate} Hz")
                print(f"  Channels: {buffer.channels}")
                print(f"  Size: {buffer.size_bytes} bytes")
            else:
                print("✗ Failed to load audio")
        else:
            print("⚠️  No test audio files found in test/audio_samples/")
            print("Run: python -m app.tts.piper_tts to generate test audio")

    else:
        print("\nTesting with real microphone...")
        print("Make sure a microphone is connected!")

        # Initialize audio input
        try:
            audio_in = AudioInput(config.audio.input)
            print("✓ Audio input initialized")
        except Exception as e:
            print(f"✗ Failed to initialize: {e}")
            print("\nTip: Set MOCK_AUDIO=true for testing without hardware")
            return

        # List devices
        print("\n--- Available Input Devices ---")
        devices = audio_in.get_device_list()
        for device in devices:
            print(f"  [{device['index']}] {device['name']}")
            print(f"      Channels: {device['channels']}, SR: {device['sample_rate']} Hz")

        # Test device
        print("\n--- Test: Device Check ---")
        if audio_in.test_device():
            print("✓ Device test passed")
        else:
            print("✗ Device test failed")
            return

        # Test recording
        print("\n--- Test: 3-second Recording ---")
        print("Recording in 2 seconds...")
        time.sleep(2)

        print("🎙️  Recording... (speak now!)")
        audio_in.start_recording()
        time.sleep(3)
        buffer = audio_in.stop_recording()

        if buffer:
            print(f"✓ Recorded {buffer.duration:.2f}s audio")
            print(f"  Sample rate: {buffer.sample_rate} Hz")
            print(f"  Size: {buffer.size_bytes} bytes")

            # Save to file
            output_file = Path("test_audio_input.wav")
            audio_in.save_wav(buffer, output_file)
            print(f"  Saved to: {output_file}")
            print(f"\nPlay back: aplay {output_file}")
        else:
            print("✗ No audio captured")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run test when module is executed directly
    test_audio_input()
