#!/bin/bash

# OpenAvatarChat Maximum Accuracy Startup Script
# Optimized for GPU with CPU fallback

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "🚀 Starting OpenAvatarChat with Maximum Accuracy Settings"
echo "🎯 STT: Faster-Whisper large-v3 with maximum accuracy"

# Set environment variables for better GPU compatibility
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024

# Detect and set LD_LIBRARY_PATH for ctranslate2
if [ -d "$PROJECT_ROOT/.venv" ]; then
    VENV_PYTHON_PATH="$PROJECT_ROOT/.venv/lib/python3.11/site-packages"
    if [ -d "$VENV_PYTHON_PATH/ctranslate2.libs" ]; then
        export LD_LIBRARY_PATH="$VENV_PYTHON_PATH/ctranslate2.libs:$LD_LIBRARY_PATH"
        echo "✅ Found ctranslate2 libraries in virtual environment"
    fi
fi

# Disable cuDNN optimizations that cause issues
export CUDNN_DETERMINISTIC=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

echo "🔧 Environment configured for maximum accuracy"
echo "📁 Config: chat_with_faster_whisper_max_accuracy.yaml"
echo ""

# Change to project directory
cd "$PROJECT_ROOT"

# Start the application with UV
echo "▶️  Starting application..."
uv run src/demo.py --config config/chat_with_faster_whisper_max_accuracy.yaml
