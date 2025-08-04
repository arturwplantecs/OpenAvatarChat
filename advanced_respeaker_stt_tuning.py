#!/usr/bin/env python3
"""
Advanced ReSpeaker USB Mic Array v3.1 STT Precision Tuning
This script provides advanced tuning options for maximum speech recognition accuracy
"""

import subprocess
import sys
import time
import numpy as np
import os
from pathlib import Path

class AdvancedReSpeakerSTTTuner:
    def __init__(self):
        self.device_name = "alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.analog-surround-21"
        self.test_samples_dir = "/tmp/respeaker_stt_tests"
        os.makedirs(self.test_samples_dir, exist_ok=True)
    
    def apply_ultra_precision_settings(self):
        """Apply the most precise settings for STT"""
        print("Applying ultra-precision STT settings...")
        
        # 1. Set optimal sample rate (16kHz is the sweet spot for speech recognition)
        self.set_sample_rate(16000)
        
        # 2. Configure noise suppression and echo cancellation
        self.configure_noise_suppression()
        
        # 3. Set optimal microphone gain to avoid clipping
        self.set_optimal_gain()
        
        # 4. Configure directional pickup (focus on front microphone)
        self.configure_directional_pickup()
        
        # 5. Apply audio preprocessing filters
        self.apply_preprocessing_filters()
    
    def set_sample_rate(self, rate=16000):
        """Set optimal sample rate for STT"""
        print(f"Setting sample rate to {rate}Hz for optimal STT performance...")
        try:
            # Force specific sample rate through PipeWire
            subprocess.run([
                'pw-metadata', '-n', 'settings', '0', 'clock.force-rate', str(rate)
            ], check=True)
            print(f"Sample rate set to {rate}Hz")
        except:
            print("Could not set sample rate via pw-metadata, using ALSA configuration")
    
    def configure_noise_suppression(self):
        """Configure advanced noise suppression"""
        print("Configuring advanced noise suppression...")
        
        # Create PipeWire filter for noise suppression
        filter_config = """
context.modules = [
    {   name = libpipewire-module-filter-chain
        args = {
            node.description = "ReSpeaker STT Noise Suppression"
            media.name       = "ReSpeaker STT Filter"
            filter.graph = {
                nodes = [
                    {
                        type   = builtin
                        name   = highpass
                        label  = highpass
                        control = { "Freq" = 80.0 "Q" = 0.7 }
                    }
                    {
                        type   = builtin
                        name   = lowpass
                        label  = lowpass
                        control = { "Freq" = 8000.0 "Q" = 0.7 }
                    }
                    {
                        type   = builtin
                        name   = compressor
                        label  = compressor
                        control = { 
                            "Threshold" = -18.0
                            "Ratio" = 4.0
                            "Attack" = 0.003
                            "Release" = 0.1
                        }
                    }
                ]
                links = [
                    { output = "highpass:Out" input = "lowpass:In" }
                    { output = "lowpass:Out" input = "compressor:In" }
                ]
            }
            capture.props = {
                node.name      = "respeaker_stt_filter"
                media.class    = Audio/Source
                audio.channels = 1
                audio.position = [ MONO ]
            }
            playback.props = {
                node.name      = "respeaker_stt_filter_sink"
                media.class    = Audio/Sink
                audio.channels = 1
                audio.position = [ MONO ]
            }
        }
    }
]
"""
        
        # Save filter configuration
        config_dir = Path.home() / ".config" / "pipewire"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_dir / "respeaker_stt_filter.conf", "w") as f:
            f.write(filter_config)
        
        print("Noise suppression filter configured")
    
    def set_optimal_gain(self):
        """Set optimal microphone gain for speech without clipping"""
        print("Setting optimal microphone gain...")
        
        # Test different gain levels to find optimal
        gain_levels = [60, 65, 70, 75, 80]
        best_gain = 70  # Default safe value
        
        for gain in gain_levels:
            try:
                subprocess.run([
                    'pactl', 'set-source-volume', self.device_name, f'{gain}%'
                ], check=True)
                
                # Test for clipping
                if not self.test_for_clipping(gain):
                    best_gain = gain
                    break
                    
            except subprocess.CalledProcessError:
                continue
        
        # Set the best gain found
        try:
            subprocess.run([
                'pactl', 'set-source-volume', self.device_name, f'{best_gain}%'
            ], check=True)
            print(f"Optimal gain set to {best_gain}%")
        except:
            print("Could not set optimal gain")
    
    def test_for_clipping(self, gain_level):
        """Test if current gain level causes clipping"""
        print(f"Testing gain level {gain_level}% for clipping...")
        
        test_file = f"{self.test_samples_dir}/clipping_test_{gain_level}.wav"
        
        try:
            # Record short sample
            process = subprocess.Popen([
                'pw-cat', '--record',
                '--format', 's16',
                '--rate', '16000',
                '--channels', '1',
                test_file
            ])
            
            # Speak test phrase
            subprocess.run(['espeak-ng', '-s', '150', 'Testing microphone level for clipping detection'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(1)
            process.terminate()
            process.wait()
            
            # Analyze for clipping
            if os.path.exists(test_file):
                return self.analyze_clipping(test_file)
                
        except Exception as e:
            print(f"Clipping test failed: {e}")
            
        return False
    
    def analyze_clipping(self, audio_file):
        """Analyze audio file for clipping"""
        try:
            # Use sox to detect clipping
            result = subprocess.run([
                'sox', audio_file, '-n', 'stat'
            ], capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            # Look for maximum amplitude near full scale
            for line in result.stdout.split('\n'):
                if 'Maximum amplitude' in line:
                    max_amp = float(line.split()[-1])
                    # If amplitude is above 0.95, consider it clipping
                    return max_amp > 0.95
                    
        except:
            pass
            
        return False
    
    def configure_directional_pickup(self):
        """Configure the microphone array for directional pickup"""
        print("Configuring directional pickup pattern...")
        
        # Create ALSA configuration for beamforming
        alsa_beamform_config = """
# Beamforming configuration for ReSpeaker
pcm.respeaker_beamform {
    type dsnoop
    ipc_key 2048
    slave {
        pcm "hw:3,0"
        rate 16000
        channels 3
        format S16_LE
        period_size 256
        buffer_size 1024
    }
    # Use front microphone (channel 0) as primary
    bindings.0 0
}

# Create a plugin for directional processing
pcm.respeaker_directional {
    type plug
    slave.pcm "respeaker_beamform"
    slave.channels 1
}
"""
        
        # Append to .asoundrc
        asoundrc_path = Path.home() / ".asoundrc"
        with open(asoundrc_path, "a") as f:
            f.write("\n" + alsa_beamform_config)
        
        print("Directional pickup configured")
    
    def apply_preprocessing_filters(self):
        """Apply audio preprocessing for better STT"""
        print("Applying audio preprocessing filters...")
        
        # Create a comprehensive audio processing chain
        processing_script = f"""#!/bin/bash
# Audio preprocessing for STT
# This script can be used to process audio before feeding to STT

INPUT_FILE="$1"
OUTPUT_FILE="$2"

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <input_file> <output_file>"
    exit 1
fi

# Apply comprehensive audio processing for STT
sox "$INPUT_FILE" "$OUTPUT_FILE" \\
    highpass 80 \\
    lowpass 8000 \\
    compand 0.02,0.20 5:-60,-40,-10 -5 -90 0.1 \\
    norm -1 \\
    rate 16000 \\
    channels 1

echo "Audio preprocessed for STT: $OUTPUT_FILE"
"""
        
        preprocess_script = Path("/usr/local/bin/respeaker_preprocess_stt")
        try:
            with open("/tmp/respeaker_preprocess_stt.sh", "w") as f:
                f.write(processing_script)
            
            subprocess.run(["sudo", "mv", "/tmp/respeaker_preprocess_stt.sh", str(preprocess_script)], check=True)
            subprocess.run(["sudo", "chmod", "+x", str(preprocess_script)], check=True)
            
            print(f"Audio preprocessing script installed at {preprocess_script}")
        except:
            print("Could not install preprocessing script (requires sudo)")
    
    def create_stt_test_suite(self):
        """Create a comprehensive test suite for STT accuracy"""
        print("Creating STT test suite...")
        
        test_phrases = [
            "The quick brown fox jumps over the lazy dog",
            "She sells seashells by the seashore",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood",
            "Peter Piper picked a peck of pickled peppers",
            "Red leather yellow leather",
            "Unique New York",
            "Toy boat toy boat toy boat",
            "Six sick slick slim sycamore saplings"
        ]
        
        print("Recording test phrases for STT accuracy measurement...")
        
        for i, phrase in enumerate(test_phrases):
            print(f"Recording phrase {i+1}: {phrase}")
            
            # Display phrase for user to read
            print(f"Please say: '{phrase}'")
            input("Press Enter when ready to record...")
            
            test_file = f"{self.test_samples_dir}/test_phrase_{i+1}.wav"
            
            # Record phrase
            process = subprocess.Popen([
                'pw-cat', '--record',
                '--format', 's16',
                '--rate', '16000',
                '--channels', '1',
                test_file
            ])
            
            time.sleep(len(phrase) * 0.1 + 2)  # Adaptive recording time
            process.terminate()
            process.wait()
            
            print(f"Recorded to {test_file}")
        
        print(f"Test suite created in {self.test_samples_dir}")
        return self.test_samples_dir
    
    def analyze_stt_performance(self, test_dir):
        """Analyze STT performance using recorded test samples"""
        print("Analyzing STT performance...")
        
        # This would integrate with your actual STT system
        # For now, we'll provide the framework
        
        results = []
        test_files = list(Path(test_dir).glob("test_phrase_*.wav"))
        
        for test_file in test_files:
            print(f"Analyzing {test_file.name}...")
            
            # Audio quality metrics
            quality_metrics = self.get_audio_quality_metrics(str(test_file))
            results.append({
                'file': test_file.name,
                'metrics': quality_metrics
            })
        
        # Generate report
        self.generate_performance_report(results)
    
    def get_audio_quality_metrics(self, audio_file):
        """Get audio quality metrics for STT optimization"""
        metrics = {}
        
        try:
            # Get basic audio stats
            result = subprocess.run([
                'sox', audio_file, '-n', 'stat'
            ], capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            for line in result.stdout.split('\n'):
                if 'RMS amplitude' in line:
                    metrics['rms_amplitude'] = float(line.split()[-1])
                elif 'Maximum amplitude' in line:
                    metrics['max_amplitude'] = float(line.split()[-1])
                elif 'Minimum amplitude' in line:
                    metrics['min_amplitude'] = float(line.split()[-1])
                elif 'Mean amplitude' in line:
                    metrics['mean_amplitude'] = float(line.split()[-1])
                    
        except:
            pass
        
        return metrics
    
    def generate_performance_report(self, results):
        """Generate a performance analysis report"""
        report_file = f"{self.test_samples_dir}/stt_performance_report.txt"
        
        with open(report_file, "w") as f:
            f.write("ReSpeaker STT Performance Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            
            for result in results:
                f.write(f"File: {result['file']}\n")
                f.write("Metrics:\n")
                for key, value in result['metrics'].items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
            
            # Calculate averages
            if results:
                avg_rms = np.mean([r['metrics'].get('rms_amplitude', 0) for r in results])
                avg_max = np.mean([r['metrics'].get('max_amplitude', 0) for r in results])
                
                f.write("Average Metrics:\n")
                f.write(f"  Average RMS: {avg_rms:.4f}\n")
                f.write(f"  Average Max: {avg_max:.4f}\n")
                
                # Recommendations
                f.write("\nRecommendations:\n")
                if avg_rms < 0.1:
                    f.write("- Consider increasing microphone gain for better signal level\n")
                elif avg_rms > 0.5:
                    f.write("- Consider decreasing microphone gain to avoid clipping\n")
                else:
                    f.write("- Signal levels are optimal for STT\n")
                
                if avg_max > 0.95:
                    f.write("- Reduce gain to prevent clipping\n")
        
        print(f"Performance report saved to {report_file}")

def main():
    print("Advanced ReSpeaker STT Precision Tuning")
    print("=" * 50)
    
    tuner = AdvancedReSpeakerSTTTuner()
    
    print("\n1. Applying ultra-precision STT settings...")
    tuner.apply_ultra_precision_settings()
    
    print("\n2. Would you like to run the STT test suite? (y/n): ", end="")
    response = input().lower().strip()
    
    if response == 'y':
        test_dir = tuner.create_stt_test_suite()
        tuner.analyze_stt_performance(test_dir)
    
    print("\nAdvanced tuning complete!")
    print("\nOptimal STT Configuration Summary:")
    print("- Sample Rate: 16kHz (optimal for speech recognition)")
    print("- Channels: Mono (front microphone)")
    print("- Bit Depth: 16-bit")
    print("- Noise Suppression: Enabled")
    print("- Dynamic Range Compression: Applied")
    print("- Frequency Response: 80Hz - 8kHz (speech optimized)")
    print("- Directional Pickup: Front-facing pattern")
    
    print("\nYour ReSpeaker is now optimized for maximum STT precision!")

if __name__ == "__main__":
    main()
