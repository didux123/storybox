# Legacy Documentation (Local AI Mode)

This directory contains documentation for the **local AI mode** implementation of StoryBox.

## ⚠️ Note

The local AI mode has been **moved to the `local_storybox` branch** and is no longer the default implementation.

The main branch now uses **cloud APIs** for better performance and flexibility.

## What's Here

This legacy documentation covers:

- **HARDWARE.md**: Hardware setup guide for Raspberry Pi with local models
- **MAC_DEVELOPMENT.md**: Local development setup on macOS
- **MODULES.md**: API documentation for local AI modules
- **RASPBERRY_PI_SETUP.md**: Complete Pi setup for offline operation
- **workflow.md**: Deployment workflow for local models

## Local AI Architecture (Deprecated)

The local mode used:
- **STT**: Whisper.cpp (small/base models) - ~18s latency
- **LLM**: TinyLlama 1.1B Q4_K_M via llama.cpp - ~12s latency
- **TTS**: Piper French voice (siwis-medium) - ~3s latency
- **Total**: ~33s end-to-end latency

## Why We Moved to Cloud APIs

Performance limitations:
- Total latency too high for interactive use (~33s)
- Model quality limited by quantization (4-bit models)
- Complex setup and deployment process
- Difficult to test and iterate

Cloud benefits:
- Much faster (~10s total)
- Better model quality (GPT-4, Claude, Gemini)
- Easier deployment and updates
- Flexible provider switching

## Access Local Mode

To use or reference the local AI implementation:

```bash
git checkout local_storybox
```

All local AI code, models configuration, and complete setup is preserved in that branch.

## Current Architecture (Cloud)

See the main README.md for cloud API setup with:
- **STT**: Google Speech Recognition (temporary) → Celeste STT (coming soon)
- **LLM**: Celeste AI (OpenAI, Anthropic, Gemini, etc.)
- **TTS**: Celeste TTS via Gradio (coming soon)

For quick start with cloud APIs, see `QUICKSTART.md` in the root directory.
