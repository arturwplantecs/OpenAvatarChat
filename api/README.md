# OpenAvatarChat API Backend

Independent backend API extracted from the OpenAvatarChat application for Polish language avatar conversations.

## Features

- **FastAPI-based REST API** with async support
- **WebSocket support** for real-time avatar conversations
- **Modular AI Pipeline**: VAD → ASR → LLM → TTS → Avatar
- **Session Management** with automatic cleanup
- **Health monitoring** and status endpoints
- **Configurable pipeline** via YAML files

## Quick Start

1. **Start the API server:**
   ```bash
   ./start_api.sh
   ```

2. **Access the API documentation:**
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

3. **Health Check:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

## API Endpoints

### Session Management
- `POST /api/v1/sessions` - Create a new chat session
- `GET /api/v1/sessions/{session_id}` - Get session info
- `DELETE /api/v1/sessions/{session_id}` - End a session

### Text Processing
- `POST /api/v1/sessions/{session_id}/text` - Send text message

### Real-time Communication
- `WebSocket /api/v1/sessions/{session_id}/ws` - WebSocket endpoint

### Monitoring
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/pipeline/status` - Detailed pipeline status

## WebSocket Protocol

The WebSocket endpoint supports the following message types:

### Client → Server

**Text Message:**
```json
{
  "type": "text_message",
  "text": "Cześć! Jak się masz?"
}
```

**Audio Chunk:**
```json
{
  "type": "audio_chunk", 
  "audio_data": "base64_encoded_audio_data"
}
```

**Configuration Update:**
```json
{
  "type": "config_update",
  "config": {
    "asr_config": {...},
    "llm_config": {...}
  }
}
```

### Server → Client

**Processing Started:**
```json
{
  "type": "processing_started",
  "timestamp": 1234567890.123
}
```

**Text Processed:**
```json
{
  "type": "text_processed",
  "input_text": "Cześć!",
  "response_text": "Cześć! Miło Cię poznać!",
  "audio_data": "base64_encoded_audio",
  "video_frames": ["base64_frame1", "base64_frame2"],
  "processing_time": 1.23
}
```

**Audio Processed:**
```json
{
  "type": "audio_processed", 
  "transcribed_text": "Jak się masz?",
  "response_text": "Dobrze, dziękuję!",
  "audio_data": "base64_encoded_audio",
  "video_frames": ["base64_frame1", "base64_frame2"],
  "processing_time": 2.45
}
```

**Error:**
```json
{
  "type": "error",
  "error": "processing_error",
  "message": "Error description"
}
```

## Configuration

The API uses environment variables for configuration:

```bash
# Server settings
AVATARCHAT_HOST=127.0.0.1
AVATARCHAT_PORT=8000
AVATARCHAT_DEBUG=false
AVATARCHAT_WORKERS=1

# Pipeline settings  
AVATARCHAT_PIPELINE_CONFIG_PATH=config/chat_with_faster_whisper_stable.yaml
AVATARCHAT_MAX_SESSIONS=100
AVATARCHAT_SESSION_TIMEOUT=3600

# Processing settings
AVATARCHAT_MAX_TEXT_LENGTH=1000
AVATARCHAT_PROCESSING_TIMEOUT=30
```

## Pipeline Components

The API processes input through these stages:

1. **VAD (Voice Activity Detection)** - SileroVAD
2. **ASR (Automatic Speech Recognition)** - FasterWhisper
3. **LLM (Large Language Model)** - OpenAI Compatible API
4. **TTS (Text-to-Speech)** - PiperTTS
5. **Avatar (Video Generation)** - LiteAvatar

## Example Usage

### Create Session and Send Text

```python
import requests
import websockets
import asyncio
import json

# Create session
response = requests.post("http://localhost:8000/api/v1/sessions")
session_id = response.json()["session_id"]

# Send text via HTTP
text_response = requests.post(
    f"http://localhost:8000/api/v1/sessions/{session_id}/text",
    json={"text": "Cześć! Jak się masz?"}
)
print(text_response.json())
```

### WebSocket Communication

```python
async def chat_with_avatar():
    # Create session first
    response = requests.post("http://localhost:8000/api/v1/sessions")
    session_id = response.json()["session_id"]
    
    # Connect to WebSocket
    uri = f"ws://localhost:8000/api/v1/sessions/{session_id}/ws"
    
    async with websockets.connect(uri) as websocket:
        # Send text message
        await websocket.send(json.dumps({
            "type": "text_message",
            "text": "Opowiedz mi coś ciekawego!"
        }))
        
        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Avatar: {data.get('response_text', '')}")

# Run the example
asyncio.run(chat_with_avatar())
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │ Session Manager │    │ Pipeline Service│
│                 │◄──►│                 │◄──►│                 │
│ • REST API      │    │ • Session CRUD  │    │ • VAD Handler   │
│ • WebSocket     │    │ • Cleanup       │    │ • ASR Handler   │  
│ • Health Check  │    │ • History       │    │ • LLM Handler   │
└─────────────────┘    └─────────────────┘    │ • TTS Handler   │
                                              │ • Avatar Handler│
┌─────────────────┐    ┌─────────────────┐    └─────────────────┘
│ WebSocket Manager│    │  Original Code  │
│                 │    │                 │
│ • Real-time     │◄──►│ • src/handlers/ │
│ • Message Types │    │ • src/chat_engine│
│ • Error Handling│    │ • Configuration │
└─────────────────┘    └─────────────────┘
```

## Dependencies

The API reuses the original OpenAvatarChat handlers and models. Make sure the following are available:

- **Models**: Place AI models in the `models/` directory
- **Configuration**: Pipeline config in `config/chat_with_faster_whisper_stable.yaml`
- **Original Handlers**: Located in `src/handlers/`

## Troubleshooting

1. **Import Errors**: Ensure the `src/` directory is in your Python path
2. **Model Not Found**: Download required models using the provided scripts
3. **Port in Use**: Change the port using `AVATARCHAT_PORT` environment variable
4. **WebSocket Issues**: Check firewall settings and CORS configuration

## Development

To run in development mode with auto-reload:

```bash
AVATARCHAT_DEBUG=true ./start_api.sh
```

This enables:
- Auto-reload on code changes
- Debug logging
- Detailed error messages

## Production Deployment

For production, consider:

1. **Use a reverse proxy** (nginx, Apache)
2. **Enable SSL** with proper certificates
3. **Set appropriate worker count** based on CPU cores
4. **Configure logging** for monitoring
5. **Set up health checks** for load balancers

Example nginx configuration:

```nginx
location /api/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```
