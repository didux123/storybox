# StoryBox IA — Workflow Dev & Déploiement

Ce document décrit le flux de travail pour développer localement, déployer sur **Raspberry Pi 4B**, et synchroniser via **Git**, sans versionner les modèles. Il sert de **guide d’intégration**.

---

## Objectifs

* Développer sur **Mac** pour itérer rapidement.
* Déployer une première fois sur le **Raspberry Pi** en « bloc ».
* Versionner uniquement le **code** et la **configuration** (pas les modèles).
* Synchroniser le Pi à chaque **commit Git**.
* Tester localement sur Mac (audio simulé), exécuter en réel sur Pi (audio/GPIO).

---

## Arborescence du projet (suggestion)

```text
storybox/
├─ app/
│  ├─ main.py
│  ├─ audio/
│  ├─ stt/
│  ├─ llm/
│  ├─ tts/
│  ├─ gpio/
│  └─ utils/
├─ configs/
│  └─ default.yaml
├─ scripts/
│  ├─ deploy_init.sh
│  └─ setup_models.sh
├─ tests/
├─ .env.example
├─ requirements.txt
├─ constraints.txt
├─ README.md
└─ .gitignore
```

---

## `.gitignore` (minimal)

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
.env
.env.*

# Models / poids / caches
models/
weights/
voices/
data/audio/
cache/

# Build / logs
build/
dist/
logs/
```

---

## Pré-requis Raspberry Pi

* **Matériel** : Raspberry Pi 4B, alimentation 5 V / 3 A, dissipateur ou ventilateur
* **OS** : Raspberry Pi OS 64-bit Lite (Bookworm), filesystem ext4

### Paquets système

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y \
  python3 python3-venv python3-pip git cmake build-essential \
  libsndfile1 portaudio19-dev sox alsa-utils
```

### Création de l’environnement virtuel

```bash
python3 -m venv /home/$USER/projects/storybox/.venv
source /home/$USER/projects/storybox/.venv/bin/activate
pip install -r requirements.txt -c constraints.txt
```

---

## Déploiement initial (Mac → Pi)

Script d’amorçage via **rsync** (rapide). Remplacer `USER` et `HOST`.

```bash
# scripts/deploy_init.sh (à lancer depuis le Mac)
set -e

PI_USER="USER"
PI_HOST="HOST"
PI_DIR="/home/${PI_USER}/projects/storybox"

rsync -avz --delete \
  --exclude 'models' \
  --exclude 'weights' \
  --exclude 'voices' \
  --exclude 'logs' \
  --exclude '__pycache__' \
  ./ "${PI_USER}@${PI_HOST}:${PI_DIR}/"

ssh "${PI_USER}@${PI_HOST}" \
  "python3 -m venv ${PI_DIR}/.venv && \
   source ${PI_DIR}/.venv/bin/activate && \
   pip install -r ${PI_DIR}/requirements.txt -c ${PI_DIR}/constraints.txt"
```

---

## Installation des modèles (sur le Pi, hors Git)

### Arborescence conseillée

```text
~/models/
├─ llm/      # gguf 3B quantifié Q4_K_M (ex: Llama-3.2-3B-Instruct)
├─ whisper/  # tiny / base / small FR
└─ piper/    # voix FR
```

### Copie des modèles

Via clé USB, SSD, `rsync` ou `scp` :

```bash
mkdir -p ~/models/{llm,whisper,piper}
# Copier ensuite les fichiers dans chaque dossier
```

Configurer les chemins dans `configs/default.yaml` ou via `.env`.

---

## Git comme canal d’updates

### Côté Mac (développement)

```bash
git add .
git commit -m "feat: streaming TTS + hold-to-talk + LED pre-roll"
git push origin main
```

### Côté Pi (synchronisation)

```bash
cd ~/projects/storybox
git fetch --all
git pull --rebase
sudo systemctl restart storybox.service
```

---

## Service systemd (Pi)

Fichier : `/etc/systemd/system/storybox.service`

```ini
[Unit]
Description=StoryBox IA
After=network.target sound.target

[Service]
User=USER
WorkingDirectory=/home/USER/projects/storybox
EnvironmentFile=/home/USER/projects/storybox/.env
ExecStart=/home/USER/projects/storybox/.venv/bin/python -m app.main
Restart=on-failure
RestartSec=2
SupplementaryGroups=audio gpio

[Install]
WantedBy=multi-user.target
```

### Activation

```bash
sudo systemctl daemon-reload
sudo systemctl enable storybox
sudo systemctl start storybox
```

---

## Tests locaux (Mac)

* Audio simulé (fichiers WAV) pour les tests unitaires **STT / LLM / TTS**.
* Même versions Python et bibliothèques (`requirements.txt` + `constraints.txt`).
* Les entrées/sorties **GPIO** ne sont testées que sur le Pi.

---

## Sécurité & bonnes pratiques

* Aucun secret en clair : utiliser `.env` (exclu du Git) et `EnvironmentFile` systemd.
* Clé SSH **ed25519**, désactiver l’authentification par mot de passe.
* Utilisateur dédié, sans `sudo` global.
* Protection de la branche `main` (PR + reviews si collaboration).
* Logs en rotation, écritures disque limitées (microSD).

---

## Hooks facultatifs

* **Timer systemd** pour mises à jour Git régulières :

  * `storybox-update.timer`
  * `storybox-update.service` exécutant `git pull` puis `systemctl restart storybox`
* Script `scripts/setup_models.sh` :

  * Création des dossiers modèles
  * Vérification d’intégrité des poids (hashs)

---

## Environnement & configuration

### `configs/default.yaml` (exemple)

```yaml
audio:
  input_rate: 16000
  device: default

stt:
  model_path: /home/USER/models/whisper/ggml-base-fr.bin

llm:
  model_path: /home/USER/models/llm/llama-3.2-3b-instruct-q4_k_m.gguf
  context_tokens: 2048

tts:
  voice_path: /home/USER/models/piper/fr-voice.onnx
  sample_rate: 22050

gpio:
  button_pin: 17
  led_pins: [22, 23, 24]
```

### `.env.example`

Variables d’environnement : chemins, device ALSA, options spécifiques.

---

## Flux global

1. Développement sur Mac, tests unitaires (audio simulé).
2. Premier déploiement en bloc (`rsync`) vers le Pi.
3. Installation des modèles sur le Pi (clé ou SSD).
4. Lancement via **systemd**.
5. À chaque commit : push → fetch/pull sur le Pi → redémarrage du service.
6. Mesure de la latence et ajustements de performance (threads, quantization, buffers).

---

## Notes LLM / STT / TTS

* **LLM** : 3B quantifié GGUF `Q4_K_M` pour un bon compromis cohérence/performance ; streaming par paragraphes.
* **STT** : Whisper `small` FR si possible, `base` pour la vitesse ; audio mono 16 kHz.
* **TTS** : Piper voix FR ; post-traitements légers (normalisation, compresseur doux) ; tester plusieurs voix pour éviter un rendu artificiel.
