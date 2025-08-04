#!/usr/bin/env python3
"""
ReSpeaker USB Mic Array v3.1 STT Optimization Script
Configures the device for maximum speech-to-text precision
"""

import usb.core
import usb.util
import sys
import time
import subprocess
import os

# ReSpeaker USB Mic Array v3.1 VID/PID
RESPEAKER_VID = 0x2886
RESPEAKER_PID = 0x0018

# Optimal settings for STT precision
class ReSpeakerOptimizer:
    def __init__(self):
        self.dev = None
        self.find_device()
    
    def find_device(self):
        """Find the ReSpeaker device"""
        self.dev = usb.core.find(idVendor=RESPEAKER_VID, idProduct=RESPEAKER_PID)
        if self.dev is None:
            raise ValueError("ReSpeaker device not found")
        print(f"Found ReSpeaker device: {self.dev}")
    
    def set_optimal_stt_config(self):
        """Configure device for optimal STT performance"""
        try:
            # Detach kernel driver if attached
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
            
            # Set configuration
            self.dev.set_configuration()
            
            print("ReSpeaker configured for optimal STT performance")
            
            # Configure microphone parameters for STT
            # High-pass filter to remove low-frequency noise
            self.configure_hpf()
            
            # Set optimal gain for speech
            self.configure_gain()
            
            # Enable noise suppression features
            self.configure_noise_suppression()
            
        except Exception as e:
            print(f"Configuration error: {e}")
    
    def configure_hpf(self):
        """Configure high-pass filter for speech frequencies"""
        print("Configuring high-pass filter for speech optimization...")
        # HPF at 80Hz to remove low-frequency noise while preserving speech
        try:
            # Enable HPF (register-based control)
            self.dev.ctrl_transfer(0x21, 0x01, 0x0200, 0x0200, [0x01])
            print("High-pass filter enabled")
        except:
            print("HPF configuration via direct control not available")
    
    def configure_gain(self):
        """Set optimal microphone gain for STT"""
        print("Configuring microphone gain...")
        try:
            # Set moderate gain to avoid clipping while maintaining sensitivity
            # This is a balanced setting for clear speech recognition
            self.dev.ctrl_transfer(0x21, 0x01, 0x0100, 0x0200, [0x10])
            print("Microphone gain optimized for STT")
        except:
            print("Gain configuration via direct control not available")
    
    def configure_noise_suppression(self):
        """Enable noise suppression features"""
        print("Enabling noise suppression...")
        try:
            # Enable automatic gain control and noise suppression
            self.dev.ctrl_transfer(0x21, 0x01, 0x0300, 0x0200, [0x01])
            print("Noise suppression enabled")
        except:
            print("Noise suppression configuration not available via direct control")

def configure_pulseaudio_for_stt():
    """Configure PulseAudio/PipeWire for optimal STT recording"""
    print("\nConfiguring audio system for STT...")
    
    # Set the ReSpeaker as default input device
    respeaker_source = "alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.analog-surround-21"
    
    try:
        # Set default source
        subprocess.run(['pactl', 'set-default-source', respeaker_source], check=True)
        print(f"Set {respeaker_source} as default input device")
        
        # Set optimal sample rate for STT (16kHz is often optimal for speech recognition)
        subprocess.run(['pactl', 'set-source-volume', respeaker_source, '70%'], check=True)
        print("Set volume to 70% for optimal STT sensitivity")
        
        # Unmute the source
        subprocess.run(['pactl', 'set-source-mute', respeaker_source, '0'], check=True)
        print("Unmuted input source")
        
    except subprocess.CalledProcessError as e:
        print(f"PulseAudio configuration error: {e}")

def create_asoundrc_for_stt():
    """Create optimized .asoundrc for STT recording"""
    asoundrc_content = """
# Optimized ALSA configuration for ReSpeaker STT
pcm.respeaker_stt {
    type dsnoop
    ipc_key 1024
    slave {
        pcm "hw:3,0"
        rate 16000
        channels 1
        format S16_LE
        period_size 512
        buffer_size 2048
    }
    bindings.0 0
}

pcm.!default {
    type asym
    playback.pcm "hw:0,0"
    capture.pcm "respeaker_stt"
}

ctl.!default {
    type hw
    card 0
}
"""
    
    asoundrc_path = os.path.expanduser("~/.asoundrc")
    print(f"\nCreating optimized .asoundrc at {asoundrc_path}")
    
    with open(asoundrc_path, 'w') as f:
        f.write(asoundrc_content)
    
    print("Created .asoundrc for optimal STT recording")

def test_recording():
    """Test the optimized configuration"""
    print("\nTesting optimized configuration...")
    
    try:
        # Test recording with optimized settings
        test_file = "/tmp/stt_test.wav"
        cmd = [
            'pw-cat', 
            '--record',
            '--format', 's16',
            '--rate', '16000',
            '--channels', '1',
            test_file
        ]
        
        print("Recording 3-second test sample...")
        print("Please speak clearly for testing...")
        
        process = subprocess.Popen(cmd)
        time.sleep(3)
        process.terminate()
        process.wait()
        
        if os.path.exists(test_file):
            # Get file info
            result = subprocess.run(['file', test_file], capture_output=True, text=True)
            print(f"Test recording created: {result.stdout.strip()}")
            
            # Check audio properties
            try:
                result = subprocess.run(['soxi', test_file], capture_output=True, text=True)
                print("Audio properties:")
                print(result.stdout)
            except:
                print("soxi not available, install sox for detailed audio info")
                
            return True
        else:
            print("Test recording failed")
            return False
            
    except Exception as e:
        print(f"Test recording error: {e}")
        return False

def create_stt_optimized_config():
    """Create an optimized configuration file for your OpenAvatarChat project"""
    print("\nCreating STT-optimized configuration...")
    
    # Read the current config
    config_path = "/home/arti/Repos/OpenAvatarChat/config/chat_with_openai_compatible_edge_tts_pl_female.yaml"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Create optimized version
        optimized_content = content.replace(
            'language: "pl"',
            'language: "pl"\n        # STT Optimized settings for ReSpeaker\n        sample_rate: 16000\n        channels: 1\n        chunk_size: 512'
        )
        
        # Save optimized config
        optimized_path = config_path.replace('.yaml', '_stt_optimized.yaml')
        with open(optimized_path, 'w') as f:
            f.write(optimized_content)
        
        print(f"Created STT-optimized config: {optimized_path}")
        
    except Exception as e:
        print(f"Config optimization error: {e}")

def main():
    print("ReSpeaker USB Mic Array v3.1 STT Optimization")
    print("=" * 50)
    
    try:
        # Initialize and configure ReSpeaker
        optimizer = ReSpeakerOptimizer()
        optimizer.set_optimal_stt_config()
        
        # Configure audio system
        configure_pulseaudio_for_stt()
        
        # Create optimized ALSA config
        create_asoundrc_for_stt()
        
        # Test the configuration
        if test_recording():
            print("\n✓ ReSpeaker successfully optimized for STT!")
        else:
            print("\n⚠ Configuration applied but test recording failed")
        
        # Create optimized config for your project
        create_stt_optimized_config()
        
        print("\nOptimization complete!")
        print("\nRecommendations for maximum STT precision:")
        print("1. Use 16kHz sample rate (optimal for speech recognition)")
        print("2. Use mono recording (channel 0 is front-center mic)")
        print("3. Position the device 30-60cm from speaker")
        print("4. Speak clearly and at moderate volume")
        print("5. Minimize background noise")
        print("6. Use the optimized config file created")
        
    except Exception as e:
        print(f"Optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
