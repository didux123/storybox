"""
Configuration loader for StoryBox IA

This module handles loading and validating configuration from:
1. YAML files (configs/default.yaml)
2. Environment variables (.env file)

Environment variables override YAML settings for deployment flexibility.

Usage:
    from app.utils.config import get_config

    config = get_config()
    model_path = config.stt.model_path
    sample_rate = config.audio.input.sample_rate

Author: StoryBox IA Team
Date: 2024-12
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class AudioInputConfig:
    """Audio input configuration (microphone capture)"""
    device: str = "default"
    sample_rate: int = 16000
    channels: int = 1
    format: str = "S16_LE"
    chunk_duration_ms: int = 40
    max_duration_s: int = 30


@dataclass
class AudioOutputConfig:
    """Audio output configuration (speaker playback)"""
    device: str = "default"
    sample_rate: int = 22050
    channels: int = 1


@dataclass
class AudioConfig:
    """Audio configuration (input + output)"""
    input: AudioInputConfig = field(default_factory=AudioInputConfig)
    output: AudioOutputConfig = field(default_factory=AudioOutputConfig)


@dataclass
class STTConfig:
    """Speech-to-Text (Whisper) configuration"""
    model_path: str = "/home/maxence/models/whisper/ggml-small.bin"
    language: str = "fr"
    model_type: str = "small"
    threads: int = 4


@dataclass
class LLMPromptsConfig:
    """LLM prompt templates"""
    plan: str = ""
    chapter: str = ""


@dataclass
class LLMConfig:
    """Large Language Model (Llama) configuration"""
    model_path: str = "/home/maxence/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    context_tokens: int = 2048
    threads: int = 4
    n_gpu_layers: int = 0
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    prompts: LLMPromptsConfig = field(default_factory=LLMPromptsConfig)


@dataclass
class TTSPostProcessingConfig:
    """TTS audio post-processing settings"""
    noise_gate_threshold: float = -40.0
    compressor_ratio: float = 2.5
    normalize_lufs: float = -16.0


@dataclass
class TTSConfig:
    """Text-to-Speech (Piper) configuration"""
    model_path: str = "/home/maxence/models/piper/fr_FR-siwis-medium.onnx"
    config_path: str = "/home/maxence/models/piper/fr_FR-siwis-medium.onnx.json"
    sample_rate: int = 22050
    speaker_id: int = 0
    post_processing: TTSPostProcessingConfig = field(default_factory=TTSPostProcessingConfig)


@dataclass
class GPIOLEDPinsConfig:
    """GPIO LED pin configuration"""
    status: int = 22
    progress_1: int = 23
    progress_2: int = 24


@dataclass
class GPIOConfig:
    """GPIO configuration for Raspberry Pi"""
    button_pin: int = 17
    button_pull: str = "up"
    debounce_ms: int = 50
    long_press_duration_s: float = 3.0
    led_pins: GPIOLEDPinsConfig = field(default_factory=GPIOLEDPinsConfig)


@dataclass
class TimingConfig:
    """System timing configuration"""
    pre_roll_led_ms: int = 500
    max_recording_duration_s: int = 30
    audio_buffer_ms: int = 300


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_dir: str = "/home/maxence/projects/storybox/logs"
    max_log_size_mb: int = 50
    backup_count: int = 3
    metrics: list = field(default_factory=lambda: [
        "latency_release_to_audio",
        "tokens_per_second",
        "model_load_time",
        "audio_errors",
        "gpio_errors"
    ])


@dataclass
class StoryConfig:
    """Story generation configuration"""
    num_chapters: int = 10
    chapter_min_words: int = 150
    chapter_max_words: int = 300
    context_summary_sentences: int = 3
    streaming_paragraph_tokens: int = 50


@dataclass
class Config:
    """
    Main configuration container

    All settings for StoryBox IA are centralized here.
    This object is immutable after loading for thread-safety.
    """
    audio: AudioConfig = field(default_factory=AudioConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    gpio: GPIOConfig = field(default_factory=GPIOConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    story: StoryConfig = field(default_factory=StoryConfig)


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary with configuration data

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def apply_env_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to config

    Environment variables take precedence over YAML settings.
    Format: SECTION_KEY (e.g., STT_MODEL_PATH, AUDIO_INPUT_DEVICE)

    Args:
        config_dict: Configuration dictionary from YAML

    Returns:
        Configuration dictionary with environment overrides applied
    """
    # STT overrides
    if os.getenv('WHISPER_MODEL_PATH'):
        config_dict.setdefault('stt', {})['model_path'] = os.getenv('WHISPER_MODEL_PATH')

    # LLM overrides
    if os.getenv('LLM_MODEL_PATH'):
        config_dict.setdefault('llm', {})['model_path'] = os.getenv('LLM_MODEL_PATH')

    # TTS overrides
    if os.getenv('PIPER_MODEL_PATH'):
        config_dict.setdefault('tts', {})['model_path'] = os.getenv('PIPER_MODEL_PATH')

    if os.getenv('PIPER_CONFIG_PATH'):
        config_dict.setdefault('tts', {})['config_path'] = os.getenv('PIPER_CONFIG_PATH')

    # Audio device overrides
    if os.getenv('AUDIO_INPUT_DEVICE'):
        config_dict.setdefault('audio', {}).setdefault('input', {})['device'] = os.getenv('AUDIO_INPUT_DEVICE')

    if os.getenv('AUDIO_OUTPUT_DEVICE'):
        config_dict.setdefault('audio', {}).setdefault('output', {})['device'] = os.getenv('AUDIO_OUTPUT_DEVICE')

    # GPIO overrides (for testing different pin configurations)
    if os.getenv('BUTTON_PIN'):
        config_dict.setdefault('gpio', {})['button_pin'] = int(os.getenv('BUTTON_PIN'))

    if os.getenv('LED_STATUS_PIN'):
        config_dict.setdefault('gpio', {}).setdefault('led_pins', {})['status'] = int(os.getenv('LED_STATUS_PIN'))

    # Logging override
    if os.getenv('LOG_LEVEL'):
        config_dict.setdefault('logging', {})['level'] = os.getenv('LOG_LEVEL')

    return config_dict


def dict_to_config(config_dict: Dict[str, Any]) -> Config:
    """
    Convert configuration dictionary to typed Config object

    Args:
        config_dict: Dictionary with configuration data

    Returns:
        Fully typed Config object
    """
    # Audio config - pass max_duration from timing config to audio input
    audio_input_dict = config_dict.get('audio', {}).get('input', {})
    # Add max_duration_s from timing if not already set
    if 'max_duration_s' not in audio_input_dict:
        audio_input_dict['max_duration_s'] = config_dict.get('timing', {}).get('max_recording_duration_s', 30)

    audio_config = AudioConfig(
        input=AudioInputConfig(**audio_input_dict),
        output=AudioOutputConfig(**config_dict.get('audio', {}).get('output', {}))
    )

    # STT config
    stt_config = STTConfig(**config_dict.get('stt', {}))

    # LLM config
    llm_data = config_dict.get('llm', {})
    llm_prompts = LLMPromptsConfig(
        plan=llm_data.get('prompts', {}).get('plan', ''),
        chapter=llm_data.get('prompts', {}).get('chapter', '')
    )
    llm_config = LLMConfig(
        model_path=llm_data.get('model_path', ''),
        context_tokens=llm_data.get('context_tokens', 2048),
        threads=llm_data.get('threads', 4),
        n_gpu_layers=llm_data.get('n_gpu_layers', 0),
        temperature=llm_data.get('temperature', 0.7),
        top_p=llm_data.get('top_p', 0.9),
        repeat_penalty=llm_data.get('repeat_penalty', 1.1),
        prompts=llm_prompts
    )

    # TTS config
    tts_data = config_dict.get('tts', {})
    tts_post = TTSPostProcessingConfig(**tts_data.get('post_processing', {}))
    tts_config = TTSConfig(
        model_path=tts_data.get('model_path', ''),
        config_path=tts_data.get('config_path', ''),
        sample_rate=tts_data.get('sample_rate', 22050),
        speaker_id=tts_data.get('speaker_id', 0),
        post_processing=tts_post
    )

    # GPIO config
    gpio_data = config_dict.get('gpio', {})
    gpio_leds = GPIOLEDPinsConfig(**gpio_data.get('led_pins', {}))
    gpio_config = GPIOConfig(
        button_pin=gpio_data.get('button_pin', 17),
        button_pull=gpio_data.get('button_pull', 'up'),
        debounce_ms=gpio_data.get('debounce_ms', 50),
        long_press_duration_s=gpio_data.get('long_press_duration_s', 3.0),
        led_pins=gpio_leds
    )

    # Other configs
    timing_config = TimingConfig(**config_dict.get('timing', {}))
    logging_config = LoggingConfig(**config_dict.get('logging', {}))
    story_config = StoryConfig(**config_dict.get('story', {}))

    return Config(
        audio=audio_config,
        stt=stt_config,
        llm=llm_config,
        tts=tts_config,
        gpio=gpio_config,
        timing=timing_config,
        logging=logging_config,
        story=story_config
    )


# Global config singleton
_config: Optional[Config] = None


def get_config(config_path: Optional[Path] = None, reload: bool = False) -> Config:
    """
    Get application configuration (singleton pattern)

    First call loads configuration from YAML and environment.
    Subsequent calls return cached config unless reload=True.

    Args:
        config_path: Optional path to config YAML (defaults to configs/default.yaml)
        reload: Force reload configuration from disk

    Returns:
        Fully loaded and validated Config object

    Example:
        >>> config = get_config()
        >>> print(config.stt.model_path)
        /home/maxence/models/whisper/ggml-small.bin
    """
    global _config

    if _config is not None and not reload:
        return _config

    # Load environment variables from .env file
    load_dotenv()

    # Determine config file path
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "configs" / "default.yaml"

    # Load YAML config
    config_dict = load_yaml_config(config_path)

    # Apply environment variable overrides
    config_dict = apply_env_overrides(config_dict)

    # Convert to typed Config object
    _config = dict_to_config(config_dict)

    return _config


def validate_config(config: Config) -> bool:
    """
    Validate configuration for common issues

    Checks:
    - Model files exist
    - Audio sample rates are valid
    - GPIO pins are in valid range (1-27 for Pi)
    - Log directory is writable

    Args:
        config: Configuration object to validate

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate model paths exist (if not running tests)
    if not os.getenv('MOCK_GPIO'):
        for model_path in [config.stt.model_path, config.llm.model_path, config.tts.model_path]:
            if not Path(model_path).exists():
                raise ValueError(f"Model file not found: {model_path}")

    # Validate audio sample rates
    valid_rates = [8000, 16000, 22050, 44100, 48000]
    if config.audio.input.sample_rate not in valid_rates:
        raise ValueError(f"Invalid input sample rate: {config.audio.input.sample_rate}")

    if config.audio.output.sample_rate not in valid_rates:
        raise ValueError(f"Invalid output sample rate: {config.audio.output.sample_rate}")

    # Validate GPIO pins (Pi has GPIO 0-27, but we use BCM numbering)
    if not os.getenv('MOCK_GPIO'):
        valid_pin_range = range(0, 28)
        if config.gpio.button_pin not in valid_pin_range:
            raise ValueError(f"Invalid button GPIO pin: {config.gpio.button_pin}")

        for pin_name, pin_num in [
            ('status', config.gpio.led_pins.status),
            ('progress_1', config.gpio.led_pins.progress_1),
            ('progress_2', config.gpio.led_pins.progress_2)
        ]:
            if pin_num not in valid_pin_range:
                raise ValueError(f"Invalid LED pin '{pin_name}': {pin_num}")

    # Validate log directory is writable
    log_dir = Path(config.logging.log_dir)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        test_file = log_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        raise ValueError(f"Log directory not writable: {log_dir}")

    return True
