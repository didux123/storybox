# Mac Development Guide

Guide for developing and testing StoryBox IA locally on Mac before deploying to Raspberry Pi.

## Overview

Develop on Mac for faster iteration, then deploy to Pi for real-world testing with GPIO and audio hardware.

**Mac Development:**
- ✅ Python code development
- ✅ STT/LLM/TTS testing with models
- ✅ Unit tests with mocked GPIO
- ✅ Audio simulation with WAV files

**Pi Required For:**
- ❌ Real GPIO button and LED control
- ❌ Real-time audio capture from microphone
- ❌ Performance benchmarking (ARM architecture)

## Initial Setup

### 1. Clone Repository

```bash
cd ~/Documents/PYTHON
git clone https://github.com/didux123/storybox.git
cd storybox
```

### 2. Install Homebrew Dependencies

```bash
# Install cmake (for compiling whisper.cpp and llama.cpp)
brew install cmake

# Optional: Install audio tools for testing
brew install sox portaudio
```

### 3. Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt
```

**Note:** GPIO libraries (gpiozero, RPi.GPIO) will fail on Mac - this is expected. They're only needed on Pi.

### 4. Download Models

Models are in `models/` directory (already downloaded in your case):

```
models/
├── llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf  (1.9GB)
├── whisper/ggml-small.bin                  (465MB)
└── piper/
    ├── fr_FR-siwis-medium.onnx            (61MB)
    └── fr_FR-siwis-medium.onnx.json       (5KB)
```

### 5. Compile Toolchains (Mac)

**These binaries are Mac-only and NOT needed on Pi. The Pi will compile its own ARM64 binaries.**

```bash
# Whisper.cpp
cd /tmp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build --config Release
# Binary: /tmp/whisper.cpp/build/bin/whisper-cli

# Llama.cpp
cd /tmp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build --config Release
# Binaries: /tmp/llama.cpp/build/bin/llama-cli

# Piper TTS (installed via pip)
pip install piper-tts
# Available as: piper command
```

**Duration:** ~5-10 minutes on M1/M2 Mac

## Configuration for Mac

### 1. Create .env File

```bash
cp .env.example .env
nano .env
```

Update for Mac development:

```bash
# Mock GPIO for Mac development
MOCK_GPIO=true

# Model paths (Mac)
WHISPER_MODEL_PATH=/Users/maxence/Documents/PYTHON/storybox/models/whisper/ggml-small.bin
LLM_MODEL_PATH=/Users/maxence/Documents/PYTHON/storybox/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf
PIPER_MODEL_PATH=/Users/maxence/Documents/PYTHON/storybox/models/piper/fr_FR-siwis-medium.onnx

# Audio devices (Mac - use default or specific device)
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default

# Logging
LOG_LEVEL=DEBUG
```

### 2. Create Mac-Specific Config

For testing, you may want to override `configs/default.yaml`:

```bash
cp configs/default.yaml configs/mac.yaml
```

Update paths in `configs/mac.yaml` to point to Mac model locations.

## Testing Individual Components

### 1. Test Whisper STT

```bash
# Create a test audio file
say -v Thomas "Bonjour, raconte moi une histoire sur les pirates" -o test_input.aiff
ffmpeg -i test_input.aiff -ar 16000 -ac 1 test_input.wav

# Test with whisper.cpp
/tmp/whisper.cpp/build/bin/whisper-cli \
  -m models/whisper/ggml-small.bin \
  -l fr \
  test_input.wav
```

### 2. Test Llama.cpp LLM

```bash
/tmp/llama.cpp/build/bin/llama-cli \
  -m models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -n 100 \
  -p "Génère un plan de 3 chapitres pour une histoire sur les pirates."
```

### 3. Test Piper TTS

```bash
source .venv/bin/activate

echo "Bonjour, ceci est un test de synthèse vocale." | \
  piper -m models/piper/fr_FR-siwis-medium.onnx \
  -f test_output.wav

# Play on Mac
afplay test_output.wav
```

## Running Unit Tests

```bash
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_stt.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Mock GPIO for Mac

Since Mac doesn't have GPIO, we'll use mocks:

```python
# In app/gpio/button.py (example)
try:
    from gpiozero import Button
except ImportError:
    # Mac fallback: mock Button
    class Button:
        def __init__(self, pin, **kwargs):
            print(f"[MOCK GPIO] Button on pin {pin}")

        def when_pressed(self, callback):
            print("[MOCK GPIO] Button pressed handler registered")

        # ... other mock methods
```

Or use environment variable:

```python
import os
if os.getenv('MOCK_GPIO') == 'true':
    # Use mock GPIO
else:
    # Use real GPIO
```

## Audio Simulation

For testing without live microphone:

```python
# app/audio/input.py (example)
def record_audio(duration_s=5):
    if os.getenv('MOCK_GPIO') == 'true':
        # Load pre-recorded WAV file for testing
        return load_test_audio('test_input.wav')
    else:
        # Real recording from microphone
        return record_from_mic(duration_s)
```

## Development Workflow

### 1. Write Code

```bash
# Activate venv
source .venv/bin/activate

# Edit code
code .  # or your editor

# Run locally
python -m app.main
```

### 2. Test Locally

```bash
# Unit tests
pytest tests/

# Manual testing with simulated audio
python -m app.main --mock
```

### 3. Commit Changes

```bash
git add .
git commit -m "feat: implement STT wrapper"
git push origin main
```

### 4. Deploy to Pi

```bash
# Deploy code
./scripts/deploy_init.sh

# SSH to Pi and test
ssh -i ~/.ssh/id_ed25519_storybox maxence@192.168.68.120
cd ~/projects/storybox
git pull --rebase
sudo systemctl restart storybox
sudo journalctl -u storybox -f
```

## Performance Notes

**Mac vs Pi Performance:**

| Operation | Mac M1/M2 | Pi 4B 8GB |
|-----------|-----------|-----------|
| Whisper small | ~2-3x realtime | ~0.5x realtime |
| Llama 3B Q4_K_M | ~20-30 tok/s | ~3-5 tok/s |
| Piper TTS | ~5-10x realtime | ~2x realtime |

Mac will be **significantly faster** for iteration, but final latency testing must be on Pi.

## Debugging

### 1. Verbose Logging

```bash
export LOG_LEVEL=DEBUG
python -m app.main
```

### 2. Profile Performance

```python
import time

start = time.time()
# ... your code
print(f"Elapsed: {time.time() - start:.2f}s")
```

### 3. Memory Usage

```bash
# Install memory profiler
pip install memory-profiler

# Profile script
python -m memory_profiler app/main.py
```

## Hot Reload for Development

Use `watchdog` for auto-reload on file changes:

```bash
pip install watchdog

# Create dev script
watchmedo auto-restart \
  --patterns="*.py" \
  --recursive \
  -- python -m app.main
```

## VS Code Setup

Recommended `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/.venv": true,
    "**/models": true
  }
}
```

## Common Issues

### 1. ImportError: gpiozero

**Expected on Mac.** Use `MOCK_GPIO=true` in `.env`.

### 2. Model Loading Slow

Normal on first run. Models are ~2.4GB and need to load into RAM.

### 3. Audio Device Not Found

On Mac, use `default` or check available devices:

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## Next Steps

Once local testing is complete:
1. Deploy to Pi: `./scripts/deploy_init.sh`
2. SSH to Pi and run: `bash scripts/install_pi.sh`
3. Test end-to-end on Pi with real GPIO and audio

See `docs/RASPBERRY_PI_SETUP.md` for Pi-specific setup.
