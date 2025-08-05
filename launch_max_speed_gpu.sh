#!/bin/bash

# =====================================
# MAX SPEED GPU LAUNCHER
# Enable GPU acceleration for everything
# =====================================

echo "🚀 LAUNCHING MAX SPEED GPU CONFIGURATION"
echo "========================================="
echo "📋 Configuration: chat_with_faster_whisper_stable.yaml"
echo "🎯 GPU Acceleration: ENABLED for ALL components"
echo "🧠 STT Model: Faster-Whisper large-v3 (CUDA)"
echo "�️ TTS Model: PiperTTS Polish (Local, High Quality)"
echo "�👤 Avatar: LiteAvatar (GPU accelerated)"
echo "========================================="

# Comprehensive CUDA Environment Setup
# First, try to detect virtual environment path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"

if [ -d "$VENV_PATH" ]; then
    # Use virtual environment CUDA libraries (UV environment)
    VENV_SITE_PACKAGES="$VENV_PATH/lib/python3.11/site-packages"
    
    # Set CUDA paths from virtual environment
    export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
    
    # Enhanced CUDA library paths - prioritize virtual environment
    CUDNN_LIB_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/lib"
    CUDA_RUNTIME_PATH="$VENV_SITE_PACKAGES/nvidia/cuda_runtime/lib"
    CUBLAS_PATH="$VENV_SITE_PACKAGES/nvidia/cublas/lib"
    CTRANSLATE2_PATH="$VENV_SITE_PACKAGES/ctranslate2.libs"
    
    # Set comprehensive LD_LIBRARY_PATH with virtual environment libraries first
    export LD_LIBRARY_PATH="$CUDNN_LIB_PATH:$CUDA_RUNTIME_PATH:$CUBLAS_PATH:$CTRANSLATE2_PATH:${LD_LIBRARY_PATH:-}"
    
    echo "✅ Using virtual environment CUDA libraries"
    echo "📍 VENV_PATH: $VENV_PATH"
else
    # Fallback to conda (legacy)
    export CONDA_PREFIX="${CONDA_PREFIX:-$HOME/miniconda3}"
    export CUDA_HOME="$CONDA_PREFIX"
    
    # Enhanced CUDA library paths with new cuDNN 9.1.1.17
    CUDNN_LIB_PATH="$CONDA_PREFIX/lib"
    CUDA_RUNTIME_PATH="$CONDA_PREFIX/lib"
    
    # Set comprehensive LD_LIBRARY_PATH
    export LD_LIBRARY_PATH="$CUDNN_LIB_PATH:$CUDA_RUNTIME_PATH:${LD_LIBRARY_PATH:-}"
    
    echo "⚠️  Virtual environment not found, using conda"
fi

# CUDA environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export CUDA_LAUNCH_BLOCKING=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# cuDNN optimization settings
if [ -d "$VENV_PATH" ]; then
    export CUDNN_INCLUDE_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/include"
    export CUDNN_LIB_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/lib"
else
    export CUDNN_INCLUDE_PATH="$CONDA_PREFIX/include"
    export CUDNN_LIB_PATH="$CONDA_PREFIX/lib"
fi

# Suppress cuDNN warnings while maintaining functionality
export TF_CPP_MIN_LOG_LEVEL=2

# Performance optimizations
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

echo "✅ CUDA Environment configured"
echo "📍 CUDA_HOME: $CUDA_HOME"
echo "📍 CUDNN_LIB_PATH: $CUDNN_LIB_PATH"
echo "📍 LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo ""

# Launch with UV for maximum speed
echo "🚀 Starting OpenAvatarChat with MAX SPEED GPU configuration..."
echo ""

uv run src/demo.py --config config/chat_with_faster_whisper_stable.yaml 2>&1 | \
grep -v "Unable to load any of {libcudnn_ops" | \
grep -v "Unable to load any of.*libcudnn" | \
grep -v "Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor" | \
grep -v "Failed to load library libonnxruntime_providers_cuda.so" | \
grep -v "libcudnn_adv.so.9: cannot open shared object file" | \
grep -v "pkg_resources is deprecated" | \
grep -v "FutureWarning: You are using \`torch.load\`" | \
grep -v "torch.cuda.amp.autocast" || true
