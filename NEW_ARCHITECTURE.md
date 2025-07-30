# OpenAvatarChat - New Architecture Implementation

This document describes the implementation of the redesigned OpenAvatarChat application based on the requirements in `INSTRUCTIONS.md`.

## Architecture Overview

The application has been redesigned with a clear separation between frontend and backend:

### Frontend (Next.js + React)
- **Framework**: Next.js 14 with TypeScript
- **UI Library**: React with Tailwind CSS
- **Communication**: WebSocket + HTTP API
- **Real-time Features**: Socket.io-client for WebSocket communication

### Backend (Python)
- **Framework**: FastAPI with WebSocket support
- **Integration**: Maintains existing ChatEngine infrastructure
- **API**: RESTful endpoints + WebSocket for real-time communication

## Project Structure

```
OpenAvatarChat/
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # Next.js app directory
│   │   │   ├── layout.tsx      # Root layout component
│   │   │   ├── page.tsx        # Main application page
│   │   │   └── globals.css     # Global styles
│   │   ├── components/         # React components
│   │   │   ├── AvatarDisplay.tsx       # LiveAvatar integration
│   │   │   ├── WebcamPiP.tsx          # Picture-in-picture webcam
│   │   │   ├── ChatInterface.tsx       # Chat UI with voice/text
│   │   │   └── ControlPanel.tsx        # Audio/video controls
│   │   └── hooks/              # Custom React hooks
│   │       ├── useSocket.ts    # WebSocket connection management
│   │       └── useLiveAvatar.ts # LiveAvatar SDK integration
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.js
├── src/                        # Python backend (existing + new)
│   ├── websocket_server.py     # New WebSocket server
│   ├── handlers/
│   │   └── websocket_chat_handler.py  # WebSocket-ChatEngine bridge
│   └── ... (existing structure)
├── start_new_architecture.sh   # Startup script for both services
└── INSTRUCTIONS.md             # Original requirements
```

## Key Features Implemented

### 1. LiveAvatar Integration (Prepared)

**Component**: `src/components/AvatarDisplay.tsx`
- Vertical orientation with centered positioning
- Responsive design for different screen sizes
- Status indicators for listening/muted states
- Volume visualization
- Prepared for LiveAvatar SDK integration

**Hook**: `src/hooks/useLiveAvatar.ts`
- Manages avatar state and initialization
- Handles message sending to avatar
- Voice activity detection state
- Ready for actual LiveAvatar SDK integration

### 2. Webcam Picture-in-Picture

**Component**: `src/components/WebcamPiP.tsx`
- Bottom-right corner positioning
- Draggable and resizable functionality
- Show/hide toggle
- Camera permission handling
- Minimal UI overlay with controls

**Features**:
- Drag to reposition anywhere on screen
- Resize handles for size adjustment
- Toggle visibility without losing camera stream
- Clean camera resource management

### 3. Real-time Communication

**WebSocket Implementation**:
- Full-duplex communication between frontend and backend
- Message types: `user_message`, `avatar_response`, `voice_data`, `ping/pong`
- Session management with automatic cleanup
- Error handling and reconnection support

**Backend Integration**:
- `websocket_server.py`: New FastAPI server with WebSocket support
- `websocket_chat_handler.py`: Bridge between WebSocket and existing ChatEngine
- Maintains compatibility with existing handler system

### 4. Chat Interface

**Component**: `src/components/ChatInterface.tsx`
- Text and voice message support
- Message history with timestamps
- Real-time typing and voice recording indicators
- Speech-to-text preparation (microphone input)
- Responsive design with scroll management

### 5. Control Panel

**Component**: `src/components/ControlPanel.tsx`
- Connection status indicator
- Microphone mute/unmute controls
- Volume slider with visual feedback
- Webcam show/hide toggle
- Voice activity indicator

## Communication Protocol

### WebSocket Messages

#### Client to Server:
```json
{
  "type": "user_message",
  "text": "Hello, avatar!",
  "timestamp": "2025-01-01T12:00:00Z"
}

{
  "type": "voice_data", 
  "audio_data": "base64_encoded_audio",
  "timestamp": "2025-01-01T12:00:00Z"
}

{
  "type": "ping"
}
```

#### Server to Client:
```json
{
  "type": "avatar_response",
  "text": "Hello! How can I help you?",
  "audio": "base64_encoded_audio_response",
  "timestamp": "2025-01-01T12:00:00Z"
}

{
  "type": "voice_received",
  "message": "Voice message received and processing..."
}

{
  "type": "error",
  "message": "Failed to process your message"
}
```

## Installation and Setup

### Prerequisites
- Python 3.11+ with existing OpenAvatarChat dependencies
- Node.js 18+ and npm
- Modern web browser with WebRTC support

### Quick Start

1. **Install Frontend Dependencies**:
   ```bash
   ./start_new_architecture.sh install
   ```

2. **Start Both Services**:
   ```bash
   ./start_new_architecture.sh start
   ```

3. **Access the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8282

### Manual Setup

1. **Backend Setup**:
   ```bash
   # Use existing Python environment
   python src/websocket_server.py --port 8282
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Configuration

### Backend Configuration
- Uses existing YAML configuration files
- Default: `config/chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml`
- WebSocket server runs on port 8282
- CORS enabled for localhost:3000

### Frontend Configuration
- Environment variables in `frontend/.env.local`
- Backend URL: `http://localhost:8282`
- WebSocket URL: `ws://localhost:8282`

## LiveAvatar SDK Integration

The frontend is prepared for LiveAvatar SDK integration:

### Integration Points

1. **Avatar Display** (`src/components/AvatarDisplay.tsx`):
   ```typescript
   // Replace placeholder with actual LiveAvatar component
   const avatarComponent = <LiveAvatarComponent
     onMessage={handleAvatarMessage}
     isListening={isListening}
     volume={volume}
   />
   ```

2. **Avatar Hook** (`src/hooks/useLiveAvatar.ts`):
   ```typescript
   // Replace with actual SDK initialization
   const initializeAvatar = useCallback(async () => {
     const avatar = new LiveAvatar({
       apiKey: process.env.NEXT_PUBLIC_LIVEAVATAR_API_KEY,
       avatarId: 'your-avatar-id'
     })
     await avatar.initialize()
     setIsAvatarLoaded(true)
   }, [])
   ```

### Required SDK Features
- Real-time voice synthesis
- Text-to-speech capabilities
- Speech-to-text integration
- WebRTC audio/video handling
- Avatar animation control

## Browser Compatibility

### Supported Browsers
- **Chrome 90+** (recommended)
- **Firefox 88+**
- **Safari 14+**
- **Edge 90+**

### Required APIs
- WebSocket API
- WebRTC (getUserMedia)
- MediaRecorder API
- Drag and Drop API
- CSS Grid and Flexbox

## Performance Considerations

### Frontend Optimizations
- Next.js automatic code splitting
- React component memoization
- Efficient WebSocket connection management
- Lazy loading of non-critical components

### Backend Optimizations
- Async WebSocket handling
- Session cleanup on disconnect
- Efficient message routing
- Memory management for audio data

## Security Considerations

### Authentication
- Session-based WebSocket connections
- CORS configuration for trusted origins
- Input validation for all messages

### Privacy
- Local camera/microphone access only
- No persistent storage of audio data
- Secure WebSocket connections (WSS in production)

## Development Guidelines

### Frontend Development
1. Use TypeScript for type safety
2. Follow React best practices
3. Implement proper error boundaries
4. Use Tailwind CSS for consistent styling
5. Test WebSocket connectivity

### Backend Development
1. Maintain compatibility with existing ChatEngine
2. Handle WebSocket exceptions gracefully
3. Implement proper logging
4. Use async/await for I/O operations
5. Clean up resources on session end

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check if backend is running on port 8282
   - Verify CORS configuration
   - Check firewall settings

2. **Camera/Microphone Not Working**:
   - Grant browser permissions
   - Use HTTPS in production
   - Check device availability

3. **Frontend Build Errors**:
   - Ensure Node.js 18+ is installed
   - Clear node_modules and reinstall
   - Check TypeScript configuration

4. **Chat Engine Integration**:
   - Verify existing ChatEngine configuration
   - Check handler initialization
   - Review session management

### Debug Mode
Enable debug logging in frontend:
```javascript
localStorage.setItem('debug', 'true')
```

## Future Enhancements

### Planned Features
1. Complete LiveAvatar SDK integration
2. Advanced voice activity detection
3. Multi-user session support
4. Video call capabilities
5. Screen sharing functionality
6. Mobile responsive design improvements

### Extension Points
- Plugin system for additional avatar providers
- Custom UI themes
- Advanced audio processing
- Integration with external services
- Analytics and monitoring

## Migration from Old Architecture

### Gradual Migration Strategy
1. **Phase 1**: Run both systems in parallel
2. **Phase 2**: Migrate users to new frontend
3. **Phase 3**: Deprecate Gradio interface
4. **Phase 4**: Full cutover to new architecture

### Compatibility
- Existing ChatEngine handlers work unchanged
- Configuration files remain compatible
- Model files and weights are reused
- Session management is enhanced, not replaced

This new architecture provides a solid foundation for the LiveAvatar integration while maintaining all existing functionality and providing a modern, responsive user interface.
