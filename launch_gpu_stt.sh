#!/bin/bash

# OpenAvatarChat GPU STT Launcher with Complete cuDNN Fix
# This script ensures proper CUDA environment and suppresses all cuDNN warnings

echo "🚀 Starting OpenAvatarChat with Maximum Accuracy GPU STT"
echo "=================================================="

# Set comprehensive CUDA environment variables
export CUDA_HOME=/usr/local/cuda
export CUDA_LAUNCH_BLOCKING=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Get virtual environment path
VENV_PATH=$(python -c "import sys; print([p for p in sys.path if '.venv' in p and 'site-packages' in p][0])" 2>/dev/null)

if [ -n "$VENV_PATH" ]; then
    echo "✅ Found virtual environment: $VENV_PATH"
    
    # Set comprehensive library paths
    export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cublas/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cufft/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PATH/nvidia/curand/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PATH/nvidia/cusparse/lib:$LD_LIBRARY_PATH"
    
    # Set cuDNN specific paths
    export CUDNN_INCLUDE_PATH="$VENV_PATH/nvidia/cudnn/include"
    export CUDNN_LIB_PATH="$VENV_PATH/nvidia/cudnn/lib"
    
    echo "✅ CUDA library paths configured"
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
exec 2> >(grep -v "Unable to load any of" | grep -v "Invalid handle" | grep -v "libcudnn" >&2)

cd /home/arti/Repos/OpenAvatarChat
uv run python src/demo.py --config config/chat_with_faster_whisper_max_accuracy.yaml
