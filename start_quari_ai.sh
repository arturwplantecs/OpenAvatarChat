#!/bin/bash

# QUARI AI Chat Setup Script
# This sets up the complete AI chat with Polish voice and avatar

echo "🚀 Starting QUARI AI Chat Setup..."

# Kill any existing processes
echo "🔄 Stopping existing processes..."
pkill -f "native_websocket_server.py" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true

# Wait for processes to stop
sleep 2

# Check if we're in the right directory
if [ ! -f "src/native_websocket_server.py" ]; then
    echo "❌ Error: Please run this script from the OpenAvatarChat root directory"
    exit 1
fi

# Check if frontend exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: Frontend directory not found. Please create the Next.js frontend first."
    exit 1
fi

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
if ! uv run python -c "import transformers" 2>/dev/null; then
    echo "Installing transformers..."
    uv add transformers torch
fi

# Start backend with working AI configuration
echo "🤖 Starting AI Backend (WebSocket server with OpenAI GPT)..."
cd /home/plantecs/Repos/OpenAvatarChat
uv run python src/native_websocket_server.py --config config/chat_websocket_text_only.yaml &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 8

# Check if backend is running
if ! curl -s http://localhost:8282/api/health > /dev/null; then
    echo "❌ Backend failed to start. Checking logs..."
    wait $BACKEND_PID
    exit 1
fi

echo "✅ Backend started successfully!"

# Start frontend
echo "🌐 Starting Frontend (Next.js with live avatar)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "🎉 QUARI AI Chat is now running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8282"
echo "🩺 Health Check: http://localhost:8282/api/health"
echo ""
echo "Features enabled:"
echo "  ✅ OpenAI GPT-4o-mini (Polish language)"
echo "  ✅ Real-time AI chat responses"
echo "  ✅ WebSocket streaming communication"
echo "  ✅ Session management"
echo "  ✅ Webcam picture-in-picture"
echo "  ✅ Modern Next.js frontend"
echo ""
echo "💬 Try typing: 'Cześć, jak masz na imię?'"
echo "💭 Text chat: Type in the input box"
echo "� Voice & Avatar: Switch to full config when ready"
echo ""
echo "To stop: Ctrl+C or run: pkill -f 'native_websocket_server\\|npm.*dev'"
echo ""

# Wait for user to stop
wait $BACKEND_PID $FRONTEND_PID
