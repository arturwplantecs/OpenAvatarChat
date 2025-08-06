#!/bin/bash
# OpenAvatarChat Setup Script

echo "🚀 Starting OpenAvatarChat Frontend & Backend"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Frontend selection
echo ""
echo -e "${PURPLE}🎨 Choose your frontend:${NC}"
echo "1) Next.js Frontend (Modern, React-based)"
echo "2) Original Frontend (Simple HTML/JS)"
echo ""
read -p "Enter your choice (1-2): " frontend_choice

case $frontend_choice in
    1)
        FRONTEND_TYPE="nextjs"
        FRONTEND_PORT=3000
        FRONTEND_DIR="frontend-nextjs"
        FRONTEND_CMD="npm run dev"
        echo -e "${GREEN}✨ Using Next.js Frontend${NC}"
        ;;
    2)
        FRONTEND_TYPE="original"
        FRONTEND_PORT=3000
        FRONTEND_DIR="frontend"
        FRONTEND_CMD="python3 serve.py"
        echo -e "${GREEN}✨ Using Original Frontend${NC}"
        ;;
    *)
        echo -e "${YELLOW}⚠️  Invalid choice, defaulting to Next.js Frontend${NC}"
        FRONTEND_TYPE="nextjs"
        FRONTEND_PORT=3000
        FRONTEND_DIR="frontend-nextjs"
        FRONTEND_CMD="npm run dev"
        ;;
esac

echo ""

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check API port
if ! check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use (API might be running)${NC}"
else
    echo -e "${BLUE}🔧 Starting API server on port 8000 (HTTP)...${NC}"
    
    # Set up CUDA environment for GPU acceleration BEFORE changing directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    VENV_PATH="$SCRIPT_DIR/.venv"
    
    if [ -d "$VENV_PATH" ]; then
        # Use virtual environment CUDA libraries
        VENV_SITE_PACKAGES="$VENV_PATH/lib/python3.11/site-packages"
        
        # Enhanced CUDA library paths - prioritize virtual environment
        CUDNN_LIB_PATH="$VENV_SITE_PACKAGES/nvidia/cudnn/lib"
        CUDA_RUNTIME_PATH="$VENV_SITE_PACKAGES/nvidia/cuda_runtime/lib"
        CUBLAS_PATH="$VENV_SITE_PACKAGES/nvidia/cublas/lib"
        CTRANSLATE2_PATH="$VENV_SITE_PACKAGES/ctranslate2.libs"
        
        # Add PyTorch CUDA libraries as well
        TORCH_LIB_PATH="$VENV_SITE_PACKAGES/torch/lib"
        
        # Set comprehensive LD_LIBRARY_PATH with virtual environment libraries first
        export LD_LIBRARY_PATH="$CUDNN_LIB_PATH:$CUDA_RUNTIME_PATH:$CUBLAS_PATH:$CTRANSLATE2_PATH:$TORCH_LIB_PATH:${LD_LIBRARY_PATH:-}"
        
        # Also set CUDA environment variables
        export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
        export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
        
        echo -e "${GREEN}✅ CUDA environment configured for GPU acceleration${NC}"
        echo -e "${BLUE}📍 CUDNN_LIB_PATH: $CUDNN_LIB_PATH${NC}"
        
        # Verify critical libraries exist
        if [ -f "$CUDNN_LIB_PATH/libcudnn_cnn.so.9" ]; then
            echo -e "${GREEN}✅ libcudnn_cnn.so.9 found${NC}"
        else
            echo -e "${RED}❌ libcudnn_cnn.so.9 NOT found${NC}"
        fi
        
        # Verify versioned links exist
        if [ -f "$CUDNN_LIB_PATH/libcudnn_cnn.so.9.1.0" ]; then
            echo -e "${GREEN}✅ libcudnn_cnn.so.9.1.0 found${NC}"
        else
            echo -e "${RED}❌ libcudnn_cnn.so.9.1.0 NOT found${NC}"
        fi
        
        echo -e "${BLUE}📍 LD_LIBRARY_PATH: $LD_LIBRARY_PATH${NC}"
    fi
    
    cd api
    
    python3 main.py --port 8000 &
    API_PID=$!
    cd ..
    sleep 3
    echo -e "${GREEN}✅ API server started (PID: $API_PID)${NC}"
fi

# Check Frontend port
if ! check_port $FRONTEND_PORT; then
    echo -e "${YELLOW}⚠️  Port $FRONTEND_PORT is already in use (Frontend might be running)${NC}"
else
    echo -e "${BLUE}🎨 Starting $FRONTEND_TYPE Frontend server on port $FRONTEND_PORT...${NC}"
    cd $FRONTEND_DIR
    
    # Install dependencies for Next.js if needed
    if [ "$FRONTEND_TYPE" = "nextjs" ]; then
        if [ ! -d "node_modules" ]; then
            echo -e "${BLUE}📦 Installing Next.js dependencies...${NC}"
            npm install
        fi
    fi
    
    $FRONTEND_CMD &
    FRONTEND_PID=$!
    cd ..
    sleep 3
    echo -e "${GREEN}✅ $FRONTEND_TYPE Frontend server started (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 OpenAvatarChat is ready!${NC}"
echo "=============================================="
echo -e "${BLUE}📱 Frontend:${NC} http://localhost:$FRONTEND_PORT"
echo -e "${BLUE}🔧 API Docs:${NC} http://localhost:8000/docs"
if [ "$FRONTEND_TYPE" = "nextjs" ]; then
    echo -e "${BLUE}🎨 Frontend Type:${NC} Next.js (Modern React App)"
    echo ""
    echo -e "${YELLOW}💡 Next.js Features:${NC}"
    echo "  • 🎬 Smooth Canvas-based avatar video (900px height, 9:16 ratio)"
    echo "  • 💬 Modern chat interface with animations"
    echo "  • 🎤 Voice recording (hold microphone button)"
    echo "  • 🔊 Audio playback with avatar lip-sync"
    echo "  • 🎨 Professional dark theme with gradients"
    echo "  • ⚡ Real-time message animations"
else
    echo -e "${BLUE}🎨 Frontend Type:${NC} Original (Simple HTML/JS)"
    echo -e "${BLUE}🧪 Test Page:${NC} http://localhost:3000/test.html"
    echo ""
    echo -e "${YELLOW}💡 Original Features:${NC}"
    echo "  • 💬 Text chat with Polish AI assistant"
    echo "  • 🎤 Voice recording (click and hold microphone)"
    echo "  • 🔊 Text-to-speech responses (Polish voice)"
    echo "  • 👤 Avatar animations (when available)"
    echo "  • ⚙️  Settings panel (gear icon)"
fi
echo ""
echo -e "${YELLOW}🎮 Controls:${NC}"
if [ "$FRONTEND_TYPE" = "nextjs" ]; then
    echo "  • Type message and press Enter - Send text"
    echo "  • Hold microphone button - Record voice message"
    echo "  • Volume button - Toggle audio on/off"
    echo "  • Settings button - Access configuration"
else
    echo "  • Enter - Send text message"
    echo "  • Space - Hold to record voice (when not typing)"
    echo "  • Escape - Close settings"
fi
echo ""
echo -e "${RED}🛑 To stop servers:${NC}"
if [ "$FRONTEND_TYPE" = "nextjs" ]; then
    echo "  pkill -f 'main.py'"
    echo "  pkill -f 'next'"
else
    echo "  pkill -f 'main.py'"
    echo "  pkill -f 'serve.py'"
fi
echo ""

# Keep script running
echo -e "${BLUE}Press Ctrl+C to stop all servers and exit${NC}"
if [ "$FRONTEND_TYPE" = "nextjs" ]; then
    trap 'echo -e "\n${RED}🛑 Stopping servers...${NC}"; pkill -f "main.py"; pkill -f "next"; exit' INT
else
    trap 'echo -e "\n${RED}🛑 Stopping servers...${NC}"; pkill -f "main.py"; pkill -f "serve.py"; exit' INT
fi
while true; do
    sleep 1
done
