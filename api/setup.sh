#!/bin/bash

# Setup script for OpenAvatarChat API
# Creates symlinks for models and ensures proper directory structure

set -e

echo "🔧 Setting up OpenAvatarChat API..."

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$SCRIPT_DIR"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 API directory: $API_DIR"

# Create models symlink in API directory
if [ ! -e "$API_DIR/models" ]; then
    if [ -d "$PROJECT_ROOT/models" ]; then
        echo "🔗 Creating models symlink..."
        ln -s "$PROJECT_ROOT/models" "$API_DIR/models"
        echo "✅ Models symlink created"
    else
        echo "⚠️  Warning: $PROJECT_ROOT/models directory not found"
        echo "   Create the models directory and download required models"
        mkdir -p "$API_DIR/models"
        echo "📁 Created empty models directory"
    fi
else
    echo "✅ Models already available"
fi

# Create logs symlink in API directory
if [ ! -e "$API_DIR/logs" ]; then
    if [ -d "$PROJECT_ROOT/logs" ]; then
        echo "🔗 Creating logs symlink..."
        ln -s "$PROJECT_ROOT/logs" "$API_DIR/logs"
        echo "✅ Logs symlink created"
    else
        echo "📁 Creating logs directory..."
        mkdir -p "$API_DIR/logs"
        echo "✅ Logs directory created"
    fi
else
    echo "✅ Logs already available"
fi

# Create ssl_certs symlink in API directory
if [ ! -e "$API_DIR/ssl_certs" ]; then
    if [ -d "$PROJECT_ROOT/ssl_certs" ]; then
        echo "🔗 Creating ssl_certs symlink..."
        ln -s "$PROJECT_ROOT/ssl_certs" "$API_DIR/ssl_certs"
        echo "✅ SSL certs symlink created"
    else
        echo "📁 Creating ssl_certs directory..."
        mkdir -p "$API_DIR/ssl_certs"
        echo "✅ SSL certs directory created"
    fi
else
    echo "✅ SSL certs already available"
fi

# Check if virtual environment exists
if [ ! -d "$API_DIR/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$API_DIR/venv"
    echo "✅ Virtual environment created"
fi

# Activate virtual environment and install requirements
echo "📥 Installing requirements..."
source "$API_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -r "$API_DIR/requirements.txt"
echo "✅ Requirements installed"

# Check for required models
echo "🔍 Checking for required models..."

MODELS_NEEDED=()

# Check FasterWhisper model
if [ ! -d "$API_DIR/models/faster-whisper-large-v3" ] && [ ! -d "$PROJECT_ROOT/models/faster-whisper-large-v3" ]; then
    MODELS_NEEDED+=("FasterWhisper large-v3")
fi

# Check PiperTTS model
if [ ! -f "$API_DIR/models/piper/pl_PL-gosia-medium.onnx" ] && [ ! -f "$PROJECT_ROOT/models/piper/pl_PL-gosia-medium.onnx" ]; then
    MODELS_NEEDED+=("PiperTTS Polish model")
fi

# Check LiteAvatar model
if [ ! -d "$API_DIR/models/lite_avatar" ] && [ ! -d "$PROJECT_ROOT/models/lite_avatar" ]; then
    MODELS_NEEDED+=("LiteAvatar models")
fi

if [ ${#MODELS_NEEDED[@]} -gt 0 ]; then
    echo "⚠️  Missing models:"
    for model in "${MODELS_NEEDED[@]}"; do
        echo "   - $model"
    done
    echo ""
    echo "📋 To download models, run the following from project root:"
    echo "   ./scripts/download_liteavatar_weights.sh"
    echo "   ./scripts/setup_pipertts.sh"
    echo "   # FasterWhisper models are downloaded automatically on first use"
    echo ""
    echo "🔄 The API will use mock handlers until real models are available"
else
    echo "✅ All required models found"
fi

echo ""
echo "🎯 Setup complete!"
echo ""
echo "To start the API:"
echo "  cd $API_DIR"
echo "  ./start_api.sh"
echo ""
echo "To start the frontend:"
echo "  cd $PROJECT_ROOT/frontend"
echo "  python3 serve.py"
echo ""
echo "Then open: http://localhost:3000"
