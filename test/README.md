# StoryBox IA - Test Suite

Scripts et fichiers de test pour valider les composants avant déploiement sur Raspberry Pi.

## Structure

```
test/
├── README.md              # Ce fichier
├── scripts/               # Scripts de test
│   ├── test_tts.py       # Test génération vocale (Piper)
│   ├── test_stt.sh       # Test transcription (Whisper)
│   └── test_llm.sh       # Test génération texte (Llama)
└── audio_samples/         # Fichiers audio générés (gitignored)
    ├── greeting.wav
    ├── chapter_intro.wav
    ├── story_sample.wav
    ├── error.wav
    └── processing.wav
```

## Prérequis

### Sur Mac

1. **Modèles téléchargés** dans `models/` :
   - `models/whisper/ggml-small.bin`
   - `models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf`
   - `models/piper/fr_FR-siwis-medium.onnx`

2. **Toolchains compilés** :
   - whisper.cpp : `/tmp/whisper.cpp/build/bin/whisper-cli`
   - llama.cpp : `/tmp/llama.cpp/build/bin/llama-cli`
   - Piper TTS : `pip install piper-tts`

3. **FFmpeg** (pour conversion audio) :
   ```bash
   brew install ffmpeg
   ```

Voir `docs/MAC_DEVELOPMENT.md` pour les instructions complètes.

## Tests Disponibles

### 1. Test TTS (Synthèse Vocale)

Génère des exemples audio avec différents types de messages :

```bash
# Depuis la racine du projet
source .venv/bin/activate
python test/scripts/test_tts.py
```

**Sortie :**
- `test/audio_samples/greeting.wav` - Message d'accueil
- `test/audio_samples/chapter_intro.wav` - Intro de chapitre
- `test/audio_samples/story_sample.wav` - Extrait d'histoire
- `test/audio_samples/error.wav` - Message d'erreur
- `test/audio_samples/processing.wav` - Message de traitement

**Écouter les résultats :**
```bash
# Mac
afplay test/audio_samples/greeting.wav

# Tous les fichiers
for f in test/audio_samples/*.wav; do
    echo "Playing: $(basename $f)"
    afplay "$f"
done
```

### 2. Test STT (Reconnaissance Vocale)

Génère un fichier audio et le transcrit :

```bash
chmod +x test/scripts/test_stt.sh
./test/scripts/test_stt.sh
```

**Ce que fait le script :**
1. Génère un fichier audio avec `say` (voix française)
2. Le convertit en WAV 16kHz mono
3. Transcrit avec whisper.cpp
4. Compare avec le texte original

**Exemple de sortie :**
```
Original: Raconte-moi une histoire sur des pirates...
Transcribed: raconte-moi une histoire sur des pirates...
```

### 3. Test LLM (Génération d'Histoire)

Teste la génération de plan d'histoire :

```bash
chmod +x test/scripts/test_llm.sh
./test/scripts/test_llm.sh
```

**Ce que fait le script :**
- Demande au LLM de générer un plan de 5 chapitres
- Format JSON avec titres et résumés
- Thème : pirates et trésor

**Exemple de sortie :**
```json
{
  "chapters": [
    {
      "number": 1,
      "title": "Le Vieux Parchemin",
      "summary": "Lucas découvre une carte au trésor dans le grenier."
    },
    ...
  ]
}
```

## Pipeline Complet (End-to-End)

Pour tester le pipeline complet en simulation :

```bash
# 1. Générer audio de test (STT input)
./test/scripts/test_stt.sh

# 2. Générer plan avec LLM
./test/scripts/test_llm.sh

# 3. Générer narration avec TTS
python test/scripts/test_tts.py

# 4. Vérifier tous les fichiers audio
ls -lh test/audio_samples/
```

## Validation Qualité

### Qualité TTS

Écouter les fichiers générés et vérifier :
- ✅ Prononciation correcte des mots français
- ✅ Intonation naturelle
- ✅ Pas de distorsion audio
- ✅ Volume adéquat
- ✅ Pas de coupures entre phrases

Si qualité insuffisante :
- Essayer une autre voix Piper (voir modèles disponibles)
- Ajuster post-processing dans `configs/default.yaml`

### Qualité STT

Vérifier la transcription :
- ✅ Mots correctement reconnus
- ✅ Pas de fautes majeures
- ✅ Phrases cohérentes

Si précision insuffisante :
- Tester avec modèle `base` (plus rapide, moins précis)
- Vérifier qualité audio d'entrée (16kHz, mono, peu de bruit)

### Qualité LLM

Vérifier la génération :
- ✅ Plan cohérent avec le thème
- ✅ Chapitres logiques et enchaînés
- ✅ Format JSON valide
- ✅ Titres accrocheurs
- ✅ Résumés pertinents

Si qualité insuffisante :
- Ajuster température dans config (0.6-0.8)
- Modifier les prompts dans `configs/default.yaml`
- Augmenter nombre de tokens générés

## Benchmarks (Mac vs Pi)

### Mac M1/M2 (Référence)

| Test | Durée | Notes |
|------|-------|-------|
| TTS (1 phrase) | ~0.5s | Très rapide |
| STT (5s audio) | ~2-3s | ~2x temps réel |
| LLM (plan 5 chapitres) | ~10-15s | 20-30 tok/s |

### Raspberry Pi 4B 8GB (Estimation)

| Test | Durée | Notes |
|------|-------|-------|
| TTS (1 phrase) | ~1-2s | Acceptable |
| STT (5s audio) | ~10s | ~0.5x temps réel |
| LLM (plan 5 chapitres) | ~60-90s | 3-5 tok/s |

**Total latency (release → audio) sur Pi : 8-12s attendu**

## Debugging

### TTS ne génère pas d'audio

```bash
# Vérifier installation Piper
pip list | grep piper

# Tester manuellement
echo "Test" | piper -m models/piper/fr_FR-siwis-medium.onnx -f test.wav

# Vérifier modèle existe
ls -lh models/piper/
```

### STT transcription vide

```bash
# Vérifier format audio (doit être 16kHz mono WAV)
ffprobe test/audio_samples/test_input_pirates.wav

# Tester avec fichier minimal
echo "Bonjour" | \
  piper -m models/piper/fr_FR-siwis-medium.onnx -f test_minimal.wav

/tmp/whisper.cpp/build/bin/whisper-cli \
  -m models/whisper/ggml-small.bin \
  -l fr \
  test_minimal.wav
```

### LLM génération lente

```bash
# Réduire contexte
/tmp/llama.cpp/build/bin/llama-cli \
  -m models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -n 100 \
  -c 512 \
  -t 4 \
  -p "Test court"
```

## Nettoyage

Pour supprimer les fichiers audio générés :

```bash
rm -rf test/audio_samples/*.wav
```

Les fichiers audio ne sont PAS versionnés dans Git (.gitignore).

## CI/CD (Future)

Pour automatiser les tests :

```yaml
# .github/workflows/test.yml (exemple)
name: Test AI Components
on: [push]
jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run TTS tests
        run: python test/scripts/test_tts.py
```

## Prochaines Étapes

Après validation des tests Mac :
1. Déployer sur Pi : `./scripts/deploy_init.sh`
2. Installer sur Pi : `bash scripts/install_pi.sh`
3. Re-tester sur Pi avec benchmarks réels
4. Ajuster configs pour performance Pi

Voir `docs/RASPBERRY_PI_SETUP.md` pour le guide complet.
