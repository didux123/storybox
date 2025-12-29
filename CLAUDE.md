# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StoryBox IA** is an AI-powered interactive storytelling web application. The system combines:
1. **Voice input**: Record and transcribe story prompts (Gradium STT)
2. **Story generation**: Generate structured stories with multiple LLM providers (Celeste AI)
3. **Voice narration**: Natural French TTS narration (Gradium TTS)
4. **Web interface**: Complete Streamlit webapp for testing and demos

**Current Status**: V0.3 - Fully functional web app with STT, LLM, and TTS integration

**Future Direction**: Evolving toward API backend (FastAPI) with separated frontend, containerized with Docker

## Current Architecture (V0.3)

### Technology Stack
- **Frontend**: Streamlit (4-tab interface)
- **LLM**: Celeste AI library
  - Multi-provider support: Gemini, Claude, GPT-4o, Mistral, DeepSeek, xAI
  - Default: Gemini 1.5 Flash (fast, free tier available)
  - Async/await for performance
- **TTS**: Gradium API
  - 4 French voices pre-configured
  - Speed control (-4.0 to +4.0)
  - WAV output format
- **STT**: Gradium API
  - Support WAV, PCM, OPUS formats
  - Streaming audio chunks
  - Auto-format detection
- **Configuration**: YAML + JSON + .env
- **Logging**: Structured logging with python-json-logger

### File Structure
```
storybox/
├── app/                          # Core modules
│   ├── llm/
│   │   └── celeste_llm.py        # LLM wrapper (Celeste AI)
│   ├── tts/
│   │   ├── gradium_tts.py        # TTS via Gradium (active)
│   │   └── celeste_tts.py        # Deprecated
│   ├── stt/
│   │   └── gradium_stt.py        # STT via Gradium
│   └── utils/
│       ├── config.py             # Configuration management
│       └── logger.py             # Logging setup
│
├── webapp/                       # Streamlit interface
│   ├── streamlit_app.py          # Main app (4 tabs)
│   └── utils/
│       └── prompt_editor.py      # Prompt editing utilities
│
├── configs/                      # Configuration files
│   ├── default.yaml              # Default settings
│   ├── prompts.json              # LLM prompts
│   └── llm_config.json           # Model pricing/config
│
├── docs/                         # Documentation
│   ├── README.md                 # Documentation index
│   ├── MODULES.md                # Module documentation
│   ├── API.md                    # API reference
│   └── legacy/                   # Old Pi documentation
│
├── test/                         # Tests
│   ├── test_cloud_pipeline.py   # Integration test
│   └── legacy/                  # Old tests
│
├── .env                          # API keys (not versioned)
├── .env.example                  # Template
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Dev dependencies
├── Makefile                      # Convenience commands
├── README.md                     # Main documentation
├── TODO.md                       # Roadmap
└── QUICKSTART_WEBAPP.md          # Quick start guide
```

## Development Workflow

### Local Setup
```bash
# Clone and setup
git clone https://github.com/didux123/storybox.git
cd storybox

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_API_KEY (for Gemini)
# - GRADIUM_API_KEY (for TTS/STT)
# - OPENAI_API_KEY (optional, for GPT)
# - ANTHROPIC_API_KEY (optional, for Claude)
```

### Running the App
```bash
# Method 1: Makefile
make webapp

# Method 2: Direct command
streamlit run webapp/streamlit_app.py

# Method 3: Shell script
./run_webapp.sh
```

### Testing
```bash
# Run tests
pytest test/

# Integration test
python test/test_cloud_pipeline.py
```

## Key Modules

### CelesteLLM (`app/llm/celeste_llm.py`)
Wrapper for story generation via Celeste AI library.

**Key Methods:**
```python
async def generate_story_plan(theme: str, num_chapters: int = 10) -> StoryPlan
async def generate_chapter(plan: StoryPlan, chapter_num: int,
                           cumulative_context: str = "") -> str
```

**Usage:**
```python
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config
import asyncio

config = get_config()
llm = CelesteLLM(config.llm)
plan = asyncio.run(llm.generate_story_plan("Un robot et les émotions", 5))
```

### GradiumTTS (`app/tts/gradium_tts.py`)
Text-to-Speech via Gradium API.

**Key Methods:**
```python
async def generate_speech(text: str, voice_id: Optional[str] = None,
                         output_format: str = "wav",
                         padding_bonus: float = 0.0) -> Optional[bytes]
```

**French Voices:**
- Claire (zIGaffB0kKEBG_8u) - Default female voice
- + 3 other French voices
- Custom voice IDs supported

### GradiumSTT (`app/stt/gradium_stt.py`)
Speech-to-Text via Gradium API.

**Key Methods:**
```python
async def transcribe(audio_data: bytes, input_format: str = "wav") -> Optional[str]
async def transcribe_file(audio_path: str) -> Optional[str]
```

## Configuration

### Environment Variables (.env)
```env
# LLM Provider (choose one)
GOOGLE_API_KEY=your-google-api-key           # Gemini (recommended)
OPENAI_API_KEY=sk-your-openai-key           # GPT-4o
ANTHROPIC_API_KEY=sk-ant-your-key           # Claude

# TTS & STT
GRADIUM_API_KEY=your-gradium-api-key

# Model Selection
LLM_MODEL_PATH=gemini-1.5-flash             # Fast & free tier
# LLM_MODEL_PATH=gpt-4o-mini                # Economical
# LLM_MODEL_PATH=claude-3-5-sonnet-20241022 # Premium
# LLM_MODEL_PATH=mistral-large-2411         # Default for future API
```

### Prompts (configs/prompts.json)
Editable via Streamlit interface or directly in JSON file.

**Structure:**
```json
{
  "plan": {
    "system_prompt": "Instructions for story plan generation...",
    "user_template": "Variables: {theme}, {num_chapters}"
  },
  "chapter": {
    "system_prompt": "Instructions for chapter generation...",
    "user_template": "Variables: {chapter_num}, {chapter_title}, ..."
  }
}
```

## Roadmap

### V0.4 - API Backend & Docker (Next Priority)
- Separate backend (FastAPI) from frontend (Streamlit)
- REST API endpoint: `POST /api/v1/generate-story`
- JWT authentication
- Docker containerization (HIGH PRIORITY)
- Multi-architecture support (amd64, arm64)

### V0.5 - Streaming Generation
- WebSocket for real-time streaming
- Parallel generation: Audio(N) || Generate(N+1)
- 5x latency reduction (~10s vs ~50s perceived)

### V1.0 - CMS & User Management
- Admin dashboard (React/Vue.js)
- User management with API tokens
- Usage tracking and billing
- PostgreSQL database
- Stripe integration

See [TODO.md](TODO.md) for complete roadmap.

## Important Notes

### API Keys
- **Never commit** `.env` file - it's in .gitignore
- Use `.env.example` as template
- Get keys from:
  - Google AI Studio: https://makersuite.google.com/app/apikey
  - Gradium: https://gradium.ai/
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/

### Provider Costs
- **Gemini Flash**: Free tier available, then $0.075/$0.30 per 1M tokens
- **GPT-4o-mini**: $0.15/$0.60 per 1M tokens
- **Claude 3.5 Sonnet**: $3.00/$15.00 per 1M tokens
- **Mistral Large**: Competitive pricing

### Performance
Typical times with Gemini Flash:
- Plan (5 chapters): ~3-5s, ~500 tokens, ~$0.0001
- Chapter (200 words): ~5-8s, ~800 tokens, ~$0.0002
- Full story (5 chapters): ~40-50s, ~4000 tokens, ~$0.001

### Raspberry Pi Client
The Raspberry Pi will become a **client** that consumes the backend API (separate project).
All Pi-specific code (GPIO, audio input, state machine) has been removed from this repository.

## Reference Documents

- **[README.md](README.md)**: Main project documentation
- **[QUICKSTART_WEBAPP.md](QUICKSTART_WEBAPP.md)**: Quick start guide
- **[TODO.md](TODO.md)**: Detailed roadmap
- **[docs/MODULES.md](docs/MODULES.md)**: Module documentation
- **[docs/API.md](docs/API.md)**: API reference
- **[Expression_besoin.md](Expression_besoin.md)**: Requirements (French)

## Branches

- **main**: Current branch - Web API mode with Streamlit frontend
- **local_storybox**: Deprecated - Old Pi standalone mode (local AI)

## Migration History

- **V0.1**: Basic LLM integration
- **V0.2**: TTS integration (Celeste → Gradium)
- **V0.3**: STT integration + Complete Streamlit UI + Metrics
- **V0.4** (planned): API backend + Docker
- **V0.5** (planned): Streaming optimization
- **V1.0** (planned): CMS and user management

---

**Last updated**: December 29, 2024
**Version**: V0.3
**Next focus**: V0.4 - Docker containerization and API backend
