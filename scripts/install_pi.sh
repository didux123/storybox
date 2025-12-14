#!/bin/bash
# Installation script for StoryBox IA on Raspberry Pi 4B
# This script installs all necessary dependencies and compiles toolchains

set -e  # Exit on error

echo "====================================="
echo "StoryBox IA - Raspberry Pi Setup"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo -e "${YELLOW}Warning: This script is designed for Raspberry Pi${NC}"
fi

# Update system
echo -e "${GREEN}[1/7] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo -e "${GREEN}[2/7] Installing system dependencies...${NC}"
sudo apt install -y \
    python3 python3-venv python3-pip git cmake build-essential \
    libsndfile1 portaudio19-dev sox alsa-utils \
    libasound2-dev

# Create project directory
echo -e "${GREEN}[3/7] Setting up project directory...${NC}"
PROJECT_DIR="$HOME/projects/storybox"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create Python virtual environment
echo -e "${GREEN}[4/7] Creating Python virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}[5/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt

# Build whisper.cpp
echo -e "${GREEN}[6/7] Building whisper.cpp...${NC}"
WHISPER_DIR="/tmp/whisper.cpp"
if [ -d "$WHISPER_DIR" ]; then
    rm -rf "$WHISPER_DIR"
fi

git clone https://github.com/ggerganov/whisper.cpp.git "$WHISPER_DIR"
cd "$WHISPER_DIR"
cmake -B build
cmake --build build --config Release

# Copy whisper binary to local bin
mkdir -p "$PROJECT_DIR/bin"
cp "$WHISPER_DIR/build/bin/whisper-cli" "$PROJECT_DIR/bin/"
echo "whisper.cpp installed: $PROJECT_DIR/bin/whisper-cli"

# Build llama.cpp
echo -e "${GREEN}[7/7] Building llama.cpp...${NC}"
LLAMA_DIR="/tmp/llama.cpp"
if [ -d "$LLAMA_DIR" ]; then
    rm -rf "$LLAMA_DIR"
fi

git clone https://github.com/ggerganov/llama.cpp.git "$LLAMA_DIR"
cd "$LLAMA_DIR"
cmake -B build
cmake --build build --config Release

# Copy llama binaries to local bin
cp "$LLAMA_DIR/build/bin/llama-cli" "$PROJECT_DIR/bin/"
cp "$LLAMA_DIR/build/bin/llama-server" "$PROJECT_DIR/bin/"
echo "llama.cpp installed: $PROJECT_DIR/bin/llama-cli"

# Piper is installed via pip (piper-tts package)
echo -e "${GREEN}Piper TTS installed via pip${NC}"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Display summary
echo ""
echo -e "${GREEN}====================================="
echo "Installation Complete!"
echo "=====================================${NC}"
echo ""
echo "Installed components:"
echo "  - System dependencies (ALSA, PortAudio, etc.)"
echo "  - Python virtual environment: $PROJECT_DIR/.venv"
echo "  - whisper.cpp: $PROJECT_DIR/bin/whisper-cli"
echo "  - llama.cpp: $PROJECT_DIR/bin/llama-cli"
echo "  - Piper TTS: via pip (piper-tts)"
echo ""
echo "Next steps:"
echo "  1. Ensure models are in ~/models/ directory:"
echo "     - ~/models/whisper/ggml-small.bin"
echo "     - ~/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
echo "     - ~/models/piper/fr_FR-siwis-medium.onnx"
echo "  2. Configure .env file"
echo "  3. Test the installation:"
echo "     source .venv/bin/activate"
echo "     python -m app.main"
echo ""
echo -e "${YELLOW}Note: Models are NOT included. Transfer them separately.${NC}"
