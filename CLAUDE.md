# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StoryBox IA** is an autonomous AI-powered storytelling device designed to run locally on Raspberry Pi 4B. The device uses a hold-to-talk button interface to:
1. Record voice input (French)
2. Transcribe the request using STT
3. Generate a 10-chapter story plan using a local LLM (3B quantized model)
4. Stream narration using TTS with LED status indicators

**Key Constraint**: Fully offline operation with no network dependencies in production.

## Architecture Components

### Core Modules (planned structure)
- **AudioIn**: Captures mono PCM 16kHz audio while button is held (no VAD)
- **STT**: French speech transcription via whisper.cpp (small/base models)
- **Planner**: Generates coherent 10-chapter story outline via LLM
- **StoryGen**: Chapter-by-chapter generation with cumulative context streaming
- **TTS**: Real-time narration via Piper (French voices)
- **State/LED**: State machine managing device states (Idle, Listening, Processing, Narrating, Error)
- **Control**: GPIO button handling (hold, short press for pause, 3s long press to stop)
- **Metrics/Logs**: Latency tracking, token/sec metrics, log rotation (≤50MB)

### Audio Pipeline
- **Input**: PCM mono 16kHz, 20-40ms frames
- **Output**: 22.05kHz/16-bit via Piper TTS
- **Storage**: Prioritize RAM, use ext4 if necessary (minimize SD card writes)

### Models (NOT versioned in Git)
Located in `~/models/` on the Pi:
- **LLM**: 3B GGUF Q4_K_M (e.g., Llama-3.2-3B-Instruct)
- **Whisper**: small/base FR models
- **Piper**: French voice models

## Development Workflow

### Local Development (Mac)
- Develop and test with simulated audio (WAV files)
- GPIO features are Pi-only, use mocks for local testing
- Same Python version and dependencies as Pi (see requirements.txt)

### Deployment to Raspberry Pi
1. **Initial deployment**: Use `scripts/deploy_init.sh` (rsync-based)
2. **Ongoing updates**: Git-based sync via `git pull` on Pi
3. **Models**: Deploy separately via USB/SSD/rsync (never via Git)

### Configuration
- **Environment**: `.env` file (excluded from Git) for secrets and paths
- **Config**: `configs/default.yaml` for model paths, GPIO pins, ALSA devices
- **SSH**: Connection config in `ssh_config.json` (template only, credentials in .env)

## Key Technical Details

### Latency Target
- ≤10s from button release to first audio output
- Visual pre-roll on LED to manage perceived latency

### Streaming & Backpressure
- StoryGen produces text by paragraphs
- TTS consumes continuously with auto-adjusted cadence
- Buffer management to prevent overruns

### Prompts
**Plan generation**:
```
Génère un plan de 10 chapitres cohérents sur [thème].
Chaque chapitre : Titre + 1 phrase de résumé.
Style : [optionnel]
```

**Chapter generation**:
```
Écris le chapitre n°, 150–300 mots, cohérent avec :
* Contexte cumulatif : [résumés précédents]
* Plan : [chapitres]
Ton narratif : [optionnel]
Paragraphes courts.
```

### Context Management
- Cumulative summaries: 2-3 sentences per chapter
- Target size: ~1-2k tokens to fit in context window

## Raspberry Pi Setup

### System Dependencies
```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y \
  python3 python3-venv python3-pip git cmake build-essential \
  libsndfile1 portaudio19-dev sox alsa-utils
```

### Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -c constraints.txt
```

### Systemd Service
Location: `/etc/systemd/system/storybox.service`
- User: Non-root user with audio/gpio supplementary groups
- Restart: `on-failure` with 2s delay
- Environment: Loaded from `.env` file

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable storybox
sudo systemctl start storybox
sudo systemctl status storybox
```

### Update Workflow
```bash
cd ~/projects/storybox
git fetch --all
git pull --rebase
sudo systemctl restart storybox.service
```

## Hardware Configuration

### Audio
- **Input**: USB microphone (class-compliant) OR I2S MEMS mic (INMP441)
- **Output**: USB audio + amplifier OR I2S DAC/AMP HAT
- Test input: `arecord -f S16_LE -r 16000 -c 1 test.wav`
- List devices: `arecord -l`

### GPIO (gpiozero or RPi.GPIO)
- Button with pull-up/pull-down and software debounce
- LEDs for state indication (recommended pins: 22, 23, 24)
- Default button pin: 17

### Storage Strategy
- microSD 64GB for OS and code (Phase 1)
- Optional: USB 3.2 SSD for models (Phase 2)
- Minimize writes: log rotation, RAM caching, disable/use zram for swap

## Testing & Validation

### Functional Tests
- Hold-to-talk → recording cycle
- Release → plan generation → streaming narration
- Pause/resume on short press
- LED state transitions
- Long press (≥3s) clean shutdown

### Performance Metrics
- Measure: button release → first audio latency
- Log: tokens/sec, model load times, audio/GPIO errors
- Target: 30 consecutive cycles without crash

### Quality Checks
- Chapter continuity validation
- Prompt tuning based on narrative coherence
- USB audio reconnection handling

## Roadmap

- **v0**: Basic hold-to-talk, STT → Plan → StoryGen → TTS pipeline
- **v1**: Streaming refinement, LED pre-roll, pause/resume, log rotation, metrics
- **v2**: SSD for models, thermal/thread tuning
- **v3**: Optional Docker arm64 image (mapping `/dev/snd`, `/dev/gpiomem`)

## Important Notes

- **Never commit models or audio data** - only code and configuration
- **Security**: Use SSH keys (ed25519), no password auth, `.env` for secrets
- **SD card longevity**: Rotate logs, limit disk writes, consider SSD for models
- **TTS quality**: Test multiple Piper FR voices, apply light post-processing (noise gate, compression)
- **Offline operation**: All inference local, no network dependencies in production
- **Thermal management**: Ensure adequate cooling (heatsink/fan) for sustained LLM inference

## Reference Documents

- `Expression_besoin.md`: Complete functional and technical requirements (French)
- `workflow.md`: Detailed deployment workflow and systemd configuration
- `ssh_config.json`: SSH connection template (credentials in .env)
- `docs/HARDWARE.md`: Complete hardware setup guide with wiring diagrams and component selection
- `docs/MODULES.md`: API documentation for all implemented modules
- `docs/RASPBERRY_PI_SETUP.md`: Software installation and deployment guide for Pi
- `docs/MAC_DEVELOPMENT.md`: Local development setup with mocks
