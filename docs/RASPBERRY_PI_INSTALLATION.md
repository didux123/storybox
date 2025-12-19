# Guide d'installation StoryBox sur Raspberry Pi 4B

## Prérequis matériel

- Raspberry Pi 4B (4GB RAM minimum recommandé)
- Carte microSD 64GB minimum
- Micro USB pour l'audio d'entrée
- Sortie audio jack 3.5mm ou HDMI
- Bouton poussoir connecté au GPIO 17 (avec résistance pull-up/down)
- Connexion réseau (WiFi ou Ethernet)

## Prérequis logiciel

- Raspberry Pi OS (Debian Bookworm ou Trixie)
- Accès SSH activé
- Utilisateur avec droits sudo

---

## Installation automatique (recommandée)

### Méthode rapide

```bash
# Sur le Raspberry Pi, télécharger et lancer le script d'installation
curl -fsSL https://raw.githubusercontent.com/didux123/storybox/main/scripts/install_pi_complete.sh -o install.sh
chmod +x install.sh
./install.sh
```

Le script va:
1. Installer toutes les dépendances système
2. Cloner le projet depuis GitHub
3. Configurer l'environnement Python
4. Télécharger les modèles IA (Whisper, Llama, Piper)
5. Créer la configuration .env
6. Tester l'installation

**Durée estimée:** 30-45 minutes (selon la connexion Internet)

---

## Installation manuelle (étape par étape)

### Étape 1: Mise à jour du système

```bash
# Se connecter au Raspberry Pi en SSH
ssh votre_utilisateur@adresse_ip_du_pi

# Mettre à jour le système
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

**Pourquoi:** Assurer que tous les paquets système sont à jour pour éviter les incompatibilités.

### Étape 2: Installation des dépendances système

```bash
# Installer les outils de compilation et développement
sudo apt install -y \
  git \
  cmake \
  build-essential \
  swig

# Installer les bibliothèques audio
sudo apt install -y \
  libsndfile1 \
  portaudio19-dev \
  sox \
  alsa-utils

# Installer Python et ses outils de développement
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev
```

**Détails des paquets:**
- `git`: Gestionnaire de versions pour cloner le projet
- `cmake`: Outil de build nécessaire pour compiler llama.cpp
- `build-essential`: Compilateur GCC et outils de développement
- `swig`: Générateur d'interfaces pour Python (nécessaire pour lgpio)
- `libsndfile1`: Bibliothèque pour lire/écrire les fichiers audio
- `portaudio19-dev`: API audio cross-platform pour Python
- `sox`: Outil de traitement audio en ligne de commande
- `alsa-utils`: Utilitaires pour gérer l'audio ALSA (arecord, aplay)
- `python3-*`: Python 3.x et ses outils de développement

### Étape 3: Cloner le projet

```bash
# Se placer dans le répertoire personnel
cd ~

# Cloner le dépôt GitHub
git clone https://github.com/didux123/storybox.git

# Entrer dans le répertoire du projet
cd storybox
```

**Note:** Le projet sera dans `~/storybox/`

### Étape 4: Créer l'environnement Python virtuel

```bash
# Créer l'environnement virtuel
python3 -m venv .venv

# Activer l'environnement virtuel
source .venv/bin/activate

# Mettre à jour pip, wheel et setuptools
pip install --upgrade pip wheel setuptools
```

**Pourquoi un venv:**
- Isolation des dépendances du projet
- Évite les conflits avec les paquets système
- Facilite la gestion des versions

### Étape 5: Installer les dépendances Python essentielles

```bash
# Installer les bibliothèques de base
pip install pyyaml python-dotenv python-json-logger psutil

# Installer les bibliothèques audio
pip install sounddevice soundfile numpy scipy pyaudio

# Installer les bibliothèques GPIO
pip install RPi.GPIO gpiozero
```

**Détails des paquets:**
- `pyyaml`: Lecture des fichiers de configuration YAML
- `python-dotenv`: Gestion des variables d'environnement (.env)
- `python-json-logger`: Logs structurés en JSON
- `psutil`: Monitoring système (CPU, RAM, etc.)
- `sounddevice/soundfile`: Capture et lecture audio
- `numpy/scipy`: Calcul numérique pour le traitement audio
- `pyaudio`: Interface Python pour PortAudio
- `RPi.GPIO/gpiozero`: Contrôle des GPIO du Raspberry Pi

### Étape 6: Installer les bindings IA

```bash
# Installer pywhispercpp pour Whisper (STT)
pip install pywhispercpp

# Installer llama-cpp-python pour Llama (LLM)
# ATTENTION: Cette étape peut prendre 10-15 minutes (compilation)
pip install llama-cpp-python --no-cache-dir
```

**Note importante:** La compilation de `llama-cpp-python` est longue car elle compile llama.cpp depuis les sources pour optimiser les performances sur ARM64.

### Étape 7: Télécharger Piper TTS (binaire)

```bash
# Créer le répertoire pour les binaires
mkdir -p ~/storybox/bin

# Télécharger Piper pour ARM64
cd ~/storybox/bin
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz

# Extraire l'archive
tar xzf piper_arm64.tar.gz

# Supprimer l'archive
rm piper_arm64.tar.gz

# Vérifier l'installation
./piper/piper --version
```

**Résultat attendu:** `1.2.0`

### Étape 8: Télécharger les modèles IA

```bash
# Créer la structure des dossiers pour les modèles
mkdir -p ~/models/{whisper,llm,piper}

# --- Modèle Whisper (STT) ---
cd ~/models/whisper
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin

# --- Modèle Llama (LLM) ---
cd ~/models/llm
# Option 1: Llama 3.2 3B Q4_K_M (recommandé)
wget https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf

# --- Modèle Piper (TTS) ---
cd ~/models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
```

**Tailles approximatives:**
- Whisper small: ~466 MB
- Llama 3.2 3B Q4: ~1.9 GB
- Piper FR siwis: ~61 MB

**Durée du téléchargement:** 5-15 minutes selon la connexion

### Étape 9: Configuration du fichier .env

```bash
# Retourner dans le projet
cd ~/storybox

# Créer le fichier .env
cat > .env << 'EOF'
# StoryBox IA - Raspberry Pi Configuration

# Model paths
WHISPER_MODEL_PATH=/home/$(whoami)/models/whisper/ggml-small.bin
LLM_MODEL_PATH=/home/$(whoami)/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf
PIPER_MODEL_PATH=/home/$(whoami)/models/piper/fr_FR-siwis-medium.onnx
PIPER_CONFIG_PATH=/home/$(whoami)/models/piper/fr_FR-siwis-medium.onnx.json
PIPER_BINARY_PATH=/home/$(whoami)/storybox/bin/piper/piper

# Audio devices (ALSA)
# Voir "arecord -l" et "aplay -l" pour identifier vos périphériques
AUDIO_INPUT_DEVICE=plughw:3,0
AUDIO_OUTPUT_DEVICE=plughw:0,0

# GPIO
BUTTON_PIN=17

# Logging
LOG_LEVEL=INFO
LOG_DIR=/home/$(whoami)/storybox/logs
EOF

# Remplacer $(whoami) par le nom d'utilisateur réel
sed -i "s/\$(whoami)/$USER/g" .env
```

**Note:** Adaptez `AUDIO_INPUT_DEVICE` et `AUDIO_OUTPUT_DEVICE` selon votre configuration matérielle.

### Étape 10: Identifier les périphériques audio

```bash
# Lister les cartes audio d'entrée
arecord -l

# Lister les cartes audio de sortie
aplay -l
```

**Exemple de sortie:**
```
**** List of CAPTURE Hardware Devices ****
card 3: Audio [AB13X USB Audio], device 0: USB Audio [USB Audio]
```

Dans cet exemple, le micro USB est sur la carte 3, donc `AUDIO_INPUT_DEVICE=plughw:3,0`

### Étape 11: Créer le répertoire de logs

```bash
mkdir -p ~/storybox/logs
```

### Étape 12: Test de l'installation

```bash
# Activer l'environnement virtuel
cd ~/storybox
source .venv/bin/activate

# Test audio basique
python3 quick_test.py
```

**Tests effectués:**
1. Enregistrement audio (3 secondes)
2. Synthèse vocale TTS
3. Lecture audio
4. Test GPIO (optionnel)

**Résultat attendu:**
```
========================================
RÉSUMÉ DES TESTS
========================================
Enregistrement audio: ✓ OK
Synthèse vocale TTS: ✓ OK
GPIO Bouton:         ✓ OK
========================================

✓ Système opérationnel!
```

### Étape 13: Test du bouton GPIO (optionnel)

```bash
# Test interactif du bouton (30 secondes)
python3 test_button_rpi.py
```

Appuyez sur le bouton pour voir les événements détectés.

### Étape 14: Test du pipeline complet (optionnel)

```bash
# Test complet: Enregistrement → STT → LLM → TTS
python3 full_test.py
```

**Attention:** Ce test nécessite que `llama-cpp-python` soit correctement installé et peut prendre plusieurs minutes lors de la première exécution (chargement des modèles).

---

## Vérification des installations

### Vérifier les paquets Python installés

```bash
source ~/storybox/.venv/bin/activate
pip list | grep -E '(whisper|llama|pyyaml|sounddevice|RPi.GPIO)'
```

### Vérifier les modèles téléchargés

```bash
ls -lh ~/models/whisper/
ls -lh ~/models/llm/
ls -lh ~/models/piper/
```

### Vérifier Piper

```bash
~/storybox/bin/piper/piper --version
```

### Test audio rapide

```bash
# Enregistrer 3 secondes
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/test.wav

# Rejouer
aplay -D plughw:0,0 /tmp/test.wav
```

---

## Dépannage

### Problème: "No module named 'lgpio'"

**Solution:**
```bash
sudo apt install -y swig
source ~/storybox/.venv/bin/activate
pip install lgpio rpi-lgpio
```

### Problème: Audio ne fonctionne pas

**Vérifier les périphériques:**
```bash
arecord -l  # Cartes d'entrée
aplay -l    # Cartes de sortie
```

**Tester manuellement:**
```bash
# Enregistrement
arecord -D plughw:CARD,DEVICE -f S16_LE -r 16000 -c 1 -d 3 test.wav

# Lecture
aplay -D plughw:CARD,DEVICE test.wav
```

Remplacez CARD et DEVICE par les numéros affichés par `arecord -l` et `aplay -l`.

### Problème: llama-cpp-python ne compile pas

**Vérifier que cmake est installé:**
```bash
cmake --version
```

**Réinstaller avec plus de verbosité:**
```bash
pip install llama-cpp-python --no-cache-dir -v
```

### Problème: Manque d'espace disque

**Vérifier l'espace:**
```bash
df -h
```

**Nettoyer les caches:**
```bash
sudo apt clean
pip cache purge
```

### Problème: Permission denied sur GPIO

**Ajouter l'utilisateur au groupe gpio:**
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

---

## Configuration avancée

### Optimisation des performances

**Fichier de swap (si RAM < 4GB):**
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Modifier CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**CPU Governor (performances maximales):**
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Service systemd (démarrage automatique)

Voir le fichier `workflow.md` pour la configuration du service systemd.

---

## Mise à jour du projet

```bash
cd ~/storybox
git pull
source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## Désinstallation

```bash
# Supprimer le projet
rm -rf ~/storybox

# Supprimer les modèles
rm -rf ~/models

# Supprimer les paquets système (optionnel)
sudo apt remove --purge cmake build-essential python3-venv
sudo apt autoremove
```

---

## Ressources

- [Documentation complète](https://github.com/didux123/storybox)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [Llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Piper TTS](https://github.com/rhasspy/piper)
- [Raspberry Pi GPIO](https://gpiozero.readthedocs.io/)

---

## Support

En cas de problème, vérifier:
1. Le fichier `INSTALLATION_SUMMARY.md` sur le Pi après installation automatique
2. Les logs dans `~/storybox/logs/`
3. Les issues GitHub du projet