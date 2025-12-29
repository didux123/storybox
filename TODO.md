# StoryBox - TODO & Roadmap

## 🔥 TOP PRIORITÉ

- [ ] **Améliorer la gestion des erreurs du backend**
  - Logger les exceptions complètes avec traceback
  - Retourner les détails d'erreur dans la réponse API (avec stacktrace si mode debug)
  - Capturer les erreurs spécifiques: API keys invalides, timeouts, rate limits
  - Ajouter des logs structurés pour debugging
  - Identifier pourquoi "Failed to generate story plan" sans plus de détails

---

## 🚧 Prochaines Étapes (V0.4+)

### V0.4 - API Backend & Architecture REST

**Status: 🟢 En cours - Docker stack opérationnel**

#### ✅ Fait (29 décembre 2024)
- [x] **Backend API (FastAPI)** créé et fonctionnel
  - API REST avec endpoint `POST /api/v1/generate-story`
  - Documentation Swagger auto-générée (`/docs`)
  - Support CORS configuré (JSON array format)
  - Health check endpoint: `GET /api/v1/health`

- [x] **Dockerisation complète**
  - Backend Dockerfile (multi-stage, Python 3.12-slim, 548MB)
  - Frontend Dockerfile (Streamlit, Python 3.12-slim, 827MB)
  - docker-compose.yml avec 4 services (backend, frontend, PostgreSQL, Redis)
  - Variables d'environnement via `.env`
  - Stack opérationnel: http://localhost:8000 (backend), http://localhost:8501 (frontend)

- [x] **Configuration & Sécurité**
  - Pydantic Settings avec validation
  - JWT authentication structure (backend/core/security.py)
  - Rate limiting middleware (in-memory, Redis-ready)
  - CORS origins fixé (format JSON array)

- [x] **Service Layer**
  - StoryService orchestrant LLM + TTS + STT
  - Métriques automatiques (tokens, cost, duration)
  - Support output_format: text ou audio (base64)

#### 🔴 À corriger
- [ ] Backend génère des erreurs vagues: "Failed to generate story plan"
  - Besoin de logs détaillés
  - Tracer l'origine exacte des erreurs (API keys? Timeout? Format?)

#### 🔵 Reste à faire
- [ ] **Tester le backend en profondeur**
  - Identifier l'erreur "Failed to generate story plan"
  - Tester génération complète avec 3+ chapitres
  - Valider output_format: text ET audio
  - Tester avec différentes voix TTS

- [ ] **Connecter Frontend Streamlit au Backend**
  - Modifier Streamlit pour appeler http://backend:8000 au lieu des APIs directes
  - Ajouter variable d'environnement BACKEND_API_URL
  - Gérer les erreurs API côté frontend
  - Afficher les métriques retournées par le backend

- [ ] **Multi-Architecture Docker**
  - Support arm64 (Mac M1/M2, Raspberry Pi)
  - GitHub Actions pour build automatique
  - Push vers DockerHub/GHCR

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

### V0.6 - Structure Narrative des histoires
**Objectif** : Créer une structure narrative plus cohérente

- [ ] **Situation initiale** 
  - point de départ de l'histoire qui présente l'univers, les personnages et le contexte dans lequel se déroule l'intrigue.
  - Cette étape permet d'établir le cadre de la narration et de donner des informations nécessaires au public pour qu'il puisse comprendre la suite.
  - La situation initiale sert à mettre en place l'équilibre du récit. Les personnages ont des objectifs, des désirs, des peurs et des conflits latents qui sont progressivement révélés au fil de l'histoire.


- [ ] **L'élément perturbateur** 
  - L'élément modificateur est l'événement qui perturbe l'équilibre initial de l'histoire et qui donne lieu à une action. C'est souvent un élément inattendu, qui change la donne et qui produit une situation conflictuelle.
  - Ce critère peut prendre différentes formes, comme une rencontre fortuite, un accident, une révélation, une découverte, une trahison, un départ, un retour, un changement de situation, etc. C'est un moment crucial dans la structure narrative, car il marque le début de l'intrigue et lance l'action.

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

- [ ] **Ajoute API Client**
  - Route pour récupérer les métriques utilisateur

---

## 🐳 Infrastructure & Déploiement

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



## 🎨 Idées Futures

- Thèmes saisonniers (Noël, Halloween, etc.)
- Histoires interactives avec choix multiples
- Support multi-langues (anglais, espagnol)
- Mode "histoire du soir" avec timing progressif vers le sommeil
- Génération d'illustrations par IA (DALL-E, Midjourney)
- Personnages récurrents avec mémoire entre sessions
- Adaptation de la longueur selon l'âge (5 min pour jeunes, 10+ min pour plus grands)

---

