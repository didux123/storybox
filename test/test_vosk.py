#!/usr/bin/env python3
"""Test rapide de Vosk STT (dictée vocale temps réel)"""
import subprocess
import time
import json
from vosk import Model, KaldiRecognizer
import wave

print("=== Test Vosk STT (Dictée Vocale Rapide) ===\n")

# Étape 1: Enregistrement audio
print("ÉTAPE 1: Enregistrement audio (5 secondes)")
print("Parlez maintenant...")

cmd = [
    "arecord",
    "-D", "plughw:1,0",
    "-f", "S16_LE",
    "-r", "16000",
    "-c", "1",
    "-d", "5",
    "/tmp/test_vosk.wav"
]

subprocess.run(cmd, capture_output=True)
print("✓ Enregistrement terminé\n")

# Étape 2: Transcription avec Vosk
print("ÉTAPE 2: Transcription avec Vosk")
print("Chargement du modèle...")
start = time.time()

try:
    # Charger le modèle Vosk
    model = Model("/home/maxence/models/vosk/vosk-model-small-fr-0.22")

    load_time = time.time() - start
    print(f"✓ Modèle chargé en {load_time:.1f}s\n")

    # Ouvrir le fichier audio
    wf = wave.open("/tmp/test_vosk.wav", "rb")

    # Vérifier le format audio
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        print(f"✗ Format audio incorrect!")
        print(f"   Channels: {wf.getnchannels()} (attendu: 1)")
        print(f"   Sample width: {wf.getsampwidth()} (attendu: 2)")
        print(f"   Frame rate: {wf.getframerate()} (attendu: 16000)")
        exit(1)

    # Créer le recognizer
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(False)

    print("Transcription en cours...")
    start_transcribe = time.time()

    # Transcrire l'audio (sans parser les résultats intermédiaires)
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)

    # Récupérer uniquement le résultat final
    final_result = json.loads(rec.FinalResult())

    transcribe_time = time.time() - start_transcribe

    print(f"✓ Transcription terminée en {transcribe_time:.1f}s\n")

    # Afficher les résultats
    print("=" * 50)
    print("TRANSCRIPTION:")
    print("=" * 50)

    text = final_result.get("text", "")
    print(text if text else "(aucun texte détecté)")

    print("=" * 50)
    print(f"\n✓ Test Vosk réussi!")
    print(f"Temps total: {load_time + transcribe_time:.1f}s")
    print(f"  - Chargement modèle: {load_time:.1f}s")
    print(f"  - Transcription: {transcribe_time:.1f}s")

except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
