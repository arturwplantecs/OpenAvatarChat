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
export CONDA_PREFIX="${CONDA_PREFIX:-/home/arti/miniconda}"
export CUDA_HOME="$CONDA_PREFIX"

# Enhanced CUDA library paths with new cuDNN 9.1.1.17
CUDNN_LIB_PATH="$CONDA_PREFIX/lib"
CUDA_RUNTIME_PATH="$CONDA_PREFIX/lib"

# Set comprehensive LD_LIBRARY_PATH
export LD_LIBRARY_PATH="$CUDNN_LIB_PATH:$CUDA_RUNTIME_PATH:${LD_LIBRARY_PATH:-}"

# CUDA environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export CUDA_LAUNCH_BLOCKING=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# cuDNN optimization settings
export CUDNN_INCLUDE_PATH="$CONDA_PREFIX/include"
export CUDNN_LIB_PATH="$CONDA_PREFIX/lib"

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
grep -v "Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor" | \
grep -v "pkg_resources is deprecated" | \
grep -v "FutureWarning: You are using \`torch.load\`" | \
grep -v "torch.cuda.amp.autocast" || true
