// Audio recording and playback handler
class AudioManager {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.audioBuffer = null;
        
        // TTS Audio element
        this.ttsAudio = document.getElementById('ttsAudio');
        
        // Initialize audio context for better browser compatibility
        this.initializeAudioContext();
    }
    
    async initializeAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio context initialized');
        } catch (error) {
            console.warn('Failed to initialize audio context:', error);
        }
    }
    
    async requestMicrophonePermission() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });
            
            console.log('Microphone permission granted');
            return true;
        } catch (error) {
            console.error('Microphone permission denied:', error);
            throw new Error('Mikrofon jest wymagany do funkcji głosowych');
        }
    }
    
    async startRecording() {
        if (this.isRecording) {
            console.warn('Already recording');
            return;
        }
        
        try {
            if (!this.stream) {
                await this.requestMicrophonePermission();
            }
            
            // Resume audio context if suspended
            if (this.audioContext && this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            this.audioChunks = [];
            
            // Configure MediaRecorder
            const options = {
                mimeType: 'audio/webm;codecs=opus'
            };
            
            // Fallback for Safari
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/mp4';
            }
            
            this.mediaRecorder = new MediaRecorder(this.stream, options);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                console.log('Recording stopped');
            };
            
            this.mediaRecorder.onerror = (error) => {
                console.error('MediaRecorder error:', error);
            };
            
            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            
            console.log('Recording started');
            return true;
        } catch (error) {
            console.error('Failed to start recording:', error);
            throw error;
        }
    }
    
    async stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            console.warn('Not recording');
            return null;
        }
        
        return new Promise((resolve, reject) => {
            this.mediaRecorder.onstop = async () => {
                try {
                    const audioBlob = new Blob(this.audioChunks, { 
                        type: this.mediaRecorder.mimeType 
                    });
                    
                    this.isRecording = false;
                    this.audioChunks = [];
                    
                    console.log('Recording completed, blob size:', audioBlob.size);
                    resolve(audioBlob);
                } catch (error) {
                    reject(error);
                }
            };
            
            this.mediaRecorder.stop();
        });
    }
    
    async playTTSAudio(base64Audio, sampleRate = 24000) {
        try {
            if (!base64Audio) {
                console.warn('No audio data to play');
                return;
            }
            
            // Decode base64 audio
            const audioData = atob(base64Audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const uint8Array = new Uint8Array(arrayBuffer);
            
            for (let i = 0; i < audioData.length; i++) {
                uint8Array[i] = audioData.charCodeAt(i);
            }
            
            // Create WAV header for PCM data
            const wavBuffer = this.createWAVFile(uint8Array, sampleRate);
            const audioBlob = new Blob([wavBuffer], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            this.ttsAudio.src = audioUrl;
            
            return new Promise((resolve, reject) => {
                this.ttsAudio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                    resolve();
                };
                
                this.ttsAudio.onerror = (error) => {
                    URL.revokeObjectURL(audioUrl);
                    reject(error);
                };
                
                this.ttsAudio.play().catch(reject);
            });
        } catch (error) {
            console.error('Failed to play TTS audio:', error);
            throw error;
        }
    }
    
    createWAVFile(pcmData, sampleRate) {
        const length = pcmData.length;
        const buffer = new ArrayBuffer(44 + length);
        const view = new DataView(buffer);
        
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, length, true);
        
        // Copy PCM data
        const dataView = new Uint8Array(buffer, 44);
        dataView.set(pcmData);
        
        return buffer;
    }
    
    getAudioLevel() {
        if (!this.analyser) return 0;
        
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.analyser.getByteFrequencyData(dataArray);
        
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
        }
        
        return sum / bufferLength / 255;
    }
    
    async cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.audioContext && this.audioContext.state !== 'closed') {
            await this.audioContext.close();
        }
        
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
    }
}

// Initialize global audio manager
window.audioManager = new AudioManager();
