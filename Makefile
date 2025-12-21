# Makefile - StoryBox IA
# Commandes pour développement et test

.PHONY: help webapp stop test clean install install-dev

# Couleurs
BLUE := \033[0;34m
GREEN := \033[0;32m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)StoryBox - Commandes disponibles$(NC)"
	@echo ""
	@echo "  $(GREEN)make webapp$(NC)      - Lancer l'interface Streamlit"
	@echo "  $(GREEN)make stop$(NC)        - Arrêter Streamlit"
	@echo "  $(GREEN)make test$(NC)        - Tester Celeste LLM (CLI)"
	@echo "  $(GREEN)make install$(NC)     - Installer dépendances de base (Pi)"
	@echo "  $(GREEN)make install-dev$(NC) - Installer dépendances dev (Mac/PC avec Streamlit)"
	@echo "  $(GREEN)make clean$(NC)       - Nettoyer les fichiers temporaires"
	@echo ""

# Lancer Streamlit
webapp:
	@echo "$(GREEN)🚀 Lancement de l'interface Streamlit...$(NC)"
	@.venv/bin/streamlit run webapp/streamlit_app.py

# Arrêter Streamlit (kill tous les processus streamlit)
stop:
	@echo "$(GREEN)🛑 Arrêt de Streamlit...$(NC)"
	@pkill -f "streamlit run" || echo "Aucun processus Streamlit en cours"

# Test Celeste en ligne de commande
test:
	@echo "$(GREEN)🧪 Test de l'intégration Celeste LLM...$(NC)"
	@.venv/bin/python3 test_celeste_local.py

# Installer les dépendances de base (Pi)
install:
	@echo "$(GREEN)📦 Installation des dépendances de base...$(NC)"
	@uv pip install -r requirements.txt

# Installer les dépendances de dev (Mac/PC avec Streamlit)
install-dev:
	@echo "$(GREEN)📦 Installation des dépendances de développement...$(NC)"
	@uv pip install -r requirements-dev.txt

# Nettoyer les fichiers temporaires
clean:
	@echo "$(GREEN)🧹 Nettoyage...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Fichiers temporaires supprimés"

# Alias
run: webapp
