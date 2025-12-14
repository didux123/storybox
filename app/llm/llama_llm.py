"""
Llama LLM Wrapper for StoryBox IA

Handles text generation using llama.cpp for story planning and generation.
Optimized for Raspberry Pi with quantized 3B models.

Features:
- Story plan generation (10 chapters with JSON output)
- Chapter-by-chapter story generation with context
- Streaming token generation
- Prompt template management
- Memory-efficient context handling

Usage:
    from app.llm.llama_llm import LlamaLLM

    llm = LlamaLLM(config.llm)
    plan = llm.generate_story_plan("pirates et trésor")
    chapter = llm.generate_chapter(plan, chapter_num=1)

Author: StoryBox IA Team
Date: 2024-12
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass

from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import LLMConfig


logger = get_logger(__name__)


@dataclass
class StoryPlan:
    """
    Story plan with chapters

    Attributes:
        theme: Story theme/topic
        chapters: List of chapters with number, title, summary
    """
    theme: str
    chapters: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'theme': self.theme,
            'chapters': self.chapters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoryPlan':
        """Create from dictionary"""
        return cls(
            theme=data.get('theme', ''),
            chapters=data.get('chapters', [])
        )


class LlamaLLM:
    """
    Llama LLM engine wrapper

    Generates story plans and chapters using llama.cpp.
    Optimized for 3B quantized models on Raspberry Pi.
    """

    def __init__(self, config: LLMConfig, llama_bin_path: Optional[Path] = None):
        """
        Initialize Llama LLM

        Args:
            config: LLM configuration object
            llama_bin_path: Optional custom path to llama-cli binary
                            Defaults to checking common locations

        Raises:
            FileNotFoundError: If model or binary not found
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Validate model exists
        if not Path(config.model_path).exists():
            raise FileNotFoundError(f"LLM model not found: {config.model_path}")

        # Find llama-cli binary
        self.llama_bin = self._find_llama_binary(llama_bin_path)

        self.logger.info("Llama LLM initialized successfully")
        self.logger.info(f"Binary: {self.llama_bin}")
        self.logger.info(f"Model: {Path(config.model_path).name}")
        self.logger.info(f"Context: {config.context_tokens} tokens")
        self.logger.info(f"Threads: {config.threads}")
        self.logger.info(f"Temperature: {config.temperature}")

    def _find_llama_binary(self, custom_path: Optional[Path] = None) -> Path:
        """
        Find llama-cli binary

        Checks (in order):
        1. Custom path if provided
        2. Project bin/ directory
        3. /tmp/llama.cpp/build/bin (Mac development)
        4. System PATH

        Args:
            custom_path: Optional custom binary path

        Returns:
            Path to llama-cli binary

        Raises:
            FileNotFoundError: If binary not found
        """
        if custom_path and custom_path.exists():
            return custom_path

        # Common locations
        search_paths = [
            # Project bin (after deployment)
            Path(__file__).parent.parent.parent / "bin" / "llama-cli",
            # Mac development location
            Path("/tmp/llama.cpp/build/bin/llama-cli"),
            # Raspberry Pi build location
            Path.home() / "projects" / "storybox" / "bin" / "llama-cli",
        ]

        for path in search_paths:
            if path.exists() and path.is_file():
                self.logger.info(f"Found llama-cli at: {path}")
                return path

        # Try system PATH
        try:
            result = subprocess.run(
                ['which', 'llama-cli'],
                capture_output=True,
                text=True,
                check=True
            )
            path = Path(result.stdout.strip())
            if path.exists():
                return path
        except subprocess.CalledProcessError:
            pass

        raise FileNotFoundError(
            "llama-cli not found. Compile llama.cpp or specify llama_bin_path. "
            "See docs/MAC_DEVELOPMENT.md or docs/RASPBERRY_PI_SETUP.md"
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (overrides config)
            stop_sequences: Sequences that stop generation

        Returns:
            Generated text or None if generation failed

        Example:
            >>> llm = LlamaLLM(config.llm)
            >>> text = llm.generate("Il était une fois")
            >>> print(text)
            "Il était une fois un jeune garçon..."
        """
        if not prompt:
            self.logger.warning("Empty prompt provided")
            return None

        self.logger.debug(f"Generating with prompt: {prompt[:50]}...")

        with TimingContext("llm_generation", log_metric=True):
            try:
                # Build llama command
                cmd = [
                    str(self.llama_bin),
                    '-m', str(self.config.model_path),
                    '-n', str(max_tokens),
                    '-c', str(self.config.context_tokens),
                    '-t', str(self.config.threads),
                    '--temp', str(temperature or self.config.temperature),
                    '--top-p', str(self.config.top_p),
                    '--repeat-penalty', str(self.config.repeat_penalty),
                    '-ngl', str(self.config.n_gpu_layers),
                    '-p', prompt,
                    '--no-display-prompt',  # Don't echo prompt in output
                ]

                # Add stop sequences if provided
                if stop_sequences:
                    for seq in stop_sequences:
                        cmd.extend(['--reverse-prompt', seq])

                # Run llama
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minute timeout
                )

                # Parse output
                output = result.stdout.strip()

                if output:
                    self.logger.info(f"Generated {len(output)} chars")
                    log_metric("llm_chars_generated", len(output))

                    # Estimate tokens (rough: 1 token ≈ 4 chars)
                    estimated_tokens = len(output) / 4
                    log_metric("llm_tokens_generated", estimated_tokens)

                    return output
                else:
                    self.logger.warning("No output from LLM")
                    return None

            except subprocess.TimeoutExpired:
                self.logger.error("LLM generation timeout (120s)")
                return None
            except subprocess.CalledProcessError as e:
                self.logger.error(f"LLM generation failed: {e.stderr}")
                return None
            except Exception as e:
                self.logger.error(f"LLM generation error: {e}", exc_info=True)
                return None

    def generate_story_plan(self, theme: str, num_chapters: int = 10) -> Optional[StoryPlan]:
        """
        Generate a story plan with chapters

        Creates a structured plan with:
        - Chapter numbers (1-10)
        - Chapter titles
        - Chapter summaries (1 sentence each)

        Args:
            theme: Story theme/topic (e.g., "pirates et trésor")
            num_chapters: Number of chapters (default 10)

        Returns:
            StoryPlan object or None if generation failed

        Example:
            >>> llm = LlamaLLM(config.llm)
            >>> plan = llm.generate_story_plan("pirates et trésor")
            >>> for chapter in plan.chapters:
            ...     print(f"{chapter['number']}. {chapter['title']}")
        """
        self.logger.info(f"Generating story plan: {theme} ({num_chapters} chapters)")

        # Use configured prompt template or default
        prompt_template = self.config.prompts.plan or self._get_default_plan_prompt()

        # Fill in template
        prompt = prompt_template.format(
            theme=theme,
            num_chapters=num_chapters
        )

        with TimingContext("story_plan_generation", log_metric=True):
            # Generate with more tokens for full plan
            output = self.generate(
                prompt,
                max_tokens=1500,  # ~10 chapters * ~30 tokens per chapter
                temperature=0.7   # Balanced creativity
            )

            if not output:
                return None

            # Parse JSON output
            plan = self._parse_story_plan(output, theme)

            if plan:
                self.logger.info(f"Generated plan with {len(plan.chapters)} chapters")
                return plan
            else:
                self.logger.error("Failed to parse story plan from LLM output")
                return None

    def _get_default_plan_prompt(self) -> str:
        """Get default story plan prompt template"""
        return """Génère un plan de {num_chapters} chapitres cohérents sur le thème suivant : {theme}.

Chaque chapitre doit contenir :
- Un titre court et accrocheur
- Un résumé en 1 phrase

Réponds UNIQUEMENT au format JSON suivant (sans texte supplémentaire) :
{{
  "chapters": [
    {{"number": 1, "title": "Titre du chapitre 1", "summary": "Résumé en une phrase."}},
    {{"number": 2, "title": "Titre du chapitre 2", "summary": "Résumé en une phrase."}},
    ...
  ]
}}

JSON :"""

    def _parse_story_plan(self, output: str, theme: str) -> Optional[StoryPlan]:
        """
        Parse story plan from LLM output

        Expects JSON format:
        {
          "chapters": [
            {"number": 1, "title": "...", "summary": "..."},
            ...
          ]
        }

        Args:
            output: LLM generated text
            theme: Original theme

        Returns:
            StoryPlan or None if parsing failed
        """
        try:
            # Find JSON in output (might have extra text)
            json_match = re.search(r'\{[\s\S]*\}', output)
            if not json_match:
                self.logger.error("No JSON found in LLM output")
                return None

            json_str = json_match.group(0)

            # Parse JSON
            data = json.loads(json_str)

            # Validate structure
            if 'chapters' not in data:
                self.logger.error("Missing 'chapters' key in JSON")
                return None

            # Create StoryPlan
            plan = StoryPlan(theme=theme, chapters=data['chapters'])

            return plan

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self.logger.debug(f"LLM output: {output}")
            return None
        except Exception as e:
            self.logger.error(f"Plan parsing error: {e}", exc_info=True)
            return None

    def generate_chapter(
        self,
        plan: StoryPlan,
        chapter_num: int,
        cumulative_context: str = "",
        min_words: int = 150,
        max_words: int = 300
    ) -> Optional[str]:
        """
        Generate a single chapter

        Args:
            plan: Story plan with all chapters
            chapter_num: Chapter number to generate (1-indexed)
            cumulative_context: Summary of previous chapters
            min_words: Minimum words per chapter
            max_words: Maximum words per chapter

        Returns:
            Generated chapter text or None if failed

        Example:
            >>> plan = llm.generate_story_plan("pirates")
            >>> chapter1 = llm.generate_chapter(plan, 1)
            >>> print(chapter1)
        """
        if chapter_num < 1 or chapter_num > len(plan.chapters):
            self.logger.error(f"Invalid chapter number: {chapter_num}")
            return None

        chapter_info = plan.chapters[chapter_num - 1]

        self.logger.info(f"Generating chapter {chapter_num}: {chapter_info['title']}")

        # Use configured prompt template or default
        prompt_template = self.config.prompts.chapter or self._get_default_chapter_prompt()

        # Prepare context
        plan_text = self._format_plan_for_context(plan)

        # Fill in template
        prompt = prompt_template.format(
            chapter_num=chapter_num,
            chapter_title=chapter_info['title'],
            cumulative_context=cumulative_context or "C'est le début de l'histoire.",
            story_plan=plan_text,
            min_words=min_words,
            max_words=max_words
        )

        with TimingContext(f"chapter_{chapter_num}_generation", log_metric=True):
            # Generate chapter
            output = self.generate(
                prompt,
                max_tokens=800,  # ~300 words * ~2.5 tokens per word
                temperature=0.8  # More creative for storytelling
            )

            if output:
                word_count = len(output.split())
                self.logger.info(f"Generated chapter {chapter_num}: {word_count} words")
                log_metric(f"chapter_{chapter_num}_words", word_count)
                return output
            else:
                return None

    def _get_default_chapter_prompt(self) -> str:
        """Get default chapter generation prompt"""
        return """Écris le chapitre {chapter_num} intitulé "{chapter_title}".

Contexte cumulatif des chapitres précédents :
{cumulative_context}

Plan global de l'histoire :
{story_plan}

Consignes :
- {min_words} à {max_words} mots
- Paragraphes courts pour la lecture à voix haute
- Cohérent avec le contexte et le plan
- Ton narratif adapté à un jeune public

Écris UNIQUEMENT le contenu du chapitre, sans répéter le titre.

Chapitre :"""

    def _format_plan_for_context(self, plan: StoryPlan) -> str:
        """
        Format story plan for context injection

        Args:
            plan: Story plan

        Returns:
            Formatted text representation
        """
        lines = []
        for chapter in plan.chapters:
            lines.append(f"{chapter['number']}. {chapter['title']}: {chapter['summary']}")

        return "\n".join(lines)

    def stream_tokens(self, prompt: str, max_tokens: int = 500) -> Generator[str, None, None]:
        """
        Generate tokens with streaming (experimental)

        Yields tokens as they're generated for real-time display.
        Note: llama-cli doesn't have built-in streaming, so this
        polls the output. For true streaming, use llama-server.

        Args:
            prompt: Input prompt
            max_tokens: Max tokens to generate

        Yields:
            Generated tokens/text chunks

        Example:
            >>> for token in llm.stream_tokens("Il était une fois"):
            ...     print(token, end='', flush=True)
        """
        # This is a simplified version
        # For production, use llama-server with streaming API
        output = self.generate(prompt, max_tokens)
        if output:
            yield output


def test_llama_llm():
    """
    Simple test function for Llama LLM

    Run this to verify LLM is working correctly.

    Usage:
        python -m app.llm.llama_llm
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("Llama LLM Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Initialize LLM
    try:
        llm = LlamaLLM(config.llm)
        print("✓ LLM initialized")
    except Exception as e:
        print(f"✗ Failed to initialize LLM: {e}")
        return

    # Test story plan generation
    print("\n--- Test 1: Generate Story Plan ---")
    theme = "des pirates qui cherchent un trésor caché"

    plan = llm.generate_story_plan(theme, num_chapters=5)

    if plan:
        print(f"✓ Generated plan for: {plan.theme}")
        print(f"\nChapters:")
        for chapter in plan.chapters:
            print(f"  {chapter['number']}. {chapter['title']}")
            print(f"     → {chapter['summary']}")

        # Test chapter generation
        print("\n--- Test 2: Generate Chapter 1 ---")
        chapter_text = llm.generate_chapter(plan, chapter_num=1)

        if chapter_text:
            word_count = len(chapter_text.split())
            print(f"✓ Generated chapter 1 ({word_count} words):")
            print(f"\n{chapter_text}\n")
        else:
            print("✗ Chapter generation failed")

    else:
        print("✗ Plan generation failed")

    print("=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run test when module is executed directly
    test_llama_llm()
