# StoryBox IA

Dispositif autonome d'histoires générées par IA pour Raspberry Pi 4B.

## Description

StoryBox IA est un projet qui transforme un Raspberry Pi en conteur interactif. L'utilisateur maintient un bouton pour dicter un thème, et le système génère et narre une histoire complète en 10 chapitres, entièrement hors ligne.

**Caractéristiques :**
- 🎤 Entrée vocale française (hold-to-talk)
- 🤖 Génération d'histoires via LLM local (3B quantifié)
- 🔊 Narration TTS en streaming
- 💡 Indicateurs LED d'état
- 📴 Fonctionnement 100% offline

## Architecture

```
Voice Input → STT (Whisper) → Planner (LLM) → StoryGen (LLM) → TTS (Piper) → Audio Output
              ↓
          Button (GPIO) → State Machine → LED Indicators
```

## Prérequis

### Matériel
- Raspberry Pi 4B (4-8 GB RAM)
- Carte microSD 64 GB
- Micro USB ou interface audio USB
- Haut-parleur USB ou HAT audio I2S
- Bouton poussoir GPIO
- LED(s) pour indicateurs d'état

### Logiciel
- Raspberry Pi OS 64-bit Lite (Bookworm)
- Python 3.10+
- whisper.cpp (compilé)
- llama.cpp (compilé)
- Piper TTS

## Installation

### 1. Cloner le repository

```bash
git clone <repository_url>
cd storybox
```

### 2. Installer les dépendances système (Raspberry Pi)

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y \
  python3 python3-venv python3-pip git cmake build-essential \
  libsndfile1 portaudio19-dev sox alsa-utils
```

### 3. Créer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -c constraints.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 5. Installer les modèles

Les modèles AI ne sont PAS versionnés dans Git. Ils doivent être installés séparément :

```bash
# Structure recommandée
~/models/
├── llm/      # Llama-3.2-3B-Instruct-Q4_K_M.gguf
├── whisper/  # ggml-small.bin
└── piper/    # fr_FR-siwis-medium.onnx + .json
```

Voir `workflow.md` pour les instructions détaillées de déploiement.

## Configuration

Modifier `configs/default.yaml` pour ajuster :
- Chemins des modèles
- Devices audio ALSA
- Pins GPIO
- Paramètres LLM (température, threads, etc.)
- Durées et seuils

## Développement

### 📚 Documentation Détaillée

- **[Mac Development Guide](docs/MAC_DEVELOPMENT.md)** - Développement local sur Mac
- **[Raspberry Pi Setup Guide](docs/RASPBERRY_PI_SETUP.md)** - Installation complète sur Pi

### Tests locaux (Mac)

```bash
# Avec GPIO mockés
export MOCK_GPIO=true
python -m app.main
```

**Note:** whisper.cpp, llama.cpp et Piper doivent être installés localement. Voir `docs/MAC_DEVELOPMENT.md` pour les instructions.

### Déploiement sur Raspberry Pi

```bash
# Premier déploiement (depuis Mac)
./scripts/deploy_init.sh

# Sur le Pi, installer les dépendances
ssh maxence@<PI_IP>
cd ~/projects/storybox
bash scripts/install_pi.sh

# Mises à jour via Git
git pull --rebase
sudo systemctl restart storybox
```

**Voir `docs/RASPBERRY_PI_SETUP.md` pour le guide complet.**

## Utilisation

### Mode interactif
1. Maintenir le bouton → LED "Listening"
2. Dicter le thème de l'histoire
3. Relâcher le bouton → LED "Processing"
4. Attendre le début de la narration → LED "Narrating"
5. Pression courte pendant narration → Pause/Reprise
6. Pression longue (≥3s) → Arrêt propre

### Métriques

Logs et métriques disponibles dans `~/projects/storybox/logs/` :
- Latence (relâchement → premier audio)
- Tokens/seconde
- Temps de chargement des modèles
- Erreurs audio/GPIO

## Architecture du code

```
storybox/
├── app/
│   ├── audio/       # Capture et playback audio
│   ├── stt/         # Whisper wrapper
│   ├── llm/         # Llama.cpp wrapper
│   ├── tts/         # Piper wrapper
│   ├── gpio/        # Button & LED handlers
│   ├── state/       # State machine
│   ├── utils/       # Config, logging, metrics
│   └── main.py      # Orchestrateur principal
├── configs/         # Fichiers YAML
├── scripts/         # Scripts de déploiement
├── tests/           # Tests unitaires et d'intégration
└── models/          # Modèles AI (non versionnés)
```

## Roadmap

- **V0**: Pipeline de base hold-to-talk → STT → Plan → StoryGen → TTS
- **V1**: Streaming affiné, LED avancées, pause/reprise, rotation logs
- **V2**: SSD pour modèles, tuning thermique/threads
- **V3**: Image Docker arm64 optionnelle

Voir `TODO.md` pour le détail complet.

## Documentation

- `Expression_besoin.md` : Spécifications complètes (français)
- `workflow.md` : Workflow de développement et déploiement
- `CLAUDE.md` : Guide pour Claude Code
- `TODO.md` : Tâches de développement

## Licence

[À définir]

## Contributeurs

Maxence - Créateur initial
