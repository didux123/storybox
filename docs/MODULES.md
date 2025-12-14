# StoryBox IA - Modules Documentation

Guide technique des modules Python de StoryBox IA.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Orchestrator                        │
│                      (app/main.py)                          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──> State Machine (app/state/)
               │     ├─ Idle → Listening → Processing → Narrating
               │     └─ Error handling & recovery
               │
               ├──> GPIO Control (app/gpio/)
               │     ├─ Button (hold-to-talk, pause, shutdown)
               │     └─ LED (status, progress indicators)
               │
               ├──> Audio Pipeline
               │     ├─ AudioIn: Microphone capture (app/audio/)
               │     ├─ STT: Whisper transcription (app/stt/)
               │     ├─ LLM: Story generation (app/llm/)
               │     └─ TTS: Piper narration (app/tts/)
               │
               └──> Utils (app/utils/)
                     ├─ Config: YAML + env loader
                     ├─ Logger: Structured logging + metrics
                     └─ Metrics: Performance tracking
```

## Module Index

### Core Modules

1. **[Config](#config-apputils configpy)** - Configuration management
2. **[Logger](#logger-app utils loggerpy)** - Logging & metrics
3. **[TTS](#tts-apptts pipera_ttspy)** - Text-to-Speech (Piper)
4. **[STT](#stt-appstt whisper_sttpy)** - Speech-to-Text (Whisper)
5. **[LLM](#llm-appllm llama_llmpy)** - Language Model (Llama)

### Integration Modules (To Be Implemented)

6. **AudioIn** - Audio capture from microphone
7. **Planner** - Story plan generation orchestrator
8. **StoryGen** - Chapter-by-chapter generation with context
9. **GPIO** - Button & LED hardware control
10. **State** - State machine for system coordination
11. **Main** - Main application orchestrator

---

## Config (app/utils/config.py)

### Purpose

Centralized configuration management with:
- YAML file loading (configs/default.yaml)
- Environment variable overrides (.env)
- Type-safe configuration objects
- Validation

### Usage

```python
from app.utils.config import get_config

# Load configuration (singleton)
config = get_config()

# Access settings
model_path = config.stt.model_path
sample_rate = config.audio.input.sample_rate
button_pin = config.gpio.button_pin

# Force reload (for testing)
config = get_config(reload=True)
```

### Configuration Structure

```python
Config
├── audio: AudioConfig
│   ├── input: AudioInputConfig (device, sample_rate, channels)
│   └── output: AudioOutputConfig (device, sample_rate)
├── stt: STTConfig (model_path, language, threads)
├── llm: LLMConfig (model_path, context_tokens, temperature, prompts)
├── tts: TTSConfig (model_path, sample_rate, post_processing)
├── gpio: GPIOConfig (button_pin, led_pins, debounce_ms)
├── timing: TimingConfig (pre_roll_led_ms, max_recording_duration_s)
├── logging: LoggingConfig (level, log_dir, max_log_size_mb)
└── story: StoryConfig (num_chapters, chapter_min_words)
```

### Environment Overrides

```bash
# In .env file
WHISPER_MODEL_PATH=/path/to/model.bin
LLM_MODEL_PATH=/path/to/model.gguf
AUDIO_INPUT_DEVICE=hw:1,0
LOG_LEVEL=DEBUG
```

### Validation

```python
from app.utils.config import validate_config

config = get_config()
validate_config(config)  # Raises ValueError if invalid
```

---

## Logger (app/utils/logger.py)

### Purpose

Structured logging with:
- File rotation (prevents SD card overflow)
- JSON formatting (for log aggregation)
- Performance metrics tracking
- Timing context managers

### Setup

```python
from app.utils.logger import setup_logging

# Initialize logging system
setup_logging(
    log_dir="logs",
    log_level="INFO",
    max_bytes=50*1024*1024,  # 50MB
    backup_count=3,
    console_output=True
)
```

### Basic Logging

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Processing started")
logger.warning("Low memory detected")
logger.error("Failed to load model", exc_info=True)

# With extra fields (for JSON logging)
logger.info("Transcription complete", extra={
    'duration_ms': 1234,
    'text_length': 42
})
```

### Metrics Tracking

```python
from app.utils.logger import log_metric, get_metrics_summary

# Log performance metrics
log_metric("stt_latency_ms", 1234)
log_metric("llm_tokens_per_second", 4.5)

# Get summary
summary = get_metrics_summary()
print(summary['metrics']['stt_latency_ms'])  # {'min': ..., 'max': ..., 'avg': ...}
```

### Timing Context

```python
from app.utils.logger import TimingContext

# Automatic timing and logging
with TimingContext("stt_transcription", log_metric=True):
    text = whisper.transcribe(audio)
    # Automatically logs "stt_transcription_ms" metric
```

### System Info Logging

```python
from app.utils.logger import log_system_info

# Log system details (Python version, CPU, memory, temperature)
log_system_info()
```

---

## TTS (app/tts/piper_tts.py)

### Purpose

Text-to-Speech using Piper neural TTS:
- High-quality French voice synthesis
- Streaming generation (sentence by sentence)
- Audio post-processing
- Memory-efficient for Pi

### Initialization

```python
from app.tts.piper_tts import PiperTTS

tts = PiperTTS(config.tts)
```

### Basic Synthesis

```python
# Generate speech from text
audio_bytes = tts.synthesize("Bonjour, voici une histoire.")

# Get audio duration
duration = tts.get_audio_duration(audio_bytes)
print(f"Audio: {duration:.1f}s")

# Save to file
from pathlib import Path
tts.save_audio(audio_bytes, Path("output.wav"))
```

### Streaming Synthesis

For long texts, generate and play incrementally:

```python
# Generate sentence by sentence
for audio_chunk in tts.synthesize_streaming(long_story, sentence_split=True):
    # audio_chunk is AudioChunk(data, sample_rate, channels)
    play_audio(audio_chunk)  # Play while generating next sentence
```

### Post-Processing

```python
import numpy as np

# Process audio (noise gate, compression, normalization)
raw_audio = np.frombuffer(audio_bytes, dtype=np.int16)
processed_audio = tts.post_process_audio(raw_audio)
```

### Testing

```bash
# Run module test
python -m app.tts.piper_tts

# Output:
# - Generates 3 test audio files
# - Reports synthesis time and file sizes
```

---

## STT (app/stt/whisper_stt.py)

### Purpose

Speech-to-Text using whisper.cpp:
- French language transcription
- Multi-threading for Pi optimization
- Audio preprocessing
- Benchmarking tools

### Initialization

```python
from app.stt.whisper_stt import WhisperSTT

stt = WhisperSTT(config.stt)
```

### Transcribe from File

```python
from pathlib import Path

# Transcribe WAV file
text = stt.transcribe_file(Path("recording.wav"))
print(f"Transcribed: {text}")
```

### Transcribe from Array

```python
import numpy as np

# From numpy array (e.g., live recording)
audio_data = np.array([...], dtype=np.int16)  # 16kHz mono
text = stt.transcribe_array(audio_data, sample_rate=16000)
```

### Audio Preprocessing

```python
# Normalize and reduce noise
processed = stt.preprocess_audio(
    audio_data,
    normalize=True,
    noise_reduce=True
)

text = stt.transcribe_array(processed)
```

### Benchmarking

```python
# Measure performance
results = stt.benchmark(Path("test.wav"))

print(f"Audio duration: {results['audio_duration_s']:.2f}s")
print(f"Transcription time: {results['transcription_time_s']:.2f}s")
print(f"RTF: {results['rtf']:.2f}")  # Real-Time Factor (<1.0 is real-time)
print(f"Text: {results['transcribed_text']}")
```

### Testing

```bash
# Run module test (requires test audio files)
python -m app.stt.whisper_stt

# First generate test audio:
python test/scripts/test_tts.py
```

---

## LLM (app/llm/llama_llm.py)

### Purpose

Text generation using llama.cpp:
- Story plan generation (JSON output)
- Chapter-by-chapter generation
- Context management
- Streaming support (experimental)

### Initialization

```python
from app.llm.llama_llm import LlamaLLM

llm = LlamaLLM(config.llm)
```

### Basic Generation

```python
# Simple text generation
text = llm.generate(
    prompt="Il était une fois",
    max_tokens=200,
    temperature=0.7
)
print(text)
```

### Story Plan Generation

```python
# Generate 10-chapter story plan
plan = llm.generate_story_plan(
    theme="des pirates qui cherchent un trésor",
    num_chapters=10
)

if plan:
    for chapter in plan.chapters:
        print(f"{chapter['number']}. {chapter['title']}")
        print(f"   {chapter['summary']}")
```

### Chapter Generation

```python
# Generate individual chapter
chapter_text = llm.generate_chapter(
    plan=plan,
    chapter_num=1,
    cumulative_context="",  # Summary of previous chapters
    min_words=150,
    max_words=300
)

print(chapter_text)
```

### Multi-Chapter Generation with Context

```python
cumulative_context = ""

for i in range(1, len(plan.chapters) + 1):
    # Generate chapter
    chapter = llm.generate_chapter(
        plan=plan,
        chapter_num=i,
        cumulative_context=cumulative_context
    )

    # Generate summary for next chapter's context
    summary = llm.generate(
        f"Résume ce chapitre en 2-3 phrases :\n{chapter}",
        max_tokens=100
    )

    # Append to cumulative context
    cumulative_context += f"\nChapitre {i}: {summary}"

    # Narrate chapter
    audio = tts.synthesize(chapter)
    play_audio(audio)
```

### StoryPlan Object

```python
from app.llm.llama_llm import StoryPlan

# Create manually
plan = StoryPlan(
    theme="pirates",
    chapters=[
        {"number": 1, "title": "Le départ", "summary": "Lucas trouve une carte."},
        ...
    ]
)

# Serialize
plan_dict = plan.to_dict()

# Deserialize
plan = StoryPlan.from_dict(plan_dict)
```

### Testing

```bash
# Run module test
python -m app.llm.llama_llm

# Output:
# - Generates 5-chapter story plan
# - Generates first chapter
# - Reports timing and word counts
```

---

## Integration Example

Complete pipeline from voice to narration:

```python
from app.utils.config import get_config
from app.utils.logger import setup_logging, get_logger
from app.stt.whisper_stt import WhisperSTT
from app.llm.llama_llm import LlamaLLM
from app.tts.piper_tts import PiperTTS
from pathlib import Path

# Setup
config = get_config()
setup_logging(
    log_dir=config.logging.log_dir,
    log_level=config.logging.level
)
logger = get_logger(__name__)

# Initialize modules
stt = WhisperSTT(config.stt)
llm = LlamaLLM(config.llm)
tts = PiperTTS(config.tts)

# 1. Transcribe user request
logger.info("=== Step 1: Transcribe ===")
user_request = stt.transcribe_file(Path("user_recording.wav"))
logger.info(f"User said: {user_request}")

# 2. Generate story plan
logger.info("=== Step 2: Generate Plan ===")
plan = llm.generate_story_plan(user_request, num_chapters=10)
logger.info(f"Generated plan with {len(plan.chapters)} chapters")

# 3. Generate and narrate chapters
cumulative_context = ""

for i in range(1, len(plan.chapters) + 1):
    logger.info(f"=== Step 3.{i}: Generate Chapter {i} ===")

    # Generate chapter text
    chapter_text = llm.generate_chapter(
        plan=plan,
        chapter_num=i,
        cumulative_context=cumulative_context
    )

    # Narrate chapter
    logger.info(f"=== Step 4.{i}: Narrate Chapter {i} ===")
    audio = tts.synthesize(chapter_text)

    if audio:
        # Save or play audio
        output_path = Path(f"chapter_{i}.wav")
        tts.save_audio(audio, output_path)
        logger.info(f"Saved: {output_path}")

    # Update context for next chapter
    summary = llm.generate(
        f"Résume ce chapitre en 2 phrases :\n{chapter_text}",
        max_tokens=100
    )
    cumulative_context += f"\nChapitre {i}: {summary}"

logger.info("=== Complete! ===")
```

---

## Performance Optimization

### On Raspberry Pi

**Memory Management:**
```python
import gc

# After each chapter, force garbage collection
gc.collect()
```

**Threading:**
```python
# Adjust threads based on Pi model
config.stt.threads = 4  # Pi 4B: 4 cores
config.llm.threads = 4
```

**Model Selection:**
```python
# For 4GB Pi, use smaller models
config.stt.model_path = "~/models/whisper/ggml-base.bin"  # Instead of small
config.llm.context_tokens = 1536  # Instead of 2048
```

### Monitoring

```python
from app.utils.logger import get_metrics_summary, log_system_info

# Log system state
log_system_info()

# Check metrics
summary = get_metrics_summary()
print(f"Average STT latency: {summary['metrics']['stt_transcription_ms']['avg']:.0f}ms")
print(f"Average LLM speed: {summary['metrics']['llm_tokens_per_second']['avg']:.1f} tok/s")
```

---

## Error Handling

All modules raise appropriate exceptions and log errors:

```python
try:
    plan = llm.generate_story_plan(theme)
    if not plan:
        logger.error("Plan generation returned None")
        # Fallback or retry logic
except FileNotFoundError as e:
    logger.error(f"Model not found: {e}")
    # Handle missing model
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # General error handling
```

---

## Next Steps

See the following modules (to be implemented):

1. **app/audio/input.py** - Microphone capture with hold-to-talk
2. **app/gpio/button.py** - GPIO button handler
3. **app/gpio/led.py** - LED status indicators
4. **app/state/machine.py** - State machine coordination
5. **app/main.py** - Main orchestrator bringing it all together

For full system integration, see `docs/RASPBERRY_PI_SETUP.md`.
