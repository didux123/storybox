#!/bin/bash
###############################################################################
# StoryBox - Script d'installation complète pour Raspberry Pi 4B
#
# Ce script installe automatiquement:
# - Toutes les dépendances système
# - Le projet StoryBox depuis GitHub
# - L'environnement Python et les packages
# - Les modèles IA (Whisper, Llama, Piper)
# - La configuration de base
#
# Usage: ./install_pi_complete.sh
# Durée estimée: 30-45 minutes
###############################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuration
PROJECT_DIR="$HOME/storybox"
MODELS_DIR="$HOME/models"
VENV_DIR="$PROJECT_DIR/.venv"
GITHUB_REPO="https://github.com/didux123/storybox.git"

###############################################################################
# Fonctions utilitaires
###############################################################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 est installé"
        return 0
    else
        print_warning "$1 n'est pas installé"
        return 1
    fi
}

###############################################################################
# Vérifications préliminaires
###############################################################################

print_header "StoryBox - Installation complète sur Raspberry Pi"

echo ""
print_step "Vérification du système..."

# Vérifier qu'on est sur un Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    print_error "Ce script doit être exécuté sur un Raspberry Pi"
    exit 1
fi

RPI_MODEL=$(cat /proc/device-tree/model)
print_success "Détecté: $RPI_MODEL"

# Vérifier l'espace disque disponible (minimum 10GB)
AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    print_error "Espace disque insuffisant: ${AVAILABLE_SPACE}GB disponibles (minimum 10GB requis)"
    exit 1
fi
print_success "Espace disque: ${AVAILABLE_SPACE}GB disponibles"

# Vérifier la connexion Internet
print_step "Vérification de la connexion Internet..."
if ping -c 1 github.com &> /dev/null; then
    print_success "Connexion Internet OK"
else
    print_error "Pas de connexion Internet"
    exit 1
fi

echo ""
read -p "Continuer l'installation? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    print_warning "Installation annulée"
    exit 0
fi

###############################################################################
# Étape 1: Mise à jour du système
###############################################################################

print_header "Étape 1/9: Mise à jour du système"

print_step "Mise à jour de la liste des paquets..."
sudo apt update

print_step "Mise à jour des paquets installés (peut prendre plusieurs minutes)..."
sudo apt upgrade -y

print_success "Système mis à jour"

###############################################################################
# Étape 2: Installation des dépendances système
###############################################################################

print_header "Étape 2/9: Installation des dépendances système"

print_step "Installation des outils de compilation..."
sudo apt install -y \
    git \
    cmake \
    build-essential \
    swig

print_step "Installation des bibliothèques audio..."
sudo apt install -y \
    libsndfile1 \
    portaudio19-dev \
    sox \
    alsa-utils

print_step "Installation de Python et outils de développement..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev

print_success "Dépendances système installées"

###############################################################################
# Étape 3: Clonage du projet
###############################################################################

print_header "Étape 3/9: Clonage du projet StoryBox"

if [ -d "$PROJECT_DIR" ]; then
    print_warning "Le dossier $PROJECT_DIR existe déjà"
    read -p "Supprimer et réinstaller? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        rm -rf "$PROJECT_DIR"
    else
        print_error "Installation annulée"
        exit 1
    fi
fi

print_step "Clonage depuis GitHub..."
git clone "$GITHUB_REPO" "$PROJECT_DIR"

cd "$PROJECT_DIR"
print_success "Projet cloné dans $PROJECT_DIR"

###############################################################################
# Étape 4: Environnement Python
###############################################################################

print_header "Étape 4/9: Configuration de l'environnement Python"

print_step "Création de l'environnement virtuel..."
python3 -m venv "$VENV_DIR"

print_step "Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"

print_step "Mise à jour de pip, wheel et setuptools..."
pip install --upgrade pip wheel setuptools

print_success "Environnement Python configuré"

###############################################################################
# Étape 5: Installation des packages Python
###############################################################################

print_header "Étape 5/9: Installation des packages Python"

print_step "Installation des bibliothèques de base..."
pip install pyyaml python-dotenv python-json-logger psutil

print_step "Installation des bibliothèques audio..."
pip install sounddevice soundfile numpy scipy pyaudio

print_step "Installation des bibliothèques GPIO..."
pip install RPi.GPIO gpiozero

print_step "Installation de pywhispercpp (STT)..."
pip install pywhispercpp

print_step "Installation de llama-cpp-python (LLM) - peut prendre 10-15 minutes..."
print_warning "Cette étape compile llama.cpp, soyez patient..."
pip install llama-cpp-python --no-cache-dir

print_success "Tous les packages Python sont installés"

###############################################################################
# Étape 6: Installation de Piper TTS
###############################################################################

print_header "Étape 6/9: Installation de Piper TTS"

print_step "Création du répertoire pour les binaires..."
mkdir -p "$PROJECT_DIR/bin"
cd "$PROJECT_DIR/bin"

print_step "Téléchargement de Piper pour ARM64..."
wget -q --show-progress https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz

print_step "Extraction de l'archive..."
tar xzf piper_arm64.tar.gz
rm piper_arm64.tar.gz

chmod +x piper/piper

PIPER_VERSION=$("$PROJECT_DIR/bin/piper/piper" --version)
print_success "Piper $PIPER_VERSION installé"

###############################################################################
# Étape 7: Téléchargement des modèles IA
###############################################################################

print_header "Étape 7/9: Téléchargement des modèles IA"

print_step "Création des répertoires pour les modèles..."
mkdir -p "$MODELS_DIR"/{whisper,llm,piper}

# Whisper (STT)
print_step "Téléchargement de Whisper small (~466MB)..."
cd "$MODELS_DIR/whisper"
if [ ! -f "ggml-small.bin" ]; then
    wget -q --show-progress https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
    print_success "Whisper téléchargé"
else
    print_warning "Whisper déjà présent, passage"
fi

# Llama (LLM)
print_step "Téléchargement de Llama 3.2 3B Q4 (~1.9GB) - peut prendre du temps..."
cd "$MODELS_DIR/llm"
if [ ! -f "Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]; then
    wget -q --show-progress https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
    print_success "Llama téléchargé"
else
    print_warning "Llama déjà présent, passage"
fi

# Piper (TTS)
print_step "Téléchargement de Piper FR (~61MB)..."
cd "$MODELS_DIR/piper"
if [ ! -f "fr_FR-siwis-medium.onnx" ]; then
    wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
    wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
    print_success "Piper voice téléchargée"
else
    print_warning "Piper voice déjà présente, passage"
fi

print_success "Tous les modèles sont téléchargés"

###############################################################################
# Étape 8: Configuration
###############################################################################

print_header "Étape 8/9: Configuration du projet"

cd "$PROJECT_DIR"

print_step "Création du fichier .env..."
cat > .env << EOF
# StoryBox IA - Raspberry Pi Configuration

# Model paths
WHISPER_MODEL_PATH=$MODELS_DIR/whisper/ggml-small.bin
LLM_MODEL_PATH=$MODELS_DIR/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf
PIPER_MODEL_PATH=$MODELS_DIR/piper/fr_FR-siwis-medium.onnx
PIPER_CONFIG_PATH=$MODELS_DIR/piper/fr_FR-siwis-medium.onnx.json
PIPER_BINARY_PATH=$PROJECT_DIR/bin/piper/piper

# Audio devices (ALSA)
# Utilisez "arecord -l" et "aplay -l" pour identifier vos périphériques
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default

# GPIO
BUTTON_PIN=17

# Logging
LOG_LEVEL=INFO
LOG_DIR=$PROJECT_DIR/logs
EOF

print_step "Création du répertoire de logs..."
mkdir -p "$PROJECT_DIR/logs"

print_step "Détection des périphériques audio..."
echo ""
echo "=== Périphériques d'entrée (micro) ==="
arecord -l
echo ""
echo "=== Périphériques de sortie (haut-parleur) ==="
aplay -l
echo ""
print_warning "Vérifiez et modifiez $PROJECT_DIR/.env si nécessaire"
print_warning "Utilisez AUDIO_INPUT_DEVICE=plughw:CARD,DEVICE"

print_success "Configuration créée"

###############################################################################
# Étape 9: Tests
###############################################################################

print_header "Étape 9/9: Tests de l'installation"

cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"

print_step "Vérification des packages Python..."
pip list | grep -E '(llama|whisper|pyyaml|sounddevice|RPi.GPIO)' || true

print_step "Test de Piper TTS..."
echo "Bonjour, je suis StoryBox!" | "$PROJECT_DIR/bin/piper/piper" \
    --model "$MODELS_DIR/piper/fr_FR-siwis-medium.onnx" \
    --output_file /tmp/test_install.wav

if [ -f /tmp/test_install.wav ]; then
    print_success "Piper fonctionne"
    print_step "Lecture du test audio..."
    aplay /tmp/test_install.wav 2>/dev/null || print_warning "Erreur lecture audio (vérifiez vos périphériques)"
    rm /tmp/test_install.wav
else
    print_error "Erreur Piper"
fi

###############################################################################
# Installation terminée
###############################################################################

print_header "Installation terminée!"

echo ""
print_success "StoryBox est installé dans: $PROJECT_DIR"
print_success "Modèles IA dans: $MODELS_DIR"
echo ""
echo "=== Prochaines étapes ==="
echo "1. Connectez-vous au projet:"
echo "   cd $PROJECT_DIR"
echo "   source .venv/bin/activate"
echo ""
echo "2. Ajustez la configuration audio dans .env si nécessaire"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "3. Testez le système:"
echo "   python3 quick_test.py          # Test rapide"
echo "   python3 test_button_rpi.py     # Test bouton GPIO"
echo "   python3 full_test.py           # Test complet (STT+LLM+TTS)"
echo ""
echo "4. Consultez la documentation:"
echo "   cat $PROJECT_DIR/INSTALLATION_SUMMARY.md"
echo ""

print_step "Informations système:"
echo "  - Python: $(python3 --version)"
echo "  - Piper: $PIPER_VERSION"
echo "  - Espace disque restant: $(df -h / | tail -1 | awk '{print $4}')"
echo ""

print_warning "N'oubliez pas d'activer l'environnement virtuel avec:"
echo "  source $PROJECT_DIR/.venv/bin/activate"
echo ""

print_success "Installation réussie! 🎉"