# Modern QUARI Frontend

This is a modern Next.js frontend for the QUARI AI avatar chat system.

## Features

✨ **Modern Design**
- Clean, dark theme interface
- Avatar video in center taking full vertical space (900px max height)
- Chat panel on the right side
- Smooth animations with Framer Motion

🎬 **Advanced Video Playback**
- Proper 9:16 aspect ratio support
- Smooth 25 FPS video rendering
- Synchronized audio/video playback
- Real-time lip sync with neural networks

💬 **Enhanced Chat Experience**
- Text and voice messaging
- Real-time transcription
- Message history with timestamps
- Loading states and visual feedback

🎙️ **Voice Features**
- Press and hold to record
- Automatic transcription
- Voice activity detection
- Audio toggle controls

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: Python FastAPI with LiteAvatar neural networks
- **Video**: Canvas-based rendering with 25 FPS timing
- **Audio**: HTML5 Audio API with base64 streaming

## Getting Started

1. Start the backend:
```bash
cd /home/arti/Repos/OpenAvatarChat
python api/main.py
```

2. Start the frontend:
```bash
cd /home/arti/Repos/OpenAvatarChat/frontend-nextjs
npm run dev
```

3. Or use the combined script:
```bash
./start_full_stack.sh
```

## URLs

- **Frontend**: http://localhost:3000
- **Backend**: https://localhost:8282

## Design Specifications

### Avatar Section
- Takes up the majority of screen space (flex-1)
- Video canvas with 900px max height
- Maintains 9:16 aspect ratio (width = height * 9/16)
- Rounded corners with blue glow effect
- Status indicator below avatar

### Chat Section
- Fixed 384px width (w-96)
- Right-side placement
- Header with QUARI branding and controls
- Scrollable message area
- Input section with text and voice controls

### Video Playback
- 25 FPS rendering (40ms per frame)
- Synchronized with audio playback
- Smooth fade transitions
- Proper aspect ratio handling

## Technical Details

The frontend uses modern React patterns with hooks for state management and effects for side effects. Video rendering is handled through HTML5 Canvas API with proper frame timing. Audio is synchronized using promises and the HTML5 Audio API.

## Previous vs New

**Old Frontend Issues Fixed:**
- ❌ Basic HTML/CSS with poor styling
- ❌ Small avatar video display
- ❌ No proper aspect ratio handling
- ❌ Jerky video playback
- ❌ Poor synchronization

**New Frontend Improvements:**
- ✅ Modern Next.js with TypeScript
- ✅ Large, centered avatar video
- ✅ Proper 9:16 aspect ratio (900px height)
- ✅ Smooth 25 FPS video playback
- ✅ Perfect audio/video sync
- ✅ Professional dark theme
- ✅ Responsive design
- ✅ Smooth animations
