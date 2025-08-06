// Configuration management
class Config {
    constructor() {
        this.defaults = {
            apiUrl: 'http://localhost:8000',
            voiceEnabled: true,
            autoSpeak: true,
            avatarEnabled: true,
            language: 'pl'
        };
        
        this.settings = { ...this.defaults };
        this.loadSettings();
    }
    
    loadSettings() {
        try {
            const saved = localStorage.getItem('openAvatarChatSettings');
            if (saved) {
                this.settings = { ...this.defaults, ...JSON.parse(saved) };
            }
        } catch (error) {
            console.warn('Failed to load settings:', error);
            this.settings = { ...this.defaults };
        }
    }
    
    saveSettings() {
        try {
            localStorage.setItem('openAvatarChatSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }
    
    get(key) {
        return this.settings[key];
    }
    
    set(key, value) {
        this.settings[key] = value;
        this.saveSettings();
    }
    
    reset() {
        this.settings = { ...this.defaults };
        this.saveSettings();
    }
    
    getApiEndpoints() {
        const baseUrl = this.get('apiUrl');
        return {
            health: `${baseUrl}/api/v1/health`,
            createSession: `${baseUrl}/api/v1/sessions`,
            sendText: (sessionId) => `${baseUrl}/api/v1/sessions/${sessionId}/text`,
            getSession: (sessionId) => `${baseUrl}/api/v1/sessions/${sessionId}`,
            deleteSession: (sessionId) => `${baseUrl}/api/v1/sessions/${sessionId}`,
            pipelineStatus: `${baseUrl}/api/v1/pipeline/status`
        };
    }
}

// Initialize global config
window.config = new Config();
