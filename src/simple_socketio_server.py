#!/usr/bin/env python3
"""
Simple Socket.IO server for OpenAvatarChat
This version avoids ASGI integration issues by running Socket.IO directly
"""

import os
import sys
import asyncio
import socketio
from loguru import logger

# Add project root to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Create a Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins=["http://localhost:3000", "https://localhost:3000"],
    logger=True,
    engineio_logger=True
)

@sio.event
async def connect(sid, environ):
    """Handle new Socket.io connection"""
    logger.info(f"Socket.io client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to OpenAvatarChat'}, to=sid)

@sio.event
async def disconnect(sid):
    """Handle Socket.io disconnection"""
    logger.info(f"Socket.io client disconnected: {sid}")

@sio.event
async def user_message(sid, data):
    """Handle user text message"""
    try:
        logger.info(f"Received message from {sid}: {data}")
        
        # Simple echo response for testing
        response = {
            "type": "avatar_response",
            "text": f"Echo: {data.get('text', 'No text received')}",
            "timestamp": data.get("timestamp"),
            "sender": "avatar"
        }
        await sio.emit('avatar_response', response, to=sid)
    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        await sio.emit('error', {'message': 'Failed to process message'}, to=sid)

@sio.event
async def voice_data(sid, data):
    """Handle voice data"""
    try:
        logger.info(f"Received voice data from {sid}")
        await sio.emit('voice_received', {'message': 'Voice data received'}, to=sid)
    except Exception as e:
        logger.error(f"Error handling voice data: {e}")
        await sio.emit('error', {'message': 'Failed to process voice'}, to=sid)

@sio.event
async def ping(sid, data):
    """Handle ping message"""
    await sio.emit('pong', {}, to=sid)

if __name__ == '__main__':
    # Create a simple ASGI app for Socket.IO
    app = socketio.ASGIApp(sio)
    
    # Run with uvicorn
    import uvicorn
    
    logger.info("Starting simple Socket.IO server on http://localhost:8282")
    uvicorn.run(app, host="0.0.0.0", port=8282, log_level="info")
