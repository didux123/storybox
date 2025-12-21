#!/bin/bash
# Script de lancement rapide pour l'interface Streamlit
# Usage: ./run_webapp.sh

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  StoryBox - Interface Streamlit${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Vérifier que .env existe
if [ ! -f ".env" ]; then
    echo -e "${GREEN}❌ Fichier .env non trouvé${NC}"
    echo "   Copiez .env.example vers .env et configurez GOOGLE_API_KEY"
    exit 1
fi

# Vérifier que GOOGLE_API_KEY est définie
if ! grep -q "^GOOGLE_API_KEY=" .env || grep -q "^GOOGLE_API_KEY=your-google-api-key-here" .env; then
    echo -e "${GREEN}⚠️  GOOGLE_API_KEY non configurée${NC}"
    echo "   Éditez .env et ajoutez votre clé API Google"
    echo
    read -p "Voulez-vous continuer quand même? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Lancer Streamlit
echo -e "${GREEN}🚀 Lancement de Streamlit...${NC}"
echo
streamlit run webapp/streamlit_app.py
