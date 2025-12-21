# 🔍 Celeste Installation Issues Report

**Date**: 2024-12-21  
**Version**: celeste-ai 0.3.2  
**Environment**: macOS, Python 3.13  
**Project**: StoryBox IA

---

## 🚨 Issues Encountered

### 1. Missing Dependencies in `text-generation` Extra

**Severity**: High  
**Status**: Workaround applied  

**Problem**: 
The `celeste-ai[text-generation]` package does not install all required provider packages automatically.

**Error Messages**:
```
ModuleNotFoundError: No module named 'celeste_cohere'
ModuleNotFoundError: No module named 'celeste_mistral'
```

**Root Cause**:
The `text-generation` extra in `setup.py`/`pyproject.toml` is missing some provider dependencies.

**Expected Behavior**:
```bash
pip install 'celeste-ai[text-generation]'
```
Should automatically install:
- ✅ `celeste-anthropic` (was installed)
- ❌ `celeste-cohere` (was missing)
- ✅ `celeste-google` (was installed)
- ❌ `celeste-mistral` (was missing)
- ✅ `celeste-openai` (was installed)

**Workaround Applied**:
```bash
pip install celeste-cohere celeste-mistral
```

---

### 2. Model Name Mismatch

**Severity**: Medium  
**Status**: Fixed  

**Problem**:
```
ModelNotFoundError: Model 'gemini-1.5-flash' not found for provider google
```

**Root Cause**:
The model name `gemini-1.5-flash` in `.env` doesn't match any supported models in Celeste's registry.

**Supported Google Models** (celeste-ai 0.3.2):
```
gemini-2.5-flash
gemini-2.5-flash-lite
gemini-2.5-pro
gemini-3-pro-preview
```

**Fix Applied**:
Updated `.env` file:
```diff
-LLM_MODEL_PATH=gemini-1.5-flash
+LLM_MODEL_PATH=gemini-2.5-flash
```

---

### 3. JSON Parsing Issues

**Severity**: Medium  
**Status**: Needs improvement  

**Problem**:
```
JSON parsing error: Expecting ',' delimiter: line 47 column 6 (char 2066)
Failed to parse story plan from LLM output
```

**Root Cause**:
The Gemini model generates text that doesn't conform to the expected JSON structure, even with explicit prompt instructions.

**Current Prompt Structure**:
```
Génère un plan de 10 chapitres cohérents sur le thème suivant : {theme}.
Chaque chapitre doit contenir :
- Un titre court et accrocheur
- Un résumé en 1 phrase

Réponds au format JSON suivant :
{{
  "chapters": [
    {{"number": 1, "title": "...", "summary": "..."}},
    ...
  ]
}}
```

**Possible Solutions**:
1. **Improve prompt engineering** - Make JSON requirements more explicit
2. **Add JSON validation/repair** - Post-process output to fix minor JSON issues
3. **Use different model parameters** - Adjust temperature/max_tokens
4. **Implement retry logic** - Regenerate if JSON parsing fails

---

## 📋 Summary of Fixes Applied

| Issue | Status | Solution |
|-------|--------|----------|
| Missing `celeste-cohere` | ✅ Fixed | Manual installation |
| Missing `celeste-mistral` | ✅ Fixed | Manual installation |
| Invalid model name | ✅ Fixed | Updated `.env` |
| JSON parsing errors | ⚠️ Partial | Needs prompt improvement |

---

## 🎯 Recommendations for Celeste Team

### 1. Fix Package Dependencies

**Action Items**:
- Update `pyproject.toml` to include all provider packages in `text-generation` extra
- Ensure version synchronization across all Celeste packages
- Add pre-install checks to verify all dependencies

**Suggested `pyproject.toml` update**:
```toml
extras_require = {
    "text-generation" = [
        "celeste-anthropic>=0.3.0",
        "celeste-cohere>=0.3.0",
        "celeste-google>=0.3.0", 
        "celeste-mistral>=0.3.0",
        "celeste-openai>=0.3.0",
        "celeste-text-generation>=0.3.0"
    ]
}
```

### 2. Improve Error Messages

**Current**: Generic "Celeste library not installed"
**Suggested**: Specific missing package identification
```
RuntimeError: Missing Celeste provider package: 'celeste-cohere'
Install with: pip install celeste-cohere
```

### 3. Document Supported Models

**Action Items**:
- Create a `SUPPORTED_MODELS.md` file
- List all supported models per provider
- Include in README with clear examples

**Example**:
```markdown
## Supported Models

### Google Gemini
- `gemini-2.5-flash` (recommended)
- `gemini-2.5-flash-lite`
- `gemini-2.5-pro`
- `gemini-3-pro-preview`

### OpenAI
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-3.5-turbo`
```

### 4. Add JSON Validation Utilities

**Suggested Features**:
- Automatic JSON repair for common issues
- Schema validation
- Retry mechanism with improved prompts

```python
def safe_parse_json(text: str) -> Optional[dict]:
    """Attempt to parse JSON with automatic repair"""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try to extract JSON from markdown code blocks
        if "```json" in text:
            json_part = text.split("```json")[1].split("```")[0]
            return json.loads(json_part)
        # Try other repair strategies...
        return None
```

### 5. Consider Meta-Package

**Suggestion**: Create `celeste-ai-all` package that installs everything:
```bash
pip install celeste-ai-all
```

---

## 📊 Current Package Versions

```
celeste-ai                0.3.2
celeste-anthropic         0.3.0
celeste-cohere            0.3.0
celeste-google            0.3.2
celeste-mistral           0.3.0
celeste-openai            0.3.0
celeste-text-generation   0.3.0
```

---

## 🔧 Testing Results

**Before Fixes**:
- ❌ All tests failed due to missing dependencies
- ❌ Model not found error

**After Fixes**:
- ✅ Basic text generation works
- ✅ Model initialization successful
- ⚠️ Story plan generation fails due to JSON parsing (needs improvement)

---

## 📝 Additional Notes

1. **Installation Time**: ~30 seconds for all Celeste packages
2. **Dependency Tree**: Clean, no conflicts detected
3. **Performance**: Good response times from Gemini API
4. **Compatibility**: Works well with Python 3.13

---

## 🤝 How to Help

1. **Star the project** on GitHub
2. **Report issues** with detailed reproduction steps
3. **Contribute fixes** for the dependency issues
4. **Improve documentation** around installation and model support

---

**Report Author**: StoryBox IA Team  
**Contact**: [GitHub Issues](https://github.com/your-repo/issues)  
**Status**: Open for developer review

---

> "The installation experience is the first impression users get of your library. Making it smooth and reliable builds trust and confidence." - Open Source Best Practices