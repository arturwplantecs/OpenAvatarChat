"""
WebSocket handler for the new Next.js frontend integration.
This module bridges the WebSocket interface with the existing ChatEngine.
"""

import asyncio
import json
import uuid
from typing import Dict, Optional
from loguru import logger

from chat_engine.data_models.session_info_data import SessionInfoData, IOQueueType
from chat_engine.data_models.chat_engine_config_data import EngineChannelType


class WebSocketChatHandler:
    """Handles WebSocket communication and integrates with ChatEngine"""
    
    def __init__(self, chat_engine, socketio_manager):
        self.chat_engine = chat_engine
        self.socketio_manager = socketio_manager
        self.active_sessions: Dict[str, str] = {}  # socket_id -> chat_session_id
        
    async def handle_user_message(self, websocket_id: str, message: dict):
        """Process a user text message through the chat engine"""
        try:
            text = message.get("text", "").strip()
            if not text:
                return
                
            # Get or create chat session
            session_id = await self._get_or_create_session(websocket_id)
            
            # Process message through chat engine
            # This is a simplified integration - you may need to adapt based on your chat engine's API
            response_text = await self._process_with_chat_engine(session_id, text)
            
            # Send response back to frontend
            response = {
                "type": "avatar_response",
                "text": response_text,
                "timestamp": message.get("timestamp"),
                "session_id": session_id
            }
            
            await self.socketio_manager.sio.emit('avatar_response', response, to=websocket_id)
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await self._send_error(websocket_id, "Failed to process your message")
    
    async def handle_voice_data(self, websocket_id: str, message: dict):
        """Process voice data through ASR and then chat engine"""
        try:
            audio_data = message.get("audio_data")
            if not audio_data:
                return
                
            # TODO: Process audio through ASR (speech-to-text)
            # This would integrate with your existing ASR handlers
            
            session_id = await self._get_or_create_session(websocket_id)
            
            # For now, send acknowledgment
            response = {
                "type": "voice_received",
                "message": "Voice message received and processing...",
                "session_id": session_id
            }
            
            await self.socketio_manager.sio.emit('voice_received', response, to=websocket_id)
            
        except Exception as e:
            logger.error(f"Error handling voice data: {e}")
            await self._send_error(websocket_id, "Failed to process voice message")
    
    async def _get_or_create_session(self, websocket_id: str) -> str:
        """Get existing session or create a new one for the WebSocket connection"""
        if websocket_id in self.active_sessions:
            return self.active_sessions[websocket_id]
            
        # Create new session
        session_id = str(uuid.uuid4())
        
        try:
            # Create session info
            session_info = SessionInfoData(
                session_id=session_id,
                user_id=websocket_id,  # Use websocket ID as user ID
                session_type="websocket"
            )
            
            # Create input/output queues for the session
            # This is simplified - adapt based on your chat engine's queue structure
            input_queues = {
                EngineChannelType.TEXT: asyncio.Queue(),
                EngineChannelType.AUDIO: asyncio.Queue()
            }
            
            output_queues = {
                EngineChannelType.TEXT: asyncio.Queue(),
                EngineChannelType.AUDIO: asyncio.Queue()
            }
            
            # Create session in chat engine
            if hasattr(self.chat_engine, '_create_session'):
                await self.chat_engine._create_session(session_info, input_queues, output_queues)
            
            self.active_sessions[websocket_id] = session_id
            logger.info(f"Created new chat session {session_id} for WebSocket {websocket_id}")
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            # Fallback to simple session ID
            self.active_sessions[websocket_id] = session_id
            
        return session_id
    
    async def _process_with_chat_engine(self, session_id: str, text: str) -> str:
        """Process text through the chat engine and return response"""
        try:
            # This is a simplified integration
            # You'll need to adapt this based on how your chat engine processes messages
            
            if hasattr(self.chat_engine, 'sessions') and session_id in self.chat_engine.sessions:
                session = self.chat_engine.sessions[session_id]
                # Process through session
                # This depends on your session's message processing API
                response = f"Processed through chat engine: {text}"
            else:
                # Simple echo for now - replace with actual chat engine integration
                response = f"Echo: {text}"
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing with chat engine: {e}")
            return "I'm sorry, I encountered an error processing your message."
    
    async def _send_error(self, websocket_id: str, error_message: str):
        """Send error message to frontend"""
        error_response = {
            "type": "error",
            "message": error_message,
            "timestamp": None
        }
        await self.socketio_manager.sio.emit('error', error_response, to=websocket_id)
    
    def cleanup_session(self, websocket_id: str):
        """Clean up session when WebSocket disconnects"""
        if websocket_id in self.active_sessions:
            session_id = self.active_sessions[websocket_id]
            
            # Clean up chat engine session if needed
            if hasattr(self.chat_engine, 'sessions') and session_id in self.chat_engine.sessions:
                try:
                    # Stop and clean up the session
                    session = self.chat_engine.sessions[session_id]
                    if hasattr(session, 'stop'):
                        session.stop()
                    del self.chat_engine.sessions[session_id]
                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {e}")
            
            del self.active_sessions[websocket_id]
            logger.info(f"Cleaned up session {session_id} for WebSocket {websocket_id}")
