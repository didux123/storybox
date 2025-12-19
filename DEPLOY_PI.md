# Déploiement sur Raspberry Pi - Guide Rapide

Guide pour tester le pipeline Vosk + Gemini sur Raspberry Pi.

## 📋 Prérequis

- Raspberry Pi 4B avec Debian/Raspberry Pi OS
- Connexion internet (pour Gemini API)
- Micro USB (carte son USB)
- Python 3.10+

## 🚀 Installation Rapide

### 1. Connexion SSH

```bash
ssh maxence@192.168.68.120
```

### 2. Cloner le Projet

```bash
cd ~
git clone https://github.com/didux123/storybox.git
cd storybox
```

### 3. Installer les Dépendances

```bash
# Dépendances système
sudo apt update
sudo apt install -y python3-venv python3-pip git portaudio19-dev

# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer packages Python
pip install vosk celeste-ai python-dotenv pyyaml
```

### 4. Installer le Modèle Vosk

```bash
# Créer dossier pour les modèles
mkdir -p ~/models/vosk
cd ~/models/vosk

# Télécharger modèle français
wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
unzip vosk-model-small-fr-0.22.zip

# Vérifier
ls -la vosk-model-small-fr-0.22/
```

### 5. Configuration

```bash
cd ~/storybox

# Copier le template
cp .env.example .env

# Éditer avec ta clé API Gemini
nano .env
```

Dans `.env`, configure:

```env
GOOGLE_API_KEY=ta-clé-google-gemini-ici
LLM_MODEL_PATH=gemini-2.0-flash-exp
```

**Obtenir une clé Gemini:**
1. Aller sur https://makersuite.google.com/app/apikey
2. Se connecter avec compte Google
3. Créer une nouvelle clé API
4. Copier la clé dans `.env`

### 6. Vérifier le Micro

```bash
# Lister les devices audio
arecord -l

# Tester l'enregistrement (5 secondes)
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav

# Écouter
aplay /tmp/test.wav
```

**Note:** Si ton micro n'est pas sur `plughw:1,0`, édite `AUDIO_INPUT` dans `test_pi_simple.py`

## 🎬 Lancer le Test

```bash
cd ~/storybox
source .venv/bin/activate
python3 test_pi_simple.py
```

### Ce que fait le script:

1. **Enregistre 5 secondes** d'audio depuis le micro
2. **Transcrit** avec Vosk (2-3s)
3. **Génère une histoire** avec Gemini via Celeste
4. **Affiche l'histoire** dans le terminal

### Exemple de sortie:

```
======================================================================
🎤 TEST SIMPLE - RASPBERRY PI
======================================================================

Pipeline:
  1. Enregistrement audio (5 secondes)
  2. Transcription (Vosk)
  3. Génération d'histoire (Gemini via Celeste)
  4. Affichage de l'histoire

======================================================================

──────────────────────────────────────────────────────────────────────
📝 ÉTAPE 1/3: ENREGISTREMENT
──────────────────────────────────────────────────────────────────────

🔴 ENREGISTREMENT (5s)...
   Parlez maintenant!

⏹️  Enregistrement terminé

──────────────────────────────────────────────────────────────────────
📝 ÉTAPE 2/3: TRANSCRIPTION (Vosk)
──────────────────────────────────────────────────────────────────────

Chargement du modèle Vosk...
✓ Modèle chargé

Transcription en cours...
✓ Transcription terminée en 2.3s

📝 Vous avez dit: 'Raconte-moi une histoire de pirates'

──────────────────────────────────────────────────────────────────────
💭 ÉTAPE 3/3: GÉNÉRATION D'HISTOIRE (Gemini via Celeste)
──────────────────────────────────────────────────────────────────────

Initialisation de Celeste avec Gemini...
✓ Celeste initialisé (model: gemini-2.0-flash-exp)

Génération d'une histoire courte sur: 'Raconte-moi une histoire de pirates'
Patience, Gemini réfléchit...

✓ Histoire générée en 3.2s

======================================================================
📖 VOTRE HISTOIRE
======================================================================

Il était une fois un jeune pirate nommé Tom qui rêvait de trouver le
trésor légendaire de l'île aux Perroquets. Un jour, son perroquet Coco
découvrit une carte mystérieuse dans une vieille bouteille. Tom et Coco
naviguèrent pendant trois jours jusqu'à l'île. Après avoir creusé sous
le grand palmier, ils trouvèrent un coffre rempli de pièces d'or ! Tom
décida de partager le trésor avec tous les enfants du village. Depuis
ce jour, Tom est devenu le pirate le plus généreux des sept mers !

======================================================================

✅ TEST TERMINÉ!

⏱️  TEMPS TOTAL: 5.5s
   • STT (Vosk):       2.3s
   • LLM (Gemini):     3.2s

🎉 Le pipeline fonctionne!
```

## 🔧 Dépannage

### Erreur: "Vosk model not found"

```bash
# Vérifier le chemin
ls -la ~/models/vosk/vosk-model-small-fr-0.22/

# Si absent, réinstaller:
cd ~/models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
unzip vosk-model-small-fr-0.22.zip
```

### Erreur: "GOOGLE_API_KEY not found"

```bash
# Vérifier le .env
cat ~/storybox/.env | grep GOOGLE_API_KEY

# Si absent ou vide, éditer:
nano ~/storybox/.env
```

### Erreur: "Audio device not found"

```bash
# Lister les devices
arecord -l

# Adapter AUDIO_INPUT dans test_pi_simple.py
# Par exemple si micro sur carte 2:
# AUDIO_INPUT = "plughw:2,0"
```

### Transcription vide

- Parler plus fort et clairement
- Vérifier que le micro capte bien (`arecord` test)
- S'assurer d'être dans un environnement pas trop bruyant

### Erreur Gemini API

- Vérifier connexion internet: `ping google.com`
- Vérifier clé API valide
- Vérifier quota API sur https://console.cloud.google.com/

## 📊 Performance Attendue

| Étape | Temps | Notes |
|-------|-------|-------|
| **Enregistrement** | 5s | Fixe (durée configurée) |
| **Vosk STT** | 2-3s | Dépend du Pi (4B recommandé) |
| **Gemini LLM** | 3-5s | Dépend connexion internet |
| **Total** | ~10s | Pipeline complet |

## 🎯 Prochaines Étapes

Une fois que le test fonctionne:

1. ✅ **Pipeline validé** : Vosk + Gemini fonctionnels
2. 🔄 **Intégrer bouton GPIO** : Hold-to-talk
3. 🔊 **Ajouter TTS** : Attendre Celeste TTS ou utiliser Piper
4. 📖 **Histoires longues** : Implémenter génération streaming
5. 🎵 **Musique de fond** : Ajouter ambiance sonore

## 📝 Notes

- Le modèle Vosk est petit (~40MB) mais performant pour du français
- Gemini a un tier gratuit généreux (60 req/min)
- Le script peut être lancé manuellement ou via GPIO button
- Pour production, voir TODO.md pour fonctionnalités avancées

## 🆘 Support

En cas de problème:
1. Vérifier logs dans le terminal
2. Consulter QUICKSTART.md
3. Voir docs/legacy/ pour infos matériel
4. Créer une issue GitHub

---

**Dernière mise à jour**: 19 décembre 2024
