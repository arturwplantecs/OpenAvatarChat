#!/bin/bash

# OpenAvatarChat Quick Install Script for Specific Configurations
# This script installs dependencies for a specific configuration only

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; exit 1; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }

# Default configuration
CONFIG_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --config <config_file>"
            echo "Example: $0 --config config/chat_with_openai_compatible_edge_tts.yaml"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Check if config file is provided
if [ -z "$CONFIG_FILE" ]; then
    log "No config file specified. Available configurations:"
    echo "1. chat_with_openai_compatible_edge_tts.yaml (Lightest, no API key needed for TTS)"
    echo "2. chat_with_openai_compatible_bailian_cosyvoice.yaml (API-based, lightweight)"
    echo "3. chat_with_openai_compatible.yaml (Local CosyVoice TTS)"
    echo "4. chat_with_minicpm.yaml (Local MiniCPM model, high VRAM requirement)"
    echo "5. chat_with_gs.yaml (LAM with API services)"
    echo "6. chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml (MuseTalk avatar)"
    echo ""
    read -p "Choose option (1-6): " choice
    
    case $choice in
        1) CONFIG_FILE="config/chat_with_openai_compatible_edge_tts.yaml" ;;
        2) CONFIG_FILE="config/chat_with_openai_compatible_bailian_cosyvoice.yaml" ;;
        3) CONFIG_FILE="config/chat_with_openai_compatible.yaml" ;;
        4) CONFIG_FILE="config/chat_with_minicpm.yaml" ;;
        5) CONFIG_FILE="config/chat_with_gs.yaml" ;;
        6) CONFIG_FILE="config/chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml" ;;
        *) error "Invalid choice" ;;
    esac
fi

# Convert to absolute path
CONFIG_FILE="$(realpath "$CONFIG_FILE")"

if [ ! -f "$CONFIG_FILE" ]; then
    error "Config file not found: $CONFIG_FILE"
fi

log "Installing dependencies for configuration: $CONFIG_FILE"

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    sudo apt update
    sudo apt install -y git-lfs curl wget build-essential bc
    git lfs install
}

# Install UV if not present
install_uv() {
    if ! command -v uv &> /dev/null; then
        log "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
}

# Update submodules
update_submodules() {
    log "Updating git submodules..."
    git submodule update --init --recursive
}

# Install Python dependencies for specific config
install_config_deps() {
    log "Creating virtual environment..."
    uv venv --python 3.11.11
    
    log "Installing basic packages..."
    uv pip install setuptools pip
    
    log "Installing dependencies for specified configuration..."
    uv run install.py --uv --config "$CONFIG_FILE"
    
    log "Running post-installation script..."
    if [ -f "scripts/post_config_install.sh" ]; then
        bash scripts/post_config_install.sh --config "$CONFIG_FILE"
    fi
}

# Download required models based on config
download_models_for_config() {
    CONFIG_NAME=$(basename "$CONFIG_FILE")
    
    log "Model download options for $CONFIG_NAME:"
    echo "1. Download only required models for this config (default, recommended)"
    echo "2. Skip model downloads (install manually later)"
    echo "3. Download additional models (for development/testing)"
    echo ""
    read -p "Choose option [1-3] (default: 1): " download_choice
    download_choice=${download_choice:-1}
    
    case $download_choice in
        2)
            warn "Skipping model downloads. You'll need to download them manually later."
            return
            ;;
        3)
            log "Will download additional models after required ones..."
            ;;
    esac
    
    # Download models based on configuration
    case "$CONFIG_NAME" in
        *"minicpm"*)
            log "Downloading models for MiniCPM configuration..."
            if [ "$download_choice" = "1" ]; then
                log "Downloading MiniCPM-o-2.6-int4 model (faster, recommended)..."
                bash scripts/download_MiniCPM-o_2.6-int4.sh || warn "Failed to download MiniCPM model"
            else
                read -p "Download full model (40GB+) or int4 quantized model (20GB+)? [full/int4] (default: int4): " model_type
                model_type=${model_type:-int4}
                if [ "$model_type" = "int4" ]; then
                    bash scripts/download_MiniCPM-o_2.6-int4.sh || warn "Failed to download MiniCPM int4 model"
                else
                    bash scripts/download_MiniCPM-o_2.6.sh || warn "Failed to download MiniCPM full model"
                fi
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
    
    # Download additional models if requested
    if [ "$download_choice" = "3" ]; then
        log "Downloading additional models..."
        echo "Available additional models:"
        echo "a. LiteAvatar weights (if not already downloaded)"
        echo "b. LAM models"
        echo "c. MuseTalk models"
        echo "d. All models"
        echo "e. Skip additional downloads"
        read -p "Choose additional models [a-e]: " additional_choice
        
        case $additional_choice in
            a) download_liteavatar_weights ;;
            b) download_lam_models ;;
            c) bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk models" ;;
            d) 
                download_liteavatar_weights
                download_lam_models
                bash scripts/download_musetalk_weights.sh || warn "Failed to download MuseTalk models"
                ;;
            *) log "Skipping additional model downloads" ;;
        esac
    fi
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

# Create SSL certificates
setup_ssl() {
    if [ ! -f "ssl_certs/localhost.crt" ]; then
        log "Creating SSL certificates..."
        bash scripts/create_ssl_certs.sh
    fi
}

# Create .env file
create_env() {
    if [ ! -f ".env" ]; then
        log "Creating .env template..."
        cat > .env << EOF
# API Keys for OpenAvatarChat
DASHSCOPE_API_KEY=your_bailian_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
EOF
        info "Created .env file. Please edit it with your API keys."
    fi
}

# Main execution
main() {
    log "Quick installation for OpenAvatarChat"
    
    # Verify we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "src" ]; then
        error "Please run this script from the OpenAvatarChat root directory"
    fi
    
    install_system_deps
    install_uv
    update_submodules
    install_config_deps
    setup_ssl
    create_env
    download_models_for_config
    
    log "Installation completed!"
    echo ""
    info "To run OpenAvatarChat:"
    echo "uv run src/demo.py --config \"$CONFIG_FILE\""
    echo ""
    info "Don't forget to edit the .env file with your API keys if using API services!"
}

main "$@"
