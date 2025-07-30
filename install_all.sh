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
    echo "1. Download only essential models (LiteAvatar - recommended for most users)"
    echo "2. Skip model downloads (install manually later)"
    echo "3. Download MiniCPM-o-2.6 model (requires ~40GB+ space)"
    echo "4. Download MiniCPM-o-2.6-int4 model (requires ~20GB+ space)"
    echo "5. Download LAM models"
    echo "6. Download MuseTalk models"
    echo "7. Download all models (requires significant disk space)"
    echo ""
    read -p "Choose option [1-7] (default: 1): " model_choice
    model_choice=${model_choice:-1}
    
    case $model_choice in
        1)
            log "Downloading essential LiteAvatar weights..."
            download_liteavatar_weights
            ;;
        2)
            warn "Skipping model downloads. You'll need to download them manually later."
            ;;
        3)
            log "Downloading MiniCPM-o-2.6 model..."
            bash scripts/download_MiniCPM-o_2.6.sh || warn "Failed to download MiniCPM-o-2.6"
            download_liteavatar_weights
            ;;
        4)
            log "Downloading MiniCPM-o-2.6-int4 model..."
            bash scripts/download_MiniCPM-o_2.6-int4.sh || warn "Failed to download MiniCPM-o-2.6-int4"
            download_liteavatar_weights
            ;;
        5)
            log "Downloading LAM models..."
            download_lam_models
            ;;
        6)
            log "Downloading MuseTalk models..."
            bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk weights"
            ;;
        7)
            log "Downloading all models (this will take a very long time)..."
            download_liteavatar_weights
            bash scripts/download_MiniCPM-o_2.6-int4.sh || warn "Failed to download MiniCPM-o-2.6-int4"
            bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk weights"
            download_lam_models
            ;;
        *)
            warn "Invalid option. Downloading essential models by default."
            download_liteavatar_weights
            ;;
    esac
}

# Download LiteAvatar weights with error handling
download_liteavatar_weights() {
    if [ -f "src/handlers/avatar/liteavatar/algo/liteavatar/weights/model_1.onnx" ]; then
        log "LiteAvatar weights already exist"
        return
    fi
    
    log "Downloading LiteAvatar weights..."
    bash scripts/download_liteavatar_weights.sh || {
        warn "Failed to download LiteAvatar weights using script. Trying alternative method..."
        # Alternative download using Python ModelScope API
        cd src/handlers/avatar/liteavatar/algo/liteavatar
        uv run python -c "
from modelscope import snapshot_download
import os
import shutil

try:
    os.makedirs('weights/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/lm', exist_ok=True)
    os.makedirs('weights', exist_ok=True)
    
    print('Downloading LiteAvatar model files...')
    local_dir = snapshot_download('HumanAIGC-Engineering/LiteAvatarGallery', cache_dir='./cache')
    
    src_lm = os.path.join(local_dir, 'lite_avatar_weights/lm.pb')
    src_model1 = os.path.join(local_dir, 'lite_avatar_weights/model_1.onnx')
    src_model = os.path.join(local_dir, 'lite_avatar_weights/model.pb')
    
    dst_lm = 'weights/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/lm/lm.pb'
    dst_model1 = 'weights/model_1.onnx'
    dst_model = 'weights/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/model.pb'
    
    if os.path.exists(src_lm):
        shutil.copy2(src_lm, dst_lm)
        print(f'Copied lm.pb successfully')
    
    if os.path.exists(src_model1):
        shutil.copy2(src_model1, dst_model1)
        print(f'Copied model_1.onnx successfully')
        
    if os.path.exists(src_model):
        shutil.copy2(src_model, dst_model)
        print(f'Copied model.pb successfully')
    
    print('LiteAvatar model files downloaded successfully!')
except Exception as e:
    print(f'Error downloading models: {e}')
    exit(1)
" || warn "Failed to download LiteAvatar weights"
        cd - > /dev/null
    }
}

# Download LAM models
download_lam_models() {
    log "Downloading LAM models..."
    
    # WAV2VEC2 model
    if [ ! -d "./models/wav2vec2-base-960h" ]; then
        log "Downloading wav2vec2-base-960h model..."
        git clone --depth 1 https://huggingface.co/facebook/wav2vec2-base-960h ./models/wav2vec2-base-960h || {
            warn "Failed to download from HuggingFace, trying ModelScope..."
            git clone --depth 1 https://www.modelscope.cn/AI-ModelScope/wav2vec2-base-960h.git ./models/wav2vec2-base-960h
        }
    else
        log "wav2vec2-base-960h model already exists"
    fi
    
    # LAM audio2exp model
    if [ ! -d "./models/LAM_audio2exp/pretrained_models" ]; then
        log "Downloading LAM audio2exp model..."
        mkdir -p ./models/LAM_audio2exp/
        wget https://huggingface.co/3DAIGC/LAM_audio2exp/resolve/main/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/ || {
            warn "Failed to download from HuggingFace, trying alternative source..."
            wget https://virutalbuy-public.oss-cn-hangzhou.aliyuncs.com/share/aigc3d/data/LAM/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/
        }
        tar -xzvf ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar -C ./models/LAM_audio2exp && rm ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar
    else
        log "LAM audio2exp model already exists"
    fi
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

# Ask user for configuration-specific installation
ask_for_config_install() {
    log "Installation mode options:"
    echo "1. Complete installation (all dependencies and essential models)"
    echo "2. Configuration-specific installation (faster, only what you need)"
    echo ""
    read -p "Choose installation mode [1-2] (default: 1): " install_mode
    install_mode=${install_mode:-1}
    
    if [ "$install_mode" = "2" ]; then
        log "Available configurations:"
        echo "1. chat_with_openai_compatible_edge_tts.yaml (Lightest, no API key needed for TTS)"
        echo "2. chat_with_openai_compatible_bailian_cosyvoice.yaml (API-based, lightweight)"
        echo "3. chat_with_openai_compatible.yaml (Local CosyVoice TTS)"
        echo "4. chat_with_minicpm.yaml (Local MiniCPM model, high VRAM requirement)"
        echo "5. chat_with_gs.yaml (LAM with API services)"
        echo "6. chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml (MuseTalk avatar)"
        echo ""
        read -p "Choose configuration (1-6): " config_choice
        
        case $config_choice in
            1) CONFIG_FILE="config/chat_with_openai_compatible_edge_tts.yaml" ;;
            2) CONFIG_FILE="config/chat_with_openai_compatible_bailian_cosyvoice.yaml" ;;
            3) CONFIG_FILE="config/chat_with_openai_compatible.yaml" ;;
            4) CONFIG_FILE="config/chat_with_minicpm.yaml" ;;
            5) CONFIG_FILE="config/chat_with_gs.yaml" ;;
            6) CONFIG_FILE="config/chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml" ;;
            *) 
                warn "Invalid choice. Using complete installation mode."
                return
                ;;
        esac
        
        # Convert to absolute path
        CONFIG_FILE="$(realpath "$CONFIG_FILE")"
        
        if [ ! -f "$CONFIG_FILE" ]; then
            error "Config file not found: $CONFIG_FILE"
        fi
        
        log "Installing for configuration: $CONFIG_FILE"
        
        # Install config-specific dependencies
        log "Installing dependencies for specific configuration..."
        uv run install.py --uv --config "$CONFIG_FILE"
        
        # Download models for this configuration
        download_models_for_config "$CONFIG_FILE"
        
        # Run post-config script
        if [ -f "scripts/post_config_install.sh" ]; then
            bash scripts/post_config_install.sh --config "$CONFIG_FILE"
        fi
        
        return 0
    fi
    
    return 1
}

# Download models for specific configuration
download_models_for_config() {
    local config_file="$1"
    local config_name=$(basename "$config_file")
    
    log "Downloading models required for $config_name..."
    
    case "$config_name" in
        *"minicpm"*)
            log "Downloading models for MiniCPM configuration..."
            read -p "Download full model (40GB+) or int4 quantized model (20GB+)? [full/int4] (default: int4): " model_type
            model_type=${model_type:-int4}
            if [ "$model_type" = "int4" ]; then
                bash scripts/download_MiniCPM-o_2.6-int4.sh || warn "Failed to download MiniCPM int4 model"
            else
                bash scripts/download_MiniCPM-o_2.6.sh || warn "Failed to download MiniCPM full model"
            fi
            download_liteavatar_weights
            ;;
        *"musetalk"*)
            log "Downloading MuseTalk models..."
            bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk models"
            ;;
        *"gs"*|*"lam"*)
            log "Downloading LAM models..."
            download_lam_models
            ;;
        *)
            log "Downloading LiteAvatar weights (required for most configurations)..."
            download_liteavatar_weights
            ;;
    esac
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
    
    # Check if user wants config-specific installation
    if ask_for_config_install; then
        # Config-specific installation was completed
        setup_ssl
        create_env_template
        
        log "Configuration-specific installation completed successfully!"
        echo ""
        info "Next steps:"
        echo "1. Edit the .env file with your API keys (if using API services)"
        echo "2. Run the application with:"
        echo "   uv run src/demo.py --config \"$CONFIG_FILE\""
        echo ""
        info "For more information, see the README.md file"
        return
    fi
    
    # Complete installation
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
