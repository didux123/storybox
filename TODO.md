# StoryBox - TODO & Roadmap

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
  - Input : `model_api_key` (str, optional) - Modèle LLM API KEY (Uniquement si un model est spécifié dans le parametre 'model')
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
