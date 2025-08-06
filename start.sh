#!/bin/bash
# OpenAvatarChat Setup Script

echo "🚀 Starting OpenAvatarChat Frontend & Backend"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo -e "${BLUE}🔧 Starting API server on port 8000...${NC}"
    cd api
    python3 main.py &
    API_PID=$!
    cd ..
    sleep 3
    echo -e "${GREEN}✅ API server started (PID: $API_PID)${NC}"
fi

# Check Frontend port
if ! check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use (Frontend might be running)${NC}"
else
    echo -e "${BLUE}🎨 Starting Frontend server on port 3000...${NC}"
    cd frontend
    python3 serve.py &
    FRONTEND_PID=$!
    cd ..
    sleep 2
    echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 OpenAvatarChat is ready!${NC}"
echo "=============================================="
echo -e "${BLUE}📱 Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}🔧 API Docs:${NC} http://localhost:8000/api/docs"
echo -e "${BLUE}🧪 Test Page:${NC} http://localhost:3000/test.html"
echo ""
echo -e "${YELLOW}💡 Features:${NC}"
echo "  • 💬 Text chat with Polish AI assistant"
echo "  • 🎤 Voice recording (click and hold microphone)"
echo "  • 🔊 Text-to-speech responses (Polish voice)"
echo "  • 👤 Avatar animations (when available)"
echo "  • ⚙️  Settings panel (gear icon)"
echo ""
echo -e "${YELLOW}🎮 Controls:${NC}"
echo "  • Enter - Send text message"
echo "  • Space - Hold to record voice (when not typing)"
echo "  • Escape - Close settings"
echo ""
echo -e "${RED}🛑 To stop servers:${NC}"
echo "  pkill -f 'main.py'"
echo "  pkill -f 'serve.py'"
echo ""

# Keep script running
echo -e "${BLUE}Press Ctrl+C to stop all servers and exit${NC}"
trap 'echo -e "\n${RED}🛑 Stopping servers...${NC}"; pkill -f "main.py"; pkill -f "serve.py"; exit' INT
while true; do
    sleep 1
done
