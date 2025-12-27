# Documentation StoryBox IA

> Documentation technique complète pour StoryBox V0.3

## 📚 Table des Matières

### Documentation Principale

- **[MODULES.md](MODULES.md)** - Documentation complète des modules Python
  - LLM (CelesteLLM)
  - TTS (GradiumTTS)
  - STT (GradiumSTT)
  - Utils (Config, Logger)
  - Exemples d'usage

- **[API.md](API.md)** - Référence API technique
  - Signatures de fonctions
  - Types et modèles
  - Paramètres détaillés
  - Gestion des erreurs
  - Exemples complets

### Guides Utilisateur

- **[../README.md](../README.md)** - Vue d'ensemble du projet
- **[../QUICKSTART_WEBAPP.md](../QUICKSTART_WEBAPP.md)** - Guide d'utilisation de l'interface Streamlit
- **[../TODO.md](../TODO.md)** - Roadmap et historique des versions

### Documentation Technique

- **[../CLAUDE.md](../CLAUDE.md)** - Guide pour Claude Code
- **[../Expression_besoin.md](../Expression_besoin.md)** - Cahier des charges (français)

### Documentation Historique

- **[legacy/](legacy/)** - Documentation des versions précédentes
  - HARDWARE.md - Configuration matérielle Raspberry Pi
  - RASPBERRY_PI_SETUP.md - Installation sur Pi
  - MAC_DEVELOPMENT.md - Développement local sur Mac
  - MODULES.md - Ancienne documentation des modules
  - workflow.md - Ancien workflow de déploiement

---

## 🚀 Par Où Commencer ?

### 1. **Débutant - Découvrir StoryBox**

Commencez par ces fichiers dans cet ordre :

1. [../README.md](../README.md) - Vue d'ensemble et installation
2. [../QUICKSTART_WEBAPP.md](../QUICKSTART_WEBAPP.md) - Premier lancement
3. [../TODO.md](../TODO.md) - Fonctionnalités disponibles

### 2. **Développeur - Utiliser les Modules**

Pour intégrer StoryBox dans votre code :

1. [MODULES.md](MODULES.md) - Comprendre les modules
2. [API.md](API.md) - Référence technique
3. [../configs/](../configs/) - Configuration

**Exemple minimal :**
```python
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config
import asyncio

config = get_config()
llm = CelesteLLM(config.llm)
plan = asyncio.run(llm.generate_story_plan("Un robot", 5))
print(plan.theme)
```

### 3. **Contributeur - Développer sur StoryBox**

Pour contribuer au projet :

1. [../README.md#-développement](../README.md#-développement) - Setup dev
2. [MODULES.md](MODULES.md) - Architecture des modules
3. [API.md](API.md) - Standards API
4. [../TODO.md](../TODO.md) - Fonctionnalités à venir

---

## 📖 Documentation par Module

### Module LLM (Génération de Texte)

**Fichier:** `app/llm/celeste_llm.py`

**Voir:**
- [MODULES.md#llm](MODULES.md#-module-llm) - Guide d'utilisation
- [API.md#llm-api](API.md#llm-api) - Référence complète

**Fonctionnalités:**
- Génération de plans d'histoires (JSON structuré)
- Génération de chapitres avec contexte
- Support multi-providers (Gemini, Claude, GPT-4o)

### Module TTS (Narration Audio)

**Fichier:** `app/tts/gradium_tts.py`

**Voir:**
- [MODULES.md#tts](MODULES.md#-module-tts-text-to-speech) - Guide d'utilisation
- [API.md#tts-api](API.md#tts-api) - Référence complète

**Fonctionnalités:**
- 4 voix françaises naturelles
- Contrôle de vitesse (-4.0 à +4.0)
- Formats: WAV, PCM, OPUS

### Module STT (Transcription Vocale)

**Fichier:** `app/stt/gradium_stt.py`

**Voir:**
- [MODULES.md#stt](MODULES.md#-module-stt-speech-to-text) - Guide d'utilisation
- [API.md#stt-api](API.md#stt-api) - Référence complète

**Fonctionnalités:**
- Transcription audio → texte
- Auto-détection des formats
- Support WAV, PCM, OPUS

### Module Utils (Utilitaires)

**Fichiers:**
- `app/utils/config.py` - Configuration
- `app/utils/logger.py` - Logging

**Voir:**
- [MODULES.md#utils](MODULES.md#-module-utils) - Guide d'utilisation
- [API.md#utils-api](API.md#utils-api) - Référence complète

---

## 🗂️ Structure de la Documentation

```
docs/
├── README.md           # Ce fichier - index de la doc
├── MODULES.md          # Documentation des modules Python
├── API.md              # Référence API technique
└── legacy/             # Documentation historique
    ├── HARDWARE.md
    ├── RASPBERRY_PI_SETUP.md
    ├── MAC_DEVELOPMENT.md
    ├── MODULES.md
    └── workflow.md

Racine du projet:
├── README.md           # Vue d'ensemble
├── TODO.md             # Roadmap
├── QUICKSTART_WEBAPP.md  # Guide Streamlit
├── CLAUDE.md           # Guide Claude Code
├── Expression_besoin.md  # Cahier des charges
└── configs/            # Configuration YAML/JSON
```

---

## 🔍 Recherche Rapide

### Recherche par Fonctionnalité

| Fonctionnalité | Documentation |
|----------------|---------------|
| Installer StoryBox | [README.md](../README.md#-démarrage-rapide) |
| Lancer Streamlit | [QUICKSTART_WEBAPP.md](../QUICKSTART_WEBAPP.md) |
| Générer une histoire (code) | [MODULES.md](MODULES.md#-exemples-dusage-complet) |
| Configurer les voix TTS | [README.md](../README.md#voix-tts-disponibles) |
| Changer de provider LLM | [README.md](../README.md#choix-du-provider-llm) |
| Personnaliser les prompts | [README.md](../README.md#personnalisation-des-prompts) |
| Comprendre l'architecture | [README.md](../README.md#-architecture) |
| Référence API complète | [API.md](API.md) |
| Gestion des erreurs | [API.md](API.md#gestion-des-erreurs) |

### Recherche par Cas d'Usage

| Cas d'Usage | Exemple |
|-------------|---------|
| Pipeline complète async | [MODULES.md#pipeline-complète](MODULES.md#pipeline-complète) |
| Pipeline simplifiée sync | [API.md#pipeline-simplifiée-synchrone](API.md#pipeline-simplifiée-synchrone) |
| Narration audio seulement | [MODULES.md#tts](MODULES.md#-module-tts-text-to-speech) |
| Transcription vocale | [MODULES.md#stt](MODULES.md#-module-stt-speech-to-text) |
| Génération LLM uniquement | [MODULES.md#llm](MODULES.md#-module-llm) |

---

## 🆕 Nouveautés V0.3

**STT Gradium intégré :**
- Enregistrement vocal dans Streamlit
- Transcription automatique
- Pré-remplissage du prompt

**Métriques complètes :**
- Tokens utilisés (input/output)
- Temps de génération
- Coût estimé ($/génération)
- Dashboard global

**Documentation complète :**
- MODULES.md créé
- API.md créé
- README.md mis à jour
- TODO.md réorganisé

Voir [TODO.md](../TODO.md) pour l'historique complet.

---

## 🔗 Liens Externes

### APIs Utilisées

- **Celeste AI** : https://github.com/withceleste/celeste-python
- **Gradium** : https://gradium.ai/docs
- **Streamlit** : https://docs.streamlit.io/

### Providers LLM

- **Google Gemini** : https://ai.google.dev/
- **OpenAI** : https://platform.openai.com/docs
- **Anthropic Claude** : https://docs.anthropic.com/

---

## 📝 Contribuer à la Documentation

Pour améliorer la documentation :

1. **Signaler une erreur** : Créer une issue sur GitHub
2. **Proposer une amélioration** : Pull request bienvenue
3. **Ajouter des exemples** : Très apprécié !

**Standards de documentation :**
- Markdown (CommonMark)
- Exemples de code testés
- Français pour les guides utilisateur
- Anglais acceptable pour la doc technique

---

**Dernière mise à jour** : 25 décembre 2024 - V0.3

**Besoin d'aide ?** Consultez la [FAQ](../README.md#-faq) ou créez une issue GitHub.
