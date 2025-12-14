#!/usr/bin/env python3
"""
Test script for Piper TTS voice generation
Generates sample audio files to verify TTS quality
"""

import subprocess
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PIPER_MODEL = PROJECT_ROOT / "models/piper/fr_FR-siwis-medium.onnx"
OUTPUT_DIR = PROJECT_ROOT / "test/audio_samples"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Test texts
TEST_TEXTS = {
    "greeting": "Bonjour ! Je suis la boîte à histoires. Maintenez le bouton et dites-moi quel genre d'histoire vous voulez entendre.",

    "chapter_intro": "Chapitre premier : Le départ de l'aventure. Il était une fois, dans un petit village au bord de la mer, un jeune pirate nommé Lucas.",

    "story_sample": """
    Lucas avait toujours rêvé de parcourir les océans à la recherche de trésors cachés.
    Un matin, il découvrit une vieille carte dans le grenier de sa grand-mère.
    Cette carte montrait le chemin vers une île mystérieuse où dormait un fabuleux trésor.
    """,

    "error": "Désolé, je n'ai pas bien compris votre demande. Pouvez-vous répéter s'il vous plaît ?",

    "processing": "Laissez-moi réfléchir à une belle histoire pour vous. Cela ne prendra qu'un instant.",
}

def generate_audio(text: str, output_file: Path):
    """Generate audio file using Piper TTS"""
    try:
        # Run piper command
        result = subprocess.run(
            ["piper", "-m", str(PIPER_MODEL), "-f", str(output_file)],
            input=text,
            text=True,
            capture_output=True,
            check=True
        )

        file_size = output_file.stat().st_size
        print(f"✓ Generated: {output_file.name} ({file_size} bytes)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {output_file.name}")
        print(f"  Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Error: 'piper' command not found")
        print("  Install: pip install piper-tts")
        return False

def main():
    print("=" * 60)
    print("StoryBox IA - TTS Voice Generation Test")
    print("=" * 60)
    print(f"Model: {PIPER_MODEL.name}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Check if model exists
    if not PIPER_MODEL.exists():
        print(f"✗ Error: Model not found at {PIPER_MODEL}")
        print("  Download models first (see README.md)")
        sys.exit(1)

    # Generate audio samples
    success_count = 0
    total_count = len(TEST_TEXTS)

    for name, text in TEST_TEXTS.items():
        output_file = OUTPUT_DIR / f"{name}.wav"
        if generate_audio(text, output_file):
            success_count += 1

    print()
    print("=" * 60)
    print(f"Results: {success_count}/{total_count} files generated")
    print("=" * 60)

    if success_count == total_count:
        print("✓ All TTS tests passed!")
        print(f"\nListen to samples: afplay {OUTPUT_DIR}/*.wav")
        return 0
    else:
        print("✗ Some TTS tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
