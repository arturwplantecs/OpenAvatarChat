#!/bin/bash

# OpenAvatarChat API Backend Startup Script

set -e

echo "🚀 Starting OpenAvatarChat API Backend..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists, create if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install API requirements
echo "📥 Installing API requirements..."
pip install -r api/requirements.txt

# Set Python path to include the src directory
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Default settings
HOST=${AVATARCHAT_HOST:-127.0.0.1}
PORT=${AVATARCHAT_PORT:-8000}
WORKERS=${AVATARCHAT_WORKERS:-1}
DEBUG=${AVATARCHAT_DEBUG:-false}

echo "🌐 Host: $HOST"
echo "🔌 Port: $PORT"
echo "👥 Workers: $WORKERS"
echo "🐛 Debug: $DEBUG"

# Check if models directory exists
if [ ! -d "models" ]; then
    echo "⚠️  Warning: models directory not found. Some features may not work properly."
    echo "   Please run the model download scripts if needed."
fi

# Start the API server
echo "🎯 Starting API server..."
cd api

if [ "$DEBUG" = "true" ]; then
    # Development mode with auto-reload
    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level debug
else
    # Production mode
    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info
fi
