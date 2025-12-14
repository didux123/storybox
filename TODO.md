# StoryBox IA - TODO List

## V0: MVP Pipeline (Hold-to-talk → STT → Plan → StoryGen → TTS)

### Infrastructure & Setup
- [ ] 1. Create project structure (app/, scripts/, tests/)
- [ ] 2. Create requirements.txt with dependencies
- [ ] 3. Build/install whisper.cpp for STT
- [ ] 4. Build/install llama.cpp for LLM inference
- [ ] 5. Install Piper TTS

### Core Modules Implementation
- [ ] 6. Implement audio input module (AudioIn)
  - Capture PCM mono 16kHz
  - Hold-to-talk buffer management
  - No VAD needed
- [ ] 7. Implement STT wrapper for whisper.cpp
  - Python binding to whisper.cpp
  - French language support
  - Audio normalization
- [ ] 8. Implement LLM wrapper for llama.cpp
  - Python binding to llama.cpp
  - Prompt template management
  - Token streaming support
- [ ] 9. Implement Planner module (10-chapter plan generation)
  - Use LLM to generate story outline
  - JSON parsing of chapter structure
  - Theme extraction from user input
- [ ] 10. Implement StoryGen module (chapter-by-chapter generation)
  - Cumulative context management (2-3 sentences per chapter)
  - Paragraph-level streaming (~50 tokens)
  - Memory optimization (~1-2k tokens total context)
- [ ] 11. Implement TTS wrapper for Piper
  - Python binding to Piper
  - Streaming audio generation
  - Post-processing (noise gate, compressor)

### Control & State Management
- [ ] 12. Implement GPIO button handler (hold-to-talk)
  - gpiozero or RPi.GPIO integration
  - Debounce logic (50ms)
  - Short press (pause/resume) detection
  - Long press (≥3s shutdown) detection
- [ ] 13. Implement basic LED state indicators
  - State-based LED patterns
  - Pre-roll visual feedback (500ms)
  - Progress indication during narration
- [ ] 14. Implement state machine (Idle/Listening/Processing/Narrating/Error)
  - State transitions
  - Event handling
  - Error recovery
- [ ] 15. Implement main orchestrator connecting all modules
  - Pipeline coordination
  - Async/threading for concurrent operations
  - Graceful shutdown

### Configuration & Observability
- [ ] 16. Add configuration loader (YAML)
  - Load configs/default.yaml
  - Environment variable override support
  - Validation
- [ ] 17. Add basic logging and metrics
  - Structured logging (rotation ≤50MB)
  - Latency tracking (release → first audio)
  - Tokens/sec metrics
  - Model load time tracking

### Testing & Deployment
- [ ] 18. Test locally on Mac (simulated audio)
  - Unit tests for each module
  - Integration tests with mock GPIO
  - WAV file playback for TTS verification
- [ ] 19. Deploy to Raspberry Pi
  - Use scripts/deploy_init.sh
  - Install system dependencies
  - Setup systemd service
- [ ] 20. Test end-to-end on Pi (real GPIO and audio)
  - 30 consecutive cycles without crash
  - Latency measurement (target ≤10s)
  - USB audio reconnection handling
  - Narrative continuity validation

---

## V1: Polish & Production Readiness (Post-V0)

### Enhancements
- [ ] Streaming TTS refinement (tighter coupling with LLM)
- [ ] Advanced LED patterns (token-sync animation)
- [ ] Enhanced pause/resume functionality
- [ ] Log rotation automation
- [ ] Performance metrics dashboard
- [ ] Prompt tuning based on narrative quality

### Robustness
- [ ] Comprehensive error handling
- [ ] Watchdog timer
- [ ] Auto-recovery from failures
- [ ] Better thermal management

---

## V2: Performance Optimization (Future)

- [ ] SSD for models (USB 3.2)
- [ ] Thread/CPU affinity tuning
- [ ] Thermal throttling mitigation
- [ ] Alternative voice models evaluation (Coqui TTS)
- [ ] Quantization experiments (Q3, Q5)

---

## V3: Containerization (Future)

- [ ] Docker arm64 image
- [ ] Device mapping (/dev/snd, /dev/gpiomem)
- [ ] docker-compose setup
- [ ] Alternative to systemd deployment

---

## Notes

- **Models**: Stored in `~/models/` on Pi, NOT versioned in Git
- **Latency Target**: ≤10s from button release to first audio
- **Context Size**: ~1-2k tokens for cumulative chapter summaries
- **Chapter Length**: 150-300 words each
- **Offline**: Zero network dependencies in production
- **Platform**: Raspberry Pi 4B (4-8GB RAM), Raspberry Pi OS 64-bit Lite

---

## Current Status

**Completed:**
- ✅ Models downloaded locally (Mac) & transferred to Pi
- ✅ SSH key configured
- ✅ GitHub repository created: https://github.com/didux123/storybox
- ✅ Project structure setup (app/, scripts/, tests/, docs/)
- ✅ Configuration file created (configs/default.yaml)
- ✅ requirements.txt & constraints.txt created
- ✅ whisper.cpp compiled for Mac
- ✅ llama.cpp compiled for Mac
- ✅ Piper TTS installed via pip
- ✅ Documentation complete:
  - README.md with overview
  - docs/MAC_DEVELOPMENT.md for local dev
  - docs/RASPBERRY_PI_SETUP.md for Pi setup
  - test/README.md for testing
- ✅ Deployment scripts:
  - scripts/deploy_init.sh (Mac → Pi rsync)
  - scripts/install_pi.sh (Pi installation automation)
- ✅ Test scripts created:
  - test/scripts/test_tts.py (voice generation)
  - test/scripts/test_stt.sh (speech recognition)
  - test/scripts/test_llm.sh (story generation)

**In Progress:**
- 🔄 Implementing integration modules (AudioIn, GPIO, State Machine)

**Recently Completed:**
- ✅ Configuration loader (YAML + env overrides)
- ✅ Logging system with metrics tracking
- ✅ TTS wrapper (Piper) with streaming support
- ✅ STT wrapper (Whisper) with preprocessing
- ✅ LLM wrapper (Llama) with story plan generation
- ✅ Complete modules documentation (docs/MODULES.md)

**Next:**
- Implement AudioIn module (microphone capture)
- Implement GPIO handlers (button + LED)
- Implement state machine
- Create main orchestrator
- End-to-end testing
