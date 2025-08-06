// Chat interface handler
class ChatManager {
    constructor() {
        this.messagesContainer = document.getElementById('chatMessages');
        this.textInput = document.getElementById('textInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearButton = document.getElementById('clearButton');
        
        this.messages = [];
        this.isProcessing = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Text input events
        this.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });
        
        this.textInput.addEventListener('input', () => {
            this.updateSendButton();
        });
        
        this.sendButton.addEventListener('click', () => {
            this.sendTextMessage();
        });
        
        this.clearButton.addEventListener('click', () => {
            this.clearChat();
        });
    }
    
    updateSendButton() {
        const hasText = this.textInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isProcessing;
    }
    
    async sendTextMessage() {
        const text = this.textInput.value.trim();
        if (!text || this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.updateSendButton();
            
            // Add user message to chat
            this.addMessage('user', text);
            this.textInput.value = '';
            
            // Keep avatar playing idle frames while processing (no interruption)
            // Don't show "thinking" animation, let video continue smoothly
            
            // Send to API
            const response = await apiClient.sendTextMessage(text);
            
            // Add bot response to chat
            if (response.response_text) {
                this.addMessage('bot', response.response_text);
                
                // Play avatar video if available and enabled (this includes TTS)
                if (response.video_frames && response.video_frames.length > 0 && config.get('avatarEnabled')) {
                    try {
                        // For synchronized playback, start audio and video together
                        if (response.audio_data && config.get('autoSpeak')) {
                            // Calculate expected duration from video frames and frame rate
                            const frameRate = 25; // Match backend FPS
                            const expectedDuration = response.video_frames.length / frameRate;
                            
                            // Start both audio and video simultaneously for perfect sync
                            const audioPromise = audioManager.playTTSAudio(response.audio_data, 24000);
                            const videoPromise = avatarManager.playVideoFrames(response.video_frames, false, expectedDuration);
                            
                            // Wait for both to complete
                            await Promise.all([audioPromise, videoPromise]);
                        } else {
                            // Video only without audio
                            await avatarManager.playVideoFrames(response.video_frames);
                        }
                    } catch (error) {
                        console.error('Failed to play synchronized avatar:', error);
                    }
                } else {
                    // Fallback: play TTS audio only if no video frames
                    if (response.audio_data && config.get('autoSpeak')) {
                        try {
                            await audioManager.playTTSAudio(response.audio_data, 24000);
                        } catch (error) {
                            console.error('Failed to play TTS audio:', error);
                            this.showError('Nie udało się odtworzyć dźwięku');
                        }
                    }
                }
            } else {
                this.addMessage('bot', 'Przepraszam, wystąpił problem z generowaniem odpowiedzi.');
            }
            
        } catch (error) {
            console.error('Failed to send text message:', error);
            this.addMessage('bot', 'Przepraszam, wystąpił błąd podczas przetwarzania wiadomości.');
            this.showError('Błąd komunikacji z serwerem');
        } finally {
            this.isProcessing = false;
            this.updateSendButton();
        }
    }
    
    async sendVoiceMessage(audioBlob) {
        if (!audioBlob || this.isProcessing) return;
        
        try {
            this.isProcessing = true;
            this.updateSendButton();
            
            // Add voice message indicator to chat
            this.addMessage('user', '🎤 Wiadomość głosowa', true);
            
            // Keep avatar playing idle frames while processing (no interruption)
            // Don't show "thinking" animation, let video continue smoothly
            
            // Send to API
            const response = await apiClient.sendAudioMessage(audioBlob);
            
            // Update user message with transcribed text
            if (response.transcribed_text) {
                this.updateLastMessage('user', response.transcribed_text);
            }
            
            // Add bot response to chat
            if (response.response_text) {
                this.addMessage('bot', response.response_text);
                
                // Play avatar video if available and enabled (this includes TTS)
                if (response.video_frames && response.video_frames.length > 0 && config.get('avatarEnabled')) {
                    try {
                        // For synchronized playback, start audio and video together
                        if (response.audio_data && config.get('autoSpeak')) {
                            // Calculate expected duration from video frames and frame rate
                            const frameRate = 25; // Match backend FPS
                            const expectedDuration = response.video_frames.length / frameRate;
                            
                            // Start both audio and video simultaneously for perfect sync
                            const audioPromise = audioManager.playTTSAudio(response.audio_data, 24000);
                            const videoPromise = avatarManager.playVideoFrames(response.video_frames, false, expectedDuration);
                            
                            // Wait for both to complete
                            await Promise.all([audioPromise, videoPromise]);
                        } else {
                            // Video only without audio
                            await avatarManager.playVideoFrames(response.video_frames);
                        }
                    } catch (error) {
                        console.error('Failed to play synchronized avatar:', error);
                    }
                } else {
                    // Fallback: play TTS audio only if no video frames
                    if (response.audio_data && config.get('autoSpeak')) {
                        try {
                            await audioManager.playTTSAudio(response.audio_data, 24000);
                        } catch (error) {
                            console.error('Failed to play TTS audio:', error);
                            this.showError('Nie udało się odtworzyć dźwięku');
                        }
                    }
                }
            } else {
                this.addMessage('bot', 'Przepraszam, nie zrozumiałem Twojej wiadomości głosowej.');
            }
            
        } catch (error) {
            console.error('Failed to send voice message:', error);
            this.addMessage('bot', 'Przepraszam, wystąpił błąd podczas przetwarzania wiadomości głosowej.');
            this.showError('Błąd przetwarzania dźwięku');
        } finally {
            this.isProcessing = false;
            this.updateSendButton();
        }
    }
    
    addMessage(sender, text, isVoice = false) {
        const messageId = Date.now() + Math.random();
        const message = {
            id: messageId,
            sender,
            text,
            timestamp: new Date(),
            isVoice
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }
    
    updateLastMessage(sender, newText) {
        const lastMessage = this.messages.findLast(m => m.sender === sender);
        if (lastMessage) {
            lastMessage.text = newText;
            lastMessage.isVoice = false;
            
            // Re-render the message
            const messageElement = this.messagesContainer.querySelector(`[data-message-id="${lastMessage.id}"]`);
            if (messageElement) {
                const contentElement = messageElement.querySelector('.message-content p');
                if (contentElement) {
                    contentElement.textContent = newText;
                }
            }
        }
    }
    
    renderMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}-message`;
        messageElement.setAttribute('data-message-id', message.id);
        
        const avatarIcon = message.sender === 'bot' ? 'fa-robot' : 'fa-user';
        const timeString = this.formatTime(message.timestamp);
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(message.text)}</p>
                <span class="message-time">${timeString}</span>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
    }
    
    formatTime(date) {
        return date.toLocaleTimeString('pl-PL', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    clearChat() {
        if (confirm('Czy na pewno chcesz wyczyścić chat?')) {
            this.messages = [];
            this.messagesContainer.innerHTML = `
                <div class="message bot-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <p>Chat został wyczyszczony. Jak mogę ci pomóc?</p>
                        <span class="message-time">${this.formatTime(new Date())}</span>
                    </div>
                </div>
            `;
        }
    }
    
    showError(message) {
        const errorToast = document.getElementById('errorToast');
        const errorMessage = document.getElementById('errorMessage');
        
        errorMessage.textContent = message;
        errorToast.style.display = 'block';
        
        setTimeout(() => {
            errorToast.style.display = 'none';
        }, 5000);
    }
    
    setProcessing(processing) {
        this.isProcessing = processing;
        this.updateSendButton();
        
        if (processing) {
            this.textInput.disabled = true;
            this.textInput.placeholder = 'Przetwarzanie...';
        } else {
            this.textInput.disabled = false;
            this.textInput.placeholder = 'Napisz wiadomość...';
        }
    }
}

// Initialize global chat manager
window.chatManager = new ChatManager();
