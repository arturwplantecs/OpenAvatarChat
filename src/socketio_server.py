import os
import sys
from typing import Dict
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import socketio
from loguru import logger

# Add project root to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.chat_engine.chat_engine import ChatEngine
from src.service.service_utils.logger_utils import config_loggers
from src.service.service_utils.service_config_loader import load_configs
from src.service.service_utils.ssl_helpers import create_ssl_context
from src.engine_utils.directory_info import DirectoryInfo
from src.handlers.websocket_chat_handler import WebSocketChatHandler


class SocketIOManager:
    """Manages Socket.io connections and integrates with ChatEngine"""
    
    def __init__(self):
        self.active_sessions: Dict[str, str] = {}  # socket_id -> session_id
        self.chat_engine: ChatEngine = None
        self.chat_handler: WebSocketChatHandler = None
        
        # Create Socket.io server
        self.sio = socketio.AsyncServer(
            cors_allowed_origins=["http://localhost:3000", "https://localhost:3000"],
            logger=False,  # Disable verbose logging for now
            engineio_logger=False,
            async_mode='asgi'
        )
        
        # Register event handlers
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('user_message', self.handle_user_message)
        self.sio.on('voice_data', self.handle_voice_data)
        self.sio.on('ping', self.handle_ping)
    
    def set_chat_engine(self, chat_engine: ChatEngine):
        """Set the chat engine and create chat handler"""
        self.chat_engine = chat_engine
        self.chat_handler = WebSocketChatHandler(chat_engine, self)
    
    async def handle_connect(self, sid, environ):
        """Handle new Socket.io connection"""
        logger.info(f"Socket.io client connected: {sid}")
        await self.sio.emit('connected', {'message': 'Connected to OpenAvatarChat'}, to=sid)
    
    async def handle_disconnect(self, sid):
        """Handle Socket.io disconnection"""
        logger.info(f"Socket.io client disconnected: {sid}")
        if self.chat_handler:
            self.chat_handler.cleanup_session(sid)
        if sid in self.active_sessions:
            del self.active_sessions[sid]
    
    async def handle_user_message(self, sid, data):
        """Handle user text message"""
        try:
            if self.chat_handler:
                await self.chat_handler.handle_user_message(sid, data)
            else:
                # Fallback response
                response = {
                    "type": "avatar_response",
                    "text": f"Echo: {data.get('text', 'No text received')}",
                    "timestamp": data.get("timestamp")
                }
                await self.sio.emit('avatar_response', response, to=sid)
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await self.sio.emit('error', {'message': 'Failed to process message'}, to=sid)
    
    async def handle_voice_data(self, sid, data):
        """Handle voice data"""
        try:
            if self.chat_handler:
                await self.chat_handler.handle_voice_data(sid, data)
            else:
                await self.sio.emit('voice_received', {'message': 'Voice data received'}, to=sid)
        except Exception as e:
            logger.error(f"Error handling voice data: {e}")
            await self.sio.emit('error', {'message': 'Failed to process voice'}, to=sid)
    
    async def handle_ping(self, sid, data):
        """Handle ping message"""
        await self.sio.emit('pong', {}, to=sid)
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session (Socket.io client)"""
        try:
            event_type = message.get('type', 'message')
            await self.sio.emit(event_type, message, to=session_id)
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")


def create_app():
    """Create FastAPI app with Socket.io integration"""
    
    # Create Socket.io server first
    socketio_manager = SocketIOManager()
    
    # Create FastAPI app
    app = FastAPI(title="OpenAvatarChat API", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "service": "OpenAvatarChat WebSocket API"}
    
    @app.get("/")
    async def root():
        return {"message": "OpenAvatarChat WebSocket API", "docs": "/docs"}
    
    # Mount Socket.io app properly with a separate path
    socket_app = socketio.ASGIApp(socketio_manager.sio, other_asgi_app=app, socketio_path="socket.io")
    
    return socket_app, socketio_manager


def initialize_chat_engine(args, logger_config, service_config, engine_config):
    """Initialize the chat engine"""
    try:
        # Set up model cache directory
        if not os.path.isabs(engine_config.model_root):
            os.environ['MODELSCOPE_CACHE'] = os.path.join(
                DirectoryInfo.get_project_dir(),
                engine_config.model_root.replace('models', '')
            )
        
        config_loggers(logger_config)
        
        # Create chat engine
        chat_engine = ChatEngine()
        chat_engine.initialize(engine_config)
        
        logger.info("Chat engine initialized for Socket.io mode")
        return chat_engine
        
    except Exception as e:
        logger.error(f"Failed to initialize chat engine: {e}")
        return None


def parse_args():
    """Parse command line arguments"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="service host address")
    parser.add_argument("--port", type=int, default=8282, help="service host port")
    parser.add_argument("--config", type=str, 
                       default="config/chat_websocket_minimal.yaml", 
                       help="config file to use")
    parser.add_argument("--env", type=str, default="default", 
                       help="environment to use in config file")
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    
    # Load configurations
    logger_config, service_config, engine_config = load_configs(args)
    
    # Create app and Socket.io manager
    app, socketio_manager = create_app()
    
    # Initialize chat engine
    chat_engine = initialize_chat_engine(args, logger_config, service_config, engine_config)
    if chat_engine:
        socketio_manager.set_chat_engine(chat_engine)
    
    # Create SSL context
    ssl_context = create_ssl_context(args, service_config)
    
    logger.info(f"Starting OpenAvatarChat Socket.io server on {service_config.host}:{service_config.port}")
    
    # Start the server
    uvicorn.run(
        app, 
        host=service_config.host, 
        port=service_config.port, 
        **ssl_context
    )


if __name__ == "__main__":
    main()
