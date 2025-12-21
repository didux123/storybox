# StoryBox - Démarrage Rapide Interface Web

Guide rapide pour utiliser l'interface Streamlit sur Mac/PC.

## 🚀 Installation (une seule fois)

```bash
# 1. Installer les dépendances de développement (inclut Streamlit)
make install-dev

# Ou manuellement:
uv pip install -r requirements-dev.txt
```

## ⚙️ Configuration

Assurez-vous que `.env` contient:

```env
GOOGLE_API_KEY=votre-clé-api-google
LLM_MODEL_PATH=gemini-1.5-flash
```

## 🎯 Utilisation Quotidienne

### Lancer l'interface

```bash
# Option 1: Avec make (recommandé)
make webapp

# Option 2: Avec le script
./run_webapp.sh

# Option 3: Streamlit direct
streamlit run webapp/streamlit_app.py
```

L'interface s'ouvre automatiquement sur `http://localhost:8501`

### Arrêter l'interface

```bash
# Option 1: Ctrl+C dans le terminal
# Option 2: Avec make
make stop
```

## 📝 Workflow

1. **Lancer l'interface**: `make webapp`
2. **Entrer un prompt**: Ex: "Raconte-moi l'histoire d'un robot qui découvre les émotions"
3. **Générer le plan**: Clic sur "Générer le Plan"
4. **Générer les chapitres**: Au choix chapitre par chapitre ou automatique
5. **Exporter**: Télécharger en Markdown quand terminé

## 🧪 Tester Celeste

Avant d'utiliser l'interface, testez que Celeste fonctionne:

```bash
make test
```

Vous devriez voir:
- ✅ Génération simple réussie
- ✅ Plan de 5 chapitres généré
- ✅ Chapitre 1 généré

## 📚 Commandes Make Disponibles

```bash
make              # Affiche l'aide
make webapp       # Lance Streamlit
make stop         # Arrête Streamlit
make test         # Teste Celeste en CLI
make install      # Installe dépendances de base (Pi)
make install-dev  # Installe dépendances dev (Mac/PC)
make clean        # Nettoie les fichiers temporaires
```

## 🔧 Configuration Avancée

### Changer de modèle LLM

Dans `.env`, changez `LLM_MODEL_PATH`:

```env
# Gemini Flash (rapide, gratuit)
LLM_MODEL_PATH=gemini-1.5-flash

# Gemini Pro (meilleur qualité)
LLM_MODEL_PATH=gemini-1.5-pro

# OpenAI (besoin de OPENAI_API_KEY)
LLM_MODEL_PATH=gpt-4o-mini

# Anthropic (besoin de ANTHROPIC_API_KEY)
LLM_MODEL_PATH=claude-3-5-sonnet-20241022
```

### Personnaliser les prompts

Éditez `app/llm/celeste_llm.py`:
- `_get_default_plan_prompt()`: Prompt de génération du plan
- `_get_default_chapter_prompt()`: Prompt de génération des chapitres

## 🐛 Dépannage

### "Config not found"
```bash
# Vérifiez que .env existe
cat .env | grep GOOGLE_API_KEY
```

### "Model not found"
Vérifiez que le modèle est supporté. Modèles valides:
- `gemini-1.5-flash`
- `gemini-1.5-pro`
- `gpt-4o`, `gpt-4o-mini`
- `claude-3-5-sonnet-20241022`

### Streamlit ne démarre pas
```bash
# Vérifiez que Streamlit est installé
streamlit --version

# Sinon, installez:
make install-dev
```

## 📁 Structure

```
storybox/
├── Makefile                  # Commandes make
├── run_webapp.sh             # Script lancement rapide
├── test_celeste_local.py     # Test CLI
├── requirements.txt          # Dépendances de base (Pi)
├── requirements-dev.txt      # Dépendances dev (Mac/PC + Streamlit)
└── webapp/
    ├── README.md             # Documentation détaillée
    ├── streamlit_app.py      # Application Streamlit
    ├── components/           # Composants UI (vide pour l'instant)
    └── utils/                # Utilitaires (vide pour l'instant)
```

## 🎓 Pour aller plus loin

- Documentation complète: `webapp/README.md`
- Code source: `webapp/streamlit_app.py`
- Configuration: `app/utils/config.py`
- LLM: `app/llm/celeste_llm.py`

---

**Besoin d'aide ?** Consultez `webapp/README.md` pour plus de détails.
