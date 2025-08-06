// API communication handler
class ApiClient {
    constructor() {
        this.sessionId = null;
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000;
    }
    
    async checkHealth() {
        try {
            const response = await fetch(config.getApiEndpoints().health, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }
            
            const data = await response.json();
            this.isConnected = true;
            this.retryCount = 0;
            return data;
        } catch (error) {
            this.isConnected = false;
            console.error('Health check failed:', error);
            throw error;
        }
    }
    
    async createSession() {
        try {
            const response = await fetch(config.getApiEndpoints().createSession, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'web-user-' + Date.now(),
                    session_name: 'Web Chat Session'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.status}`);
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            console.log('Session created:', this.sessionId);
            return data;
        } catch (error) {
            console.error('Failed to create session:', error);
            throw error;
        }
    }
    
    async sendTextMessage(text) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        try {
            const response = await fetch(config.getApiEndpoints().sendText(this.sessionId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to send message: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to send text message:', error);
            throw error;
        }
    }
    
    async sendAudioMessage(audioBlob) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'audio.wav');
            
            const response = await fetch(`${config.get('apiUrl')}/api/v1/sessions/${this.sessionId}/audio`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Failed to send audio: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to send audio message:', error);
            throw error;
        }
    }
    
    async sendMessage(text, options = {}) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }
        
        try {
            const payload = {
                text: text,
                ...options
            };
            
            const response = await fetch(config.getApiEndpoints().sendText(this.sessionId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to send message: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to send message:', error);
            throw error;
        }
    }
    
    async getPipelineStatus() {
        try {
            const response = await fetch(config.getApiEndpoints().pipelineStatus, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get pipeline status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to get pipeline status:', error);
            throw error;
        }
    }
    
    async initialize() {
        try {
            // Check API health
            await this.checkHealth();
            
            // Create session
            await this.createSession();
            
            // Get pipeline status
            const status = await this.getPipelineStatus();
            console.log('Pipeline status:', status);
            
            return true;
        } catch (error) {
            console.error('API initialization failed:', error);
            
            // Retry logic
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Retrying API initialization (${this.retryCount}/${this.maxRetries})...`);
                
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * this.retryCount));
                return await this.initialize();
            }
            
            throw error;
        }
    }
    
    async cleanup() {
        if (this.sessionId) {
            try {
                await fetch(config.getApiEndpoints().deleteSession(this.sessionId), {
                    method: 'DELETE'
                });
                console.log('Session cleaned up:', this.sessionId);
            } catch (error) {
                console.warn('Failed to cleanup session:', error);
            }
            this.sessionId = null;
        }
    }
}

// Initialize global API client
window.apiClient = new ApiClient();
