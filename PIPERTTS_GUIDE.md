# PiperTTS Integration Guide

## Overview
PiperTTS has been integrated as a local, high-quality text-to-speech solution to replace EdgeTTS. PiperTTS provides:

- **Local processing** - No internet connection required
- **High quality** - Neural voices with natural sound
- **Fast synthesis** - Optimized for real-time applications
- **Polish language support** - Native Polish models available
- **Customizable** - Adjustable speed, voice variation, and speaker selection

## Quick Setup

1. **Run the setup script:**
   ```bash
   ./scripts/setup_pipertts.sh
   ```

2. **Launch with PiperTTS:**
   ```bash
   ./launch_max_speed_gpu.sh
   ```

## Manual Installation

If the automatic setup doesn't work:

### 1. Install PiperTTS Binary

```bash
# Download latest release
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_amd64.tar.gz
tar -xzf piper_linux_amd64.tar.gz
sudo mv piper/piper /usr/local/bin/
```

### 2. Download Polish Models

```bash
mkdir -p models/piper
cd models/piper

# Main model (medium quality, native Polish speaker - RECOMMENDED)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx.json
```

## Configuration Options

The PiperTTS handler supports these parameters in your YAML config:

```yaml
PiperTTS:
  enabled: True
  module: tts/pipertts/tts_handler_pipertts
  model_path: "models/piper/pl_PL-gosia-medium.onnx"
  config_path: "models/piper/pl_PL-gosia-medium.onnx.json"
  sample_rate: 22050
  speaker_id: null              # For multi-speaker models (0, 1, 2, etc.)
  length_scale: 1.0            # Speed: 0.8=faster, 1.0=normal, 1.2=slower
  noise_scale: 0.667           # Voice variation: 0.1=robotic, 0.9=natural
  noise_w: 0.8                 # Phoneme variation: 0.1=clear, 0.9=varied
```

## Available Polish Models

| Model | Quality | Speed | Size | Description |
|-------|---------|-------|------|-------------|
| `pl_PL-gosia-medium` | High | Balanced | ~60MB | **Recommended** - Native Polish speaker |
| `pl_PL-mls_6892-low` | Low | Fast | ~60MB | Synthetic dataset, less natural |
| `pl_PL-mls_6892-medium` | Medium | Balanced | ~60MB | Synthetic dataset |

## Troubleshooting

### Model Not Found Error
- Ensure models are in `models/piper/` directory
- Check file paths in configuration match actual files
- Run setup script again if files are missing

### Piper Executable Not Found
- Install piper binary: `sudo apt install piper-tts` (if available)
- Or download manually from GitHub releases
- Ensure piper is in PATH or use absolute path

### Audio Quality Issues
- Increase `noise_scale` for more natural voice (try 0.8-0.9)
- Adjust `length_scale` for comfortable speed
- Try different models (medium vs high quality)

### Performance Optimization
- Use `low` quality model for fastest synthesis
- Reduce `noise_scale` slightly for faster processing
- Ensure adequate CPU resources

## Testing

Test PiperTTS installation:

```bash
# Test basic synthesis with native Polish model
echo "Witaj świecie, jestem Gosia" | piper --model models/piper/pl_PL-gosia-medium.onnx --config models/piper/pl_PL-gosia-medium.onnx.json --output_file test.wav

# Play test audio
aplay test.wav  # or use your preferred audio player
```

## Migration from EdgeTTS

The configuration has been automatically updated to use PiperTTS instead of EdgeTTS. Key differences:

- **EdgeTTS**: Required internet connection, Microsoft voices
- **PiperTTS**: Local processing, open-source neural voices
- **Quality**: PiperTTS provides comparable or better quality
- **Latency**: PiperTTS is typically faster due to local processing
- **Privacy**: All processing happens locally

## Voice Customization

For different voice characteristics:

1. **Faster speech**: Set `length_scale: 0.8`
2. **Slower speech**: Set `length_scale: 1.2`
3. **More robotic**: Set `noise_scale: 0.3`
4. **More natural**: Set `noise_scale: 0.9`
5. **Clearer pronunciation**: Set `noise_w: 0.3`
6. **More varied intonation**: Set `noise_w: 0.9`
