# LLM Configuration Guide

This file explains how to configure the LLM parameters for StoryBox IA.

## Configuration Files

### `llm_config.json`

This file contains all LLM-specific parameters in a model-agnostic way.

#### Key Sections:

1. **`default`**: Default parameters for all generation types
   - `max_tokens`: Maximum tokens to generate (set to `null` to let model decide)
   - `temperature`: Controls randomness (0.1-1.0)
   - `top_p`: Nucleus sampling (0.1-1.0)
   - `repeat_penalty`: Penalty for repeated tokens

2. **`generation_specific`**: Override parameters for specific generation types
   - `story_plan`: Parameters for story plan generation
   - `chapter`: Parameters for chapter generation

3. **`model_presets`**: Information about different models (for reference only)
   - Shows context window sizes and recommended settings
   - Completely optional - just for your reference

## How to Use

### Switching Models

1. Edit `configs/default.yaml`
2. Change the `model_path` to any Celeste-supported model:
   ```yaml
   llm:
     model_path: "claude-3-5-sonnet"  # or "gpt-4o-mini", "mistral-large", etc.
   ```
3. No other changes needed! The configuration is model-agnostic.

### Adjusting Generation Parameters

Edit `configs/llm_config.json`:

#### For Complete Responses (Recommended):
```json
"generation_specific": {
  "story_plan": {
    "max_tokens": null  // Let model decide length
  },
  "chapter": {
    "max_tokens": null  // Let model decide length
  }
}
```

#### For Controlled Responses:
```json
"generation_specific": {
  "story_plan": {
    "max_tokens": 4000  // Limit to 4000 tokens
  },
  "chapter": {
    "max_tokens": 2000  // Limit to 2000 tokens
  }
}
```

## Tips

- **`max_tokens: null`** is recommended for most use cases - lets the model complete its response naturally
- Higher `temperature` (0.8-1.2) = more creative, unpredictable output
- Lower `temperature` (0.3-0.7) = more deterministic, focused output
- The system automatically detects and uses the best parameters for each model

## Supported Models

Any model supported by Celeste will work:
- Google Gemini models (gemini-2.5-flash, gemini-2.0-pro, etc.)
- OpenAI models (gpt-4o, gpt-4o-mini, etc.)
- Anthropic models (claude-3-5-sonnet, claude-3-opus, etc.)
- Mistral models (mistral-large, mistral-medium, etc.)

Just change the `model_path` and ensure you have the corresponding API key set in your environment variables.