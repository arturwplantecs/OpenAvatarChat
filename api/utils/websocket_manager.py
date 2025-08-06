"""
WebSocket manager for real-time communication
"""

import asyncio
import json
import base64
import time
from typing import Dict, Optional, Any, List
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time avatar chat"""
    
    def __init__(self, pipeline_service):
        self.pipeline_service = pipeline_service
        self.session_manager = None  # Will be set from main.py
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.connection_sessions[websocket] = session_id
        
        # Send initial connection success message
        await self.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": time.time()
        })
        
        logger.info(f"🔌 WebSocket connected for session: {session_id}")
    
    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            del self.active_connections[session_id]
            del self.connection_sessions[websocket]
            logger.info(f"🔌 WebSocket disconnected for session: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to session {session_id}: {e}")
                await self.disconnect(session_id)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude_session: Optional[str] = None):
        """Broadcast a message to all connected sessions"""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            if exclude_session and session_id == exclude_session:
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to session {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            await self.disconnect(session_id)
    
    async def handle_message(self, data: Dict[str, Any], session_id: str):
        """Handle incoming WebSocket message"""
        try:
            message_type = data.get("type")
            
            if message_type == "audio_chunk":
                await self._handle_audio_chunk(data, session_id)
            elif message_type == "text_message":
                await self._handle_text_message(data, session_id)
            elif message_type == "config_update":
                await self._handle_config_update(data, session_id)
            elif message_type == "ping":
                await self._handle_ping(data, session_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(session_id, "unknown_message_type", "Unknown message type")
        
        except Exception as e:
            logger.error(f"Error handling message for session {session_id}: {e}")
            await self.send_error(session_id, "processing_error", str(e))
    
    async def _handle_audio_chunk(self, data: Dict[str, Any], session_id: str):
        """Handle audio chunk for processing"""
        try:
            # Update session activity
            if self.session_manager:
                await self.session_manager.update_session_activity(session_id)
            
            # Get audio data
            audio_data_b64 = data.get("audio_data")
            if not audio_data_b64:
                await self.send_error(session_id, "missing_audio_data", "Audio data is required")
                return
            
            # Decode audio data
            try:
                audio_data = base64.b64decode(audio_data_b64)
            except Exception as e:
                await self.send_error(session_id, "invalid_audio_data", "Invalid base64 audio data")
                return
            
            # Send processing started message
            await self.send_message(session_id, {
                "type": "processing_started",
                "timestamp": time.time()
            })
            
            # Process audio through pipeline
            result = await self.pipeline_service.process_audio(audio_data, session_id)
            
            # Add to conversation history
            if self.session_manager:
                await self.session_manager.add_message_to_history(
                    session_id, 
                    "audio_input",
                    {
                        "transcribed_text": result.get("transcribed_text", ""),
                        "processing_time": result.get("processing_time", 0)
                    }
                )
                
                await self.session_manager.add_message_to_history(
                    session_id,
                    "ai_response", 
                    {
                        "response_text": result.get("response_text", ""),
                        "has_audio": bool(result.get("audio_data")),
                        "has_video": bool(result.get("video_frames")),
                        "processing_time": result.get("processing_time", 0)
                    }
                )
            
            # Send results back to client
            await self.send_message(session_id, {
                "type": "audio_processed",
                "transcribed_text": result.get("transcribed_text", ""),
                "response_text": result.get("response_text", ""),
                "audio_data": result.get("audio_data"),
                "video_frames": result.get("video_frames", []),
                "processing_time": result.get("processing_time", 0),
                "timestamp": time.time()
            })
            
        except Exception as e:
            logger.error(f"Audio processing error for session {session_id}: {e}")
            await self.send_error(session_id, "audio_processing_error", str(e))
    
    async def _handle_text_message(self, data: Dict[str, Any], session_id: str):
        """Handle text message for processing"""
        try:
            # Update session activity
            if self.session_manager:
                await self.session_manager.update_session_activity(session_id)
            
            # Get text
            text = data.get("text", "").strip()
            if not text:
                await self.send_error(session_id, "missing_text", "Text is required")
                return
            
            # Send processing started message
            await self.send_message(session_id, {
                "type": "processing_started",
                "timestamp": time.time()
            })
            
            # Process text through pipeline
            result = await self.pipeline_service.process_text(text, session_id)
            
            # Add to conversation history
            if self.session_manager:
                await self.session_manager.add_message_to_history(
                    session_id,
                    "text_input",
                    {
                        "input_text": text,
                        "processing_time": result.get("processing_time", 0)
                    }
                )
                
                await self.session_manager.add_message_to_history(
                    session_id,
                    "ai_response",
                    {
                        "response_text": result.get("response_text", ""),
                        "has_audio": bool(result.get("audio_data")),
                        "has_video": bool(result.get("video_frames")),
                        "processing_time": result.get("processing_time", 0)
                    }
                )
            
            # Send results back to client
            await self.send_message(session_id, {
                "type": "text_processed",
                "input_text": text,
                "response_text": result.get("response_text", ""),
                "audio_data": result.get("audio_data"),
                "video_frames": result.get("video_frames", []),
                "processing_time": result.get("processing_time", 0),
                "timestamp": time.time()
            })
            
        except Exception as e:
            logger.error(f"Text processing error for session {session_id}: {e}")
            await self.send_error(session_id, "text_processing_error", str(e))
    
    async def _handle_config_update(self, data: Dict[str, Any], session_id: str):
        """Handle configuration update"""
        try:
            config_update = data.get("config", {})
            
            if self.session_manager:
                success = await self.session_manager.update_session_config(session_id, config_update)
                
                if success:
                    await self.send_message(session_id, {
                        "type": "config_updated",
                        "message": "Configuration updated successfully",
                        "timestamp": time.time()
                    })
                else:
                    await self.send_error(session_id, "config_update_failed", "Failed to update configuration")
            else:
                await self.send_error(session_id, "session_manager_unavailable", "Session manager not available")
                
        except Exception as e:
            logger.error(f"Config update error for session {session_id}: {e}")
            await self.send_error(session_id, "config_update_error", str(e))
    
    async def _handle_ping(self, data: Dict[str, Any], session_id: str):
        """Handle ping message"""
        await self.send_message(session_id, {
            "type": "pong",
            "timestamp": time.time()
        })
    
    async def send_error(self, session_id: str, error_type: str, message: str):
        """Send error message to client"""
        await self.send_message(session_id, {
            "type": "error",
            "error": error_type,
            "message": message,
            "timestamp": time.time()
        })
    
    def get_active_connections_count(self) -> int:
        """Get number of active WebSocket connections"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about active connections"""
        info = []
        for session_id, websocket in self.active_connections.items():
            info.append({
                "session_id": session_id,
                "client_host": getattr(websocket.client, 'host', 'unknown'),
                "client_port": getattr(websocket.client, 'port', 0)
            })
        return info
