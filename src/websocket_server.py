import os
import sys
from typing import Dict
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
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


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_engine: ChatEngine = None
        self.chat_handler: WebSocketChatHandler = None

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            # Clean up chat session
            if self.chat_handler:
                self.chat_handler.cleanup_session(session_id)
            
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

    async def broadcast(self, message: dict):
        for session_id in list(self.active_connections.keys()):
            await self.send_message(session_id, message)

    def set_chat_engine(self, chat_engine: ChatEngine):
        self.chat_engine = chat_engine
        self.chat_handler = WebSocketChatHandler(chat_engine, self)


def create_app():
    app = FastAPI(title="OpenAvatarChat API", version="1.0.0")
    
    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve static files (if needed)
    frontend_build_path = os.path.join(project_dir, "frontend", "out")
    if os.path.exists(frontend_build_path):
        app.mount("/static", StaticFiles(directory=frontend_build_path), name="static")

    # WebSocket manager
    ws_manager = WebSocketManager()

    @app.get("/")
    async def root():
        return {"message": "OpenAvatarChat API", "status": "running"}

    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "chat_engine_initialized": ws_manager.chat_engine is not None and ws_manager.chat_engine.inited
        }

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await ws_manager.connect(websocket, session_id)
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.info(f"Received message from {session_id}: {message}")
                
                # Handle different message types
                if message.get("type") == "user_message":
                    if ws_manager.chat_handler:
                        await ws_manager.chat_handler.handle_user_message(session_id, message)
                    else:
                        # Fallback response if chat engine not ready
                        response = {
                            "type": "avatar_response",
                            "text": "Chat engine is not ready yet. Please try again.",
                            "timestamp": message.get("timestamp")
                        }
                        await ws_manager.send_message(session_id, response)
                
                elif message.get("type") == "voice_data":
                    if ws_manager.chat_handler:
                        await ws_manager.chat_handler.handle_voice_data(session_id, message)
                    else:
                        logger.warning("Voice data received but chat handler not ready")
                
                elif message.get("type") == "ping":
                    # Respond to ping with pong
                    await ws_manager.send_message(session_id, {"type": "pong"})

        except WebSocketDisconnect:
            ws_manager.disconnect(session_id)
        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {e}")
            ws_manager.disconnect(session_id)

    # Initialize chat engine
    def initialize_chat_engine(args, logger_config, service_config, engine_config):
        # Set up ModelScope cache
        if not os.path.isabs(engine_config.model_root):
            os.environ['MODELSCOPE_CACHE'] = os.path.join(
                DirectoryInfo.get_project_dir(),
                engine_config.model_root.replace('models', '')
            )

        config_loggers(logger_config)
        chat_engine = ChatEngine()
        
        # Initialize without Gradio UI
        chat_engine.initialize(engine_config, app=app)
        ws_manager.set_chat_engine(chat_engine)
        
        logger.info("Chat engine initialized for WebSocket mode")

    return app, ws_manager, initialize_chat_engine


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="service host address")
    parser.add_argument("--port", type=int, default=8282, help="service host port")
    parser.add_argument("--config", type=str, 
                       default="config/chat_with_openai_compatible_bailian_cosyvoice_musetalk.yaml", 
                       help="config file to use")
    parser.add_argument("--env", type=str, default="default", help="environment to use in config file")
    args = parser.parse_args()

    # Load configurations
    logger_config, service_config, engine_config = load_configs(args)
    
    # Create app
    app, ws_manager, init_chat_engine = create_app()
    
    # Initialize chat engine
    init_chat_engine(args, logger_config, service_config, engine_config)
    
    # Create SSL context
    ssl_context = create_ssl_context(args, service_config)
    
    # Run the server
    logger.info(f"Starting OpenAvatarChat WebSocket server on {service_config.host}:{service_config.port}")
    uvicorn.run(
        app, 
        host=service_config.host, 
        port=service_config.port, 
        **ssl_context
    )


if __name__ == "__main__":
    main()
