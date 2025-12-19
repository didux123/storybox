#!/usr/bin/env python3
"""
Test Simple pour Raspberry Pi: Vosk STT + Gemini LLM avec Bouton GPIO

Test basique du pipeline:
1. Appuyer sur le bouton pour enregistrer
2. Relâcher pour lancer la transcription (Vosk)
3. Génération d'histoire (Gemini via Celeste)
4. Affichage de l'histoire dans le terminal

Prérequis:
    - Vosk model installé dans /home/maxence/models/vosk/
    - Celeste AI installé
    - Variable GOOGLE_API_KEY dans .env
    - Bouton GPIO sur pin 17

Usage sur Raspberry Pi:
    python3 test_pi_simple.py

Author: StoryBox IA Team
Date: 2024-12-19
"""

import asyncio
import sys
import time
import wave
import threading
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.stt.vosk_stt import VoskSTT
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config

# Import GPIO libraries
try:
    from gpiozero import Button
    import pyaudio
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️  GPIO/PyAudio non disponible - mode simulation")


# Configuration
AUDIO_FILE = "/tmp/storybox_recording.wav"
AUDIO_INPUT = "plughw:1,0"  # USB mic
BUTTON_PIN = 17
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
LOG_DIR = Path.home() / "storybox" / "logs"
LOG_FILE = LOG_DIR / "stories.log"


def log_session(transcription: str, story: str, stt_time: float, llm_time: float, total_time: float):
    """
    Log une session avec timestamp, transcription et histoire générée

    Args:
        transcription: Texte transcrit par Vosk
        story: Histoire générée par Gemini
        stt_time: Temps de transcription (s)
        llm_time: Temps de génération (s)
        total_time: Temps total (s)
    """
    # Créer le répertoire de logs si nécessaire
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Créer l'entrée de log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "transcription": transcription,
        "story": story,
        "timing": {
            "stt_seconds": round(stt_time, 2),
            "llm_seconds": round(llm_time, 2),
            "total_seconds": round(total_time, 2)
        }
    }

    # Écrire dans le fichier de log (mode append)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"📝 Session loggée dans: {LOG_FILE}")
    print()


class AudioRecorder:
    """Enregistreur audio en temps réel avec contrôle GPIO"""

    def __init__(self, output_file: str, device_name: str = "plughw:1,0"):
        self.output_file = output_file
        self.device_name = device_name
        self.is_recording = False
        self.frames = []
        self.audio = None
        self.stream = None

    def start_recording(self):
        """Démarre l'enregistrement"""
        self.is_recording = True
        self.frames = []

        # Initialiser PyAudio
        self.audio = pyaudio.PyAudio()

        # Trouver l'index du device
        device_index = None
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if self.device_name in info.get('name', ''):
                device_index = i
                break

        # Ouvrir le stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )

        # Thread d'enregistrement
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()

    def _record_loop(self):
        """Boucle d'enregistrement"""
        while self.is_recording:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Erreur enregistrement: {e}")
                break

    def stop_recording(self):
        """Arrête l'enregistrement et sauvegarde"""
        self.is_recording = False

        if self.record_thread:
            self.record_thread.join()

        # Fermer le stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio:
            self.audio.terminate()

        # Sauvegarder le fichier WAV
        if self.frames:
            wf = wave.open(self.output_file, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            return True
        return False


async def test_pipeline():
    """Test complet du pipeline avec bouton GPIO"""

    print("=" * 70)
    print("🎤 TEST SIMPLE - RASPBERRY PI (avec bouton GPIO)")
    print("=" * 70)
    print()
    print("Pipeline:")
    print("  1. Appuyez sur le bouton pour enregistrer")
    print("  2. Relâchez pour lancer la transcription (Vosk)")
    print("  3. Génération d'histoire (Gemini via Celeste)")
    print("  4. Affichage de l'histoire")
    print()
    print("=" * 70)
    print()

    if not GPIO_AVAILABLE:
        print("❌ GPIO/PyAudio requis sur Raspberry Pi")
        print("   Installez: pip install gpiozero RPi.GPIO pyaudio")
        return

    # ÉTAPE 1: Attendre le bouton et enregistrer
    print("─" * 70)
    print("📝 ÉTAPE 1/3: ENREGISTREMENT")
    print("─" * 70)
    print()
    print("🔵 Appuyez sur le bouton (GPIO pin 17) pour parler...")
    print()

    # Créer le bouton
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.1)
    recorder = AudioRecorder(AUDIO_FILE, AUDIO_INPUT)

    # Variable pour suivre l'état
    recording_started = False
    button_pressed = threading.Event()

    def on_button_press():
        nonlocal recording_started
        if not recording_started:
            print("🔴 ENREGISTREMENT EN COURS...")
            print("   (Relâchez le bouton quand vous avez fini)")
            print()
            recorder.start_recording()
            recording_started = True

    def on_button_release():
        if recording_started:
            button_pressed.set()

    # Attacher les callbacks
    button.when_pressed = on_button_press
    button.when_released = on_button_release

    # Attendre que le bouton soit relâché
    button_pressed.wait()

    # Arrêter l'enregistrement
    print("⏹️  Enregistrement terminé")
    print()

    if not recorder.stop_recording():
        print("❌ Échec de l'enregistrement (aucune donnée)")
        return

    # Nettoyer le bouton
    button.close()

    # ÉTAPE 2: Transcription avec Vosk
    print("─" * 70)
    print("📝 ÉTAPE 2/3: TRANSCRIPTION (Vosk)")
    print("─" * 70)
    print()

    try:
        print("Chargement du modèle Vosk...")
        start_stt = time.time()

        stt = VoskSTT()
        print("✓ Modèle chargé")
        print()

        print("Transcription en cours...")
        transcription = stt.transcribe(AUDIO_FILE)
        stt_time = time.time() - start_stt

        if not transcription:
            print("❌ Échec de la transcription")
            print("\nVérifiez que:")
            print("  - Vous avez parlé assez fort")
            print("  - Le micro fonctionne (arecord -l)")
            return

        print(f"✓ Transcription terminée en {stt_time:.1f}s")
        print()
        print(f"📝 Vous avez dit: '{transcription}'")
        print()

    except FileNotFoundError as e:
        print(f"❌ Modèle Vosk non trouvé: {e}")
        print("\nInstallez le modèle Vosk:")
        print("  cd /home/maxence/models/vosk")
        print("  wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip")
        print("  unzip vosk-model-small-fr-0.22.zip")
        return
    except Exception as e:
        print(f"❌ Erreur Vosk: {e}")
        return

    # ÉTAPE 3: Génération d'histoire avec Gemini
    print("─" * 70)
    print("💭 ÉTAPE 3/3: GÉNÉRATION D'HISTOIRE (Gemini via Celeste)")
    print("─" * 70)
    print()

    try:
        # Charger config
        config = get_config()

        # Vérifier que le model est bien Gemini
        if "gemini" not in config.llm.model_path.lower():
            print(f"⚠️  Note: Model configuré = {config.llm.model_path}")
            print("   Pour utiliser Gemini, configurez LLM_MODEL_PATH=gemini-2.0-flash-exp dans .env")
            print()

        # Initialiser Celeste LLM
        print("Initialisation de Celeste avec Gemini...")
        llm = CelesteLLM(config.llm)
        print(f"✓ Celeste initialisé (model: {config.llm.model_path})")
        print()

        # Générer l'histoire (juste 1 chapitre pour le test)
        print(f"Génération d'une histoire courte sur: '{transcription}'")
        print("Patience, Gemini réfléchit...")
        print()

        start_llm = time.time()

        # Créer un prompt simple pour une histoire courte
        prompt = f"""Écris une histoire courte et amusante (environ 150 mots) pour enfants sur le thème suivant: {transcription}

L'histoire doit:
- Être captivante et adaptée aux jeunes enfants
- Avoir un début, un développement et une fin
- Être écrite en français avec des phrases courtes

Histoire:"""

        response = await llm.generate(
            prompt,
            max_tokens=300,
            temperature=0.8
        )

        llm_time = time.time() - start_llm

        if not response:
            print("❌ Échec de la génération")
            print("\nVérifiez que:")
            print("  - GOOGLE_API_KEY est définie dans .env")
            print("  - Vous avez une connexion internet")
            print("  - Votre clé API est valide")
            return

        print(f"✓ Histoire générée en {llm_time:.1f}s")
        print()

        # Afficher l'histoire
        print("=" * 70)
        print("📖 VOTRE HISTOIRE")
        print("=" * 70)
        print()
        print(response)
        print()
        print("=" * 70)
        print()

        # Logger la session
        total_time = time.time() - start_stt
        log_session(transcription, response, stt_time, llm_time, total_time)

    except Exception as e:
        print(f"❌ Erreur LLM: {e}")
        import traceback
        traceback.print_exc()
        return

    # RÉSUMÉ
    print("✅ TEST TERMINÉ!")
    print()
    print(f"⏱️  TEMPS TOTAL: {total_time:.1f}s")
    print(f"   • STT (Vosk):       {stt_time:.1f}s")
    print(f"   • LLM (Gemini):     {llm_time:.1f}s")
    print()
    print("🎉 Le pipeline fonctionne!")
    print()


def main():
    """Point d'entrée principal"""
    try:
        asyncio.run(test_pipeline())
    except KeyboardInterrupt:
        print()
        print("🛑 Test interrompu")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
