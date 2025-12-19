#!/usr/bin/env python3
"""Test interactif hold-to-talk : Bouton → Enregistrement → STT → LLM → TTS"""
import RPi.GPIO as GPIO
import subprocess
import time
import json
import wave
from vosk import Model, KaldiRecognizer
from llama_cpp import Llama
import threading
import sys

# Configuration
BUTTON_PIN = 17
AUDIO_INPUT = "plughw:1,0"
AUDIO_OUTPUT = "plughw:0,0"
AUDIO_FILE = "/tmp/hold_to_talk.wav"
VOSK_MODEL = "/home/maxence/models/vosk/vosk-model-small-fr-0.22"
LLM_MODEL = "/home/maxence/models/llm/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"
PIPER_BIN = "/home/maxence/storybox/bin/piper/piper"
PIPER_MODEL = "/home/maxence/models/piper/fr_FR-siwis-medium.onnx"

print("=" * 70)
print("🎤 TEST HOLD-TO-TALK - STORYBOX PIPELINE COMPLET")
print("=" * 70)
print()
print("Instructions:")
print("  1. Maintenez le bouton enfoncé pour enregistrer")
print("  2. Relâchez pour lancer le pipeline STT → LLM → TTS")
print("  3. Appuyez sur Ctrl+C pour quitter")
print()
print("=" * 70)
print()

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables globales
recording_process = None
is_recording = False

def start_recording():
    """Démarre l'enregistrement audio"""
    global recording_process, is_recording

    print("🔴 ENREGISTREMENT EN COURS... (parlez maintenant)")

    cmd = [
        "arecord",
        "-D", AUDIO_INPUT,
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        AUDIO_FILE
    ]

    recording_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    is_recording = True

def stop_recording():
    """Arrête l'enregistrement audio"""
    global recording_process, is_recording

    if recording_process:
        recording_process.terminate()
        recording_process.wait()
        is_recording = False
        print("⏹️  Enregistrement terminé")
        print()

def process_pipeline():
    """Pipeline complet: STT → LLM → TTS"""

    start_total = time.time()

    # ========================================================================
    # ÉTAPE 1: TRANSCRIPTION (STT)
    # ========================================================================
    print("-" * 70)
    print("📝 ÉTAPE 1/3: TRANSCRIPTION (Vosk STT)")
    print("-" * 70)

    try:
        print("Chargement du modèle Vosk...")
        start_stt = time.time()

        model_vosk = Model(VOSK_MODEL)
        wf = wave.open(AUDIO_FILE, "rb")
        rec = KaldiRecognizer(model_vosk, wf.getframerate())
        rec.SetWords(False)

        print("Transcription...")
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        transcription = result.get("text", "").strip()

        stt_time = time.time() - start_stt

        print(f"✓ Transcription terminée en {stt_time:.1f}s")
        print(f"📝 Vous avez dit: '{transcription}'")
        print()

        if not transcription:
            print("⚠️  Aucun texte détecté. Essayez de parler plus fort.")
            return

    except Exception as e:
        print(f"❌ Erreur STT: {e}")
        return

    # ========================================================================
    # ÉTAPE 2: GÉNÉRATION D'HISTOIRE (LLM)
    # ========================================================================
    print("-" * 70)
    print("💭 ÉTAPE 2/3: GÉNÉRATION D'HISTOIRE (TinyLlama)")
    print("-" * 70)

    try:
        print("Chargement du modèle LLM...")
        start_llm = time.time()

        llm = Llama(
            model_path=LLM_MODEL,
            n_ctx=256,
            n_threads=4,
            n_batch=128,
            verbose=False
        )

        load_time = time.time() - start_llm
        print(f"✓ Modèle chargé en {load_time:.1f}s")

        # Prompt optimisé
        prompt = f"Raconte une histoire courte et amusante (2-3 phrases) sur: {transcription}\n\nHistoire:"

        print("Génération de l'histoire...")
        start_gen = time.time()

        response = llm(
            prompt,
            max_tokens=60,
            temperature=0.8,
            stop=["\n\n", "Histoire:", "Raconte:", ".\""],
            echo=False
        )

        story = response['choices'][0]['text'].strip()
        gen_time = time.time() - start_gen
        llm_time = time.time() - start_llm

        print(f"✓ Histoire générée en {gen_time:.1f}s (total: {llm_time:.1f}s)")
        print()
        print("📖 HISTOIRE:")
        print("-" * 70)
        print(story)
        print("-" * 70)
        print()

    except Exception as e:
        print(f"❌ Erreur LLM: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # ÉTAPE 3: SYNTHÈSE VOCALE (TTS)
    # ========================================================================
    print("-" * 70)
    print("🔊 ÉTAPE 3/3: SYNTHÈSE VOCALE (Piper TTS)")
    print("-" * 70)

    try:
        print("Génération de l'audio...")
        start_tts = time.time()

        # Générer l'audio
        piper_cmd = [
            PIPER_BIN,
            "--model", PIPER_MODEL,
            "--output_file", "/tmp/story_output.wav"
        ]

        result = subprocess.run(
            piper_cmd,
            input=story.encode('utf-8'),
            capture_output=True
        )

        if result.returncode != 0:
            print(f"❌ Erreur Piper: {result.stderr.decode()}")
            return

        tts_time = time.time() - start_tts
        print(f"✓ Audio généré en {tts_time:.1f}s")

        # Lire l'audio
        print("🔊 Lecture de l'histoire...")
        play_cmd = ["aplay", "-D", AUDIO_OUTPUT, "/tmp/story_output.wav"]
        subprocess.run(play_cmd, capture_output=True)

        print("✓ Lecture terminée")
        print()

    except Exception as e:
        print(f"❌ Erreur TTS: {e}")
        return

    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    total_time = time.time() - start_total

    print("=" * 70)
    print("✅ PIPELINE TERMINÉ!")
    print("=" * 70)
    print(f"⏱️  TEMPS TOTAL: {total_time:.1f}s")
    print(f"   • STT (Transcription):  {stt_time:.1f}s")
    print(f"   • LLM (Génération):     {llm_time:.1f}s")
    print(f"   • TTS (Synthèse):       {tts_time:.1f}s")
    print("=" * 70)
    print()
    print("✨ Prêt pour une nouvelle histoire ! Maintenez le bouton...")
    print()

# Boucle principale
try:
    print("⏳ En attente... Maintenez le bouton pour commencer")
    print()

    last_state = GPIO.input(BUTTON_PIN)

    while True:
        current_state = GPIO.input(BUTTON_PIN)

        # Bouton pressé (transition HIGH → LOW)
        if last_state == GPIO.HIGH and current_state == GPIO.LOW:
            start_recording()

        # Bouton relâché (transition LOW → HIGH)
        elif last_state == GPIO.LOW and current_state == GPIO.HIGH:
            stop_recording()
            print("⚙️  Traitement en cours...")
            print()
            process_pipeline()
            print("⏳ En attente... Maintenez le bouton pour une nouvelle histoire")
            print()

        last_state = current_state
        time.sleep(0.05)  # Debounce 50ms

except KeyboardInterrupt:
    print()
    print("🛑 Arrêt du programme...")
    if is_recording:
        stop_recording()
    GPIO.cleanup()
    print("✓ Nettoyage terminé. Au revoir!")
    sys.exit(0)

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    if is_recording:
        stop_recording()
    GPIO.cleanup()
    sys.exit(1)
