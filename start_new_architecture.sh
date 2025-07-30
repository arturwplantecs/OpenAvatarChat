#!/bin/bash

# OpenAvatarChat - New Architecture Startup Script
# This script starts both the Python backend and Next.js frontend

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    # Try netstat first, fall back to ss if not available
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            return 0  # Port is in use
        else
            return 1  # Port is free
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":$port "; then
            return 0  # Port is in use
        else
            return 1  # Port is free
        fi
    else
        # Fallback: try to connect to the port
        if timeout 1 bash -c "</dev/tcp/localhost/$port" 2>/dev/null; then
            return 0  # Port is in use
        else
            return 1  # Port is free
        fi
    fi
}

# Function to install frontend dependencies
install_frontend_deps() {
    print_status "Installing frontend dependencies..."
    cd "$FRONTEND_DIR"
    
    if command -v npm &> /dev/null; then
        npm install
    elif command -v yarn &> /dev/null; then
        yarn install
    else
        print_error "Neither npm nor yarn found. Please install Node.js and npm."
        exit 1
    fi
    
    print_success "Frontend dependencies installed"
}

# Function to install Python backend dependencies
install_backend_deps() {
    print_status "Installing Python backend dependencies..."
    cd "$PROJECT_ROOT"
    
    if ! command -v uv &> /dev/null; then
        print_error "UV is not installed. Please install UV first:"
        print_error "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Install dependencies using UV
    uv sync
    
    print_success "Python backend dependencies installed"
}

# Function to install all dependencies
install_all_deps() {
    print_status "Installing all dependencies..."
    install_backend_deps
    install_frontend_deps
    print_success "All dependencies installed"
}

# Function to start the Python backend
start_backend() {
    print_status "Starting Python backend..."
    
    cd "$PROJECT_ROOT"
    
    # Check if backend port is already in use
    if check_port 8282; then
        print_warning "Port 8282 is already in use. Backend may already be running."
        return 0
    fi
    
    # Check if UV is available
    if ! command -v uv &> /dev/null; then
        print_error "UV is not installed. Please install UV first: pip install uv"
        exit 1
    fi
    
    # Start the native WebSocket server using UV
    uv run python src/native_websocket_server.py &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/openavatar_backend.pid
    
    # Wait a moment for the server to start
    sleep 3
    
    if ps -p $BACKEND_PID > /dev/null; then
        print_success "Backend started (PID: $BACKEND_PID)"
    else
        print_error "Failed to start backend"
        exit 1
    fi
}

# Function to start the Next.js frontend
start_frontend() {
    print_status "Starting Next.js frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Check if frontend port is already in use
    if check_port 3000; then
        print_warning "Port 3000 is already in use. Frontend may already be running."
        return 0
    fi
    
    # Start the development server
    if command -v npm &> /dev/null; then
        npm run dev &
    elif command -v yarn &> /dev/null; then
        yarn dev &
    else
        print_error "Neither npm nor yarn found."
        exit 1
    fi
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/openavatar_frontend.pid
    
    print_success "Frontend starting (PID: $FRONTEND_PID)"
}

# Function to stop services
stop_services() {
    print_status "Stopping OpenAvatarChat services..."
    
    # Stop backend
    if [ -f /tmp/openavatar_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/openavatar_backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            rm /tmp/openavatar_backend.pid
            print_success "Backend stopped"
        fi
    fi
    
    # Stop frontend
    if [ -f /tmp/openavatar_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/openavatar_frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            rm /tmp/openavatar_frontend.pid
            print_success "Frontend stopped"
        fi
    fi
    
    # Kill any remaining Node.js processes on port 3000
    pkill -f "next.*dev" || true
    
    print_success "All services stopped"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [start|stop|restart|status|install|install-frontend|install-backend]"
    echo ""
    echo "Commands:"
    echo "  start            - Start both backend and frontend services"
    echo "  stop             - Stop all services"
    echo "  restart          - Restart all services"
    echo "  status           - Show service status"
    echo "  install          - Install all dependencies (backend + frontend)"
    echo "  install-frontend - Install only frontend dependencies"
    echo "  install-backend  - Install only backend dependencies"
    echo ""
    echo "The application will be available at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8282"
    echo ""
    echo "Prerequisites:"
    echo "  - UV (Python package manager): https://astral.sh/uv/install.sh"
    echo "  - Node.js 18+ and npm"
}

# Function to show status
show_status() {
    print_status "Service Status:"
    
    # Check backend
    if check_port 8282; then
        print_success "Backend: Running on port 8282"
    else
        print_warning "Backend: Not running"
    fi
    
    # Check frontend
    if check_port 3000; then
        print_success "Frontend: Running on port 3000"
    else
        print_warning "Frontend: Not running"
    fi
    
    echo ""
    echo "URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8282"
    echo "  Health Check: http://localhost:8282/api/health"
}

# Main script logic
case "$1" in
    start)
        print_status "Starting OpenAvatarChat with new architecture..."
        start_backend
        sleep 2
        start_frontend
        sleep 5
        show_status
        print_success "OpenAvatarChat is now running!"
        print_status "Frontend: http://localhost:3000"
        print_status "Backend: http://localhost:8282"
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_backend
        sleep 2
        start_frontend
        sleep 5
        show_status
        ;;
    status)
        show_status
        ;;
    install)
        install_all_deps
        ;;
    install-frontend)
        install_frontend_deps
        ;;
    install-backend)
        install_backend_deps
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
