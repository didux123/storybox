"""
Story Generation Module for StoryBox IA

High-level orchestrator for chapter-by-chapter story generation.
Manages cumulative context and streaming generation.

Features:
- Sequential chapter generation with context
- Cumulative summary management (2-3 sentences per chapter)
- Memory optimization (~1-2k tokens total context)
- Chapter validation and quality checks

Usage:
    from app.llm.story_gen import StoryGenerator

    story_gen = StoryGenerator(config.llm)
    for chapter_text in story_gen.generate_story(plan):
        # Narrate chapter with TTS
        audio = tts.synthesize(chapter_text)

Author: StoryBox IA Team
Date: 2024-12
"""

from typing import Optional, Generator, List
from dataclasses import dataclass

from app.llm.llama_llm import LlamaLLM, StoryPlan
from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import LLMConfig


logger = get_logger(__name__)


@dataclass
class ChapterResult:
    """
    Result of chapter generation

    Attributes:
        chapter_num: Chapter number (1-indexed)
        title: Chapter title
        text: Generated chapter text
        word_count: Number of words
        summary: 2-3 sentence summary for context
    """
    chapter_num: int
    title: str
    text: str
    word_count: int
    summary: Optional[str] = None


class StoryGenerator:
    """
    Story generator orchestrator

    Handles chapter-by-chapter generation with cumulative context management.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize story generator

        Args:
            config: LLM configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Initialize LLM
        self.llm = LlamaLLM(config)

        # Story state
        self.current_plan = None
        self.cumulative_context = ""
        self.generated_chapters = []

        self.logger.info("StoryGenerator initialized successfully")

    def generate_story(
        self,
        plan: StoryPlan,
        min_words: int = 150,
        max_words: int = 300
    ) -> Generator[ChapterResult, None, None]:
        """
        Generate full story chapter by chapter

        Yields chapters as they're generated for real-time narration.

        Args:
            plan: Story plan with all chapters
            min_words: Minimum words per chapter
            max_words: Maximum words per chapter

        Yields:
            ChapterResult for each generated chapter

        Example:
            >>> story_gen = StoryGenerator(config.llm)
            >>> for chapter in story_gen.generate_story(plan):
            ...     print(f"Chapter {chapter.chapter_num}: {chapter.title}")
            ...     audio = tts.synthesize(chapter.text)
            ...     play_audio(audio)
        """
        if not plan or not plan.chapters:
            self.logger.error("Invalid plan provided")
            return

        self.logger.info(f"Starting story generation: {plan.theme}")
        self.logger.info(f"Chapters: {len(plan.chapters)}")

        # Reset state
        self.current_plan = plan
        self.cumulative_context = ""
        self.generated_chapters = []

        # Generate each chapter
        for i in range(1, len(plan.chapters) + 1):
            self.logger.info(f"Generating chapter {i}/{len(plan.chapters)}")

            with TimingContext(f"chapter_{i}_generation", log_metric=True):
                chapter_result = self._generate_chapter(
                    plan=plan,
                    chapter_num=i,
                    min_words=min_words,
                    max_words=max_words
                )

            if chapter_result:
                # Store result
                self.generated_chapters.append(chapter_result)

                # Update cumulative context with summary
                self._update_context(chapter_result)

                # Log progress
                self.logger.info(
                    f"Generated chapter {i}: {chapter_result.word_count} words"
                )
                log_metric(f"chapter_{i}_words", chapter_result.word_count)

                # Yield chapter for immediate processing
                yield chapter_result
            else:
                self.logger.error(f"Failed to generate chapter {i}")
                # Continue with next chapter or abort?
                # For now, abort to maintain story coherence
                break

        self.logger.info("Story generation complete")

    def _generate_chapter(
        self,
        plan: StoryPlan,
        chapter_num: int,
        min_words: int,
        max_words: int
    ) -> Optional[ChapterResult]:
        """
        Generate single chapter with validation

        Args:
            plan: Story plan
            chapter_num: Chapter number to generate
            min_words: Minimum words
            max_words: Maximum words

        Returns:
            ChapterResult or None if generation failed
        """
        chapter_info = plan.chapters[chapter_num - 1]

        # Generate chapter text
        chapter_text = self.llm.generate_chapter(
            plan=plan,
            chapter_num=chapter_num,
            cumulative_context=self.cumulative_context,
            min_words=min_words,
            max_words=max_words
        )

        if not chapter_text:
            return None

        # Validate chapter
        if not self._validate_chapter(chapter_text, min_words, max_words):
            self.logger.warning(f"Chapter {chapter_num} validation failed")
            # Still return it, but log the issue
            # Could implement retry logic here

        # Count words
        word_count = len(chapter_text.split())

        # Generate summary for context
        summary = self._generate_summary(chapter_text, chapter_num)

        # Create result
        result = ChapterResult(
            chapter_num=chapter_num,
            title=chapter_info['title'],
            text=chapter_text,
            word_count=word_count,
            summary=summary
        )

        return result

    def _validate_chapter(self, text: str, min_words: int, max_words: int) -> bool:
        """
        Validate generated chapter

        Checks:
        - Word count within range
        - Not empty or too short
        - Basic quality (no repetitions, etc.)

        Args:
            text: Chapter text
            min_words: Minimum words
            max_words: Maximum words

        Returns:
            True if valid, False otherwise
        """
        if not text or not text.strip():
            self.logger.error("Chapter text is empty")
            return False

        word_count = len(text.split())

        # Check word count (allow 20% margin)
        if word_count < min_words * 0.8:
            self.logger.warning(f"Chapter too short: {word_count} words (min: {min_words})")
            return False

        if word_count > max_words * 1.2:
            self.logger.warning(f"Chapter too long: {word_count} words (max: {max_words})")
            return False

        # Check for excessive repetition (simple check)
        words = text.lower().split()
        unique_words = set(words)
        repetition_ratio = len(words) / len(unique_words) if unique_words else 0

        if repetition_ratio > 3.0:
            self.logger.warning(f"High word repetition ratio: {repetition_ratio:.1f}")
            return False

        return True

    def _generate_summary(self, chapter_text: str, chapter_num: int) -> Optional[str]:
        """
        Generate 2-3 sentence summary of chapter for context

        Args:
            chapter_text: Full chapter text
            chapter_num: Chapter number

        Returns:
            Summary text or None if generation failed
        """
        self.logger.debug(f"Generating summary for chapter {chapter_num}")

        # Prompt for summary generation
        prompt = f"""Résume ce chapitre en 2-3 phrases courtes (maximum 50 mots).
Concentre-toi sur les événements clés et les éléments importants pour la suite de l'histoire.

Chapitre :
{chapter_text}

Résumé (2-3 phrases) :"""

        with TimingContext(f"chapter_{chapter_num}_summary", log_metric=True):
            summary = self.llm.generate(
                prompt,
                max_tokens=100,  # ~50 words * 2 tokens/word
                temperature=0.5   # Lower temperature for factual summary
            )

        if summary:
            summary = summary.strip()
            self.logger.debug(f"Summary: {summary}")
            return summary
        else:
            self.logger.warning(f"Failed to generate summary for chapter {chapter_num}")
            # Fallback: use first 2 sentences of chapter
            sentences = chapter_text.split('.')[:2]
            return '. '.join(sentences) + '.'

    def _update_context(self, chapter_result: ChapterResult):
        """
        Update cumulative context with chapter summary

        Manages context size to stay within ~1-2k tokens.

        Args:
            chapter_result: Generated chapter result
        """
        if chapter_result.summary:
            # Add summary to cumulative context
            context_entry = f"Chapitre {chapter_result.chapter_num}: {chapter_result.summary}"

            if self.cumulative_context:
                self.cumulative_context += f"\n{context_entry}"
            else:
                self.cumulative_context = context_entry

            # Estimate token count (rough: 1 token ≈ 4 chars)
            estimated_tokens = len(self.cumulative_context) / 4

            self.logger.debug(f"Cumulative context: ~{estimated_tokens:.0f} tokens")

            # If context too large, trim oldest summaries
            max_context_tokens = 1500  # Leave room for other prompt elements
            if estimated_tokens > max_context_tokens:
                self.logger.warning("Context exceeds limit, trimming oldest summaries")
                self._trim_context(max_context_tokens)

    def _trim_context(self, max_tokens: int):
        """
        Trim cumulative context to fit within token limit

        Removes oldest chapter summaries first.

        Args:
            max_tokens: Maximum tokens to keep
        """
        # Split by chapter summaries
        lines = self.cumulative_context.split('\n')

        # Keep removing oldest summaries until under limit
        while lines and len('\n'.join(lines)) / 4 > max_tokens:
            lines.pop(0)

        self.cumulative_context = '\n'.join(lines)

        estimated_tokens = len(self.cumulative_context) / 4
        self.logger.info(f"Context trimmed to ~{estimated_tokens:.0f} tokens")

    def get_full_story(self) -> str:
        """
        Get full story text (all generated chapters)

        Returns:
            Complete story text
        """
        if not self.generated_chapters:
            return ""

        story_parts = []

        for chapter in self.generated_chapters:
            story_parts.append(f"Chapitre {chapter.chapter_num}: {chapter.title}\n")
            story_parts.append(chapter.text)
            story_parts.append("\n\n")

        return "".join(story_parts)

    def save_story(self, output_path):
        """
        Save complete story to text file

        Args:
            output_path: Output file path
        """
        story_text = self.get_full_story()

        with open(output_path, 'w', encoding='utf-8') as f:
            # Add header
            if self.current_plan:
                f.write(f"Histoire : {self.current_plan.theme}\n")
                f.write("=" * 60 + "\n\n")

            f.write(story_text)

        self.logger.info(f"Saved story to {output_path}")

    def get_statistics(self) -> dict:
        """
        Get generation statistics

        Returns:
            Dictionary with stats (total words, chapters, etc.)
        """
        total_words = sum(ch.word_count for ch in self.generated_chapters)
        avg_words = total_words / len(self.generated_chapters) if self.generated_chapters else 0

        return {
            'total_chapters': len(self.generated_chapters),
            'total_words': total_words,
            'average_words_per_chapter': avg_words,
            'context_size_chars': len(self.cumulative_context),
            'context_size_tokens_estimate': len(self.cumulative_context) / 4
        }


def test_story_generator():
    """
    Test function for story generator module

    Usage:
        python -m app.llm.story_gen
    """
    from app.utils.config import get_config
    from app.llm.planner import Planner
    from pathlib import Path

    print("=" * 60)
    print("Story Generator Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Initialize story generator
    try:
        story_gen = StoryGenerator(config.llm)
        print("✓ StoryGenerator initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # Generate or load a plan
    print("\n--- Generating Story Plan ---")
    planner = Planner(config.llm)
    plan = planner.create_plan("des pirates qui cherchent un trésor", num_chapters=3)

    if not plan:
        print("✗ Failed to generate plan")
        return

    print(f"✓ Plan created: {plan.theme}")
    print(f"  Chapters: {len(plan.chapters)}")

    # Generate story
    print("\n--- Generating Story ---")
    chapter_count = 0

    for chapter in story_gen.generate_story(plan, min_words=100, max_words=200):
        chapter_count += 1
        print(f"\nChapter {chapter.chapter_num}: {chapter.title}")
        print(f"Words: {chapter.word_count}")
        print(f"Text preview: {chapter.text[:100]}...")
        if chapter.summary:
            print(f"Summary: {chapter.summary}")

    if chapter_count > 0:
        print(f"\n✓ Generated {chapter_count} chapters")

        # Show statistics
        stats = story_gen.get_statistics()
        print("\n--- Statistics ---")
        print(f"Total words: {stats['total_words']}")
        print(f"Average words/chapter: {stats['average_words_per_chapter']:.1f}")
        print(f"Context size: ~{stats['context_size_tokens_estimate']:.0f} tokens")

        # Save story
        output_file = Path("test_generated_story.txt")
        story_gen.save_story(output_file)
        print(f"\n✓ Saved full story to {output_file}")

    else:
        print("✗ No chapters generated")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run test when module is executed directly
    test_story_generator()
