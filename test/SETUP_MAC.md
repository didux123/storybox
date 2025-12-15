# Setup Mac pour tests

## État actuel

✅ **Ce qui fonctionne:**
- Audio input (détection micro MacBook Pro)
- Configuration chargée
- Structure du code

❌ **Ce qui manque:**
- Modèles AI (Whisper, Llama, Piper)
- Binaires compilés (whisper-cli, llama-cli, piper)

## Installation complète pour tests

### 1. Installer les dépendances Python

```bash
source .venv/bin/activate
uv pip install pyyaml sounddevice soundfile numpy scipy pyaudio python-dotenv python-json-logger psutil
```

### 2. Télécharger et installer les modèles

#### Whisper (STT)

```bash
# Créer le dossier
mkdir -p ~/models/whisper

# Télécharger le modèle small (466 MB)
cd ~/models/whisper
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
```

#### Llama (LLM)

```bash
# Créer le dossier
mkdir -p ~/models/llm

# Télécharger Llama 3.2 3B Instruct Q4 (~1.9 GB)
cd ~/models/llm
curl -L -O https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf
```

#### Piper (TTS)

```bash
# Créer le dossier
mkdir -p ~/models/piper

# Télécharger le modèle français siwis-medium
cd ~/models/piper
curl -L -O https://github.com/rhasspy/piper/releases/download/v1.2.0/fr_FR-siwis-medium.onnx
curl -L -O https://github.com/rhasspy/piper/releases/download/v1.2.0/fr_FR-siwis-medium.onnx.json
```

### 3. Compiler les binaires (whisper.cpp, llama.cpp)

Ces binaires sont déjà compilés dans `/tmp/whisper.cpp/` et `/tmp/llama.cpp/` selon la session précédente.

Si non disponibles:

```bash
# Whisper
cd /tmp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build
cmake --build build

# Llama
cd /tmp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build
```

### 4. Installer Piper TTS

```bash
pip install piper-tts
```

### 5. Créer le fichier .env

```bash
cp .env.example .env
# Éditer .env avec les bons chemins
```

Contenu du .env:

```bash
WHISPER_MODEL_PATH=/Users/maxence/models/whisper/ggml-small.bin
LLM_MODEL_PATH=/Users/maxence/models/llm/llama-3.2-3b-instruct.Q4_K_M.gguf
PIPER_MODEL_PATH=/Users/maxence/models/piper/fr_FR-siwis-medium.onnx
PIPER_CONFIG_PATH=/Users/maxence/models/piper/fr_FR-siwis-medium.onnx.json
```

### 6. Lancer le test

```bash
python test/mac_test_interface.py
```

## Tailles des téléchargements

- Whisper small: ~466 MB
- Llama 3.2 3B Q4: ~1.9 GB
- Piper français: ~60 MB

**Total: ~2.4 GB**

## Estimation temps

- Téléchargement modèles: 5-15 min (selon connexion)
- Compilation binaires: 2-5 min
- Premier test: 30-60 sec (chargement modèles)
- Tests suivants: 10-20 sec

## Alternative: Tests unitaires sans modèles

Si tu veux tester sans télécharger tous les modèles:

```bash
# Test audio input seulement
MOCK_AUDIO=false python -m app.audio.input

# Test TTS (si Piper installé)
python -m app.tts.piper_tts

# Test GPIO en mode mock
MOCK_GPIO=true python -m app.gpio.button
MOCK_GPIO=true python -m app.gpio.led
```
