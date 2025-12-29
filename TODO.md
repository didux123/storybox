# StoryBox - TODO & Roadmap

## ✅ V0.3 - STT Integration (Terminée!)

### 🎉 Session du 25 décembre 2024 - Partie 2
**Travail effectué:**

1. ✅ **Intégration STT complète avec Gradium**
   - Module `GradiumSTT` créé (`app/stt/gradium_stt.py`)
   - API Gradium directe pour transcription audio
   - Support des formats WAV, PCM, OPUS
   - Méthodes async/sync pour flexibilité
   - Auto-détection du format audio depuis l'extension de fichier

2. ✅ **Interface utilisateur STT dans Streamlit**
   - Widget d'enregistrement audio natif (st.audio_input)
   - Bouton de transcription avec indicateur de progression
   - Affichage du texte transcrit avec métriques (temps de transcription)
   - Pré-remplissage automatique du champ de prompt avec le texte transcrit
   - Option pour effacer la transcription
   - Double option : enregistrement vocal OU saisie manuelle

3. ✅ **Métriques de performance déjà implémentées**
   - Affichage des tokens utilisés (input/output) par chapitre et plan
   - Temps de génération affiché pour chaque opération
   - Coût estimé calculé et affiché ($/génération)
   - Dashboard global avec métriques cumulatives
   - Tracking des erreurs API avec historique

**Architecture:**
```
Utilisateur → 🎤 Enregistrement vocal → GradiumSTT → Texte transcrit
                                                          ↓
                                                    Génération plan (CelesteLLM)
                                                          ↓
                                                    Génération chapitres
                                                          ↓
                                                    Narration (GradiumTTS) → 🔊 Audio
```

---

## ✅ V0.2 - TTS Integration (Terminée!)

### 🎉 Session du 25 décembre 2024 - Partie 1
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

**Commits V0.2:**
- `584411a` - fix: Remove hardcoded prompts from default.yaml
- `c2b458d` - fix: Add temperature parameter support
- `79849bf` - feat: Add num_chapters context to prompts
- `794ece0` - feat: Add voice preset selection
- `7575368` - feat: Implement Celeste TTS (abandonné)
- `bfb846e` - feat: Replace Celeste with direct Gradium API ⭐

---

## 🚀 Fonctionnalités Actuelles (V0.3)

### Webapp Streamlit Complète
- [x] Interface web avec 4 onglets fonctionnels
  - 🎤 **Prompt & Plan** : Enregistrement vocal OU saisie manuelle + génération du plan
  - ✍️ **Génération Chapitres** : Génération chapitre par chapitre avec contexte
  - 📚 **Histoire Complète** : Vue d'ensemble + génération automatique de tous les chapitres
  - ⚙️ **Prompts** : Éditeur de prompts en temps réel
- [x] Métriques de performance complètes
  - Tokens (input/output) par génération
  - Temps de génération
  - Coût estimé ($/génération)
  - Dashboard cumulatif
  - Historique des erreurs API
- [x] Export de l'histoire en Markdown
- [x] Makefile pour lancement facile (`make webapp`)

### Modules IA Complets
- [x] **LLM** : CelesteLLM avec support multi-providers (Gemini, Claude, GPT-4o)
- [x] **TTS** : GradiumTTS avec 4 voix françaises + vitesse configurable
- [x] **STT** : GradiumSTT avec enregistrement audio intégré
- [x] Configuration centralisée (YAML + JSON + .env)
- [x] Logging structuré

### Configuration
- [x] Prompts éditables via interface Streamlit
- [x] Paramètres de génération ajustables (température, longueur, nb chapitres)
- [x] Voix TTS sélectionnable avec IDs personnalisés
- [x] Validation Pydantic pour JSON structuré

---

## 🚧 Prochaines Étapes (V0.4+)

### V0.4 - API Backend & Architecture REST

**Objectif** : Séparation Frontend/Backend avec API professionnelle

#### Architecture API REST
- [ ] **Backend API (FastAPI)**
  - Créer API REST indépendante
  - Endpoint principal: `POST /api/v1/generate-story`
  - Documentation OpenAPI/Swagger automatique
  - Support CORS pour frontend

- [ ] **Authentification & Sécurité**
  - Authentification par token (JWT)
  - Rate limiting par token
  - Validation des inputs (Pydantic)
  - Logs sécurisés des requêtes

- [ ] **Paramètres API**
  - Input : `prompt` (str) - Thème de l'histoire
  - Input : `model` (str, optional) - Modèle LLM (default: mistral-large-2411)
  - Input : `output_format` (enum) - "text" ou "audio"
  - Input : `num_chapters` (int, optional) - Nombre de chapitres
  - Input : `voice_id` (str, optional) - ID voix TTS (si format audio)
  - Input : `temperature` (float, optional) - Température génération
  - Output : Histoire (JSON ou WAV selon format)

- [ ] **Séparation Frontend/Backend**
  - Streamlit reste frontend (parfait tel quel)
  - Streamlit consomme l'API backend
  - Communication via HTTP REST
  - Variables d'environnement pour URL API

#### Response Format
```json
{
  "status": "success",
  "data": {
    "story_id": "uuid",
    "theme": "Un robot qui découvre les émotions",
    "chapters": [...],
    "output": "base64_audio" | "text_content",
    "format": "audio" | "text",
    "metadata": {
      "model": "mistral-large-2411",
      "tokens": 4521,
      "duration": 45.2,
      "cost": 0.0034
    }
  }
}
```

---

### V0.5 - Génération Streaming Optimisée

**Objectif** : Pipeline parallèle pour minimiser latence totale

#### Streaming Pipeline
- [ ] **Génération + Audio en Parallèle**
  - Chapitre 1 généré → Audio streaming immédiat (Gradium)
  - Pendant audio Ch1 → Génération Ch2 en arrière-plan
  - Pipeline concurrent : Audio(N) || Generate(N+1)
  - Envoi streaming au client via WebSocket

- [ ] **WebSocket pour Streaming Temps Réel**
  - Endpoint WebSocket : `/ws/stream-story`
  - Events : `chapter_generated`, `audio_chunk`, `complete`
  - Buffer management côté serveur
  - Gestion reconnexion automatique

- [ ] **Buffer Management Intelligent**
  - Préchargement des 2 prochains chapitres
  - Calcul durée narration par chapitre
  - Ajustement dynamique du buffer
  - Métriques de performance temps réel

#### Optimisation Latence
- [ ] Calculer la durée de narration par chapitre
- [ ] Ajuster le nombre de mots pour ~10 min total
- [ ] Logger les performances de génération vs narration
- [ ] Précharger les chapitres suivants

**Timeline estimée (streaming) :**
```
0s    : Client envoie prompt
2s    : Plan généré
5s    : Ch1 généré → Audio streaming START
10s   : Premier audio chunk reçu par client
5-60s : Audio Ch1 streaming || Génération Ch2
60-120s: Audio Ch2 streaming || Génération Ch3
...
Latence perçue : ~10s au lieu de ~50s (5x plus rapide!)
```

---

## 📋 Backlog (V0.6+)

### V0.6 - Structure Narrative en 3 Actes
**Objectif** : Créer une structure narrative plus cohérente

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

- [ ] Prompts structurés par acte
- [ ] Validation de cohérence entre les actes


### V0.7 - Ambiance Sonore Immersive
**Objectif** : Ajouter de la musique de fond

- [ ] Demander dans le structured output une ambiance par chapitre
- [ ] Générer de la musique par IA (MUREKA generator)
- [ ] Sauvegarder les musiques par thème
- [ ] Mixer musique de fond + narration TTS
- [ ] Ajuster les niveaux (musique à 20-30% du volume narration)
- [ ] Transitions fluides (fade in/out)

### V0.8 - Multiples Voix TTS
**Objectif** : Dialogues naturels avec plusieurs voix

- [ ] **Détection des Dialogues**
  - Parser le texte pour identifier les dialogues
  - Détection automatique des personnages
  - Attribution voix par personnage

- [ ] **Génération Multi-Voix**
  - Générer chaque dialogue avec voix différente
  - Assembler les segments audio
  - Transitions fluides entre voix
  - Respect du timing et de l'intonation

---

## 🎯 V1.0 - CMS Admin & User Management

**Objectif** : Plateforme SaaS complète avec gestion utilisateurs

### CMS Admin Dashboard
- [ ] **Interface Admin (React/Vue.js)**
  - Dashboard principal avec métriques globales
  - Gestion utilisateurs API
  - Création/révocation tokens JWT
  - Configuration quotas par utilisateur
  - Gestion des modèles LLM disponibles

- [ ] **Base de Données**
  - PostgreSQL pour persistance
  - Tables : users, api_tokens, stories, usage_metrics
  - Migrations avec Alembic
  - Backups automatiques

### Tracking & Analytics
- [ ] **Métriques par Utilisateur**
  - Nombre d'histoires générées
  - Tokens consommés (input/output)
  - Coûts API par provider
  - Temps de génération moyens
  - Taux de succès/erreur

- [ ] **Facturation & Crédits**
  - Système de crédits virtuels
  - Packages de crédits (Starter, Pro, Enterprise)
  - Facturation mensuelle automatique
  - Webhooks pour paiements (Stripe)
  - Historique des transactions

### API Management
- [ ] **Quotas & Limites**
  - Rate limiting personnalisé par user
  - Limites de tokens par mois
  - Limites de coût maximum
  - Alertes email avant dépassement

- [ ] **Monitoring**
  - Dashboard temps réel (Grafana)
  - Logs centralisés (ELK Stack)
  - Alertes incidents (PagerDuty)
  - Métriques de performance

---

## 🐳 Infrastructure & Déploiement

### Docker (V0.4 - Priorité Haute)
- [ ] **Dockerisation Backend API**
  - Dockerfile optimisé multi-stage
  - Image Python 3.10+ Alpine
  - Dépendances figées (requirements.txt)
  - Healthcheck endpoint

- [ ] **Dockerisation Frontend Streamlit**
  - Dockerfile séparé pour Streamlit
  - Configuration via variables d'environnement
  - Port 8501 exposé

- [ ] **Docker Compose**
  - `docker-compose.yml` pour stack complète
  - Services : backend, frontend, postgres, redis
  - Volumes pour persistance
  - Réseau interne pour communication
  - Variables d'environnement centralisées

- [ ] **Multi-Architecture**
  - Support amd64 (serveurs cloud)
  - Support arm64 (Mac M1/M2, Raspberry Pi)
  - GitHub Actions pour build automatique
  - Push vers DockerHub/GHCR

### CI/CD
- [ ] **GitHub Actions**
  - Tests automatiques (pytest)
  - Linting (flake8, mypy)
  - Build Docker images
  - Déploiement automatique (staging/prod)

- [ ] **Déploiement**
  - Déploiement sur cloud (AWS/GCP/Azure)
  - Kubernetes manifests (optionnel)
  - Monitoring et logs
  - Rollback automatique en cas d'erreur

---

## 📦 Modules Implémentés

### LLM (app/llm/)
- ✅ **CelesteLLM** (`celeste_llm.py`)
  - Génération de plans d'histoires structurés (JSON avec Pydantic)
  - Génération de chapitres avec contexte cumulatif
  - Support multi-providers (Gemini, Claude, GPT-4o via Celeste AI)
  - Gestion de la température et des tokens
  - Prompts configurables via `configs/prompts.json`

### TTS - Text-to-Speech (app/tts/)
- ✅ **GradiumTTS** (`gradium_tts.py`)
  - API Gradium directe (pas via Celeste)
  - Support voix personnalisées (IDs de voix Gradium)
  - Contrôle de vitesse (padding_bonus -4.0 à +4.0)
  - Format WAV optimisé
  - Méthodes async + wrappers sync

- ⚠️ **CelesteTTS** (`celeste_tts.py`) - Deprecated
  - Remplacé par GradiumTTS pour meilleure compatibilité
  - Conservé pour référence

### STT - Speech-to-Text (app/stt/)
- ✅ **GradiumSTT** (`gradium_stt.py`)
  - API Gradium directe pour transcription
  - Support WAV, PCM, OPUS
  - Streaming audio par chunks (80ms à 24kHz)
  - Auto-détection du format
  - Méthodes async + wrappers sync

- ⚠️ **PiperSTT** (`piper_stt.py`) - À supprimer
  - Ancien module pour Raspberry Pi (local)
  - Non utilisé, remplacé par GradiumSTT

### Utils (app/utils/)
- ✅ **Config** (`config.py`)
  - Chargement centralisé depuis `configs/default.yaml`
  - Support des variables d'environnement
  - Validation des chemins et paramètres

- ✅ **Logger** (`logger.py`)
  - Logging structuré avec rotation
  - Niveaux configurables
  - Format JSON pour analyse

### Webapp (webapp/)
- ✅ **Streamlit UI** (`streamlit_app.py`)
  - 4 onglets fonctionnels (Prompt & Plan, Chapitres, Histoire complète, Prompts)
  - Enregistrement vocal intégré (STT)
  - Narration audio intégrée (TTS)
  - Configuration TTS avec sélection de voix et vitesse
  - Métriques de performance complètes
  - Édition en temps réel des prompts
  - Export Markdown

- ✅ **Prompt Editor** (`utils/prompt_editor.py`)
  - Chargement/sauvegarde de `configs/prompts.json`
  - Validation des templates

---

## 🔧 Configuration Actuelle

### TTS - Voix Disponibles
- **Claire** (zIGaffB0kKEBG_8u) - féminine française ⭐ par défaut
- **Voix 2** (IB53xJtufx1sbfbt) - française
- **Voix 3** (s0PhgjzOTRD5wo5L) - française
- **Voix 4** (rIYDMY3dLccdauWA) - française
- **ID personnalisé** - pour tester d'autres voix Gradium

### TTS - Contrôle de Vitesse
- Très rapide (-2.0)
- Rapide (-1.0)
- Normale (0.0)
- Lent (1.0)
- Très lent (2.0)

### STT - Formats Supportés
- WAV (recommandé pour Streamlit)
- PCM (24kHz, 16-bit, mono)
- OPUS

### LLM - Providers Supportés
- Gemini 1.5 Flash (rapide, gratuit)
- Gemini 1.5 Pro (meilleure qualité)
- GPT-4o Mini (OpenAI)
- Claude 3.5 Sonnet (Anthropic)

---

## 🎨 Idées Futures

- Thèmes saisonniers (Noël, Halloween, etc.)
- Histoires interactives avec choix multiples
- Support multi-langues (anglais, espagnol)
- Export audio complet des histoires générées
- Partage communautaire d'histoires
- Mode "histoire du soir" avec timing progressif vers le sommeil
- Génération d'illustrations par IA (DALL-E, Midjourney)
- Personnages récurrents avec mémoire entre sessions
- Adaptation de la longueur selon l'âge (5 min pour jeunes, 10+ min pour plus grands)

---

**Dernière mise à jour** : 25 décembre 2024
**Version actuelle** : V0.3 (STT + TTS + Métriques complets)
**Prochaine release** : V0.4 (Génération streaming + histoires longues)

## 📊 Statistiques du Projet

- **Modules Python** : 8 modules principaux
- **Lignes de code** : ~3000+ lignes
- **APIs intégrées** : Celeste AI (LLM), Gradium (TTS/STT)
- **Providers LLM** : 4 (Gemini, Claude, GPT-4o, OpenAI)
- **Voix TTS** : 4 voix françaises configurées + personnalisable
- **Formats audio** : WAV, PCM, OPUS
- **Interface** : Streamlit (4 onglets)
