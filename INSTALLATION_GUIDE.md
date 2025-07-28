# OpenAvatarChat Installation Scripts

This directory contains automated installation scripts to help you set up OpenAvatarChat quickly and easily.

## Available Scripts

### 1. `install_all.sh` - Complete Installation (Linux/macOS)
**Recommended for first-time users**

This script performs a complete installation of OpenAvatarChat with all components and models.

```bash
# Make executable and run
chmod +x install_all.sh
./install_all.sh
```

**What it does:**
- Checks system requirements (Python, CUDA, etc.)
- Installs system dependencies (git-lfs, etc.)
- Installs UV package manager
- Updates git submodules
- Creates virtual environment and installs all Python dependencies
- Downloads models (with user choice)
- Sets up SSL certificates
- Creates environment file template
- Runs post-installation configuration

**Features:**
- Interactive model download selection
- System requirement validation
- Comprehensive error checking
- Colored output for better readability

### 2. `quick_install.sh` - Configuration-Specific Installation (Linux/macOS)
**Recommended for users who know which configuration they want**

This script installs only the dependencies needed for a specific configuration.

```bash
# Interactive mode
./quick_install.sh

# Or specify config directly
./quick_install.sh --config config/chat_with_openai_compatible_edge_tts.yaml
```

**Benefits:**
- Faster installation
- Uses less disk space
- Downloads only required models
- Perfect for specific use cases

### 3. `install_windows.ps1` - Windows Installation
**For Windows users**

PowerShell script that handles Windows-specific installation requirements.

```powershell
# Run in PowerShell as Administrator
.\install_windows.ps1

# Or with specific config
.\install_windows.ps1 -Config config\chat_with_openai_compatible_edge_tts.yaml
```

**Windows-specific features:**
- Installs Chocolatey package manager
- Handles Git LFS installation
- Special handling for CosyVoice on Windows
- Creates proper Windows paths

## Configuration Options

The scripts support all available OpenAvatarChat configurations:

| Configuration | Description | Requirements | Best For |
|--------------|-------------|--------------|----------|
| `chat_with_openai_compatible_edge_tts.yaml` | API LLM + Edge TTS | Low | Beginners, testing |
| `chat_with_openai_compatible_bailian_cosyvoice.yaml` | API LLM + API TTS | Low | Production, API users |
| `chat_with_openai_compatible.yaml` | API LLM + Local CosyVoice | Medium | Local TTS needs |
| `chat_with_minicpm.yaml` | Local MiniCPM model | High (20GB+ VRAM) | Full local setup |
| `chat_with_gs.yaml` | LAM with API services | Medium | 3D avatars |
| `chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml` | API services + MuseTalk | Medium | 2D lip-sync avatars |

## Quick Start Guide

### For Beginners (Easiest Setup)
```bash
# 1. Clone the repository
git clone https://github.com/HumanAIGC-Engineering/OpenAvatarChat.git
cd OpenAvatarChat

# 2. Run the quick installer
./quick_install.sh

# 3. Choose option 1 (Edge TTS configuration)

# 4. Edit .env file with your API keys
nano .env

# 5. Run the application
uv run src/demo.py --config config/chat_with_openai_compatible_edge_tts.yaml
```

### For Advanced Users (Full Setup)
```bash
# 1. Clone and enter directory
git clone https://github.com/HumanAIGC-Engineering/OpenAvatarChat.git
cd OpenAvatarChat

# 2. Run complete installation
./install_all.sh

# 3. Choose models to download when prompted

# 4. Configure API keys in .env file

# 5. Run with your preferred configuration
uv run src/demo.py --config <your_chosen_config>
```

## Environment Variables

After installation, edit the `.env` file with your API keys:

```bash
# Required for most configurations
DASHSCOPE_API_KEY=your_bailian_api_key_here

# Optional, for OpenAI-based services
OPENAI_API_KEY=your_openai_api_key_here
```

**Getting API Keys:**
- **Bailian/DashScope**: Register at [Bailian Console](https://bailian.console.aliyun.com/)
- **OpenAI**: Get from [OpenAI Platform](https://platform.openai.com/)

## Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
chmod +x install_all.sh quick_install.sh
```

**2. Python Version Issues**
Ensure you have Python 3.10 or 3.11 installed:
```bash
python3 --version
```

**3. CUDA Issues**
Check NVIDIA driver and CUDA version:
```bash
nvidia-smi
```

**4. Git LFS Issues**
Manually install git-lfs:
```bash
sudo apt install git-lfs
git lfs install
```

**5. UV Installation Issues**
Manually install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Windows-Specific Issues

**1. PowerShell Execution Policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**2. CosyVoice on Windows**
Follow the Conda setup instructions printed by the script.

## Manual Installation

If the scripts don't work for your system, follow the manual installation steps in the main README.md:

1. Install system dependencies
2. Install UV package manager
3. Update git submodules
4. Create virtual environment
5. Install Python dependencies
6. Download required models
7. Configure environment variables

## Support

- Check the main [README.md](../README.md) for detailed information
- Visit the [FAQ](../docs/FAQ.md) for common questions
- Open an issue on GitHub if you encounter problems
- Join the WeChat community group (QR code in main README)

## Script Customization

You can modify these scripts for your specific needs:

- Change default Python version in the `uv venv` command
- Add custom model download sources
- Modify system dependency installation
- Add custom post-installation steps

The scripts are designed to be readable and modifiable.
