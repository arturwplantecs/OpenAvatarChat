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
        
        // For smooth transitions
        this.lastRenderedFrame = null;
        this.previousFrameIndex = -1;
        this.transitionFrames = 0; // Number of frames to blend during transition
        
        this.canvasContext = null;
        this.initializeCanvas();
    }
    
    initializeCanvas() {
        try {
            this.canvasContext = this.avatarCanvas.getContext('2d');
            
            // Set canvas size to match avatar video format (9:16 aspect ratio, 1024x1408)
            const resizeCanvas = () => {
                // Force recalculation by getting fresh container bounds
                const rect = this.avatarContainer.getBoundingClientRect();
                const containerWidth = rect.width - 16; // Minimal padding for maximum space
                const containerHeight = rect.height - 16;
                
                // Calculate size to fit 9:16 aspect ratio within container
                const targetAspectRatio = 9 / 16; // width / height
                let canvasWidth, canvasHeight;
                
                if (containerWidth / containerHeight > targetAspectRatio) {
                    // Container is wider than needed, fit to height
                    canvasHeight = containerHeight;
                    canvasWidth = canvasHeight * targetAspectRatio;
                } else {
                    // Container is taller than needed, fit to width
                    canvasWidth = containerWidth;
                    canvasHeight = canvasWidth / targetAspectRatio;
                }
                
                // Ensure minimum size but respect container constraints
                canvasWidth = Math.max(200, Math.min(canvasWidth, containerWidth));
                canvasHeight = Math.max(300, Math.min(canvasHeight, containerHeight));
                
                // Set canvas internal resolution
                this.avatarCanvas.width = canvasWidth;
                this.avatarCanvas.height = canvasHeight;
                
                // Force CSS size to match exactly - prevent zoom artifacts
                this.avatarCanvas.style.width = `${canvasWidth}px`;
                this.avatarCanvas.style.height = `${canvasHeight}px`;
                this.avatarCanvas.style.maxWidth = `${containerWidth}px`;
                this.avatarCanvas.style.maxHeight = `${containerHeight}px`;
                
                console.log(`Canvas resized to: ${canvasWidth}x${canvasHeight} (container: ${containerWidth}x${containerHeight})`);
            };
            
            // Initial resize with a delay to ensure DOM is ready
            setTimeout(() => {
                resizeCanvas();
            }, 100);
            
            // Resize on window resize with debouncing
            let resizeTimeout;
            const debouncedResize = () => {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    resizeCanvas();
                }, 150);
            };
            
            window.addEventListener('resize', debouncedResize);
            
            // Also listen for zoom changes
            window.addEventListener('orientationchange', debouncedResize);
            
            // Listen for page visibility changes to fix zoom issues
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    setTimeout(() => {
                        resizeCanvas();
                    }, 100);
                }
            });
            
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
        
        // Force canvas resize when showing to fix zoom issues
        setTimeout(() => {
            this.refreshCanvasSize();
        }, 50);
    }
    
    refreshCanvasSize() {
        // Manually trigger canvas resize to fix zoom artifacts
        if (this.avatarContainer && this.avatarCanvas) {
            const rect = this.avatarContainer.getBoundingClientRect();
            const containerWidth = rect.width - 16;
            const containerHeight = rect.height - 16;
            
            const targetAspectRatio = 9 / 16;
            let canvasWidth, canvasHeight;
            
            if (containerWidth / containerHeight > targetAspectRatio) {
                canvasHeight = containerHeight;
                canvasWidth = canvasHeight * targetAspectRatio;
            } else {
                canvasWidth = containerWidth;
                canvasHeight = canvasWidth / targetAspectRatio;
            }
            
            canvasWidth = Math.max(200, Math.min(canvasWidth, containerWidth));
            canvasHeight = Math.max(300, Math.min(canvasHeight, containerHeight));
            
            this.avatarCanvas.width = canvasWidth;
            this.avatarCanvas.height = canvasHeight;
            this.avatarCanvas.style.width = `${canvasWidth}px`;
            this.avatarCanvas.style.height = `${canvasHeight}px`;
            this.avatarCanvas.style.maxWidth = `${containerWidth}px`;
            this.avatarCanvas.style.maxHeight = `${containerHeight}px`;
            
            console.log(`Canvas refreshed to: ${canvasWidth}x${canvasHeight}`);
        }
    }
    
    showVideo() {
        this.avatarPlaceholder.style.display = 'none';
        this.avatarVideo.style.display = 'block';
        this.avatarCanvas.style.display = 'none';
    }
    
    async playVideoFrames(frames, isIdleLoop = false, expectedDuration = null) {
        if (!frames || frames.length === 0) {
            console.log('No video frames to play, continuing idle animation');
            return;
        }
        
        return new Promise((resolve) => {
            try {
                // Store previous animation state for smooth transition
                const wasIdle = this.isIdleLoop;
                const previousFrames = this.currentFrames;
                const previousIndex = this.frameIndex;
                
                this.currentFrames = frames;
                this.isIdleLoop = isIdleLoop;
                this.showCanvas();
                
                // Calculate frame rate based on expected duration if provided
                if (expectedDuration && !isIdleLoop) {
                    this.fps = Math.max(15, Math.min(30, frames.length / expectedDuration));
                    console.log(`Adjusting FPS to ${this.fps} for duration ${expectedDuration}s`);
                } else {
                    this.fps = 25; // Default FPS
                }
                
                // For smooth transitions: start from a logical frame index
                if (!isIdleLoop && wasIdle && previousFrames.length > 0) {
                    // When transitioning from idle to speech, start from frame 0
                    this.frameIndex = 0;
                    this.transitionFrames = 3; // Blend first 3 frames for smooth transition
                } else if (isIdleLoop && !wasIdle) {
                    // When returning to idle, start from middle of idle sequence for natural look
                    this.frameIndex = Math.floor(frames.length / 2);
                    this.transitionFrames = 3; // Blend first 3 frames
                } else {
                    // Normal case
                    this.frameIndex = 0;
                    this.transitionFrames = 0;
                }
                
                // Don't update status - let video play uninterrupted
                this.startFrameAnimation(resolve, isIdleLoop);
                
            } catch (error) {
                console.error('Failed to play video frames:', error);
                resolve(); // Resolve even on error
            }
        });
    }
    
    startFrameAnimation(resolveCallback = null, isIdleLoop = false) {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        const frameDelay = 1000 / this.fps; // ms per frame
        let lastFrameTime = 0;
        
        // Initialize ping-pong direction for idle loops
        if (this.isIdleLoop && this.pingPongDirection === undefined) {
            this.pingPongDirection = 1; // 1 = forward, -1 = backward
        }
        
        const animate = (currentTime) => {
            if (currentTime - lastFrameTime >= frameDelay) {
                this.renderFrame();
                lastFrameTime = currentTime;
                
                if (this.isIdleLoop) {
                    // Ping-pong animation for idle frames
                    this.frameIndex += this.pingPongDirection;
                    
                    // Reverse direction at boundaries
                    if (this.frameIndex >= this.currentFrames.length - 1) {
                        this.pingPongDirection = -1;
                        this.frameIndex = this.currentFrames.length - 1;
                    } else if (this.frameIndex <= 0) {
                        this.pingPongDirection = 1;
                        this.frameIndex = 0;
                    }
                } else {
                    // Normal forward playback for speech/response frames
                    this.frameIndex++;
                    if (this.frameIndex >= this.currentFrames.length) {
                        // Animation completed - notify completion and return to idle
                        this.frameIndex = 0;
                        this.stopAnimation();
                        if (resolveCallback) {
                            resolveCallback();
                        }
                        return;
                    }
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
        this.isIdleLoop = false;
        this.pingPongDirection = undefined;
        
        // Automatically return to idle animation after speaking
        // Don't show placeholder - maintain video flow
        setTimeout(() => {
            if (!this.isPlaying && this.idleFrames && this.idleFrames.length > 0) {
                this.playVideoFrames(this.idleFrames, true); // Set as idle loop
            }
        }, 100);
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
                // Use smooth rendering instead of clearing
                if (this.transitionFrames > 0) {
                    // During transition, blend with previous frame
                    const transitionProgress = (3 - this.transitionFrames + 1) / 3;
                    
                    // Don't clear - draw new frame with calculated opacity
                    this.canvasContext.globalAlpha = 0.3 + (0.7 * transitionProgress);
                    this.canvasContext.globalCompositeOperation = 'source-over';
                    
                    this.transitionFrames--;
                } else {
                    // Normal rendering - still avoid full clear for smoother look
                    this.canvasContext.globalAlpha = 1.0;
                    this.canvasContext.globalCompositeOperation = 'source-over';
                    
                    // Only clear if this is a significantly different frame
                    if (this.shouldClearCanvas()) {
                        this.canvasContext.clearRect(0, 0, this.avatarCanvas.width, this.avatarCanvas.height);
                    }
                }
                
                // Draw frame to canvas
                this.canvasContext.drawImage(
                    img, 
                    0, 0, 
                    this.avatarCanvas.width, 
                    this.avatarCanvas.height
                );
                
                // Reset composite operation for next frame
                this.canvasContext.globalAlpha = 1.0;
                this.canvasContext.globalCompositeOperation = 'source-over';
                
                // Store this frame for potential future blending
                this.lastRenderedFrame = frameData;
                this.previousFrameIndex = this.frameIndex;
            };
            
            img.src = `data:image/jpeg;base64,${frameData}`;
            
        } catch (error) {
            console.error('Failed to render frame:', error);
        }
    }
    
    shouldClearCanvas() {
        // Only clear canvas when switching animation types or starting new sequence
        if (this.frameIndex === 0 && this.transitionFrames === 0) {
            return true;
        }
        // For continuous animation within same sequence, don't clear
        return false;
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
