# 📜 Changelog - AI Storybox

## 🚧 V0.4 - API Backend & Docker (En cours)

### 🎉 Session du 29 décembre 2024
**Travail effectué:**

1. ✅ **Backend FastAPI créé**
   - Structure backend/ complète avec architecture REST
   - Modèles Pydantic pour validation (request.py, response.py)
   - Endpoint principal: `POST /api/v1/generate-story`
   - Healthcheck endpoint: `GET /health`
   - Documentation Swagger auto-générée (/docs)

2. ✅ **Service Layer**
   - StoryService créé (backend/services/story_service.py)
   - Orchestration LLM + TTS + STT
   - Réutilise modules existants (app/llm, app/tts, app/stt)
   - Calcul automatique des métriques (tokens, cost, duration)
   - Support output_format: text ou audio (base64)

3. ✅ **Sécurité & Middleware**
   - JWT authentication (backend/core/security.py)
   - Rate limiting middleware (in-memory, Redis-ready)
   - CORS middleware pour frontend
   - Configuration centralisée (pydantic-settings)

4. ✅ **Dockerisation complète**
   - Dockerfile backend (multi-stage build)
   - Dockerfile frontend (Streamlit)
   - docker-compose.yml avec 4 services:
     - Backend API (port 8000)
     - Frontend Streamlit (port 8501)
     - PostgreSQL (pour V1.0)
     - Redis (rate limiting)
   - .env.docker.example template

5. ✅ **Requirements split**
   - requirements-backend.txt (FastAPI, uvicorn, jose, passlib)
   - requirements-frontend.txt (Streamlit, httpx)
   - Optimisation des dépendances par service

**Architecture V0.4:**
```
┌─────────────────────────────────────────────────┐
│              Docker Compose Stack                │
│                                                  │
│  ┌──────────────┐      ┌──────────────┐         │
│  │   Frontend   │─────▶│   Backend    │         │
│  │  Streamlit   │      │   FastAPI    │         │
│  │  (port 8501) │      │  (port 8000) │         │
│  └──────────────┘      └──────┬───────┘         │
│                               │                  │
│                    ┌──────────┴──────────┐       │
│                    │                     │       │
│              ┌─────▼─────┐      ┌───────▼────┐  │
│              │PostgreSQL │      │   Redis    │  │
│              │(port 5432)│      │(port 6379) │  │
│              └───────────┘      └────────────┘  │
└─────────────────────────────────────────────────┘

API Endpoints:
- POST /api/v1/generate-story
- GET /api/v1/health
- GET /docs (Swagger UI)
```

**Commits V0.4:**
- Branche: feature/v0.4-api-backend

**Prochaines étapes:**
- [ ] Tests backend locaux
- [ ] Tests Docker Compose
- [ ] Documentation README
- [ ] Merge vers main

---

## ✅ V0.3 - STT Integration (Terminée!)

### 🎉 Session du 25 décembre 2024 - Partie 2
**Travail effectué:**

1. ✅ **Intégration STT complète avec Gradium**
   - Module `GradiumSTT` créé (`app/stt/gradium_stt.py`)
   - API Gradium directe pour transcription audio
   - Support des formats WAV, PCM, OPUS
   - Méthodes async/sync pour flexibilité
   - Auto-détection du format audio depuis l'extension de fichier

2. ✅ **Interface utilisateur STT dans Streamlit**
   - Widget d'enregistrement audio natif (st.audio_input)
   - Bouton de transcription avec indicateur de progression
   - Affichage du texte transcrit avec métriques (temps de transcription)
   - Pré-remplissage automatique du champ de prompt avec le texte transcrit
   - Option pour effacer la transcription
   - Double option : enregistrement vocal OU saisie manuelle

3. ✅ **Métriques de performance déjà implémentées**
   - Affichage des tokens utilisés (input/output) par chapitre et plan
   - Temps de génération affiché pour chaque opération
   - Coût estimé calculé et affiché ($/génération)
   - Dashboard global avec métriques cumulatives
   - Tracking des erreurs API avec historique

**Architecture:**
```
Utilisateur → 🎤 Enregistrement vocal → GradiumSTT → Texte transcrit
                                                          ↓
                                                    Génération plan (CelesteLLM)
                                                          ↓
                                                    Génération chapitres
                                                          ↓
                                                    Narration (GradiumTTS) → 🔊 Audio
```

---

## ✅ V0.2 - TTS Integration (Terminée!)

### 🎉 Session du 25 décembre 2024 - Partie 1
**Travail effectué:**
1. ✅ Fix des paramètres Streamlit
   - Résolution bug: nombre de chapitres toujours à 10 → maintenant configurable
   - Ajout support température dans génération (plan + chapitres)
   - Ajout variable `{num_chapters}` dans prompts pour meilleure cohérence narrative

2. ✅ Intégration TTS complète avec Gradium
   - Tentative initiale avec Celeste → problèmes de compatibilité
   - **Solution finale:** API Gradium directe (module `GradiumTTS`)
   - Support complet des IDs de voix personnalisés fournis par l'utilisateur
   - Contrôle de vitesse fonctionnel (padding_bonus)
   - Tests réussis: 391KB audio généré (voix Claire)

3. ✅ Interface utilisateur TTS
   - 4 voix françaises pré-configurées + option personnalisée
   - Slider de vitesse avec 5 presets
   - Boutons 🔊 pour chaque chapitre
   - Bouton 🔊 pour histoire complète

**Commits V0.2:**
- `584411a` - fix: Remove hardcoded prompts from default.yaml
- `c2b458d` - fix: Add temperature parameter support
- `79849bf` - feat: Add num_chapters context to prompts
- `794ece0` - feat: Add voice preset selection
- `7575368` - feat: Implement Celeste TTS (abandonné)
- `bfb846e` - feat: Replace Celeste with direct Gradium API ⭐

---

## 🚀 Fonctionnalités Actuelles (V0.3)

### Webapp Streamlit Complète
- [x] Interface web avec 4 onglets fonctionnels
  - 🎤 **Prompt & Plan** : Enregistrement vocal OU saisie manuelle + génération du plan
  - ✍️ **Génération Chapitres** : Génération chapitre par chapitre avec contexte
  - 📚 **Histoire Complète** : Vue d'ensemble + génération automatique de tous les chapitres
  - ⚙️ **Prompts** : Éditeur de prompts en temps réel
- [x] Métriques de performance complètes
  - Tokens (input/output) par génération
  - Temps de génération
  - Coût estimé ($/génération)
  - Dashboard cumulatif
  - Historique des erreurs API
- [x] Export de l'histoire en Markdown
- [x] Makefile pour lancement facile (`make webapp`)

### Modules IA Complets
- [x] **LLM** : CelesteLLM avec support multi-providers (Gemini, Claude, GPT-4o)
- [x] **TTS** : GradiumTTS avec 4 voix françaises + vitesse configurable
- [x] **STT** : GradiumSTT avec enregistrement audio intégré
- [x] Configuration centralisée (YAML + JSON + .env)
- [x] Logging structuré

### Configuration
- [x] Prompts éditables via interface Streamlit
- [x] Paramètres de génération ajustables (température, longueur, nb chapitres)
- [x] Voix TTS sélectionnable avec IDs personnalisés
- [x] Validation Pydantic pour JSON structuré

---

---

## 📦 Modules Implémentés

### LLM (app/llm/)
- ✅ **CelesteLLM** (`celeste_llm.py`)
  - Génération de plans d'histoires structurés (JSON avec Pydantic)
  - Génération de chapitres avec contexte cumulatif
  - Support multi-providers (Gemini, Claude, GPT-4o via Celeste AI)
  - Gestion de la température et des tokens
  - Prompts configurables via `configs/prompts.json`

### TTS - Text-to-Speech (app/tts/)
- ✅ **GradiumTTS** (`gradium_tts.py`)
  - API Gradium directe (pas via Celeste)
  - Support voix personnalisées (IDs de voix Gradium)
  - Contrôle de vitesse (padding_bonus -4.0 à +4.0)
  - Format WAV optimisé
  - Méthodes async + wrappers sync

- ⚠️ **CelesteTTS** (`celeste_tts.py`) - Deprecated
  - Remplacé par GradiumTTS pour meilleure compatibilité
  - Conservé pour référence

### STT - Speech-to-Text (app/stt/)
- ✅ **GradiumSTT** (`gradium_stt.py`)
  - API Gradium directe pour transcription
  - Support WAV, PCM, OPUS
  - Streaming audio par chunks (80ms à 24kHz)
  - Auto-détection du format
  - Méthodes async + wrappers sync

- ⚠️ **PiperSTT** (`piper_stt.py`) - À supprimer
  - Ancien module pour Raspberry Pi (local)
  - Non utilisé, remplacé par GradiumSTT

### Utils (app/utils/)
- ✅ **Config** (`config.py`)
  - Chargement centralisé depuis `configs/default.yaml`
  - Support des variables d'environnement
  - Validation des chemins et paramètres

- ✅ **Logger** (`logger.py`)
  - Logging structuré avec rotation
  - Niveaux configurables
  - Format JSON pour analyse

### Webapp (webapp/)
- ✅ **Streamlit UI** (`streamlit_app.py`)
  - 4 onglets fonctionnels (Prompt & Plan, Chapitres, Histoire complète, Prompts)
  - Enregistrement vocal intégré (STT)
  - Narration audio intégrée (TTS)
  - Configuration TTS avec sélection de voix et vitesse
  - Métriques de performance complètes
  - Édition en temps réel des prompts
  - Export Markdown

- ✅ **Prompt Editor** (`utils/prompt_editor.py`)
  - Chargement/sauvegarde de `configs/prompts.json`
  - Validation des templates

---

## 🔧 Configuration Actuelle

### TTS - Voix Disponibles
- **Claire** (zIGaffB0kKEBG_8u) - féminine française ⭐ par défaut
- **Voix 2** (IB53xJtufx1sbfbt) - française
- **Voix 3** (s0PhgjzOTRD5wo5L) - française
- **Voix 4** (rIYDMY3dLccdauWA) - française
- **ID personnalisé** - pour tester d'autres voix Gradium

### TTS - Contrôle de Vitesse
- Très rapide (-2.0)
- Rapide (-1.0)
- Normale (0.0)
- Lent (1.0)
- Très lent (2.0)

### STT - Formats Supportés
- WAV (recommandé pour Streamlit)
- PCM (24kHz, 16-bit, mono)
- OPUS

### LLM - Providers Supportés
- Gemini 1.5 Flash (rapide, gratuit)
- Gemini 1.5 Pro (meilleure qualité)
- GPT-4o Mini (OpenAI)
- Claude 3.5 Sonnet (Anthropic)

---
