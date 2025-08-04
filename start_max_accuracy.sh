#!/bin/bash

# OpenAvatarChat Maximum Accuracy Startup Script
# Optimized for GPU with CPU fallback

echo "🚀 Starting OpenAvatarChat with Maximum Accuracy Settings"
echo "📊 GPU: NVIDIA GeForce RTX 2060, CUDA: 12.9"
echo "🎯 STT: Faster-Whisper large-v3 with maximum accuracy"

# Set environment variables for better GPU compatibility
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export LD_LIBRARY_PATH="/home/arti/Repos/OpenAvatarChat/.venv/lib/python3.11/site-packages/ctranslate2.libs:$LD_LIBRARY_PATH"

# Disable cuDNN optimizations that cause issues
export CUDNN_DETERMINISTIC=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

echo "🔧 Environment configured for maximum accuracy"
echo "📁 Config: chat_with_faster_whisper_max_accuracy.yaml"
echo ""

# Change to project directory
cd /home/arti/Repos/OpenAvatarChat

# Start the application with UV
echo "▶️  Starting application..."
uv run python src/demo.py --config config/chat_with_faster_whisper_max_accuracy.yaml
