'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Mic, MicOff, Settings, Volume2, VolumeX } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface APIResponse {
  response_text?: string;
  video_frames?: string[];
  audio_data?: string;
  transcribed_text?: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [currentVideoFrames, setCurrentVideoFrames] = useState<string[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [currentFrameTiming, setCurrentFrameTiming] = useState(33); // Dynamic frame timing in ms (30 FPS default)
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [idleFrames, setIdleFrames] = useState<string[]>([]);
  const [isIdleLoop, setIsIdleLoop] = useState(false);
  const [showIdlePlaceholder, setShowIdlePlaceholder] = useState(true);
  const [pingPongDirection, setPingPongDirection] = useState(1); // 1 = forward, -1 = backward
  const [transitionFrames, setTransitionFrames] = useState(0); // For smooth transitions
  const [isStreamingFrames, setIsStreamingFrames] = useState(false);
  const [streamBuffer, setStreamBuffer] = useState<string[]>([]);
  const [streamAudioData, setStreamAudioData] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const breathingPhaseRef = useRef(0);
  const breathingOffsetRef = useRef({ x: 0, y: 0, scale: 1 });
  const lastBreathingUpdateRef = useRef(0);

  // API Configuration
  const API_URL = 'http://localhost:8000';

  // Load idle avatar frames from API
  const loadIdleAvatarFrames = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      console.log('Loading idle avatar frames...');
      
      const response = await fetch(`${API_URL}/api/v1/sessions/${sessionId}/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          text: '', 
          get_idle_frames: true,
          frame_count: 60 // 2.4 seconds at 25fps
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to load idle frames');
      }

      const data: APIResponse = await response.json();
      
      if (data.video_frames && data.video_frames.length > 0) {
        console.log(`Loaded ${data.video_frames.length} idle avatar frames`);
        setIdleFrames(data.video_frames);
        setShowIdlePlaceholder(false);
        
        // Start idle animation immediately
        startIdleAnimation(data.video_frames);
      } else {
        console.log('No idle frames received from API');
      }
    } catch (error) {
      console.error('Failed to load idle avatar frames:', error);
    }
  }, [sessionId]);

  // Start idle animation loop
  const startIdleAnimation = useCallback((frames: string[]) => {
    setCurrentVideoFrames(frames);
    setCurrentFrameIndex(0);
    setIsIdleLoop(true);
    setIsPlaying(true);
    setPingPongDirection(1); // Start moving forward
  }, []);

  // Start idle animation with smooth transition
  const startIdleAnimationWithTransition = useCallback((frames: string[]) => {
    setTransitionFrames(3); // 3 frames of transition blending
    setCurrentVideoFrames(frames);
    // Start from middle of idle sequence for natural look when returning from speech
    setCurrentFrameIndex(Math.floor(frames.length / 2));
    setIsIdleLoop(true);
    setIsPlaying(true);
    setPingPongDirection(1);
  }, []);

  // Initialize session and WebSocket when component mounts
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setIsLoading(true);
        
        // Initialize audio context for better browser compatibility
        if (!audioContext) {
          const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
          setAudioContext(ctx);
        }
        
        // Check API health
        const healthResponse = await fetch(`${API_URL}/api/v1/health`);
        if (!healthResponse.ok) {
          throw new Error('API not available');
        }
        
        // Create session
        const sessionResponse = await fetch(`${API_URL}/api/v1/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: 'web-user-' + Date.now(),
            session_name: 'Next.js Chat Session'
          }),
        });
        
        if (!sessionResponse.ok) {
          throw new Error('Failed to create session');
        }
        
        const sessionData = await sessionResponse.json();
        setSessionId(sessionData.session_id);
        setIsConnected(true);
        console.log('Session created:', sessionData.session_id);
        
        // Initialize WebSocket connection
        await initializeWebSocket(sessionData.session_id);
        
      } catch (error) {
        console.error('Failed to initialize session:', error);
        setIsConnected(false);
      } finally {
        setIsLoading(false);
      }
    };

    initializeSession();
    
    // Cleanup WebSocket on component unmount
    return () => {
      if (ws) {
        ws.close(1000, 'Component unmounting');
        setWs(null);
        setWsConnected(false);
      }
    };
  }, [audioContext]);

  // Initialize WebSocket connection
  const initializeWebSocket = async (sessionId: string) => {
    try {
      const wsUrl = `ws://localhost:8000/api/v1/sessions/${sessionId}/ws`;
      console.log('Connecting to WebSocket:', wsUrl);
      
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('✅ WebSocket connected');
        setWsConnected(true);
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
      websocket.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setWsConnected(false);
        setWs(null);
        
        // Attempt to reconnect after a delay
        if (event.code !== 1000) { // Not a normal closure
          setTimeout(() => {
            console.log('Attempting WebSocket reconnection...');
            initializeWebSocket(sessionId);
          }, 3000);
        }
      };
      
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setWsConnected(false);
    }
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    console.log('WebSocket message received:', data.type);
    
    switch (data.type) {
      case 'connection_established':
        console.log('✅ WebSocket connection established');
        break;
        
      case 'processing_started':
        console.log('🤔 Processing started...');
        setIsLoading(true);
        break;
        
      case 'text_processed':
        console.log('✅ Text processed, frames:', data.video_frames?.length || 0);
        handleProcessedResponse(data);
        break;
        
      case 'audio_processed':
        console.log('✅ Audio processed, frames:', data.video_frames?.length || 0);
        handleProcessedResponse(data);
        break;
        
      case 'error':
        console.error('❌ WebSocket error:', data.error_type, data.message);
        setIsLoading(false);
        break;
        
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  // Handle processed response from WebSocket
  const handleProcessedResponse = async (data: any) => {
    setIsLoading(false);
    
    if (data.response_text) {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response_text,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);

      // Play video and audio
      if (data.video_frames && data.video_frames.length > 0) {
        await playVideo(data.video_frames, data.audio_data);
      }
    }
  };

  // Load idle frames when session is ready
  useEffect(() => {
    if (sessionId && isConnected && wsConnected) {
      loadIdleAvatarFrames();
    }
  }, [sessionId, isConnected, wsConnected, loadIdleAvatarFrames]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // ORIGINAL APP canvas rendering logic - exact copy from avatar.js with organic breathing
  const renderFrame = useCallback((frameData: string, interpolationFactor?: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Update breathing animation for idle frames
    if (isIdleLoop) {
      const now = Date.now();
      if (now - lastBreathingUpdateRef.current > 100) { // Update breathing every 100ms for smoother, slower motion
        lastBreathingUpdateRef.current = now;
        breathingPhaseRef.current += 0.008; // Much slower breathing cycle - about 8 seconds per full cycle
        
        // Create very subtle organic movement - gentle breathing-like animation
        const breathingCycle = Math.sin(breathingPhaseRef.current);
        const secondaryMove = Math.sin(breathingPhaseRef.current * 1.3) * 0.3; // Subtle secondary movement
        
        breathingOffsetRef.current = {
          x: breathingCycle * 0.3 + secondaryMove * 0.1, // Very subtle horizontal drift
          y: breathingCycle * 0.5 + secondaryMove * 0.2, // Gentle vertical movement (breathing)
          scale: 1 + (breathingCycle * 0.002) + (secondaryMove * 0.001) // Micro scale changes
        };
      }
    }

    const img = new Image();
    img.onload = () => {
      // ORIGINAL APP LOGIC: Handle smooth transitions with blending
      if (transitionFrames > 0) {
        // During transition, blend with previous frame
        const transitionProgress = (3 - transitionFrames + 1) / 3;
        
        // Don't clear - draw new frame with calculated opacity
        ctx.globalAlpha = 0.3 + (0.7 * transitionProgress);
        ctx.globalCompositeOperation = 'source-over';
        
        setTransitionFrames(prev => prev - 1);
      } else {
        // ORIGINAL APP LOGIC: Normal rendering - avoid full clear for smoother look
        ctx.globalAlpha = 1.0;
        ctx.globalCompositeOperation = 'source-over';
        
        // ORIGINAL APP LOGIC: Only clear if this is a significantly different frame
        if (shouldClearCanvas()) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }

      // Apply organic breathing transformation for idle
      if (isIdleLoop) {
        ctx.save();
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        
        // Translate to center, apply breathing transformation, translate back
        ctx.translate(centerX + breathingOffsetRef.current.x, centerY + breathingOffsetRef.current.y);
        ctx.scale(breathingOffsetRef.current.scale, breathingOffsetRef.current.scale);
        ctx.translate(-centerX, -centerY);
      }

      // Draw frame to canvas - exact same approach as original
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      
      if (isIdleLoop) {
        ctx.restore(); // Restore transformation matrix
      }
      
      // Reset composite operation for next frame
      ctx.globalAlpha = 1.0;
      ctx.globalCompositeOperation = 'source-over';
    };
    
    img.src = `data:image/jpeg;base64,${frameData}`;
  }, [currentFrameIndex, isIdleLoop, transitionFrames]);

  // ORIGINAL APP LOGIC: Smart canvas clearing decision
  const shouldClearCanvas = useCallback(() => {
    // Only clear canvas when switching animation types or starting new sequence
    if (currentFrameIndex === 0 && transitionFrames === 0) {
      return true;
    }
    // For continuous animation within same sequence, don't clear
    return false;
  }, [currentFrameIndex, transitionFrames]);

  // ORIGINAL APP animation logic - direct copy from avatar.js startFrameAnimation()
  useEffect(() => {
    if (currentVideoFrames.length > 0 && isPlaying) {
      const frameDelay = isIdleLoop ? 250 : currentFrameTiming; // Much slower idle: 4 FPS (250ms) for very natural, calm look
      let lastFrameTime = 0;
      
      const animate = (currentTime: number) => {
        if (currentTime - lastFrameTime >= frameDelay) {
          renderFrame(currentVideoFrames[currentFrameIndex]);
          lastFrameTime = currentTime;
          
          // Debug timing for the first few frames
          if (currentFrameIndex < 5) {
            console.log(`📺 Frame ${currentFrameIndex} at ${currentTime.toFixed(1)}ms (delay: ${frameDelay}ms)`);
          }
          
          if (isIdleLoop) {
            // ORIGINAL APP LOGIC: Ping-pong animation for idle frames
            setCurrentFrameIndex(prev => {
              const nextIndex = prev + pingPongDirection;
              
              // Reverse direction at boundaries
              if (nextIndex >= currentVideoFrames.length - 1) {
                setPingPongDirection(-1);
                return currentVideoFrames.length - 1;
              } else if (nextIndex <= 0) {
                setPingPongDirection(1);
                return 0;
              }
              
              return nextIndex;
            });
          } else {
            // ORIGINAL APP LOGIC: Normal forward playback for speech/response frames
            setCurrentFrameIndex(prev => {
              const nextIndex = prev + 1;
              if (nextIndex >= currentVideoFrames.length) {
                // Animation completed - return to idle like original
                setIsPlaying(false);
                setTimeout(() => {
                  if (idleFrames.length > 0) {
                    startIdleAnimationWithTransition(idleFrames);
                  }
                }, 100);
                return 0;
              }
              return nextIndex;
            });
          }
        }
        
        // Continue animation
        animationFrameRef.current = requestAnimationFrame(animate);
      };
      
      // Start the animation loop
      animationFrameRef.current = requestAnimationFrame(animate);
      
      // Cleanup function
      return () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      };
    }
  }, [currentVideoFrames, isPlaying, isIdleLoop, pingPongDirection, currentFrameTiming, currentFrameIndex, renderFrame, setPingPongDirection, setIsPlaying, setCurrentFrameIndex, startIdleAnimationWithTransition, idleFrames]);

  // Canvas setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const updateCanvasSize = () => {
      // Set canvas back to 900px height as requested
      const height = Math.min(900, window.innerHeight * 0.9); // Back to 900px
      const width = height * (9 / 16); // 9:16 aspect ratio
      
      canvas.height = height;
      canvas.width = width;
      canvas.style.height = `${height}px`;
      canvas.style.width = `${width}px`;

      // Initial background
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#0f0f0f';
        ctx.fillRect(0, 0, width, height);
      }
    };

    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);
    return () => window.removeEventListener('resize', updateCanvasSize);
  }, []);

  // Create WAV file with proper headers (matching the working basic frontend)
  const createWAVFile = (pcmData: Uint8Array, sampleRate: number = 24000): ArrayBuffer => {
    const length = pcmData.length;
    const buffer = new ArrayBuffer(44 + length);
    const view = new DataView(buffer);
    
    // WAV header
    const writeString = (offset: number, string: string) => {
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
  };

  const playVideo = async (frames: string[], audioData?: string) => {
    // Smooth transition from idle to speech
    const wasIdle = isIdleLoop;
    
    // Stop idle animation and start speech animation with transition
    setIsIdleLoop(false);
    
    if (wasIdle) {
      // When transitioning from idle to speech, add smooth transition
      setTransitionFrames(3);
    }
    
    setCurrentVideoFrames(frames);
    setCurrentFrameIndex(0);
    setIsPlaying(true);
    setShowIdlePlaceholder(false);
    setPingPongDirection(1); // Reset ping-pong direction

    if (audioData && isAudioEnabled && audioRef.current) {
      try {
        console.log('Audio data length:', audioData.length);
        console.log('Video frames count:', frames.length);
        
        // Ensure audio context is resumed
        if (audioContext && audioContext.state === 'suspended') {
          await audioContext.resume();
          console.log('AudioContext resumed');
        }
        
        // Decode base64 audio data
        const binaryString = atob(audioData);
        const pcmData = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          pcmData[i] = binaryString.charCodeAt(i);
        }
        
        // Create proper WAV file with headers
        const wavBuffer = createWAVFile(pcmData, 24000);
        const audioBlob = new Blob([wavBuffer], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        console.log('Created WAV audio URL:', audioUrl);
        console.log('PCM data length:', pcmData.length);
        
        // Set audio source
        audioRef.current.src = audioUrl;
        
        // Wait for the audio to be loaded
        const loadPromise = new Promise<void>((resolve, reject) => {
          const audio = audioRef.current!;
          
          let timeoutId: NodeJS.Timeout;
          
          const onLoad = () => {
            console.log('WAV audio loaded successfully, duration:', audio.duration);
            clearTimeout(timeoutId);
            audio.removeEventListener('canplaythrough', onLoad);
            audio.removeEventListener('loadeddata', onLoad);
            audio.removeEventListener('error', onError);
            resolve();
          };
          
          const onError = (e: Event) => {
            console.error('WAV audio loading error:', e);
            console.error('Audio error details:', (e.target as HTMLAudioElement)?.error);
            clearTimeout(timeoutId);
            audio.removeEventListener('canplaythrough', onLoad);
            audio.removeEventListener('loadeddata', onLoad);
            audio.removeEventListener('error', onError);
            reject(new Error('Failed to load WAV audio'));
          };
          
          // Set timeout for loading
          timeoutId = setTimeout(() => {
            console.error('WAV audio loading timeout');
            audio.removeEventListener('canplaythrough', onLoad);
            audio.removeEventListener('loadeddata', onLoad);
            audio.removeEventListener('error', onError);
            reject(new Error('WAV audio loading timeout'));
          }, 5000);
          
          audio.addEventListener('canplaythrough', onLoad);
          audio.addEventListener('loadeddata', onLoad);
          audio.addEventListener('error', onError);
          audio.load();
        });
        
        await loadPromise;
        
        // ORIGINAL APP METHOD: Calculate FPS based on expected duration like the original
        const actualAudioDuration = audioRef.current.duration;
        const calculatedFPS = Math.max(15, Math.min(30, frames.length / actualAudioDuration));
        const frameDelay = 1000 / calculatedFPS;
        
        console.log(`� ORIGINAL APP METHOD:`);
        console.log(`   Audio duration: ${actualAudioDuration.toFixed(3)}s`);
        console.log(`   Video frames: ${frames.length}`);
        console.log(`   Calculated FPS: ${calculatedFPS.toFixed(1)} (clamped 15-30)`);
        console.log(`   Frame delay: ${frameDelay.toFixed(2)}ms per frame`);
        console.log(`   This matches original avatar.js logic exactly`);
        
        // Store the calculated frame timing using original method
        setCurrentFrameTiming(frameDelay);
        
        // Synchronize audio and video start
        console.log('🎬 Starting original-method synchronized playback...');
        const startTime = performance.now();
        
        // Start video animation immediately
        setCurrentFrameIndex(0);
        
        // Start audio playback
        try {
          await audioRef.current.play();
          console.log('🔊 Audio started at:', performance.now() - startTime, 'ms after sync point');
        } catch (playError) {
          console.warn('Direct play failed, trying with volume adjustment:', playError);
          audioRef.current.volume = 0.8;
          await audioRef.current.play();
          console.log('🔊 Audio started after retry at:', performance.now() - startTime, 'ms after sync point');
        }
        
        // Clean up URL after playing
        audioRef.current.onended = () => {
          URL.revokeObjectURL(audioUrl);
          console.log('🔊 Audio finished playing');
        };
        
      } catch (error) {
        console.error('Audio playback failed:', error);
        console.error('Error details:', {
          name: (error as Error).name,
          message: (error as Error).message,
          audioEnabled: isAudioEnabled,
          audioRef: !!audioRef.current,
          audioContextState: audioContext?.state
        });
        // Fallback to original app's default timing
        setCurrentFrameTiming(40); // 25 FPS like original
      }
    } else {
      // No audio, use original app's default timing
      console.log('🎬 Starting video-only playback with original timing...');
      setCurrentFrameTiming(40); // 25 FPS like original
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || !sessionId || !ws || !wsConnected) {
      console.warn('Cannot send message: missing requirements', {
        hasText: !!text.trim(),
        hasSession: !!sessionId,
        hasWs: !!ws,
        wsConnected
      });
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Send message via WebSocket
      const message = {
        type: 'text_message',
        text: text.trim(),
        timestamp: Date.now()
      };
      
      console.log('Sending WebSocket message:', message);
      ws.send(JSON.stringify(message));
      
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      setIsLoading(false);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Przepraszam, wystąpił błąd z połączeniem. Spróbuj ponownie.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioMessage(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioMessage = async (audioBlob: Blob) => {
    if (!sessionId) return;
    
    setIsLoading(true);

    const userMessage: Message = {
      id: Date.now().toString(),
      text: '[Wiadomość głosowa]',
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.wav');

      const response = await fetch(`${API_URL}/api/v1/sessions/${sessionId}/audio`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data: APIResponse = await response.json();

      // Update the user message with transcribed text
      if (data.transcribed_text) {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === userMessage.id
              ? { ...msg, text: data.transcribed_text! }
              : msg
          )
        );
      }

      if (data.response_text) {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response_text,
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, botMessage]);

        // Play video and audio
        if (data.video_frames && data.video_frames.length > 0) {
          await playVideo(data.video_frames, data.audio_data);
        }
      }
    } catch (error) {
      console.error('Error sending audio message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Przepraszam, wystąpił błąd podczas przetwarzania nagrania.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Enable audio context on first user interaction
    if (audioContext && audioContext.state === 'suspended') {
      audioContext.resume().then(() => {
        console.log('AudioContext resumed on user interaction');
      });
    }
    
    sendMessage(inputText);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex">
      {/* Avatar Section - Center */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="relative">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="relative"
          >
            <canvas
              ref={canvasRef}
              className="rounded-2xl shadow-2xl border border-gray-700"
              style={{
                filter: 'brightness(1.1) contrast(1.1)',
                boxShadow: '0 0 50px rgba(59, 130, 246, 0.3)',
                display: showIdlePlaceholder ? 'none' : 'block'
              }}
            />
            
            {/* Idle placeholder */}
            {showIdlePlaceholder && (
              <div className="flex flex-col items-center justify-center bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 p-8"
                   style={{
                     width: 'min(500px, 85vw)',  // Increased from 350px
                     height: 'min(700px, 85vh)', // Increased from 450px
                     maxHeight: '900px',         // Back to 900px
                     aspectRatio: '9/16',
                     boxShadow: '0 0 50px rgba(59, 130, 246, 0.3)',
                   }}>
                <motion.div
                  className="text-blue-400 mb-4"
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                >
                  <svg
                    className="w-24 h-24"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 9.5V7L7 11V13L15 17V14.5L21 17V15L17 13.5L21 12V10L17 8.5L21 9ZM3 13C3 11.9 3.9 11 5 11S7 11.9 7 13 6.1 15 5 15 3 14.1 3 13Z"/>
                  </svg>
                </motion.div>
                <h3 className="text-xl font-bold text-white mb-2">Avatar QUARI</h3>
                <p className="text-gray-400 text-center">
                  {!isConnected 
                    ? 'Łączenie z serwerem...' 
                    : !wsConnected
                    ? 'Łączenie WebSocket...'
                    : idleFrames.length === 0
                    ? 'Ładowanie avatara...'
                    : 'Gotowy do rozmowy'
                  }
                </p>
                {isConnected && !wsConnected && (
                  <motion.div 
                    className="flex space-x-1 mt-4"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </motion.div>
                )}
                {isConnected && wsConnected && idleFrames.length === 0 && (
                  <motion.div 
                    className="flex space-x-1 mt-4"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </motion.div>
                )}
              </div>
            )}
            
            {/* Status indicator */}
            <motion.div
              className={`absolute -bottom-3 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-full text-xs font-medium ${
                !isConnected || !wsConnected
                  ? 'bg-red-500 text-white'
                  : isPlaying
                  ? 'bg-green-500 text-white'
                  : isLoading
                  ? 'bg-yellow-500 text-white'
                  : 'bg-gray-700 text-gray-300'
              }`}
              animate={{ scale: isPlaying ? [1, 1.05, 1] : 1 }}
              transition={{ repeat: isPlaying ? Infinity : 0, duration: 2 }}
            >
              {!isConnected 
                ? 'Łączenie z API...' 
                : !wsConnected
                ? 'Łączenie WebSocket...'
                : isPlaying 
                ? 'Odpowiadam...' 
                : isLoading 
                ? 'Myślę...' 
                : 'Gotowy do rozmowy'
              }
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Chat Section - Right */}
      <div className="w-96 bg-gray-900/90 backdrop-blur-sm border-l border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-white">QUARI</h1>
            <div className="flex items-center gap-3">
              <button
                onClick={async () => {
                  // Enable audio context on user interaction
                  if (audioContext && audioContext.state === 'suspended') {
                    await audioContext.resume();
                    console.log('AudioContext resumed via audio button');
                  }
                  setIsAudioEnabled(!isAudioEnabled);
                }}
                className={`p-2 rounded-lg transition-colors ${
                  isAudioEnabled
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {isAudioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
              </button>
              <button className="p-2 bg-gray-700 text-gray-400 rounded-lg hover:bg-gray-600 transition-colors">
                <Settings size={16} />
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-400 mt-1">Twój inteligentny asystent AI</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white rounded-br-md'
                      : 'bg-gray-700 text-gray-100 rounded-bl-md'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.text}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString('pl-PL', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-gray-700 px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-700">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={isConnected && wsConnected ? "Napisz wiadomość..." : !isConnected ? "Łączenie z serwerem..." : "Łączenie WebSocket..."}
              className="flex-1 px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading || !isConnected || !wsConnected}
            />
            <button
              type="button"
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={stopRecording}
              className={`p-3 rounded-lg transition-colors ${
                isRecording
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              }`}
              disabled={isLoading || !isConnected || !wsConnected}
            >
              {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading || !isConnected || !wsConnected}
              className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={16} />
            </button>
          </form>
          <p className="text-xs text-gray-500 mt-2">
            Przytrzymaj mikrofon aby nagrać wiadomość głosową
          </p>
        </div>
      </div>

      {/* Hidden audio element */}
      <audio 
        ref={audioRef} 
        preload="auto"
        controls={false}
        style={{ display: 'none' }}
        playsInline
        autoPlay={false}
      />
    </div>
  );
}
