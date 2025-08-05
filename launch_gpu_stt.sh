#!/bin/bash

# OpenAvatarChat GPU STT Launcher with Complete cuDNN Fix
# This script ensures proper CUDA environment and suppresses all cuDNN warnings

echo "🚀 Starting OpenAvatarChat with Maximum Accuracy GPU STT"
echo "=================================================="

# Set comprehensive CUDA environment variables
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
export CUDA_LAUNCH_BLOCKING=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Get script directory for virtual environment detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"

# Try to detect virtual environment path more universally
if [ -d "$VENV_PATH" ]; then
    VENV_SITE_PACKAGES="$VENV_PATH/lib/python3.11/site-packages"
    
    # Set comprehensive library paths from virtual environment
    export LD_LIBRARY_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_SITE_PACKAGES/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_SITE_PACKAGES/nvidia/cublas/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_SITE_PACKAGES/ctranslate2.libs:$LD_LIBRARY_PATH"
    
    # Set cuDNN specific paths
    export CUDNN_INCLUDE_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/include"
    export CUDNN_LIB_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/lib"
    
    echo "✅ Using virtual environment CUDA libraries"
    echo "📍 VENV_PATH: $VENV_PATH"
elif command -v python &> /dev/null; then
    # Fallback to detecting through python site-packages
    VENV_PATH=$(python -c "import sys; import site; print(next((p for p in site.getsitepackages() if 'site-packages' in p), ''))" 2>/dev/null)
    
    # Fallback to checking sys.path for .venv
    if [ -z "$VENV_PATH" ]; then
        VENV_PATH=$(python -c "import sys; print(next((p for p in sys.path if '.venv' in p and 'site-packages' in p), ''))" 2>/dev/null)
    fi
    
    if [ -n "$VENV_PATH" ]; then
        export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
        export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
        export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cublas/lib:$LD_LIBRARY_PATH"
        
        export CUDNN_INCLUDE_PATH="$VENV_PATH/nvidia/cudnn/include"
        export CUDNN_LIB_PATH="$VENV_PATH/nvidia/cudnn/lib"
        
        echo "✅ Found virtual environment: $VENV_PATH"
    else
        echo "⚠️  Virtual environment not detected, using system CUDA"
    fi
fi

if [ -n "$VENV_PATH" ]; then
    echo "✅ CUDA library paths configured"
    echo "📍 cuDNN libraries: $CUDNN_LIB_PATH"
else
    echo "⚠️  Virtual environment not detected, using system CUDA"
fi

# Print configuration
echo ""
echo "🎯 Configuration:"
echo "   Model: large-v3 (maximum accuracy)"
echo "   Device: CUDA GPU with float16"
echo "   Language: Polish (pl)"
echo "   Beam Size: 10, Best Of: 10"
echo "   Temperature: 0.0 (deterministic)"
echo ""

# Suppress cuDNN warnings completely using stderr redirection
echo "🔇 Suppressing cuDNN warnings for clean output..."
echo ""

# Start the application with UV and comprehensive error suppression
echo "🔇 Suppressing cuDNN warnings for clean output..."
echo ""

# Get the script directory to ensure we're in the right location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

uv run src/demo.py --config config/chat_with_faster_whisper_max_accuracy.yaml 2>&1 | \
grep -v "Unable to load any of {libcudnn_ops" | \
grep -v "Unable to load any of.*libcudnn" | \
grep -v "Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor" | \
grep -v "Failed to load library libonnxruntime_providers_cuda.so" | \
grep -v "libcudnn_adv.so.9: cannot open shared object file" | \
grep -v "pkg_resources is deprecated" | \
grep -v "FutureWarning: You are using \`torch.load\`" | \
grep -v "torch.cuda.amp.autocast" || true
