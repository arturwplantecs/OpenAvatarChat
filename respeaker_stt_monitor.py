#!/usr/bin/env python3
"""
Real-time ReSpeaker STT Performance Monitor
Continuously monitors audio input quality and provides feedback for optimal STT performance
"""

import subprocess
import time
import sys
import threading
import queue
import os
import signal
from datetime import datetime

class ReSpeakerSTTMonitor:
    def __init__(self):
        self.monitoring = False
        self.audio_queue = queue.Queue()
        self.device_name = "alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.analog-surround-21"
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        print("ReSpeaker STT Performance Monitor")
        print("=" * 40)
        print("Monitoring audio input quality for optimal STT...")
        print("Press Ctrl+C to stop monitoring\n")
        
        self.monitoring = True
        
        # Start audio level monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_audio_levels)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start main monitoring loop
        try:
            self.monitoring_loop()
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            self.monitoring = False
    
    def monitor_audio_levels(self):
        """Monitor audio input levels continuously"""
        while self.monitoring:
            try:
                # Get current audio level
                result = subprocess.run([
                    'pactl', 'list', 'sources'
                ], capture_output=True, text=True, timeout=2)
                
                # Parse volume level for ReSpeaker
                lines = result.stdout.split('\n')
                in_respeaker_section = False
                
                for line in lines:
                    if self.device_name in line:
                        in_respeaker_section = True
                    elif in_respeaker_section and 'Volume:' in line:
                        # Extract volume percentage
                        if '%' in line:
                            volume_part = line.split('%')[0]
                            volume_str = volume_part.split()[-1]
                            try:
                                volume = int(volume_str)
                                self.audio_queue.put(('volume', volume))
                            except ValueError:
                                pass
                        break
                    elif in_respeaker_section and 'Name:' in line and self.device_name not in line:
                        break
                
                time.sleep(1)
                
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                time.sleep(1)
                continue
    
    def monitoring_loop(self):
        """Main monitoring display loop"""
        last_volume = 0
        last_recommendation = ""
        
        while self.monitoring:
            try:
                # Process queued updates
                while not self.audio_queue.empty():
                    msg_type, value = self.audio_queue.get_nowait()
                    
                    if msg_type == 'volume':
                        if value != last_volume:
                            last_volume = value
                            
                            # Clear line and show current status
                            print(f"\r{datetime.now().strftime('%H:%M:%S')} | Volume: {value:3d}% | ", end="")
                            
                            # Provide real-time feedback
                            if value < 50:
                                recommendation = "LOW - Increase gain for better STT sensitivity"
                                status_color = "🔴"
                            elif value > 85:
                                recommendation = "HIGH - Reduce gain to prevent clipping"
                                status_color = "🟡"
                            elif 60 <= value <= 75:
                                recommendation = "OPTIMAL - Perfect for STT recognition"
                                status_color = "🟢"
                            else:
                                recommendation = "GOOD - Suitable for STT"
                                status_color = "🟡"
                            
                            if recommendation != last_recommendation:
                                print(f"{status_color} {recommendation}", end="")
                                last_recommendation = recommendation
                            
                            sys.stdout.flush()
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
    
    def quick_test_recording(self):
        """Perform a quick test recording and analysis"""
        print("\nPerforming quick STT quality test...")
        print("Please say: 'Testing microphone quality for speech recognition'")
        input("Press Enter when ready...")
        
        test_file = "/tmp/stt_quick_test.wav"
        
        # Record 3-second sample
        process = subprocess.Popen([
            'pw-cat', '--record',
            '--format', 's16',
            '--rate', '16000',
            '--channels', '1',
            test_file
        ])
        
        time.sleep(3)
        process.terminate()
        process.wait()
        
        if os.path.exists(test_file):
            # Analyze recording
            self.analyze_test_recording(test_file)
        else:
            print("❌ Test recording failed")
    
    def analyze_test_recording(self, audio_file):
        """Analyze test recording quality"""
        print("\nAnalyzing recording quality...")
        
        try:
            # Get audio statistics
            result = subprocess.run([
                'sox', audio_file, '-n', 'stat'
            ], capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            max_amplitude = 0
            rms_amplitude = 0
            
            for line in result.stdout.split('\n'):
                if 'Maximum amplitude' in line:
                    max_amplitude = float(line.split()[-1])
                elif 'RMS amplitude' in line:
                    rms_amplitude = float(line.split()[-1])
            
            print(f"Maximum amplitude: {max_amplitude:.3f}")
            print(f"RMS amplitude: {rms_amplitude:.3f}")
            
            # Provide quality assessment
            if max_amplitude > 0.95:
                print("⚠️  WARNING: Clipping detected - reduce microphone gain")
            elif max_amplitude < 0.1:
                print("⚠️  WARNING: Signal too low - increase microphone gain")
            else:
                print("✅ Signal level is good for STT")
            
            if rms_amplitude < 0.05:
                print("🔇 Signal is very quiet - speak louder or increase gain")
            elif rms_amplitude > 0.3:
                print("📢 Signal is very loud - speak softer or reduce gain")
            else:
                print("🎯 Signal strength is optimal for STT")
            
            # Check for optimal STT range
            if 0.1 <= max_amplitude <= 0.8 and 0.05 <= rms_amplitude <= 0.2:
                print("🏆 EXCELLENT: Audio is in optimal range for STT accuracy!")
            
        except Exception as e:
            print(f"Analysis failed: {e}")
    
    def show_current_settings(self):
        """Display current audio settings"""
        print("\nCurrent ReSpeaker Settings:")
        print("-" * 30)
        
        try:
            # Get source info
            result = subprocess.run([
                'pactl', 'list', 'sources'
            ], capture_output=True, text=True)
            
            lines = result.stdout.split('\n')
            in_respeaker_section = False
            
            for line in lines:
                if self.device_name in line:
                    in_respeaker_section = True
                    print(f"Device: {self.device_name}")
                elif in_respeaker_section:
                    if 'State:' in line:
                        print(f"State: {line.split(':', 1)[1].strip()}")
                    elif 'Sample Specification:' in line:
                        print(f"Format: {line.split(':', 1)[1].strip()}")
                    elif 'Volume:' in line:
                        print(f"Volume: {line.split(':', 1)[1].strip()}")
                    elif 'Mute:' in line:
                        print(f"Mute: {line.split(':', 1)[1].strip()}")
                    elif 'Name:' in line and self.device_name not in line:
                        break
                        
        except subprocess.CalledProcessError:
            print("Could not retrieve current settings")

def main():
    monitor = ReSpeakerSTTMonitor()
    
    while True:
        print("\nReSpeaker STT Performance Monitor")
        print("1. Start real-time monitoring")
        print("2. Quick test recording")
        print("3. Show current settings")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            monitor.quick_test_recording()
        elif choice == '3':
            monitor.show_current_settings()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
