#!/usr/bin/env python3
"""
Test Celeste LLM en local (Mac)

Script simple pour tester que Celeste fonctionne correctement avec Gemini.
Génère un plan d'histoire et un chapitre pour valider l'intégration.

Usage:
    python3 test_celeste_local.py

Author: StoryBox IA Team
Date: 2024-12-21
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm.celeste_llm import CelesteLLM
from app.utils.config import get_config


async def test_celeste():
    """Test complet de l'intégration Celeste"""

    print("=" * 70)
    print("🧪 TEST CELESTE LLM (Local Mac)")
    print("=" * 70)
    print()

    # Charger config
    try:
        config = get_config()
        print(f"✓ Configuration chargée")
        print(f"  Model: {config.llm.model_path}")
        print()
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return

    # Initialiser Celeste LLM
    try:
        llm = CelesteLLM(config.llm)
        print("✓ Celeste LLM initialisé")
        print()
    except Exception as e:
        print(f"❌ Erreur initialisation Celeste: {e}")
        print()
        print("Vérifiez que:")
        print("  1. GOOGLE_API_KEY est définie dans .env")
        print("  2. LLM_MODEL_PATH=gemini-1.5-flash (ou gemini-1.5-pro)")
        print("  3. Celeste est installé: uv pip install 'celeste-ai[text-generation]'")
        return

    # Test 1: Génération simple
    print("─" * 70)
    print("📝 TEST 1: Génération Simple")
    print("─" * 70)
    print()

    prompt_simple = "Écris une courte introduction (2 phrases) pour une histoire de pirates."
    print(f"Prompt: \"{prompt_simple}\"")
    print()

    try:
        response = await llm.generate(prompt_simple, max_tokens=100, temperature=0.7)

        if response:
            print(f"✓ Génération réussie ({len(response)} caractères)")
            print()
            print(f"Réponse:")
            print(f"  {response}")
            print()
        else:
            print("❌ Aucune réponse générée")
            return

    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Génération de plan
    print("─" * 70)
    print("📖 TEST 2: Génération de Plan (5 chapitres)")
    print("─" * 70)
    print()

    theme = "un petit robot qui découvre les émotions"
    print(f"Thème: \"{theme}\"")
    print()

    try:
        plan = await llm.generate_story_plan(theme, num_chapters=5)

        if plan:
            print(f"✓ Plan généré ({len(plan.chapters)} chapitres)")
            print()
            print("Chapitres:")
            for chapter in plan.chapters:
                print(f"  {chapter['number']}. {chapter['title']}")
                print(f"     → {chapter['summary']}")
                print()
        else:
            print("❌ Échec génération du plan")
            return

    except Exception as e:
        print(f"❌ Erreur génération plan: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 3: Génération de chapitre
    print("─" * 70)
    print("✍️  TEST 3: Génération du Chapitre 1")
    print("─" * 70)
    print()

    try:
        chapter_text = await llm.generate_chapter(
            plan,
            chapter_num=1,
            min_words=100,
            max_words=200
        )

        if chapter_text:
            word_count = len(chapter_text.split())
            print(f"✓ Chapitre 1 généré ({word_count} mots)")
            print()
            print(f"Titre: {plan.chapters[0]['title']}")
            print()
            print("Contenu:")
            print(chapter_text)
            print()
        else:
            print("❌ Échec génération du chapitre")
            return

    except Exception as e:
        print(f"❌ Erreur génération chapitre: {e}")
        import traceback
        traceback.print_exc()
        return

    # Résumé
    print("=" * 70)
    print("✅ TOUS LES TESTS RÉUSSIS!")
    print("=" * 70)
    print()
    print("Celeste LLM fonctionne correctement avec Gemini.")
    print("Vous pouvez maintenant lancer l'interface Streamlit.")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_celeste())
    except KeyboardInterrupt:
        print()
        print("🛑 Test interrompu")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
