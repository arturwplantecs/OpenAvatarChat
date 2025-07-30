# App Redesign Instructions

## Overview
This document outlines the requirements for redesigning the application with LiveAvatar integration for voice and text chat capabilities.

## Architecture Requirements

### Backend
- **Language**: Python
- **Framework**: Maintain existing Python backend infrastructure
- **API**: RESTful API or WebSocket connections for real-time communication

### Frontend
- **Framework**: Next.js or Node.js
- **UI Library**: React (if using Next.js)
- **Styling**: CSS Modules, Tailwind CSS, or styled-components

## Core Features

### 1. LiveAvatar Integration
- Implement LiveAvatar SDK for voice and text chat functionality
- Configure avatar for real-time voice synthesis
- Set up text-to-speech and speech-to-text capabilities
- Handle WebRTC connections for voice communication

### 2. UI Layout

#### Avatar Display
- **Position**: Vertical orientation
- **Location**: Center or prominent position in the interface
- **Responsive**: Ensure proper scaling across different screen sizes

#### Webcam Picture-in-Picture
- **Position**: Bottom right corner
- **Size**: Small, non-intrusive window
- **Features**:
  - Draggable/repositionable
  - Resizable
  - Toggle show/hide
  - Minimal UI overlay

### 3. Communication Features
- Real-time voice chat with LiveAvatar
- Text chat interface with message history
- Voice activity detection
- Mute/unmute controls
- Volume controls

## Implementation Steps

1. **Backend Setup**
   - Create API endpoints for LiveAvatar communication
   - Implement WebSocket server for real-time features
   - Set up authentication and session management

2. **Frontend Development**
   - Initialize Next.js/Node.js project
   - Integrate LiveAvatar SDK
   - Create avatar component with vertical layout
   - Implement webcam PiP component
   - Design chat interface

3. **Integration**
   - Connect frontend to Python backend
   - Test voice and text communication
   - Implement error handling and fallbacks

4. **Testing**
   - Unit tests for components
   - Integration tests for communication features
   - Cross-browser compatibility testing
   - Performance optimization

## Technical Considerations

- **Browser Compatibility**: Ensure WebRTC support
- **Security**: Implement proper authentication and encryption
- **Performance**: Optimize for low-latency communication
- **Accessibility**: Include keyboard navigation and screen reader support

## Dependencies
- LiveAvatar SDK
- WebRTC libraries
- Socket.io or similar for real-time communication
- Media stream APIs for webcam functionality