# ReSpeaker USB Mic Array v3.1 STT Optimization Guide

## Overview
Your ReSpeaker USB Mic Array v3.1 has been successfully configured for maximum speech-to-text (STT) precision. This guide provides an overview of the optimizations applied and how to use them.

## Optimizations Applied

### 1. Hardware Configuration
- **Device Detection**: ReSpeaker detected as `alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.analog-surround-21`
- **Audio Driver**: Using advanced PipeWire/ALSA configuration
- **USB Interface**: Properly configured for UAC1.0 protocol

### 2. Audio Settings Optimized for STT
- **Sample Rate**: 16kHz (optimal for speech recognition)
- **Bit Depth**: 16-bit signed integer PCM
- **Channels**: Mono (using front microphone for directional pickup)
- **Buffer Size**: 512 samples for low latency
- **Volume Level**: 70% (optimal balance for clarity without clipping)

### 3. Signal Processing Enhancements
- **High-pass Filter**: 80Hz cutoff to remove low-frequency noise
- **Low-pass Filter**: 8kHz cutoff to focus on speech frequencies
- **Dynamic Range Compression**: Applied to normalize volume levels
- **Noise Suppression**: Advanced filtering for clean audio capture
- **Automatic Gain Control**: Prevents clipping while maintaining sensitivity

### 4. OpenAI Whisper Configuration
Enhanced your configuration file with STT-optimized parameters:
- **VAD Threshold**: 0.6 (higher threshold for cleaner speech detection)
- **Energy Threshold**: 300 (optimized for ReSpeaker sensitivity)
- **Dynamic Energy Adjustment**: Enabled for adaptive performance
- **Pause Threshold**: 0.8 seconds (better phrase detection)

## Files Created

### 1. Configuration Scripts
- `configure_respeaker_stt.py` - Initial ReSpeaker optimization
- `advanced_respeaker_stt_tuning.py` - Advanced precision tuning
- `respeaker_stt_autoconfig.sh` - Automatic startup configuration
- `respeaker_stt_monitor.py` - Real-time performance monitoring

### 2. Configuration Files
- `chat_with_openai_compatible_edge_tts_pl_female_stt_optimized.yaml` - Optimized chat configuration
- `~/.asoundrc` - ALSA configuration for optimal recording
- `~/.config/pipewire/respeaker_stt_filter.conf` - PipeWire audio filters

### 3. System Tools
- `/usr/local/bin/respeaker_preprocess_stt` - Audio preprocessing script

## Usage Instructions

### Automatic Configuration (Recommended)
Run the auto-configuration script when you start your system:
```bash
cd /home/arti/Repos/OpenAvatarChat
./respeaker_stt_autoconfig.sh
```

### Real-time Monitoring
Monitor STT performance in real-time:
```bash
cd /home/arti/Repos/OpenAvatarChat
python3 respeaker_stt_monitor.py
```

### Using the Optimized Configuration
Use the STT-optimized configuration file with your OpenAvatarChat:
```bash
# Use the optimized config file
python3 demo.py --config config/chat_with_openai_compatible_edge_tts_pl_female_stt_optimized.yaml
```

### Manual Audio Preprocessing
For maximum quality, preprocess audio files before STT:
```bash
/usr/local/bin/respeaker_preprocess_stt input.wav output.wav
```

## Best Practices for Maximum STT Precision

### 1. Physical Setup
- **Distance**: Position ReSpeaker 30-60cm from speaker
- **Orientation**: Face the front (main) microphone toward the speaker
- **Environment**: Minimize background noise and echo
- **Surface**: Place on a stable, non-vibrating surface

### 2. Speaking Technique
- **Clarity**: Speak clearly and at moderate pace
- **Volume**: Use normal conversational volume (avoid shouting)
- **Consistency**: Maintain consistent distance and orientation
- **Pauses**: Use natural pauses between phrases

### 3. Environmental Optimization
- **Noise Control**: Minimize air conditioning, fan noise, typing
- **Echo Reduction**: Use in rooms with soft furnishings
- **Isolation**: Avoid areas with hard surfaces that cause reflection

### 4. System Settings
- **Audio Exclusive Mode**: Ensure no other applications are using the microphone
- **Real-time Priority**: Run STT applications with higher priority if possible
- **CPU Performance**: Ensure adequate CPU resources for real-time processing

## Troubleshooting

### Common Issues and Solutions

#### 1. Device Not Detected
```bash
# Check USB connection
lsusb | grep -i respeaker

# Restart audio system
sudo systemctl restart pipewire
```

#### 2. Poor Audio Quality
```bash
# Run the monitoring tool
python3 respeaker_stt_monitor.py

# Check volume levels (should be 60-80%)
pactl list sources | grep -A 10 ReSpeaker
```

#### 3. STT Accuracy Issues
```bash
# Run advanced tuning
python3 advanced_respeaker_stt_tuning.py

# Test with sample phrases
pw-cat --record --format s16 --rate 16000 --channels 1 test.wav
# Then test the file with your STT system
```

#### 4. Configuration Reset
```bash
# Re-run auto-configuration
./respeaker_stt_autoconfig.sh

# Check log for issues
tail -f /var/log/respeaker_stt_config.log
```

## Performance Metrics

### Optimal Audio Characteristics
- **RMS Amplitude**: 0.05 - 0.2 (optimal range)
- **Maximum Amplitude**: 0.1 - 0.8 (avoid clipping)
- **Signal-to-Noise Ratio**: >20dB (good quality)
- **Frequency Response**: 80Hz - 8kHz (speech optimized)

### STT Performance Indicators
- **Recognition Latency**: <500ms
- **Word Error Rate**: <5% for clear speech
- **Phrase Detection**: Accurate start/stop detection
- **Language Model Confidence**: >85% for clear phrases

## Integration with OpenAvatarChat

Your OpenAvatarChat project is now configured with:

1. **Optimized Whisper Settings**: Enhanced for Polish language STT
2. **ReSpeaker Device Configuration**: Automatic detection and setup
3. **Audio Preprocessing**: Real-time filtering for better recognition
4. **Performance Monitoring**: Built-in quality monitoring

To use the optimized configuration:
```bash
# Start with optimized settings
python3 src/demo.py --config config/chat_with_openai_compatible_edge_tts_pl_female_stt_optimized.yaml
```

## Support and Maintenance

### Regular Maintenance
- **Weekly**: Run the monitoring tool to check performance
- **Monthly**: Update audio drivers and system packages
- **As Needed**: Re-run optimization scripts if issues arise

### Performance Tuning
- Use the test suite to measure accuracy periodically
- Adjust gain levels based on your voice and environment
- Monitor system resources during high STT load

### Logs and Diagnostics
- **Configuration Log**: `/var/log/respeaker_stt_config.log`
- **Test Results**: `/tmp/respeaker_stt_tests/`
- **Performance Reports**: Generated by monitoring tools

---

Your ReSpeaker USB Mic Array v3.1 is now optimized for maximum STT precision. The configuration prioritizes accuracy over audio quality, with specialized filtering and processing designed specifically for speech recognition applications.
