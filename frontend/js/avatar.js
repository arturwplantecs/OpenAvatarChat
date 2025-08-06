// Avatar display and animation handler
class AvatarManager {
    constructor() {
        this.avatarContainer = document.getElementById('avatarContainer');
        this.avatarPlaceholder = document.getElementById('avatarPlaceholder');
        this.avatarVideo = document.getElementById('avatarVideo');
        this.avatarCanvas = document.getElementById('avatarCanvas');
        
        this.isInitialized = false;
        this.isPlaying = false;
        this.currentFrames = [];
        this.frameIndex = 0;
        this.animationId = null;
        this.fps = 25; // Match API configuration
        
        this.canvasContext = null;
        this.initializeCanvas();
    }
    
    initializeCanvas() {
        try {
            this.canvasContext = this.avatarCanvas.getContext('2d');
            
            // Set canvas size to match container
            const resizeCanvas = () => {
                const rect = this.avatarContainer.getBoundingClientRect();
                this.avatarCanvas.width = rect.width;
                this.avatarCanvas.height = rect.height;
            };
            
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            
            console.log('Avatar canvas initialized');
        } catch (error) {
            console.error('Failed to initialize avatar canvas:', error);
        }
    }
    
    async initialize() {
        try {
            this.updateStatus('Inicjalizacja avatara...');
            
            // Simulate avatar initialization
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showPlaceholder();
            this.isInitialized = true;
            
            this.updateStatus('Avatar gotowy');
            console.log('Avatar manager initialized');
            
            return true;
        } catch (error) {
            console.error('Failed to initialize avatar:', error);
            this.updateStatus('Błąd avatara', 'error');
            throw error;
        }
    }
    
    showPlaceholder() {
        this.avatarPlaceholder.style.display = 'flex';
        this.avatarVideo.style.display = 'none';
        this.avatarCanvas.style.display = 'none';
        
        this.avatarPlaceholder.innerHTML = `
            <i class="fas fa-user-circle"></i>
            <p>Avatar QUARI gotowy</p>
        `;
    }
    
    showCanvas() {
        this.avatarPlaceholder.style.display = 'none';
        this.avatarVideo.style.display = 'none';
        this.avatarCanvas.style.display = 'block';
    }
    
    showVideo() {
        this.avatarPlaceholder.style.display = 'none';
        this.avatarVideo.style.display = 'block';
        this.avatarCanvas.style.display = 'none';
    }
    
    async playVideoFrames(frames) {
        if (!frames || frames.length === 0) {
            console.log('No video frames to play');
            this.showPlaceholder();
            return;
        }
        
        try {
            this.currentFrames = frames;
            this.frameIndex = 0;
            this.showCanvas();
            
            this.updateStatus('Odtwarzanie animacji...');
            this.startFrameAnimation();
            
        } catch (error) {
            console.error('Failed to play video frames:', error);
            this.showPlaceholder();
        }
    }
    
    startFrameAnimation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        const frameDelay = 1000 / this.fps; // ms per frame
        let lastFrameTime = 0;
        
        const animate = (currentTime) => {
            if (currentTime - lastFrameTime >= frameDelay) {
                this.renderFrame();
                lastFrameTime = currentTime;
                
                this.frameIndex++;
                if (this.frameIndex >= this.currentFrames.length) {
                    // Loop animation or stop
                    this.frameIndex = 0;
                    this.stopAnimation();
                    return;
                }
            }
            
            this.animationId = requestAnimationFrame(animate);
        };
        
        this.isPlaying = true;
        this.animationId = requestAnimationFrame(animate);
    }
    
    stopAnimation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        this.isPlaying = false;
        this.updateStatus('Avatar gotowy');
        
        // Return to placeholder after animation
        setTimeout(() => {
            if (!this.isPlaying) {
                this.showPlaceholder();
            }
        }, 500);
    }
    
    renderFrame() {
        if (!this.canvasContext || !this.currentFrames[this.frameIndex]) {
            return;
        }
        
        try {
            const frameData = this.currentFrames[this.frameIndex];
            
            // Decode base64 frame
            const img = new Image();
            img.onload = () => {
                // Clear canvas
                this.canvasContext.clearRect(0, 0, this.avatarCanvas.width, this.avatarCanvas.height);
                
                // Draw frame to canvas
                this.canvasContext.drawImage(
                    img, 
                    0, 0, 
                    this.avatarCanvas.width, 
                    this.avatarCanvas.height
                );
            };
            
            img.src = `data:image/jpeg;base64,${frameData}`;
            
        } catch (error) {
            console.error('Failed to render frame:', error);
        }
    }
    
    displayThinkingAnimation() {
        if (!this.isInitialized) return;
        
        this.showPlaceholder();
        this.updateStatus('Myślę...');
        
        // Animate thinking indicator with pulsing brain
        this.avatarPlaceholder.innerHTML = `
            <i class="fas fa-brain fa-pulse" style="color: #f59e0b; font-size: 6rem;"></i>
            <p style="color: #f59e0b; font-weight: 600; font-size: 1.4rem; margin-top: 1rem;">QUARI myśli...</p>
            <div style="margin-top: 1rem;">
                <div style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #f59e0b; margin: 0 4px; animation: bounce 1.4s infinite; animation-delay: 0s;"></div>
                <div style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #f59e0b; margin: 0 4px; animation: bounce 1.4s infinite; animation-delay: 0.2s;"></div>
                <div style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #f59e0b; margin: 0 4px; animation: bounce 1.4s infinite; animation-delay: 0.4s;"></div>
            </div>
        `;
        
        // Add bounce animation style if not exists
        if (!document.getElementById('bounceStyle')) {
            const style = document.createElement('style');
            style.id = 'bounceStyle';
            style.textContent = `
                @keyframes bounce {
                    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    displaySpeakingAnimation() {
        if (!this.isInitialized) return;
        
        this.updateStatus('Mówię...');
        
        // Animate speaking indicator with sound waves
        this.avatarPlaceholder.innerHTML = `
            <i class="fas fa-volume-up" style="color: #22c55e; font-size: 6rem; animation: pulse 1s infinite;"></i>
            <p style="color: #22c55e; font-weight: 600; font-size: 1.4rem; margin-top: 1rem;">QUARI mówi...</p>
            <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 4px;">
                <div style="width: 4px; height: 30px; background: #22c55e; border-radius: 2px; animation: wave 1s infinite; animation-delay: 0s;"></div>
                <div style="width: 4px; height: 40px; background: #22c55e; border-radius: 2px; animation: wave 1s infinite; animation-delay: 0.1s;"></div>
                <div style="width: 4px; height: 35px; background: #22c55e; border-radius: 2px; animation: wave 1s infinite; animation-delay: 0.2s;"></div>
                <div style="width: 4px; height: 45px; background: #22c55e; border-radius: 2px; animation: wave 1s infinite; animation-delay: 0.3s;"></div>
                <div style="width: 4px; height: 30px; background: #22c55e; border-radius: 2px; animation: wave 1s infinite; animation-delay: 0.4s;"></div>
            </div>
        `;
        
        // Add wave animation style if not exists
        if (!document.getElementById('waveStyle')) {
            const style = document.createElement('style');
            style.id = 'waveStyle';
            style.textContent = `
                @keyframes wave {
                    0%, 100% { transform: scaleY(0.5); }
                    50% { transform: scaleY(1); }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    displayListeningAnimation() {
        if (!this.isInitialized) return;
        
        this.updateStatus('Słucham...');
        
        // Animate listening indicator with ear and sound waves
        this.avatarPlaceholder.innerHTML = `
            <i class="fas fa-ear-listen" style="color: #ef4444; font-size: 6rem; animation: pulse 1.5s infinite;"></i>
            <p style="color: #ef4444; font-weight: 600; font-size: 1.4rem; margin-top: 1rem;">QUARI słucha...</p>
            <div style="margin-top: 1rem;">
                <div style="display: inline-block; width: 12px; height: 12px; border: 2px solid #ef4444; border-radius: 50%; margin: 0 8px; animation: ripple 2s infinite; animation-delay: 0s;"></div>
                <div style="display: inline-block; width: 16px; height: 16px; border: 2px solid #ef4444; border-radius: 50%; margin: 0 8px; animation: ripple 2s infinite; animation-delay: 0.5s;"></div>
                <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid #ef4444; border-radius: 50%; margin: 0 8px; animation: ripple 2s infinite; animation-delay: 1s;"></div>
            </div>
        `;
        
        // Add ripple animation style if not exists
        if (!document.getElementById('rippleStyle')) {
            const style = document.createElement('style');
            style.id = 'rippleStyle';
            style.textContent = `
                @keyframes ripple {
                    0% { transform: scale(0.8); opacity: 1; }
                    100% { transform: scale(2); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    resetToIdle() {
        if (!this.isInitialized) return;
        
        this.stopAnimation();
        this.showPlaceholder();
        this.updateStatus('Avatar gotowy');
        
        this.avatarPlaceholder.innerHTML = `
            <i class="fas fa-user-circle"></i>
            <p>Avatar QUARI gotowy</p>
        `;
    }
    
    updateStatus(message, type = 'success') {
        const videoStatus = document.getElementById('videoStatus');
        if (videoStatus) {
            videoStatus.textContent = message;
            
            const statusItem = videoStatus.parentElement;
            statusItem.className = 'status-item';
            if (type === 'error') {
                statusItem.classList.add('error');
            } else if (type === 'warning') {
                statusItem.classList.add('warning');
            }
        }
    }
    
    setEnabled(enabled) {
        if (!enabled) {
            this.showPlaceholder();
            this.avatarPlaceholder.innerHTML = `
                <i class="fas fa-user-slash"></i>
                <p>Avatar wyłączony</p>
            `;
            this.updateStatus('Avatar wyłączony', 'warning');
        } else {
            this.resetToIdle();
        }
    }
    
    async cleanup() {
        this.stopAnimation();
        this.currentFrames = [];
        this.isInitialized = false;
    }
}

// Initialize global avatar manager
window.avatarManager = new AvatarManager();
