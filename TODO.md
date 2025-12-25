# StoryBox - TODO & Roadmap

## ✅ V0.2 - TTS Integration (Terminée!)

### 🎉 Session du 25 décembre 2024
**Travail effectué:**
1. ✅ Fix des paramètres Streamlit
   - Résolution bug: nombre de chapitres toujours à 10 → maintenant configurable
   - Ajout support température dans génération (plan + chapitres)
   - Ajout variable `{num_chapters}` dans prompts pour meilleure cohérence narrative

2. ✅ Intégration TTS complète avec Gradium
   - Tentative initiale avec Celeste → problèmes de compatibilité
   - **Solution finale:** API Gradium directe (module `GradiumTTS`)
   - Support complet des IDs de voix personnalisés fournis par l'utilisateur
   - Contrôle de vitesse fonctionnel (padding_bonus)
   - Tests réussis: 391KB audio généré (voix Claire)

3. ✅ Interface utilisateur TTS
   - 4 voix françaises pré-configurées + option personnalisée
   - Slider de vitesse avec 5 presets
   - Boutons 🔊 pour chaque chapitre
   - Bouton 🔊 pour histoire complète

**Commits:**
- `584411a` - fix: Remove hardcoded prompts from default.yaml
- `c2b458d` - fix: Add temperature parameter support
- `79849bf` - feat: Add num_chapters context to prompts
- `794ece0` - feat: Add voice preset selection
- `7575368` - feat: Implement Celeste TTS (abandonné)
- `bfb846e` - **feat: Replace Celeste with direct Gradium API** ⭐

### Déjà Fait ✅
- [x] Créer webapp Streamlit pour tester la pipeline de génération d'histoire
  - [x] Interface web complète avec 4 onglets (Plan, Chapitres, Histoire complète, Éditeur de prompts)
  - [x] Makefile pour lancer facilement (`make webapp`)
  - [x] Fix: Problème de troncature JSON résolu (max_tokens=4000)
  - [x] Fix: Event loop handling pour Streamlit
  - [x] Prompts configurables via `configs/prompts.json`
  - [x] Validation Pydantic pour JSON structuré

- [x] **Éditeur de prompts intégré** ✅
  - [x] Onglet "Prompts" fonctionnel
  - [x] Modification system prompt + user prompt dans l'interface
  - [x] Réglage du nombre de chapitres dynamique (slider 1-20)
  - [x] Réglage de la température (slider 0.1-2.0)
  - [x] Réglage de la longueur des chapitres (Court/Moyen/Long)

- [x] **Intégration Gradium TTS** pour la narration ✅
  - [x] Module `GradiumTTS` avec API directe (pas Celeste)
  - [x] Support des IDs de voix personnalisés (4 voix françaises configurées)
  - [x] Contrôle de vitesse via `padding_bonus` (-4.0 à +4.0)
  - [x] Boutons 🔊 pour écouter chaque chapitre individuellement
  - [x] Bouton 🔊 pour écouter toute l'histoire complète
  - [x] Format WAV pour compatibilité optimale
  - [x] GRADIUM_API_KEY configurée en .env

### Configuration TTS Actuelle
- **Voix disponibles:**
  - Claire (zIGaffB0kKEBG_8u) - féminine française ⭐ par défaut
  - Voix 2 (IB53xJtufx1sbfbt)
  - Voix 3 (s0PhgjzOTRD5wo5L)
  - Voix 4 (rIYDMY3dLccdauWA)
  - + ID personnalisé pour tester d'autres voix

- **Contrôle de vitesse:**
  - Très rapide (-2.0), Rapide (-1.0), Normale (0.0), Lent (1.0), Très lent (2.0)

## 🚧 En Cours (V0.3)

### À Faire Maintenant
- [ ] **Webapp: Ajouter métriques de performance**
  - [ ] Afficher tokens utilisés par chapitre/plan
  - [ ] Afficher temps de génération
  - [ ] Afficher coût estimé par génération
  - [ ] Afficher erreurs API (dépassement tokens, erreurs, etc.)

- [ ] **Ajouter Gradium STT** (Speech-to-Text)
  - [ ] Module `GradiumSTT` similaire à `GradiumTTS`
  - [ ] API key déjà configurée: `GRADIUM_API_KEY`
  - [ ] Doc Swagger disponible: `/Users/maxence/Documents/PYTHON/swagger/Gradium.md`
  - [ ] Intégration dans le pipeline pour enregistrement vocal

## 📋 Prochaines Fonctionnalités



- Utiliser le mode streaming des IA pour recevoir les données plus rapidement ?

### V0.3 - Histoires Longues & Génération Streaming

**Objectif** : Créer des histoires de ~10 minutes avec génération en parallèle de la narration

#### Système de Génération en 2 Temps
- [ ] **Étape 1** : Génération du plan (5 chapitres initiaux)
  - Créer le plan complet de l'histoire
  - Générer les 2-3 premiers chapitres immédiatement
  - Commencer la narration du chapitre 1
- 
- [ ] **Étape 2** : Génération chapitre par chapitre pendant narration
  - Pendant que le chapitre N est narré, générer le chapitre N+2
  - Pipeline concurrent : TTS (chapitre N) || LLM (chapitre N+2)
  - Buffer management pour éviter les latences
  - générer un chapitre puis l'autre en envoyant un context de ce qui s'est passé précédemment
    - Donner du context de ce qui s'est passé précédemment dans les chapitres précédentes
      - Demander un structured output en JSON avec : 
        - TITLE histoire (qui doit réster le même tout le temps)
        - TITLE CHAPITRE + NUMERO (envoyé suite à la toute première génération)
        - Chapitre rédigé
        - CONTEXT GLOBAL (l'IA met à jour à chaque fois un context global de l'histoire pour permettre au prochain appel d'avoir du context sur la génération à créer)
      


#### Métriques & Timing
- [ ] Calculer la durée de narration par chapitre
- [ ] Ajuster le nombre de mots par chapitre pour ~10 min total
- [ ] Logger les performances de génération vs narration

### V0.4 - Structure Narrative Améliorée

**Objectif** : Créer une structure narrative en 3 actes pour des histoires plus cohérentes

#### Structure en 3 Actes
- [ ] **Commencement** (3 chapitres)
  - Introduction du personnage principal
  - Mise en place du contexte et du monde
  - Déclencheur de l'aventure

- [ ] **Péripéties** (3-4 chapitres)
  - Défis et obstacles
  - Développement de l'intrigue
  - Rebondissements

- [ ] **Conclusion** (2-3 chapitres)
  - Résolution du conflit principal
  - Climax de l'histoire
  - Dénouement satisfaisant

#### Prompts Structurés
- [ ] Créer des templates de prompts par acte
- [ ] Ajuster le ton narratif selon la progression
- [ ] Validation de cohérence entre les actes

### V0.5 - Ambiance Sonore Immersive

**Objectif** : Ajouter de la musique de fond pour une expérience plus immersive

- [ ] Demander dans le structured output des chapitrages une ambiance ou un thème sur ce chapitre
  - Ca permettra de générer des musiques correspondantes à ce chapitre pour les jouer en même temps que la lecture


#### Musique de Fond
- [ ] générer de la musique par IA via API
  - MUREKA generator
  - Sauvegarder ces musiques en fonction de leur thème, on pourra les sélectionner au besoin pendant la lecture de l'histoire quand il y en aura beaucoup

- [ ] Intégration audio
  - Mixer musique de fond + narration TTS
  - Ajuster les niveaux (musique à 20-30% du volume narration)
  - Transitions fluides entre les morceaux

- [ ] Gestion dynamique
  - Changer la musique selon l'acte narratif
  - Fade in/out lors des transitions de chapitres
  - Silence pendant les moments clés

#### Effets Sonores (optionnel)
- [ ] Bruitages contextuels selon le thème de l'histoire
- [ ] Sons d'ambiance (nature, ville, fantastique, etc.)

## 🎯 Backlog (V1.0+)

### Interface & UX
- [ ] LED status indicators sur Raspberry Pi
  - Idle (vert fixe)
  - Listening (bleu pulsé)
  - Processing (orange pulsé)
  - Narrating (violet fixe)
  - Error (rouge clignotant)

- [ ] Bouton GPIO multi-fonction
  - Hold-to-talk pour enregistrement
  - Short press pour pause/reprise
  - Long press (3s) pour arrêt

### Performance & Qualité
- [ ] Cache des prompts et contexte
- [ ] Optimisation de la latence totale (<8s)
- [ ] A/B testing de différents modèles LLM
- [ ] Fine-tuning des prompts pour histoires jeunesse

### Fonctionnalités Avancées
- [ ] Sélection du style narratif (aventure, fantastique, science-fiction, etc.)
- [ ] Personnages récurrents avec mémoire
- [ ] Adaptation de la longueur selon l'âge (5 min pour jeunes, 10+ min pour plus grands)
- [ ] Interface web optionnelle pour configuration

### Déploiement Raspberry Pi
- [ ] Script d'installation automatique
- [ ] Service systemd pour démarrage automatique
- [ ] Gestion des logs et rotation
- [ ] Métriques de performance

## 🔬 Recherche & Expérimentation

- [ ] Tester différents providers LLM (GPT-4o vs Claude vs Gemini)
- [ ] Comparer qualité narrative entre modèles
- [ ] Évaluer coûts API par histoire générée
- [ ] Explorer Celeste STT quand disponible (remplacer Google Speech)

## 📝 Notes Techniques

### Génération Streaming (V0.3)
```
Timeline:
0s    : Début enregistrement
5s    : Fin enregistrement, début STT
7s    : STT terminé, début génération plan
10s   : Plan généré, début génération chapitres 1-3
15s   : Chapitres 1-3 prêts, début narration chapitre 1
15-60s: Narration ch1 || Génération ch4
60-120s: Narration ch2 || Génération ch5
...
```

### Structure Narrative (V0.4)
```python
story_structure = {
    "commencement": {
        "chapters": 3,
        "tone": "introduction",
        "music": "calm_beginning.mp3"
    },
    "peripéties": {
        "chapters": 4,
        "tone": "adventure",
        "music": "action_theme.mp3"
    },
    "conclusion": {
        "chapters": 3,
        "tone": "resolution",
        "music": "peaceful_ending.mp3"
    }
}
```

### Musique de Fond (V0.5)
```python
# Mixer audio avec pydub ou sounddevice
from pydub import AudioSegment
from pydub.playback import play

narration = AudioSegment.from_wav("chapter1.wav")
music = AudioSegment.from_mp3("background.mp3") - 20  # -20dB
combined = narration.overlay(music, loop=True)
```

## 🎨 Idées Futures

- Thèmes saisonniers (Noël, Halloween, etc.)
- Histoires interactives avec choix
- Support multi-langues
- Export audio des histoires générées
- Partage communautaire d'histoires
- Mode "histoire du soir" avec timing progressif vers le sommeil

---

**Dernière mise à jour** : 25 décembre 2024
**Version actuelle** : V0.2 (TTS Gradium intégré)
**Prochaine release** : V0.3 (Génération streaming + STT Gradium)

## 📦 Modules Implémentés

### LLM
- **CelesteLLM** (`app/llm/celeste_llm.py`)
  - Génération de plans d'histoires structurés (JSON)
  - Génération de chapitres avec contexte cumulatif
  - Support multi-providers (Gemini, Claude, GPT-4o via Celeste AI)
  - Gestion de la température et des tokens

### TTS (Text-to-Speech)
- **GradiumTTS** (`app/tts/gradium_tts.py`) ✅
  - API Gradium directe (pas via Celeste)
  - Support voix personnalisées (IDs de voix)
  - Contrôle de vitesse (padding_bonus -4.0 à +4.0)
  - Format WAV optimisé

- **CelesteTTS** (`app/tts/celeste_tts.py`) - Deprecated
  - Remplacé par GradiumTTS pour meilleure compatibilité

### STT (Speech-to-Text)
- **PiperSTT** (`app/stt/piper_stt.py`) - À remplacer
  - Actuellement pour Raspberry Pi (local)
  - **TODO:** Remplacer par GradiumSTT pour cohérence

### Webapp
- **Streamlit UI** (`webapp/streamlit_app.py`)
  - 4 onglets: Plan, Chapitres, Histoire complète, Éditeur de prompts
  - Configuration TTS avec sélection de voix et vitesse
  - Boutons audio pour écouter chapitres/histoire
  - Édition en temps réel des prompts
