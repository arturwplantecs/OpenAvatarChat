"""
API Models for OpenAvatarChat
"""

from .requests import (
    CreateSessionRequest,
    TextMessageRequest,
    AudioMessageRequest,
    GetSessionRequest
)

from .responses import (
    SessionResponse,
    TextMessageResponse,
    AudioMessageResponse,
    HealthResponse,
    ErrorResponse,
    StatusResponse
)

__all__ = [
    # Requests
    "CreateSessionRequest",
    "TextMessageRequest", 
    "AudioMessageRequest",
    "GetSessionRequest",
    # Responses
    "SessionResponse",
    "TextMessageResponse",
    "AudioMessageResponse",
    "HealthResponse",
    "ErrorResponse",
    "StatusResponse"
]
