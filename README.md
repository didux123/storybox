# StoryBox IA

> Dispositif interactif de génération d'histoires par IA pour Raspberry Pi 4B

## 🎯 Description

StoryBox IA transforme un Raspberry Pi en conteur interactif alimenté par des IA cloud de dernière génération. L'utilisateur maintient un bouton pour dicter un thème, et le système génère une histoire captivante narrée automatiquement.

**Caractéristiques principales :**
- 🎤 Entrée vocale française (hold-to-talk)
- 🤖 Génération d'histoires via LLM cloud (GPT-4, Claude, Gemini, etc.)
- 🔊 Narration TTS en streaming (à venir avec Celeste TTS)
- 💡 Indicateurs LED d'état
- 🌐 Architecture cloud flexible avec multi-providers

## 🏗️ Architecture Cloud (main branch)

```
Voice Input → STT (Google Speech) → Celeste LLM → [TTS - coming soon] → Audio Output
              ↓
          Button (GPIO) → State Machine → LED Indicators
```

**Stack technique actuelle :**
- **STT**: Google Speech Recognition (gratuit, temporaire)
- **LLM**: [Celeste AI](https://github.com/withceleste/celeste-python) - Unified API supportant:
  - OpenAI (GPT-4o, GPT-4o-mini)
  - Anthropic (Claude 3.5 Sonnet)
  - Google (Gemini 2.0 Flash)
  - Mistral, xAI, DeepSeek, Groq, etc.
- **TTS**: En attente de Celeste TTS via Gradio (release prochaine)

**Avantages du cloud :**
- ⚡ Latence réduite : ~10s (vs ~33s en local)
- 🎯 Meilleure qualité des modèles
- 🔄 Changement de provider instantané
- 🚀 Déploiement simplifié

## 📦 Mode Local (deprecated)

L'implémentation locale avec Whisper/TinyLlama/Piper est disponible dans la branche `local_storybox` :

```bash
git checkout local_storybox
```

Voir `docs/legacy/` pour la documentation du mode local.

## 🚀 Démarrage Rapide

### 1. Cloner le repository

```bash
git clone https://github.com/didux123/storybox.git
cd storybox
```

### 2. Installer les dépendances

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
```

Éditer `.env` et ajouter votre clé API :

```env
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL_PATH=gpt-4o-mini
```

**Obtenir une clé API :**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Google: https://makersuite.google.com/app/apikey

### 4. Test

```bash
python test/test_cloud_pipeline.py
```

**Pour un guide complet, voir [QUICKSTART.md](QUICKSTART.md)**

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Guide de démarrage rapide avec cloud API
- **[Expression_besoin.md](Expression_besoin.md)** - Cahier des charges complet (français)
- **[CLAUDE.md](CLAUDE.md)** - Guide pour Claude Code
- **[docs/legacy/](docs/legacy/)** - Documentation du mode local (deprecated)

## 🗂️ Structure du Projet

```
storybox/
├── app/
│   ├── llm/             # Celeste LLM wrapper
│   │   └── celeste_llm.py
│   ├── stt/             # System dictation (temporary)
│   │   └── system_dictation.py
│   ├── tts/             # TTS module (à venir)
│   ├── gpio/            # Button & LED handlers
│   ├── state/           # State machine
│   └── utils/           # Config, logging, metrics
├── test/                # Tests
│   └── test_cloud_pipeline.py
├── docs/                # Documentation
│   └── legacy/          # Docs mode local
├── configs/             # Configuration YAML
├── scripts/             # Scripts de déploiement
│   └── legacy/          # Scripts mode local
├── .env.example         # Template de configuration
├── requirements.txt     # Dépendances cloud
└── QUICKSTART.md        # Guide de démarrage rapide
```

## 🎮 Utilisation

### Test interactif (développement)

```bash
python test/test_cloud_pipeline.py
```

Le test va :
1. Enregistrer 5 secondes d'audio
2. Transcrire avec Google Speech Recognition
3. Générer un plan d'histoire avec Celeste LLM
4. Générer le premier chapitre
5. Afficher les résultats

### Sur Raspberry Pi (production)

```bash
# TODO: À venir quand TTS sera disponible
# Le système utilisera le bouton GPIO pour l'interface hold-to-talk
```

## 🛠️ Prérequis

### Pour le développement (Mac/Linux)

- Python 3.10+
- PyAudio (pour l'enregistrement)
- Connexion internet (APIs cloud)
- Clé API OpenAI/Anthropic/Google

### Pour la production (Raspberry Pi)

- Raspberry Pi 4B (2GB+ RAM suffisant en mode cloud)
- Carte microSD 16 GB minimum
- Micro USB ou interface audio USB
- Haut-parleur
- Bouton poussoir GPIO
- LED pour indicateurs d'état
- **Connexion internet** (requis pour APIs cloud)

## ⚙️ Configuration

La configuration se fait via :
1. **`.env`** : Clés API et chemins
2. **`configs/default.yaml`** : Paramètres GPIO, audio, etc.

Exemple `.env` :

```env
# Cloud API keys
OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key
# GOOGLE_API_KEY=your-google-key

# Model selection
LLM_MODEL_PATH=gpt-4o-mini

# Audio devices (optionnel)
# AUDIO_INPUT_DEVICE=plughw:1,0
# AUDIO_OUTPUT_DEVICE=plughw:0,0

# GPIO pins (Raspberry Pi only)
# BUTTON_PIN=17
```

## 🗺️ Roadmap

- [x] **V0.1**: Pipeline cloud de base (STT + LLM)
- [ ] **V0.2**: Intégration Celeste TTS via Gradio
- [ ] **V0.3**: Déploiement Raspberry Pi avec GPIO
- [ ] **V1.0**: LED status, pause/reprise, système complet
- [ ] **V1.1**: Optimisations streaming et gestion du contexte
- [ ] **V2.0**: Interface web optionnelle, analytics

## 🔄 Changement de Provider

Celeste permet de changer de provider en modifiant simplement le model ID :

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

Aucun changement de code nécessaire !

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à :
- Reporter des bugs via les issues
- Proposer des améliorations
- Soumettre des pull requests

## 📄 Licence

MIT

## 👤 Auteur

**Maxence** - Créateur initial

---

**Note**: Pour l'implémentation locale 100% offline avec modèles Whisper/TinyLlama/Piper, voir la branche `local_storybox` et la documentation dans `docs/legacy/`.
