#!/bin/bash

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Set CUDA environment variables for proper cuDNN loading
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"

# Detect virtual environment path
if [ -d "$PROJECT_ROOT/.venv" ]; then
    VENV_PYTHON_PATH="$PROJECT_ROOT/.venv/lib/python3.11/site-packages"
    export LD_LIBRARY_PATH="$VENV_PYTHON_PATH/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PYTHON_PATH/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VENV_PYTHON_PATH/nvidia/cublas/lib:$LD_LIBRARY_PATH"
    
    # Print environment info
    echo "CUDA Environment Setup:"
    echo "CUDA_HOME: $CUDA_HOME"
    echo "VENV_PATH: $VENV_PYTHON_PATH"
    echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
    echo ""

    # Check if cuDNN libraries are accessible
    echo "Checking cuDNN libraries:"
    if [ -d "$VENV_PYTHON_PATH/nvidia/cudnn/lib" ]; then
        find "$VENV_PYTHON_PATH/nvidia/cudnn/lib" -name "*cudnn*" | head -5
    else
        echo "cuDNN library path not found in virtual environment"
    fi
else
    echo "⚠️  Virtual environment not found, using system CUDA"
fi

echo ""
echo "Starting OpenAvatarChat with GPU-accelerated maximum accuracy STT..."
echo ""

# Start the application with UV from project root
cd "$PROJECT_ROOT"
uv run src/demo.py --config config/chat_with_faster_whisper_max_accuracy.yaml
