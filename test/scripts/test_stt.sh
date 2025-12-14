#!/bin/bash
# Test script for Whisper STT
# Generates a test audio file and transcribes it

set -e

# Paths
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WHISPER_BIN="/tmp/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL="$PROJECT_ROOT/models/whisper/ggml-small.bin"
OUTPUT_DIR="$PROJECT_ROOT/test/audio_samples"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "======================================"
echo "StoryBox IA - STT Test"
echo "======================================"
echo "Model: $(basename $WHISPER_MODEL)"
echo "Output: $OUTPUT_DIR"
echo ""

# Check if whisper-cli exists
if [ ! -f "$WHISPER_BIN" ]; then
    echo "✗ Error: whisper-cli not found at $WHISPER_BIN"
    echo "  Compile whisper.cpp first (see docs/MAC_DEVELOPMENT.md)"
    exit 1
fi

# Check if model exists
if [ ! -f "$WHISPER_MODEL" ]; then
    echo "✗ Error: Model not found at $WHISPER_MODEL"
    echo "  Download models first (see README.md)"
    exit 1
fi

# Generate test audio using macOS 'say' command
echo "Generating test audio..."
TEST_TEXT="Raconte-moi une histoire sur des pirates qui cherchent un trésor caché sur une île mystérieuse."
TEST_AUDIO="$OUTPUT_DIR/test_input_pirates.wav"

# Use macOS say command (French voice)
if command -v say &> /dev/null; then
    say -v Thomas "$TEST_TEXT" -o "$OUTPUT_DIR/test_input_pirates.aiff"
    # Convert to 16kHz mono WAV (required for Whisper)
    ffmpeg -y -i "$OUTPUT_DIR/test_input_pirates.aiff" -ar 16000 -ac 1 "$TEST_AUDIO" 2>/dev/null
    rm "$OUTPUT_DIR/test_input_pirates.aiff"
    echo "✓ Generated: test_input_pirates.wav"
else
    echo "✗ Error: 'say' command not found (macOS only)"
    exit 1
fi

# Test transcription
echo ""
echo "Transcribing audio..."
echo "Original: $TEST_TEXT"
echo ""

$WHISPER_BIN \
    -m "$WHISPER_MODEL" \
    -l fr \
    -t 4 \
    "$TEST_AUDIO"

echo ""
echo "======================================"
echo "✓ STT test completed"
echo "======================================"
