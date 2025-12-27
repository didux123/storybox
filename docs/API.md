# API Reference - StoryBox IA

> Référence complète de l'API Python pour StoryBox

## Table des Matières

- [LLM API](#llm-api)
- [TTS API](#tts-api)
- [STT API](#stt-api)
- [Utils API](#utils-api)
- [Types et Modèles](#types-et-modèles)

---

## LLM API

### `class CelesteLLM`

Wrapper pour la génération d'histoires via Celeste AI.

**Location:** `app/llm/celeste_llm.py`

#### `__init__(config: LLMConfig)`

Initialise le client LLM.

**Paramètres:**
- `config` (LLMConfig): Configuration LLM

**Raises:**
- `Exception`: Si l'initialisation échoue

**Exemple:**
```python
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config

config = get_config()
llm = CelesteLLM(config.llm)
```

#### `async generate_story_plan(theme: str, num_chapters: int = 10, temperature: Optional[float] = None) -> Optional[StoryPlan]`

Génère un plan d'histoire structuré.

**Paramètres:**
- `theme` (str): Thème ou description de l'histoire
- `num_chapters` (int, optional): Nombre de chapitres. Default: 10
- `temperature` (float, optional): Température de génération (0.1-1.0). Default: depuis config

**Retour:**
- `StoryPlan | None`: Plan généré ou None si échec

**Exemple:**
```python
plan = await llm.generate_story_plan(
    theme="Un robot qui découvre les émotions",
    num_chapters=5,
    temperature=0.7
)
```

#### `async generate_chapter(...) -> Optional[str]`

Génère le contenu d'un chapitre.

**Paramètres:**
- `plan` (StoryPlan): Plan de l'histoire
- `chapter_num` (int): Numéro du chapitre (1-based)
- `cumulative_context` (str, optional): Résumé des chapitres précédents. Default: ""
- `min_words` (int, optional): Minimum de mots. Default: 150
- `max_words` (int, optional): Maximum de mots. Default: 300
- `temperature` (float, optional): Température. Default: depuis config

**Retour:**
- `str | None`: Texte du chapitre ou None si échec

**Exemple:**
```python
chapter_text = await llm.generate_chapter(
    plan=plan,
    chapter_num=1,
    cumulative_context="",
    min_words=200,
    max_words=400,
    temperature=0.8
)
```

#### `async generate(prompt: str, **kwargs) -> str`

Génération générique de texte.

**Paramètres:**
- `prompt` (str): Prompt de génération
- `**kwargs`: Arguments supplémentaires (max_tokens, temperature, etc.)

**Retour:**
- `str`: Texte généré

---

## TTS API

### `class GradiumTTS`

Client Text-to-Speech utilisant l'API Gradium.

**Location:** `app/tts/gradium_tts.py`

#### `__init__(config: Optional[Config] = None)`

Initialise le client TTS.

**Paramètres:**
- `config` (Config, optional): Configuration. Default: charge depuis default.yaml

**Attributes:**
- `client` (GradiumClient | None): Client Gradium
- `logger` (Logger): Logger de la classe

**Exemple:**
```python
from app.tts.gradium_tts import GradiumTTS

tts = GradiumTTS()
if not tts.client:
    print("TTS non initialisé: clé API manquante")
```

#### `async generate_speech(...) -> Optional[bytes]`

Génère l'audio depuis du texte.

**Paramètres:**
- `text` (str): Texte à narrer
- `voice_id` (str, optional): ID de voix Gradium. Default: None (voix par défaut)
- `output_format` (str, optional): Format audio. Default: "wav"
  - Valeurs possibles: "wav", "pcm", "opus"
- `padding_bonus` (float, optional): Contrôle de vitesse (-4.0 à +4.0). Default: 0.0
  - < 0: Plus rapide
  - = 0: Vitesse normale
  - > 0: Plus lent

**Retour:**
- `bytes | None`: Audio brut ou None si échec

**Exemple:**
```python
audio = await tts.generate_speech(
    text="Bonjour le monde!",
    voice_id="zIGaffB0kKEBG_8u",
    output_format="wav",
    padding_bonus=-1.0  # Légèrement plus rapide
)
```

#### `async generate_to_file(...) -> bool`

Génère l'audio et le sauvegarde directement.

**Paramètres:**
- `text` (str): Texte à narrer
- `output_path` (str): Chemin du fichier de sortie
- `voice_id` (str, optional): ID de voix
- `output_format` (str, optional): Format audio
- `padding_bonus` (float, optional): Contrôle de vitesse

**Retour:**
- `bool`: True si succès, False sinon

**Exemple:**
```python
success = await tts.generate_to_file(
    text="Chapitre 1...",
    output_path="/tmp/chapter1.wav",
    voice_id="zIGaffB0kKEBG_8u"
)
```

#### `get_audio_stream(audio_bytes: bytes) -> BytesIO`

Convertit les bytes audio en stream pour playback.

**Paramètres:**
- `audio_bytes` (bytes): Données audio brutes

**Retour:**
- `BytesIO`: Stream audio

**Exemple:**
```python
stream = tts.get_audio_stream(audio)
# Utilisable avec st.audio(stream) dans Streamlit
```

### Fonctions Utilitaires

#### `generate_speech_sync(...) -> Optional[bytes]`

Wrapper synchrone pour `generate_speech()`.

**Paramètres:** Identiques à `generate_speech()`

**Retour:** Identique à `generate_speech()`

**Exemple:**
```python
from app.tts.gradium_tts import generate_speech_sync

audio = generate_speech_sync("Hello", voice_id="zIGaffB0kKEBG_8u")
```

#### `generate_to_file_sync(...) -> bool`

Wrapper synchrone pour `generate_to_file()`.

---

## STT API

### `class GradiumSTT`

Client Speech-to-Text utilisant l'API Gradium.

**Location:** `app/stt/gradium_stt.py`

#### `__init__(config: Optional[Config] = None)`

Initialise le client STT.

**Paramètres:**
- `config` (Config, optional): Configuration

**Attributes:**
- `client` (GradiumClient | None): Client Gradium
- `logger` (Logger): Logger

#### `async transcribe(...) -> Optional[str]`

Transcrit de l'audio en texte.

**Paramètres:**
- `audio_data` (bytes): Données audio brutes
- `input_format` (str, optional): Format audio. Default: "wav"
  - Valeurs possibles: "wav", "pcm", "opus"
- `model_name` (str, optional): Modèle STT. Default: "default"

**Retour:**
- `str | None`: Texte transcrit ou None si échec

**Exemple:**
```python
with open("recording.wav", "rb") as f:
    audio = f.read()

text = await stt.transcribe(audio, input_format="wav")
```

#### `async transcribe_file(...) -> Optional[str]`

Transcrit directement depuis un fichier audio.

**Paramètres:**
- `audio_path` (str): Chemin du fichier audio
- `input_format` (str, optional): Format. Default: None (auto-détecté)

**Auto-détection des formats:**
```python
{
    ".wav": "wav",
    ".pcm": "pcm",
    ".opus": "opus",
    ".ogg": "opus"
}
```

**Retour:**
- `str | None`: Texte transcrit

**Exemple:**
```python
text = await stt.transcribe_file("user_recording.wav")
```

### Fonctions Utilitaires

#### `transcribe_sync(audio_data: bytes, ...) -> Optional[str]`

Wrapper synchrone pour `transcribe()`.

#### `transcribe_file_sync(audio_path: str, ...) -> Optional[str]`

Wrapper synchrone pour `transcribe_file()`.

---

## Utils API

### Configuration

#### `get_config() -> Config`

Charge la configuration depuis `configs/default.yaml`.

**Retour:**
- `Config`: Objet de configuration

**Exemple:**
```python
from app.utils.config import get_config

config = get_config()
print(config.llm.model_path)
print(config.story.num_chapters)
```

### Logging

#### `get_logger(name: str) -> logging.Logger`

Obtient un logger configuré.

**Paramètres:**
- `name` (str): Nom du logger (généralement `__name__`)

**Retour:**
- `logging.Logger`: Logger configuré

**Exemple:**
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message d'information")
logger.error("Message d'erreur", exc_info=True)
```

---

## Types et Modèles

### `StoryPlan`

Modèle Pydantic pour le plan d'histoire.

**Champs:**
- `theme` (str): Titre/thème de l'histoire
- `chapters` (List[Dict]): Liste des chapitres
  - `number` (int): Numéro du chapitre
  - `title` (str): Titre du chapitre
  - `summary` (str): Résumé du chapitre

**Méthodes:**
- `to_dict() -> Dict`: Convertit en dictionnaire
- `from_dict(data: Dict) -> StoryPlan`: Crée depuis un dictionnaire

**Exemple:**
```python
from app.llm.celeste_llm import StoryPlan

plan = StoryPlan(
    theme="L'aventure du robot",
    chapters=[
        {
            "number": 1,
            "title": "Le réveil",
            "summary": "Un robot s'active pour la première fois"
        },
        # ...
    ]
)

# Conversion
data = plan.to_dict()
plan2 = StoryPlan.from_dict(data)
```

### `LLMConfig`

Configuration pour le module LLM.

**Champs:**
- `model_path` (str): ID du modèle (ex: "gemini-1.5-flash")
- `temperature` (float): Température par défaut
- `max_tokens` (int): Limite de tokens
- `plan_temperature` (float): Température pour génération de plan
- `chapter_temperature` (float): Température pour génération de chapitres

### `StoryConfig`

Configuration pour les paramètres d'histoire.

**Champs:**
- `num_chapters` (int): Nombre de chapitres par défaut
- `min_words_per_chapter` (int): Minimum de mots
- `max_words_per_chapter` (int): Maximum de mots

---

## Constantes

### Voix TTS

```python
FRENCH_VOICES = {
    "Claire": "zIGaffB0kKEBG_8u",      # Voix féminine française
    "Voix 2": "IB53xJtufx1sbfbt",
    "Voix 3": "s0PhgjzOTRD5wo5L",
    "Voix 4": "rIYDMY3dLccdauWA"
}
```

### Contrôle de Vitesse TTS

```python
SPEED_PRESETS = {
    "Très rapide": -2.0,
    "Rapide": -1.0,
    "Normale": 0.0,
    "Lent": 1.0,
    "Très lent": 2.0
}
```

### Formats Audio

```python
AUDIO_FORMATS = {
    "TTS": ["wav", "pcm", "opus"],
    "STT": ["wav", "pcm", "opus"]
}
```

---

## Gestion des Erreurs

### Exceptions Communes

#### API Key Manquante

```python
from app.tts.gradium_tts import GradiumTTS

try:
    tts = GradiumTTS()
    if not tts.client:
        raise ValueError("GRADIUM_API_KEY manquante dans .env")
except Exception as e:
    logger.error(f"Erreur initialisation TTS: {e}")
```

#### Timeout

```python
import asyncio

try:
    result = await asyncio.wait_for(
        llm.generate_story_plan(theme, 5),
        timeout=30.0
    )
except asyncio.TimeoutError:
    logger.error("Timeout: génération trop longue")
```

#### Validation JSON

```python
from pydantic import ValidationError

try:
    plan = StoryPlan.from_dict(data)
except ValidationError as e:
    logger.error(f"Données invalides: {e}")
```

---

## Exemples Complets

### Pipeline Complète Asynchrone

```python
import asyncio
from app.llm.celeste_llm import CelesteLLM
from app.tts.gradium_tts import GradiumTTS
from app.stt.gradium_stt import GradiumSTT
from app.utils.config import get_config
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def full_pipeline():
    # Init
    config = get_config()
    llm = CelesteLLM(config.llm)
    tts = GradiumTTS(config)
    stt = GradiumSTT(config)

    # STT
    theme = await stt.transcribe_file("user_voice.wav")
    logger.info(f"Thème transcrit: {theme}")

    # LLM Plan
    plan = await llm.generate_story_plan(theme, num_chapters=5)
    logger.info(f"Plan créé: {plan.theme}")

    # LLM Chapitres
    chapters = []
    context = ""
    for i in range(1, 6):
        chapter = await llm.generate_chapter(
            plan, i, context, 150, 300
        )
        chapters.append(chapter)
        context += f" Ch{i}: {plan.chapters[i-1]['summary']}"

    # TTS
    full_story = " ".join(chapters)
    audio = await tts.generate_speech(full_story, voice_id="zIGaffB0kKEBG_8u")

    # Save
    with open("story.wav", "wb") as f:
        f.write(audio)

    logger.info("Pipeline terminée!")

asyncio.run(full_pipeline())
```

### Pipeline Simplifiée Synchrone

```python
import asyncio
from app.llm.celeste_llm import CelesteLLM
from app.tts.gradium_tts import generate_speech_sync
from app.stt.gradium_stt import transcribe_file_sync
from app.utils.config import get_config

# STT (sync)
theme = transcribe_file_sync("voice.wav")

# LLM (async requis)
config = get_config()
llm = CelesteLLM(config.llm)
plan = asyncio.run(llm.generate_story_plan(theme, 3))
chapter = asyncio.run(llm.generate_chapter(plan, 1))

# TTS (sync)
audio = generate_speech_sync(chapter)

with open("narration.wav", "wb") as f:
    f.write(audio)
```

---

## Performance et Optimisation

### Métriques

```python
import time

# Mesurer le temps
start = time.time()
plan = await llm.generate_story_plan(theme, 5)
elapsed = time.time() - start
print(f"Génération en {elapsed:.2f}s")

# Estimer les tokens
tokens = len(theme) // 4 + len(str(plan.to_dict())) // 4
print(f"~{tokens} tokens")
```

### Caching

```python
import streamlit as st

@st.cache_resource
def get_cached_llm():
    config = get_config()
    return CelesteLLM(config.llm)

# Réutilisation
llm = get_cached_llm()
```

### Batch Processing

```python
async def generate_all_chapters(plan, llm):
    """Génère tous les chapitres avec contexte cumulatif"""
    chapters = []
    context = ""

    for i in range(1, len(plan.chapters) + 1):
        chapter = await llm.generate_chapter(plan, i, context)
        chapters.append(chapter)

        # Mise à jour contexte
        summary = plan.chapters[i-1]['summary']
        context += f" Chapitre {i}: {summary}"

    return chapters
```

---

**Dernière mise à jour**: 25 décembre 2024 - V0.3
