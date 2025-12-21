"""
Prompt Editor Utility for Streamlit

Helper functions to load, edit, and save prompt configurations.
"""

import json
from pathlib import Path
from typing import Dict, Any


def get_prompts_file_path() -> Path:
    """Get the path to prompts.json"""
    # From webapp/utils/ go to project root
    return Path(__file__).parent.parent.parent / "configs" / "prompts.json"


def load_prompts() -> Dict[str, Any]:
    """
    Load prompts configuration from JSON

    Returns:
        Dictionary with prompt configurations
    """
    prompts_file = get_prompts_file_path()

    if not prompts_file.exists():
        raise FileNotFoundError(f"Prompts config not found: {prompts_file}")

    with open(prompts_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_prompts(prompts_config: Dict[str, Any]) -> bool:
    """
    Save prompts configuration to JSON

    Args:
        prompts_config: Dictionary with prompt configurations

    Returns:
        True if save was successful
    """
    prompts_file = get_prompts_file_path()

    try:
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(prompts_config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving prompts: {e}")
        return False


def get_filled_prompt(template: str, variables: Dict[str, Any]) -> str:
    """
    Fill in a prompt template with variables

    Args:
        template: Prompt template with {variable} placeholders
        variables: Dictionary of variable values

    Returns:
        Filled prompt string
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        return f"Error: Missing variable {e} in template"
