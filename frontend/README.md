# OpenAvatarChat Frontend

This is the Next.js frontend for the OpenAvatarChat application, implementing the redesigned UI with LiveAvatar integration.

## Features

- **Live Avatar Display**: Central avatar with vertical orientation
- **Webcam Picture-in-Picture**: Draggable, resizable webcam feed in bottom-right corner
- **Real-time Chat Interface**: Text and voice communication with the avatar
- **WebSocket Communication**: Real-time connection to Python backend
- **Responsive Design**: Tailwind CSS with dark mode support
- **Voice Controls**: Microphone input with speech-to-text capabilities

## Architecture

### Components

- `AvatarDisplay`: Main avatar component with LiveAvatar SDK integration
- `WebcamPiP`: Picture-in-picture webcam component with drag/resize functionality
- `ChatInterface`: Text and voice chat interface with message history
- `ControlPanel`: Audio/video controls and connection status

### Hooks

- `useSocket`: WebSocket connection management
- `useLiveAvatar`: LiveAvatar SDK integration and state management

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Python backend running on `localhost:8282`

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Configuration

### Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8282
NEXT_PUBLIC_WS_URL=ws://localhost:8282
```

### Backend Integration

The frontend connects to the Python backend via:
- WebSocket: `ws://localhost:8282/ws/{session_id}`
- HTTP API: `http://localhost:8282/api/*`

## LiveAvatar SDK Integration

The `useLiveAvatar` hook is prepared for LiveAvatar SDK integration. To integrate:

1. Install the LiveAvatar SDK package
2. Update `src/hooks/useLiveAvatar.ts` with actual SDK calls
3. Configure the avatar in `src/components/AvatarDisplay.tsx`

## Customization

### Styling

The application uses Tailwind CSS. Customize styles in:
- `src/app/globals.css`: Global styles and CSS variables
- Component files: Tailwind utility classes
- `tailwind.config.ts`: Tailwind configuration

### Layout

Modify the layout in `src/app/page.tsx`:
- Avatar position and sizing
- Chat interface placement
- Control panel positioning
- Webcam PiP default location

## API Integration

### WebSocket Messages

The frontend sends/receives these message types:

```typescript
// User message
{
  type: "user_message",
  text: string,
  timestamp: Date
}

// Avatar response
{
  type: "avatar_response", 
  text: string,
  audio?: string,
  timestamp: Date
}

// Voice data
{
  type: "voice_data",
  audio_data: Blob
}
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure Python backend is running on port 8282
   - Check CORS configuration in backend

2. **Webcam Not Working**
   - Grant camera permissions in browser
   - Check HTTPS requirements for getUserMedia

3. **Audio Issues**
   - Grant microphone permissions
   - Check audio device settings

### Debug Mode

Enable debug logging by setting:
```typescript
localStorage.setItem('debug', 'true')
```

## Browser Support

- Chrome 90+ (recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

WebRTC and modern media APIs required for full functionality.
