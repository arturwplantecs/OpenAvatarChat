"""
Request models for the OpenAvatarChat API
"""

from typing import Optional
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    """Request to create a new session"""
    session_name: Optional[str] = None
    language: str = "pl"
    voice_id: Optional[str] = None


class TextMessageRequest(BaseModel):
    """Request to process text message"""
    text: str
    get_idle_frames: Optional[bool] = False
    frame_count: Optional[int] = 30


class AudioMessageRequest(BaseModel):
    """Request to process audio message"""
    audio_data: str  # Base64 encoded audio
    audio_format: str = "wav"


class GetSessionRequest(BaseModel):
    """Request to get session information"""
    session_id: str
