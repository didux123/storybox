#!/usr/bin/env python3
"""
Test Cloud Pipeline: Dictation + Celeste LLM

Interactive test for the cloud-based StoryBox pipeline:
1. Press SPACE to start recording (simulates button press)
2. Speak your story theme
3. Press SPACE to stop recording (simulates button release)
4. Automatic transcription using system dictation
5. Story generation using Celeste cloud LLM
6. Display the generated story

This tests the core pipeline without TTS (TTS will be added later with Gradio).

Requirements:
    pip install SpeechRecognition 'celeste-ai[text-generation]' pyaudio

Environment:
    Set OPENAI_API_KEY in .env file

Usage:
    python test/test_cloud_pipeline.py

Author: StoryBox IA Team
Date: 2024-12-19
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.stt.system_dictation import SystemDictation
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config

# For audio recording
try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️  PyAudio not installed. Install with: pip install pyaudio")


class CloudPipelineTest:
    """Interactive test for cloud-based StoryBox pipeline"""

    def __init__(self):
        """Initialize test components"""
        self.config = get_config()
        self.stt = SystemDictation(language="fr-FR")
        self.llm = CelesteLLM(self.config.llm)
        self.recording = False
        self.audio_file = "/tmp/test_recording.wav"

    def record_audio(self, duration: int = 10) -> bool:
        """
        Record audio from microphone

        Args:
            duration: Maximum recording duration in seconds

        Returns:
            True if recording successful
        """
        if not PYAUDIO_AVAILABLE:
            print("❌ PyAudio not available, cannot record")
            return False

        print("🔴 ENREGISTREMENT... (parlez maintenant)")
        print(f"   Durée max: {duration} secondes")
        print()

        try:
            # Audio parameters
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            audio = pyaudio.PyAudio()

            # Open stream
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            frames = []

            # Record for duration
            for i in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)

            print("⏹️  Enregistrement terminé")
            print()

            # Stop and close stream
            stream.stop_stream()
            stream.close()
            audio.terminate()

            # Save to WAV file
            wf = wave.open(self.audio_file, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            return True

        except Exception as e:
            print(f"❌ Erreur d'enregistrement: {e}")
            return False

    async def run_pipeline(self):
        """Run the complete cloud pipeline"""

        print("=" * 70)
        print("🎤 TEST PIPELINE CLOUD - STORYBOX")
        print("=" * 70)
        print()
        print("Pipeline:")
        print("  1. Enregistrement audio (dictée vocale)")
        print("  2. Transcription (Google Speech Recognition)")
        print("  3. Génération d'histoire (Celeste LLM)")
        print("  4. Affichage du résultat")
        print()
        print("=" * 70)
        print()

        # Check if STT is available
        if not self.stt.is_available():
            print("❌ System dictation non disponible")
            print("\nInstallez SpeechRecognition:")
            print("  pip install SpeechRecognition")
            return

        # STEP 1: Record audio
        print("─" * 70)
        print("📝 ÉTAPE 1/3: ENREGISTREMENT")
        print("─" * 70)
        print()

        input("Appuyez sur ENTRÉE pour commencer l'enregistrement...")

        if not self.record_audio(duration=5):
            print("❌ Échec de l'enregistrement")
            return

        # STEP 2: Transcription
        print("─" * 70)
        print("📝 ÉTAPE 2/3: TRANSCRIPTION")
        print("─" * 70)
        print()

        start_stt = time.time()
        print("Transcription en cours...")

        transcription = self.stt.transcribe_simple(self.audio_file)
        stt_time = time.time() - start_stt

        if not transcription:
            print("❌ Échec de la transcription")
            print("\nVérifiez que:")
            print("  - Vous avez parlé assez fort")
            print("  - Le microphone fonctionne")
            print("  - Vous avez une connexion internet (Google Speech API)")
            return

        print(f"✓ Transcription terminée en {stt_time:.1f}s")
        print()
        print(f"📝 Vous avez dit: '{transcription}'")
        print()

        # STEP 3: Story generation with Celeste LLM
        print("─" * 70)
        print("💭 ÉTAPE 3/3: GÉNÉRATION D'HISTOIRE (Celeste LLM)")
        print("─" * 70)
        print()

        start_llm = time.time()

        # Generate story plan
        print("Génération du plan de l'histoire...")
        plan = await self.llm.generate_story_plan(transcription, num_chapters=5)

        if not plan:
            print("❌ Échec de la génération du plan")
            print("\nVérifiez que:")
            print("  - OPENAI_API_KEY est définie dans .env")
            print("  - Vous avez une connexion internet")
            print("  - Votre clé API est valide")
            return

        plan_time = time.time() - start_llm
        print(f"✓ Plan généré en {plan_time:.1f}s")
        print()
        print("📖 PLAN DE L'HISTOIRE:")
        print("─" * 70)
        for chapter in plan.chapters:
            print(f"{chapter['number']}. {chapter['title']}")
            print(f"   → {chapter['summary']}")
        print("─" * 70)
        print()

        # Generate first chapter
        print("Génération du chapitre 1...")
        start_chapter = time.time()

        chapter1 = await self.llm.generate_chapter(plan, chapter_num=1)

        if not chapter1:
            print("❌ Échec de la génération du chapitre")
            return

        chapter_time = time.time() - start_chapter
        llm_time = time.time() - start_llm

        print(f"✓ Chapitre 1 généré en {chapter_time:.1f}s")
        print()
        print("📖 CHAPITRE 1:")
        print("─" * 70)
        print(chapter1)
        print("─" * 70)
        print()

        # SUMMARY
        total_time = time.time() - start_stt

        print("=" * 70)
        print("✅ PIPELINE TERMINÉ!")
        print("=" * 70)
        print(f"⏱️  TEMPS TOTAL: {total_time:.1f}s")
        print(f"   • STT (Transcription):  {stt_time:.1f}s")
        print(f"   • LLM (Plan):           {plan_time:.1f}s")
        print(f"   • LLM (Chapitre 1):     {chapter_time:.1f}s")
        print(f"   • LLM Total:            {llm_time:.1f}s")
        print("=" * 70)
        print()
        print("✨ Pipeline cloud fonctionnel!")
        print("   → Prochaine étape: Ajouter TTS avec Gradio quand disponible")
        print()


async def main():
    """Main entry point"""
    try:
        test = CloudPipelineTest()
        await test.run_pipeline()
    except KeyboardInterrupt:
        print()
        print("🛑 Test interrompu")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
