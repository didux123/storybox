# Expression de besoin — Boîte à histoires IA

**Version :** maintien du bouton (« hold-to-talk ») + modèles maximaux compatibles **Raspberry Pi 4B**

---

## 1. Objectif

Dispositif **autonome** qui, tant que le bouton est maintenu :

1. Enregistre le microphone
2. Transcrit la consigne vocale
3. Génère un **plan narratif (~10 chapitres)** via un **LLM 3B quantifié**
4. Narrer l’histoire en **streaming TTS**

Le tout avec :

* **LED** pour l’état et la progression
* Fonctionnement **local**, **hors réseau** en production

---

## 2. Périmètre fonctionnel

### Entrée vocale

* Mode **hold-to-talk** :

  * Appui → début d’écoute
  * Relâchement → fin d’écoute
* Aucune détection de fin de parole (VAD) nécessaire

### Compréhension

* **STT français** de la consigne
* Extraction du **thème** et des **contraintes**

### Planification

* Génération d’un **plan de 10 chapitres cohérents**

  * Titres
  * Résumés courts

### Narration (streaming)

* Génération **chapitre par chapitre**
* Maintien d’un **contexte global**
* Lecture **TTS en continu** pendant la génération
* Objectif : réduire la **latence perçue**

### LED

* États :

  * `Idle`
  * `Listening`
  * `Processing`
  * `Narrating`
  * `Error`
* **Pré-roll visuel** avant le début audio
* Pendant la narration :

  * Animation synchronisée (tokens / audio)

### Contrôles physiques

* **Maintien bouton** : enregistrement actif
* **Relâchement** : arrêt enregistrement → traitement
* **Pression courte pendant narration** : pause / reprise
* **Pression longue (≥ 3 s)** : arrêt propre du service

### Journalisation & métriques

* Latence : `relâchement → premier audio`
* Tokens/seconde (LLM)
* Temps de chargement des modèles
* Erreurs audio / GPIO
* Rotation des logs

---

## 3. Exigences non fonctionnelles

* **Latence cible** :

  * ≤ 10 s entre fin d’appui et début audio
  * Tolérance si le pré-roll LED est explicite
* **Robustesse offline** :

  * Aucune dépendance réseau
  * Reprise automatique après redémarrage
  * Tolérance aux déconnexions USB audio
* **Endurance microSD** :

  * Limiter les écritures disque
  * Rotation des logs
  * Cache en mémoire
  * Swap désactivé ou zram

---

## 4. Matériel

### Plateforme

* Raspberry Pi 4B (4–8 Go)
* Alimentation officielle 5 V / 3 A
* Dissipation thermique / ventilation

### Audio

* **Entrée** :

  * Option simple : micro USB « class compliant » ou interface USB (UAC1/2) + micro XLR
  * Option faible latence : micro MEMS I2S (INMP441)
* **Sortie** :

  * USB audio + ampli
  * ou HAT DAC/AMP I2S

### Commandes & indicateurs

* Bouton poussoir GPIO

  * Pull-up / pull-down
  * Debounce logiciel
* LED(s) pour états et progression

### Stockage

* microSD 64 Go (phase 1)
* Option SSD USB 3.2 pour modèles (phase 2)

---

## 5. Système & logiciels

### OS & dépendances

* Raspberry Pi OS 64-bit Lite (Bookworm), ext4
* Paquets :

  * `python3`, `python3-venv`, `pip`, `git`
  * `cmake`, `build-essential`
  * `libsndfile1`, `portaudio19-dev`, `sox`, `alsa-utils`

### STT (français)

* **whisper.cpp**
* Modèles : `small` ou `base` (int8 / fp16)
* Par défaut : `small` (meilleure précision)
* Fallback : `base` si contrainte de vitesse

### LLM

* **llama.cpp**
* Modèle : 3B instruct GGUF `Q4_K_M`

  * Ex. *Llama-3.2-3B-Instruct* ou équivalent
* Priorité : cohérence inter-chapitres
* Contexte cumulatif court

### TTS

* **Piper** (voix FR)
* 22.05 kHz / 16-bit
* Post-traitement :

  * Noise gate léger
  * Compresseur doux
* Option d’évaluation : voix plus premium (Coqui TTS) si CPU OK

### Orchestration

* Service Python événementiel
* Gestion :

  * États
  * Pipeline audio
  * GPIO

### GPIO & audio

* GPIO : `gpiozero` (simplicité) ou `RPi.GPIO`
* Audio : ALSA par défaut

---

## 6. Architecture logique

* **AudioIn** :

  * Capture PCM mono 16 kHz tant que bouton maintenu
  * Normalisation
  * Pas de VAD
* **STT** : whisper.cpp → texte de consigne
* **Planner** : génération du plan (10 chapitres)
* **StoryGen** :

  * Génération du chapitre *n*
  * Mémoire courte :

    * Résumés cumulés
    * Plan global
  * Sortie par paragraphes (streaming)
* **TTS** :

  * Lecture à la volée
  * Buffer de quelques centaines de ms
* **State / LED** : machine d’états + pré-roll
* **Control** : bouton, pause/reprise, arrêt long, watchdog
* **Metrics / Logs** : rotation ≤ 50 Mo

---

## 7. Spécifications techniques

### Audio

* PCM mono 16 kHz
* Frames 20–40 ms
* Stockage temporaire : RAM prioritaire, ext4 si nécessaire

### Prompts

**Plan**

> Génère un plan de 10 chapitres cohérents sur [thème].
> Chaque chapitre : Titre + 1 phrase de résumé.
> Style : [optionnel]

**Chapitre**

> Écris le chapitre n°, 150–300 mots, cohérent avec :
>
> * Contexte cumulatif : [résumés précédents]
> * Plan : [chapitres]
>   Ton narratif : [optionnel]
>   Paragraphes courts.

### Contexte

* Résumés cumulés : 2–3 phrases / chapitre
* Taille cible : ~1–2k tokens

### Streaming & backpressure

* StoryGen produit par paragraphes
* TTS consomme en continu
* Ajustement automatique de cadence si TTS ralentit

---

## 8. Déploiement & exploitation

* Démarrage via **systemd**
* Aucune dépendance réseau
* `Restart=on-failure`
* Configuration : YAML / JSON

  * Devices ALSA
  * Modèles STT / LLM / TTS
  * Seuils
  * Patterns LED
* Maintenance :

  * CLI locale de test STT / LLM / TTS
  * Script d’update offline (clé / SSD)
  * Purge optionnelle des enregistrements audio

---

## 9. Tests & acceptation

### Fonctionnels

* Hold-to-talk → enregistrement
* Relâchement → plan → narration streaming
* Pause / reprise
* LED conformes aux états

### Performance

* Latence `relâchement → premier audio` ≤ 10 s (Pi 4B, LLM 3B Q4)
* Mesure et journalisation systématiques

### Qualité narrative

* Continuité entre chapitres validée
* Vérification manuelle + ajustement des prompts

### Robustesse

* 30 cycles consécutifs sans crash
* Reprise après déconnexion USB audio

---

## 10. Roadmap

* **v0** : hold-to-talk, STT → Plan → StoryGen → TTS
* **v1** : streaming affiné, pré-roll LED, pause/reprise, rotation logs, , LED états, métriques
* **v2** : SSD pour modèles, tuning thermiques et threads
* **v3** : image Docker arm64 optionnelle (mapping `/dev/snd`, `/dev/gpiomem`), compose/systemd

---

## Annexe A — Connexion micro (Raspberry Pi 4B)

### Option 1 — USB (recommandée)

* Micro USB ou interface audio USB « class-compliant »
* Branchement sur port USB 3 du Pi
* Vérification :

```bash
arecord -l
```

* Configuration carte par défaut (`~/.asoundrc` ou `alsamixer`)
* Test :

```bash
arecord -f S16_LE -r 16000 -c 1 test.wav
```

### Option 2 — I2S (latence basse)

* Micro MEMS INMP441

**Câblage typique** :

* BCLK → GPIO18 (PCM_CLK)

* LRCLK → GPIO19 (PCM_FS)

* DOUT → GPIO20 (PCM_DIN)

* 3.3 V → 3V3

* GND → GND

* Activation I2S :

  * `dtparam=i2s=on` dans `/boot/config.txt`
  * Charger l’overlay / driver adapté

* Capture via `arecord` sur le device I2S

> Plus technique : privilégier l’USB pour du plug-and-play.

---

## Qualité TTS (voix)

* Piper FR :

  * Choisir une voix au timbre naturel
  * Évaluer plusieurs voix FR
  * Sample rate : 22.05 kHz
  * Réglage de la prosodie
* Post-traitement :

  * De-esser si nécessaire
  * Compresseur doux
  * Normalisation LUFS

Objectif : éviter un rendu « cheap ».

---

## Contraintes & hypothèses

* Raspberry Pi 4B + Raspberry Pi OS 64-bit Lite
* Fonctionnement offline en production
* Whisper `small` / `base`
* LLM 3B GGUF `Q4_K_M`
* TTS Piper FR
* Alimentation fiable et refroidissement adéquat
