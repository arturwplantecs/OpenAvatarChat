#!/bin/bash

# OpenAvatarChat Complete Installation Script
# This script automates the installation of all necessary components for OpenAvatarChat

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user."
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        warn "This script is optimized for Linux. Some steps may not work on other systems."
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed. Please install Python 3.10 or 3.11."
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    # Check if bc command is available for version comparison
    if ! command -v bc &> /dev/null; then
        # Fallback version check without bc
        MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
        MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
        
        if [[ $MAJOR -eq 3 ]] && [[ $MINOR -ge 10 ]]; then
            if [[ $MINOR -ge 12 ]]; then
                warn "Python version $PYTHON_VERSION detected. Officially supported versions are 3.10-3.11, but continuing anyway."
            fi
            log "Python version $PYTHON_VERSION detected and proceeding with installation"
        else
            error "Python version must be >= 3.10. Current version: $PYTHON_VERSION"
        fi
    else
        # Use bc for precise version comparison
        if [[ $(echo "$PYTHON_VERSION < 3.10" | bc) -eq 1 ]]; then
            error "Python version must be >= 3.10. Current version: $PYTHON_VERSION"
        elif [[ $(echo "$PYTHON_VERSION >= 3.12" | bc) -eq 1 ]]; then
            warn "Python version $PYTHON_VERSION detected. Officially supported versions are 3.10-3.11, but continuing anyway."
        fi
        log "Python version $PYTHON_VERSION detected and proceeding with installation"
    fi
    
    # Check CUDA
    if command -v nvidia-smi &> /dev/null; then
        CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | sed -n 's/.*CUDA Version: \([0-9.]*\).*/\1/p')
        if [[ -n "$CUDA_VERSION" ]]; then
            log "NVIDIA GPU detected with CUDA version: $CUDA_VERSION"
            if [[ $(echo "$CUDA_VERSION < 12.4" | bc) -eq 1 ]]; then
                warn "CUDA version $CUDA_VERSION detected. Version >= 12.4 is recommended."
            fi
        fi
    else
        warn "NVIDIA GPU not detected. Some features may require GPU acceleration."
    fi
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install git-lfs
    if ! command -v git-lfs &> /dev/null; then
        log "Installing git-lfs..."
        sudo apt install -y git-lfs
        git lfs install
    else
        log "git-lfs already installed"
    fi
    
    # Install other dependencies
    sudo apt install -y curl wget build-essential bc
}

# Install UV
install_uv() {
    log "Installing UV package manager..."
    
    if command -v uv &> /dev/null; then
        log "UV already installed"
        return
    fi
    
    # Install UV using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the shell configuration to make uv available
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verify installation
    if command -v uv &> /dev/null; then
        log "UV installed successfully"
    else
        error "Failed to install UV"
    fi
}

# Update git submodules
update_submodules() {
    log "Updating git submodules..."
    git submodule update --init --recursive
}

# Create virtual environment and install dependencies
install_python_deps() {
    log "Creating virtual environment and installing Python dependencies..."
    
    # Create virtual environment
    uv venv --python 3.11.11
    
    # Install basic packages
    uv pip install setuptools pip
    
    # Install all dependencies
    log "Installing all dependencies (this may take a while)..."
    uv sync --all-packages
}

# Download models based on user choice
download_models() {
    log "Model download options:"
    echo "1. Skip model downloads (install manually later)"
    echo "2. Download LiteAvatar weights only (recommended for beginners)"
    echo "3. Download MiniCPM-o-2.6 model (requires ~40GB+ space)"
    echo "4. Download MiniCPM-o-2.6-int4 model (requires ~20GB+ space)"
    echo "5. Download LAM models"
    echo "6. Download MuseTalk models"
    echo "7. Download all models (requires significant disk space)"
    
    read -p "Choose option (1-7): " model_choice
    
    case $model_choice in
        1)
            warn "Skipping model downloads. You'll need to download them manually later."
            ;;
        2)
            log "Downloading LiteAvatar weights..."
            bash scripts/download_liteavatar_weights.sh || warn "Failed to download LiteAvatar weights"
            ;;
        3)
            log "Downloading MiniCPM-o-2.6 model..."
            bash scripts/download_MiniCPM-o_2.6.sh || warn "Failed to download MiniCPM-o-2.6"
            ;;
        4)
            log "Downloading MiniCPM-o-2.6-int4 model..."
            bash scripts/download_MiniCPM-o_2.6-int4.sh || warn "Failed to download MiniCPM-o-2.6-int4"
            ;;
        5)
            log "Downloading LAM models..."
            # WAV2VEC2 model
            if [ ! -d "./models/wav2vec2-base-960h" ]; then
                git clone --depth 1 https://huggingface.co/facebook/wav2vec2-base-960h ./models/wav2vec2-base-960h || warn "Failed to download wav2vec2 model"
            fi
            # LAM audio2exp model
            mkdir -p ./models/LAM_audio2exp/
            wget https://huggingface.co/3DAIGC/LAM_audio2exp/resolve/main/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/ || {
                warn "Failed to download from HuggingFace, trying alternative source..."
                wget https://virutalbuy-public.oss-cn-hangzhou.aliyuncs.com/share/aigc3d/data/LAM/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/
            }
            tar -xzvf ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar -C ./models/LAM_audio2exp && rm ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar
            ;;
        6)
            log "Downloading MuseTalk models..."
            bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk weights"
            ;;
        7)
            log "Downloading all models (this will take a very long time)..."
            bash scripts/download_liteavatar_weights.sh || warn "Failed to download LiteAvatar weights"
            bash scripts/download_MiniCPM-o_2.6.sh || warn "Failed to download MiniCPM-o-2.6"
            bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk weights"
            
            # WAV2VEC2 model
            if [ ! -d "./models/wav2vec2-base-960h" ]; then
                git clone --depth 1 https://huggingface.co/facebook/wav2vec2-base-960h ./models/wav2vec2-base-960h || warn "Failed to download wav2vec2 model"
            fi
            # LAM audio2exp model
            mkdir -p ./models/LAM_audio2exp/
            wget https://huggingface.co/3DAIGC/LAM_audio2exp/resolve/main/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/ || {
                warn "Failed to download from HuggingFace, trying alternative source..."
                wget https://virutalbuy-public.oss-cn-hangzhou.aliyuncs.com/share/aigc3d/data/LAM/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/
            }
            tar -xzvf ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar -C ./models/LAM_audio2exp && rm ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar
            ;;
        *)
            warn "Invalid option. Skipping model downloads."
            ;;
    esac
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    if [ ! -f "ssl_certs/localhost.crt" ] || [ ! -f "ssl_certs/localhost.key" ]; then
        log "Creating self-signed SSL certificates..."
        bash scripts/create_ssl_certs.sh
    else
        log "SSL certificates already exist"
    fi
}

# Post-installation configuration
post_install_config() {
    log "Running post-installation configuration..."
    
    # Run post-config script for a default configuration
    if [ -f "scripts/post_config_install.sh" ]; then
        bash scripts/post_config_install.sh --config config/chat_with_openai_compatible_edge_tts.yaml
    fi
}

# Create environment file template
create_env_template() {
    log "Creating .env template file..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# OpenAvatarChat Environment Variables
# Copy this file and add your API keys

# Bailian/DashScope API Key (for Alibaba Cloud services)
# Get your key from: https://bailian.console.aliyun.com/
DASHSCOPE_API_KEY=your_bailian_api_key_here

# OpenAI API Key (if using OpenAI services)
OPENAI_API_KEY=your_openai_api_key_here

# Other API keys can be added here as needed
EOF
        info "Created .env template file. Please edit it with your API keys."
    else
        log ".env file already exists"
    fi
}

# Main installation function
main() {
    log "Starting OpenAvatarChat installation..."
    
    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    
    # Verify we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "src" ]; then
        error "Please run this script from the OpenAvatarChat root directory"
    fi
    
    check_root
    check_system
    install_system_deps
    install_uv
    update_submodules
    install_python_deps
    setup_ssl
    create_env_template
    download_models
    post_install_config
    
    log "Installation completed successfully!"
    echo ""
    info "Next steps:"
    echo "1. Edit the .env file with your API keys (if using API services)"
    echo "2. Choose a configuration from the config/ directory"
    echo "3. Run the application with:"
    echo "   uv run src/demo.py --config config/chat_with_openai_compatible_edge_tts.yaml"
    echo ""
    info "Available configurations:"
    echo "- config/chat_with_openai_compatible_edge_tts.yaml (recommended for beginners)"
    echo "- config/chat_with_openai_compatible_bailian_cosyvoice.yaml"
    echo "- config/chat_with_minicpm.yaml (requires local MiniCPM model)"
    echo "- config/chat_with_gs.yaml (requires LAM models)"
    echo ""
    info "For more information, see the README.md file"
}

# Run main function
main "$@"
