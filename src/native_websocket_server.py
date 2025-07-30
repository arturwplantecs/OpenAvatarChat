#!/usr/bin/env python3
"""
WebSocket server for OpenAvatarChat using FastAPI's native WebSocket support
This integrates with the existing ChatEngine and handlers
"""

import os
import sys
import json
import asyncio
import uuid
import time
import base64
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from loguru import logger
import numpy as np
import cv2

# Add project root to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.chat_engine.chat_engine import ChatEngine
from src.service.service_utils.logger_utils import config_loggers
from src.service.service_utils.service_config_loader import load_configs
from src.engine_utils.directory_info import DirectoryInfo
from src.chat_engine.data_models.session_info_data import SessionInfoData
from src.chat_engine.data_models.chat_engine_config_data import EngineChannelType

app = FastAPI(title="OpenAvatarChat WebSocket API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chat engine instance
chat_engine = None

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_data: Dict[str, dict] = {}
        self.sessions: Dict[str, str] = {}  # websocket_id -> session_id
        self.response_buffers: Dict[str, str] = {}  # client_id -> accumulated response
        self.buffer_timers: Dict[str, asyncio.TimerHandle] = {}  # client_id -> timer

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_data[client_id] = {}
        
        # Create a chat session for this WebSocket connection
        if chat_engine and chat_engine.inited:
            try:
                session_id = str(uuid.uuid4())
                session_info = SessionInfoData(
                    session_id=session_id,
                    user_id=client_id,
                    session_type="websocket"
                )
                
                # Create input/output queues for the session
                input_queues = {
                    EngineChannelType.TEXT: asyncio.Queue(),
                    EngineChannelType.AUDIO: asyncio.Queue()
                }
                output_queues = {
                    EngineChannelType.TEXT: asyncio.Queue(),
                    EngineChannelType.AUDIO: asyncio.Queue(),
                    EngineChannelType.VIDEO: asyncio.Queue()
                }
                
                session = chat_engine._create_session(session_info, input_queues, output_queues)
                if session:
                    # Start the session to begin processing
                    session.start()
                    self.sessions[client_id] = session_id
                    
                    # Start monitoring output queues for responses
                    asyncio.create_task(self._monitor_session_outputs(client_id, session_id, output_queues))
                    
                    logger.info(f"Created and started chat session {session_id} for client {client_id}")
                else:
                    logger.error(f"Failed to create session for {client_id}")
            except Exception as e:
                logger.error(f"Failed to create chat session for {client_id}: {e}")
        
        logger.info(f"Client {client_id} connected")

    async def _monitor_session_outputs(self, client_id: str, session_id: str, output_queues: dict):
        """Monitor session output queues and send responses to WebSocket client"""
        try:
            while client_id in self.active_connections:
                # Check for text responses (from LLM)
                if EngineChannelType.TEXT in output_queues:
                    try:
                        text_data = await asyncio.wait_for(
                            output_queues[EngineChannelType.TEXT].get(), 
                            timeout=0.1
                        )
                        # Extract text content from ChatData
                        if hasattr(text_data, 'data') and text_data.data:
                            text_content = text_data.data.get_main_data()
                        elif hasattr(text_data, 'content'):
                            text_content = text_data.content
                        else:
                            text_content = str(text_data)
                        
                        # Buffer the token instead of sending immediately
                        self._buffer_response_token(client_id, text_content)
                    except asyncio.TimeoutError:
                        pass
                    except Exception as e:
                        logger.error(f"Error processing text output: {e}")
                
                # Check for audio responses (from TTS)
                if EngineChannelType.AUDIO in output_queues:
                    try:
                        audio_data = await asyncio.wait_for(
                            output_queues[EngineChannelType.AUDIO].get(), 
                            timeout=0.1
                        )
                        # Send audio data to frontend
                        await self.send_personal_message({
                            "type": "avatar_audio",
                            "audio_data": "audio_data_placeholder",  # Placeholder for now
                            "timestamp": int(time.time() * 1000)
                        }, client_id)
                    except asyncio.TimeoutError:
                        pass
                
                # Check for video responses (from avatar)
                if EngineChannelType.VIDEO in output_queues:
                    try:
                        video_data = await asyncio.wait_for(
                            output_queues[EngineChannelType.VIDEO].get(), 
                            timeout=0.1
                        )
                        
                        # Process and encode video frame for web streaming
                        if video_data and video_data.data is not None:
                            try:
                                # Handle different video data formats
                                video_frame = video_data.data.get_main_data()
                                
                                # If it's a numpy array, convert to image
                                if isinstance(video_frame, np.ndarray):
                                    logger.debug(f"Video frame shape: {video_frame.shape}, dtype: {video_frame.dtype}")
                                    
                                    # Handle batch dimension if present (N, H, W, C) -> (H, W, C)
                                    if len(video_frame.shape) == 4:
                                        if video_frame.shape[0] == 1:
                                            video_frame = video_frame[0]  # Remove batch dimension
                                            logger.debug(f"Removed batch dimension, new shape: {video_frame.shape}")
                                        else:
                                            logger.warning(f"Unexpected batch size: {video_frame.shape[0]}")
                                            continue
                                    
                                    # Validate dimensions
                                    if len(video_frame.shape) != 3:
                                        logger.warning(f"Invalid video frame shape: {video_frame.shape}")
                                        continue
                                    
                                    height, width, channels = video_frame.shape
                                    
                                    # Check if dimensions are reasonable (max 2048x2048)
                                    if height > 2048 or width > 2048 or height <= 0 or width <= 0:
                                        logger.warning(f"Invalid video frame dimensions: {width}x{height}")
                                        continue
                                    
                                    # Ensure proper data type
                                    if video_frame.dtype != np.uint8:
                                        # Normalize to 0-255 range
                                        if video_frame.max() <= 1.0:
                                            video_frame = (video_frame * 255).astype(np.uint8)
                                        else:
                                            video_frame = np.clip(video_frame, 0, 255).astype(np.uint8)
                                    
                                    # Resize to a reasonable size for web streaming (512x512 max)
                                    if height > 512 or width > 512:
                                        scale = min(512/height, 512/width)
                                        new_height = int(height * scale)
                                        new_width = int(width * scale)
                                        video_frame = cv2.resize(video_frame, (new_width, new_height))
                                        logger.debug(f"Resized frame from {width}x{height} to {new_width}x{new_height}")
                                    
                                    # Convert from RGB to BGR for OpenCV (if needed)
                                    if channels == 3:
                                        # Assume RGB input, convert to BGR for cv2.imencode
                                        video_frame = cv2.cvtColor(video_frame, cv2.COLOR_RGB2BGR)
                                    
                                    # Encode as JPEG with quality settings
                                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
                                    success, buffer = cv2.imencode('.jpg', video_frame, encode_params)
                                    
                                    if success:
                                        video_base64 = base64.b64encode(buffer).decode('utf-8')
                                    else:
                                        logger.error("Failed to encode video frame as JPEG")
                                        continue
                                        
                                else:
                                    # If already encoded, try to use as-is
                                    if isinstance(video_frame, bytes):
                                        video_base64 = base64.b64encode(video_frame).decode('utf-8')
                                    else:
                                        logger.warning(f"Unknown video frame format: {type(video_frame)}")
                                        continue
                                
                                # Send video frame to frontend
                                await self.send_personal_message({
                                    "type": "avatar_video",
                                    "video_data": video_base64,
                                    "timestamp": int(time.time() * 1000)
                                }, client_id)
                                
                            except Exception as video_error:
                                logger.error(f"Error processing video frame for {client_id}: {video_error}")
                                
                    except asyncio.TimeoutError:
                        pass
                
                await asyncio.sleep(0.05)  # Small delay to prevent busy waiting
                
        except Exception as e:
            logger.error(f"Error monitoring session outputs for {client_id}: {e}")

    def disconnect(self, client_id: str):
        # Clean up chat session
        if client_id in self.sessions:
            session_id = self.sessions[client_id]
            if chat_engine and session_id in chat_engine.sessions:
                try:
                    chat_engine.stop_session(session_id)
                    logger.info(f"Stopped chat session {session_id}")
                except Exception as e:
                    logger.error(f"Error stopping session {session_id}: {e}")
            del self.sessions[client_id]
        
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_data:
            del self.connection_data[client_id]
        if client_id in self.response_buffers:
            del self.response_buffers[client_id]
        if client_id in self.buffer_timers:
            self.buffer_timers[client_id].cancel()
            del self.buffer_timers[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def _send_buffered_response(self, client_id: str):
        """Send the accumulated response buffer for a client"""
        if client_id in self.response_buffers and self.response_buffers[client_id].strip():
            response_text = self.response_buffers[client_id].strip()
            logger.info(f"Sending buffered AI response to client {client_id}: {response_text}")
            await self.send_personal_message({
                "type": "avatar_response",
                "text": response_text,
                "timestamp": int(time.time() * 1000),
                "sender": "avatar"
            }, client_id)
            # Clear the buffer
            self.response_buffers[client_id] = ""
        
        # Clear the timer
        if client_id in self.buffer_timers:
            del self.buffer_timers[client_id]

    def _buffer_response_token(self, client_id: str, token: str):
        """Buffer a response token and set timer to send complete response"""
        # Initialize buffer if needed
        if client_id not in self.response_buffers:
            self.response_buffers[client_id] = ""
        
        # Add token to buffer
        self.response_buffers[client_id] += token
        
        # Cancel existing timer
        if client_id in self.buffer_timers:
            self.buffer_timers[client_id].cancel()
        
        # Set new timer to send response after 500ms of no new tokens
        loop = asyncio.get_event_loop()
        
        def timer_callback():
            asyncio.create_task(self._send_buffered_response(client_id))
        
        self.buffer_timers[client_id] = loop.call_later(0.5, timer_callback)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "OpenAvatarChat WebSocket API", "docs": "/docs"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "OpenAvatarChat WebSocket API", 
        "connections": len(manager.active_connections),
        "chat_engine_initialized": chat_engine is not None and chat_engine.inited if chat_engine else False
    }

async def process_user_message(client_id: str, text: str):
    """Process user message through the chat engine"""
    try:
        if not chat_engine or not chat_engine.inited:
            return f"Echo (no engine): {text}"
        
        session_id = manager.sessions.get(client_id)
        if not session_id or session_id not in chat_engine.sessions:
            return f"Echo (no session): {text}"
        
        session = chat_engine.sessions[session_id]
        
        # Create and send text data using the proper ChatData model
        from chat_engine.data_models.chat_data.chat_data_model import ChatData
        from chat_engine.data_models.chat_data_type import ChatDataType
        from chat_engine.data_models.runtime_data.data_bundle import DataBundle
        from uuid import uuid4
        import time
        
        # Get the input definition for text
        if hasattr(session, 'session_context') and session.session_context.input_queues:
            text_queue = session.session_context.input_queues.get(EngineChannelType.TEXT)
            if text_queue:
                # Put raw text data into the input queue (the session will package it properly)
                # Format: (timestamp, text_content)
                import time
                timestamp = (int(time.time()), int(time.time() * 1000000) % 1000000)
                input_data = (timestamp, text)
                
                await text_queue.put(input_data)
                logger.info(f"Sent message to session {session_id}: {text}")
                return None  # Don't send immediate response, wait for AI
        
        # Fallback if queues not available
        return f"Session ready but no queues: {text}"
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing: {text}"

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    # Send welcome message
    await manager.send_personal_message({
        "type": "connected",
        "message": "Connected to OpenAvatarChat",
        "client_id": client_id,
        "chat_engine_ready": chat_engine is not None and chat_engine.inited if chat_engine else False
    }, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"Received from {client_id}: {message}")
            
            # Handle different message types
            message_type = message.get("type", "unknown")
            
            if message_type == "user_message":
                # Process through chat engine
                text = message.get('text', '')
                await process_user_message(client_id, text)
                # Don't send any immediate response - wait for AI
                
            elif message_type == "voice_data":
                response = {
                    "type": "voice_received",
                    "message": "Voice data received"
                }
                await manager.send_personal_message(response, client_id)
                
            elif message_type == "ping":
                response = {
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                }
                await manager.send_personal_message(response, client_id)
            
            else:
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
                await manager.send_personal_message(response, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in websocket connection for {client_id}: {e}")
        manager.disconnect(client_id)

def initialize_chat_engine():
    """Initialize the chat engine with configuration"""
    global chat_engine
    
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", type=str, 
                           default="config/chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml", 
                           help="config file to use")
        parser.add_argument("--env", type=str, default="default", 
                           help="environment to use in config file")
        
        # For WebSocket server, we'll use the avatar configuration
        parser.set_defaults(config="config/chat_websocket_avatar.yaml")
        
        args, _ = parser.parse_known_args()
        
        # Load configurations
        logger_config, service_config, engine_config = load_configs(args)
        
        # Set up model cache directory
        if not os.path.isabs(engine_config.model_root):
            os.environ['MODELSCOPE_CACHE'] = os.path.join(
                DirectoryInfo.get_project_dir(),
                engine_config.model_root.replace('models', '')
            )
        
        config_loggers(logger_config)
        
        # Create and initialize chat engine
        chat_engine = ChatEngine()
        chat_engine.initialize(engine_config)
        
        logger.info("Chat engine initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize chat engine: {e}")
        logger.info("Running in echo mode without chat engine")
        return False

if __name__ == "__main__":
    logger.info("Starting OpenAvatarChat WebSocket server on http://localhost:8282")
    
    # Initialize chat engine
    initialize_chat_engine()
    
    uvicorn.run(app, host="0.0.0.0", port=8282, log_level="info")
