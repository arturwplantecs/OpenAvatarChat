# OpenAvatarChat Windows Installation Script
# This script automates the installation process for Windows users

param(
    [string]$Config = "",
    [switch]$Help
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

function Write-Log {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Error-Log {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

function Write-Warning-Log {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Info-Log {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

if ($Help) {
    Write-Host "OpenAvatarChat Windows Installation Script"
    Write-Host "Usage: .\install_windows.ps1 [-Config <config_file>]"
    Write-Host "Example: .\install_windows.ps1 -Config config\chat_with_openai_compatible_edge_tts.yaml"
    exit 0
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check system requirements
function Test-SystemRequirements {
    Write-Log "Checking system requirements..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            $version = "$major.$minor"
            
            if ($major -eq 3 -and $minor -ge 10 -and $minor -lt 12) {
                Write-Log "Python version $version is compatible"
            } else {
                Write-Error-Log "Python version must be >= 3.10 and < 3.12. Current version: $version"
            }
        }
    } catch {
        Write-Error-Log "Python 3 is required but not found. Please install Python 3.10 or 3.11."
    }
    
    # Check Git
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error-Log "Git is required but not found. Please install Git for Windows."
    }
    
    # Check for NVIDIA GPU
    try {
        $nvidiaSmi = nvidia-smi 2>&1
        if ($nvidiaSmi -match "CUDA Version: ([\d.]+)") {
            $cudaVersion = $matches[1]
            Write-Log "NVIDIA GPU detected with CUDA version: $cudaVersion"
            if ([version]$cudaVersion -lt [version]"12.4") {
                Write-Warning-Log "CUDA version $cudaVersion detected. Version >= 12.4 is recommended."
            }
        }
    } catch {
        Write-Warning-Log "NVIDIA GPU not detected. Some features may require GPU acceleration."
    }
}

# Install Chocolatey if not present
function Install-Chocolatey {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Log "Installing Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    } else {
        Write-Log "Chocolatey already installed"
    }
}

# Install Git LFS
function Install-GitLFS {
    Write-Log "Installing Git LFS..."
    if (-not (Get-Command git-lfs -ErrorAction SilentlyContinue)) {
        choco install git-lfs -y
        git lfs install
    } else {
        Write-Log "Git LFS already installed"
    }
}

# Install UV
function Install-UV {
    Write-Log "Installing UV package manager..."
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        # Install UV using PowerShell
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        # Refresh environment variables
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Log "UV already installed"
    }
}

# Update git submodules
function Update-Submodules {
    Write-Log "Updating git submodules..."
    git submodule update --init --recursive
}

# Install Python dependencies
function Install-PythonDependencies {
    param([string]$ConfigFile = "")
    
    Write-Log "Creating virtual environment..."
    uv venv --python 3.11.11
    
    Write-Log "Installing basic packages..."
    uv pip install setuptools pip
    
    if ($ConfigFile -ne "") {
        Write-Log "Installing dependencies for specific configuration..."
        uv run install.py --uv --config $ConfigFile
        
        # Run post-config script if exists
        if (Test-Path "scripts\post_config_install.sh") {
            Write-Log "Running post-installation script..."
            bash scripts/post_config_install.sh --config $ConfigFile
        }
    } else {
        Write-Log "Installing all dependencies..."
        uv sync --all-packages
    }
}

# Download models based on configuration
function Install-ModelsForConfig {
    param([string]$ConfigFile)
    
    $ConfigName = Split-Path $ConfigFile -Leaf
    
    Write-Log "Model download options for $ConfigName"
    Write-Host "1. Download only required models for this config (default, recommended)"
    Write-Host "2. Skip model downloads (install manually later)" 
    Write-Host "3. Download additional models (for development/testing)"
    Write-Host ""
    $downloadChoice = Read-Host "Choose option [1-3] (default: 1)"
    if ([string]::IsNullOrEmpty($downloadChoice)) { $downloadChoice = "1" }
    
    switch ($downloadChoice) {
        "2" {
            Write-Warning-Log "Skipping model downloads. You'll need to download them manually later."
            return
        }
        "3" {
            Write-Log "Will download additional models after required ones..."
        }
    }
    
    # Download models based on configuration
    switch -Wildcard ($ConfigName) {
        "*minicpm*" {
            Write-Log "Downloading models for MiniCPM configuration..."
            if ($downloadChoice -eq "1") {
                Write-Log "Downloading MiniCPM-o-2.6-int4 model (faster, recommended)..."
                if (Test-Path "scripts\download_MiniCPM-o_2.6-int4.sh") {
                    bash scripts/download_MiniCPM-o_2.6-int4.sh
                }
            } else {
                $modelType = Read-Host "Download full model (40GB+) or int4 quantized model (20GB+)? [full/int4] (default: int4)"
                if ([string]::IsNullOrEmpty($modelType)) { $modelType = "int4" }
                
                if ($modelType -eq "int4") {
                    if (Test-Path "scripts\download_MiniCPM-o_2.6-int4.sh") {
                        bash scripts/download_MiniCPM-o_2.6-int4.sh
                    }
                } else {
                    if (Test-Path "scripts\download_MiniCPM-o_2.6.sh") {
                        bash scripts/download_MiniCPM-o_2.6.sh
                    }
                }
            }
            Install-LiteAvatarWeights
            break
        }
        "*musetalk*" {
            Write-Log "Downloading MuseTalk models..."
            if (Test-Path "scripts\download_musetalk_weights.sh") {
                bash scripts/download_musetalk_weights.sh
            }
            break
        }
        "*gs*" {
            Write-Log "Downloading LAM models..."
            Install-LAMModels
            break
        }
        "*lam*" {
            Write-Log "Downloading LAM models..."
            Install-LAMModels
            break
        }
        default {
            Write-Log "Downloading LiteAvatar weights (required for most configurations)..."
            Install-LiteAvatarWeights
            break
        }
    }
    
    # Download additional models if requested
    if ($downloadChoice -eq "3") {
        Write-Log "Downloading additional models..."
        Write-Host "Available additional models:"
        Write-Host "a. LiteAvatar weights (if not already downloaded)"
        Write-Host "b. LAM models"
        Write-Host "c. MuseTalk models"
        Write-Host "d. All models"
        Write-Host "e. Skip additional downloads"
        $additionalChoice = Read-Host "Choose additional models [a-e]"
        
        switch ($additionalChoice) {
            "a" { Install-LiteAvatarWeights }
            "b" { Install-LAMModels }
            "c" { 
                if (Test-Path "scripts\download_musetalk_weights.sh") {
                    bash scripts/download_musetalk_weights.sh
                }
            }
            "d" {
                Install-LiteAvatarWeights
                Install-LAMModels
                if (Test-Path "scripts\download_musetalk_weights.sh") {
                    bash scripts/download_musetalk_weights.sh
                }
            }
            default { Write-Log "Skipping additional model downloads" }
        }
    }
}

# Download LiteAvatar weights with error handling
function Install-LiteAvatarWeights {
    if (Test-Path "src\handlers\avatar\liteavatar\algo\liteavatar\weights\model_1.onnx") {
        Write-Log "LiteAvatar weights already exist"
        return
    }
    
    Write-Log "Downloading LiteAvatar weights..."
    if (Test-Path "scripts\download_liteavatar_weights.sh") {
        try {
            bash scripts/download_liteavatar_weights.sh
        } catch {
            Write-Warning-Log "Failed to download LiteAvatar weights using script. Trying alternative method..."
            # Alternative download using Python ModelScope API
            Push-Location "src\handlers\avatar\liteavatar\algo\liteavatar"
            try {
                uv run python -c @"
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
        print('Copied lm.pb successfully')
    
    if os.path.exists(src_model1):
        shutil.copy2(src_model1, dst_model1)
        print('Copied model_1.onnx successfully')
        
    if os.path.exists(src_model):
        shutil.copy2(src_model, dst_model)
        print('Copied model.pb successfully')
    
    print('LiteAvatar model files downloaded successfully!')
except Exception as e:
    print(f'Error downloading models: {e}')
    exit(1)
"@
            } catch {
                Write-Warning-Log "Failed to download LiteAvatar weights"
            } finally {
                Pop-Location
            }
        }
    }
}

# Download LAM models
function Install-LAMModels {
    Write-Log "Downloading LAM models..."
    
    # WAV2VEC2 model
    if (-not (Test-Path "models\wav2vec2-base-960h")) {
        Write-Log "Downloading wav2vec2-base-960h model..."
        try {
            git clone --depth 1 https://huggingface.co/facebook/wav2vec2-base-960h ./models/wav2vec2-base-960h
        } catch {
            Write-Warning-Log "Failed to download from HuggingFace, trying ModelScope..."
            git clone --depth 1 https://www.modelscope.cn/AI-ModelScope/wav2vec2-base-960h.git ./models/wav2vec2-base-960h
        }
    } else {
        Write-Log "wav2vec2-base-960h model already exists"
    }
    
    # LAM audio2exp model
    if (-not (Test-Path "models\LAM_audio2exp\pretrained_models")) {
        Write-Log "Downloading LAM audio2exp model..."
        New-Item -ItemType Directory -Force -Path "models\LAM_audio2exp"
        
        try {
            # Try HuggingFace first
            if (Get-Command wget -ErrorAction SilentlyContinue) {
                wget https://huggingface.co/3DAIGC/LAM_audio2exp/resolve/main/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/
            } else {
                Invoke-WebRequest -Uri "https://huggingface.co/3DAIGC/LAM_audio2exp/resolve/main/LAM_audio2exp_streaming.tar" -OutFile "models\LAM_audio2exp\LAM_audio2exp_streaming.tar"
            }
        } catch {
            Write-Warning-Log "Failed to download from HuggingFace, trying alternative source..."
            try {
                if (Get-Command wget -ErrorAction SilentlyContinue) {
                    wget https://virutalbuy-public.oss-cn-hangzhou.aliyuncs.com/share/aigc3d/data/LAM/LAM_audio2exp_streaming.tar -P ./models/LAM_audio2exp/
                } else {
                    Invoke-WebRequest -Uri "https://virutalbuy-public.oss-cn-hangzhou.aliyuncs.com/share/aigc3d/data/LAM/LAM_audio2exp_streaming.tar" -OutFile "models\LAM_audio2exp\LAM_audio2exp_streaming.tar"
                }
            } catch {
                Write-Warning-Log "Failed to download LAM audio2exp model"
                return
            }
        }
        
        # Extract the tar file
        if (Test-Path "models\LAM_audio2exp\LAM_audio2exp_streaming.tar") {
            tar -xzvf ./models/LAM_audio2exp/LAM_audio2exp_streaming.tar -C ./models/LAM_audio2exp
            Remove-Item "models\LAM_audio2exp\LAM_audio2exp_streaming.tar"
        }
    } else {
        Write-Log "LAM audio2exp model already exists"
    }
}

# Create SSL certificates
function New-SSLCertificates {
    if (-not (Test-Path "ssl_certs\localhost.crt")) {
        Write-Log "Creating SSL certificates..."
        if (Test-Path "scripts\create_ssl_certs.sh") {
            bash scripts/create_ssl_certs.sh
        }
    } else {
        Write-Log "SSL certificates already exist"
    }
}

# Create environment file
function New-EnvironmentFile {
    if (-not (Test-Path ".env")) {
        Write-Log "Creating .env template..."
        @"
# OpenAvatarChat Environment Variables
# Add your API keys here

# Bailian/DashScope API Key
DASHSCOPE_API_KEY=your_bailian_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Info-Log "Created .env template file. Please edit it with your API keys."
    } else {
        Write-Log ".env file already exists"
    }
}

# Main installation function
function Start-Installation {
    Write-Log "Starting OpenAvatarChat installation for Windows..."
    
    # Verify we're in the right directory
    if (-not (Test-Path "README.md") -or -not (Test-Path "src")) {
        Write-Error-Log "Please run this script from the OpenAvatarChat root directory"
    }
    
    Test-SystemRequirements
    Install-Chocolatey
    Install-GitLFS
    Install-UV
    Update-Submodules
    
    # Handle configuration selection
    if ($Config -eq "") {
        Write-Log "Available configurations:"
        Write-Host "1. chat_with_openai_compatible_edge_tts.yaml (Recommended for beginners)"
        Write-Host "2. chat_with_openai_compatible_bailian_cosyvoice.yaml"
        Write-Host "3. chat_with_openai_compatible.yaml (Requires Conda for CosyVoice)"
        Write-Host "4. Skip configuration-specific install (install all dependencies)"
        
        $choice = Read-Host "Choose option (1-4)"
        switch ($choice) {
            "1" { $Config = "config\chat_with_openai_compatible_edge_tts.yaml" }
            "2" { $Config = "config\chat_with_openai_compatible_bailian_cosyvoice.yaml" }
            "3" { 
                $Config = "config\chat_with_openai_compatible.yaml"
                Install-CosyVoiceWindows
            }
            "4" { $Config = "" }
            default { 
                Write-Warning-Log "Invalid choice. Installing all dependencies."
                $Config = ""
            }
        }
    }
    
    Install-PythonDependencies -ConfigFile $Config
    New-SSLCertificates
    New-EnvironmentFile
    
    # Download models for the selected configuration
    if ($Config -ne "") {
        Install-ModelsForConfig -ConfigFile $Config
    }
    
    Write-Log "Installation completed successfully!" -Color Green
    Write-Host ""
    Write-Info-Log "Next steps:"
    Write-Host "1. Edit the .env file with your API keys"
    if ($Config -ne "") {
        Write-Host "2. Run: uv run src\demo.py --config `"$Config`""
    } else {
        Write-Host "2. Choose a configuration and run: uv run src\demo.py --config <config_file>"
    }
    Write-Host ""
    Write-Info-Log "For more information, see the README.md file"
}

# Execute main function
Start-Installation
