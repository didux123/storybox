#!/usr/bin/env python3
"""
Test Simple pour Raspberry Pi: Vosk STT + Gemini LLM

Test basique du pipeline:
1. Enregistre 5 secondes d'audio
2. Transcrit avec Vosk
3. Génère une histoire avec Gemini (via Celeste)
4. Affiche l'histoire dans le terminal

Prérequis:
    - Vosk model installé dans /home/maxence/models/vosk/
    - Celeste AI installé
    - Variable GOOGLE_API_KEY dans .env

Usage sur Raspberry Pi:
    python3 test_pi_simple.py

Author: StoryBox IA Team
Date: 2024-12-19
"""

import asyncio
import sys
import time
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.stt.vosk_stt import VoskSTT
from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config


# Configuration audio
AUDIO_FILE = "/tmp/storybox_recording.wav"
AUDIO_INPUT = "plughw:1,0"  # USB mic
RECORD_DURATION = 5  # secondes


def record_audio(duration: int = 5) -> bool:
    """
    Enregistre l'audio depuis le micro USB

    Args:
        duration: Durée d'enregistrement en secondes

    Returns:
        True si l'enregistrement a réussi
    """
    print(f"🔴 ENREGISTREMENT ({duration}s)...")
    print("   Parlez maintenant!")
    print()

    try:
        cmd = [
            "arecord",
            "-D", AUDIO_INPUT,
            "-f", "S16_LE",
            "-r", "16000",
            "-c", "1",
            "-d", str(duration),
            AUDIO_FILE
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=duration + 2
        )

        if result.returncode == 0:
            print("⏹️  Enregistrement terminé")
            print()
            return True
        else:
            print(f"❌ Erreur d'enregistrement: {result.stderr.decode()}")
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


async def test_pipeline():
    """Test complet du pipeline"""

    print("=" * 70)
    print("🎤 TEST SIMPLE - RASPBERRY PI")
    print("=" * 70)
    print()
    print("Pipeline:")
    print("  1. Enregistrement audio (5 secondes)")
    print("  2. Transcription (Vosk)")
    print("  3. Génération d'histoire (Gemini via Celeste)")
    print("  4. Affichage de l'histoire")
    print()
    print("=" * 70)
    print()

    # ÉTAPE 1: Enregistrement
    print("─" * 70)
    print("📝 ÉTAPE 1/3: ENREGISTREMENT")
    print("─" * 70)
    print()

    if not record_audio(RECORD_DURATION):
        print("❌ Échec de l'enregistrement")
        return

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

    except Exception as e:
        print(f"❌ Erreur LLM: {e}")
        import traceback
        traceback.print_exc()
        return

    # RÉSUMÉ
    total_time = time.time() - start_stt

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
