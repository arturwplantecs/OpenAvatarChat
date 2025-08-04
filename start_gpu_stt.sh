#!/bin/bash

# Set CUDA environment variables for proper cuDNN loading
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH="/home/arti/Repos/OpenAvatarChat/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/home/arti/Repos/OpenAvatarChat/.venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/home/arti/Repos/OpenAvatarChat/.venv/lib/python3.11/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH"

# Print environment info
echo "CUDA Environment Setup:"
echo "CUDA_HOME: $CUDA_HOME"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo ""

# Check if cuDNN libraries are accessible
echo "Checking cuDNN libraries:"
find /home/arti/Repos/OpenAvatarChat/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib -name "*cudnn*" | head -5

echo ""
echo "Starting OpenAvatarChat with GPU-accelerated maximum accuracy STT..."
echo ""

# Start the application with UV
cd /home/arti/Repos/OpenAvatarChat
uv run python src/demo.py --config config/chat_with_faster_whisper_max_accuracy.yaml
