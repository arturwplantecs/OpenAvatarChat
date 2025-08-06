# OpenAvatarChat API Extraction Plan

## Overview

Based on my investigation of the OpenAvatarChat application, this plan outlines how to extract and create an independent backend API from the current Gradio/FastAPI-based application that requires manual user interaction steps.

## Current Application Architecture

### Main Components Analysis

1. **Entry Point**: `src/demo.py` - FastAPI app with embedded Gradio UI
2. **Chat Engine**: `src/chat_engine/chat_engine.py` - Core orchestration
3. **Handler System**: Modular pipeline components in `src/handlers/`
4. **WebRTC Client**: `src/handlers/client/rtc_client/client_handler_rtc.py`
5. **Third-party WebRTC**: `src/third_party/gradio_webrtc_videochat/`

### Current User Interaction Flow

1. User visits `/` → redirects to `/ui` (Gradio interface)
2. User clicks "Click to Access Webcam" 
3. User selects camera/mic and clicks "点击开始对话"
4. Avatar session starts with WebRTC connection
5. Audio/video/text processing pipeline begins

### Processing Pipeline

The application follows this data flow:
```
Audio Input → VAD → ASR → LLM → TTS → Avatar → Video/Audio Output
```

**Components:**
- **VAD**: `SileroVad` - Voice Activity Detection
- **ASR**: `FasterWhisper` - Speech-to-Text (Polish language)
- **LLM**: `OpenAI Compatible` - Text generation
- **TTS**: `PiperTTS` - Text-to-Speech (Polish)
- **Avatar**: `LiteAvatar` - Video generation with lip-sync

## API Extraction Strategy

### Phase 1: Core API Backend Creation

#### 1.1 Create Independent FastAPI Server
```
api/
├── main.py                 # FastAPI app entry point
├── models/                 # Data models
│   ├── __init__.py
│   ├── requests.py         # API request models
│   ├── responses.py        # API response models
│   └── chat.py            # Chat session models
├── services/              # Business logic
│   ├── __init__.py
│   ├── chat_service.py    # Main chat orchestration
│   ├── session_manager.py # Session lifecycle management
│   └── pipeline_service.py # AI pipeline management
├── handlers/              # Copy and adapt existing handlers
│   ├── __init__.py
│   ├── asr/              # Speech-to-Text
│   ├── llm/              # Language Model
│   ├── tts/              # Text-to-Speech
│   └── avatar/           # Avatar generation
├── config/               # Configuration
│   ├── __init__.py
│   ├── settings.py       # App settings
│   └── pipeline.yaml    # Pipeline configuration
└── utils/                # Utilities
    ├── __init__.py
    ├── audio.py          # Audio processing
    ├── video.py          # Video processing
    └── websocket.py      # WebSocket handling
```

#### 1.2 API Endpoints Design

**Session Management:**
```python
POST /api/v1/sessions                    # Create new chat session
GET  /api/v1/sessions/{session_id}       # Get session info
DELETE /api/v1/sessions/{session_id}     # End session
```

**Real-time Communication:**
```python
WebSocket /api/v1/sessions/{session_id}/ws  # Main communication channel
```

**Media Processing:**
```python
POST /api/v1/sessions/{session_id}/audio    # Send audio chunk
POST /api/v1/sessions/{session_id}/text     # Send text message
GET  /api/v1/sessions/{session_id}/avatar   # Get avatar video stream
```

**Health & Status:**
```python
GET /api/v1/health                       # Service health check
GET /api/v1/pipeline/status              # Pipeline component status
```

### Phase 2: Handler Abstraction

#### 2.1 Extract Core Handlers
Copy and adapt these key handlers:
- `handlers/asr/faster_whisper/handler.py` → `api/handlers/asr/`
- `handlers/llm/openai_compatible/llm_handler_openai_compatible.py` → `api/handlers/llm/`
- `handlers/tts/pipertts/tts_handler_pipertts.py` → `api/handlers/tts/`
- `handlers/avatar/liteavatar/avatar_handler_liteavatar.py` → `api/handlers/avatar/`

#### 2.2 Create Handler Interface
```python
# api/handlers/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseHandler(ABC):
    @abstractmethod
    async def process(self, input_data: Any, context: Dict) -> Any:
        """Process input and return output"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict) -> None:
        """Initialize handler with configuration"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass
```

#### 2.3 Pipeline Service
```python
# api/services/pipeline_service.py
class PipelineService:
    def __init__(self):
        self.asr_handler = FasterWhisperHandler()
        self.llm_handler = OpenAICompatibleHandler()
        self.tts_handler = PiperTTSHandler()
        self.avatar_handler = LiteAvatarHandler()
    
    async def process_audio(self, audio_data: bytes, session_id: str) -> Dict:
        # VAD → ASR → LLM → TTS → Avatar pipeline
        pass
    
    async def process_text(self, text: str, session_id: str) -> Dict:
        # LLM → TTS → Avatar pipeline
        pass
```

### Phase 3: WebSocket Communication

#### 3.1 WebSocket Protocol Design
```python
# Message Types
{
    "type": "audio_chunk",
    "data": "<base64_encoded_audio>",
    "session_id": "uuid",
    "timestamp": 1234567890
}

{
    "type": "text_message", 
    "data": "Hello, how are you?",
    "session_id": "uuid",
    "timestamp": 1234567890
}

{
    "type": "avatar_frame",
    "data": "<base64_encoded_video_frame>",
    "session_id": "uuid", 
    "timestamp": 1234567890,
    "frame_id": 123
}

{
    "type": "audio_response",
    "data": "<base64_encoded_audio>",
    "session_id": "uuid",
    "timestamp": 1234567890
}

{
    "type": "text_response",
    "data": "I'm doing well, thank you!",
    "session_id": "uuid",
    "timestamp": 1234567890,
    "is_final": true
}

{
    "type": "error",
    "message": "Processing failed",
    "code": "PROCESSING_ERROR",
    "session_id": "uuid"
}
```

#### 3.2 WebSocket Handler
```python
# api/utils/websocket.py
class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.pipeline_service = PipelineService()
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.connections[session_id] = websocket
        await self.start_session(session_id)
    
    async def handle_message(self, message: Dict, session_id: str):
        if message["type"] == "audio_chunk":
            await self.process_audio(message["data"], session_id)
        elif message["type"] == "text_message":
            await self.process_text(message["data"], session_id)
    
    async def send_avatar_frame(self, frame_data: bytes, session_id: str):
        # Send video frame to client
        pass
```

### Phase 4: Configuration Management

#### 4.1 Configuration Structure
```yaml
# api/config/pipeline.yaml
pipeline:
  asr:
    handler: "faster_whisper"
    model_size: "large-v3"
    language: "pl"
    device: "cuda"
    
  llm:
    handler: "openai_compatible"
    model_name: "gpt-4o-mini"
    api_url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"
    
  tts:
    handler: "pipertts"
    model_path: "models/piper/pl_PL-gosia-medium.onnx"
    sample_rate: 24000
    
  avatar:
    handler: "liteavatar"
    avatar_name: "20250408/P1-hDQRxa5xfpZK-1yDX8PrQ"
    fps: 25
    enable_fast_mode: true

server:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["*"]
  
models:
  root_path: "models"
  cache_size: 1000
```

#### 4.2 Settings Management
```python
# api/config/settings.py
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["*"]
    
    # Pipeline settings
    pipeline_config_path: str = "api/config/pipeline.yaml"
    models_root_path: str = "models"
    
    # OpenAI settings
    openai_api_key: str = ""
    openai_api_url: str = "https://api.openai.com/v1"
    
    class Config:
        env_file = ".env"
        env_prefix = "AVATAR_"

settings = Settings()
```

### Phase 5: Client Integration

#### 5.1 JavaScript Client Library
```javascript
// client/avatar-client.js
class AvatarChatClient {
    constructor(baseUrl, sessionId) {
        this.baseUrl = baseUrl;
        this.sessionId = sessionId;
        this.websocket = null;
        this.audioContext = null;
        this.mediaRecorder = null;
    }
    
    async connect() {
        const wsUrl = `${this.baseUrl}/api/v1/sessions/${this.sessionId}/ws`;
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
    }
    
    async startAudioCapture() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.setupAudioRecording(stream);
    }
    
    sendText(text) {
        this.websocket.send(JSON.stringify({
            type: "text_message",
            data: text,
            session_id: this.sessionId,
            timestamp: Date.now()
        }));
    }
    
    handleMessage(message) {
        switch (message.type) {
            case "avatar_frame":
                this.displayAvatarFrame(message.data);
                break;
            case "audio_response":
                this.playAudio(message.data);
                break;
            case "text_response":
                this.displayText(message.data);
                break;
        }
    }
}
```

#### 5.2 React Component Example
```jsx
// client/components/AvatarChat.jsx
import React, { useEffect, useState, useRef } from 'react';
import { AvatarChatClient } from '../avatar-client';

const AvatarChat = () => {
    const [client, setClient] = useState(null);
    const [sessionId, setSessionId] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const videoRef = useRef(null);
    
    useEffect(() => {
        async function initializeSession() {
            const response = await fetch('/api/v1/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const session = await response.json();
            setSessionId(session.session_id);
            
            const avatarClient = new AvatarChatClient('ws://localhost:8000', session.session_id);
            await avatarClient.connect();
            setClient(avatarClient);
            setIsConnected(true);
        }
        
        initializeSession();
    }, []);
    
    const handleSendMessage = (text) => {
        if (client) {
            client.sendText(text);
        }
    };
    
    return (
        <div className="avatar-chat">
            <video ref={videoRef} autoPlay muted />
            <ChatInput onSendMessage={handleSendMessage} />
            <StatusIndicator connected={isConnected} />
        </div>
    );
};
```

### Phase 6: Deployment & Documentation

#### 6.1 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY api/ /app/api/
COPY models/ /app/models/
WORKDIR /app

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 6.2 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  avatar-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AVATAR_OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./models:/app/models
      - ./config:/app/config
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - avatar-api
```

## Implementation Timeline

### Week 1: Foundation
- [ ] Create basic FastAPI server structure
- [ ] Implement session management endpoints
- [ ] Set up WebSocket communication
- [ ] Create basic data models

### Week 2: Handler Integration
- [ ] Extract and adapt ASR handler (FasterWhisper)
- [ ] Extract and adapt LLM handler (OpenAI Compatible)
- [ ] Extract and adapt TTS handler (PiperTTS)
- [ ] Create pipeline service

### Week 3: Avatar Integration
- [ ] Extract and adapt LiteAvatar handler
- [ ] Implement video streaming
- [ ] Integrate full pipeline (Audio → Text → Avatar)
- [ ] Add error handling and recovery

### Week 4: Client & Testing
- [ ] Create JavaScript client library
- [ ] Build React demo component
- [ ] Write comprehensive tests
- [ ] Create API documentation
- [ ] Performance optimization

### Week 5: Production Readiness
- [ ] Docker containerization
- [ ] Load testing and optimization
- [ ] Security hardening
- [ ] Monitoring and logging
- [ ] Deployment documentation

## API Advantages

### Current Limitations Solved:
1. **Manual Interaction**: API removes need for manual webcam/mic setup
2. **UI Coupling**: Backend logic separated from UI presentation
3. **Scalability**: Can handle multiple concurrent sessions
4. **Integration**: Easy to embed in existing applications
5. **Flexibility**: Different clients can use same backend

### New Capabilities:
1. **REST API**: Traditional HTTP endpoints for session management
2. **WebSocket**: Real-time bidirectional communication
3. **Multi-client**: Support for web, mobile, desktop clients
4. **Headless**: Run without UI for server-side integrations
5. **Configurable**: Flexible pipeline configuration

## Dependencies to Extract

### Core Libraries:
```
fastapi>=0.104.1
uvicorn>=0.24.0
websockets>=12.0
pydantic>=2.5.0
python-multipart>=0.0.6
```

### AI/ML Libraries:
```
torch>=2.1.0
faster-whisper>=0.10.0
openai>=1.0.0
librosa>=0.10.1
numpy>=1.24.0
soundfile>=0.12.1
```

### From Original App:
- Copy entire `src/handlers/` structure
- Copy `src/chat_engine/` core logic
- Copy model configurations from `config/`
- Copy necessary utilities from `src/engine_utils/`

## Security Considerations

1. **API Keys**: Secure storage and management of LLM API keys
2. **Rate Limiting**: Prevent abuse of expensive AI operations
3. **Session Management**: Secure session tokens and cleanup
4. **Input Validation**: Sanitize all audio/text inputs
5. **CORS**: Proper cross-origin request handling
6. **WebSocket Security**: Authentication and authorization

## Monitoring & Observability

1. **Metrics**: Track processing times, error rates, active sessions
2. **Logging**: Structured logging for debugging and audit
3. **Health Checks**: Endpoint health and dependency status
4. **Performance**: Real-time performance monitoring
5. **Alerts**: Automated alerting for failures and anomalies

This plan provides a comprehensive roadmap for extracting a production-ready API from the existing OpenAvatarChat application while maintaining all its AI capabilities and removing the manual interaction requirements.
