# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StoryBox IA** is an AI-powered interactive storytelling device for Raspberry Pi 4B. The device uses a hold-to-talk button interface to:
1. Record voice input (French)
2. Transcribe the request using cloud STT
3. Generate story plan and chapters using cloud LLM (Celeste AI)
4. Stream narration using TTS (coming soon with Celeste TTS)

**Key Feature**: Cloud-based AI with multi-provider support via Celeste AI library.

## Current Architecture (Cloud API - main branch)

### Core Stack
- **STT**: Google Speech Recognition (temporary solution)
  - Free, fast (~2s transcription)
  - Will migrate to Celeste STT when available
- **LLM**: Celeste AI unified library
  - Supports OpenAI, Anthropic, Google, Mistral, xAI, DeepSeek, Groq
  - Zero lock-in: switch providers by changing model ID
  - Async/await for better performance
- **TTS**: Placeholder for Celeste TTS via Gradio (coming soon)
- **GPIO**: Button and LED control (Raspberry Pi only)
- **State Machine**: Manages device states and pipeline flow

### File Structure (Cloud Mode)
```
app/
├── llm/
│   ├── celeste_llm.py       # Cloud LLM via Celeste
│   └── __init__.py
├── stt/
│   ├── system_dictation.py  # Google Speech Recognition
│   └── __init__.py
├── tts/                      # TTS module (to be implemented)
│   └── __init__.py
├── gpio/                     # GPIO handlers (keep for Pi)
│   ├── button.py
│   ├── led.py
│   └── __init__.py
├── state/                    # State machine (keep)
│   ├── machine.py
│   └── __init__.py
├── utils/                    # Config, logging (keep)
│   ├── config.py
│   ├── logger.py
│   └── __init__.py
└── main.py                   # Main orchestrator

test/
└── test_cloud_pipeline.py    # Interactive cloud test

docs/
└── legacy/                   # Local AI docs (deprecated)
    ├── README.md
    ├── HARDWARE.md
    ├── MAC_DEVELOPMENT.md
    ├── MODULES.md
    └── RASPBERRY_PI_SETUP.md
```

## Development Workflow

### Local Development (Mac/Linux)
1. Install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure API keys in `.env`:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   LLM_MODEL_PATH=gpt-4o-mini
   ```

3. Test the pipeline:
   ```bash
   python test/test_cloud_pipeline.py
   ```

### Deployment to Raspberry Pi
1. Ensure internet connectivity on Pi (required for cloud APIs)
2. Clone repo and install dependencies
3. Configure `.env` with API keys
4. Run tests to verify functionality
5. Set up systemd service for production (optional)

### Configuration
- **`.env`**: API keys, model selection, paths (NOT versioned in Git)
- **`configs/default.yaml`**: GPIO pins, audio devices, system settings
- Environment variables override YAML settings

## Key Technical Details

### Celeste LLM Integration
The `celeste_llm.py` module wraps the Celeste AI library:
- Supports async/await for concurrent operations
- Generates story plans (10 chapters) as structured JSON
- Generates individual chapters with cumulative context
- Model switching via config (no code changes needed)

Example usage:
```python
from app.llm.celeste_llm import CelesteLLM

llm = CelesteLLM(config.llm)
plan = await llm.generate_story_plan("pirates et trésor", num_chapters=10)
chapter1 = await llm.generate_chapter(plan, chapter_num=1)
```

### System Dictation (Temporary STT)
Uses `SpeechRecognition` library with Google Speech API:
- Free, no API key needed (uses public endpoint)
- Fast transcription (~2s)
- Requires internet connection
- Will be replaced by Celeste STT when available

### Prompts
**Plan generation**:
```
Génère un plan de {num_chapters} chapitres cohérents sur le thème suivant : {theme}.

Chaque chapitre doit contenir :
- Un titre court et accrocheur
- Un résumé en 1 phrase

Réponds UNIQUEMENT au format JSON suivant :
{
  "chapters": [
    {"number": 1, "title": "...", "summary": "..."},
    ...
  ]
}
```

**Chapter generation**:
```
Écris le chapitre {chapter_num} intitulé "{chapter_title}".

Contexte cumulatif des chapitres précédents :
{cumulative_context}

Plan global de l'histoire :
{story_plan}

Consignes :
- {min_words} à {max_words} mots
- Paragraphes courts pour la lecture à voix haute
- Cohérent avec le contexte et le plan
- Ton narratif adapté à un jeune public

Écris UNIQUEMENT le contenu du chapitre, sans répéter le titre.
```

### Provider Switching
Change provider by updating `.env`:
```env
# OpenAI
LLM_MODEL_PATH=gpt-4o-mini

# Anthropic
LLM_MODEL_PATH=claude-3-5-sonnet-20241022

# Google
LLM_MODEL_PATH=gemini-2.0-flash

# Mistral
LLM_MODEL_PATH=mistral-large-2411
```

No code changes required!

## Testing

### Quick Test (Development)
```bash
python test/test_cloud_pipeline.py
```

This tests:
1. Audio recording (5 seconds)
2. Transcription via Google Speech
3. Story plan generation
4. First chapter generation
5. Display results

### Integration Testing
- GPIO: Use actual Pi hardware or mocks (set `MOCK_GPIO=true`)
- Audio: Test with real microphone and speaker
- APIs: Ensure internet connectivity and valid API keys

## Important Notes

- **Never commit API keys** - use `.env` file (excluded from Git)
- **Internet required**: Cloud APIs need network connectivity
- **API costs**: Monitor usage (GPT-4o-mini is cheap, ~$0.15/1M input tokens)
- **Local mode**: Available in `local_storybox` branch (see `docs/legacy/`)
- **TTS pending**: Waiting for Celeste TTS release via Gradio

## Reference Documents

- **README.md**: Main project documentation (cloud mode)
- **QUICKSTART.md**: Quick start guide for cloud setup
- **Expression_besoin.md**: Complete functional requirements (French)
- **docs/legacy/**: Local AI mode documentation (deprecated)

## Branches

- **main**: Cloud API mode (current)
- **local_storybox**: Local AI mode (Whisper/TinyLlama/Piper)

To switch to local mode:
```bash
git checkout local_storybox
```

## Migration Notes

The project transitioned from local AI (Whisper/TinyLlama/Piper) to cloud APIs for:
- **Performance**: ~10s total (vs ~33s local)
- **Quality**: Better models (GPT-4, Claude, Gemini vs quantized 1B model)
- **Flexibility**: Easy provider switching
- **Development**: Simpler testing and iteration

Local implementation is preserved in `local_storybox` branch and `docs/legacy/` for reference.
