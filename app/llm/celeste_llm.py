"""
Celeste LLM Wrapper for StoryBox IA

Handles text generation using Celeste unified AI library.
Supports multiple cloud providers (OpenAI, Anthropic, Gemini, Mistral, etc.)

Features:
- Story plan generation (10 chapters with JSON output)
- Chapter-by-chapter story generation with context
- Easy provider switching via configuration
- Type-safe with Pydantic validation
- Cloud-based (requires internet connection)

Usage:
    from app.llm.celeste_llm import CelesteLLM

    llm = CelesteLLM(config.llm)
    plan = await llm.generate_story_plan("pirates et trésor")
    chapter = await llm.generate_chapter(plan, chapter_num=1)

Author: StoryBox IA Team
Date: 2024-12
"""

import json
import re
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseModel, Field

from app.utils.logger import get_logger, TimingContext, log_metric
from app.utils.config import LLMConfig


def load_prompts_config() -> Dict[str, Any]:
    """
    Load prompts configuration from JSON file

    Returns:
        Dictionary with prompt configurations

    Raises:
        FileNotFoundError: If prompts.json doesn't exist
    """
    project_root = Path(__file__).parent.parent.parent
    prompts_file = project_root / "configs" / "prompts.json"

    if not prompts_file.exists():
        raise FileNotFoundError(f"Prompts config not found: {prompts_file}")

    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)


logger = get_logger(__name__)


# Pydantic models for structured output
class ChapterModel(BaseModel):
    """Pydantic model for a single chapter in story plan"""
    number: int = Field(description="Chapter number (1-indexed)")
    title: str = Field(description="Chapter title")
    summary: str = Field(description="One-sentence summary of the chapter")


class StoryPlanResponse(BaseModel):
    """Pydantic model for complete story plan response"""
    chapters: List[ChapterModel] = Field(description="List of chapters in the story")


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


class CelesteLLM:
    """
    Celeste LLM engine wrapper

    Generates story plans and chapters using Celeste unified AI library.
    Supports multiple cloud providers with zero lock-in.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize Celeste LLM

        Args:
            config: LLM configuration object
                   config.model_path should contain the model ID
                   (e.g., "gpt-4o", "claude-3-5-sonnet", "gemini-2.0-flash")

        Environment variables required:
            - OPENAI_API_KEY: For OpenAI models
            - ANTHROPIC_API_KEY: For Anthropic models
            - GOOGLE_API_KEY: For Google Gemini models
            - MISTRAL_API_KEY: For Mistral models
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Extract model ID from model_path
        # For cloud APIs, model_path is just the model ID
        self.model_id = self._extract_model_id(config.model_path)

        self.client = None

        # Load prompts configuration from JSON
        try:
            self.prompts_config = load_prompts_config()
            self.logger.info("Prompts configuration loaded from configs/prompts.json")
        except FileNotFoundError as e:
            self.logger.warning(f"Prompts config not found, using defaults: {e}")
            self.prompts_config = {}

        # Load LLM-specific configuration
        try:
            self.llm_specific_config = self._load_llm_config()
            self.logger.info("LLM configuration loaded from configs/llm_config.json")
        except FileNotFoundError as e:
            self.logger.warning(f"LLM config not found, using defaults: {e}")
            self.llm_specific_config = {}

        self.logger.info("Celeste LLM initialized successfully")
        self.logger.info(f"Model: {self.model_id}")
        self.logger.info(f"Temperature: {config.temperature}")
        self.logger.info(f"Max tokens: {config.context_tokens}")
        
        # Log model-specific info if available
        if self.llm_specific_config and 'model_presets' in self.llm_specific_config:
            model_info = self.llm_specific_config['model_presets'].get(self.model_id, {})
            if model_info:
                self.logger.info(f"Model context window: {model_info.get('context_window', 'Unknown')}")
                self.logger.info(f"Recommended max tokens: {model_info.get('recommended_max_tokens', 'Unknown')}")

    def _extract_model_id(self, model_path: str) -> str:
        """
        Extract model ID from config.model_path

        Args:
            model_path: Can be full path or model ID

        Returns:
            Clean model ID for Celeste

        Examples:
            "gpt-4o" -> "gpt-4o"
            "/path/to/model.gguf" -> "gpt-4o" (uses default)
            "claude-3-5-sonnet-20241022" -> "claude-3-5-sonnet-20241022"
        """
        # If it looks like a file path, return default model
        if '/' in model_path or model_path.endswith('.gguf'):
            default_model = "gpt-4o-mini"
            self.logger.warning(f"Model path looks like file path: {model_path}")
            self.logger.warning(f"Using default cloud model: {default_model}")
            return default_model

        return model_path

    def _load_llm_config(self) -> Dict[str, Any]:
        """
        Load LLM-specific configuration from JSON file

        Returns:
            Dictionary with LLM configuration data

        Raises:
            FileNotFoundError: If llm_config.json doesn't exist
        """
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "configs" / "llm_config.json"

        if not config_file.exists():
            raise FileNotFoundError(f"LLM config not found: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _detect_provider(self, model_id: str):
        """
        Detect provider enum from model ID

        Args:
            model_id: Model identifier

        Returns:
            Provider enum for Celeste

        Examples:
            "gemini-2.0-flash-exp" -> Provider.GOOGLE
            "gpt-4o" -> Provider.OPENAI
            "claude-3-5-sonnet" -> Provider.ANTHROPIC
            "mistral-large" -> Provider.MISTRAL
        """
        from celeste import Provider

        model_lower = model_id.lower()

        if "gemini" in model_lower:
            return Provider.GOOGLE
        elif "gpt" in model_lower or "o1" in model_lower:
            return Provider.OPENAI
        elif "claude" in model_lower:
            return Provider.ANTHROPIC
        elif "mistral" in model_lower:
            return Provider.MISTRAL
        else:
            # Default to openai if unknown
            self.logger.warning(f"Unknown model provider for '{model_id}', defaulting to OpenAI")
            return Provider.OPENAI

    def _get_client(self):
        """
        Get or create Celeste client (lazy initialization)

        Returns:
            Celeste text generation client
        """
        if self.client is None:
            try:
                from celeste import create_client, Capability

                # Detect provider from model ID
                provider = self._detect_provider(self.model_id)

                self.logger.info(f"Creating Celeste client with provider={provider}, model='{self.model_id}'")

                self.client = create_client(
                    capability=Capability.TEXT_GENERATION,
                    provider=provider,
                    model=self.model_id
                )

                self.logger.info(f"Celeste client created successfully")
            except ImportError:
                raise RuntimeError(
                    "Celeste library not installed. Install with: pip install 'celeste-ai[text-generation]'"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to create Celeste client: {e}")

        return self.client

    async def generate(
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
            stop_sequences: Sequences that stop generation (not all models support)

        Returns:
            Generated text or None if generation failed

        Example:
            >>> llm = CelesteLLM(config.llm)
            >>> text = await llm.generate("Il était une fois")
            >>> print(text)
            "Il était une fois un jeune garçon..."
        """
        if not prompt:
            self.logger.warning("Empty prompt provided")
            return None

        self.logger.debug(f"Generating with prompt: {prompt[:100]}...")
        self.logger.info(f"Generation params: max_tokens={max_tokens}, temperature={temperature or self.config.temperature}")

        with TimingContext("llm_generation", log_metric=True):
            try:
                client = self._get_client()

                # Generate with Celeste - add detailed logging
                self.logger.debug(f"Calling Celeste generate with params: max_tokens={max_tokens}, temperature={temperature or self.config.temperature}")

                # Generate with Celeste
                response = await client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature or self.config.temperature,
                    # Note: Not all models support stop sequences
                    # Celeste handles this automatically
                )

                output = response.content.strip() if response and response.content else ""

                if output:
                    self.logger.info(f"Generated {len(output)} chars")
                    log_metric("llm_chars_generated", len(output))

                    # Log first 200 chars for debugging
                    self.logger.debug(f"Generated text preview: {output[:200]}...")
                    
                    # Check if response ends with complete sentence
                    if not any(output.rstrip().endswith(punct) for punct in ['.', '!', '?', '...']):
                        self.logger.warning(f"INCOMPLETE RESPONSE: Text does not end with proper punctuation")
                        self.logger.warning(f"Last 50 chars: '{output[-50:]}'")

                    # Estimate tokens (rough: 1 token ≈ 4 chars)
                    estimated_tokens = len(output) / 4
                    log_metric("llm_tokens_generated", estimated_tokens)

                    return output
                else:
                    self.logger.warning("No output from LLM")
                    if response:
                        self.logger.debug(f"Response object: {vars(response)}")
                    return None

            except Exception as e:
                self.logger.error(f"LLM generation error: {e}", exc_info=True)
                return None

    async def generate_story_plan(self, theme: str, num_chapters: int = 10, temperature: Optional[float] = None) -> Optional[StoryPlan]:
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
            >>> llm = CelesteLLM(config.llm)
            >>> plan = await llm.generate_story_plan("pirates et trésor")
            >>> for chapter in plan.chapters:
            ...     print(f"{chapter['number']}. {chapter['title']}")
        """
        self.logger.info(f"Generating story plan: {theme} ({num_chapters} chapters)")

        # Use configured prompt template or default
        prompt_template = self.config.prompts.plan or self._get_plan_prompt()

        # Fill in template
        prompt = prompt_template.format(
            theme=theme,
            num_chapters=num_chapters
        )

        with TimingContext("story_plan_generation", log_metric=True):
            # Get max_tokens from configuration (model-agnostic)
            plan_max_tokens = self._get_max_tokens_for_generation('plan')
            # Use parameter temperature if provided, otherwise use configured temperature
            plan_temperature = temperature if temperature is not None else self._get_temperature_for_generation('plan')

            self.logger.info(f"Generating story plan with max_tokens={plan_max_tokens}, temperature={plan_temperature}")

            output = await self.generate(
                prompt,
                max_tokens=plan_max_tokens,  # Use configured max_tokens (None = let model decide)
                temperature=plan_temperature  # Use parameter or configured temperature
            )

            if not output:
                return None

            # Log raw output for debugging
            self.logger.debug(f"Raw LLM output (first 500 chars): {output[:500]}")

            # Parse JSON output with Pydantic validation
            try:
                # Clean markdown code blocks if present
                json_str = output.strip()

                # Remove markdown code fence if present (```json ... ```)
                if '```' in json_str:
                    # Extract JSON from code block
                    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', json_str, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1).strip()
                    else:
                        # Fallback: try to find raw JSON
                        json_match = re.search(r'\{[\s\S]*\}', json_str)
                        if json_match:
                            json_str = json_match.group(0)

                # Additional cleaning for common issues
                # Remove any text before or after JSON
                json_str = json_str.strip()
                
                # Try to parse with Pydantic
                try:
                    plan_data = StoryPlanResponse.model_validate_json(json_str)
                except Exception as parse_error:
                    # If Pydantic fails, try more aggressive cleaning
                    self.logger.warning(f"Pydantic parsing failed, trying fallback: {parse_error}")
                    
                    # Try to extract JSON more aggressively
                    json_match = re.search(r'"chapters"\s*:\s*\[.*\]', json_str, re.DOTALL)
                    if json_match:
                        # Try to reconstruct valid JSON
                        json_str = "{" + json_match.group(0) + "}"
                        plan_data = StoryPlanResponse.model_validate_json(json_str)
                    else:
                        raise parse_error

                # Convert to StoryPlan
                chapters = [
                    {
                        'number': ch.number,
                        'title': ch.title,
                        'summary': ch.summary
                    }
                    for ch in plan_data.chapters
                ]

                plan = StoryPlan(theme=theme, chapters=chapters)
                self.logger.info(f"Generated plan with {len(plan.chapters)} chapters")
                return plan

            except Exception as e:
                self.logger.error(f"Story plan parsing error: {e}", exc_info=True)
                self.logger.debug(f"Full LLM output: {output}")
                return None

    def _get_max_tokens_for_generation(self, generation_type: str) -> Optional[int]:
        """
        Get max_tokens configuration for specific generation type

        Args:
            generation_type: Type of generation ('plan' or 'chapter')

        Returns:
            max_tokens value or None if not specified (let model decide)
        """
        if not self.llm_specific_config or 'generation_specific' not in self.llm_specific_config:
            return None

        gen_config = self.llm_specific_config['generation_specific']
        
        if generation_type == 'plan' and 'story_plan' in gen_config:
            return gen_config['story_plan'].get('max_tokens')
        elif generation_type == 'chapter' and 'chapter' in gen_config:
            return gen_config['chapter'].get('max_tokens')
        
        return None

    def _get_temperature_for_generation(self, generation_type: str) -> float:
        """
        Get temperature configuration for specific generation type

        Args:
            generation_type: Type of generation ('plan' or 'chapter')

        Returns:
            temperature value, falling back to config.temperature if not specified
        """
        if not self.llm_specific_config or 'generation_specific' not in self.llm_specific_config:
            return self.config.temperature

        gen_config = self.llm_specific_config['generation_specific']
        
        if generation_type == 'plan' and 'story_plan' in gen_config:
            return gen_config['story_plan'].get('temperature', self.config.temperature)
        elif generation_type == 'chapter' and 'chapter' in gen_config:
            return gen_config['chapter'].get('temperature', self.config.temperature)
        
        return self.config.temperature

    def _get_plan_prompt(self) -> str:
        """
        Get story plan prompt template from config

        Returns:
            Prompt template string or default if not in config
        """
        if 'plan' in self.prompts_config and 'user_template' in self.prompts_config['plan']:
            return self.prompts_config['plan']['user_template']

        # Fallback to default
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
            # Log raw output for debugging
            self.logger.debug(f"Parsing story plan from output: {output[:500]}...")

            # Try multiple strategies to extract JSON
            json_str = None

            # Strategy 1: Look for markdown code blocks
            if '```' in output:
                json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()

            # Strategy 2: Look for raw JSON object
            if not json_str:
                json_match = re.search(r'\{[\s\S]*\}', output)
                if json_match:
                    json_str = json_match.group(0)

            # Strategy 3: Look for chapters array specifically
            if not json_str:
                json_match = re.search(r'"chapters"\s*:\s*\[.*\]', output, re.DOTALL)
                if json_match:
                    json_str = "{" + json_match.group(0) + "}"

            if not json_str:
                self.logger.error("No JSON found in LLM output")
                return None

            # Clean JSON string
            json_str = json_str.strip()
            
            # Remove any trailing commas or incomplete parts
            json_str = re.sub(r',\s*\}\s*$', '}', json_str)
            json_str = re.sub(r',\s*\]\s*$', ']', json_str)

            # Parse JSON
            data = json.loads(json_str)

            # Validate structure
            if 'chapters' not in data:
                self.logger.error("Missing 'chapters' key in JSON")
                return None

            # Validate chapters structure
            chapters = []
            for i, chapter in enumerate(data['chapters']):
                if not isinstance(chapter, dict):
                    self.logger.warning(f"Invalid chapter format at index {i}")
                    continue
                
                # Ensure required fields
                if 'number' not in chapter or 'title' not in chapter or 'summary' not in chapter:
                    self.logger.warning(f"Missing required fields in chapter {i}")
                    continue
                    
                chapters.append(chapter)

            if not chapters:
                self.logger.error("No valid chapters found in JSON")
                return None

            # Create StoryPlan
            plan = StoryPlan(theme=theme, chapters=chapters)

            return plan

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self.logger.debug(f"Failed to parse JSON: {output}")
            return None
        except Exception as e:
            self.logger.error(f"Plan parsing error: {e}", exc_info=True)
            return None

    async def generate_chapter(
        self,
        plan: StoryPlan,
        chapter_num: int,
        cumulative_context: str = "",
        min_words: int = 150,
        max_words: int = 300,
        temperature: Optional[float] = None
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
            >>> plan = await llm.generate_story_plan("pirates")
            >>> chapter1 = await llm.generate_chapter(plan, 1)
            >>> print(chapter1)
        """
        if chapter_num < 1 or chapter_num > len(plan.chapters):
            self.logger.error(f"Invalid chapter number: {chapter_num}")
            return None

        chapter_info = plan.chapters[chapter_num - 1]

        self.logger.info(f"Generating chapter {chapter_num}: {chapter_info['title']}")

        # Use configured prompt template or default
        prompt_template = self.config.prompts.chapter or self._get_chapter_prompt()

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
            # Get max_tokens from configuration (model-agnostic)
            chapter_max_tokens = self._get_max_tokens_for_generation('chapter')
            # Use parameter temperature if provided, otherwise use configured temperature
            chapter_temperature = temperature if temperature is not None else self._get_temperature_for_generation('chapter')

            self.logger.info(f"Generating chapter {chapter_num} with max_tokens={chapter_max_tokens}, temperature={chapter_temperature}")

            output = await self.generate(
                prompt,
                max_tokens=chapter_max_tokens,  # Use configured max_tokens (None = let model decide)
                temperature=chapter_temperature  # Use parameter or configured temperature
            )

            if output:
                word_count = len(output.split())
                self.logger.info(f"Generated chapter {chapter_num}: {word_count} words")
                log_metric(f"chapter_{chapter_num}_words", word_count)
                
                # Log preview for debugging
                self.logger.debug(f"Chapter {chapter_num} preview: {output[:200]}...")
                
                return output
            else:
                return None

    def _get_chapter_prompt(self) -> str:
        """
        Get chapter generation prompt template from config

        Returns:
            Prompt template string or default if not in config
        """
        if 'chapter' in self.prompts_config and 'user_template' in self.prompts_config['chapter']:
            return self.prompts_config['chapter']['user_template']

        # Fallback to default
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


async def test_celeste_llm():
    """
    Simple test function for Celeste LLM

    Run this to verify cloud LLM is working correctly.

    Usage:
        python -m app.llm.celeste_llm
    """
    from app.utils.config import get_config

    print("=" * 60)
    print("Celeste LLM Test (Cloud API)")
    print("=" * 60)

    # Load config
    config = get_config()

    # Initialize LLM
    try:
        llm = CelesteLLM(config.llm)
        print("✓ LLM initialized")
    except Exception as e:
        print(f"✗ Failed to initialize LLM: {e}")
        return

    # Test story plan generation
    print("\n--- Test 1: Generate Story Plan ---")
    theme = "des pirates qui cherchent un trésor caché"

    plan = await llm.generate_story_plan(theme, num_chapters=5)

    if plan:
        print(f"✓ Generated plan for: {plan.theme}")
        print(f"\nChapters:")
        for chapter in plan.chapters:
            print(f"  {chapter['number']}. {chapter['title']}")
            print(f"     → {chapter['summary']}")

        # Test chapter generation
        print("\n--- Test 2: Generate Chapter 1 ---")
        chapter_text = await llm.generate_chapter(plan, chapter_num=1)

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
    asyncio.run(test_celeste_llm())
