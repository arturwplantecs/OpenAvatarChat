// Main application controller
class OpenAvatarChatApp {
    constructor() {
        this.isInitialized = false;
        this.isVoiceRecording = false;
        
        // UI Elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.voiceButton = document.getElementById('voiceButton');
        this.voiceStatus = document.getElementById('voiceStatus');
        this.voiceIndicator = document.getElementById('voiceIndicator');
        this.settingsButton = document.getElementById('settingsButton');
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettings = document.getElementById('closeSettings');
        this.saveSettings = document.getElementById('saveSettings');
        this.resetSettings = document.getElementById('resetSettings');
        
        // Status indicators
        this.micStatus = document.getElementById('micStatus');
        this.aiStatus = document.getElementById('aiStatus');
        this.videoStatus = document.getElementById('videoStatus');
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Voice recording
        this.voiceButton.addEventListener('mousedown', () => this.startVoiceRecording());
        this.voiceButton.addEventListener('mouseup', () => this.stopVoiceRecording());
        this.voiceButton.addEventListener('mouseleave', () => this.stopVoiceRecording());
        
        // Touch events for mobile
        this.voiceButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startVoiceRecording();
        });
        this.voiceButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopVoiceRecording();
        });
        
        // Settings modal
        this.settingsButton.addEventListener('click', () => this.openSettings());
        this.closeSettings.addEventListener('click', () => this.closeSettingsModal());
        this.saveSettings.addEventListener('click', () => this.saveSettingsHandler());
        this.resetSettings.addEventListener('click', () => this.resetSettingsHandler());
        
        // Close modal on overlay click
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettingsModal();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSettingsModal();
            }
            
            // Space bar for voice recording (when not typing)
            if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                if (!this.isVoiceRecording) {
                    this.startVoiceRecording();
                }
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.stopVoiceRecording();
            }
        });
        
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isVoiceRecording) {
                this.stopVoiceRecording();
            }
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    async initialize() {
        try {
            this.showLoading('Inicjalizacja aplikacji...');
            
            // Initialize audio manager
            this.updateLoadingText('Inicjalizacja systemu audio...');
            await audioManager.initializeAudioContext();
            this.updateMicStatus('Mikrofon gotowy');
            
            // Initialize avatar manager
            this.updateLoadingText('Inicjalizacja avatara...');
            await avatarManager.initialize();
            
            // Initialize API connection
            this.updateLoadingText('Łączenie z serwerem...');
            await apiClient.initialize();
            this.updateConnectionStatus('connected', 'Połączono');
            this.updateAIStatus('AI gotowy');
            
            // Load idle avatar frames
            if (config.get('avatarEnabled')) {
                this.updateLoadingText('Ładowanie avatara...');
                await this.loadIdleAvatarFrames();
            }
            
            // Request microphone permission if voice is enabled
            if (config.get('voiceEnabled')) {
                this.updateLoadingText('Inicjalizacja mikrofonu...');
                try {
                    await audioManager.requestMicrophonePermission();
                    this.updateMicStatus('Mikrofon gotowy');
                } catch (error) {
                    console.warn('Microphone permission not granted:', error);
                    this.updateMicStatus('Mikrofon niedostępny', 'warning');
                    config.set('voiceEnabled', false);
                }
            }
            
            this.isInitialized = true;
            this.hideLoading();
            
            console.log('OpenAvatarChat initialized successfully');
            
        } catch (error) {
            console.error('Initialization failed:', error);
            this.updateConnectionStatus('disconnected', 'Błąd połączenia');
            this.updateAIStatus('Błąd AI', 'error');
            this.showError('Nie udało się zainicjalizować aplikacji. Sprawdź połączenie z serwerem.');
            this.hideLoading();
        }
    }
    
    async startVoiceRecording() {
        if (!config.get('voiceEnabled') || this.isVoiceRecording || !this.isInitialized) {
            return;
        }
        
        try {
            this.isVoiceRecording = true;
            this.voiceButton.classList.add('active');
            this.voiceStatus.textContent = 'Nagrywanie...';
            
            avatarManager.displayListeningAnimation();
            await audioManager.startRecording();
            
        } catch (error) {
            console.error('Failed to start voice recording:', error);
            this.isVoiceRecording = false;
            this.voiceButton.classList.remove('active');
            this.voiceStatus.textContent = 'Błąd mikrofonu';
            this.showError('Nie udało się uruchomić nagrywania');
            avatarManager.resetToIdle();
        }
    }
    
    async stopVoiceRecording() {
        if (!this.isVoiceRecording) {
            return;
        }
        
        try {
            this.voiceButton.classList.remove('active');
            this.voiceStatus.textContent = 'Przetwarzanie...';
            
            const audioBlob = await audioManager.stopRecording();
            this.isVoiceRecording = false;
            
            if (audioBlob && audioBlob.size > 0) {
                await chatManager.sendVoiceMessage(audioBlob);
            } else {
                console.warn('No audio data recorded');
                avatarManager.resetToIdle();
            }
            
            this.voiceStatus.textContent = 'Kliknij i mów';
            
        } catch (error) {
            console.error('Failed to stop voice recording:', error);
            this.isVoiceRecording = false;
            this.voiceStatus.textContent = 'Błąd nagrywania';
            this.showError('Nie udało się przetworzyć nagrania');
            avatarManager.resetToIdle();
        }
    }
    
    // UI Update Methods
    showLoading(text = 'Ładowanie...') {
        this.loadingOverlay.style.display = 'flex';
        this.updateLoadingText(text);
    }
    
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
    
    updateLoadingText(text) {
        this.loadingText.textContent = text;
    }
    
    updateConnectionStatus(status, text) {
        this.connectionStatus.className = `connection-status ${status}`;
        this.connectionStatus.querySelector('span').textContent = text;
    }
    
    updateMicStatus(text, type = 'success') {
        this.micStatus.textContent = text;
        const statusItem = this.micStatus.parentElement;
        statusItem.className = 'status-item';
        if (type === 'error') statusItem.classList.add('error');
        if (type === 'warning') statusItem.classList.add('warning');
    }
    
    updateAIStatus(text, type = 'success') {
        this.aiStatus.textContent = text;
        const statusItem = this.aiStatus.parentElement;
        statusItem.className = 'status-item';
        if (type === 'error') statusItem.classList.add('error');
        if (type === 'warning') statusItem.classList.add('warning');
    }
    
    showError(message) {
        chatManager.showError(message);
    }
    
    // Settings Management
    openSettings() {
        this.settingsModal.style.display = 'flex';
        this.loadSettingsToForm();
    }
    
    closeSettingsModal() {
        this.settingsModal.style.display = 'none';
    }
    
    loadSettingsToForm() {
        document.getElementById('apiUrl').value = config.get('apiUrl');
        document.getElementById('voiceEnabled').checked = config.get('voiceEnabled');
        document.getElementById('autoSpeak').checked = config.get('autoSpeak');
        document.getElementById('avatarEnabled').checked = config.get('avatarEnabled');
    }
    
    async saveSettingsHandler() {
        try {
            const newSettings = {
                apiUrl: document.getElementById('apiUrl').value,
                voiceEnabled: document.getElementById('voiceEnabled').checked,
                autoSpeak: document.getElementById('autoSpeak').checked,
                avatarEnabled: document.getElementById('avatarEnabled').checked
            };
            
            // Update config
            Object.keys(newSettings).forEach(key => {
                config.set(key, newSettings[key]);
            });
            
            // Apply settings
            await this.applySettings();
            
            this.closeSettingsModal();
            this.showError('Ustawienia zostały zapisane');
            
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showError('Błąd zapisywania ustawień');
        }
    }
    
    async resetSettingsHandler() {
        if (confirm('Czy na pewno chcesz przywrócić ustawienia domyślne?')) {
            config.reset();
            this.loadSettingsToForm();
            await this.applySettings();
            this.showError('Ustawienia zostały przywrócone');
        }
    }
    
    async applySettings() {
        // Update avatar display
        avatarManager.setEnabled(config.get('avatarEnabled'));
        
        // Update voice recording availability
        if (config.get('voiceEnabled')) {
            try {
                await audioManager.requestMicrophonePermission();
                this.updateMicStatus('Mikrofon gotowy');
            } catch (error) {
                this.updateMicStatus('Mikrofon niedostępny', 'warning');
                config.set('voiceEnabled', false);
            }
        } else {
            this.updateMicStatus('Mikrofon wyłączony', 'warning');
        }
        
        // Update voice button state
        this.voiceButton.style.display = config.get('voiceEnabled') ? 'flex' : 'none';
    }
    
    async loadIdleAvatarFrames() {
        try {
            // Request idle avatar frames from the API
            const response = await apiClient.sendMessage('', {
                get_idle_frames: true,  // Fixed: use snake_case to match backend
                frame_count: 60  // 2.4 seconds at 25fps
            });
            
            if (response && response.video_frames && response.video_frames.length > 0) {
                console.log(`Loaded ${response.video_frames.length} idle avatar frames`);
                
                // Start playing idle frames in ping-pong loop
                avatarManager.idleFrames = response.video_frames;
                avatarManager.playVideoFrames(response.video_frames, true); // Set as idle loop
                
            } else {
                console.log('No idle frames received from API');
                console.log('Response:', response);
            }
        } catch (error) {
            console.error('Failed to load idle avatar frames:', error);
        }
    }
    
    setupIdleLoop(idleFrames) {
        // Store idle frames for continuous playback
        avatarManager.idleFrames = idleFrames;
        
        // Set up interval to restart idle animation
        if (avatarManager.idleInterval) {
            clearInterval(avatarManager.idleInterval);
        }
        
        avatarManager.idleInterval = setInterval(() => {
            if (!avatarManager.isPlaying && config.get('avatarEnabled')) {
                avatarManager.playVideoFrames(idleFrames);
            }
        }, 3000); // Restart every 3 seconds when not playing other animations
    }
    
    async cleanup() {
        try {
            if (this.isVoiceRecording) {
                await this.stopVoiceRecording();
            }
            
            await audioManager.cleanup();
            await avatarManager.cleanup();
            await apiClient.cleanup();
            
            console.log('Application cleanup completed');
        } catch (error) {
            console.error('Cleanup failed:', error);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    window.app = new OpenAvatarChatApp();
    await app.initialize();
});

// Handle service worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
