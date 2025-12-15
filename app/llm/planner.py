"""
Story Planner Module for StoryBox IA

High-level orchestrator for story plan generation.
Wraps LLM module with user-friendly API.

Features:
- Theme extraction from user input
- 10-chapter story plan generation
- Plan validation and error handling
- Caching for repeated requests

Usage:
    from app.llm.planner import Planner

    planner = Planner(config.llm)
    plan = planner.create_plan("des pirates qui cherchent un trésor")

Author: StoryBox IA Team
Date: 2024-12
"""

import re
from typing import Optional
from pathlib import Path

from app.llm.llama_llm import LlamaLLM, StoryPlan
from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import LLMConfig


logger = get_logger(__name__)


class Planner:
    """
    Story plan orchestrator

    High-level interface for generating story plans from user input.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize planner

        Args:
            config: LLM configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Initialize LLM
        self.llm = LlamaLLM(config)

        # Cache for last generated plan
        self.last_plan = None
        self.last_theme = None

        self.logger.info("Planner initialized successfully")

    def create_plan(self, user_input: str, num_chapters: int = 10) -> Optional[StoryPlan]:
        """
        Create story plan from user input

        Extracts theme and generates structured story plan.

        Args:
            user_input: User's story request (e.g., "Raconte-moi une histoire de pirates")
            num_chapters: Number of chapters (default 10)

        Returns:
            StoryPlan or None if generation failed

        Example:
            >>> planner = Planner(config.llm)
            >>> plan = planner.create_plan("des dragons et des chevaliers")
            >>> print(f"Generated {len(plan.chapters)} chapters")
        """
        if not user_input or not user_input.strip():
            self.logger.error("Empty user input provided")
            return None

        self.logger.info(f"Creating plan from: '{user_input}'")

        # Extract theme from user input
        with TimingContext("theme_extraction", log_metric=True):
            theme = self._extract_theme(user_input)

        if not theme:
            self.logger.error("Failed to extract theme from user input")
            return None

        self.logger.info(f"Extracted theme: '{theme}'")

        # Check cache
        if self.last_theme == theme and self.last_plan:
            self.logger.info("Using cached plan for same theme")
            return self.last_plan

        # Generate plan
        with TimingContext("plan_generation", log_metric=True):
            plan = self.llm.generate_story_plan(theme, num_chapters)

        if plan:
            # Validate plan
            if self._validate_plan(plan, num_chapters):
                # Cache result
                self.last_plan = plan
                self.last_theme = theme

                self.logger.info(f"Successfully generated plan with {len(plan.chapters)} chapters")
                log_metric("plan_chapters_generated", len(plan.chapters))

                return plan
            else:
                self.logger.error("Plan validation failed")
                return None
        else:
            self.logger.error("LLM returned no plan")
            return None

    def _extract_theme(self, user_input: str) -> Optional[str]:
        """
        Extract story theme from user input

        Handles various user input formats:
        - "Raconte-moi une histoire de pirates"
        - "Une histoire sur les dragons"
        - "pirates et trésor"
        - etc.

        Args:
            user_input: Raw user input

        Returns:
            Extracted theme or None if extraction failed
        """
        # Clean input
        text = user_input.lower().strip()

        # Remove common prefixes
        prefixes = [
            r"raconte[- ]moi une histoire (de |sur |avec )?",
            r"une histoire (de |sur |avec )?",
            r"parle[- ]moi (de |d')?",
            r"je veux une histoire (de |sur |avec )?",
            r"je voudrais une histoire (de |sur |avec )?",
        ]

        for prefix in prefixes:
            text = re.sub(prefix, "", text, flags=re.IGNORECASE)

        # Clean up
        text = text.strip()

        # If still too long, might be a full sentence - extract key nouns
        if len(text.split()) > 10:
            # Simple keyword extraction (could use spaCy for better results)
            # For now, just take the text as-is and let LLM figure it out
            pass

        # Validate extracted theme
        if len(text) < 3:
            self.logger.warning(f"Extracted theme too short: '{text}'")
            # Use original input as fallback
            return user_input

        return text

    def _validate_plan(self, plan: StoryPlan, expected_chapters: int) -> bool:
        """
        Validate story plan structure

        Checks:
        - Correct number of chapters
        - All chapters have required fields
        - Chapter numbers are sequential
        - No duplicate titles

        Args:
            plan: Story plan to validate
            expected_chapters: Expected number of chapters

        Returns:
            True if valid, False otherwise
        """
        if not plan or not plan.chapters:
            self.logger.error("Plan is empty")
            return False

        # Check chapter count
        actual_count = len(plan.chapters)
        if actual_count != expected_chapters:
            self.logger.warning(
                f"Chapter count mismatch: expected {expected_chapters}, got {actual_count}"
            )
            # Allow small discrepancy (±1)
            if abs(actual_count - expected_chapters) > 1:
                return False

        # Validate each chapter
        titles_seen = set()

        for i, chapter in enumerate(plan.chapters):
            # Check required fields
            if 'number' not in chapter:
                self.logger.error(f"Chapter {i} missing 'number' field")
                return False

            if 'title' not in chapter or not chapter['title']:
                self.logger.error(f"Chapter {i} missing 'title' field")
                return False

            if 'summary' not in chapter or not chapter['summary']:
                self.logger.error(f"Chapter {i} missing 'summary' field")
                return False

            # Check sequential numbering
            expected_num = i + 1
            if chapter['number'] != expected_num:
                self.logger.warning(
                    f"Chapter numbering issue: expected {expected_num}, got {chapter['number']}"
                )
                # Fix numbering
                chapter['number'] = expected_num

            # Check for duplicate titles
            title = chapter['title'].lower()
            if title in titles_seen:
                self.logger.warning(f"Duplicate chapter title: {chapter['title']}")
            titles_seen.add(title)

        self.logger.info("Plan validation: PASS")
        return True

    def get_chapter_info(self, plan: StoryPlan, chapter_num: int) -> Optional[dict]:
        """
        Get information for specific chapter

        Args:
            plan: Story plan
            chapter_num: Chapter number (1-indexed)

        Returns:
            Chapter info dict or None if not found
        """
        if not plan or chapter_num < 1 or chapter_num > len(plan.chapters):
            return None

        return plan.chapters[chapter_num - 1]

    def summarize_plan(self, plan: StoryPlan) -> str:
        """
        Generate human-readable summary of plan

        Args:
            plan: Story plan

        Returns:
            Formatted summary text
        """
        lines = [
            f"Histoire : {plan.theme}",
            f"Nombre de chapitres : {len(plan.chapters)}",
            "",
            "Chapitres :"
        ]

        for chapter in plan.chapters:
            lines.append(f"  {chapter['number']}. {chapter['title']}")
            lines.append(f"     {chapter['summary']}")

        return "\n".join(lines)

    def save_plan(self, plan: StoryPlan, output_path: Path):
        """
        Save plan to JSON file

        Args:
            plan: Story plan to save
            output_path: Output file path
        """
        import json

        plan_dict = plan.to_dict()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved plan to {output_path}")

    def load_plan(self, input_path: Path) -> Optional[StoryPlan]:
        """
        Load plan from JSON file

        Args:
            input_path: Input file path

        Returns:
            StoryPlan or None if loading failed
        """
        import json

        if not input_path.exists():
            self.logger.error(f"Plan file not found: {input_path}")
            return None

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                plan_dict = json.load(f)

            plan = StoryPlan.from_dict(plan_dict)

            self.logger.info(f"Loaded plan from {input_path}")
            return plan

        except Exception as e:
            self.logger.error(f"Failed to load plan: {e}", exc_info=True)
            return None


def test_planner():
    """
    Test function for planner module

    Usage:
        python -m app.llm.planner
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("Planner Test")
    print("=" * 60)

    # Load config
    config = get_config()

    # Initialize planner
    try:
        planner = Planner(config.llm)
        print("✓ Planner initialized")
    except Exception as e:
        print(f"✗ Failed to initialize planner: {e}")
        return

    # Test theme extraction
    print("\n--- Test 1: Theme Extraction ---")
    test_inputs = [
        "Raconte-moi une histoire de pirates qui cherchent un trésor",
        "Une histoire sur les dragons et les chevaliers",
        "des dinosaures dans la jungle",
        "je veux une histoire avec des robots",
    ]

    for user_input in test_inputs:
        theme = planner._extract_theme(user_input)
        print(f"Input:  '{user_input}'")
        print(f"Theme:  '{theme}'")
        print()

    # Test plan generation
    print("\n--- Test 2: Generate Story Plan ---")
    user_input = "des pirates qui cherchent un trésor caché"

    plan = planner.create_plan(user_input, num_chapters=5)

    if plan:
        print(f"✓ Generated plan for: {plan.theme}")
        print(f"\nPlan summary:")
        print(planner.summarize_plan(plan))

        # Save plan
        output_file = Path("test_story_plan.json")
        planner.save_plan(plan, output_file)
        print(f"\n✓ Saved plan to {output_file}")

        # Test loading
        print("\n--- Test 3: Load Saved Plan ---")
        loaded_plan = planner.load_plan(output_file)

        if loaded_plan:
            print(f"✓ Loaded plan: {loaded_plan.theme}")
            print(f"  Chapters: {len(loaded_plan.chapters)}")
        else:
            print("✗ Failed to load plan")

    else:
        print("✗ Plan generation failed")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run test when module is executed directly
    test_planner()
