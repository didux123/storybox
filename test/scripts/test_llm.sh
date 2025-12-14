#!/bin/bash
# Test script for LLM story generation

set -e

# Paths
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LLAMA_BIN="/tmp/llama.cpp/build/bin/llama-cli"
LLM_MODEL="$PROJECT_ROOT/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf"

echo "======================================"
echo "StoryBox IA - LLM Test"
echo "======================================"
echo "Model: $(basename $LLM_MODEL)"
echo ""

# Check if llama-cli exists
if [ ! -f "$LLAMA_BIN" ]; then
    echo "✗ Error: llama-cli not found at $LLAMA_BIN"
    echo "  Compile llama.cpp first (see docs/MAC_DEVELOPMENT.md)"
    exit 1
fi

# Check if model exists
if [ ! -f "$LLM_MODEL" ]; then
    echo "✗ Error: Model not found at $LLM_MODEL"
    echo "  Download models first (see README.md)"
    exit 1
fi

# Test prompt for story plan generation
PROMPT="Génère un plan de 5 chapitres cohérents pour une histoire sur des pirates qui cherchent un trésor.
Chaque chapitre doit contenir :
- Un titre court et accrocheur
- Un résumé en 1 phrase

Format JSON :
{
  \"chapters\": [
    {\"number\": 1, \"title\": \"...\", \"summary\": \"...\"},
    ...
  ]
}"

echo "Generating story plan..."
echo ""
echo "Prompt:"
echo "$PROMPT"
echo ""
echo "======================================"
echo "LLM Output:"
echo "======================================"

$LLAMA_BIN \
    -m "$LLM_MODEL" \
    -n 500 \
    -t 4 \
    --temp 0.7 \
    --top-p 0.9 \
    -p "$PROMPT"

echo ""
echo "======================================"
echo "✓ LLM test completed"
echo "======================================"
