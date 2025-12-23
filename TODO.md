# StoryBox - TODO & Roadmap

## 🚧 En Cours (V0.2)

### Déjà Fait ✅
- [x] Créer webapp Streamlit pour tester la pipeline de génération d'histoire
  - [x] Interface web complète avec 3 onglets (Plan, Chapitres, Histoire complète)
  - [x] Makefile pour lancer facilement (`make webapp`)
  - [x] Fix: Problème de troncature JSON résolu (max_tokens=4000)
  - [x] Fix: Event loop handling pour Streamlit
  - [x] Prompts configurables via `configs/prompts.json`
  - [x] Validation Pydantic pour JSON structuré

### À Faire Maintenant
- [ ] **Webapp: Ajouter métriques de performance**
  - [ ] Afficher tokens utilisés par chapitre/plan
  - [ ] Afficher temps de génération
  - [ ] Afficher coût estimé par génération
  - [ ] Afficher erreurs Celeste (dépassement tokens, erreurs API, etc.)

- [ ] **Webapp: Éditeur de prompts intégré**
  - [ ] Implémenter l'onglet "Prompts" (code disponible dans `webapp/TODO_PROMPTS.md`)
  - [ ] Pouvoir modifier system prompt + user prompt dans l'interface
  - [ ] Réglage du nombre de chapitres dynamique

- [ ] **Intégrer Celeste TTS** pour la narration
  - Celeste TTS est disponible et fonctionnel
  - À intégrer dans le pipeline

- [ ] **Ajouter Gradium STT**
  - API key configurée en .env: `GRADIUM_API_KEY`
  - Doc Swagger disponible: `/Users/maxence/Documents/PYTHON/swagger/gradium_swagger.json`
  - Note: Pour TTS, utiliser Celeste (qui supporte aussi Gradium)

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

**Dernière mise à jour** : 19 décembre 2024
**Version actuelle** : V0.1 (Cloud API de base)
**Prochaine release** : V0.2 (avec Celeste TTS)
