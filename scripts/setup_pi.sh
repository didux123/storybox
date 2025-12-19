#!/bin/bash
# Script d'installation pour Raspberry Pi - StoryBox
# Installe toutes les dépendances et configure l'environnement

set -e  # Arrêter en cas d'erreur

echo "======================================================================"
echo "🚀 Installation StoryBox sur Raspberry Pi"
echo "======================================================================"
echo

# Couleurs pour l'output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Répertoire du projet
PROJECT_DIR="$HOME/storybox"
cd "$PROJECT_DIR"

echo -e "${BLUE}📦 Étape 1/5: Installation des dépendances système${NC}"
echo "----------------------------------------------------------------------"
sudo apt update
sudo apt install -y \
    python3-venv \
    python3-pip \
    portaudio19-dev \
    python3-pyaudio \
    liblgpio-dev \
    git \
    alsa-utils
echo -e "${GREEN}✓ Dépendances système installées${NC}"
echo

echo -e "${BLUE}🐍 Étape 2/5: Création de l'environnement virtuel Python${NC}"
echo "----------------------------------------------------------------------"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Environnement virtuel créé${NC}"
else
    echo -e "${YELLOW}⚠️  Environnement virtuel existe déjà${NC}"
fi
echo

echo -e "${BLUE}📚 Étape 3/5: Installation des packages Python${NC}"
echo "----------------------------------------------------------------------"
source .venv/bin/activate

# Installer les dépendances de base
pip install --upgrade pip

# Installer les packages requis
pip install \
    vosk \
    celeste-ai \
    python-dotenv \
    pyyaml \
    pyaudio \
    gpiozero \
    RPi.GPIO \
    python-json-logger

echo -e "${GREEN}✓ Packages Python installés${NC}"
echo

echo -e "${BLUE}🎙️  Étape 4/5: Installation du modèle Vosk${NC}"
echo "----------------------------------------------------------------------"
VOSK_MODEL_DIR="$HOME/models/vosk"
VOSK_MODEL_NAME="vosk-model-small-fr-0.22"
VOSK_MODEL_PATH="$VOSK_MODEL_DIR/$VOSK_MODEL_NAME"

if [ ! -d "$VOSK_MODEL_PATH" ]; then
    echo "Téléchargement du modèle Vosk français..."
    mkdir -p "$VOSK_MODEL_DIR"
    cd "$VOSK_MODEL_DIR"

    wget -q --show-progress \
        https://alphacephei.com/vosk/models/${VOSK_MODEL_NAME}.zip

    unzip -q ${VOSK_MODEL_NAME}.zip
    rm ${VOSK_MODEL_NAME}.zip

    echo -e "${GREEN}✓ Modèle Vosk installé: $VOSK_MODEL_PATH${NC}"
else
    echo -e "${YELLOW}⚠️  Modèle Vosk existe déjà: $VOSK_MODEL_PATH${NC}"
fi
cd "$PROJECT_DIR"
echo

echo -e "${BLUE}⚙️  Étape 5/5: Configuration de l'environnement${NC}"
echo "----------------------------------------------------------------------"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Fichier .env créé depuis .env.example${NC}"
    echo -e "${YELLOW}   IMPORTANT: Modifiez .env pour ajouter votre GOOGLE_API_KEY${NC}"
    echo
    echo "   Obtenir une clé API Gemini:"
    echo "   → https://makersuite.google.com/app/apikey"
    echo
else
    echo -e "${YELLOW}⚠️  Fichier .env existe déjà${NC}"
fi
echo

echo -e "${BLUE}🔊 Test de l'audio${NC}"
echo "----------------------------------------------------------------------"
echo "Devices audio disponibles:"
arecord -l
echo

echo "======================================================================"
echo -e "${GREEN}✅ Installation terminée!${NC}"
echo "======================================================================"
echo
echo "Prochaines étapes:"
echo "  1. Éditer .env et ajouter votre GOOGLE_API_KEY:"
echo "     nano ~/storybox/.env"
echo
echo "  2. Lancer le test:"
echo "     cd ~/storybox"
echo "     source .venv/bin/activate"
echo "     python3 test_pi_simple.py"
echo
echo "  3. Appuyer sur le bouton (GPIO pin 17) pour enregistrer"
echo "     Relâcher pour lancer la transcription et génération"
echo
echo "======================================================================"
