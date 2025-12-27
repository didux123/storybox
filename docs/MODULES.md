# Documentation des Modules StoryBox

> Documentation technique complète des modules Python de StoryBox IA

## 📦 Vue d'Ensemble

StoryBox est organisé en modules fonctionnels indépendants :

```
app/
├── llm/          # Génération de texte (LLM)
├── tts/          # Text-to-Speech (narration)
├── stt/          # Speech-to-Text (transcription)
└── utils/        # Utilitaires (config, logging)
```

---

## 🤖 Module LLM

### CelesteLLM (`app/llm/celeste_llm.py`)

Wrapper pour Celeste AI permettant la génération d'histoires via différents providers LLM.

#### Initialisation

```python
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config

# Charger la config
config = get_config()

# Initialiser le LLM
llm = CelesteLLM(config.llm)
```

#### Génération de Plan d'Histoire

```python
import asyncio

# Générer un plan d'histoire
plan = asyncio.run(llm.generate_story_plan(
    theme="Un robot qui découvre les émotions",
    num_chapters=5,
    temperature=0.7
))

# Accéder aux chapitres
print(f"Titre: {plan.theme}")
for chapter in plan.chapters:
    print(f"Chapitre {chapter['number']}: {chapter['title']}")
    print(f"  Résumé: {chapter['summary']}")
```

**Paramètres:**
- `theme` (str): Thème de l'histoire
- `num_chapters` (int): Nombre de chapitres (3-10)
- `temperature` (float, optional): Température de génération (0.1-1.0)

**Retour:**
- `StoryPlan`: Objet Pydantic contenant le plan

#### Génération de Chapitre

```python
# Générer un chapitre
chapter_text = asyncio.run(llm.generate_chapter(
    plan=plan,
    chapter_num=1,
    cumulative_context="",
    min_words=150,
    max_words=300,
    temperature=0.7
))

print(chapter_text)
```

**Paramètres:**
- `plan` (StoryPlan): Plan de l'histoire
- `chapter_num` (int): Numéro du chapitre à générer
- `cumulative_context` (str): Contexte des chapitres précédents
- `min_words` (int): Nombre minimum de mots
- `max_words` (int): Nombre maximum de mots
- `temperature` (float, optional): Température de génération

**Retour:**
- `str`: Texte du chapitre généré

#### Modèle StoryPlan

```python
from app.llm.celeste_llm import StoryPlan

# Structure du StoryPlan
class StoryPlan:
    theme: str                    # Titre de l'histoire
    chapters: List[Dict]          # Liste des chapitres
        # Chaque chapitre contient:
        # - number: int
        # - title: str
        # - summary: str
```

---

## 🔊 Module TTS (Text-to-Speech)

### GradiumTTS (`app/tts/gradium_tts.py`)

Module de narration audio utilisant l'API Gradium.

#### Initialisation

```python
from app.tts.gradium_tts import GradiumTTS
from app.utils.config import get_config

config = get_config()
tts = GradiumTTS(config)
```

#### Génération Audio Asynchrone

```python
import asyncio

# Générer l'audio
audio_bytes = asyncio.run(tts.generate_speech(
    text="Bonjour, ceci est un test de narration.",
    voice_id="zIGaffB0kKEBG_8u",  # Voix Claire
    output_format="wav",
    padding_bonus=0.0  # Vitesse normale
))

# Sauvegarder dans un fichier
with open("narration.wav", "wb") as f:
    f.write(audio_bytes)
```

**Paramètres:**
- `text` (str): Texte à narrer
- `voice_id` (str, optional): ID de la voix Gradium
- `output_format` (str): Format audio ("wav", "pcm", "opus")
- `padding_bonus` (float): Contrôle de vitesse (-4.0 à +4.0)
  - Négatif = plus rapide
  - Positif = plus lent
  - 0.0 = vitesse normale

**Retour:**
- `bytes`: Audio brut

#### Sauvegarde Directe dans un Fichier

```python
success = asyncio.run(tts.generate_to_file(
    text="Texte à narrer",
    output_path="output.wav",
    voice_id="zIGaffB0kKEBG_8u",
    padding_bonus=-1.0  # Légèrement plus rapide
))

if success:
    print("Audio généré avec succès!")
```

#### Wrapper Synchrone

Pour utiliser sans `asyncio` :

```python
from app.tts.gradium_tts import generate_speech_sync

# Version synchrone
audio = generate_speech_sync(
    text="Texte à narrer",
    voice_id="zIGaffB0kKEBG_8u",
    padding_bonus=0.0
)
```

#### Voix Disponibles

```python
# Voix françaises pré-configurées
FRENCH_VOICES = {
    "Claire": "zIGaffB0kKEBG_8u",      # Féminine (par défaut)
    "Voix 2": "IB53xJtufx1sbfbt",
    "Voix 3": "s0PhgjzOTRD5wo5L",
    "Voix 4": "rIYDMY3dLccdauWA"
}
```

---

## 🎤 Module STT (Speech-to-Text)

### GradiumSTT (`app/stt/gradium_stt.py`)

Module de transcription audio utilisant l'API Gradium.

#### Initialisation

```python
from app.stt.gradium_stt import GradiumSTT
from app.utils.config import get_config

config = get_config()
stt = GradiumSTT(config)
```

#### Transcription depuis Bytes Audio

```python
import asyncio

# Lire le fichier audio
with open("recording.wav", "rb") as f:
    audio_data = f.read()

# Transcrire
text = asyncio.run(stt.transcribe(
    audio_data=audio_data,
    input_format="wav",
    model_name="default"
))

print(f"Texte transcrit: {text}")
```

**Paramètres:**
- `audio_data` (bytes): Données audio brutes
- `input_format` (str): Format audio ("wav", "pcm", "opus")
- `model_name` (str): Modèle STT à utiliser

**Retour:**
- `str`: Texte transcrit

#### Transcription depuis un Fichier

```python
# Transcription directe depuis un fichier
text = asyncio.run(stt.transcribe_file(
    audio_path="recording.wav",
    input_format=None  # Auto-détection depuis l'extension
))
```

**Auto-détection des formats:**
```python
# Extensions supportées
FORMAT_MAP = {
    ".wav": "wav",
    ".pcm": "pcm",
    ".opus": "opus",
    ".ogg": "opus"
}
```

#### Wrapper Synchrone

```python
from app.stt.gradium_stt import transcribe_file_sync

# Version synchrone
text = transcribe_file_sync("recording.wav")
print(text)
```

---

## ⚙️ Module Utils

### Config (`app/utils/config.py`)

Gestion centralisée de la configuration.

#### Chargement de la Config

```python
from app.utils.config import get_config

# Charger la config par défaut
config = get_config()

# Accéder aux paramètres
print(config.llm.model_path)
print(config.llm.temperature)
print(config.story.num_chapters)
```

#### Structure de Config

```yaml
# configs/default.yaml
llm:
  model_path: "gemini-1.5-flash"
  temperature: 0.7
  max_tokens: 4000

story:
  num_chapters: 5
  min_words_per_chapter: 150
  max_words_per_chapter: 300

prompts:
  plan: null      # Chargé depuis prompts.json
  chapter: null   # Chargé depuis prompts.json
```

#### Variables d'Environnement

```python
import os

# Clés API depuis .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GRADIUM_API_KEY = os.getenv("GRADIUM_API_KEY")
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "gemini-1.5-flash")
```

### Logger (`app/utils/logger.py`)

Logging structuré pour le projet.

#### Utilisation

```python
from app.utils.logger import get_logger

# Obtenir un logger
logger = get_logger(__name__)

# Différents niveaux de log
logger.debug("Message de debug")
logger.info("Information")
logger.warning("Avertissement")
logger.error("Erreur")

# Avec contexte
logger.info("Génération terminée", extra={
    "tokens": 1234,
    "time": 5.6,
    "cost": 0.0012
})
```

#### Configuration

```python
# Format de log
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Rotation des logs
# Logs sauvegardés dans: logs/storybox.log
# Rotation automatique à 10MB
```

---

## 🌐 Module Webapp

### Streamlit App (`webapp/streamlit_app.py`)

Interface web principale pour tester la pipeline.

#### Fonctions Utilitaires

```python
# Exécuter une coroutine async dans Streamlit
from webapp.streamlit_app import run_async

result = run_async(llm.generate_story_plan("Un robot", 5))
```

#### Fonctions Cachées

```python
# Ces fonctions utilisent @st.cache_resource
from webapp.streamlit_app import get_llm, get_tts, get_stt

llm = get_llm()    # LLM mis en cache
tts = get_tts()    # TTS mis en cache
stt = get_stt()    # STT mis en cache
```

### Prompt Editor (`webapp/utils/prompt_editor.py`)

Utilitaires pour éditer les prompts.

```python
from webapp.utils.prompt_editor import load_prompts, save_prompts

# Charger les prompts
prompts = load_prompts()
print(prompts["plan"]["system_prompt"])
print(prompts["chapter"]["user_template"])

# Modifier et sauvegarder
prompts["plan"]["system_prompt"] = "Nouveau prompt..."
save_prompts(prompts)
```

---

## 🔄 Exemples d'Usage Complet

### Pipeline Complète

```python
import asyncio
from app.llm.celeste_llm import CelesteLLM
from app.tts.gradium_tts import GradiumTTS
from app.stt.gradium_stt import GradiumSTT
from app.utils.config import get_config

async def generate_and_narrate_story():
    # Initialisation
    config = get_config()
    llm = CelesteLLM(config.llm)
    tts = GradiumTTS(config)
    stt = GradiumSTT(config)

    # 1. Transcription vocale (optionnel)
    # text_theme = await stt.transcribe_file("user_voice.wav")
    text_theme = "Un robot qui découvre les émotions"

    # 2. Génération du plan
    plan = await llm.generate_story_plan(text_theme, num_chapters=5)
    print(f"Plan généré: {plan.theme}")

    # 3. Génération des chapitres
    chapters = []
    cumulative_context = ""

    for i in range(1, len(plan.chapters) + 1):
        chapter = await llm.generate_chapter(
            plan=plan,
            chapter_num=i,
            cumulative_context=cumulative_context,
            min_words=150,
            max_words=300
        )
        chapters.append(chapter)

        # Mise à jour du contexte
        summary = plan.chapters[i-1]['summary']
        cumulative_context += f" Chapitre {i}: {summary}"

    # 4. Narration audio
    full_story = " ".join(chapters)
    audio = await tts.generate_speech(
        text=full_story,
        voice_id="zIGaffB0kKEBG_8u"
    )

    # Sauvegarder
    with open("story_narration.wav", "wb") as f:
        f.write(audio)

    print("Histoire générée et narrée avec succès!")

# Exécuter
asyncio.run(generate_and_narrate_story())
```

### Utilisation des Wrappers Synchrones

```python
from app.llm.celeste_llm import CelesteLLM
from app.tts.gradium_tts import generate_speech_sync
from app.stt.gradium_stt import transcribe_file_sync
from app.utils.config import get_config
import asyncio

# STT (sync)
theme = transcribe_file_sync("user_voice.wav")

# LLM (async requis pour CelesteLLM)
config = get_config()
llm = CelesteLLM(config.llm)
plan = asyncio.run(llm.generate_story_plan(theme, 5))

chapter = asyncio.run(llm.generate_chapter(plan, 1))

# TTS (sync)
audio = generate_speech_sync(chapter, voice_id="zIGaffB0kKEBG_8u")

with open("chapter1.wav", "wb") as f:
    f.write(audio)
```

---

## 🐛 Gestion des Erreurs

### Erreurs Communes

#### 1. API Key Manquante

```python
from app.tts.gradium_tts import GradiumTTS

tts = GradiumTTS()
if not tts.client:
    print("Erreur: GRADIUM_API_KEY manquante dans .env")
```

#### 2. Erreurs de Génération

```python
try:
    plan = await llm.generate_story_plan(theme, 5)
    if not plan:
        print("Échec de la génération du plan")
except Exception as e:
    print(f"Erreur: {e}")
```

#### 3. Timeout

```python
import asyncio

try:
    chapter = await asyncio.wait_for(
        llm.generate_chapter(plan, 1),
        timeout=30.0  # 30 secondes max
    )
except asyncio.TimeoutError:
    print("Timeout: la génération a pris trop de temps")
```

---

## 📊 Métriques et Monitoring

### Estimation des Tokens

```python
def estimate_tokens(text: str) -> int:
    """Estimation approximative: 1 token ≈ 4 caractères"""
    return len(text) // 4
```

### Calcul du Coût

```python
def calculate_cost(input_tokens: int, output_tokens: int, model_id: str) -> float:
    """Calculer le coût en USD basé sur le modèle"""
    pricing = {
        "gemini-1.5-flash": {"input_per_1m": 0.075, "output_per_1m": 0.30},
        "gpt-4o-mini": {"input_per_1m": 0.150, "output_per_1m": 0.600},
        "claude-3-5-sonnet-20241022": {"input_per_1m": 3.00, "output_per_1m": 15.00}
    }

    model_pricing = pricing.get(model_id, {})
    input_cost = (input_tokens / 1_000_000) * model_pricing.get('input_per_1m', 0)
    output_cost = (output_tokens / 1_000_000) * model_pricing.get('output_per_1m', 0)

    return input_cost + output_cost
```

---

## 🔗 Références

- **Celeste AI**: https://github.com/withceleste/celeste-python
- **Gradium API**: https://gradium.ai/docs
- **Streamlit**: https://docs.streamlit.io/

---

**Dernière mise à jour**: 25 décembre 2024 - V0.3
