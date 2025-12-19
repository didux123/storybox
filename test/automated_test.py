"""
Automated test for StoryBox IA components
Tests each module without requiring user interaction
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.config import get_config
from app.utils.logger import get_logger
from app.tts.piper_tts import PiperTTS
from app.stt.whisper_stt import WhisperSTT
from app.llm.llama_llm import LlamaLLM
from app.llm.planner import Planner
from app.llm.story_gen import StoryGenerator

logger = get_logger(__name__)


def test_config():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    try:
        config = get_config()
        print(f"✓ Config loaded successfully")
        print(f"  → STT model: {Path(config.stt.model_path).name}")
        print(f"  → LLM model: {Path(config.llm.model_path).name}")
        print(f"  → TTS model: {Path(config.tts.model_path).name}")
        print(f"  → Audio max duration: {config.audio.input.max_duration_s}s")
        return True
    except Exception as e:
        print(f"✗ Config failed: {e}")
        return False


def test_tts():
    """Test TTS synthesis"""
    print("\n" + "=" * 60)
    print("Testing TTS (Piper)")
    print("=" * 60)

    try:
        config = get_config()
        tts = PiperTTS(config.tts)
        print(f"✓ TTS initialized")

        # Test synthesis
        test_text = "Bonjour, ceci est un test."
        audio_data = tts.synthesize(test_text)

        if audio_data:
            size_kb = len(audio_data) / 1024
            duration = tts.get_audio_duration(audio_data)
            print(f"✓ Synthesis successful: {size_kb:.1f} KB, {duration:.1f}s")

            # Save test file
            output_file = Path("test_automated_tts.wav")
            tts.save_audio(audio_data, output_file)
            print(f"  → Saved to: {output_file}")
            return True
        else:
            print(f"✗ Synthesis failed")
            return False

    except Exception as e:
        print(f"✗ TTS failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stt():
    """Test STT transcription"""
    print("\n" + "=" * 60)
    print("Testing STT (Whisper)")
    print("=" * 60)

    try:
        config = get_config()
        stt = WhisperSTT(config.stt)
        print(f"✓ STT initialized")

        # Use the TTS output as test input
        test_audio = Path("test_automated_tts.wav")
        if not test_audio.exists():
            print(f"⚠ No test audio file, skipping STT test")
            return True

        # Transcribe
        result = stt.transcribe_file(str(test_audio))

        if result:
            print(f"✓ Transcription successful")
            print(f"  → Text: {result.text}")
            print(f"  → Confidence: {result.confidence:.2f}")
            return True
        else:
            print(f"✗ Transcription failed")
            return False

    except Exception as e:
        print(f"✗ STT failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm():
    """Test LLM generation"""
    print("\n" + "=" * 60)
    print("Testing LLM (Llama)")
    print("=" * 60)

    try:
        config = get_config()
        llm = LlamaLLM(config.llm)
        print(f"✓ LLM initialized")

        # Test simple generation
        prompt = "Réponds en une phrase: quelle est ta fonction?"
        response = llm.generate(prompt, max_tokens=50)

        if response:
            print(f"✓ Generation successful")
            print(f"  → Response: {response[:100]}...")
            return True
        else:
            print(f"✗ Generation failed")
            return False

    except Exception as e:
        print(f"✗ LLM failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_planner():
    """Test story planner"""
    print("\n" + "=" * 60)
    print("Testing Planner")
    print("=" * 60)

    try:
        config = get_config()
        planner = Planner(config.llm)
        print(f"✓ Planner initialized")

        # Test plan generation (3 chapters for speed)
        theme = "pirates"
        plan = planner.create_plan(theme, num_chapters=3)

        if plan and plan.chapters:
            print(f"✓ Plan generated: {len(plan.chapters)} chapters")
            for i, chapter in enumerate(plan.chapters, 1):
                print(f"  → Chapter {i}: {chapter.title}")
            return True
        else:
            print(f"✗ Plan generation failed")
            return False

    except Exception as e:
        print(f"✗ Planner failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_story_gen():
    """Test story generator"""
    print("\n" + "=" * 60)
    print("Testing Story Generator")
    print("=" * 60)

    try:
        config = get_config()
        story_gen = StoryGenerator(config.llm)
        planner = Planner(config.llm)
        print(f"✓ Story generator initialized")

        # Generate a simple plan first
        theme = "pirates"
        plan = planner.create_plan(theme, num_chapters=2)

        if not plan:
            print(f"⚠ Could not generate plan, skipping story test")
            return True

        # Generate first chapter
        print(f"  Generating chapter 1...")
        chapter_result = next(story_gen.generate_story(plan))

        if chapter_result and chapter_result.text:
            print(f"✓ Chapter generated: {len(chapter_result.text)} chars")
            print(f"  → Preview: {chapter_result.text[:100]}...")
            return True
        else:
            print(f"✗ Chapter generation failed")
            return False

    except Exception as e:
        print(f"✗ Story generator failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("StoryBox IA - Automated Component Tests")
    print("=" * 60)

    results = {
        "Config": test_config(),
        "TTS": test_tts(),
        "STT": test_stt(),
        "LLM": test_llm(),
        "Planner": test_planner(),
        "Story Gen": test_story_gen()
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:15} {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} tests passed")

    # Cleanup
    print("\n" + "=" * 60)
    print("Cleaning up test files...")
    test_files = ["test_automated_tts.wav"]
    for f in test_files:
        path = Path(f)
        if path.exists():
            path.unlink()
            print(f"  → Removed {f}")

    print("=" * 60)

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
