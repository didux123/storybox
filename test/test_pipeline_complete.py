#!/usr/bin/env python3
"""Test complet du pipeline StoryBox: STT → LLM → TTS"""
import subprocess
import time
import json
from vosk import Model, KaldiRecognizer
import wave
from llama_cpp import Llama

print("=" * 60)
print("TEST COMPLET DU PIPELINE STORYBOX")
print("=" * 60)
print("\n🎤 Enregistrement → 🧠 Transcription → 💭 LLM → 🔊 Audio\n")

# ============================================================================
# ÉTAPE 1: ENREGISTREMENT AUDIO (STT)
# ============================================================================
print("=" * 60)
print("ÉTAPE 1/4: ENREGISTREMENT AUDIO")
print("=" * 60)
print("🎤 Parlez maintenant pendant 5 secondes...")
print("   (Exemple: 'des dinosaures qui jouent au football')\n")

start_total = time.time()

cmd = [
    "arecord",
    "-D", "plughw:1,0",
    "-f", "S16_LE",
    "-r", "16000",
    "-c", "1",
    "-d", "5",
    "/tmp/pipeline_input.wav"
]

subprocess.run(cmd, capture_output=True)
print("✓ Enregistrement terminé\n")

# ============================================================================
# ÉTAPE 2: TRANSCRIPTION (VOSK)
# ============================================================================
print("=" * 60)
print("ÉTAPE 2/4: TRANSCRIPTION VOCALE")
print("=" * 60)

try:
    print("Chargement du modèle Vosk...")
    start_stt = time.time()

    model_vosk = Model("/home/maxence/models/vosk/vosk-model-small-fr-0.22")
    print(f"✓ Modèle Vosk chargé en {time.time() - start_stt:.1f}s\n")

    # Ouvrir et transcrire
    wf = wave.open("/tmp/pipeline_input.wav", "rb")
    rec = KaldiRecognizer(model_vosk, wf.getframerate())
    rec.SetWords(False)

    print("Transcription en cours...")
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    transcription = result.get("text", "").strip()

    stt_time = time.time() - start_stt

    print("-" * 60)
    print(f"📝 TRANSCRIPTION: {transcription}")
    print("-" * 60)
    print(f"✓ Transcription terminée en {stt_time:.1f}s\n")

    if not transcription:
        print("⚠️  Aucun texte détecté. Veuillez réessayer en parlant plus fort.")
        exit(1)

except Exception as e:
    print(f"✗ Erreur transcription: {e}")
    exit(1)

# ============================================================================
# ÉTAPE 3: GÉNÉRATION D'HISTOIRE (LLM)
# ============================================================================
print("=" * 60)
print("ÉTAPE 3/4: GÉNÉRATION D'HISTOIRE")
print("=" * 60)

try:
    print("Chargement du modèle LLM...")
    start_llm = time.time()

    llm = Llama(
        model_path="/home/maxence/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        n_ctx=512,
        n_threads=4,
        verbose=False
    )

    print(f"✓ Modèle LLM chargé en {time.time() - start_llm:.1f}s\n")

    # Créer le prompt
    prompt = f"""Tu es un conteur pour enfants. Raconte une histoire courte et amusante (3-4 phrases maximum) sur le thème suivant:

Thème: {transcription}

Histoire:"""

    print("Génération de l'histoire...")
    start_gen = time.time()

    response = llm(
        prompt,
        max_tokens=150,
        temperature=0.8,
        stop=["Thème:", "\n\n\n"],
        echo=False
    )

    story = response['choices'][0]['text'].strip()
    gen_time = time.time() - start_gen
    llm_total_time = time.time() - start_llm

    print("-" * 60)
    print(f"📖 HISTOIRE GÉNÉRÉE:")
    print(story)
    print("-" * 60)
    print(f"✓ Histoire générée en {gen_time:.1f}s (total LLM: {llm_total_time:.1f}s)\n")

except Exception as e:
    print(f"✗ Erreur LLM: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================================
# ÉTAPE 4: SYNTHÈSE VOCALE (TTS)
# ============================================================================
print("=" * 60)
print("ÉTAPE 4/4: SYNTHÈSE VOCALE")
print("=" * 60)

try:
    print("Génération de l'audio...")
    start_tts = time.time()

    # Générer l'audio avec Piper
    piper_cmd = [
        "/home/maxence/storybox/bin/piper/piper",
        "--model", "/home/maxence/models/piper/fr_FR-siwis-medium.onnx",
        "--output_file", "/tmp/pipeline_output.wav"
    ]

    result = subprocess.run(
        piper_cmd,
        input=story.encode('utf-8'),
        capture_output=True
    )

    if result.returncode != 0:
        print(f"✗ Erreur Piper: {result.stderr.decode()}")
        exit(1)

    tts_time = time.time() - start_tts
    print(f"✓ Audio généré en {tts_time:.1f}s\n")

    # Lire l'audio
    print("🔊 Lecture de l'histoire...")
    play_cmd = [
        "aplay",
        "-D", "plughw:0,0",
        "/tmp/pipeline_output.wav"
    ]

    subprocess.run(play_cmd, capture_output=True)
    print("✓ Lecture terminée\n")

except Exception as e:
    print(f"✗ Erreur TTS: {e}")
    exit(1)

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
total_time = time.time() - start_total

print("=" * 60)
print("✅ TEST COMPLET RÉUSSI!")
print("=" * 60)
print(f"\n⏱️  PERFORMANCES:")
print(f"   • Transcription (STT):  {stt_time:.1f}s")
print(f"   • Génération (LLM):     {llm_total_time:.1f}s")
print(f"   • Synthèse (TTS):       {tts_time:.1f}s")
print(f"   • TEMPS TOTAL:          {total_time:.1f}s")
print("\n" + "=" * 60)
print("🎉 Pipeline StoryBox opérationnel!")
print("=" * 60)
