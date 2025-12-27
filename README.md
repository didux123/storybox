# StoryBox IA

> Générateur d'histoires interactives par IA avec narration vocale

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/didux123/storybox)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 Description

StoryBox IA est un système complet de génération d'histoires pour enfants alimenté par l'IA. Le système combine:
- 🎤 **Enregistrement vocal** pour dicter le thème de l'histoire
- 🤖 **Génération d'histoires** via LLM (Gemini, Claude, GPT-4o)
- 🔊 **Narration audio** avec voix françaises naturelles
- 📊 **Métriques en temps réel** (tokens, coûts, performances)

**Démo en ligne:** Interface web Streamlit complète pour tester toute la pipeline

## ✨ Fonctionnalités V0.3

### Interface Web Streamlit
- 🎤 **Enregistrement vocal** : Dictez votre demande d'histoire directement dans le navigateur
- 📝 **Transcription STT** : Conversion automatique audio → texte (Gradium API)
- 📖 **Génération de plan** : Structure narrative en 3-10 chapitres
- ✍️ **Génération de chapitres** : Rédaction chapitre par chapitre avec contexte cumulatif
- 🔊 **Narration TTS** : 4 voix françaises naturelles avec contrôle de vitesse
- 📊 **Métriques complètes** : Tokens, temps, coûts estimés
- ⚙️ **Éditeur de prompts** : Personnalisation en temps réel
- 💾 **Export** : Téléchargement de l'histoire complète en Markdown

### Modules IA
- **LLM** : Support multi-providers via Celeste AI (Gemini, Claude, GPT-4o, Mistral)
- **TTS** : Gradium API avec 4 voix françaises + contrôle de vitesse
- **STT** : Gradium API pour transcription vocale
- **Configuration** : Paramètres ajustables (température, longueur, nombre de chapitres)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit WebApp                        │
│  ┌──────────┐  ┌───────────┐  ┌────────┐  ┌──────────┐    │
│  │  🎤 STT  │→ │  🤖 LLM   │→ │ 📖 Plan│→ │ 🔊 TTS   │    │
│  │ Gradium  │  │ Celeste   │  │Chapitres│ │ Gradium  │    │
│  └──────────┘  └───────────┘  └────────┘  └──────────┘    │
│                                                              │
│  📊 Métriques: Tokens | Temps | Coûts | Erreurs            │
└─────────────────────────────────────────────────────────────┘

APIs Utilisées:
- Gradium API (STT + TTS) - voix françaises
- Celeste AI (LLM) - multi-providers
  ↳ Gemini 1.5 Flash/Pro
  ↳ Claude 3.5 Sonnet
  ↳ GPT-4o / GPT-4o-mini
  ↳ Mistral, DeepSeek, etc.
```

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Cloner le repository
git clone https://github.com/didux123/storybox.git
cd storybox

# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier le template de configuration
cp .env.example .env
```

Éditer `.env` et ajouter vos clés API :

```env
# LLM (choisir un provider)
GOOGLE_API_KEY=your-google-api-key           # Pour Gemini (gratuit)
# OPENAI_API_KEY=sk-your-openai-key          # Pour GPT-4o
# ANTHROPIC_API_KEY=sk-ant-your-key          # Pour Claude

# TTS & STT
GRADIUM_API_KEY=your-gradium-api-key

# Modèle LLM (exemples)
LLM_MODEL_PATH=gemini-1.5-flash              # Rapide et gratuit
# LLM_MODEL_PATH=gpt-4o-mini                 # OpenAI économique
# LLM_MODEL_PATH=claude-3-5-sonnet-20241022  # Anthropic premium
```

**Obtenir les clés API :**
- Google (Gemini) : https://makersuite.google.com/app/apikey
- Gradium : https://gradium.ai/
- OpenAI : https://platform.openai.com/api-keys
- Anthropic : https://console.anthropic.com/

### 3. Lancer l'interface web

```bash
# Méthode 1: Via Makefile
make webapp

# Méthode 2: Commande directe
streamlit run webapp/streamlit_app.py

# Méthode 3: Script shell
./run_webapp.sh
```

L'interface s'ouvrira automatiquement dans votre navigateur à `http://localhost:8501`

## 📖 Utilisation

### Interface Web (Streamlit)

1. **Onglet "🎤 Prompt & Plan"**
   - Option 1 : Enregistrer vocalement votre demande d'histoire
   - Option 2 : Saisir manuellement le thème
   - Générer le plan de l'histoire

2. **Onglet "✍️ Génération Chapitres"**
   - Sélectionner un chapitre
   - Générer le texte
   - Écouter la narration audio

3. **Onglet "📚 Histoire Complète"**
   - Vue d'ensemble de l'histoire
   - Génération automatique de tous les chapitres
   - Écouter toute l'histoire
   - Télécharger en Markdown

4. **Onglet "⚙️ Prompts"**
   - Modifier les prompts système
   - Personnaliser le style narratif
   - Prévisualiser les prompts

### Paramètres Configurables

**Génération :**
- Nombre de chapitres : 3-10
- Température : 0.1-1.0 (créativité)
- Longueur des chapitres : Court / Moyen / Long

**Narration (TTS) :**
- 4 voix françaises pré-configurées
- Vitesse : Très rapide (-2.0) à Très lent (+2.0)
- Support IDs de voix personnalisés

## 🗂️ Structure du Projet

```
storybox/
├── app/                      # Code source principal
│   ├── llm/                  # Module LLM (Celeste)
│   │   └── celeste_llm.py    # Wrapper Celeste pour génération
│   ├── tts/                  # Modules Text-to-Speech
│   │   ├── gradium_tts.py    # TTS Gradium (actif)
│   │   └── celeste_tts.py    # TTS Celeste (deprecated)
│   ├── stt/                  # Modules Speech-to-Text
│   │   ├── gradium_stt.py    # STT Gradium (actif)
│   │   └── piper_stt.py      # STT Piper (deprecated)
│   └── utils/                # Utilitaires
│       ├── config.py         # Gestion configuration
│       └── logger.py         # Logging structuré
│
├── webapp/                   # Interface Streamlit
│   ├── streamlit_app.py      # Application principale
│   └── utils/                # Utilitaires webapp
│       └── prompt_editor.py  # Éditeur de prompts
│
├── configs/                  # Configuration
│   ├── default.yaml          # Config par défaut
│   ├── prompts.json          # Templates de prompts
│   └── llm_config.json       # Config LLM (pricing, etc.)
│
├── docs/                     # Documentation
│   ├── MODULES.md            # Documentation des modules
│   ├── API.md                # Référence API
│   └── legacy/               # Docs anciennes versions
│
├── test/                     # Tests
├── scripts/                  # Scripts utilitaires
│
├── .env                      # Configuration (ne pas commiter!)
├── .env.example              # Template de configuration
├── requirements.txt          # Dépendances Python
├── Makefile                  # Commandes pratiques
├── TODO.md                   # Roadmap et tâches
└── README.md                 # Ce fichier
```

## 📊 Métriques et Performance

L'interface Streamlit affiche en temps réel :
- **Tokens** : Input/Output par génération
- **Temps** : Durée de chaque opération
- **Coût** : Estimation basée sur les tarifs du provider
- **Erreurs** : Historique des erreurs API

**Performances typiques (Gemini Flash) :**
- Plan (5 chapitres) : ~3-5s, ~500 tokens, ~$0.0001
- Chapitre (200 mots) : ~5-8s, ~800 tokens, ~$0.0002
- Histoire complète (5 chapitres) : ~40-50s, ~4000 tokens, ~$0.001

## 🔧 Configuration Avancée

### Choix du Provider LLM

Modifier `LLM_MODEL_PATH` dans `.env` :

```env
# Google Gemini (gratuit, rapide)
LLM_MODEL_PATH=gemini-1.5-flash
LLM_MODEL_PATH=gemini-1.5-pro        # Meilleure qualité

# OpenAI
LLM_MODEL_PATH=gpt-4o-mini           # Économique
LLM_MODEL_PATH=gpt-4o                # Meilleur qualité

# Anthropic Claude
LLM_MODEL_PATH=claude-3-5-sonnet-20241022

# Mistral
LLM_MODEL_PATH=mistral-large-2411
```

### Personnalisation des Prompts

Les prompts sont dans `configs/prompts.json` :

```json
{
  "plan": {
    "system_prompt": "Instructions pour génération du plan...",
    "user_template": "Template avec variables: {theme}, {num_chapters}"
  },
  "chapter": {
    "system_prompt": "Instructions pour génération des chapitres...",
    "user_template": "Variables: {chapter_num}, {chapter_title}, {cumulative_context}..."
  }
}
```

### Voix TTS Disponibles

**Voix françaises pré-configurées :**
- Claire (zIGaffB0kKEBG_8u) - Féminine, par défaut
- Voix 2 (IB53xJtufx1sbfbt)
- Voix 3 (s0PhgjzOTRD5wo5L)
- Voix 4 (rIYDMY3dLccdauWA)
- + Possibilité d'utiliser n'importe quel ID de voix Gradium

## 🛠️ Développement

### Structure de Développement

```bash
# Installer les dépendances de dev
pip install -r requirements-dev.txt

# Lancer les tests
pytest test/

# Vérifier le code
flake8 app/ webapp/
```

### Tests Disponibles

```bash
# Test complet de la pipeline
python test/test_cloud_pipeline.py

# Test LLM uniquement
python test_celeste_local.py

# Test TTS
# (voir test/ pour plus de tests)
```

## 🗺️ Roadmap

- [x] **V0.1** - Pipeline LLM de base
- [x] **V0.2** - Intégration TTS Gradium
- [x] **V0.3** - STT Gradium + Interface Streamlit complète + Métriques
- [ ] **V0.4** - Génération streaming + histoires longues (10 min)
- [ ] **V0.5** - Structure narrative en 3 actes
- [ ] **V0.6** - Musique de fond IA (MUREKA)
- [ ] **V1.0** - Déploiement Raspberry Pi avec GPIO et LEDs

Pour plus de détails, voir [TODO.md](TODO.md)

## 📚 Documentation Complète

- **[TODO.md](TODO.md)** - Roadmap détaillée et historique des versions
- **[QUICKSTART_WEBAPP.md](QUICKSTART_WEBAPP.md)** - Guide détaillé de l'interface web
- **[docs/MODULES.md](docs/MODULES.md)** - Documentation des modules Python
- **[docs/API.md](docs/API.md)** - Référence API complète
- **[CLAUDE.md](CLAUDE.md)** - Guide pour Claude Code
- **[Expression_besoin.md](Expression_besoin.md)** - Cahier des charges (français)

## ❓ FAQ

**Q: Pourquoi l'audio ne se génère pas ?**
A: Vérifiez que `GRADIUM_API_KEY` est bien configurée dans `.env` et que le package `gradium` est installé.

**Q: Comment changer de voix ?**
A: Dans l'interface Streamlit, onglet latéral "🔊 Paramètres TTS", sélectionnez une voix ou entrez un ID personnalisé.

**Q: Puis-je utiliser sans Streamlit ?**
A: Oui, les modules (`app/llm/`, `app/tts/`, `app/stt/`) peuvent être importés directement dans vos scripts Python.

**Q: Le STT fonctionne-t-il hors ligne ?**
A: Non, V0.3 utilise l'API Gradium cloud. Pour une version locale, voir la branche `local_storybox` (deprecated).

**Q: Comment réduire les coûts ?**
A: Utilisez `gemini-1.5-flash` (gratuit jusqu'à un certain quota) ou `gpt-4o-mini` (très économique).

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir [LICENSE](LICENSE) pour plus de détails

## 👤 Auteur

**Maxence** - Créateur et mainteneur principal

---

## 📊 Statistiques du Projet

- **Version actuelle** : V0.3 (STT + TTS + Interface complète)
- **Modules Python** : 8 modules principaux
- **Lignes de code** : ~3000+
- **Providers LLM** : 4 supportés (Gemini, Claude, GPT-4o, Mistral)
- **Voix TTS** : 4 voix françaises configurées + personnalisable
- **Formats audio** : WAV, PCM, OPUS

---

**Note**: Pour une version 100% offline avec modèles locaux (Whisper/TinyLlama/Piper), voir la branche `local_storybox` et `docs/legacy/`. Cette version est deprecated car beaucoup plus lente (~33s vs ~10s).

**Bon storytelling ! 📖✨**
