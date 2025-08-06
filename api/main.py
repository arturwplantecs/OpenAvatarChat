#!/usr/bin/env python3
"""
OpenAvatarChat API Backend
Independent backend API extracted from the original OpenAvatarChat application
"""

# CUDA Environment Setup - MUST BE FIRST
import os
from pathlib import Path

def setup_cuda_environment():
    """Set up CUDA environment variables and library paths before any CUDA imports"""
    
    # Get the virtual environment path
    script_dir = Path(__file__).parent.parent
    venv_path = script_dir / ".venv"
    
    if venv_path.exists():
        venv_site_packages = venv_path / "lib" / "python3.11" / "site-packages"
        
        # Enhanced CUDA library paths
        cuda_paths = [
            str(venv_site_packages / "nvidia" / "cudnn" / "lib"),
            str(venv_site_packages / "nvidia" / "cuda_runtime" / "lib"), 
            str(venv_site_packages / "nvidia" / "cublas" / "lib"),
            str(venv_site_packages / "ctranslate2.libs"),
            str(venv_site_packages / "torch" / "lib"),
        ]
        
        # Filter existing paths
        existing_paths = [path for path in cuda_paths if Path(path).exists()]
        
        # Set LD_LIBRARY_PATH
        current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        if existing_paths:
            if current_ld_path:
                new_ld_path = ':'.join(existing_paths) + ':' + current_ld_path
            else:
                new_ld_path = ':'.join(existing_paths)
            
            os.environ['LD_LIBRARY_PATH'] = new_ld_path
            print(f"✅ CUDA LD_LIBRARY_PATH configured: {new_ld_path}")
        
        # Set CUDA environment variables
        os.environ.setdefault('CUDA_HOME', '/usr/local/cuda')
        os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')

# Set up CUDA environment immediately
setup_cuda_environment()

import sys
import time
from datetime import datetime
from typing import Dict
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging

# Add the project root to Python path to import original components
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))  # Add current directory for relative imports

from api_models.requests import CreateSessionRequest, TextMessageRequest
from api_models.responses import SessionResponse, HealthResponse
from services.session_manager import SessionManager
from services.pipeline_service import PipelineService
from utils.websocket_manager import WebSocketManager
from config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Track application start time
start_time = time.time()

# Create FastAPI app
app = FastAPI(
    title="OpenAvatarChat API",
    description="Independent backend API for OpenAvatarChat - Polish language avatar conversations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
session_manager = SessionManager()
pipeline_service = PipelineService()
websocket_manager = WebSocketManager(pipeline_service)

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("🚀 Starting OpenAvatarChat API Backend")
    
    # Set session manager in pipeline service for conversation history
    pipeline_service.session_manager = session_manager
    
    # Initialize pipeline service
    await pipeline_service.initialize()
    logger.info("✅ Pipeline service initialized")
    
    # Set session manager in websocket manager and start cleanup
    websocket_manager.session_manager = session_manager
    await session_manager.start_cleanup_task()
    
    logger.info("🎯 API Backend ready to serve requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down OpenAvatarChat API Backend")
    
    # Cleanup all active sessions
    await session_manager.cleanup_all_sessions()
    
    # Cleanup pipeline service
    await pipeline_service.cleanup()
    
    logger.info("✅ Cleanup completed")

# Health check endpoint
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        pipeline_status = await pipeline_service.get_status()
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            pipeline_status=pipeline_status,
            uptime=time.time() - start_time
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Pipeline status endpoint
@app.get("/api/v1/pipeline/status")
async def pipeline_status():
    """Get detailed pipeline component status"""
    try:
        return await pipeline_service.get_detailed_status()
    except Exception as e:
        logger.error(f"Pipeline status check failed: {e}")
        raise HTTPException(status_code=503, detail="Pipeline status unavailable")

# Session management endpoints
@app.post("/api/v1/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest = None):
    """Create a new chat session"""
    try:
        session_id = await session_manager.create_session()
        logger.info(f"📋 Created new session: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            status="active"
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@app.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session information"""
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session_id,
            created_at=session_info.get("created_at", datetime.now().isoformat()),
            status=session_info.get("status", "active")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session")

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """End a chat session"""
    try:
        success = await session_manager.end_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"🗑️ Ended session: {session_id}")
        return {"message": "Session ended successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")

# Text message endpoint (alternative to WebSocket)
@app.post("/api/v1/sessions/{session_id}/text")
async def send_text_message(session_id: str, request: TextMessageRequest):
    """Send a text message to the session (HTTP alternative)"""
    try:
        # Verify session exists
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Handle idle frame requests
        if request.get_idle_frames:
            logger.info(f"🎭 Generating {request.frame_count} idle avatar frames for session {session_id}")
            idle_frames = await pipeline_service.generate_idle_frames(request.frame_count)
            return {
                "message": "Idle frames generated successfully",
                "transcribed_text": "",
                "response_text": "",
                "audio_data": None,
                "video_frames": idle_frames.get("video_frames", [])
            }
        
        # Process text through pipeline
        result = await pipeline_service.process_text(request.text, session_id)
        
        return {
            "message": "Text processed successfully",
            "transcribed_text": request.text,
            "response_text": result.get("response_text", ""),
            "audio_data": result.get("audio_data"),  # Base64 encoded
            "video_frames": result.get("video_frames", [])  # List of base64 encoded frames
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process text for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process text")

# Audio message endpoint
@app.post("/api/v1/sessions/{session_id}/audio")
async def send_audio_message(session_id: str, audio: UploadFile = File(...)):
    """Send an audio message to the session"""
    try:
        # Verify session exists
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Process audio through pipeline
        result = await pipeline_service.process_audio(audio_data, session_id)
        
        return {
            "message": "Audio processed successfully",
            "transcribed_text": result.get("transcribed_text", ""),
            "response_text": result.get("response_text", ""),
            "audio_data": result.get("audio_data"),  # Base64 encoded
            "video_frames": result.get("video_frames", [])  # List of base64 encoded frames
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process audio for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process audio")

# WebSocket endpoint for real-time communication
@app.websocket("/api/v1/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time avatar chat"""
    try:
        # Verify session exists
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            await websocket.close(code=4004, reason="Session not found")
            return
        
        # Accept connection and start handling
        await websocket_manager.connect(websocket, session_id)
        logger.info(f"🔌 WebSocket connected for session: {session_id}")
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_json()
                await websocket_manager.handle_message(data, session_id)
                
        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket disconnected for session: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
            await websocket.close(code=1011, reason="Internal error")
        finally:
            await websocket_manager.disconnect(session_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection failed for session {session_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Connection failed")
        except:
            pass

# Root redirect
@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return JSONResponse({
        "message": "OpenAvatarChat API Backend",
        "docs": "/api/docs",
        "health": "/api/v1/health",
        "version": "1.0.0"
    })

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OpenAvatarChat API Backend')
    parser.add_argument('--port', type=int, default=settings.port, help='Port to run the server on')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL/HTTPS')
    parser.add_argument('--host', type=str, default=settings.host, help='Host to bind to')
    args = parser.parse_args()
    
    # Override settings with command line arguments
    settings.port = args.port
    settings.host = args.host
    if args.ssl:
        settings.enable_ssl = True
    
    # SSL configuration
    ssl_keyfile = None
    ssl_certfile = None
    
    if settings.enable_ssl:
        ssl_certfile = str(project_root / settings.ssl_cert_path)
        ssl_keyfile = str(project_root / settings.ssl_key_path)
        logger.info(f"🔒 SSL enabled with cert: {ssl_certfile}")
    
    logger.info(f"🚀 Starting OpenAvatarChat API on {settings.host}:{settings.port}")
    if settings.enable_ssl:
        logger.info(f"🔒 HTTPS mode enabled")
    else:
        logger.info(f"🔓 HTTP mode (no SSL)")
        
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )
