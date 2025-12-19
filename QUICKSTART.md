# StoryBox - Quick Start Guide

Démarrage rapide pour tester le pipeline cloud StoryBox.

## Architecture Actuelle (main branch)

**Mode Cloud API** - Recommandé pour le développement et les tests

- **STT**: Google Speech Recognition (gratuit, nécessite internet)
- **LLM**: Celeste AI (support multi-providers: OpenAI, Anthropic, Gemini, etc.)
- **TTS**: À venir avec Gradio (bientôt disponible)

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/didux123/storybox.git
cd storybox
```

### 2. Installer les dépendances

```bash
# Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Installer les packages
pip install -r requirements.txt
```

### 3. Configuration

Créer un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditer `.env` et ajouter votre clé API OpenAI :

```env
OPENAI_API_KEY=sk-votre-clé-api-ici
LLM_MODEL_PATH=gpt-4o-mini
```

**Obtenir une clé API OpenAI:**
1. Créer un compte sur https://platform.openai.com
2. Aller dans API Keys: https://platform.openai.com/api-keys
3. Créer une nouvelle clé et la copier dans `.env`

## Test du Pipeline

Lancer le test interactif :

```bash
python test/test_cloud_pipeline.py
```

Le test va :
1. Vous demander de parler pendant 5 secondes
2. Transcrire votre audio avec Google Speech Recognition
3. Générer un plan d'histoire avec Celeste LLM
4. Générer le premier chapitre
5. Afficher les résultats

### Exemple de sortie

```
======================================================================
🎤 TEST PIPELINE CLOUD - STORYBOX
======================================================================

Pipeline:
  1. Enregistrement audio (dictée vocale)
  2. Transcription (Google Speech Recognition)
  3. Génération d'histoire (Celeste LLM)
  4. Affichage du résultat

======================================================================

──────────────────────────────────────────────────────────────────────
📝 ÉTAPE 1/3: ENREGISTREMENT
──────────────────────────────────────────────────────────────────────

Appuyez sur ENTRÉE pour commencer l'enregistrement...
🔴 ENREGISTREMENT... (parlez maintenant)
   Durée max: 5 secondes

⏹️  Enregistrement terminé

──────────────────────────────────────────────────────────────────────
📝 ÉTAPE 2/3: TRANSCRIPTION
──────────────────────────────────────────────────────────────────────

Transcription en cours...
✓ Transcription terminée en 2.3s

📝 Vous avez dit: 'Raconte-moi une histoire de pirates'

──────────────────────────────────────────────────────────────────────
💭 ÉTAPE 3/3: GÉNÉRATION D'HISTOIRE (Celeste LLM)
──────────────────────────────────────────────────────────────────────

Génération du plan de l'histoire...
✓ Plan généré en 3.2s

📖 PLAN DE L'HISTOIRE:
──────────────────────────────────────────────────────────────────────
1. Le départ
   → Le capitaine Jack et son équipage quittent le port.
2. La tempête
   → Une violente tempête met l'équipage à l'épreuve.
...
──────────────────────────────────────────────────────────────────────

Génération du chapitre 1...
✓ Chapitre 1 généré en 4.5s

📖 CHAPITRE 1:
──────────────────────────────────────────────────────────────────────
Le capitaine Jack se tenait fièrement sur le pont de son navire...
──────────────────────────────────────────────────────────────────────

======================================================================
✅ PIPELINE TERMINÉ!
======================================================================
⏱️  TEMPS TOTAL: 10.0s
   • STT (Transcription):  2.3s
   • LLM (Plan):           3.2s
   • LLM (Chapitre 1):     4.5s
   • LLM Total:            7.7s
======================================================================
```

## Prochaines Étapes

1. **TTS avec Gradio** (en attente de release)
   - Sera ajouté quand le package Celeste TTS sera disponible
   - Permettra la synthèse vocale de l'histoire

2. **Intégration Raspberry Pi**
   - Déployer sur le Pi
   - Tester avec le bouton GPIO
   - Configurer les LED de status

3. **Optimisation**
   - Ajuster les prompts pour de meilleures histoires
   - Tester différents modèles (GPT-4, Claude, Gemini)
   - Améliorer la gestion du contexte

## Branches

- **`main`**: Mode cloud API (actuel)
- **`local_storybox`**: Mode local avec modèles offline (Whisper, TinyLlama, Piper)

Pour basculer vers le mode local :

```bash
git checkout local_storybox
```

## Dépannage

### Erreur: "PyAudio not installed"

```bash
# macOS
brew install portaudio
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Erreur: "SpeechRecognition not installed"

```bash
pip install SpeechRecognition
```

### Erreur: "Celeste library not installed"

```bash
pip install 'celeste-ai[text-generation]'
```

### Erreur: "API key not found"

Vérifiez que votre `.env` contient :

```env
OPENAI_API_KEY=sk-votre-clé-ici
```

### Erreur de transcription vide

- Parlez plus fort et clairement
- Vérifiez que votre microphone fonctionne
- Vérifiez votre connexion internet (Google Speech API)

## Support

Pour plus d'informations, consultez :

- `CLAUDE.md` : Instructions détaillées pour Claude Code
- `docs/` : Documentation technique complète
- `Expression_besoin.md` : Cahier des charges complet

## Licence

MIT
