#!/bin/bash
# Initial deployment script for StoryBox IA
# Deploys code from Mac to Raspberry Pi via rsync

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
PI_USER="${PI_USER:-maxence}"
PI_HOST="${RPI_IP_ADDRESS:-192.168.68.120}"
PI_DIR="/home/${PI_USER}/projects/storybox"
SSH_KEY="$HOME/.ssh/id_ed25519_storybox"

echo "====================================="
echo "StoryBox IA - Deployment to Pi"
echo "====================================="
echo "Target: ${PI_USER}@${PI_HOST}:${PI_DIR}"
echo ""

# Check SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found at $SSH_KEY"
    echo "Please configure SSH key first"
    exit 1
fi

# Test SSH connection
echo "Testing SSH connection..."
ssh -i "$SSH_KEY" "${PI_USER}@${PI_HOST}" "echo 'SSH connection successful'" || {
    echo "Error: Cannot connect to Pi"
    exit 1
}

# Sync code to Pi (exclude models, logs, venv)
echo ""
echo "Syncing code to Raspberry Pi..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY" \
    --exclude '.venv/' \
    --exclude 'models/' \
    --exclude 'logs/' \
    --exclude '__pycache__/' \
    --exclude '.git/' \
    --exclude '.idea/' \
    --exclude '.DS_Store' \
    --exclude '*.pyc' \
    ./ "${PI_USER}@${PI_HOST}:${PI_DIR}/"

echo ""
echo "====================================="
echo "Deployment Complete!"
echo "====================================="
echo ""
echo "Next steps on the Raspberry Pi:"
echo "  1. SSH to Pi: ssh -i $SSH_KEY ${PI_USER}@${PI_HOST}"
echo "  2. Navigate: cd ${PI_DIR}"
echo "  3. Run installation: bash scripts/install_pi.sh"
echo "  4. Copy .env: cp .env.example .env && nano .env"
echo "  5. Ensure models are in ~/models/ (rsync or manual copy)"
echo ""
