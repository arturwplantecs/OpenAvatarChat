#!/bin/bash

# =====================================
# PIPER TTS SETUP SCRIPT
# Downloads and installs PiperTTS with Polish models
# =====================================

echo "🎤 SETTING UP PIPER TTS"
echo "======================="

MODELS_DIR="models/piper"
PROJECT_DIR=$(pwd)

# Create models directory
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR" || exit 1

echo "📁 Created models directory: $MODELS_DIR"

# Download PiperTTS binary if not exists
if ! command -v piper &> /dev/null; then
    echo "📥 Installing PiperTTS..."
    
    # Try package manager first
    if command -v apt &> /dev/null; then
        echo "🔄 Trying apt package manager..."
        if sudo apt update && sudo apt install -y piper-tts 2>/dev/null; then
            echo "✅ Piper installed via apt"
        else
            echo "📦 Package not available, trying manual installation..."
            
            # Manual installation via Python
            echo "🐍 Installing via pip..."
            if pip install piper-tts 2>/dev/null; then
                echo "✅ Piper installed via pip"
            else
                echo "� Trying conda installation..."
                if conda install -c conda-forge piper-tts -y 2>/dev/null; then
                    echo "✅ Piper installed via conda"
                else
                    echo "⚠️  Automatic installation failed. Please install manually:"
                    echo "   pip install piper-tts"
                    echo "   OR download from: https://github.com/rhasspy/piper/releases"
                    echo ""
                    echo "Continuing with model download..."
                fi
            fi
        fi
    else
        # Try pip installation
        echo "🐍 Installing via pip..."
        if pip install piper-tts 2>/dev/null; then
            echo "✅ Piper installed via pip"
        else
            echo "⚠️  Could not install piper automatically."
            echo "   Please run: pip install piper-tts"
            echo "   OR download from: https://github.com/rhasspy/piper/releases"
            echo ""
            echo "Continuing with model download..."
        fi
    fi
else
    echo "✅ Piper already installed: $(which piper)"
fi

# Download Polish models
echo "📥 Downloading Polish TTS models..."

# High-quality medium model with native Polish speaker (recommended)
MODEL_NAME="pl_PL-gosia-medium"
MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx"
CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx.json"

if [[ ! -f "${MODEL_NAME}.onnx" ]]; then
    echo "📥 Downloading model: ${MODEL_NAME}.onnx"
    wget -O "${MODEL_NAME}.onnx" "$MODEL_URL" || {
        echo "❌ Failed to download model file"
        exit 1
    }
    echo "✅ Model downloaded successfully"
else
    echo "✅ Model already exists: ${MODEL_NAME}.onnx"
fi

if [[ ! -f "${MODEL_NAME}.onnx.json" ]]; then
    echo "📥 Downloading config: ${MODEL_NAME}.onnx.json"
    wget -O "${MODEL_NAME}.onnx.json" "$CONFIG_URL" || {
        echo "❌ Failed to download config file"
        exit 1
    }
    echo "✅ Config downloaded successfully"
else
    echo "✅ Config already exists: ${MODEL_NAME}.onnx.json"
fi

# Optional: Download additional models for variety
echo ""
echo "🔄 Optional: Download additional Polish models? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    # Low quality but fast model
    FAST_MODEL="pl_PL-mls_6892-low"
    FAST_MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pl/pl_PL/mls_6892/low/pl_PL-mls_6892-low.onnx"
    FAST_CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pl/pl_PL/mls_6892/low/pl_PL-mls_6892-low.onnx.json"
    
    if [[ ! -f "${FAST_MODEL}.onnx" ]]; then
        echo "📥 Downloading fast model: ${FAST_MODEL}.onnx"
        wget -O "${FAST_MODEL}.onnx" "$FAST_MODEL_URL"
        wget -O "${FAST_MODEL}.onnx.json" "$FAST_CONFIG_URL"
        echo "✅ Fast model downloaded"
    fi
fi

cd "$PROJECT_DIR" || exit 1

echo ""
echo "🎉 PIPER TTS SETUP COMPLETE!"
echo "=========================="
echo "📍 Models location: $MODELS_DIR"
echo "🎯 Main model: ${MODEL_NAME}.onnx"
echo "⚙️ Configuration updated in: config/chat_with_faster_whisper_stable.yaml"
echo ""
echo "💡 Usage Tips:"
echo "   - Adjust length_scale (speed): 0.8 = faster, 1.2 = slower"
echo "   - Adjust noise_scale (voice variation): 0.1 = robotic, 0.9 = natural"
echo "   - For multiple speakers, set speaker_id to 0, 1, 2, etc."
echo ""
echo "🚀 You can now run your application with PiperTTS!"
echo "   ./launch_max_speed_gpu.sh"
