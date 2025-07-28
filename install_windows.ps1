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

# Handle CosyVoice special installation for Windows
function Install-CosyVoiceWindows {
    Write-Log "Setting up CosyVoice for Windows..."
    Write-Warning-Log "CosyVoice on Windows requires Conda. Please install Miniconda if you plan to use local CosyVoice."
    Write-Info-Log "To use CosyVoice locally on Windows:"
    Write-Info-Log "1. Install Miniconda"
    Write-Info-Log "2. Run: conda create -n openavatarchat python=3.10"
    Write-Info-Log "3. Run: conda activate openavatarchat"
    Write-Info-Log "4. Run: conda install -c conda-forge pynini==2.1.6"
    Write-Info-Log "5. Set environment variable: `$env:VIRTUAL_ENV=`$env:CONDA_PREFIX"
    Write-Info-Log "6. Use --active flag with uv commands"
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
