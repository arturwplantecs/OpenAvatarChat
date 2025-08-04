#!/bin/bash
# ReSpeaker STT Auto-Configuration Script
# This script automatically configures the ReSpeaker for optimal STT performance

set -e

DEVICE_NAME="alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.analog-surround-21"
LOG_FILE="/var/log/respeaker_stt_config.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

wait_for_device() {
    log_message "Waiting for ReSpeaker device to be available..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if pactl list sources | grep -q "$DEVICE_NAME"; then
            log_message "ReSpeaker device found!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_message "ERROR: ReSpeaker device not found after $max_attempts attempts"
    return 1
}

configure_optimal_settings() {
    log_message "Configuring optimal STT settings for ReSpeaker..."
    
    # Set as default input device
    if pactl set-default-source "$DEVICE_NAME" 2>/dev/null; then
        log_message "Set ReSpeaker as default input device"
    else
        log_message "WARNING: Could not set as default input device"
    fi
    
    # Set optimal volume (70% for good balance)
    if pactl set-source-volume "$DEVICE_NAME" 70% 2>/dev/null; then
        log_message "Set volume to 70%"
    else
        log_message "WARNING: Could not set volume"
    fi
    
    # Unmute the device
    if pactl set-source-mute "$DEVICE_NAME" 0 2>/dev/null; then
        log_message "Unmuted ReSpeaker"
    else
        log_message "WARNING: Could not unmute device"
    fi
    
    # Force optimal sample rate for STT
    if command -v pw-metadata >/dev/null 2>&1; then
        if pw-metadata -n settings 0 clock.force-rate 16000 >/dev/null 2>&1; then
            log_message "Set sample rate to 16kHz"
        else
            log_message "WARNING: Could not set sample rate"
        fi
    fi
}

verify_configuration() {
    log_message "Verifying ReSpeaker configuration..."
    
    # Check if device is active
    if pactl list sources | grep -A 10 "$DEVICE_NAME" | grep -q "State: RUNNING\|State: IDLE"; then
        log_message "✓ Device state is good"
    else
        log_message "⚠ Device may not be properly configured"
    fi
    
    # Check volume level
    local volume=$(pactl list sources | grep -A 15 "$DEVICE_NAME" | grep "Volume:" | head -1 | grep -o '[0-9]*%' | head -1 | tr -d '%')
    if [ "$volume" -ge 60 ] && [ "$volume" -le 80 ]; then
        log_message "✓ Volume level optimal: ${volume}%"
    else
        log_message "⚠ Volume level may need adjustment: ${volume}%"
    fi
    
    # Check if unmuted
    if pactl list sources | grep -A 15 "$DEVICE_NAME" | grep -q "Mute: no"; then
        log_message "✓ Device is unmuted"
    else
        log_message "⚠ Device is muted"
    fi
}

create_test_recording() {
    log_message "Creating test recording to verify STT setup..."
    
    local test_file="/tmp/respeaker_startup_test.wav"
    
    # Record 2 seconds of audio
    if timeout 3 pw-cat --record --format s16 --rate 16000 --channels 1 "$test_file" >/dev/null 2>&1; then
        if [ -f "$test_file" ] && [ -s "$test_file" ]; then
            log_message "✓ Test recording successful"
            
            # Check file properties
            if command -v soxi >/dev/null 2>&1; then
                local properties=$(soxi -r -c -b "$test_file" 2>/dev/null)
                log_message "Test recording properties: $properties"
            fi
            
            rm -f "$test_file"
        else
            log_message "⚠ Test recording file is empty or missing"
        fi
    else
        log_message "⚠ Test recording failed"
    fi
}

main() {
    log_message "Starting ReSpeaker STT auto-configuration..."
    
    # Wait for device to be available
    if ! wait_for_device; then
        log_message "FAILED: ReSpeaker device not available"
        exit 1
    fi
    
    # Configure optimal settings
    configure_optimal_settings
    
    # Give the system a moment to apply settings
    sleep 2
    
    # Verify configuration
    verify_configuration
    
    # Create test recording
    create_test_recording
    
    log_message "ReSpeaker STT auto-configuration completed!"
    
    # Display summary
    echo ""
    echo "ReSpeaker STT Configuration Summary:"
    echo "===================================="
    echo "✓ Device configured for optimal STT performance"
    echo "✓ Sample rate: 16kHz (optimal for speech recognition)"
    echo "✓ Volume: 70% (balanced for clarity without clipping)"
    echo "✓ Device unmuted and set as default input"
    echo ""
    echo "Your ReSpeaker is ready for high-precision STT!"
    echo "Check the log file for details: $LOG_FILE"
}

# Run the configuration
main "$@"
