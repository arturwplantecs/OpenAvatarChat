"""
Response models for the OpenAvatarChat API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class SessionResponse(BaseModel):
    """Response for session operations"""
    session_id: str
    session_name: Optional[str] = None
    language: str = "pl"
    created_at: str
    status: str = "active"


class TextMessageResponse(BaseModel):
    """Response for text message processing"""
    session_id: str
    input_text: str
    response_text: str
    audio_data: Optional[str] = None  # Base64 encoded audio
    video_frames: Optional[List[str]] = None  # Base64 encoded video frames
    processing_time: float
    timestamp: str


class AudioMessageResponse(BaseModel):
    """Response for audio message processing"""
    session_id: str
    transcribed_text: str
    response_text: str
    audio_data: Optional[str] = None  # Base64 encoded audio
    video_frames: Optional[List[str]] = None  # Base64 encoded video frames
    processing_time: float
    timestamp: str


class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    version: str
    pipeline_status: Dict[str, Any]
    uptime: float


class ErrorResponse(BaseModel):
    """Response for errors"""
    error: str
    details: Optional[str] = None
    status_code: int = 500


class StatusResponse(BaseModel):
    """Response for status endpoint"""
    api_status: str
    pipeline_initialized: bool
    components: Dict[str, Any]
    stats: Dict[str, Any]
