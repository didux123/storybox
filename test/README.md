# StoryBox IA - Mac Test Interface

Interface de test simple pour tester le pipeline complet sur Mac sans hardware GPIO.

## Installation

```bash
# Installer les dépendances
pip install sounddevice pyaudio

# Optionnel: pour le mode clavier (nécessite sudo)
pip install keyboard
```

## Utilisation

### Mode 1: CLI Simple (Recommandé)

Mode le plus simple, pas besoin de permissions spéciales:

```bash
python test/mac_test_interface.py
```

**Instructions:**
1. Appuie sur ENTRÉE pour commencer l'enregistrement
2. Parle (ex: "raconte-moi une histoire de pirates")
3. Appuie sur ENTRÉE pour arrêter
4. Attends la réponse audio (génération + lecture)

### Mode 2: Clavier (Hold Space)

Mode avec détection de la touche ESPACE (nécessite sudo sur Mac):

```bash
sudo python test/mac_test_interface.py
```

**Instructions:**
1. Maintiens ESPACE enfoncé pour enregistrer
2. Parle pendant l'enregistrement
3. Relâche ESPACE pour arrêter et traiter
4. Écoute la réponse audio

## Ce que fait l'interface

### Pipeline complet testé:

1. **Audio Input** → Enregistrement micro (sounddevice)
2. **STT** → Transcription avec Whisper
3. **Planner** → Génération plan d'histoire (3 chapitres pour test)
4. **StoryGen** → Génération du chapitre 1
5. **TTS** → Synthèse audio avec Piper
6. **Audio Output** → Lecture audio (PyAudio ou afplay)

### Exemple de sortie:

```
🎙️  READY TO TEST (CLI Mode)
Press ENTER to start recording...

🔴 RECORDING... (speak now, press ENTER when done)

⏹️  Recording stopped

✅ Captured 3.2s audio

📝 Step 1/4: Transcribing audio...
✅ Transcription: "raconte-moi une histoire de pirates"

📋 Step 2/4: Generating story plan...
✅ Generated plan: pirates

Chapters:
  1. Le départ
     → Lucas trouve une vieille carte au trésor.
  2. L'île mystérieuse
     → Le bateau arrive sur une île inconnue.
  3. Le trésor caché
     → Les pirates découvrent le coffre.

📖 Step 3/4: Generating chapter 1...
✅ Chapter 1 generated (145 words)

Text preview:
  Lucas était un jeune garçon qui aimait les aventures...

🔊 Step 4/4: Synthesizing and playing audio...
✅ Generated 12.3s audio

🎵 Playing audio...

✨ Pipeline complete!
```

## Dépannage

### Erreur: "No microphone detected"

```bash
# Lister les devices audio disponibles
python -c "import sounddevice; print(sounddevice.query_devices())"

# Vérifier que le micro fonctionne
python -m app.audio.input
```

### Erreur: "PyAudio not found"

L'interface utilisera automatiquement `afplay` (macOS) à la place.

Ou installer PyAudio:

```bash
# Sur Mac
brew install portaudio
pip install pyaudio
```

### Erreur: "keyboard requires sudo"

Utilise le mode CLI simple sans keyboard:
- L'interface détectera automatiquement et utilisera `input()` au lieu de `keyboard`
- Pas besoin de sudo dans ce mode

### Audio coupé ou de mauvaise qualité

Vérifie le niveau du micro dans les Préférences Système → Son → Entrée.

### LLM/STT trop lent

Première utilisation: les modèles doivent être chargés en RAM (~2-3 GB).
Les générations suivantes seront plus rapides.

## Tests unitaires des modules

Chaque module peut être testé indépendamment:

```bash
# Test audio input
MOCK_AUDIO=false python -m app.audio.input

# Test STT (nécessite audio de test)
python -m app.stt.whisper_stt

# Test LLM Planner
python -m app.llm.planner

# Test LLM StoryGen
python -m app.llm.story_gen

# Test TTS
python -m app.tts.piper_tts

# Test GPIO (mode mock)
MOCK_GPIO=true python -m app.gpio.button
MOCK_GPIO=true python -m app.gpio.led
```

## Limites du test sur Mac

- **Pas de GPIO** → LEDs et boutons simulés (mode mock)
- **Performance** → Mac plus rapide que Pi, les timings seront différents
- **Audio** → Device différent de celui du Pi

Pour un test complet, déployer sur le Raspberry Pi.

## Prochaines étapes

Une fois l'interface testée sur Mac:

1. **Deploy to Pi**: `./scripts/deploy_init.sh`
2. **Install on Pi**: `ssh pi@192.168.68.120 'cd ~/projects/storybox && bash scripts/install_pi.sh'`
3. **Run on Pi**: Test avec hardware GPIO réel

Voir `docs/RASPBERRY_PI_SETUP.md` pour plus de détails.
